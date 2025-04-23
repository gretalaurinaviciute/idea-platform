from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    STATUS_CHOICES = [
        ('APPROVED', _('Approved')),
        ('PENDING', _('Pending')),
    ]

    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    suggested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suggested_categories"
    )

    def __str__(self):
        return self.name


class User(AbstractUser):
    USER_TYPES = [
        ('ADMIN', _('administrator')),
        ('SPECIALIST', _('skilled specialist')),
        ('PROPOSER', _('idea proposer')),
    ]
    type = models.CharField(max_length=20, choices=USER_TYPES, verbose_name=_("user type"))
    description = models.TextField(blank=True, null=True, verbose_name=_("description"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("category"))
    skills = models.TextField(blank=True, null=True, verbose_name=_("skills"))
    experience = models.IntegerField(blank=True, null=True, verbose_name=_("experience"))
    agreed_to_terms_at = models.DateTimeField(null=True, blank=True, verbose_name=_("agreed to terms at"))

    def __str__(self):
        return self.username

    def is_specialist(self):
        return self.type == "SPECIALIST"

    def is_proposer(self):
        return self.type == "PROPOSER"


class Idea(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ideas")
    title = models.CharField(max_length=255, verbose_name=_("title"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("category"))
    description = models.TextField(verbose_name=_("description"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))

    def __str__(self):
        return self.title


class IdeaFile(models.Model):
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="idea_files/", verbose_name=_("file"))

    def __str__(self):
        return f"{_('File for')} {self.idea.title}"


class Portfolio(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolios")
    image = models.ImageField(upload_to="portfolio_images/", null=True, blank=True, verbose_name=_("image"))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("uploaded at"))

    def __str__(self):
        return f"{self.user.username} — {_('portfolio image')}"


class SavedIdea(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_ideas')
    idea = models.ForeignKey('Idea', on_delete=models.CASCADE, related_name='saves')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'idea')
        verbose_name = _("saved idea")
        verbose_name_plural = _("saved ideas")

    def __str__(self):
        return f"{self.user.username} {_('saved')} {self.idea.title}"


class Review(models.Model):
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="given_reviews")
    reviewed_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_reviews")
    rating = models.IntegerField(choices=[(i, f"{i} {_('star') if i == 1 else _('stars')}") for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True, verbose_name=_("comment"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))

    class Meta:
        unique_together = ('reviewer', 'reviewed_user')
        verbose_name = _("review")
        verbose_name_plural = _("reviews")

    def __str__(self):
        return f"{self.reviewer} → {self.reviewed_user} ({self.rating})"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages", verbose_name=_("sender"))
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages", verbose_name=_("receiver"))
    body = models.TextField(verbose_name=_("message body"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("timestamp"))
    is_read = models.BooleanField(default=False, verbose_name=_("is read"))

    class Meta:
        ordering = ['timestamp']
        verbose_name = _("message")
        verbose_name_plural = _("messages")

    def __str__(self):
        return f"{self.sender} ➜ {self.receiver}: {self.body[:30]}"
