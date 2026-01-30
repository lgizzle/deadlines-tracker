"""
API views for gmail-daily integration.
Simple JsonResponse-based API without DRF.
"""
import json
import logging
import os
from datetime import datetime
from functools import wraps

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import Entity, Deadline, Task, Document

# Security audit logger
audit_logger = logging.getLogger("security.audit")


# =============================================================================
# Authentication
# =============================================================================

def api_key_required(view_func):
    """Decorator to require API key authentication.

    Accepts API key via:
    - X-API-Key header (preferred for IAP passthrough)
    - Authorization: Bearer <key> header

    SECURITY: No localhost bypass - always require authentication.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get expected API key from environment
        expected_key = os.environ.get("ERP_API_KEY", "")

        # SECURITY: Fail hard if no API key configured
        if not expected_key:
            audit_logger.error(
                f"API_MISCONFIGURED: ERP_API_KEY not set, "
                f"ip={request.META.get('REMOTE_ADDR')} "
                f"path={request.path}"
            )
            return JsonResponse({
                "status": "error",
                "code": "SERVER_MISCONFIGURED",
                "message": "API authentication not configured"
            }, status=500)

        # Check X-API-Key header first (preferred for IAP scenarios)
        provided_key = request.META.get("HTTP_X_API_KEY", "")

        # Fall back to Authorization: Bearer header
        if not provided_key:
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                provided_key = auth_header[7:]

        if not provided_key:
            audit_logger.warning(
                f"API_AUTH_MISSING: No API key provided, "
                f"ip={request.META.get('REMOTE_ADDR')} "
                f"path={request.path}"
            )
            return JsonResponse({
                "status": "error",
                "code": "AUTH_REQUIRED",
                "message": "API key required (X-API-Key header or Authorization: Bearer)"
            }, status=401)

        if provided_key != expected_key:
            audit_logger.warning(
                f"API_AUTH_INVALID: Invalid API key attempt, "
                f"ip={request.META.get('REMOTE_ADDR')} "
                f"path={request.path}"
            )
            return JsonResponse({
                "status": "error",
                "code": "AUTH_INVALID",
                "message": "Invalid API key"
            }, status=401)

        return view_func(request, *args, **kwargs)
    return wrapper


def parse_json_body(request):
    """Parse JSON body from request."""
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# =============================================================================
# Health Check
# =============================================================================

@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint."""
    return JsonResponse({
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


# =============================================================================
# Entity Endpoints
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
@api_key_required
def entity_list(request):
    """List all entities."""
    entities = Entity.objects.filter(status="Active").values(
        "entity_code", "legal_name", "dba_name", "status"
    )
    return JsonResponse({
        "entities": list(entities)
    })


# =============================================================================
# Task Endpoints
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def task_create(request):
    """Create a new task from email action item."""
    data = parse_json_body(request)
    if not data:
        return JsonResponse({
            "status": "error",
            "code": "INVALID_JSON",
            "message": "Invalid JSON body"
        }, status=400)

    # Check for duplicate by email_id
    email_id = data.get("email_id", "")
    if email_id:
        existing = Task.objects.filter(email_id=email_id).first()
        if existing:
            return JsonResponse({
                "status": "duplicate",
                "existing_task_id": existing.id,
                "url": f"/tasks/{existing.id}/",
                "message": f"Task already exists for email_id {email_id}"
            }, status=409)

    # Validate entity_code if provided
    entity = None
    entity_code = data.get("entity_code")
    if entity_code:
        entity = Entity.objects.filter(entity_code=entity_code).first()
        if not entity:
            return JsonResponse({
                "status": "error",
                "code": "VALIDATION_ERROR",
                "message": f"entity_code '{entity_code}' not found",
                "field": "entity_code"
            }, status=400)

    # Validate deadline_id if provided
    deadline = None
    deadline_id = data.get("deadline_id")
    if deadline_id:
        deadline = Deadline.objects.filter(id=deadline_id).first()
        if not deadline:
            return JsonResponse({
                "status": "error",
                "code": "VALIDATION_ERROR",
                "message": f"deadline_id '{deadline_id}' not found",
                "field": "deadline_id"
            }, status=400)

    # Parse due_date
    due_date = None
    if data.get("due_date"):
        try:
            due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({
                "status": "error",
                "code": "VALIDATION_ERROR",
                "message": "due_date must be in YYYY-MM-DD format",
                "field": "due_date"
            }, status=400)

    # Parse email_date
    email_date = None
    if data.get("email_date"):
        try:
            email_date = datetime.fromisoformat(data["email_date"].replace("Z", "+00:00"))
        except ValueError:
            pass  # Non-critical, skip if invalid

    # Create task
    task = Task.objects.create(
        title=data.get("title", "Untitled Task"),
        description=data.get("description", ""),
        entity=entity,
        task_type=data.get("task_type", "other"),
        priority=data.get("priority", "normal"),
        status="pending",
        source=data.get("source", "email"),
        due_date=due_date,
        amount=data.get("amount"),
        email_id=email_id,
        email_thread_id=data.get("email_thread_id", ""),
        email_subject=data.get("email_subject", ""),
        email_from=data.get("email_from", ""),
        email_date=email_date,
        deadline=deadline,
        metadata=data.get("metadata", {}),
    )

    return JsonResponse({
        "task_id": task.id,
        "url": f"/tasks/{task.id}/",
        "status": "created",
        "title": task.title,
        "entity_code": entity_code,
        "due_date": str(task.due_date) if task.due_date else None,
        "created_at": task.created_at.isoformat()
    }, status=201)


@csrf_exempt
@require_http_methods(["GET"])
@api_key_required
def task_check_duplicate(request):
    """Check if task already exists for email_id."""
    email_id = request.GET.get("email_id", "")
    if not email_id:
        return JsonResponse({
            "status": "error",
            "code": "MISSING_PARAM",
            "message": "email_id parameter required"
        }, status=400)

    task = Task.objects.filter(email_id=email_id).first()
    if task:
        return JsonResponse({
            "exists": True,
            "task_id": task.id,
            "url": f"/tasks/{task.id}/",
            "status": task.status,
            "title": task.title
        })

    return JsonResponse({"exists": False})


@csrf_exempt
@require_http_methods(["PATCH"])
@api_key_required
def task_update(request, task_id):
    """Update task status."""
    task = Task.objects.filter(id=task_id).first()
    if not task:
        return JsonResponse({
            "status": "error",
            "code": "NOT_FOUND",
            "message": f"Task {task_id} not found"
        }, status=404)

    data = parse_json_body(request)
    if not data:
        return JsonResponse({
            "status": "error",
            "code": "INVALID_JSON",
            "message": "Invalid JSON body"
        }, status=400)

    # Update allowed fields
    if "status" in data:
        task.status = data["status"]
        if data["status"] == "completed":
            task.completed_at = datetime.utcnow()
    if "priority" in data:
        task.priority = data["priority"]
    if "notes" in data:
        task.description = data["notes"]

    task.save()

    return JsonResponse({
        "task_id": task.id,
        "status": task.status,
        "updated_at": task.updated_at.isoformat()
    })


# =============================================================================
# Document Endpoints
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def document_create(request):
    """Store document metadata (file stored separately in OneDrive)."""
    data = parse_json_body(request)
    if not data:
        return JsonResponse({
            "status": "error",
            "code": "INVALID_JSON",
            "message": "Invalid JSON body"
        }, status=400)

    # Require sha256_hash
    sha256_hash = data.get("sha256_hash", "")
    if not sha256_hash:
        return JsonResponse({
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": "sha256_hash is required",
            "field": "sha256_hash"
        }, status=400)

    # Check for duplicate by hash
    existing = Document.objects.filter(sha256_hash=sha256_hash).first()
    if existing:
        return JsonResponse({
            "status": "duplicate",
            "existing_document_id": existing.id,
            "url": f"/documents/{existing.id}/",
            "message": "Document with same content already exists",
            "match_type": "sha256_hash"
        }, status=409)

    # Validate entity_code if provided
    entity = None
    entity_code = data.get("entity_code")
    if entity_code:
        entity = Entity.objects.filter(entity_code=entity_code).first()
        if not entity:
            return JsonResponse({
                "status": "error",
                "code": "VALIDATION_ERROR",
                "message": f"entity_code '{entity_code}' not found",
                "field": "entity_code"
            }, status=400)

    # Parse dates
    document_date = None
    if data.get("document_date"):
        try:
            document_date = datetime.strptime(data["document_date"], "%Y-%m-%d").date()
        except ValueError:
            pass

    due_date = None
    if data.get("due_date"):
        try:
            due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
        except ValueError:
            pass

    email_date = None
    if data.get("email_date"):
        try:
            email_date = datetime.fromisoformat(data["email_date"].replace("Z", "+00:00"))
        except ValueError:
            pass

    # Create document
    document = Document.objects.create(
        filename=data.get("filename", "unknown"),
        title=data.get("title", ""),
        document_type=data.get("document_type", "other"),
        entity=entity,
        file_path=data.get("file_path", ""),
        file_size=data.get("file_size"),
        mime_type=data.get("mime_type", ""),
        sha256_hash=sha256_hash,
        source=data.get("source", "email"),
        email_id=data.get("email_id", ""),
        email_subject=data.get("email_subject", ""),
        email_from=data.get("email_from", ""),
        email_date=email_date,
        document_date=document_date,
        due_date=due_date,
        amount=data.get("amount"),
        metadata=data.get("metadata", {}),
        notes=data.get("notes", ""),
    )

    return JsonResponse({
        "document_id": document.id,
        "url": f"/documents/{document.id}/",
        "status": "created",
        "filename": document.filename,
        "entity_code": entity_code,
        "file_path": document.file_path
    }, status=201)


@csrf_exempt
@require_http_methods(["GET"])
@api_key_required
def document_check_duplicate(request):
    """Check if document already exists."""
    sha256_hash = request.GET.get("sha256_hash", "")
    email_id = request.GET.get("email_id", "")
    filename = request.GET.get("filename", "")

    # Check by hash first (most reliable)
    if sha256_hash:
        doc = Document.objects.filter(sha256_hash=sha256_hash).first()
        if doc:
            return JsonResponse({
                "exists": True,
                "document_id": doc.id,
                "url": f"/documents/{doc.id}/",
                "match_type": "sha256_hash",
                "filename": doc.filename
            })

    # Check by email_id + filename
    if email_id and filename:
        doc = Document.objects.filter(email_id=email_id, filename=filename).first()
        if doc:
            return JsonResponse({
                "exists": True,
                "document_id": doc.id,
                "url": f"/documents/{doc.id}/",
                "match_type": "email_id_filename",
                "filename": doc.filename
            })

    return JsonResponse({"exists": False})


# =============================================================================
# Deadline Search Endpoint
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
@api_key_required
def deadline_search(request):
    """Search deadlines by entity and keywords."""
    entity_code = request.GET.get("entity_code", "")
    keywords = request.GET.get("keywords", "")
    vendor = request.GET.get("vendor", "")
    category = request.GET.get("category", "")

    queryset = Deadline.objects.filter(status="Active")

    if entity_code:
        queryset = queryset.filter(entity__entity_code=entity_code)

    if keywords:
        queryset = queryset.filter(
            Q(title__icontains=keywords) |
            Q(notes__icontains=keywords)
        )

    if vendor:
        queryset = queryset.filter(
            Q(title__icontains=vendor) |
            Q(notes__icontains=vendor)
        )

    if category:
        queryset = queryset.filter(category=category)

    # Limit results
    deadlines = queryset[:20].values(
        "id", "title", "entity__entity_code", "category", "frequency",
        "next_due", "estimated_amount", "autopay"
    )

    return JsonResponse({
        "count": queryset.count(),
        "deadlines": list(deadlines)
    })
