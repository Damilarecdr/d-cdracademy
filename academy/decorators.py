from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def tutor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # User must be logged in
        if not request.user.is_authenticated:
            return redirect("login")

        # Tutor is identified by the role field
        if request.user.role != "TUTOR":
            messages.error(
                request,
                "You must be a tutor to access this page.",
            )
            return redirect("dashboard")

        # Prevent suspended tutors from accessing tutor pages
        if getattr(request.user, "is_suspended", False):
            messages.error(
                request,
                "Your account has been suspended.",
            )
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


from functools import wraps

from django.contrib.auth.decorators import login_required


def student_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return wrapper