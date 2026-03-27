from .models import LegalDocument

def get_legal_document_content(document_type: str, lang: str) -> str:
    latest = LegalDocument.objects.filter(
        document_type=document_type
    ).latest('created_at')

    content = latest.content_fr if lang == 'fr' else latest.content_en

    return content