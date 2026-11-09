from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="auth-login"),
    path("forgot_password/", views.forgot_password_view, name="auth-forgot-password"),
    path("logout/", views.logout_view, name="auth-logout"),
    path("me/", views.me_view, name="auth-me"),

    # ── Team Access — Employees ──────────────────────────────────────────
    path("employees/", views.get_all_employee_credentials, name="employee-credentials-list"),
    path("employees/departments/", views.get_employee_departments, name="employee-departments"),
    path("employees/create/", views.create_employee_credential, name="employee-credentials-create"),
    path("employees/<int:pk>/edit/", views.edit_employee_credential, name="employee-credentials-edit"),
    path("employees/<int:pk>/delete/", views.delete_employee_credential, name="employee-credentials-delete"),

    # ── Team Access — Admins ─────────────────────────────────────────────
    path("admins/", views.get_all_admin_credentials, name="admin-credentials-list"),
    path("admins/create/", views.create_admin_credential, name="admin-credentials-create"),
    path("admins/<int:pk>/edit/", views.edit_admin_credential, name="admin-credentials-edit"),
    path("admins/<int:pk>/delete/", views.delete_admin_credential, name="admin-credentials-delete"),
]