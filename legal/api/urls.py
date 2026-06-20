from django.urls import path

from . import views

urlpatterns = [
    path(
        "get_document_content/<str:document_type>/<str:lang>/",
        views.get_document_content,
        name="get_document_content",
    ),
]
