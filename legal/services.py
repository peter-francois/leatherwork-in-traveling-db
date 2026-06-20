from django.urls import reverse
from django.utils import translation

from legal.choices import DocumentType

from .models import LegalDocument


def get_legal_document_content(document_type: str, lang: str) -> str:
    latest = LegalDocument.objects.filter(document_type=document_type).latest(
        "created_at"
    )

    content = latest.content_fr if lang == "fr" else latest.content_en
    with translation.override(lang):
        if document_type in (DocumentType.TERMS, DocumentType.LEGAL_MENTIONS):
            content = content.replace("cookies_url", reverse("legal:cookies"))
            content = content.replace(
                "privacy_policy_url", reverse("legal:privacy_policy")
            )

        if document_type == DocumentType.LEGAL_MENTIONS:
            content = content.replace("cgv_url", reverse("legal:terms"))

    return content
