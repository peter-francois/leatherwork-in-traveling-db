from django.shortcuts import render
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
