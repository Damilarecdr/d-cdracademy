from django.db import models

from django.db import models


class Navbar(models.Model):
    name = models.CharField(max_length=200, default="EduSphere")
    logo = models.FileField(upload_to="logo/", blank=True, null=True)

    def __str__(self):
        return self.name

from django.db import models

from django.db import models

class HeroSection(models.Model):
    title_main = models.CharField(max_length=200, default="Unlock Your")
    title_gradient = models.CharField(max_length=200, default="Academic Potential")
    title_sub = models.CharField(max_length=200, default="with D-cdr Academy")
    description = models.TextField(default="Access top-quality tutorials tailored for Nigerian university students. Learn at your own pace, anytime, anywhere with our comprehensive learning platform.")
    download_button_text = models.CharField(max_length=50, default="Download Now")
    download_button_link = models.URLField(blank=True, null=True)
    learn_more_button_text = models.CharField(max_length=50, default="Learn More")
    learn_more_button_link = models.URLField(blank=True, null=True)
    background_video = models.FileField(upload_to="hero_videos/", blank=True, null=True)

    def __str__(self):
        return self.title_main


class AcademyAdvertisement(models.Model):

    title = models.CharField(
        max_length=200,
        default="Ready to Excel Academically?"
    )

    label = models.CharField(
        max_length=100,
        default="YOUR SUCCESS STARTS HERE"
    )

    description = models.TextField()

    image = models.ImageField(
        upload_to="advertisements/",
        blank=True,
        null=True
    )

    button_text = models.CharField(
        max_length=100,
        default="Get Started Today"
    )

    button_url = models.CharField(
        max_length=255,
        default="#"
    )

    footer_text = models.CharField(
        max_length=150,
        default="Learn Better. Achieve More."
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Academy Advertisement"
        verbose_name_plural = "Academy Advertisements"

    def __str__(self):
        return self.title

    

class Statistic(models.Model):
    number = models.CharField(max_length=50)
    description = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.number} - {self.description}"




class AboutSection(models.Model):
    title_main = models.CharField(max_length=200, default="Empowering Nigerian Students")
    title_sub = models.CharField(max_length=200, default="to Excel Academically")
    description = models.TextField(default="Brilliant Mind Academy is committed to making learning easier and more accessible, while making it more engaging and effective through quality teaching, structured learning resources and student-centred academic support.")

    def __str__(self):
        return self.title_main




class Feature(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    svg_icon = models.TextField(
        help_text="Paste the full SVG code here. Make sure to use double quotes for attributes."
    )
    color_from = models.CharField(max_length=7, default="#0D0950")  # Tailwind green-400
    color_to = models.CharField(max_length=7, default="#757C0C")    # Tailwind green-500

    def __str__(self):
        return self.title



class Aboutstat(models.Model):
    number = models.CharField(max_length=50)
    description = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.number} - {self.description}"


from django.db import models


class Founder(models.Model):
    name = models.CharField(max_length=150)

    title = models.CharField(
        max_length=200,
        default="Founder, Brilliant Mind Academy"
    )

    photo = models.ImageField(
        upload_to="founder/",
        blank=True,
        null=True
    )

    bio = models.TextField(
        help_text="Write the founder's biography."
    )

    message = models.TextField(
        blank=True,
        null=True,
        help_text="A personal message or quote from the founder."
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Founder"
        verbose_name_plural = "Founder"

    def __str__(self):
        return self.name


class Tutor(models.Model):
    name = models.CharField(max_length=100)
    qualification = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='tutors/')  # Upload photo via admin

    def __str__(self):
        return self.name


    
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

def validate_image_size(image):
    max_size = 5 * 1024 * 1024  # 5MB

    if image.size > max_size:
        raise ValidationError(
            "Image size must not exceed 5MB."
        )



def validate_student_result_image_size(file):
    if file and file.size > 5 * 1024 * 1024:
        raise ValidationError("Student result images must not exceed 5 MB.")


class StudentResult(models.Model):
    EXAM_CHOICES = [
        ("WAEC", "WAEC"),
        ("NECO", "NECO"),
        ("JAMB", "JAMB"),
        ("POST_UTME", "Post UTME"),
        ("A_LEVEL", "A-Level"),
        ("UNIVERSITY", "University Examination"),
        ("OTHER", "Other Achievement"),
    ]

    student_name = models.CharField(
        max_length=200,
        help_text="Full name of the student."
    )

    exam = models.CharField(
        max_length=30,
        choices=EXAM_CHOICES,
        default="WAEC"
    )

    achievement = models.TextField(
        blank=True,
        help_text="Describe the student's academic achievement."
    )

    score = models.CharField(
        max_length=100,
        blank=True,
        help_text="Example: 320 UTME, 7 A's, 85%, First Class."
    )

    photo = models.ImageField(
        upload_to="student_results/",
        blank=True,
        null=True,
        validators=[
            validate_student_result_image_size,
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"])
        ],
        help_text="Upload a student photograph (maximum 20 MB)."
    )

    is_featured = models.BooleanField(
        default=True,
        help_text="Display this result on the homepage."
    )

    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first."
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["display_order", "-created_at"]
        verbose_name = "Student Result"
        verbose_name_plural = "Student Results"

    def __str__(self):
        return f"{self.student_name} - {self.get_exam_display()}"



class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    university = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='testimonials/')
    rating = models.PositiveSmallIntegerField(default=5)  # 1 to 5
    content = models.TextField()

    def __str__(self):
        return f"{self.name} - {self.university}"






class VisionMission(models.Model):
    vision_title = models.CharField(max_length=100, default="Our Vision")
    vision_text = models.TextField(default="To become Nigeria’s leading online academic platform, equipping every student with the right knowledge, tools, and guidance to achieve excellence and compete globally.")
    mission_title = models.CharField(max_length=100, default="Our Mission")
    mission_text = models.TextField(default="To provide accessible, affordable, and high-quality tutorial support that empowers Nigerian students to excel academically, fostering innovation, confidence, and lifelong learning.")

    def __str__(self):
        return "Vision & Mission"


class CTASection(models.Model):
    badge_text = models.CharField(max_length=100, default="Join the Success Story")
    heading_main = models.CharField(max_length=200, default="Ready to Get")
    heading_gradient = models.CharField(max_length=200, default="Started?")
    subtext = models.TextField(default="Join a learning community committed to academic growth, confidence and excellence.")
    button_text = models.CharField(max_length=100, default="Create Account Now")
    button_url = models.URLField(default="#")

    def __str__(self):
        return "CTA Section"

class CTAFeature(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon_svg = models.TextField(help_text="Paste raw SVG code here")
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']


class DownloadAppSection(models.Model):
    heading_main = models.CharField(max_length=100, default="Download the App")
    heading_highlight = models.CharField(max_length=100, default="Today")
    description = models.TextField(default="Join a learning community committed to academic growth, confidence and excellence.")
    button_text = models.CharField(max_length=50, default="Download App")
    button_url = models.URLField(default="#")

    def __str__(self):
        return "Download App Section"


class DownloadAppFeature(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    icon_svg = models.TextField(help_text="Paste raw SVG code here")
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']




class Footer(models.Model):
    academy_name = models.CharField(max_length=255, default="Proffyemphy's Ideal Academy")
    description = models.TextField(default="Empowering Nigerian university students with comprehensive tutorial support and expert guidance for academic excellence.")
    
    email = models.EmailField(default="proffyemphy001@gmail.com")
    phone = models.CharField(max_length=50, default="+234 (0) 8128235805")
    address = models.TextField(default="5, Okeolokun street, Ok bustop, Agura-gberigbe, Ikorodu, Lagos state")

    logo = models.ImageField(upload_to="footer/", blank=True, null=True)

    facebook = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    youtube = models.URLField(blank=True, null=True)
    tiktok = models.URLField(blank=True, null=True)
    whatsapp = models.URLField(blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.academy_name
