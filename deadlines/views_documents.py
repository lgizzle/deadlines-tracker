from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from .models import Document, Entity


def format_file_size(size_bytes):
    """Convert file size in bytes to human-readable format."""
    if size_bytes is None:
        return "--"

    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


@login_required
def document_list(request):
    """List all documents with filtering by document_type, entity, and source."""
    # Get filter parameters
    entity_filter = request.GET.get("entity", "")
    type_filter = request.GET.get("document_type", "")
    source_filter = request.GET.get("source", "")

    # Base queryset - order by created_at descending
    documents = Document.objects.select_related("entity").order_by("-created_at")

    # Apply filters
    if entity_filter:
        documents = documents.filter(entity__entity_code=entity_filter)
    if type_filter:
        documents = documents.filter(document_type=type_filter)
    if source_filter:
        documents = documents.filter(source=source_filter)

    # Add human-readable file size to each document
    for doc in documents:
        doc.file_size_display = format_file_size(doc.file_size)

    # Get unique values for filter dropdowns
    entities = Entity.objects.filter(status="Active").order_by("entity_code")

    # Get document types with counts for sidebar
    type_counts = (
        Document.objects.values("document_type")
        .annotate(count=Count("id"))
        .order_by("document_type")
    )

    # Map document type codes to display names
    doctype_display = dict(Document.DOCTYPE_CHOICES)
    for tc in type_counts:
        tc["display_name"] = doctype_display.get(tc["document_type"], tc["document_type"])

    # Get unique sources
    sources = (
        Document.objects.values_list("source", flat=True)
        .distinct()
        .order_by("source")
    )
    source_display = dict(Document.SOURCE_CHOICES)
    sources_with_names = [(s, source_display.get(s, s)) for s in sources]

    # Calculate stats
    stats = {
        "total": documents.count(),
        "email": Document.objects.filter(source="email").count(),
        "upload": Document.objects.filter(source="upload").count(),
        "scan": Document.objects.filter(source="scan").count(),
    }

    context = {
        "documents": documents,
        "entities": entities,
        "type_counts": type_counts,
        "sources": sources_with_names,
        "entity_filter": entity_filter,
        "type_filter": type_filter,
        "source_filter": source_filter,
        "stats": stats,
        "doctype_choices": Document.DOCTYPE_CHOICES,
    }

    return render(request, "deadlines/documents/document_list.html", context)


@login_required
def document_detail(request, pk):
    """View single document details."""
    document = get_object_or_404(Document, pk=pk)
    document.file_size_display = format_file_size(document.file_size)

    # Truncate sha256_hash for display (show first 16 and last 16 characters)
    if document.sha256_hash:
        hash_val = document.sha256_hash
        if len(hash_val) > 32:
            document.hash_truncated = f"{hash_val[:16]}...{hash_val[-16:]}"
        else:
            document.hash_truncated = hash_val
    else:
        document.hash_truncated = "--"

    # Get document type display name
    doctype_display = dict(Document.DOCTYPE_CHOICES)
    document.document_type_display = doctype_display.get(
        document.document_type, document.document_type
    )

    # Get source display name
    source_display = dict(Document.SOURCE_CHOICES)
    document.source_display = source_display.get(document.source, document.source)

    context = {
        "document": document,
    }

    return render(request, "deadlines/documents/document_detail.html", context)
