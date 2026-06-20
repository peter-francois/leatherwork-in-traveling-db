from django.http import HttpResponse, JsonResponse

from ..choices import DocumentType
from ..models import LegalDocument
from ..services import get_legal_document_content


def get_document_content(request, document_type, lang):
    if document_type not in DocumentType.values:
        return JsonResponse({"error": "Invalid document type"}, status=400)

    try:
        content = get_legal_document_content(document_type, lang)

        return HttpResponse(content, content_type="text/html")

    except LegalDocument.DoesNotExist:
        return JsonResponse({"error": "Document not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
