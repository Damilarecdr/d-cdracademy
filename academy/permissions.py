from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            if not user.is_active or user.is_suspended:
                raise PermissionDenied("Your account is inactive or suspended.")

            if user.is_superuser or user.role == "ADMIN":
                return view_func(request, *args, **kwargs)

            if user.role not in roles:
                raise PermissionDenied("You are not authorized to access this page.")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def student_required(view_func):
    return role_required("JAMB", "ALEVEL", "UNIVERSITY")(view_func)


def tutor_required(view_func):
    return role_required("TUTOR")(view_func)
