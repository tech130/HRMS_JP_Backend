# tasks/views/__init__.py

from .task_views import (
    create_task, assign_task, edit_task, create_and_assign_task, get_all_departments,
    get_all_employees, get_priority_choices, get_all_admins, get_admin_my_tasks,
    task_master_view, task_master_detail_view
)
from .timer_views import (
    get_active_session, start_task, pause_task, resume_task,
    submit_task, get_task_sessions,
)
from .review_views import (
    get_review_tasks, get_tl_review_tasks, start_review,
    approve_task, request_rework, get_rework_tasks
)
from .correction_views import (
    request_correction, get_pending_corrections, decide_correction,
    get_approved_corrections, get_rejected_corrections,
)
from .lifecycle_views import (
    hold_task, release_hold, cancel_task,
)
from .activity_views import (
    get_all_activity, get_my_activity,
)
from .report_views import (
    get_admin_reports, get_my_reports, get_employee_rating_trends, get_daily_timeline,
    get_assigned_hours_tracking, get_monthly_performance_report,
)

from .recurring import (
    get_recurring_tasks, create_recurring_task, stop_recurring_task, generate_recurring_tasks, get_all_tasks,
    get_my_tasks, get_tl_tasks, get_my_recurring_tasks, toggle_recurring_date, get_assigned_recurring_tasks
)

from .notification_views import (
    get_notifications, get_unread_notification_count, mark_notification_read, mark_all_notifications_read
)

from .utils import (health_check)
