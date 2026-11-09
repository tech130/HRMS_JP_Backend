# accounts/models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import secrets


class Admin(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = raw_password

    def check_password(self, raw_password):
        if self.password == raw_password:
            return True
        try:
            return check_password(raw_password, self.password)
        except Exception:
            return False

    def __str__(self):
        return f"{self.name} ({self.email})"


class Employee(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)  # NEW — manually entered by admin
    department = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=100, blank=True)   # e.g. "Team Lead", "Developer"
    belong_to_tl = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="team_members",
        help_text="The Team Lead this employee reports to.",
    )
    is_active = models.BooleanField(default=True)   # NEW — lets admin disable a login without deleting history
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = raw_password

    def check_password(self, raw_password):
        if self.password == raw_password:
            return True
        try:
            return check_password(raw_password, self.password)
        except Exception:
            return False

    def __str__(self):
        return f"{self.name} ({self.email})"


class AuthToken(models.Model):
    """
    Our own lightweight token table, since DRF's built-in Token model
    expects a single AUTH_USER_MODEL — we have two separate tables instead.
    Exactly one of admin/employee is set per row.
    """ 
    key = models.CharField(max_length=64, unique=True, editable=False)
    admin = models.ForeignKey(Admin, null=True, blank=True, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_hex(32)
        super().save(*args, **kwargs)

    @property
    def role(self):
        return "admin" if self.admin_id else "employee"

    @property
    def owner(self):
        return self.admin if self.admin_id else self.employee