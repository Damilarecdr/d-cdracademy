from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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
    Quiz,
    QuizQuestion,
    QuizOption,
  
)


# =========================================================
# USER ADMIN
# =========================================================

@admin.register(User)
class AcademyUserAdmin(UserAdmin):
    ordering = ("email",)

    list_display = (
        "email",
        "get_full_name",
        "role",
        "is_active",
        "is_suspended",
        "is_staff",
    )

    list_filter = (
        "role",
        "is_active",
        "is_suspended",
        "is_staff",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

    fieldsets = (
        (None, {
            "fields": (
                "email",
                "password",
            )
        }),

        ("Personal information", {
            "fields": (
                "first_name",
                "last_name",
            )
        }),

        ("Role & status", {
            "fields": (
                "role",
                "is_suspended",
            )
        }),

        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Important dates", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "first_name",
                "last_name",
                "role",
                "is_active",
                "is_staff",
                "is_superuser",
            ),
        }),
    )

    def get_full_name(self, obj):
        return obj.get_full_name() or "—"

    get_full_name.short_description = "Full name"


# =========================================================
# STUDENT PROFILE
# =========================================================

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "phone",
        "updated_at",
    )

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
    )

    autocomplete_fields = (
        "user",
    )


# =========================================================
# TUTOR PROFILE
# =========================================================

@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "qualification",
        "specialization",
        "updated_at",
    )

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "specialization",
    )

    autocomplete_fields = (
        "user",
    )


# =========================================================
# COURSE
# =========================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):

    list_display = (
        "course_code",
        "title",
        "category",
        "display_university_category",
        "display_university_program",
        "university_level",
        "tutor",
        "is_active",
        "lesson_count",
        "created_at",
    )

    list_filter = (
        "category",
        "jamb_category",
        "alevel_category",
        "university_category",
        "university_program",
        "university_level",
        "is_active",
    )

    search_fields = (
        "course_code",
        "title",
        "description",
        "university_program",
        "tutor__email",
        "tutor__first_name",
        "tutor__last_name",
    )

    autocomplete_fields = (
        "tutor",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "lesson_count",
    )

    ordering = (
        "category",
        "university_category",
        "university_program",
        "university_level",
        "title",
    )

    fieldsets = (
        ("Basic Course Information", {
            "fields": (
                "title",
                "course_code",
                "description",
                "thumbnail",
                "is_active",
            )
        }),

        ("Course Classification", {
            "fields": (
                "category",
                "jamb_category",
                "alevel_category",
                "university_category",
                "university_program",
                "university_level",
            )
        }),

        ("Course Tutor", {
            "fields": (
                "tutor",
            )
        }),

        ("Course Statistics", {
            "fields": (
                "lesson_count",
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="University Category")
    def display_university_category(self, obj):
        if obj.university_category:
            return obj.get_university_category_display()
        return "—"

    @admin.display(description="Programme")
    def display_university_program(self, obj):
        if obj.university_program:
            programs = dict(
                Course.SCIENCE_PROGRAM_CHOICES +
                Course.ENGINEERING_PROGRAM_CHOICES
            )
            return programs.get(
                obj.university_program,
                obj.university_program
            )
        return "—"


# =========================================================
# LESSON
# =========================================================

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "lesson_order",
        "title",
        "is_published",
        "duration",
        "has_quiz",
        "updated_at",
    )

    list_filter = (
        "is_published",
        "course__category",
        "course",
    )

    search_fields = (
        "title",
        "description",
        "course__title",
        "course__course_code",
    )

    autocomplete_fields = (
        "course",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "course",
        "lesson_order",
    )

    def has_quiz(self, obj):
        return hasattr(obj, "quiz")

    has_quiz.boolean = True
    has_quiz.short_description = "Quiz"


# =========================================================
# QUIZ
# =========================================================

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lesson",
        "get_course",
        "question_count",
        "pass_mark",
        "time_limit",
        "max_attempts",
        "is_published",
        "updated_at",
    )

    list_filter = (
        "is_published",
        "lesson__course__category",
        "lesson__course",
    )

    search_fields = (
        "title",
        "description",
        "lesson__title",
        "lesson__course__title",
        "lesson__course__course_code",
    )

    autocomplete_fields = (
        "lesson",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "lesson__course",
        "lesson__lesson_order",
    )

    def get_course(self, obj):
        return obj.lesson.course

    get_course.short_description = "Course"


# =========================================================
# QUIZ OPTION INLINE
# =========================================================

class QuizOptionInline(admin.TabularInline):
    model = QuizOption
    extra = 4
    min_num = 2
    max_num = 6

    fields = (
        "option_order",
        "text",
        "is_correct",
    )

    ordering = (
        "option_order",
        "id",
    )


# =========================================================
# QUIZ QUESTION
# =========================================================

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "quiz",
        "question_order",
        "short_question",
        "question_type",
        "points",
        "option_count",
    )

    list_filter = (
        "question_type",
        "quiz__lesson__course__category",
        "quiz",
    )

    search_fields = (
        "question",
        "quiz__title",
        "quiz__lesson__title",
        "quiz__lesson__course__title",
    )

    autocomplete_fields = (
        "quiz",
    )

    ordering = (
        "quiz",
        "question_order",
    )

    inlines = (
        QuizOptionInline,
    )

    def short_question(self, obj):
        if len(obj.question) > 80:
            return f"{obj.question[:80]}..."
        return obj.question

    short_question.short_description = "Question"

    def option_count(self, obj):
        return obj.options.count()

    option_count.short_description = "Options"





# =========================================================
# COURSE REGISTRATION
# =========================================================

@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "registered_at",
    )

    list_filter = (
        "course__category",
        "course",
        "registered_at",
    )

    search_fields = (
        "student__email",
        "student__first_name",
        "student__last_name",
        "course__title",
        "course__course_code",
    )

    autocomplete_fields = (
        "student",
        "course",
    )


# =========================================================
# LESSON PROGRESS
# =========================================================

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "lesson",
        "completed",
        "completed_at",
        "last_viewed",
    )

    list_filter = (
        "completed",
        "lesson__course__category",
        "lesson__course",
    )

    search_fields = (
        "student__email",
        "student__first_name",
        "student__last_name",
        "lesson__title",
        "lesson__course__title",
    )

    autocomplete_fields = (
        "student",
        "lesson",
    )

    ordering = (
        "-last_viewed",
    )


# =========================================================
# NOTIFICATION
# =========================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "recipient",
        "title",
        "is_read",
        "created_at",
    )

    list_filter = (
        "is_read",
        "created_at",
    )

    search_fields = (
        "recipient__email",
        "recipient__first_name",
        "recipient__last_name",
        "title",
        "message",
    )

    autocomplete_fields = (
        "recipient",
    )

    ordering = (
        "-created_at",
    )


# =========================================================
# PLATFORM SETTINGS
# =========================================================

@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "university_course_limit",
        "updated_at",
    )

    readonly_fields = (
        "updated_at",
    )

    def has_add_permission(self, request):
        return not PlatformSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False