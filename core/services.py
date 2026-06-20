from django.contrib.sessions.models import Session


def generate_sitemap_index(base_url: str, langs: list[str]) -> str:
    urls = [f"{base_url}sitemap-{lang}.xml" for lang in langs]

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f"  <sitemap>\n    <loc>{url}</loc>\n  </sitemap>\n"
    xml += "</sitemapindex>"

    return xml


def get_session_expiration(request):
    """
    Returns the expiration date of the current user session.
    """
    session_key = request.session.session_key
    if not session_key:
        return None

    try:
        session = Session.objects.get(session_key=session_key)
        return session.expire_date
    except Session.DoesNotExist:
        request.session.create()
        return None
