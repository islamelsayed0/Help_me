from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    """
    Validate that the password contains at least one uppercase letter.
    """
    def validate(self, password, user=None):
        if not any(c.isupper() for c in password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_uppercase',
            )

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter.")


class SymbolValidator:
    """
    Validate that the password contains at least one special character (symbol).
    """
    def validate(self, password, user=None):
        special_characters = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_characters for c in password):
            raise ValidationError(
                _("Password must contain at least one special character (symbol)."),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _("Your password must contain at least one special character (symbol).")


