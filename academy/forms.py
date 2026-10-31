from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Course, Lesson, StudentProfile, TutorProfile, User



class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    role = forms.ChoiceField(
        choices=[
            ("JAMB", "JAMB"),
            ("ALEVEL", "A-Level"),
            ("UNIVERSITY", "University"),
            ("TUTOR", "Tutor"),
        ]
    )

    # JAMB Category
    jamb_category = forms.ChoiceField(
        choices=[
            ("SCIENCE", "Science"),
            ("ARTS", "Arts"),
            ("COMMERCIAL", "Commercial"),
        ],
        required=False
    )

    # A-Level Category
    alevel_category = forms.ChoiceField(
        choices=[
            ("SCIENCE", "Science"),
            ("ARTS", "Arts"),
            ("SOCIAL_SCIENCE", "Social Science"),
        ],
        required=False
    )

    # University Category
    university_category = forms.ChoiceField(
        choices=[
            ("SCIENCE", "Science"),
            ("ENGINEERING", "Engineering"),
        ],
        required=False
    )

    # University Level
    university_level = forms.ChoiceField(
        choices=[
            ("100", "100 Level"),
            ("200", "200 Level"),
            ("300", "300 Level"),
            ("400", "400 Level"),
            ("500", "500 Level"),
            ("600", "600 Level"),
        ],
        required=False
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean(self):
        cleaned = super().clean()

        password = cleaned.get("password")
        confirm = cleaned.get("confirm_password")
        role = cleaned.get("role")

        # Password confirmation
        if password and confirm and password != confirm:
            self.add_error(
                "confirm_password",
                "Passwords do not match."
            )

        # Password validation
        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error("password", exc)

        # JAMB validation
        if role == "JAMB":
            if not cleaned.get("jamb_category"):
                self.add_error(
                    "jamb_category",
                    "Please select your JAMB category."
                )

        # A-Level validation
        elif role == "ALEVEL":
            if not cleaned.get("alevel_category"):
                self.add_error(
                    "alevel_category",
                    "Please select your A-Level category."
                )

        # University validation
        elif role == "UNIVERSITY":

            if not cleaned.get("university_category"):
                self.add_error(
                    "university_category",
                    "Please select your university category."
                )

            if not cleaned.get("university_level"):
                self.add_error(
                    "university_level",
                    "Please select your university level."
                )

        return cleaned



class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")

        if email and password:
            user = authenticate(
                username=email.strip().lower(),
                password=password,
            )
            if user is None:
                raise forms.ValidationError("Invalid email or password.")
            if not user.is_active:
                raise forms.ValidationError("This account is inactive.")
            if user.is_suspended:
                raise forms.ValidationError("This account has been suspended.")
            cleaned["user"] = user

        return cleaned


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["profile_picture", "phone", "bio"]


class TutorProfileForm(forms.ModelForm):
    class Meta:
        model = TutorProfile
        fields = ["profile_picture", "qualification", "specialization", "bio"]


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "course_code",
            "description",
            "category",
            "tutor",
            "thumbnail",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tutor"].queryset = User.objects.filter(
            role="TUTOR",
            is_active=True,
            is_suspended=False,
        )


class TutorLessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "video",
            "video_url",
            "material",
            "lesson_order",
            "duration",
            "is_published",
        ]

    def clean(self):
        cleaned = super().clean()
        video = cleaned.get("video")
        video_url = cleaned.get("video_url")

        if not video and not video_url:
            raise forms.ValidationError("Provide a video file or a video URL.")

        return cleaned


class UniversityLimitForm(forms.Form):
    university_course_limit = forms.IntegerField(min_value=1, max_value=100)


class ProfilePasswordChangeForm(PasswordChangeForm):
    pass


class PasswordResetRequestForm(PasswordResetForm):
    pass


class LoginPasswordResetConfirmForm(SetPasswordForm):
    pass
