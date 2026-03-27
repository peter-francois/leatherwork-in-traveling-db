from django.http import HttpResponseForbidden, HttpResponsePermanentRedirect

class CustomRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        # Dictionnaire des redirections permanentes
        self.redirects = {
            '/': '/fr/',
            '/tous-les-produits/': '/fr/produits',
            '/tous-les-produits/macrames/': '/fr/produits/macrames',
            '/tous-les-produits/maroquinerie/': '/fr/produits/maroquinerie',
            '/tous-les-produits/hybride/': '/fr/produits/hybride',
            '/cgv/': '/fr/cgv',
            '/mentions-legales/': '/fr/mentions-legales',
            '/cookies/': '/fr/cookies',
            '/politique-confidentialite/': '/fr/politique-confidentialite',
            '/paiement_reussi/': '/fr/paiement_reussi',
            '/paiement_annule/': '/fr/paiement_annule',
            '/creation-sur-mesure/': '/fr/creation-sur-mesure',
            '/panier/': '/fr/panier'
        }

    def __call__(self, request):
        path = request.path

        # Blocage des requêtes suspectes liées à WordPress
        if any(wp_path in path for wp_path in ['/wp-includes', '/wp-content', '/wp-config', '/wp-admin', '/wordpress']):
            return HttpResponseForbidden("Accès interdit")

        # Redirection si l'ancienne URL est dans la liste
        if path in self.redirects:
            return HttpResponsePermanentRedirect(self.redirects[path])

        # Sinon, on continue normalement
        response = self.get_response(request)
        return response