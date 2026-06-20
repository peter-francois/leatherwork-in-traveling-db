from django.http import JsonResponse

from catalog.models import Product


def get_product_images(request, article_id):
    try:
        product = Product.objects.get(id=article_id)
        images = [
            product.image1.url if product.image1 else None,
            product.image2.url if product.image2 else None,
            product.image3.url if product.image3 else None,
            product.image4.url if product.image4 else None,
            product.image5.url if product.image5 else None,
            product.image6.url if product.image6 else None,
        ]
        images = [image for image in images if image]
        return JsonResponse(
            {
                "images": images,
                "nom": product.name,
                "description": product.description if product.description else None,
                "discount": product.discount,
                "prix": product.price,
                "en_attente_dans_panier": product.pending_in_cart,
                "sur_commande": product.on_demand,
            }
        )
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
