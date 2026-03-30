from django.test import TestCase
from .models import LegalDocument
from .choices import DocumentType
from .services import get_legal_document_content
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch


class GetLegalDocumentContentTest(TestCase):
    """Tests for the get_legal_document_content service"""

    def setUp(self):
        self.document = LegalDocument.objects.create(
            document_type=DocumentType.TERMS,
            version='2024-01-01',
            content_fr='Contenu en français',
            content_en='Content in english',
        )

    def test_returns_french_content(self):
        """Should return french content when lang is fr"""
        result = get_legal_document_content(DocumentType.TERMS, 'fr')
        self.assertEqual(result, self.document.content_fr)

    def test_returns_english_content(self):
        """Should return english content when lang is en"""
        result = get_legal_document_content(DocumentType.TERMS, 'en')
        self.assertEqual(result, self.document.content_en)

    def test_returns_latest_version(self):
        """Should return the latest version of the document using a mocked future date"""
        future = timezone.now() + timedelta(days=1)
        with patch('django.utils.timezone.now', return_value=future):
            new_doc = LegalDocument.objects.create(
                document_type=DocumentType.TERMS,
                version='2024-06-01',
                content_fr='Nouveau contenu',
                content_en='New content',
            )
        result = get_legal_document_content(DocumentType.TERMS, 'fr')
        self.assertEqual(result, new_doc.content_fr)

    def test_raises_error_when_document_not_found(self):
        """Should raise DoesNotExist when no document found"""
        with self.assertRaises(LegalDocument.DoesNotExist):
            get_legal_document_content(DocumentType.COOKIES, 'fr')

