from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from .models import User, Idea, Category, Portfolio, Review
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe


class UserRegisterForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        ('SPECIALIST', _('skilled specialist')),
        ('PROPOSER', _('idea proposer')),
    ]

    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'user-type-radio'}),
        label=_("i am a")
    )

    # specialist fields
    skills_1 = forms.CharField(required=False, max_length=100, label=_("skill 1"))
    skills_2 = forms.CharField(required=False, max_length=100, label=_("skill 2"))
    skills_3 = forms.CharField(required=False, max_length=100, label=_("skill 3"))

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(status="APPROVED"),
        required=False,
        widget=forms.Select(),
        label=_("category")
    )

    EXPERIENCE_CHOICES = [
        (0, _('less than 1 year')),
        (1, _('1-3 years')),
        (3, _('3-5 years')),
        (5, _('more than 5 years')),
    ]

    experience = forms.ChoiceField(
        choices=EXPERIENCE_CHOICES,
        required=False,
        widget=forms.Select(),
        label=_("years of experience")
    )

    agree_to_terms = forms.BooleanField(
        required=True,
        label=mark_safe(
            _('I agree to the <a href="/terms/" target="_blank">Platform Terms of Use & Community Guidelines</a>.')
        ),
        error_messages={'required': _('You must agree to the platform rules to register.')}
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'user_type',
                  'skills_1', 'skills_2', 'skills_3', 'category', 'experience', 'agree_to_terms']

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get("user_type")

        if user_type == "SPECIALIST":
            skills = [
                cleaned_data.get("skills_1"),
                cleaned_data.get("skills_2"),
                cleaned_data.get("skills_3"),
            ]
            if not any(skills):
                self.add_error("skills_1", _("At least one skill is required"))

        return cleaned_data


class IdeaForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(status="APPROVED"),
        required=False,
        empty_label=_("Select a category"),
        widget=forms.Select(attrs={"class": "form-control"})
    )

    new_category = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("Suggest a new category")})
    )

    class Meta:
        model = Idea
        fields = ["title", "category", "description"]

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        new_category = cleaned_data.get("new_category")

        if not category and not new_category:
            raise forms.ValidationError(_("You must select a category or suggest a new one."))

        return cleaned_data


class ProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ["username", "category", "description", "skills", "experience"]

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(status="APPROVED"),
        required=False,
        widget=forms.Select(),
        label=_("category")
    )

    EXPERIENCE_CHOICES = [
        (0, _('less than 1 year')),
        (1, _('1-3 years')),
        (3, _('3-5 years')),
        (5, _('more than 5 years')),
    ]

    experience = forms.ChoiceField(
        choices=EXPERIENCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("years of experience")
    )

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

        if self.instance.is_proposer():
            del self.fields["skills"]
            del self.fields["experience"]


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label=_("old password")
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label=_("new password"),
        help_text=_("your password must be at least 8 characters, cannot be commonly used, and cannot be fully numeric.")
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label=_("new password confirmation"),
        help_text=_("enter the same password as before for verification.")
    )


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f"{i} ★") for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': _('leave an optional comment...')})
        }
