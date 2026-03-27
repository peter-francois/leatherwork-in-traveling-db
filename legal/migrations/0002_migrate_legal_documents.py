from django.db import migrations

def migrate_legal_data(apps, schema_editor):
    CGV = apps.get_model('page_vente', 'CGV')
    CookiesPolicy = apps.get_model('page_vente', 'CookiesPolicy')
    LegalMention = apps.get_model('page_vente', 'LegalMention')
    PrivacyPolicy = apps.get_model('page_vente', 'PrivacyPolicy')
    LegalDocument = apps.get_model('legal', 'LegalDocument')

    for obj in CGV.objects.all():
        LegalDocument.objects.create(
            document_type='cgv',
            version=obj.version,
            content_fr=obj.content_fr,
            content_en=obj.content_en,
            created_at=obj.created_at,
        )

    for obj in CookiesPolicy.objects.all():
        LegalDocument.objects.create(
            document_type='cookies',
            version=obj.version,
            content_fr=obj.content_fr,
            content_en=obj.content_en,
            created_at=obj.created_at,
        )

    for obj in LegalMention.objects.all():
        LegalDocument.objects.create(
            document_type='legal_mentions',
            version=obj.version,
            content_fr=obj.content_fr,
            content_en=obj.content_en,
            created_at=obj.created_at,
        )

    for obj in PrivacyPolicy.objects.all():
        LegalDocument.objects.create(
            document_type='privacy_policy',
            version=obj.version,
            content_fr=obj.content_fr,
            content_en=obj.content_en,
            created_at=obj.created_at,
        )

class Migration(migrations.Migration):

    dependencies = [
        ('legal', '0001_initial'),
        ('page_vente', '0043_allproducts_discount'),  # adapte le numéro
    ]

    operations = [
        migrations.RunPython(migrate_legal_data),
    ]