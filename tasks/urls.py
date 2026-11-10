# tasks/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # ── Task CRUD & listing ──────────────────────────────────────────────
    path("get_all_tasks/", views.get_all_tasks, name="task-list"),
    path("create_task/", views.create_task, name="task-create"),
    path("create_and_assign/", views.create_and_assign_task, name="task-create-assign"),
    path("<int:pk>/edit/", views.edit_task, name="task-edit"),
    path("assign_task/<int:pk>/", views.assign_task, name="task-assign"),

    path("get_all_departments/", views.get_all_departments, name="task-departments"),
    path("get_all_employees/", views.get_all_employees, name="task-employees"),
    path("get_priority_choices/", views.get_priority_choices, name="task-priorities"),

    # ── Task Master / Catalog ─────────────────────────────────────────────
    path("task_master/", views.task_master_view, name="task-master"),
    path("task_master/<int:pk>/", views.task_master_detail_view, name="task-master-detail"),

    path("my_tasks/", views.get_my_tasks, name="employee-my-tasks"),
    path("tl_tasks/", views.get_tl_tasks, name="tl-tasks"),

    # ── Timer flow ────────────────────────────────────────────────────────
    path("my_active_session/", views.get_active_session, name="task-active-session"),
    path("<int:pk>/start/", views.start_task, name="task-start"),
    path("<int:pk>/pause/", views.pause_task, name="task-pause"),
    path("<int:pk>/resume/", views.resume_task, name="task-resume"),
    path("<int:pk>/submit/", views.submit_task, name="task-submit"),
    path("<int:pk>/sessions/", views.get_task_sessions, name="task-sessions"),

    # ── Review queue (admin + TL) ────────────────────────────────────────
    path("review_tasks/", views.get_review_tasks, name="task-review-tasks"),
    path("tl_review_tasks/", views.get_tl_review_tasks, name="tl-review-tasks"),
    path("<int:pk>/review/start/", views.start_review, name="task-review-start"),
    path("<int:pk>/review/approve/", views.approve_task, name="task-review-approve"),
    path("<int:pk>/review/rework/", views.request_rework, name="task-review-rework"),
    path("rework_tasks/", views.get_rework_tasks, name="task-rework-tasks"),

    # ── Time corrections ─── NOTE: these use "sessions/" and "corrections/",
    # NOT "tasks/" — make sure whatever include() maps this urls.py doesn't
    # prefix everything with /api/tasks/, or these paths won't match
    # /api/sessions/... and /api/corrections/... at all.
    path("sessions/<int:session_id>/correction-request/", views.request_correction, name="correction-request"),
    path("corrections/pending/", views.get_pending_corrections, name="correction-pending"),
    path("corrections/approved/", views.get_approved_corrections, name="correction-approved"),
    path("corrections/rejected/", views.get_rejected_corrections, name="correction-rejected"),
    path("corrections/<int:pk>/decision/", views.decide_correction, name="correction-decision"),

    # ── Hold / Cancel  ──────────────────────────────────────────
    path("<int:pk>/hold/", views.hold_task, name="task-hold"),
    path("<int:pk>/release_hold/", views.release_hold, name="task-release-hold"),
    path("<int:pk>/cancel/", views.cancel_task, name="task-cancel"),

    # ── Activity / audit log ─────────────────────────────────────────────
    path("activity/", views.get_all_activity, name="activity-all"),
    path("my_activity/", views.get_my_activity, name="activity-employee"),

    # ── Reports ───────────────────────────────────────────────────────────
    path("reports/admin/", views.get_admin_reports, name="reports-admin"),
    path("reports/employee/", views.get_my_reports, name="reports-employee"),
    path("reports/daily_timeline/", views.get_daily_timeline, name="reports-daily-timeline"),
    path("reports/assigned_hours_tracking/", views.get_assigned_hours_tracking, name="reports-assigned-hours-tracking"),
    path("reports/monthly_performance/", views.get_monthly_performance_report, name="reports-monthly-performance"),

    # ── Recurring (daily) tasks ──────────────────────────────────────────
    path("recurring/", views.get_recurring_tasks, name="recurring-list"),
    path("recurring/mine/", views.get_my_recurring_tasks, name="recurring-mine"),   # ← ADDED
    path("recurring/create/", views.create_recurring_task, name="recurring-create"),
    path("recurring/<int:pk>/stop/", views.stop_recurring_task, name="recurring-stop"),
    path("recurring/<int:pk>/toggle_date/", views.toggle_recurring_date, name="recurring-toggle-date"),  # <-- ADD THIS
    path("recurring/assigned_to_me/", views.get_assigned_recurring_tasks, name="recurring-assigned-to-me"),
    
    path("reports/rating_trends/", views.get_employee_rating_trends, name="reports-rating-trends"),
    
    path("get_all_admins/", views.get_all_admins, name="task-admins"),
    path("admin_my_tasks/", views.get_admin_my_tasks, name="admin-my-tasks"),

    # ── Notifications ────────────────────────────────────────────────────
    path("notifications/", views.get_notifications, name="notifications-list"),
    path("notifications/unread_count/", views.get_unread_notification_count, name="notifications-unread-count"),
    path("notifications/<int:pk>/mark_read/", views.mark_notification_read, name="notifications-mark-read"),
    path("notifications/mark_all_read/", views.mark_all_notifications_read, name="notifications-mark-all-read"),
    
    path("health/", views.health_check, name="health-check"),
]
