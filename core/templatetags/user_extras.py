from django import template
from django.utils.translation import gettext as _

register = template.Library()

EXPERIENCE_LABELS = {
    0: _('less than 1 year'),
    1: _('1–3 years'),
    3: _('3–5 years'),
    5: _('more than 5 years'),
}

@register.filter
def experience_label(value):
    return EXPERIENCE_LABELS.get(value, _("N/A"))
