from django.core.validators import RegexValidator

version_validator = RegexValidator(
    regex=r'^\d{4}-\d{2}-\d{2}$',
    message="Version format must be YYYY-MM-DD."
)