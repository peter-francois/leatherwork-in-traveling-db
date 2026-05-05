from django.urls import path
from . import  views


urlpatterns = [    
    path('get_product_images/<int:article_id>/', views.get_product_images, name='get_product_images'),
]