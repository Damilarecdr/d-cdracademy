from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    LoginForm,
    RegistrationForm,
    StudentProfileForm,
    TutorLessonForm,
    TutorProfileForm,
)
from .models import (
    Course,
    CourseRegistration,
    Lesson,
    LessonProgress,
    Notification,
    PlatformSettings,
    StudentProfile,
    TutorProfile,
    User,
)
from .permissions import role_required, student_required, tutor_required






def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = RegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data

        with transaction.atomic():
            user = User.objects.create_user(
                email=data["email"],
                password=data["password"],
                first_name=data["full_name"].split()[0],
                last_name=" ".join(data["full_name"].split()[1:]),
                role=data["role"],

                jamb_category=data.get("jamb_category") or None,
                alevel_category=data.get("alevel_category") or None,

                university_category=data.get("university_category") or None,
                university_level=data.get("university_level") or None,
            )

            if user.role in {"JAMB", "ALEVEL", "UNIVERSITY"}:
                StudentProfile.objects.create(user=user)

            elif user.role == "TUTOR":
                TutorProfile.objects.create(user=user)

        login(request, user)

        messages.success(
            request,
            "Your account has been created successfully."
        )

        return redirect("dashboard")

    return render(
        request,
        "academy/register.html",
        {"form": form}
    )



def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.cleaned_data["user"])
        messages.success(request, "Welcome back.")
        return redirect("dashboard")

    return render(request, "academy/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")


@login_required
def dashboard(request):
    user = request.user

    if not user.is_active or user.is_suspended:
        logout(request)
        messages.error(request, "Your account is inactive or suspended.")
        return redirect("login")

    if user.is_superuser or user.role == "ADMIN":
        return redirect("/admin/")

    mapping = {
        "JAMB": "jamb-dashboard",
        "ALEVEL": "alevel-dashboard",
        "UNIVERSITY": "university-dashboard",
        "TUTOR": "tutor-dashboard",
    }

    return redirect(mapping[user.role])


def _course_limit(user):
    if user.role == "JAMB":
        return 4
    if user.role == "ALEVEL":
        return 3
    if user.role == "UNIVERSITY":
        settings = PlatformSettings.objects.first()
        return settings.university_course_limit if settings else 6
    return 0


def _student_dashboard_context(user):
    registrations = (
        CourseRegistration.objects
        .filter(student=user, course__is_active=True)
        .select_related("course", "course__tutor")
    )

    courses = [r.course for r in registrations]
    progress = []

    for course in courses:
        total = course.lessons.filter(is_published=True).count()
        completed = LessonProgress.objects.filter(
            student=user,
            lesson__course=course,
            lesson__is_published=True,
            completed=True,
        ).count()

        percentage = round((completed / total) * 100) if total else 0
        progress.append({
            "course": course,
            "total": total,
            "completed": completed,
            "percentage": percentage,
        })

    available = Course.objects.filter(
        is_active=True,
        category=user.role,
    ).exclude(
        registrations__student=user
    ).select_related("tutor")

    return {
        "registrations": registrations,
        "progress": progress,
        "available_courses": available,
        "course_count": len(courses),
        "course_limit": _course_limit(user),
        "remaining_slots": max(_course_limit(user) - len(courses), 0),
    }


@role_required("JAMB")
def jamb_dashboard(request):
    context = _student_dashboard_context(request.user)
    return render(request, "academy/dashboard/jamb.html", context)


@role_required("ALEVEL")
def alevel_dashboard(request):
    context = _student_dashboard_context(request.user)
    return render(request, "academy/dashboard/alevel.html", context)


@role_required("UNIVERSITY")
def university_dashboard(request):
    context = _student_dashboard_context(request.user)
    return render(request, "academy/dashboard/university.html", context)


@login_required
@role_required("TUTOR")
def tutor_dashboard(request):
    """
    Tutor dashboard.

    Displays only courses assigned to the logged-in tutor.
    """

    courses = (
        Course.objects
        .filter(
            tutor=request.user,
            is_active=True,
        )
        .select_related("tutor")
        .prefetch_related("lessons")
        .order_by("-created_at")
    )

    course_count = courses.count()

    # Total lessons across tutor's courses
    lesson_count = Lesson.objects.filter(
        course__tutor=request.user
    ).count()

    # Unique students registered for tutor's courses
    student_count = (
        CourseRegistration.objects
        .filter(
            course__tutor=request.user
        )
        .values("student")
        .distinct()
        .count()
    )

    context = {
        "courses": courses,
        "course_count": course_count,
        "student_count": student_count,
        "lesson_count": lesson_count,
    }

    return render(
        request,
        "academy/dashboard/tutor.html",
        context,
    )



@student_required
def course_list(request):

    # Get active courses for the student's programme
    courses = Course.objects.filter(
        is_active=True,
        category=request.user.role,
    )

    # Filter JAMB courses by student's category
    if request.user.role == "JAMB":
        courses = courses.filter(
            jamb_category=request.user.jamb_category,
        )

    # Filter A-Level courses by student's category
    elif request.user.role == "ALEVEL":
        courses = courses.filter(
            alevel_category=request.user.alevel_category,
        )

    # Filter University courses by category and academic level
    elif request.user.role == "UNIVERSITY":
        courses = courses.filter(
            university_category=request.user.university_category,
            university_level=request.user.university_level,
        )

    courses = courses.select_related("tutor")

    registered_ids = CourseRegistration.objects.filter(
        student=request.user
    ).values_list("course_id", flat=True)

    current_count = CourseRegistration.objects.filter(
        student=request.user
    ).count()

    return render(
        request,
        "academy/courses/course_list.html",
        {
            "courses": courses,
            "registered_ids": set(registered_ids),
            "course_limit": _course_limit(request.user),
            "current_count": current_count,
        },
    )



@student_required
def my_courses(request):
    registrations = (
        CourseRegistration.objects
        .filter(student=request.user, course__is_active=True)
        .select_related("course", "course__tutor")
    )

    course_data = []

    for registration in registrations:
        course = registration.course
        total = course.lessons.filter(is_published=True).count()
        completed = LessonProgress.objects.filter(
            student=request.user,
            lesson__course=course,
            lesson__is_published=True,
            completed=True,
        ).count()
        percentage = round((completed / total) * 100) if total else 0

        course_data.append({
            "registration": registration,
            "course": course,
            "total": total,
            "completed": completed,
            "percentage": percentage,
        })

    return render(
        request,
        "academy/courses/my_courses.html",
        {"course_data": course_data},
    )


@student_required
def course_detail(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("tutor"),
        id=course_id,
        is_active=True,
        category=request.user.role,
    )

    registered = CourseRegistration.objects.filter(
        student=request.user,
        course=course,
    ).exists()

    lessons = course.lessons.filter(is_published=True)

    if not registered:
        return render(
            request,
            "academy/courses/course_detail.html",
            {
                "course": course,
                "registered": False,
                "lessons": [],
                "progress": 0,
            },
            status=403,
        )

    total = lessons.count()
    completed = LessonProgress.objects.filter(
        student=request.user,
        lesson__course=course,
        lesson__is_published=True,
        completed=True,
    ).count()

    percentage = round((completed / total) * 100) if total else 0

    completed_ids = set(
        LessonProgress.objects.filter(
            student=request.user,
            lesson__course=course,
            completed=True,
        ).values_list("lesson_id", flat=True)
    )

    return render(
        request,
        "academy/courses/course_detail.html",
        {
            "course": course,
            "registered": True,
            "lessons": lessons,
            "completed_ids": completed_ids,
            "total": total,
            "completed": completed,
            "progress": percentage,
        },
    )


@student_required
@require_POST
def register_course(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
        is_active=True,
        category=request.user.role,
    )

    with transaction.atomic():
        existing = CourseRegistration.objects.filter(
            student=request.user,
            course=course,
        ).exists()

        if existing:
            messages.info(request, "You are already registered for this course.")
            return redirect("course-detail", course_id=course.id)

        registration_count = CourseRegistration.objects.filter(
            student=request.user
        ).count()

        limit = _course_limit(request.user)

        if registration_count >= limit:
            messages.error(
                request,
                f"You can register for a maximum of {limit} courses.",
            )
            return redirect("course-list")

        CourseRegistration.objects.create(
            student=request.user,
            course=course,
        )

    Notification.objects.create(
        recipient=request.user,
        title="Course Registration",
        message=f"You successfully registered for {course.title}.",
    )

    messages.success(request, f"You are now registered for {course.title}.")
    return redirect("my-courses")


@student_required
@require_POST
def unregister_course(request, course_id):
    registration = get_object_or_404(
        CourseRegistration,
        student=request.user,
        course_id=course_id,
    )

    course_title = registration.course.title
    registration.delete()

    Notification.objects.create(
        recipient=request.user,
        title="Course Removed",
        message=f"You removed {course_title} from your registered courses.",
    )

    messages.success(request, f"{course_title} has been removed.")
    return redirect("my-courses")


@student_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("course"),
        id=lesson_id,
        is_published=True,
    )

    registration_exists = CourseRegistration.objects.filter(
        student=request.user,
        course=lesson.course,
    ).exists()

    if not registration_exists:
        raise PermissionDenied("You are not registered for this course.")

    progress, _ = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson,
    )

    previous_lesson = (
        lesson.course.lessons
        .filter(is_published=True, lesson_order__lt=lesson.lesson_order)
        .order_by("-lesson_order", "-id")
        .first()
    )

    next_lesson = (
        lesson.course.lessons
        .filter(is_published=True, lesson_order__gt=lesson.lesson_order)
        .order_by("lesson_order", "id")
        .first()
    )

    total = lesson.course.lessons.filter(is_published=True).count()
    completed = LessonProgress.objects.filter(
        student=request.user,
        lesson__course=lesson.course,
        lesson__is_published=True,
        completed=True,
    ).count()

    percentage = round((completed / total) * 100) if total else 0

    return render(
        request,
        "academy/lessons/lesson_detail.html",
        {
            "lesson": lesson,
            "progress": progress,
            "previous_lesson": previous_lesson,
            "next_lesson": next_lesson,
            "total": total,
            "completed": completed,
            "percentage": percentage,
        },
    )


@student_required
@require_POST
def complete_lesson(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        is_published=True,
    )

    if not CourseRegistration.objects.filter(
        student=request.user,
        course=lesson.course,
    ).exists():
        raise PermissionDenied("You are not registered for this course.")

    progress, _ = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson,
    )

    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save(update_fields=["completed", "completed_at", "last_viewed"])

    messages.success(request, "Lesson marked as completed.")
    return redirect("lesson-detail", lesson_id=lesson.id)


@login_required
def profile(request):
    user = request.user

    if user.role == "TUTOR":
        profile_obj, _ = TutorProfile.objects.get_or_create(user=user)
        form = TutorProfileForm(
            request.POST or None,
            request.FILES or None,
            instance=profile_obj,
        )
    elif user.is_student:
        profile_obj, _ = StudentProfile.objects.get_or_create(user=user)
        form = StudentProfileForm(
            request.POST or None,
            request.FILES or None,
            instance=profile_obj,
        )
    else:
        profile_obj = None
        form = None

    if request.method == "POST" and form and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("profile")

    notifications = user.notifications.all()[:10]

    return render(
        request,
        "academy/profile/profile.html",
        {
            "profile_obj": profile_obj,
            "form": form,
            "notifications": notifications,
        },
    )


@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your password has been changed. Please log in again.")
        logout(request)
        return redirect("login")

    return render(
        request,
        "academy/profile/change_password.html",
        {"form": form},
    )


from django.contrib.auth.decorators import login_required
from django.db.models import Count

@tutor_required
def tutor_courses(request):
    courses = (
        Course.objects
        .filter(tutor=request.user)
        .annotate(
            total_students=Count("registrations", distinct=True),
            total_lessons=Count("lessons", distinct=True),
        )
    )

    return render(
        request,
        "academy/tutor/courses.html",
        {"courses": courses},
    )


@login_required
@role_required("TUTOR")
def tutor_course_detail(request, course_id):
    course = get_object_or_404(
        Course.objects
        .select_related("tutor"),
        id=course_id,
        tutor=request.user,
    )

    lessons = (
        Lesson.objects
        .filter(course=course)
        .order_by("lesson_order", "created_at")
    )

    student_count = (
        CourseRegistration.objects
        .filter(course=course)
        .values("student")
        .distinct()
        .count()
    )

    lesson_count = lessons.count()

    context = {
        "course": course,
        "lessons": lessons,
        "student_count": student_count,
        "lesson_count": lesson_count,
    }

    return render(
        request,
        "academy/tutor/course_detail.html",
        context,
    )


@tutor_required
def tutor_students(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
        tutor=request.user,
    )

    registrations = (
        CourseRegistration.objects
        .filter(course=course)
        .select_related("student")
    )

    rows = []

    for registration in registrations:
        total = course.lessons.filter(is_published=True).count()
        completed = LessonProgress.objects.filter(
            student=registration.student,
            lesson__course=course,
            lesson__is_published=True,
            completed=True,
        ).count()
        percentage = round((completed / total) * 100) if total else 0

        rows.append({
            "registration": registration,
            "student": registration.student,
            "total": total,
            "completed": completed,
            "percentage": percentage,
        })

    return render(
        request,
        "academy/tutor/students.html",
        {"course": course, "rows": rows},
    )


from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

@tutor_required
def tutor_lesson_create(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
        tutor=request.user,
    )

    form = TutorLessonForm(
        request.POST or None,
        request.FILES or None
    )

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                lesson = form.save(commit=False)

                # Always attach the lesson to the current course
                lesson.course = course

                # Automatically determine the next lesson order.
                # This prevents duplicate (course, lesson_order) values.
                last_order = (
                    Lesson.objects
                    .filter(course=course)
                    .order_by("-lesson_order")
                    .values_list("lesson_order", flat=True)
                    .first()
                )

                lesson.lesson_order = (last_order or 0) + 1

                lesson.save()

            messages.success(
                request,
                f'Lesson "{lesson.title}" created successfully.'
            )

            return redirect(
                "tutor-course-detail",
                course_id=course.id
            )

        except Exception:
            messages.error(
                request,
                "Unable to create the lesson. Please try again."
            )

    return render(
        request,
        "academy/tutor/lesson_create.html",
        {
            "course": course,
            "form": form,
        },
    )


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import tutor_required
from .forms import TutorLessonForm
from .models import Lesson, Quiz


@tutor_required
def tutor_lesson_edit(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__tutor=request.user,
    )

    form = TutorLessonForm(
        request.POST or None,
        request.FILES or None,
        instance=lesson,
    )

    # Get the quiz if this lesson already has one
    quiz = getattr(lesson, "quiz", None)

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Lesson updated successfully."
        )

        return redirect(
            "tutor-course-detail",
            course_id=lesson.course.id,
        )

    return render(
        request,
        "academy/tutor/lesson_edit.html",
        {
            "lesson": lesson,
            "course": lesson.course,
            "form": form,
            "quiz": quiz,
        },
    )


@tutor_required
def tutor_quiz_create(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__tutor=request.user,
    )

    # A lesson can only have one quiz
    if hasattr(lesson, "quiz"):
        messages.info(
            request,
            "This lesson already has a quiz."
        )
        return redirect(
            "tutor-quiz-edit",
            lesson_id=lesson.id,
        )

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        pass_mark = request.POST.get("pass_mark", 50)
        time_limit = request.POST.get("time_limit", 0)
        max_attempts = request.POST.get("max_attempts", 0)

        if not title:
            messages.error(
                request,
                "Quiz title is required."
            )

            return render(
                request,
                "academy/tutor/quiz/quiz_create.html",
                {
                    "lesson": lesson,
                    "course": lesson.course,
                },
            )

        try:
            pass_mark = int(pass_mark)
            time_limit = int(time_limit)
            max_attempts = int(max_attempts)
        except (TypeError, ValueError):
            messages.error(
                request,
                "Please enter valid quiz settings."
            )

            return render(
                request,
                "academy/tutor/quiz_create.html",
                {
                    "lesson": lesson,
                    "course": lesson.course,
                },
            )

        if not 0 <= pass_mark <= 100:
            messages.error(
                request,
                "Pass mark must be between 0 and 100."
            )

            return render(
                request,
                "academy/tutor/quiz_create.html",
                {
                    "lesson": lesson,
                    "course": lesson.course,
                },
            )

        if time_limit < 0 or max_attempts < 0:
            messages.error(
                request,
                "Time limit and maximum attempts cannot be negative."
            )

            return render(
                request,
                "academy/tutor/quiz_create.html",
                {
                    "lesson": lesson,
                    "course": lesson.course,
                },
            )

        quiz = Quiz.objects.create(
            lesson=lesson,
            title=title,
            description=description,
            pass_mark=pass_mark,
            time_limit=time_limit,
            max_attempts=max_attempts,
            is_published=False,
        )

        messages.success(
            request,
            "Quiz created successfully. You can now add questions."
        )

        return redirect(
            "tutor-quiz-edit",
            lesson_id=lesson.id,
        )

    return render(
        request,
        "academy/tutor/quiz_create.html",
        {
            "lesson": lesson,
            "course": lesson.course,
        },
    )

@tutor_required
def tutor_quiz_edit(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__tutor=request.user,
    )

    quiz = get_object_or_404(
        Quiz,
        lesson=lesson,
    )

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        try:
            pass_mark = int(request.POST.get("pass_mark", 50))
            time_limit = int(request.POST.get("time_limit", 0))
            max_attempts = int(request.POST.get("max_attempts", 0))
        except (TypeError, ValueError):
            messages.error(
                request,
                "Please enter valid quiz settings."
            )

            return redirect(
                "tutor-quiz-edit",
                lesson_id=lesson.id,
            )

        if not title:
            messages.error(
                request,
                "Quiz title is required."
            )

            return redirect(
                "tutor-quiz-edit",
                lesson_id=lesson.id,
            )

        if not 0 <= pass_mark <= 100:
            messages.error(
                request,
                "Pass mark must be between 0 and 100."
            )

            return redirect(
                "tutor-quiz-edit",
                lesson_id=lesson.id,
            )

        if time_limit < 0 or max_attempts < 0:
            messages.error(
                request,
                "Time limit and maximum attempts cannot be negative."
            )

            return redirect(
                "tutor-quiz-edit",
                lesson_id=lesson.id,
            )

        quiz.title = title
        quiz.description = description
        quiz.pass_mark = pass_mark
        quiz.time_limit = time_limit
        quiz.max_attempts = max_attempts

        if "is_published" in request.POST:
            quiz.is_published = True
        else:
            quiz.is_published = False

        quiz.save()

        messages.success(
            request,
            "Quiz updated successfully."
        )

        return redirect(
            "tutor-quiz-edit",
            lesson_id=lesson.id,
        )

    questions = quiz.questions.prefetch_related("options")

    return render(
        request,
        "academy/tutor/quiz/quiz_edit.html",
        {
            "lesson": lesson,
            "course": lesson.course,
            "quiz": quiz,
            "questions": questions,
        },
    )



from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .models import Quiz, QuizQuestion, QuizOption


from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction

from .decorators import tutor_required
from .models import (
    Lesson,
    Quiz,
    QuizQuestion,
    QuizOption,
)


@tutor_required
def tutor_quiz_question_create(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__tutor=request.user,
    )

    quiz = get_object_or_404(
        Quiz,
        lesson=lesson,
    )

    if request.method == "POST":

        question_text = request.POST.get(
            "question",
            ""
        ).strip()

        question_type = request.POST.get(
            "question_type",
            "MCQ"
        )

        points = request.POST.get(
            "points",
            "1"
        )

        correct_option = request.POST.get(
            "correct_option",
            ""
        )

        # --------------------------------
        # VALIDATE QUESTION
        # --------------------------------

        if not question_text:
            messages.error(
                request,
                "Question text is required."
            )

            return render(
                request,
                "academy/tutor/quiz/question_create.html",
                {
                    "lesson": lesson,
                    "course": lesson.course,
                    "quiz": quiz,
                },
            )

        # --------------------------------
        # VALIDATE QUESTION TYPE
        # --------------------------------

        valid_types = dict(
            QuizQuestion.QUESTION_TYPES
        )

        if question_type not in valid_types:
            messages.error(
                request,
                "Invalid question type."
            )

            return render(
                request,
                "academy/tutor/quiz/question_create.html",
                {
                    "lesson": lesson,
                    "course": lesson.course,
                    "quiz": quiz,
                },
            )

        # --------------------------------
        # VALIDATE POINTS
        # --------------------------------

        try:
            points = int(points)
        except (TypeError, ValueError):
            messages.error(
                request,
                "Points must be a valid number."
            )

            return render(
                request,
                "academy/tutor/quiz/question_create.html",
                {
                    "lesson": lesson,
                    "course": lesson.course,
                    "quiz": quiz,
                },
            )

        if points < 1:
            messages.error(
                request,
                "Points must be at least 1."
            )

            return render(
                request,
                "academy/tutor/quiz/question_create.html",
                {
                    "lesson": lesson,
                    "course": lesson.course,
                    "quiz": quiz,
                },
            )

        # --------------------------------
        # GET OPTIONS
        # --------------------------------

        option_values = [
            request.POST.get("option_1", "").strip(),
            request.POST.get("option_2", "").strip(),
            request.POST.get("option_3", "").strip(),
            request.POST.get("option_4", "").strip(),
        ]

        # --------------------------------
        # TRUE / FALSE
        # --------------------------------

        if question_type == "TF":

            options = [
                "True",
                "False",
            ]

            if correct_option not in ["1", "2"]:
                messages.error(
                    request,
                    "Please select the correct answer."
                )

                return render(
                    request,
                    "academy/tutor/quiz/question_create.html",
                    {
                        "lesson": lesson,
                        "course": lesson.course,
                        "quiz": quiz,
                    },
                )

        # --------------------------------
        # MULTIPLE CHOICE
        # --------------------------------

        else:

            # Remove empty options
            options = [
                option
                for option in option_values
                if option
            ]

            if len(options) < 2:
                messages.error(
                    request,
                    "A multiple choice question must have at least 2 options."
                )

                return render(
                    request,
                    "academy/tutor/quiz/question_create.html",
                    {
                        "lesson": lesson,
                        "course": lesson.course,
                        "quiz": quiz,
                    },
                )

            if len(options) > 4:
                messages.error(
                    request,
                    "A question can have a maximum of 4 options."
                )

                return render(
                    request,
                    "academy/tutor/quiz/question_create.html",
                    {
                        "lesson": lesson,
                        "course": lesson.course,
                        "quiz": quiz,
                    },
                )

            try:
                correct_index = int(correct_option)
            except (TypeError, ValueError):
                correct_index = 0

            if correct_index < 1 or correct_index > len(options):
                messages.error(
                    request,
                    "Please select the correct answer."
                )

                return render(
                    request,
                    "academy/tutor/quiz/question_create.html",
                    {
                        "lesson": lesson,
                        "course": lesson.course,
                        "quiz": quiz,
                    },
                )

        # --------------------------------
        # NEXT QUESTION ORDER
        # --------------------------------

        last_question = (
            quiz.questions
            .order_by("-question_order")
            .first()
        )

        next_order = (
            last_question.question_order + 1
            if last_question
            else 1
        )

        # --------------------------------
        # CREATE QUESTION + OPTIONS
        # --------------------------------

        with transaction.atomic():

            question = QuizQuestion.objects.create(
                quiz=quiz,
                question=question_text,
                question_type=question_type,
                points=points,
                question_order=next_order,
            )

            for index, option_text in enumerate(
                options,
                start=1
            ):
                QuizOption.objects.create(
                    question=question,
                    text=option_text,
                    option_order=index,
                    is_correct=(
                        str(index) == correct_option
                    ),
                )

        messages.success(
            request,
            "Question and options created successfully."
        )

        return redirect(
            "tutor-quiz-edit",
            lesson_id=lesson.id,
        )

    return render(
        request,
        "academy/tutor/quiz/question_create.html",
        {
            "lesson": lesson,
            "course": lesson.course,
            "quiz": quiz,
        },
    )


@tutor_required
def tutor_quiz_question_edit(request, question_id):

    question = get_object_or_404(
        QuizQuestion.objects.select_related(
            "quiz",
            "quiz__lesson",
            "quiz__lesson__course",
        ).prefetch_related("options"),
        id=question_id,
        quiz__lesson__course__tutor=request.user,
    )

    lesson = question.quiz.lesson
    quiz = question.quiz

    options = list(
        question.options.all().order_by(
            "option_order",
            "id",
        )
    )

    if request.method == "POST":

        question_text = request.POST.get(
            "question",
            ""
        ).strip()

        question_type = request.POST.get(
            "question_type",
            question.question_type,
        ).strip().upper()

        points_raw = request.POST.get(
            "points",
            str(question.points),
        ).strip()

        correct_option = request.POST.get(
            "correct_option",
            "",
        ).strip()


        # Preserve submitted values

        context = {
            "lesson": lesson,
            "course": lesson.course,
            "quiz": quiz,
            "question": question,

            "question_text": question_text,

            "question_type": question_type,

            "points": points_raw,

            "option_1": request.POST.get(
                "option_1",
                "",
            ),

            "option_2": request.POST.get(
                "option_2",
                "",
            ),

            "option_3": request.POST.get(
                "option_3",
                "",
            ),

            "option_4": request.POST.get(
                "option_4",
                "",
            ),

            "correct_option": correct_option,
        }


        if not question_text:

            messages.error(
                request,
                "Please enter the question.",
            )

            return render(
                request,
                "academy/tutor/quiz/quiz_question_edit.html",
                context,
            )


        if question_type not in dict(
            QuizQuestion.QUESTION_TYPES
        ):

            messages.error(
                request,
                "Invalid question type.",
            )

            return render(
                request,
                "academy/tutor/quiz/quiz_question_edit.html",
                context,
            )


        try:

            points = int(points_raw)

        except (
            TypeError,
            ValueError,
        ):

            messages.error(
                request,
                "Points must be a valid number.",
            )

            return render(
                request,
                "academy/tutor/quiz/quiz_question_edit.html",
                context,
            )


        if points < 1:

            messages.error(
                request,
                "Points must be at least 1.",
            )

            return render(
                request,
                "academy/tutor/quiz/quiz_question_edit.html",
                context,
            )


        if question_type == "MCQ":

            submitted_options = []


            for number in range(1, 5):

                option_text = request.POST.get(
                    f"option_{number}",
                    "",
                ).strip()


                option_check = (
                    option_text
                    .replace("<p>", "")
                    .replace("</p>", "")
                    .replace("<br>", "")
                    .replace("<br/>", "")
                    .replace("<br />", "")
                    .replace("&nbsp;", "")
                    .strip()
                )


                if option_check:

                    submitted_options.append(
                        (
                            number,
                            option_text,
                        )
                    )


            if len(submitted_options) < 2:

                messages.error(
                    request,
                    "Please provide at least 2 answer options.",
                )

                return render(
                    request,
                    "academy/tutor/quiz/quiz_question_edit.html",
                    context,
                )


            try:

                correct_number = int(
                    correct_option
                )

            except (
                TypeError,
                ValueError,
            ):

                messages.error(
                    request,
                    "Please select the correct answer.",
                )

                return render(
                    request,
                    "academy/tutor/quiz/quiz_question_edit.html",
                    context,
                )


            valid_numbers = [
                number
                for number, text
                in submitted_options
            ]


            if correct_number not in valid_numbers:

                messages.error(
                    request,
                    "The selected correct answer does not contain an option.",
                )

                return render(
                    request,
                    "academy/tutor/quiz/quiz_question_edit.html",
                    context,
                )


            from django.db import transaction


            with transaction.atomic():

                question.question = question_text

                question.question_type = "MCQ"

                question.points = points

                question.save()


                question.options.all().delete()


                for option_order, (
                    original_number,
                    option_text,
                ) in enumerate(
                    submitted_options,
                    start=1,
                ):

                    QuizOption.objects.create(

                        question=question,

                        text=option_text,

                        is_correct=(
                            original_number ==
                            correct_number
                        ),

                        option_order=option_order,

                    )


            messages.success(
                request,
                "Question updated successfully.",
            )


            return redirect(
                "tutor-quiz-edit",
                lesson_id=lesson.id,
            )


        elif question_type == "TF":

            if correct_option not in [
                "1",
                "2",
            ]:

                messages.error(
                    request,
                    "Please select True or False as the correct answer.",
                )

                return render(
                    request,
                    "academy/tutor/quiz/quiz_question_edit.html",
                    context,
                )


            from django.db import transaction


            with transaction.atomic():

                question.question = question_text

                question.question_type = "TF"

                question.points = points

                question.save()


                question.options.all().delete()


                QuizOption.objects.create(

                    question=question,

                    text="True",

                    is_correct=(
                        correct_option == "1"
                    ),

                    option_order=1,

                )


                QuizOption.objects.create(

                    question=question,

                    text="False",

                    is_correct=(
                        correct_option == "2"
                    ),

                    option_order=2,

                )


            messages.success(
                request,
                "Question updated successfully.",
            )


            return redirect(
                "tutor-quiz-edit",
                lesson_id=lesson.id,
            )


    else:

        option_1 = ""
        option_2 = ""
        option_3 = ""
        option_4 = ""

        correct_option = ""


        for index, option in enumerate(
            options[:4],
            start=1,
        ):

            if index == 1:
                option_1 = option.text

            elif index == 2:
                option_2 = option.text

            elif index == 3:
                option_3 = option.text

            elif index == 4:
                option_4 = option.text


            if option.is_correct:

                correct_option = str(index)


        context = {

            "lesson": lesson,

            "course": lesson.course,

            "quiz": quiz,

            "question": question,

            "question_text": question.question,

            "question_type": question.question_type,

            "points": question.points,

            "option_1": option_1,

            "option_2": option_2,

            "option_3": option_3,

            "option_4": option_4,

            "correct_option": correct_option,

        }


    return render(
        request,
        "academy/tutor/quiz/quiz_question_edit.html",
        context,
    )


@tutor_required
def tutor_quiz_question_delete(request, question_id):
    question = get_object_or_404(
        QuizQuestion.objects.select_related(
            "quiz",
            "quiz__lesson",
            "quiz__lesson__course",
        ),
        id=question_id,
        quiz__lesson__course__tutor=request.user,
    )

    lesson = question.quiz.lesson

    if request.method == "POST":
        question.delete()

        messages.success(
            request,
            "Question deleted successfully."
        )

        return redirect(
            "tutor-quiz-edit",
            lesson_id=lesson.id,
        )

    return redirect(
        "tutor-quiz-question-edit",
        question_id=question.id,
    )

import os
import re
import uuid

from django.contrib import messages
from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from docx import Document

from .decorators import tutor_required
from .models import (
    Lesson,
    Quiz,
    QuizQuestion,
    QuizOption,
)

@tutor_required
def tutor_quiz_question_create(request, lesson_id):

    # =========================================================
    # GET LESSON
    # =========================================================

    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__tutor=request.user,
    )

    # =========================================================
    # GET QUIZ
    # =========================================================

    quiz = get_object_or_404(
        Quiz,
        lesson=lesson,
    )

    # =========================================================
    # COMMON TEMPLATE CONTEXT
    # =========================================================

    context = {
        "lesson": lesson,
        "course": lesson.course,
        "quiz": quiz,

        # Form defaults
        "question_text": "",
        "question_type": "MCQ",
        "points": 1,

        "option_1": "",
        "option_2": "",
        "option_3": "",
        "option_4": "",

        "correct_option": "",
    }

    # =========================================================
    # POST
    # =========================================================

    if request.method == "POST":

        # =====================================================
        # QUESTION
        # =====================================================

        question_text = request.POST.get(
            "question",
            ""
        ).strip()

        question_type = request.POST.get(
            "question_type",
            "MCQ"
        ).strip().upper()

        points_raw = request.POST.get(
            "points",
            "1"
        ).strip()

        # =====================================================
        # PRESERVE FORM VALUES
        # =====================================================

        context.update({
            "question_text": question_text,
            "question_type": question_type,
            "points": points_raw,

            "option_1": request.POST.get(
                "option_1",
                ""
            ),

            "option_2": request.POST.get(
                "option_2",
                ""
            ),

            "option_3": request.POST.get(
                "option_3",
                ""
            ),

            "option_4": request.POST.get(
                "option_4",
                ""
            ),

            "correct_option": request.POST.get(
                "correct_option",
                ""
            ),
        })

        # =====================================================
        # QUESTION VALIDATION
        # =====================================================

        # CKEditor may submit HTML such as:
        #
        # <p></p>
        #
        # or
        #
        # <p>&nbsp;</p>
        #
        # So remove those cases before deciding whether
        # the question is actually empty.
        # =====================================================

        question_check = (
            question_text
            .replace("<p>", "")
            .replace("</p>", "")
            .replace("<br>", "")
            .replace("<br/>", "")
            .replace("<br />", "")
            .replace("&nbsp;", "")
            .strip()
        )

        if not question_check:

            messages.error(
                request,
                "Please enter the question."
            )

            return render(
                request,
                "academy/tutor/quiz/question_create.html",
                context,
            )

        # =====================================================
        # QUESTION TYPE
        # =====================================================

        valid_question_types = dict(
            QuizQuestion.QUESTION_TYPES
        )

        if question_type not in valid_question_types:

            messages.error(
                request,
                "Invalid question type."
            )

            return render(
                request,
                "academy/tutor/quiz/question_create.html",
                context,
            )

        # =====================================================
        # POINTS
        # =====================================================

        try:

            points = int(points_raw)

        except (TypeError, ValueError):

            messages.error(
                request,
                "Points must be a valid number."
            )

            return render(
                request,
                "academy/tutor/quiz/question_create.html",
                context,
            )

        if points < 1:

            messages.error(
                request,
                "Points must be at least 1."
            )

            return render(
                request,
                "academy/tutor/quiz/question_create.html",
                context,
            )

        # =====================================================
        # GET NEXT QUESTION ORDER
        # =====================================================

        last_question = (
            quiz.questions
            .order_by("-question_order")
            .first()
        )

        next_order = (
            last_question.question_order + 1
            if last_question
            else 1
        )

        # =========================================================
        # MCQ
        # =========================================================

        if question_type == "MCQ":

            option_values = []

            # -----------------------------------------------------
            # Read all four CKEditor fields
            # -----------------------------------------------------

            for number in range(1, 5):

                option_text = request.POST.get(
                    f"option_{number}",
                    ""
                ).strip()

                # -------------------------------------------------
                # Determine whether the editor actually contains
                # useful content.
                # -------------------------------------------------

                option_check = (
                    option_text
                    .replace("<p>", "")
                    .replace("</p>", "")
                    .replace("<br>", "")
                    .replace("<br/>", "")
                    .replace("<br />", "")
                    .replace("&nbsp;", "")
                    .strip()
                )

                if option_check:

                    option_values.append(
                        (
                            number,
                            option_text,
                        )
                    )

            # -----------------------------------------------------
            # Require at least two options
            # -----------------------------------------------------

            if len(option_values) < 2:

                messages.error(
                    request,
                    "Please provide at least 2 answer options."
                )

                return render(
                    request,
                    "academy/tutor/quiz/question_create.html",
                    context,
                )

            # =====================================================
            # CORRECT ANSWER
            # =====================================================

            correct_option = request.POST.get(
                "correct_option",
                ""
            ).strip()

            if not correct_option:

                messages.error(
                    request,
                    "Please select the correct answer."
                )

                return render(
                    request,
                    "academy/tutor/quiz/question_create.html",
                    context,
                )

            # -----------------------------------------------------
            # Convert correct option to integer
            # -----------------------------------------------------

            try:

                correct_option = int(
                    correct_option
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    "Invalid correct answer."
                )

                return render(
                    request,
                    "academy/tutor/quiz/question_create.html",
                    context,
                )

            # =====================================================
            # MAKE SURE CORRECT OPTION EXISTS
            # =====================================================

            valid_option_numbers = [
                number
                for number, text in option_values
            ]

            if correct_option not in valid_option_numbers:

                messages.error(
                    request,
                    "The selected correct answer does not contain an option."
                )

                return render(
                    request,
                    "academy/tutor/quiz/question_create.html",
                    context,
                )

            # =====================================================
            # CREATE QUESTION + OPTIONS
            # =====================================================

            with transaction.atomic():

                question = QuizQuestion.objects.create(
                    quiz=quiz,
                    question=question_text,
                    question_type="MCQ",
                    points=points,
                    question_order=next_order,
                )

                # -------------------------------------------------
                # Save options using their original editor order
                # -------------------------------------------------

                for option_order, (
                    original_number,
                    option_text,
                ) in enumerate(
                    option_values,
                    start=1,
                ):

                    QuizOption.objects.create(
                        question=question,
                        text=option_text,

                        is_correct=(
                            original_number
                            == correct_option
                        ),

                        option_order=option_order,
                    )

            messages.success(
                request,
                "Question and answer options created successfully."
            )

            return redirect(
                "tutor-quiz-edit",
                lesson_id=lesson.id,
            )

        # =========================================================
        # TRUE / FALSE
        # =========================================================

        if question_type == "TF":

            correct_option = request.POST.get(
                "correct_option",
                ""
            ).strip()

            # -----------------------------------------------------
            # Correct answer must be 1 or 2
            #
            # 1 = True
            # 2 = False
            # -----------------------------------------------------

            if correct_option not in [
                "1",
                "2",
            ]:

                messages.error(
                    request,
                    "Please select True or False as the correct answer."
                )

                return render(
                    request,
                    "academy/tutor/quiz/question_create.html",
                    context,
                )

            # =====================================================
            # CREATE TRUE/FALSE QUESTION
            # =====================================================

            with transaction.atomic():

                question = QuizQuestion.objects.create(
                    quiz=quiz,
                    question=question_text,
                    question_type="TF",
                    points=points,
                    question_order=next_order,
                )

                # -------------------------------------------------
                # TRUE
                # -------------------------------------------------

                QuizOption.objects.create(
                    question=question,
                    text="True",

                    is_correct=(
                        correct_option == "1"
                    ),

                    option_order=1,
                )

                # -------------------------------------------------
                # FALSE
                # -------------------------------------------------

                QuizOption.objects.create(
                    question=question,
                    text="False",

                    is_correct=(
                        correct_option == "2"
                    ),

                    option_order=2,
                )

            messages.success(
                request,
                "True / False question created successfully."
            )

            return redirect(
                "tutor-quiz-edit",
                lesson_id=lesson.id,
            )

    # =========================================================
    # GET
    # =========================================================

    return render(
        request,
        "academy/tutor/quiz/question_create.html",
        context,
    )
# =========================================================
# IMPORTS
# =========================================================

import os
import re
import uuid

from django.contrib import messages
from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from docx import Document

from .decorators import tutor_required, student_required
from .models import (
    Lesson,
    Quiz,
    QuizQuestion,
    QuizOption,
    QuizAttempt,
    QuizAnswer,
)


# =========================================================
# HTML HELPERS
# =========================================================

def _escape_html(text):
    """
    Escape normal text before storing it as HTML.
    """

    if not text:
        return ""

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _html_to_text(html):
    """
    Convert stored HTML to plain text for validation.
    """

    if not html:
        return ""

    text = re.sub(
        r"<[^>]+>",
        " ",
        html,
    )

    text = (
        text
        .replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )

    return " ".join(
        text.split()
    ).strip()


# =========================================================
# DOCX IMAGE STORAGE
# =========================================================

def _save_docx_image(image_part):
    """
    Save an embedded image from a DOCX file
    into Django's media storage.
    """

    content_type = getattr(
        image_part,
        "content_type",
        "",
    )

    extension_map = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
    }

    extension = extension_map.get(
        content_type,
        ".png",
    )

    filename = (
        "ckeditor/quiz/docx/"
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    saved_path = default_storage.save(
        filename,
        image_part.blob,
    )

    return default_storage.url(
        saved_path
    )


# =========================================================
# GET IMAGES FROM DOCX PARAGRAPH
# =========================================================

def _get_paragraph_image_parts(
    paragraph,
    document,
):
    """
    Detect images directly from the DOCX XML.

    This works better with Word/WPS images than relying
    only on paragraph.runs.
    """

    image_parts = []

    try:

        blips = paragraph._p.xpath(
            ".//*[local-name()='blip']"
        )

    except Exception:

        blips = []

    for blip in blips:

        relationship_id = blip.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
        )

        if not relationship_id:
            continue

        try:

            image_part = (
                document.part
                .related_parts
                .get(
                    relationship_id
                )
            )

        except Exception:

            image_part = None

        if not image_part:
            continue

        content_type = getattr(
            image_part,
            "content_type",
            "",
        )

        if not content_type.startswith(
            "image/"
        ):
            continue

        image_parts.append(
            image_part
        )

    return image_parts


# =========================================================
# CHECK WHETHER PARAGRAPH HAS IMAGE
# =========================================================

def _paragraph_has_image(
    paragraph,
):
    """
    Return True when a DOCX paragraph contains
    an embedded image.
    """

    try:

        images = paragraph._p.xpath(
            ".//*[local-name()='blip']"
        )

        return bool(images)

    except Exception:

        return False


# =========================================================
# DOCX RUN → HTML
# =========================================================

def _run_to_html(
    run,
):
    """
    Convert a DOCX run into safe HTML.
    """

    text = run.text or ""

    if not text:
        return ""

    text = _escape_html(
        text
    )

    text = text.replace(
        "\n",
        "<br>",
    )

    if run.bold:

        text = (
            f"<strong>{text}</strong>"
        )

    if run.italic:

        text = (
            f"<em>{text}</em>"
        )

    if run.underline:

        text = (
            f"<u>{text}</u>"
        )

    return text


# =========================================================
# DOCX PARAGRAPH → HTML
# =========================================================

def _paragraph_to_html(
    paragraph,
    document,
):
    """
    Convert a complete DOCX paragraph into HTML.

    Supports:

    - normal text
    - bold
    - italic
    - underline
    - embedded images
    - image-only paragraphs
    - floating images
    """

    html = ""

    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------

    for run in paragraph.runs:

        html += _run_to_html(
            run
        )

    # -----------------------------------------------------
    # IMAGES
    # -----------------------------------------------------

    image_parts = (
        _get_paragraph_image_parts(
            paragraph,
            document,
        )
    )

    for image_part in image_parts:

        try:

            image_url = (
                _save_docx_image(
                    image_part
                )
            )

            html += (
                '<div '
                'class="quiz-docx-image" '
                'style="'
                'margin:15px 0;'
                'text-align:left;'
                '">'

                f'<img '
                f'src="{image_url}" '
                f'alt="Question image" '

                'style="'
                'max-width:100%;'
                'width:auto;'
                'height:auto;'
                'display:block;'
                'border-radius:8px;'
                '">'

                '</div>'
            )

        except Exception:

            continue

    return html.strip()


# =========================================================
# REMOVE QUESTION NUMBER
# =========================================================

def _strip_question_number(
    text,
):
    """

    1. Question
    2) Question

    becomes:

    Question
    """

    if not text:
        return ""

    return re.sub(
        r"^\s*\d+\s*[\.\)]\s*",
        "",
        text,
    ).strip()


# =========================================================
# REMOVE OPTION LETTER
# =========================================================

def _strip_option_letter(
    text,
):
    """

    A. Lagos
    B) Abuja

    becomes:

    Lagos
    Abuja
    """

    if not text:
        return ""

    return re.sub(
        r"^\s*[A-Da-d]\s*[\.\)]\s*",
        "",
        text,
    ).strip()


# =========================================================
# TUTOR QUIZ QUESTION IMPORT
# =========================================================

@tutor_required
def tutor_quiz_questions_import_docx(
    request,
    lesson_id,
):

    # =====================================================
    # GET LESSON
    # =====================================================

    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__tutor=request.user,
    )

    # =====================================================
    # GET QUIZ
    # =====================================================

    quiz = get_object_or_404(
        Quiz,
        lesson=lesson,
    )

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        uploaded_file = request.FILES.get(
            "docx_file"
        )

        # -------------------------------------------------
        # NO FILE
        # -------------------------------------------------

        if not uploaded_file:

            messages.error(
                request,
                "Please select a Word document.",
            )

            return render(
                request,
                "academy/tutor/quiz/import_docx.html",
                {
                    "lesson": lesson,
                    "quiz": quiz,
                },
            )

        # -------------------------------------------------
        # CHECK EXTENSION
        # -------------------------------------------------

        extension = os.path.splitext(
            uploaded_file.name
        )[1].lower()

        if extension != ".docx":

            messages.error(
                request,
                "Only .docx Word documents are supported.",
            )

            return render(
                request,
                "academy/tutor/quiz/import_docx.html",
                {
                    "lesson": lesson,
                    "quiz": quiz,
                },
            )

        # -------------------------------------------------
        # CHECK FILE SIZE
        # -------------------------------------------------

        max_size = 10 * 1024 * 1024

        if uploaded_file.size > max_size:

            messages.error(
                request,
                "The Word document must not exceed 10 MB.",
            )

            return render(
                request,
                "academy/tutor/quiz/import_docx.html",
                {
                    "lesson": lesson,
                    "quiz": quiz,
                },
            )

        # =================================================
        # TEMP DOCX
        # =================================================

        temp_name = (
            "quiz_imports/"
            f"{uuid.uuid4().hex}.docx"
        )

        temp_path = default_storage.save(
            temp_name,
            uploaded_file,
        )

        try:

            # =================================================
            # OPEN DOCX
            # =================================================

            with default_storage.open(
                temp_path,
                "rb",
            ) as document_file:

                document = Document(
                    document_file
                )

                parsed_questions = []

                current_question = None

                # =================================================
                # READ ALL PARAGRAPHS
                # =================================================

                for paragraph in document.paragraphs:

                    raw_text = (
                        paragraph.text or ""
                    ).strip()

                    has_image = (
                        _paragraph_has_image(
                            paragraph
                        )
                    )

                    paragraph_html = (
                        _paragraph_to_html(
                            paragraph,
                            document,
                        )
                    )

                    # =============================================
                    # QUESTION NUMBER
                    # =============================================

                    question_match = re.match(
                        r"^\s*(\d+)\s*[\.\)]\s*(.*)$",
                        raw_text,
                        re.IGNORECASE,
                    )

                    if question_match:

                        # -----------------------------------------
                        # SAVE PREVIOUS QUESTION
                        # -----------------------------------------

                        if current_question:

                            parsed_questions.append(
                                current_question
                            )

                        # -----------------------------------------
                        # CREATE NEW QUESTION
                        # -----------------------------------------

                        question_html = (
                            _strip_question_number(
                                paragraph_html
                            )
                        )

                        current_question = {
                            "question": question_html,
                            "options": [],
                            "answer": None,
                            "points": 1,
                        }

                        continue

                    # =============================================
                    # IMAGE-ONLY PARAGRAPH
                    # =============================================

                    if (
                        has_image
                        and not raw_text
                    ):

                        # -----------------------------------------
                        # NO CURRENT QUESTION
                        # -----------------------------------------

                        if current_question is None:

                            current_question = {
                                "question": paragraph_html,
                                "options": [],
                                "answer": None,
                                "points": 1,
                            }

                            continue

                        # -----------------------------------------
                        # IMAGE BEFORE OPTIONS
                        # -----------------------------------------

                        if not current_question[
                            "options"
                        ]:

                            if paragraph_html:

                                if current_question[
                                    "question"
                                ]:

                                    current_question[
                                        "question"
                                    ] += (
                                        "<br>"
                                        + paragraph_html
                                    )

                                else:

                                    current_question[
                                        "question"
                                    ] = paragraph_html

                            continue

                    # =============================================
                    # OPTION
                    # =============================================

                    option_match = re.match(
                        r"^\s*([A-Da-d])\s*[\.\)]\s*(.+)$",
                        raw_text,
                        re.IGNORECASE,
                    )

                    if (
                        option_match
                        and current_question
                    ):

                        letter = (
                            option_match
                            .group(1)
                            .upper()
                        )

                        option_html = (
                            _strip_option_letter(
                                paragraph_html
                            )
                        )

                        current_question[
                            "options"
                        ].append(
                            {
                                "letter": letter,
                                "text": option_html,
                            }
                        )

                        continue

                    # =============================================
                    # ANSWER
                    # =============================================

                    answer_match = re.match(
                        r"^\s*"
                        r"(?:answer|correct\s+answer)"
                        r"\s*:\s*"
                        r"([A-Da-d])"
                        r"\s*$",
                        raw_text,
                        re.IGNORECASE,
                    )

                    if (
                        answer_match
                        and current_question
                    ):

                        current_question[
                            "answer"
                        ] = (
                            answer_match
                            .group(1)
                            .upper()
                        )

                        continue

                    # =============================================
                    # POINTS
                    # =============================================

                    points_match = re.match(
                        r"^\s*"
                        r"points?"
                        r"\s*:\s*"
                        r"(\d+)"
                        r"\s*$",
                        raw_text,
                        re.IGNORECASE,
                    )

                    if (
                        points_match
                        and current_question
                    ):

                        points = int(
                            points_match.group(1)
                        )

                        current_question[
                            "points"
                        ] = max(
                            points,
                            1,
                        )

                        continue

                    # =============================================
                    # QUESTION CONTINUATION
                    # =============================================

                    if (
                        current_question
                        and paragraph_html
                        and not current_question[
                            "options"
                        ]
                    ):

                        if current_question[
                            "question"
                        ]:

                            current_question[
                                "question"
                            ] += (
                                "<br>"
                                + paragraph_html
                            )

                        else:

                            current_question[
                                "question"
                            ] = paragraph_html

                # =================================================
                # SAVE LAST QUESTION
                # =================================================

                if current_question:

                    parsed_questions.append(
                        current_question
                    )

                # =================================================
                # NO QUESTIONS
                # =================================================

                if not parsed_questions:

                    messages.error(
                        request,
                        (
                            "No questions were found "
                            "in the Word document."
                        ),
                    )

                    return render(
                        request,
                        "academy/tutor/quiz/import_docx.html",
                        {
                            "lesson": lesson,
                            "quiz": quiz,
                        },
                    )

                # =================================================
                # VALIDATION
                # =================================================

                errors = []

                for index, item in enumerate(
                    parsed_questions,
                    start=1,
                ):

                    question_html = (
                        item["question"]
                        or ""
                    )

                    question_text = (
                        _html_to_text(
                            question_html
                        )
                    )

                    # ---------------------------------------------
                    # QUESTION MUST HAVE TEXT OR IMAGE
                    # ---------------------------------------------

                    has_question_image = (
                        "<img"
                        in question_html.lower()
                    )

                    if (
                        not question_text
                        and not has_question_image
                    ):

                        errors.append(
                            (
                                f"Question {index} "
                                "has no question content."
                            )
                        )

                    # ---------------------------------------------
                    # OPTIONS
                    # ---------------------------------------------

                    if len(
                        item["options"]
                    ) < 2:

                        errors.append(
                            (
                                f"Question {index} "
                                "must have at least "
                                "two options."
                            )
                        )

                    # ---------------------------------------------
                    # ANSWER
                    # ---------------------------------------------

                    letters = {
                        option["letter"]
                        for option
                        in item["options"]
                    }

                    if (
                        not item["answer"]
                        or item["answer"]
                        not in letters
                    ):

                        errors.append(
                            (
                                f"Question {index} "
                                "has no valid answer."
                            )
                        )

                # =================================================
                # SHOW VALIDATION ERRORS
                # =================================================

                if errors:

                    for error in errors[:10]:

                        messages.error(
                            request,
                            error,
                        )

                    return render(
                        request,
                        "academy/tutor/quiz/import_docx.html",
                        {
                            "lesson": lesson,
                            "quiz": quiz,
                        },
                    )

                # =================================================
                # FIND NEXT ORDER
                # =================================================

                last_question = (
                    QuizQuestion.objects
                    .filter(
                        quiz=quiz
                    )
                    .order_by(
                        "-question_order"
                    )
                    .first()
                )

                if last_question:

                    next_order = (
                        last_question.question_order
                        + 1
                    )

                else:

                    next_order = 1

                # =================================================
                # DATABASE TRANSACTION
                # =================================================

                with transaction.atomic():

                    imported_count = 0

                    for item in parsed_questions:

                        options = item[
                            "options"
                        ]

                        # =========================================
                        # DETECT TRUE/FALSE
                        # =========================================

                        option_values = []

                        for option in options:

                            clean_text = (
                                _html_to_text(
                                    option["text"]
                                )
                                .strip()
                                .lower()
                            )

                            option_values.append(
                                clean_text
                            )

                        is_true_false = (
                            len(options) == 2
                            and set(
                                option_values
                            ) == {
                                "true",
                                "false",
                            }
                        )

                        question_type = (
                            "TF"
                            if is_true_false
                            else "MCQ"
                        )

                        # =========================================
                        # CREATE QUESTION
                        # =========================================

                        question = (
                            QuizQuestion.objects.create(
                                quiz=quiz,

                                question=(
                                    item[
                                        "question"
                                    ]
                                ),

                                question_type=(
                                    question_type
                                ),

                                points=(
                                    item[
                                        "points"
                                    ]
                                ),

                                question_order=(
                                    next_order
                                ),
                            )
                        )

                        # =========================================
                        # CREATE OPTIONS
                        # =========================================

                        for (
                            option_index,
                            option,
                        ) in enumerate(
                            options,
                            start=1,
                        ):

                            QuizOption.objects.create(

                                question=question,

                                text=option[
                                    "text"
                                ],

                                is_correct=(
                                    option[
                                        "letter"
                                    ]
                                    == item[
                                        "answer"
                                    ]
                                ),

                                option_order=(
                                    option_index
                                ),
                            )

                        next_order += 1

                        imported_count += 1

                # =================================================
                # SUCCESS
                # =================================================

                messages.success(
                    request,
                    (
                        f"{imported_count} "
                        f"question"
                        f"{'s' if imported_count != 1 else ''} "
                        "imported successfully."
                    ),
                )

                return redirect(
                    "tutor-quiz-edit",
                    lesson_id=lesson.id,
                )

        # =========================================================
        # ERROR
        # =========================================================

        except Exception as exc:

            messages.error(
                request,
                (
                    "The Word document could not "
                    "be imported. "
                    f"Error: {exc}"
                ),
            )

            return render(
                request,
                "academy/tutor/quiz/import_docx.html",
                {
                    "lesson": lesson,
                    "quiz": quiz,
                },
            )

        # =========================================================
        # DELETE TEMP FILE
        # =========================================================

        finally:

            try:

                if default_storage.exists(
                    temp_path
                ):

                    default_storage.delete(
                        temp_path
                    )

            except Exception:

                pass

    # =========================================================
    # GET
    # =========================================================

    return render(
        request,
        "academy/tutor/quiz/import_docx.html",
        {
            "lesson": lesson,
            "quiz": quiz,
        },
    )
    

@tutor_required
@require_POST
def tutor_lesson_delete(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__tutor=request.user,
    )

    course_id = lesson.course_id
    lesson.delete()

    messages.success(request, "Lesson deleted successfully.")
    return redirect(
        "tutor-course-detail",
        course_id=course_id,
    )


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user,
    )
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect("profile")


class AcademyPasswordResetView(PasswordResetView):
    template_name = "academy/auth/password_reset.html"
    email_template_name = "academy/auth/password_reset_email.txt"
    subject_template_name = "academy/auth/password_reset_subject.txt"
    success_url = reverse_lazy("password-reset-done")


class AcademyPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "academy/auth/password_reset_confirm.html"
    success_url = reverse_lazy("login")




import os
import uuid

from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .decorators import tutor_required


@tutor_required
@require_POST
def tutor_ckeditor_image_upload(request):

    image = request.FILES.get("upload")

    if not image:
        return JsonResponse(
            {
                "error": {
                    "message": "No image was uploaded."
                }
            },
            status=400,
        )

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    }

    if image.content_type not in allowed_types:
        return JsonResponse(
            {
                "error": {
                    "message": "Unsupported image type. Please upload JPG, PNG, GIF or WebP."
                }
            },
            status=400,
        )

    max_size = 5 * 1024 * 1024

    if image.size > max_size:
        return JsonResponse(
            {
                "error": {
                    "message": "Image is too large. Maximum size is 5 MB."
                }
            },
            status=400,
        )

    extension = os.path.splitext(image.name)[1].lower()

    filename = f"{uuid.uuid4().hex}{extension}"

    upload_path = f"ckeditor/quiz/{filename}"

    saved_path = default_storage.save(
        upload_path,
        image,
    )

    image_url = default_storage.url(saved_path)

    return JsonResponse({
        "url": image_url
    })



from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import student_required
from .models import (
    Quiz,
    QuizQuestion,
    QuizAttempt,
    QuizAnswer,
)

@student_required
def student_quiz_attempt(request, quiz_id):

    quiz = get_object_or_404(
        Quiz.objects.select_related(
            "lesson",
            "lesson__course",
        ).prefetch_related(
            "questions__options"
        ),
        id=quiz_id,
        is_published=True,
    )

    lesson = quiz.lesson

    questions = list(
        quiz.questions.all().order_by(
            "question_order",
            "id",
        )
    )

    if not questions:
        messages.info(
            request,
            "This quiz does not have any questions yet.",
        )

        return redirect(
            "lesson-detail",
            lesson_id=lesson.id,
        )

    # ---------------------------------------------------------
    # CHECK MAXIMUM ATTEMPTS
    # ---------------------------------------------------------

    previous_attempts = QuizAttempt.objects.filter(
        quiz=quiz,
        student=request.user,
    ).count()

    if (
        quiz.max_attempts
        and previous_attempts >= quiz.max_attempts
        and request.method == "GET"
    ):
        messages.warning(
            request,
            "You have reached the maximum number of attempts for this quiz.",
        )

        latest_attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            student=request.user,
        ).first()

        if latest_attempt:
            return redirect(
                "student-quiz-result",
                attempt_id=latest_attempt.id,
            )

        return redirect(
            "lesson-detail",
            lesson_id=lesson.id,
        )

    # ---------------------------------------------------------
    # SUBMIT QUIZ
    # ---------------------------------------------------------

    if request.method == "POST":

        # Re-check attempts because this is the important
        # server-side protection.
        previous_attempts = QuizAttempt.objects.filter(
            quiz=quiz,
            student=request.user,
        ).count()

        if (
            quiz.max_attempts
            and previous_attempts >= quiz.max_attempts
        ):
            messages.warning(
                request,
                "You have reached the maximum number of attempts for this quiz.",
            )

            latest_attempt = QuizAttempt.objects.filter(
                quiz=quiz,
                student=request.user,
            ).first()

            if latest_attempt:
                return redirect(
                    "student-quiz-result",
                    attempt_id=latest_attempt.id,
                )

            return redirect(
                "lesson-detail",
                lesson_id=lesson.id,
            )

        attempt_number = previous_attempts + 1

        total_points = sum(
            question.points
            for question in questions
        )

        earned_points = 0

        with transaction.atomic():

            attempt = QuizAttempt.objects.create(
                quiz=quiz,
                student=request.user,
                attempt_number=attempt_number,
                total_points=total_points,
                score=0,
                percentage=0,
                passed=False,
            )

            for question in questions:

                selected_option_id = request.POST.get(
                    f"question_{question.id}"
                )

                selected_option = None

                if selected_option_id:

                    try:
                        selected_option_id = int(
                            selected_option_id
                        )
                    except (
                        TypeError,
                        ValueError,
                    ):
                        selected_option_id = None

                if selected_option_id:

                    selected_option = next(
                        (
                            option
                            for option in question.options.all()
                            if option.id == selected_option_id
                        ),
                        None,
                    )

                correct_option = next(
                    (
                        option
                        for option in question.options.all()
                        if option.is_correct
                    ),
                    None,
                )

                is_correct = (
                    selected_option is not None
                    and correct_option is not None
                    and selected_option.id == correct_option.id
                )

                points_earned = (
                    question.points
                    if is_correct
                    else 0
                )

                if is_correct:
                    earned_points += question.points

                QuizAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_option=selected_option,
                    correct_option=correct_option,
                    is_correct=is_correct,
                    points_earned=points_earned,
                )

            percentage = (
                round(
                    (earned_points / total_points) * 100,
                    2,
                )
                if total_points
                else 0
            )

            passed = percentage >= quiz.pass_mark

            attempt.score = earned_points
            attempt.percentage = percentage
            attempt.passed = passed
            attempt.submitted_at = timezone.now()

            attempt.save()

        messages.success(
            request,
            "Quiz submitted successfully.",
        )

        return redirect(
            "student-quiz-result",
            attempt_id=attempt.id,
        )

    # ---------------------------------------------------------
    # SHOW QUIZ
    # ---------------------------------------------------------

    return render(
        request,
        "academy/student/quiz_att.html",
        {
            "quiz": quiz,
            "lesson": lesson,
            "questions": questions,
        },
    )




@student_required
def student_quiz_result(request, attempt_id):

    attempt = get_object_or_404(
        QuizAttempt.objects.select_related(
            "quiz",
            "quiz__lesson",
            "quiz__lesson__course",
        ).prefetch_related(
            "answers__question",
            "answers__selected_option",
            "answers__correct_option",
        ),
        id=attempt_id,
        student=request.user,
    )

    answers = list(
        attempt.answers.all().order_by(
            "question__question_order",
            "id",
        )
    )

    return render(
        request,
        "academy/student/quiz_result.html",
        {
            "attempt": attempt,
            "quiz": attempt.quiz,
            "lesson": attempt.quiz.lesson,
            "answers": answers,
        },
    )