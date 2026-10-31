
from django.shortcuts import render

from .models import (
    Navbar,
    HeroSection,
    AcademyAdvertisement,
    Statistic,
    AboutSection,
    Feature,
    Aboutstat,
    Tutor,
    Testimonial,
    VisionMission,
    CTASection,
    CTAFeature,
    DownloadAppSection,
    DownloadAppFeature,
    Founder,
    StudentResult,
    Footer,
)


def Navbar_view(request):
    navbar = Navbar.objects.first()

    return render(request, "navbar.html", {
        "navbar": navbar,
    })


def home(request):
    hero = HeroSection.objects.first()
    advertisement = AcademyAdvertisement.objects.filter(
        is_active=True
    ).order_by("-created_at").first()

    stats = Statistic.objects.all()
    about = AboutSection.objects.first()
    features = Feature.objects.all()
    abt = Aboutstat.objects.all()
    tutors = Tutor.objects.all()
    testimonials = Testimonial.objects.all()
    vision_mission = VisionMission.objects.first()
    cta_section = CTASection.objects.first()
    cta_features = CTAFeature.objects.all()
    download_app = DownloadAppSection.objects.first()
    download_features = DownloadAppFeature.objects.all()
    founder = Founder.objects.filter(is_active=True).first()
    student_results = StudentResult.objects.all()

    context = {
        "hero": hero,
        "advertisement": advertisement,
        "stats": stats,
        "about": about,
        "abt": abt,
        "features": features,
        "tutors": tutors,
        "testimonials": testimonials,
        "vision_mission": vision_mission,
        "cta_section": cta_section,
        "cta_features": cta_features,
        "download_app": download_app,
        "download_features": download_features,
        "founder": founder,
        "student_results": student_results, 
    }

    return render(request, "academy/home.html", context)


def footer_view(request):
    footer = Footer.objects.first()

    return render(request, "footer.html", {
        "footer": footer,
    })


