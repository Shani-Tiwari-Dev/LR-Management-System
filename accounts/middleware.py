from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    """Send every anonymous visitor to the login page.

    The only pages reachable while signed out are the login page itself,
    the admin login and static files.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info
            open_paths = (
                reverse("login"),
                "/admin/login/",
            )
            if path not in open_paths and not path.startswith(settings.STATIC_URL):
                return redirect(f"{reverse('login')}?next={path}")
        return self.get_response(request)
