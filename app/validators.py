from email_validator import EmailNotValidError, validate_email
import phonenumbers
from wtforms.validators import ValidationError


# Common disposable domains to block quick fake signups.
DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com",
    "tempmail.com",
    "10minutemail.com",
    "guerrillamail.com",
    "yopmail.com",
}


def normalize_and_validate_email(raw_email):
    try:
        result = validate_email(raw_email, check_deliverability=True)
    except EmailNotValidError as exc:
        raise ValidationError(str(exc)) from exc

    email = result.normalized
    domain = email.split("@", 1)[1].lower()
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        raise ValidationError("Disposable email addresses are not allowed.")

    return email


def normalize_and_validate_phone(raw_phone, default_region="IN"):
    try:
        parsed = phonenumbers.parse(raw_phone, default_region)
    except phonenumbers.NumberParseException as exc:
        raise ValidationError("Enter a valid phone number.") from exc

    if not phonenumbers.is_valid_number(parsed):
        raise ValidationError("Enter a valid phone number.")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
