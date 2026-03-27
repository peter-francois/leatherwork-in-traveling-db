def generate_sitemap_index(base_url: str, langs: list[str]) -> str:
    urls = [f'{base_url}sitemap-{lang}.xml' for lang in langs]
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f'  <sitemap>\n    <loc>{url}</loc>\n  </sitemap>\n'
    xml += '</sitemapindex>'
    
    return xml