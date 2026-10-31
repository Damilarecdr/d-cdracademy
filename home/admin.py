from django.contrib import admin
from .models import (
    HeroSection,
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
    Footer,
    Navbar,
)


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = (
        "title_main",
        "title_gradient",
        "title_sub",
        "download_button_text",
        "learn_more_button_text",
    )
    search_fields = (
        "title_main",
        "title_gradient",
        "title_sub",
        "description",
    )


from django.contrib import admin
from .models import AcademyAdvertisement


@admin.register(AcademyAdvertisement)
class AcademyAdvertisementAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "button_text",
        "is_active",
        "created_at",
    )

    list_filter = ("is_active", "created_at")

    search_fields = ("title", "description")

    list_editable = ("is_active",)

    readonly_fields = ("created_at",)

@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ("number", "description")
    search_fields = ("number", "description")
    ordering = ("id",)


@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ("title_main", "title_sub")
    search_fields = (
        "title_main",
        "title_sub",
        "description",
    )


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "color_from",
        "color_to",
    )
    search_fields = (
        "title",
        "description",
    )
    list_filter = (
        "color_from",
        "color_to",
    )


@admin.register(Aboutstat)
class AboutstatAdmin(admin.ModelAdmin):
    list_display = ("number", "description")
    search_fields = ("number", "description")
    ordering = ("id",)


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "qualification",
        "role",
        "course",
        "photo",
    )
    search_fields = (
        "name",
        "qualification",
        "role",
        "course",
    )
    list_filter = (
        "qualification",
        "role",
        "course",
    )

from django.contrib import admin
from .models import Founder


@admin.register(Founder)
class FounderAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "title")
    list_editable = ("is_active",)

    fieldsets = (
        ("Founder Information", {
            "fields": ("name", "title", "photo")
        }),
        ("Biography & Message", {
            "fields": ("bio", "message")
        }),
        ("Settings", {
            "fields": ("is_active",)
        }),
    )




from django.contrib import admin
from .models import StudentResult


@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "exam",
        "score",
        "is_featured",
        "display_order",
        "created_at",
    )

    list_filter = (
        "exam",
        "is_featured",
        "created_at",
    )

    search_fields = (
        "student_name",
        "achievement",
        "score",
    )

    list_editable = (
        "is_featured",
        "display_order",
    )

    ordering = ("display_order", "-created_at")



@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "university",
        "rating",
        "photo",
    )
    search_fields = (
        "name",
        "university",
        "content",
    )
    list_filter = (
        "university",
        "rating",
    )
    ordering = ("-rating",)


@admin.register(VisionMission)
class VisionMissionAdmin(admin.ModelAdmin):
    list_display = (
        "vision_title",
        "mission_title",
    )
    search_fields = (
        "vision_title",
        "vision_text",
        "mission_title",
        "mission_text",
    )


@admin.register(CTASection)
class CTASectionAdmin(admin.ModelAdmin):
    list_display = (
        "badge_text",
        "heading_main",
        "heading_gradient",
        "button_text",
    )
    search_fields = (
        "badge_text",
        "heading_main",
        "heading_gradient",
        "subtext",
    )


@admin.register(CTAFeature)
class CTAFeatureAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "order",
    )
    search_fields = (
        "title",
        "description",
    )
    ordering = ("order",)


@admin.register(DownloadAppSection)
class DownloadAppSectionAdmin(admin.ModelAdmin):
    list_display = (
        "heading_main",
        "heading_highlight",
        "button_text",
    )
    search_fields = (
        "heading_main",
        "heading_highlight",
        "description",
    )


@admin.register(DownloadAppFeature)
class DownloadAppFeatureAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "order",
    )
    search_fields = (
        "title",
        "description",
    )
    ordering = ("order",)


@admin.register(Footer)
class FooterAdmin(admin.ModelAdmin):
    list_display = (
        "academy_name",
        "email",
        "phone",
        "updated_at",
    )
    search_fields = (
        "academy_name",
        "email",
        "phone",
        "address",
    )
    readonly_fields = ("updated_at",)


@admin.register(Navbar)
class NavbarAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        
    )
