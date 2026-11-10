# Task CRUD & Listing
# Core task creation, assignment, and listing across roles.

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import Employee
from ..models import Task, TaskMaster
from ..serializers import (
    TaskListSerializer, TaskCreateSerializer, TaskAssignSerializer,
    TaskCreateAssignSerializer, TaskMasterSerializer, TaskMasterWriteSerializer
)
from ..activity import ActivityLog, log_activity
from ..notification_utils import send_notification
from ..models import Notification
from django.db import transaction
from .utils import _is_admin, _current_employee, _is_tl, _can_manage_tasks, _owns_task_for_management, task_list_queryset


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_task(request):
    if not _can_manage_tasks(request):
        return Response({"detail": "Only admins or team leads can create tasks."}, status=status.HTTP_403_FORBIDDEN)

    serializer = TaskCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if _is_admin(request):
        task = serializer.save(assigned_by_admin=request.user.instance)
    else:
        task = serializer.save(assigned_by_employee=request.user.instance)

    return Response(TaskListSerializer(task).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def assign_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not _owns_task_for_management(request, task):
        return Response({"detail": "You can only assign or reassign tasks you created."}, status=status.HTTP_403_FORBIDDEN)
    if request.data.get("assigned_to_admin") and not _is_tl(request):
        return Response({"detail": "Only team leads can assign a task to an admin."}, status=status.HTTP_403_FORBIDDEN)

    serializer = TaskAssignSerializer(task, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)

    new_employee = serializer.validated_data.get("assigned_to")
    new_admin = serializer.validated_data.get("assigned_to_admin")

    # Check if the assignee was actually changed to someone else
    assignee_changed = (
        ("assigned_to" in serializer.validated_data and new_employee != task.assigned_to) or
        ("assigned_to_admin" in serializer.validated_data and new_admin != task.assigned_to_admin)
    )

    with transaction.atomic():
        if assignee_changed:
            # If reassigned to a different person, close any running timer first
            open_session = task.sessions.filter(end_time__isnull=True).first()
            if open_session:
                open_session.close()
                task.recalc_total_time()
            task = serializer.save(task_status=Task.Status.NOT_STARTED)

            sender = request.user.instance.name if hasattr(request.user, "instance") and request.user.instance else "Management"
            assignee = task.assigned_to if task.assigned_to else task.assigned_to_admin
            url = "/employee/all_tasks" if task.assigned_to else "/admin/my_tasks"
            send_notification(
                recipient=assignee,
                title="Task Reassigned to You",
                message=f"{sender} assigned you task: '{task.task_name}' (Priority: {task.priority.capitalize()}).",
                event_type=Notification.EventType.TASK_ASSIGNED,
                action_url=url,
                sender_name=sender,
            )
        else:
            # If only details (due date, priority, hours) changed, PRESERVE current task_status
            task = serializer.save()

    return Response(TaskListSerializer(task).data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_and_assign_task(request):
    if not _can_manage_tasks(request):
        return Response({"detail": "Only admins or team leads can create tasks."}, status=status.HTTP_403_FORBIDDEN)

    if request.data.get("assigned_to_admin") and not _is_tl(request):
        return Response({"detail": "Only team leads can assign a task to an admin."}, status=status.HTTP_403_FORBIDDEN)

    serializer = TaskCreateAssignSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        if _is_admin(request):
            task = serializer.save(assigned_by_admin=request.user.instance, task_status=Task.Status.NOT_STARTED)
        else:
            task = serializer.save(assigned_by_employee=request.user.instance, task_status=Task.Status.NOT_STARTED)

        log_activity(
            task, request.user, ActivityLog.Action.CREATED,
            to_status="not_started",
            details={
                "assigned_to": task.assignee_name,
                "assignee_role": task.assignee_role,
                "priority": task.priority,
                "due_date": str(task.due_date) if task.due_date else None,
                "allotted_time": str(task.allotted_time) if task.allotted_time is not None else None,
            },
        )

        sender = request.user.instance.name if hasattr(request.user, "instance") and request.user.instance else "Management"
        assignee = task.assigned_to if task.assigned_to else task.assigned_to_admin
        url = "/employee/all_tasks" if task.assigned_to else "/admin/my_tasks"
        send_notification(
            recipient=assignee,
            title="New Task Assigned",
            message=f"{sender} assigned you a new task: '{task.task_name}' (Priority: {task.priority.capitalize()}).",
            event_type=Notification.EventType.TASK_ASSIGNED,
            action_url=url,
            sender_name=sender,
        )

    return Response(TaskListSerializer(task).data, status=status.HTTP_201_CREATED)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_departments(request):
    """GET /api/tasks/get_all_departments/"""
    departments = (
        Employee.objects.exclude(department="")
        .values_list("department", flat=True)
        .distinct()
        .order_by("department")
    )
    return Response([{"id": name, "name": name} for name in departments])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_employees(request):
    """GET /api/tasks/get_all_employees/?department=Engineering"""
    employees = Employee.objects.all()
    department = request.query_params.get("department")
    if department:
        employees = employees.filter(department=department)
    data = [{"id": e.id, "name": e.name, "department": e.department} for e in employees]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_priority_choices(request):
    """GET /api/tasks/get_priority_choices/"""
    return Response([{"value": value, "label": label} for value, label in Task.Priority.choices])

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_admins(request):
    """GET /api/tasks/get_all_admins/ — dropdown source for a TL's 'Assign to Admin' option."""
    if not _is_tl(request):
        return Response({"detail": "Team leads only."}, status=status.HTTP_403_FORBIDDEN)
    from accounts.models import Admin
    admins = Admin.objects.filter(is_active=True).order_by("name")
    return Response([{"id": a.id, "name": a.name} for a in admins])

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_admin_my_tasks(request):
    """GET /api/tasks/admin_my_tasks/ — tasks a TL assigned TO this logged-in admin."""
    if not _is_admin(request):
        return Response({"detail": "Admins only."}, status=status.HTTP_403_FORBIDDEN)
    admin = request.user.instance
    tasks = task_list_queryset().filter(assigned_to_admin=admin)
    return Response(TaskListSerializer(tasks, many=True).data)

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def task_master_view(request):
    """GET /api/tasks/task_master/ and POST /api/tasks/task_master/"""
    if request.method == "GET":
        items = TaskMaster.objects.filter(is_active=True).order_by("project_name", "task_name")
        return Response(TaskMasterSerializer(items, many=True).data)

    if not _can_manage_tasks(request):
        return Response({"detail": "Only admins or team leads can manage task catalog."}, status=status.HTTP_403_FORBIDDEN)

    serializer = TaskMasterWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    obj = serializer.save()
    return Response(TaskMasterSerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(["DELETE", "PATCH"])
@permission_classes([IsAuthenticated])
def task_master_detail_view(request, pk):
    """DELETE /api/tasks/task_master/<int:pk>/"""
    if not _can_manage_tasks(request):
        return Response({"detail": "Only admins or team leads can manage task catalog."}, status=status.HTTP_403_FORBIDDEN)
    item = get_object_or_404(TaskMaster, pk=pk)
    if request.method == "DELETE":
        item.is_active = False
        item.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method == "PATCH":
        serializer = TaskMasterWriteSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(TaskMasterSerializer(obj).data)


@api_view(["PATCH", "PUT"])
@permission_classes([IsAuthenticated])
def edit_task(request, pk):
    """
    PATCH /api/tasks/<int:pk>/edit/
    Full task edit endpoint.
    Prefilled with existing task data, allows changing any detail including assigned_to.
    Guarantees that task_id and sub_task_id remain identical.
    """
    try:
        task = get_object_or_404(Task, pk=pk)
        if not _owns_task_for_management(request, task):
            return Response({"detail": "You do not have permission to edit this task."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data

        # Store previous IDs to strictly ensure task_id and sub_task_id are NEVER changed
        original_task_id = task.task_id
        original_sub_task_id = task.sub_task_id

        # Handle assignee change
        assignee_changed = False
        if "assigned_to" in data:
            new_emp_id = data.get("assigned_to")
            target_emp = Employee.objects.filter(pk=new_emp_id).first() if new_emp_id else None
            if target_emp != task.assigned_to:
                assignee_changed = True
                task.assigned_to = target_emp
                task.assigned_to_admin = None
                if target_emp and target_emp.department and not data.get("department"):
                    task.department = target_emp.department

        if "assigned_to_admin" in data:
            new_admin_id = data.get("assigned_to_admin")
            from accounts.models import Admin
            target_admin = Admin.objects.filter(pk=new_admin_id).first() if new_admin_id else None
            if target_admin != task.assigned_to_admin:
                assignee_changed = True
                task.assigned_to_admin = target_admin
                task.assigned_to = None
                task.department = ""

        if "project_name" in data:
            task.project_name = str(data.get("project_name") or "").strip()
        if "task_name" in data and data.get("task_name"):
            task.task_name = str(data["task_name"]).strip()
        if "task_details" in data:
            task.task_details = str(data.get("task_details") or "").strip()
        if "department" in data:
            dept_val = str(data.get("department") or "").strip()
            if dept_val:
                task.department = dept_val
        if "priority" in data and data.get("priority"):
            task.priority = data["priority"]
        if "start_date" in data:
            task.start_date = data["start_date"] or None
        if "due_date" in data:
            task.due_date = data["due_date"] or None
        if "due_time" in data:
            task.due_time = data["due_time"] or None
        if "allotted_time" in data and data.get("allotted_time") is not None:
            try:
                from decimal import Decimal
                task.allotted_time = Decimal(str(data["allotted_time"]))
            except (ValueError, TypeError, Exception):
                pass

        with transaction.atomic():
            if assignee_changed:
                open_session = task.sessions.filter(end_time__isnull=True).first()
                if open_session:
                    open_session.close()
                    task.recalc_total_time()
                if task.task_status != Task.Status.COMPLETED:
                    task.task_status = Task.Status.NOT_STARTED

                sender = request.user.instance.name if hasattr(request.user, "instance") and request.user.instance else "Management"
                assignee = task.assigned_to if task.assigned_to else task.assigned_to_admin
                if assignee:
                    url = "/employee/all_tasks" if task.assigned_to else "/admin/my_tasks"
                    try:
                        send_notification(
                            recipient=assignee,
                            title="Task Reassigned to You",
                            message=f"{sender} updated and assigned you task: '{task.task_name}' (Priority: {task.priority.capitalize()}).",
                            event_type=Notification.EventType.TASK_ASSIGNED,
                            action_url=url,
                            sender_name=sender,
                        )
                    except Exception as notif_err:
                        print(f"Failed to send task reassign notification: {notif_err}")

            # Strictly maintain same task_id and sub_task_id
            task.task_id = original_task_id
            task.sub_task_id = original_sub_task_id
            task.save()

            try:
                log_activity(
                    task, request.user,
                    ActivityLog.Action.ASSIGNED if assignee_changed else ActivityLog.Action.EDITED,
                    details={
                        "task_id": task.task_id,
                        "sub_task_id": task.sub_task_id,
                        "assigned_to": task.assignee_name,
                        "priority": task.priority,
                        "due_date": str(task.due_date) if task.due_date else None,
                    }
                )
            except Exception as log_err:
                print(f"Failed to log activity: {log_err}")

        return Response(TaskListSerializer(task).data, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
