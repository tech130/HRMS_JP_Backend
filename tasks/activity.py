# tasks/activity.py
from django.db import models
from accounts.models import Admin, Employee


class ActivityLog(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Task Created"
        ASSIGNED = "assigned", "Assigned / Reassigned"
        EDITED = "edited", "Task Edited"
        STARTED = "started", "Timer Started"
        PAUSED = "paused", "Timer Paused"
        RESUMED = "resumed", "Timer Resumed"
        SUBMITTED = "submitted", "Submitted"
        REVIEW_STARTED = "review_started", "Review Started"
        APPROVED = "approved", "Approved"
        REWORK_REQUESTED = "rework_requested", "Rework Requested"
        HOLD = "hold", "Put On Hold"
        RELEASED_HOLD = "released_hold", "Hold Released"
        CANCELLED = "cancelled", "Cancelled"
        CORRECTION_REQUESTED = "correction_requested", "Time Correction Requested"
        CORRECTION_DECIDED = "correction_decided", "Time Correction Decided"

    task = models.ForeignKey("tasks.Task", on_delete=models.CASCADE, related_name="activity_log")
    # Two nullable FKs, same pattern as AuthToken — exactly one is set per row.
    actor_admin = models.ForeignKey(Admin, null=True, blank=True, on_delete=models.SET_NULL)
    actor_employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=30, choices=Action.choices)
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, blank=True)
    details = models.JSONField(default=dict, blank=True)  # old/new values, remarks snapshot, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def actor_name(self):
        if self.actor_admin_id:
            return self.actor_admin.name
        if self.actor_employee_id:
            return self.actor_employee.name
        return "System"


def log_activity(task, principal, action, from_status="", to_status="", details=None):
    """
    principal = request.user (the SimplePrincipal from your authentication.py).
    Call this at the END of every view that changes task/session state —
    after the save succeeds, not before.
    """
    kwargs = dict(task=task, action=action, from_status=from_status,
                  to_status=to_status, details=details or {})
    if principal is not None and getattr(principal, "role", None) == "admin":
        kwargs["actor_admin"] = principal.instance
    elif principal is not None and getattr(principal, "role", None) == "employee":
        kwargs["actor_employee"] = principal.instance
    ActivityLog.objects.create(**kwargs)