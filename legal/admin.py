from django.contrib import admin
from .models import LegalDocument


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        if change:
            obj.pk = None
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ('document_type', 'version', 'created_at')
    list_filter = ('document_type',) 
    ordering = ('-created_at',)