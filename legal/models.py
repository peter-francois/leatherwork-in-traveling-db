from django.db import models
from .choices import DocumentType
from .validators import version_validator


class LegalDocument(models.Model):

    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
    )
    version = models.CharField(
        max_length=20,
        help_text="Ex: 2024-06-01",
        validators=[version_validator]
    )
    content_fr = models.TextField(default='')
    content_en = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_document_type_display()} {self.version}"
    

    class Meta:
        ordering = ['-created_at']
        unique_together = [['document_type', 'version']]