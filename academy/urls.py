from .views import tutor_ckeditor_image_upload

from django.contrib.auth.views import (
    PasswordResetDoneView,
    PasswordResetCompleteView,
)
from django.urls import path

from .views import (
    AcademyPasswordResetConfirmView,
    AcademyPasswordResetView,

    # Student
    alevel_dashboard,
    change_password,
    complete_lesson,
    course_detail,
    course_list,
    dashboard,
    jamb_dashboard,
    lesson_detail,
    login_view,
    logout_view,
    mark_notification_read,
    my_courses,
    profile,
    register_course,
    register_view,
    university_dashboard,
    unregister_course,

    # Tutor
    tutor_course_detail,
    tutor_courses,
    tutor_dashboard,
    tutor_lesson_create,
    tutor_lesson_delete,
    tutor_lesson_edit,
    tutor_students,

    # Tutor Quiz
    tutor_quiz_create,
    tutor_quiz_edit,
    tutor_quiz_question_create,
    tutor_quiz_question_edit,
    tutor_quiz_question_delete,
    student_quiz_attempt,
    student_quiz_result,
    tutor_quiz_questions_import_docx,
    

)


urlpatterns = [

    # =========================================================
    # AUTHENTICATION
    # =========================================================
    path(
    "tutor/quiz/questions/<int:question_id>/delete/",
    tutor_quiz_question_delete,
    name="tutor-quiz-question-delete",
),

    path(
    "student/quiz/<int:quiz_id>/attempt/",
    student_quiz_attempt,
    name="student-quiz-attempt",
),

    path(
    "student/quiz/attempt/<int:attempt_id>/result/",
    student_quiz_result,
    name="student-quiz-result",
),

    path(
        "tutor/lesson/<int:lesson_id>/quiz/questions/import-docx/",
        tutor_quiz_questions_import_docx,
        name="tutor-quiz-questions-import-docx",
    ),
    path(
        "register/",
        register_view,
        name="register",
    ),

    path(
        "login/",
        login_view,
        name="login",
    ),

    path(
        "logout/",
        logout_view,
        name="logout",
    ),



    # =========================================================
    # STUDENT DASHBOARDS
    # =========================================================

    path(
        "dashboard/",
        dashboard,
        name="dashboard",
    ),

    path(
        "dashboard/jamb/",
        jamb_dashboard,
        name="jamb-dashboard",
    ),

    path(
        "dashboard/alevel/",
        alevel_dashboard,
        name="alevel-dashboard",
    ),

    path(
        "dashboard/university/",
        university_dashboard,
        name="university-dashboard",
    ),

    path(
        "dashboard/tutor/",
        tutor_dashboard,
        name="tutor-dashboard",
    ),


    # =========================================================
    # COURSES
    # =========================================================

    path(
        "courses/",
        course_list,
        name="course-list",
    ),

    path(
        "my-courses/",
        my_courses,
        name="my-courses",
    ),

    path(
        "course/<int:course_id>/",
        course_detail,
        name="course-detail",
    ),

    path(
        "course/<int:course_id>/register/",
        register_course,
        name="course-register",
    ),

    path(
        "course/<int:course_id>/unregister/",
        unregister_course,
        name="course-unregister",
    ),


    # =========================================================
    # LESSONS
    # =========================================================

    path(
        "lesson/<int:lesson_id>/",
        lesson_detail,
        name="lesson-detail",
    ),

    path(
        "lesson/<int:lesson_id>/complete/",
        complete_lesson,
        name="lesson-complete",
    ),


    # =========================================================
    # PROFILE
    # =========================================================

    path(
        "profile/",
        profile,
        name="profile",
    ),

    path(
        "profile/password/",
        change_password,
        name="change-password",
    ),


    # =========================================================
    # NOTIFICATIONS
    # =========================================================

    path(
        "notifications/<int:notification_id>/read/",
        mark_notification_read,
        name="notification-read",
    ),


    # =========================================================
    # TUTOR DASHBOARD
    # =========================================================

    path(
        "tutor/dashboard/",
        tutor_dashboard,
        name="tutor-dashboard",
    ),

    path(
        "tutor/courses/",
        tutor_courses,
        name="tutor-courses",
    ),

    path(
        "tutor/course/<int:course_id>/",
        tutor_course_detail,
        name="tutor-course-detail",
    ),

    path(
        "tutor/course/<int:course_id>/students/",
        tutor_students,
        name="tutor-students",
    ),


    # =========================================================
    # TUTOR LESSON MANAGEMENT
    # =========================================================

    # Create lesson
    path(
        "tutor/course/<int:course_id>/lesson/create/",
        tutor_lesson_create,
        name="tutor-lesson-create",
    ),

    # Edit lesson
    path(
        "tutor/lesson/<int:lesson_id>/edit/",
        tutor_lesson_edit,
        name="tutor-lesson-edit",
    ),

    # Delete lesson
    path(
        "tutor/lesson/<int:lesson_id>/delete/",
        tutor_lesson_delete,
        name="tutor-lesson-delete",
    ),


    # =========================================================
    # TUTOR QUIZ MANAGEMENT
    # =========================================================

    # ---------------------------------------------------------
    # Create Quiz
    # ---------------------------------------------------------

    path(
        "tutor/lesson/<int:lesson_id>/quiz/create/",
        tutor_quiz_create,
        name="tutor-quiz-create",
    ),


    # ---------------------------------------------------------
    # Quiz Builder / Edit Quiz
    # ---------------------------------------------------------

    path(
        "tutor/lesson/<int:lesson_id>/quiz/",
        tutor_quiz_edit,
        name="tutor-quiz-edit",
    ),


    # =========================================================
    # TUTOR QUIZ QUESTION MANAGEMENT
    # =========================================================

    # ---------------------------------------------------------
    # Add Question
    # ---------------------------------------------------------

    path(
        "tutor/lesson/<int:lesson_id>/quiz/questions/create/",
        tutor_quiz_question_create,
        name="tutor-quiz-question-create",
    ),


    # ---------------------------------------------------------
    # Edit Question
    # ---------------------------------------------------------

    path(
        "tutor/quiz/questions/<int:question_id>/edit/",
        tutor_quiz_question_edit,
        name="tutor-quiz-question-edit",
    ),


    

    # =========================================================
    # PASSWORD RESET
    # =========================================================

    path(
        "password-reset/",
        AcademyPasswordResetView.as_view(),
        name="password-reset",
    ),

    path(
        "password-reset/done/",
        PasswordResetDoneView.as_view(
            template_name="academy/auth/password_reset_done.html"
        ),
        name="password-reset-done",
    ),

    path(
        "password-reset/<uidb64>/<token>/",
        AcademyPasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),

    path(
        "password-reset/complete/",
        PasswordResetCompleteView.as_view(
            template_name="academy/auth/password_reset_complete.html"
        ),
        name="password-reset-complete",
    ),



    path(
    "tutor/ckeditor/upload/",
    tutor_ckeditor_image_upload,
    name="tutor-ckeditor-image-upload",
),
]