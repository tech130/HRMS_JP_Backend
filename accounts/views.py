# accounts/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import LoginSerializer, AdminCredentialSerializer, AdminWriteSerializer,  AdminSerializer, EmployeeSerializer, EmployeeCredentialSerializer, EmployeeWriteSerializer
from .models import AuthToken, Employee, Admin
from django.shortcuts import get_object_or_404
from django.db.models.deletion import ProtectedError

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST /api/auth/login/
    body: { "email": "...", "password": "..." }
    returns: { "token": "...", "role": "admin" | "employee", "name": "..." }
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    principal = serializer.validated_data["principal"]
    role = serializer.validated_data["role"]

    token = AuthToken.objects.create(
        admin=principal if role == "admin" else None,
        employee=principal if role == "employee" else None,
    )

    return Response(
        {"token": token.key, "role": role, "name": principal.name},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password_view(request):
    """
    POST /api/auth/forgot_password/
    body: { "email": "...", "new_password": "..." }
    """
    email = request.data.get("email", "").strip()
    new_password = request.data.get("new_password", "").strip()

    if not email:
        return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
    if not new_password:
        return Response({"detail": "New password is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Check Admin table first
    admin = Admin.objects.filter(email__iexact=email).first()
    if admin:
        admin.set_password(new_password)
        admin.save()
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

    # Check Employee table
    employee = Employee.objects.filter(email__iexact=email).first()
    if employee:
        employee.set_password(new_password)
        employee.save()
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

    return Response({"detail": "No account found with this email."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # request.auth is the AuthToken row (see authentication.py)
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    principal = request.user
    if principal.role == "admin":
        data = AdminSerializer(principal.instance).data
        data["auth_role"] = "admin"
        data["is_tl"] = False
    else:
        data = EmployeeSerializer(principal.instance).data  # keeps job-title `role`, e.g. "TL"
        data["auth_role"] = "employee"
        data["is_tl"] = bool(principal.instance.role and principal.instance.role.strip().upper() in ["TL", "TEAM LEAD"])
    return Response(data)


def _is_admin(request):
    return getattr(request.user, "role", None) == "admin"


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_employee_credentials(request):
    """GET /api/auth/employees/ — Team Access list. Admin-only."""
    if not _is_admin(request):
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)
    employees = Employee.objects.select_related("belong_to_tl").all().order_by("name")
    return Response(EmployeeCredentialSerializer(employees, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_employee_departments(request):
    """
    GET /api/auth/employees/departments/
    Distinct department strings already in use — dropdown source, plus the
    admin can still type a brand-new department name (Select is searchable/tag-friendly).
    """
    if not _is_admin(request):
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)
    departments = (
        Employee.objects.exclude(department="")
        .values_list("department", flat=True)
        .distinct()
        .order_by("department")
    )
    return Response(list(departments))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_employee_credential(request):
    """POST /api/auth/employees/create/"""
    if not _is_admin(request):
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)
    serializer = EmployeeWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    employee = serializer.save()
    return Response(EmployeeCredentialSerializer(employee).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def edit_employee_credential(request, pk):
    """PATCH /api/auth/employees/<id>/edit/"""
    if not _is_admin(request):
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)
    employee = get_object_or_404(Employee, pk=pk)
    serializer = EmployeeWriteSerializer(employee, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    employee = serializer.save()
    return Response(EmployeeCredentialSerializer(employee).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_employee_credential(request, pk):
    """DELETE /api/auth/employees/<id>/delete/"""
    if not _is_admin(request):
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)
    employee = get_object_or_404(Employee, pk=pk)
    name = employee.name
    try:
        employee.delete()
        return Response({"detail": f'"{name}" deleted.'}, status=status.HTTP_200_OK)
    except ProtectedError:
        return Response(
            {"detail": "This employee has tasks or timer history and can't be deleted. Consider deactivating instead."},
            status=status.HTTP_409_CONFLICT,
        )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_admin_credentials(request):
    """GET /api/auth/admins/ — Team Access Admin tab. Admin-only."""
    if not _is_admin(request):
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)
    admins = Admin.objects.all().order_by("name")
    return Response(AdminCredentialSerializer(admins, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_admin_credential(request):
    """POST /api/auth/admins/create/"""
    if not _is_admin(request):
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)
    serializer = AdminWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    admin = serializer.save()
    return Response(AdminCredentialSerializer(admin).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def edit_admin_credential(request, pk):
    """PATCH /api/auth/admins/<id>/edit/"""
    if not _is_admin(request):
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)
    admin = get_object_or_404(Admin, pk=pk)
    serializer = AdminWriteSerializer(admin, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    admin = serializer.save()
    return Response(AdminCredentialSerializer(admin).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_admin_credential(request, pk):
    """DELETE /api/auth/admins/<id>/delete/"""
    if not _is_admin(request):
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)
    if Admin.objects.count() <= 1:
        return Response({"detail": "Can't delete the last remaining admin."}, status=status.HTTP_409_CONFLICT)
    if request.user.role == "admin" and request.user.instance.pk == pk:
        return Response({"detail": "You can't delete your own admin account."}, status=status.HTTP_409_CONFLICT)
    admin = get_object_or_404(Admin, pk=pk)
    admin.delete()
    return Response({"detail": f'"{admin.name}" deleted.'}, status=status.HTTP_200_OK)