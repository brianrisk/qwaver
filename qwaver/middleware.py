from django.shortcuts import redirect, reverse


class EmailVerificationMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # TODO: get email working, then activate this
        # should_verify_email = (
        #     request.user.is_authenticated and
        #     not request.user.profile.email_verified
        # )
        # is_regular_user = not (
        #     request.user.is_staff or
        #     request.user.is_superuser
        # )
        # exempted_views = [
        #     reverse('verify-email'),
        #     reverse('logout'),
        # ]
        #
        # if is_regular_user and should_verify_email:
        #     if request.path not in exempted_views:
        #         return redirect('verify-email')

        return self.get_response(request)
