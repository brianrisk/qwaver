from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from users import views as user_views
from users.views import OrganizationCreateView, OrganizationEditView, OrganizationListView, OrganizationDeleteView, \
    ReferralCreateView, ReferralEditView, ReferralListView
from users.views.invites import InvitationCreateView, InvitationEditView, InvitationListView, InvitationDeleteView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', user_views.register, name='register'),
    path('register/<str:ref_code>', user_views.register, name='register'),
    path('profile/', user_views.profile, name='profile'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='queries/about.html'), name='logout'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    path('organization/new/', OrganizationCreateView.as_view(), name='organization-create'),
    path('organization/<int:pk>/', OrganizationEditView.as_view(), name='organization-detail'),
    path('organization/<int:pk>/edit/', OrganizationEditView.as_view(), name='organization-update'),
    path('organizations/', OrganizationListView.as_view(), name='organization-list'),
    path('organization/<int:pk>/delete/', OrganizationDeleteView.as_view(), name='organization-delete'),

    path('invitation/new/', InvitationCreateView.as_view(), name='invitation-create'),
    # TODO: these two seem redundant
    path('invitation/<int:pk>/', InvitationEditView.as_view(), name='invitation-detail'),
    path('invitation/<int:pk>/edit/', InvitationEditView.as_view(), name='invitation-update'),
    path('invitations/', InvitationListView.as_view(), name='invitation-list'),
    path('invitation/<int:pk>/delete/', InvitationDeleteView.as_view(), name='invitation-delete'),

    path('referrals/new/', ReferralCreateView.as_view(), name='referral-create'),
    path('referrals/<int:pk>/edit/', ReferralEditView.as_view(), name='referral-update'),
    path('referrals/', ReferralListView.as_view(), name='referral-list'),
]
