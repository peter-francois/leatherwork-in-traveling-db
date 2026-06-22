from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .choices import DocumentType
from .models import LegalDocument
from .services import get_legal_document_content
from .validators import version_validator


# Helpers
def make_terms_document() -> LegalDocument:
    """Create a Terms (CGV) legal document"""
    return LegalDocument.objects.create(
        document_type=DocumentType.TERMS,
        version="2024-01-01",
        content_fr="Contenu en français",
        content_en="Content in english",
    )


# Test case
class GetLegalDocumentContentTest(TestCase):
    """Tests for the get_legal_document_content service"""

    def setUp(self):
        self.document = make_terms_document()

    def test_returns_french_content(self):
        """Should return french content when lang is fr"""
        result = get_legal_document_content(DocumentType.TERMS, "fr")
        self.assertEqual(result, self.document.content_fr)

    def test_returns_english_content(self):
        """Should return english content when lang is en"""
        result = get_legal_document_content(DocumentType.TERMS, "en")
        self.assertEqual(result, self.document.content_en)

    def test_returns_latest_version(self):
        """Should return the latest version of the document using a mocked future date"""
        future = timezone.now() + timedelta(days=1)
        with patch("django.utils.timezone.now", return_value=future):
            new_doc = LegalDocument.objects.create(
                document_type=DocumentType.TERMS,
                version="2024-06-01",
                content_fr="Nouveau contenu",
                content_en="New content",
            )
        result = get_legal_document_content(DocumentType.TERMS, "fr")
        self.assertEqual(result, new_doc.content_fr)

    def test_raises_error_when_document_not_found(self):
        """Should raise DoesNotExist when no document found"""
        with self.assertRaises(LegalDocument.DoesNotExist):
            get_legal_document_content(DocumentType.COOKIES, "fr")


class VersionValidatorTest(TestCase):
    """Tests for the version_validator"""

    def test_valid_format(self):
        """Should not raise for valid YYYY-MM-DD format"""
        try:
            version_validator("2024-01-01")
        except ValidationError:
            self.fail("version_validator raised ValidationError for valid format")

    def test_invalid_format_letters(self):
        """Should raise ValidationError for non-numeric format"""
        with self.assertRaises(ValidationError):
            version_validator("abcd-ef-gh")

    def test_invalid_format_missing_dashes(self):
        """Should raise ValidationError when dashes are missing"""
        with self.assertRaises(ValidationError):
            version_validator("20240101")

    def test_invalid_format_wrong_order(self):
        """Should raise ValidationError for DD-MM-YYYY format"""
        with self.assertRaises(ValidationError):
            version_validator("01-01-2024")

    def test_invalid_format_empty(self):
        """Should raise ValidationError for empty string"""
        with self.assertRaises(ValidationError):
            version_validator("")
