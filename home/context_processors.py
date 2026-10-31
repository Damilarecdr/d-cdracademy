from .models import Navbar


def navbar_context(request):
    return {
        "navbar": Navbar.objects.first()
    }