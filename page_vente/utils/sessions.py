from django.contrib.sessions.models import Session


def get_session_expiration(request):
    """
    Récupère la date d'expiration de la session actuelle de l'utilisateur.
    """
    session_key = request.session.session_key
    if not session_key:
        return None  # Aucune session active

    try:
        session = Session.objects.get(session_key=session_key)
        return session.expire_date  # 📌 Date d'expiration de la session
    except Session.DoesNotExist:
        request.session.create()
        return None


