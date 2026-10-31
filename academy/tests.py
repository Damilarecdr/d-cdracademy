from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from .models import (
    Course,
    CourseRegistration,
    Lesson,
    LessonProgress,
    PlatformSettings,
    StudentProfile,
    TutorProfile,
)

User = get_user_model()


class LMSBaseTest(TestCase):
    def setUp(self):
        self.jamb = User.objects.create_user(
            email="jamb@example.com",
            password="StrongPassword123!",
            first_name="Jamb",
            role="JAMB",
        )
        StudentProfile.objects.create(user=self.jamb)

        self.alevel = User.objects.create_user(
            email="alevel@example.com",
            password="StrongPassword123!",
            first_name="Alevel",
            role="ALEVEL",
        )
        StudentProfile.objects.create(user=self.alevel)

        self.university = User.objects.create_user(
            email="uni@example.com",
            password="StrongPassword123!",
            first_name="University",
            role="UNIVERSITY",
        )
        StudentProfile.objects.create(user=self.university)

        self.tutor = User.objects.create_user(
            email="tutor@example.com",
            password="StrongPassword123!",
            first_name="Tutor",
            role="TUTOR",
        )
        TutorProfile.objects.create(user=self.tutor)

        self.other_tutor = User.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
            first_name="Other",
            role="TUTOR",
        )
        TutorProfile.objects.create(user=self.other_tutor)

        self.jamb_courses = [
            Course.objects.create(
                title=f"JAMB Course {i}",
                course_code=f"JAMB{i}",
                description="Test",
                category="JAMB",
                tutor=self.tutor,
            )
            for i in range(1, 6)
        ]

        self.alevel_courses = [
            Course.objects.create(
                title=f"A-Level Course {i}",
                course_code=f"A{i}",
                description="Test",
                category="ALEVEL",
                tutor=self.tutor,
            )
            for i in range(1, 5)
        ]

        PlatformSettings.objects.create(university_course_limit=2)


class RegistrationLimitTests(LMSBaseTest):
    def test_jamb_limit_is_four(self):
        self.client.force_login(self.jamb)

        for course in self.jamb_courses[:4]:
            response = self.client.post(
                reverse("course-register", args=[course.id])
            )
            self.assertEqual(response.status_code, 302)

        response = self.client.post(
            reverse("course-register", args=[self.jamb_courses[4].id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            CourseRegistration.objects.filter(student=self.jamb).count(),
            4,
        )

    def test_alevel_limit_is_three(self):
        self.client.force_login(self.alevel)

        for course in self.alevel_courses[:3]:
            self.client.post(reverse("course-register", args=[course.id]))

        self.client.post(
            reverse("course-register", args=[self.alevel_courses[3].id])
        )

        self.assertEqual(
            CourseRegistration.objects.filter(student=self.alevel).count(),
            3,
        )

    def test_university_limit_is_configurable(self):
        uni_courses = [
            Course.objects.create(
                title=f"University {i}",
                course_code=f"U{i}",
                description="Test",
                category="UNIVERSITY",
                tutor=self.tutor,
            )
            for i in range(3)
        ]

        self.client.force_login(self.university)

        self.client.post(reverse("course-register", args=[uni_courses[0].id]))
        self.client.post(reverse("course-register", args=[uni_courses[1].id]))
        self.client.post(reverse("course-register", args=[uni_courses[2].id]))

        self.assertEqual(
            CourseRegistration.objects.filter(student=self.university).count(),
            2,
        )


class AccessControlTests(LMSBaseTest):
    def test_student_cannot_open_unregistered_course(self):
        self.client.force_login(self.jamb)

        response = self.client.get(
            reverse("course-detail", args=[self.jamb_courses[0].id])
        )
        self.assertEqual(response.status_code, 403)

    def test_student_can_open_registered_course(self):
        CourseRegistration.objects.create(
            student=self.jamb,
            course=self.jamb_courses[0],
        )

        self.client.force_login(self.jamb)

        response = self.client.get(
            reverse("course-detail", args=[self.jamb_courses[0].id])
        )
        self.assertEqual(response.status_code, 200)

    def test_tutor_cannot_edit_another_tutor_course(self):
        other_course = Course.objects.create(
            title="Other Course",
            course_code="OTHER1",
            description="Test",
            category="JAMB",
            tutor=self.other_tutor,
        )
        lesson = Lesson.objects.create(
            course=other_course,
            title="Other Lesson",
            lesson_order=1,
            video_url="https://example.com/video.mp4",
        )

        self.client.force_login(self.tutor)

        response = self.client.get(
            reverse("tutor-lesson-edit", args=[lesson.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_lesson_requires_registration(self):
        lesson = Lesson.objects.create(
            course=self.jamb_courses[0],
            title="Lesson",
            lesson_order=1,
            video_url="https://example.com/video.mp4",
            is_published=True,
        )

        self.client.force_login(self.jamb)

        response = self.client.get(
            reverse("lesson-detail", args=[lesson.id])
        )
        self.assertEqual(response.status_code, 403)


class ProgressTests(LMSBaseTest):
    def test_student_can_complete_registered_lesson(self):
        course = self.jamb_courses[0]
        CourseRegistration.objects.create(
            student=self.jamb,
            course=course,
        )

        lesson = Lesson.objects.create(
            course=course,
            title="Lesson",
            lesson_order=1,
            video_url="https://example.com/video.mp4",
            is_published=True,
        )

        self.client.force_login(self.jamb)

        response = self.client.post(
            reverse("lesson-complete", args=[lesson.id])
        )

        self.assertEqual(response.status_code, 302)
        progress = LessonProgress.objects.get(
            student=self.jamb,
            lesson=lesson,
        )
        self.assertTrue(progress.completed)


class AuthenticationTests(LMSBaseTest):
    def test_login_with_email(self):
        response = self.client.post(
            reverse("login"),
            {
                "email": "jamb@example.com",
                "password": "StrongPassword123!",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_role_dashboard_is_protected(self):
        self.client.force_login(self.tutor)
        response = self.client.get(reverse("jamb-dashboard"))
        self.assertEqual(response.status_code, 403)
