from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .services import get_legal_document_content
from .models import LegalDocument
from .choices import DocumentType


def legal_view(request, document_type):
    latest = LegalDocument.objects.filter(document_type=document_type).latest('created_at')
    return render(request, f'legal/{document_type}.html', {'document': latest})

def terms_view(request):
    return legal_view(request, DocumentType.TERMS)

def cookies_view(request):
    return legal_view(request, DocumentType.COOKIES)

def legal_mentions_view(request):
    return legal_view(request, DocumentType.LEGAL_MENTIONS)

def privacy_policy_view(request):
    return legal_view(request, DocumentType.PRIVACY_POLICY)

def get_document_content(request, document_type, lang):
    if document_type not in DocumentType.values:
        return JsonResponse({'error': 'Invalid document type'}, status=400)

    try:
        content = get_legal_document_content(document_type, lang)

        return HttpResponse(content, content_type="text/html")
    
    except LegalDocument.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)