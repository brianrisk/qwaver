from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from queries.common.access import create_api_key
from users.forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from users.models import UserOrganization, Invitation, Referral


def register(request, ref_code=None):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # saving referrer
            if ref_code is not None:
                try:
                    if ref_code.isdigit():
                        referral = Referral.objects.get(pk=int(ref_code))
                    else:
                        referral = Referral.objects.get(ref_code=ref_code)
                except Referral.DoesNotExist:
                    referral = None
                if referral is not None:
                    user.profile.referral_id = referral
                    user.profile.save()
            # logging in the user
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            messages.success(request, f'Your account has been created!')
            resolve_invitations(user, request)
            # TODO: get email working, then activate this
            # send_verification_email(user, request)
            login(request, user)
            # login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('queries-home')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def resolve_invitations(user, request):
    invitations = Invitation.objects.filter(email__iexact=user.email)

    if len(invitations) > 0:
        # set one of these as the selected organization on the user profile
        user.profile.selected_organization = invitations.first().organization
        user.profile.save()
        # add for each invitation
        for invitation in invitations:
            user_org = UserOrganization.objects.create(user=user, organization=invitation.organization)
            user_org.save()
            # we don't need the invitation anymore
            invitation.delete()
            messages.success(request, f'You have been added to the organization {invitation.organization.name}')


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.is_active)

email_verification_token = EmailVerificationTokenGenerator()


def send_verification_email(user, request):
    mail_subject = 'Confirm your Account'
    message = render_to_string('users/verify_email_content.html', {
                'user': user,
                'domain': request.get_host(),
                'uid': urlsafe_base64_encode(bytes(str(user.pk), encoding='utf-8')),
                'token': email_verification_token.make_token(user),
            })
    send_mail(mail_subject, message, None, [user.email], fail_silently=False)


@login_required
def profile(request):
    profile = request.user.profile
    # this could possibly be removed.
    # It is here as some profiles were created before there was an api_key
    if profile.api_key is None:
        profile.api_key = create_api_key()
        profile.save()
    user_orgs = UserOrganization.objects.filter(user=request.user)
    # https://stackoverflow.com/questions/39702538/python-converting-a-queryset-in-a-list-of-tuples
    # converting the queryset to list of tuples
    orgs = [(q.organization.pk, q.organization.name) for q in user_orgs]
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=profile)
        # api_key field is readonly
        p_form.fields['api_key'].disabled = True
        # p_form.fields['selected_organization'].choices = orgs
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)
        p_form.fields['selected_organization'].choices = orgs
        p_form.fields['api_key'].disabled = True

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile.html', context)


def verify_email(request):
    encoded_uid = request.GET.get('uid')
    token = request.GET.get('token')
    if not encoded_uid or not token:
        return render(request, 'users/verify_email.html')

    User = get_user_model()
    try:
        uid = int(str(urlsafe_base64_decode(encoded_uid), encoding='utf-8'))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and email_verification_token.check_token(user, token):
        profile = user.profile
        profile.email_verified = True
        profile.save()

        messages.success(request, f'Your email has been verified!')
        if request.user.is_authenticated:
            return redirect('queries-home')
        return redirect('login')

    return render(request, 'users/verify_email.html', context={
        'error': 'There was a problem verifying your email address.'
    })
