from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


def validate_video_size(file):
    if file and file.size > 500 * 1024 * 1024:
        raise ValidationError("Video files must not exceed 500 MB.")


def validate_material_size(file):
    if file and file.size > 20 * 1024 * 1024:
        raise ValidationError("Learning materials must not exceed 20 MB.")


def validate_image_size(file):
    if file and file.size > 5 * 1024 * 1024:
        raise ValidationError("Images must not exceed 5 MB.")


class UserManager(UserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "ADMIN")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("role") != "ADMIN":
            raise ValueError("Superuser role must be ADMIN.")
        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)



from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    ROLE_CHOICES = [
        ("JAMB", "JAMB"),
        ("ALEVEL", "A-Level"),
        ("UNIVERSITY", "University"),
        ("TUTOR", "Tutor"),
        ("ADMIN", "Administrator"),
    ]

    JAMB_CATEGORY_CHOICES = [
        ("SCIENCE", "Science"),
        ("ARTS", "Arts"),
        ("COMMERCIAL", "Commercial"),
    ]

    ALEVEL_CATEGORY_CHOICES = [
        ("SCIENCE", "Science"),
        ("ARTS", "Arts"),
        ("SOCIAL_SCIENCE", "Social Science"),
    ]

    UNIVERSITY_CATEGORY_CHOICES = [
        ("SCIENCE", "Science"),
        ("ENGINEERING", "Engineering"),
    ]

    UNIVERSITY_LEVEL_CHOICES = [
        ("100", "100 Level"),
        ("200", "200 Level"),
        ("300", "300 Level"),
        ("400", "400 Level"),
        ("500", "500 Level"),
        ("600", "600 Level"),
    ]

    SCIENCE_PROGRAM_CHOICES = [
        ("CHEMISTRY", "Chemistry"),
        ("PHYSICS", "Physics"),
        ("BIOCHEMISTRY", "Biochemistry"),
        ("MICROBIOLOGY", "Microbiology"),
        ("BIOLOGY", "Biology"),
        ("MATHEMATICS", "Mathematics"),
        ("COMPUTER_SCIENCE", "Computer Science"),
        ("STATISTICS", "Statistics"),
        ("BOTANY", "Botany"),
        ("ZOOLOGY", "Zoology"),
    ]

    ENGINEERING_PROGRAM_CHOICES = [
        ("ELECTRICAL_ENGINEERING", "Electrical Engineering"),
        ("MECHANICAL_ENGINEERING", "Mechanical Engineering"),
        ("CIVIL_ENGINEERING", "Civil Engineering"),
        ("COMPUTER_ENGINEERING", "Computer Engineering"),
        ("CHEMICAL_ENGINEERING", "Chemical Engineering"),
        ("AGRICULTURAL_ENGINEERING", "Agricultural Engineering"),
        ("MECHATRONICS_ENGINEERING", "Mechatronics Engineering"),
        ("BIOMEDICAL_ENGINEERING", "Biomedical Engineering"),
        ("PETROLEUM_ENGINEERING", "Petroleum Engineering"),
    ]

    username = None

    email = models.EmailField(unique=True, db_index=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="UNIVERSITY"
    )

    # JAMB category
    jamb_category = models.CharField(
        max_length=20,
        choices=JAMB_CATEGORY_CHOICES,
        blank=True,
        null=True
    )

    # A-Level category
    alevel_category = models.CharField(
        max_length=20,
        choices=ALEVEL_CATEGORY_CHOICES,
        blank=True,
        null=True
    )

    # University category
    university_category = models.CharField(
        max_length=20,
        choices=UNIVERSITY_CATEGORY_CHOICES,
        blank=True,
        null=True
    )

    # University programme
    university_program = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # University level
    university_level = models.CharField(
        max_length=10,
        choices=UNIVERSITY_LEVEL_CHOICES,
        blank=True,
        null=True
    )

    is_suspended = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.email})"

    @property
    def is_student(self):
        return self.role in {"JAMB", "ALEVEL", "UNIVERSITY"}

    @property
    def available_university_programs(self):
        if self.university_category == "SCIENCE":
            return self.SCIENCE_PROGRAM_CHOICES

        if self.university_category == "ENGINEERING":
            return self.ENGINEERING_PROGRAM_CHOICES

        return []

    def save(self, *args, **kwargs):

        if self.is_superuser:
            self.role = "ADMIN"

        # Clear university-specific fields for non-university users
        if self.role != "UNIVERSITY":
            self.university_category = None
            self.university_program = None
            self.university_level = None

        # Clear programme when category changes to an incompatible option
        valid_programs = dict(self.available_university_programs)

        if self.university_program not in valid_programs:
            self.university_program = None

        super().save(*args, **kwargs)



class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    profile_picture = models.ImageField(
        upload_to="profiles/students/",
        blank=True,
        null=True,
        validators=[validate_image_size, FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Student Profile: {self.user.email}"


class TutorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="tutor_profile")
    nickname = models.CharField(max_length=200, blank=True)
    whatsApp_number =models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(
        upload_to="profiles/tutors/",
        blank=True,
        null=True,
        validators=[validate_image_size, FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    qualification = models.CharField(max_length=255, blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tutor Profile: {self.user.email}"


class PlatformSettings(models.Model):
    university_course_limit = models.PositiveIntegerField(
        default=6,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform Settings"
        verbose_name_plural = "Platform Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Platform Settings"




class Course(models.Model):

    # ==========================================
    # CATEGORY CHOICES
    # ==========================================

    CATEGORY_CHOICES = [
        ("JAMB", "JAMB"),
        ("ALEVEL", "A-Level"),
        ("UNIVERSITY", "University"),
    ]

    JAMB_CATEGORY_CHOICES = [
        ("SCIENCE", "Science"),
        ("ARTS", "Arts"),
        ("COMMERCIAL", "Commercial"),
    ]

    ALEVEL_CATEGORY_CHOICES = [
        ("SCIENCE", "Science"),
        ("ARTS", "Arts"),
        ("SOCIAL_SCIENCE", "Social Science"),
    ]

    UNIVERSITY_CATEGORY_CHOICES = [
        ("SCIENCE", "Science"),
        ("ENGINEERING", "Engineering"),
    ]

    UNIVERSITY_LEVEL_CHOICES = [
        ("100", "100 Level"),
        ("200", "200 Level"),
        ("300", "300 Level"),
        ("400", "400 Level"),
        ("500", "500 Level"),
        ("600", "600 Level"),
    ]

    # ==========================================
    # UNIVERSITY PROGRAMME CHOICES
    # ==========================================

    SCIENCE_PROGRAM_CHOICES = [
        ("CHEMISTRY", "Chemistry"),
        ("PHYSICS", "Physics"),
        ("BIOCHEMISTRY", "Biochemistry"),
        ("MICROBIOLOGY", "Microbiology"),
        ("BIOLOGY", "Biology"),
        ("MATHEMATICS", "Mathematics"),
        ("COMPUTER_SCIENCE", "Computer Science"),
        ("STATISTICS", "Statistics"),
        ("BOTANY", "Botany"),
        ("ZOOLOGY", "Zoology"),
    ]

    ENGINEERING_PROGRAM_CHOICES = [
        ("ELECTRICAL_ENGINEERING", "Electrical Engineering"),
        ("MECHANICAL_ENGINEERING", "Mechanical Engineering"),
        ("CIVIL_ENGINEERING", "Civil Engineering"),
        ("COMPUTER_ENGINEERING", "Computer Engineering"),
        ("CHEMICAL_ENGINEERING", "Chemical Engineering"),
        ("AGRICULTURAL_ENGINEERING", "Agricultural Engineering"),
        ("MECHATRONICS_ENGINEERING", "Mechatronics Engineering"),
        ("BIOMEDICAL_ENGINEERING", "Biomedical Engineering"),
        ("PETROLEUM_ENGINEERING", "Petroleum Engineering"),
    ]

    UNIVERSITY_PROGRAM_CHOICES = (
        SCIENCE_PROGRAM_CHOICES +
        ENGINEERING_PROGRAM_CHOICES
    )

    # ==========================================
    # BASIC COURSE INFORMATION
    # ==========================================

    title = models.CharField(
        max_length=200
    )

    course_code = models.CharField(
        max_length=50,
        unique=True
    )

    description = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    # ==========================================
    # JAMB CATEGORY
    # ==========================================

    jamb_category = models.CharField(
        max_length=20,
        choices=JAMB_CATEGORY_CHOICES,
        blank=True,
        null=True
    )

    # ==========================================
    # A-LEVEL CATEGORY
    # ==========================================

    alevel_category = models.CharField(
        max_length=20,
        choices=ALEVEL_CATEGORY_CHOICES,
        blank=True,
        null=True
    )

    # ==========================================
    # UNIVERSITY CATEGORY
    # ==========================================

    university_category = models.CharField(
        max_length=20,
        choices=UNIVERSITY_CATEGORY_CHOICES,
        blank=True,
        null=True
    )

    # ==========================================
    # UNIVERSITY PROGRAMME
    # ==========================================

    university_program = models.CharField(
        max_length=50,
        choices=UNIVERSITY_PROGRAM_CHOICES,
        blank=True,
        null=True
    )

    # ==========================================
    # UNIVERSITY LEVEL
    # ==========================================

    university_level = models.CharField(
        max_length=10,
        choices=UNIVERSITY_LEVEL_CHOICES,
        blank=True,
        null=True
    )

    # ==========================================
    # COURSE TUTOR
    # ==========================================

    tutor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_courses",
        limit_choices_to={"role": "TUTOR"},
    )

    # ==========================================
    # COURSE THUMBNAIL
    # ==========================================

    thumbnail = models.ImageField(
        upload_to="course_thumbnails/",
        blank=True,
        null=True,
        validators=[
            validate_image_size,
            FileExtensionValidator(
                ["jpg", "jpeg", "png", "webp"]
            )
        ],
    )

    # ==========================================
    # COURSE STATUS
    # ==========================================

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ==========================================
    # MODEL META
    # ==========================================

    class Meta:
        ordering = [
            "category",
            "title"
        ]

    # ==========================================
    # MODEL VALIDATION
    # ==========================================

    def clean(self):
        super().clean()

        errors = {}

        # Validate assigned tutor
        if self.tutor and self.tutor.role != "TUTOR":
            errors["tutor"] = (
                "Only users with the Tutor role can be assigned to a course."
            )

        # --------------------------------------
        # JAMB VALIDATION
        # --------------------------------------

        if self.category == "JAMB":

            if not self.jamb_category:
                errors["jamb_category"] = (
                    "Please select a JAMB category."
                )

        elif self.jamb_category:
            errors["jamb_category"] = (
                "JAMB category is only applicable to JAMB courses."
            )

        # --------------------------------------
        # A-LEVEL VALIDATION
        # --------------------------------------

        if self.category == "ALEVEL":

            if not self.alevel_category:
                errors["alevel_category"] = (
                    "Please select an A-Level category."
                )

        elif self.alevel_category:
            errors["alevel_category"] = (
                "A-Level category is only applicable to A-Level courses."
            )

        # --------------------------------------
        # UNIVERSITY VALIDATION
        # --------------------------------------

        if self.category == "UNIVERSITY":

            if not self.university_category:
                errors["university_category"] = (
                    "Please select a university category."
                )

            if not self.university_program:
                errors["university_program"] = (
                    "Please select a university programme."
                )

            if not self.university_level:
                errors["university_level"] = (
                    "Please select a university level."
                )

            # Validate programme against category

            science_programs = {
                value for value, label
                in self.SCIENCE_PROGRAM_CHOICES
            }

            engineering_programs = {
                value for value, label
                in self.ENGINEERING_PROGRAM_CHOICES
            }

            if self.university_category == "SCIENCE":

                valid_programs = science_programs

            elif self.university_category == "ENGINEERING":

                valid_programs = engineering_programs

            else:

                valid_programs = set()

            if (
                self.university_program
                and self.university_program not in valid_programs
            ):
                errors["university_program"] = (
                    "The selected programme does not belong "
                    "to the selected university category."
                )

        else:

            if self.university_category:
                errors["university_category"] = (
                    "University category is only applicable "
                    "to University courses."
                )

            if self.university_program:
                errors["university_program"] = (
                    "University programme is only applicable "
                    "to University courses."
                )

            if self.university_level:
                errors["university_level"] = (
                    "University level is only applicable "
                    "to University courses."
                )

        # --------------------------------------
        # RAISE VALIDATION ERRORS
        # --------------------------------------

        if errors:
            raise ValidationError(errors)

    # ==========================================
    # STRING REPRESENTATION
    # ==========================================

    def __str__(self):
        return f"{self.course_code} — {self.title}"

    # ==========================================
    # PUBLISHED LESSON COUNT
    # ==========================================

    @property
    def lesson_count(self):
        return self.lessons.filter(
            is_published=True
        ).count()

    # ==========================================
    # AVAILABLE UNIVERSITY PROGRAMMES
    # ==========================================

    @property
    def available_university_programs(self):

        if self.university_category == "SCIENCE":
            return self.SCIENCE_PROGRAM_CHOICES

        elif self.university_category == "ENGINEERING":
            return self.ENGINEERING_PROGRAM_CHOICES

        return []


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video = models.FileField(
        upload_to="lesson_videos/",
        blank=True,
        null=True,
        validators=[validate_video_size, FileExtensionValidator(["mp4", "webm", "ogg", "mov"])],
    )
    video_url = models.URLField(blank=True)
    material = models.FileField(
        upload_to="lesson_materials/",
        blank=True,
        null=True,
        validators=[validate_material_size, FileExtensionValidator(["pdf"])],
    )
    lesson_order = models.PositiveIntegerField(default=1)
    duration = models.PositiveIntegerField(default=0, help_text="Duration in minutes")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "lesson_order"],
                name="unique_course_lesson_order",
            )
        ]

    def clean(self):
        if not self.video and not self.video_url:
            raise ValidationError("Provide either a video file or a video URL.")

    def __str__(self):
        return f"{self.course.course_code}: {self.lesson_order}. {self.title}"


class CourseRegistration(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="course_registrations",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-registered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course",
            )
        ]

    def clean(self):
        if not self.student.is_student:
            raise ValidationError({"student": "Only students can register for courses."})

        if self.course.category != self.student.role:
            raise ValidationError({
                "course": f"This course is for {self.course.get_category_display()} students."
            })

    def __str__(self):
        return f"{self.student.email} → {self.course.course_code}"







# ==========================================================
# QUIZ
# ==========================================================

class Quiz(models.Model):
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name="quiz",
    )

    title = models.CharField(
        max_length=200,
        default="Lesson Quiz",
    )

    description = models.TextField(
        blank=True,
        help_text="Instructions shown to students before starting the quiz.",
    )

    pass_mark = models.PositiveIntegerField(
        default=50,
        help_text="Minimum percentage required to pass.",
    )

    time_limit = models.PositiveIntegerField(
        default=0,
        help_text="Time limit in minutes. Use 0 for no time limit.",
    )

    max_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Maximum attempts. Use 0 for unlimited attempts.",
    )

    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson"]

    def clean(self):
        if self.pass_mark > 100:
            raise ValidationError({
                "pass_mark": "Pass mark cannot exceed 100%."
            })

    @property
    def question_count(self):
        return self.questions.count()

    def __str__(self):
        return f"{self.lesson.title} — {self.title}"

class QuizQuestion(models.Model):
    QUESTION_TYPES = [
        ("MCQ", "Multiple Choice"),
        ("TF", "True / False"),
    ]

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    question = models.TextField()

    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES,
        default="MCQ",
    )

    points = models.PositiveIntegerField(
        default=1,
    )

    question_order = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["question_order", "id"]

        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "question_order"],
                name="unique_quiz_question_order",
            )
        ]

    def __str__(self):
        return f"{self.quiz.title}: Question {self.question_order}"


class QuizOption(models.Model):
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name="options",
    )

    # TextField is recommended for CKEditor HTML
    text = models.TextField()

    is_correct = models.BooleanField(
        default=False,
    )

    option_order = models.PositiveIntegerField(
        default=1,
    )

    class Meta:
        ordering = ["option_order", "id"]

    def __str__(self):
        return self.text[:100]





from django.conf import settings
from django.db import models


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(
        "Quiz",
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )

    attempt_number = models.PositiveIntegerField(
        default=1,
    )

    score = models.PositiveIntegerField(
        default=0,
    )

    total_points = models.PositiveIntegerField(
        default=0,
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    passed = models.BooleanField(
        default=False,
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.quiz.title} - "
            f"Attempt {self.attempt_number}"
        )


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    question = models.ForeignKey(
        "QuizQuestion",
        on_delete=models.CASCADE,
        related_name="attempt_answers",
    )

    selected_option = models.ForeignKey(
        "QuizOption",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="selected_answers",
    )

    correct_option = models.ForeignKey(
        "QuizOption",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correct_answers",
    )

    is_correct = models.BooleanField(
        default=False,
    )

    points_earned = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["question__question_order", "id"]

        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="unique_quiz_attempt_question",
            )
        ]

    def __str__(self):
        return (
            f"{self.attempt} - "
            f"Question {self.question.question_order}"
        )

class LessonProgress(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="progress_records",
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_viewed = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_viewed"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "lesson"],
                name="unique_student_lesson_progress",
            )
        ]

    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        if not self.completed:
            self.completed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.email} — {self.lesson.title}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.email}: {self.title}"
