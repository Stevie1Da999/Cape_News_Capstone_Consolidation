"""Website forms for signing up and writing stories."""

# Model forms keep the website forms linked to the database models.
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Article, Newsletter, Publisher, User


class UserRegistrationForm(UserCreationForm):
    """Registration form for the three user roles used by the news website."""

    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        label="Account role",
    )

    class Meta:
        model = User
        fields = ["username", "email", "role", "password1", "password2"]

    def clean_role(self):
        # Check the role again on the backend in case the form is changed.
        """Check that the chosen account role is one we support."""

        role = self.cleaned_data["role"]
        valid_roles = {choice[0] for choice in User.ROLE_CHOICES}

        if role not in valid_roles:
            raise forms.ValidationError("Please select a valid account role.")

        return role

    def save(self, commit=True):
        # Save the role selected by the user onto their account.
        """Save the selected role together with the new account."""

        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]

        if commit:
            user.save()

        return user


class ArticleForm(forms.ModelForm):
    """Form used by journalists and editors when working with articles."""

    class Meta:
        model = Article
        fields = ["title", "content", "publisher"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 12}),
        }

    def __init__(self, *args, user=None, **kwargs):
        """Limit the publisher choices to the journalist's own publishers."""

        super().__init__(*args, **kwargs)

        # A journalist should only be able to choose publishers they work for.
        if user and user.role == "journalist":
            self.fields["publisher"].queryset = user.publishers.all()


class NewsletterForm(forms.ModelForm):
    """Form for creating and editing newsletters."""

    class Meta:
        model = Newsletter
        fields = ["title", "description", "articles"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "articles": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        """Only offer approved articles for newsletter selection."""

        super().__init__(*args, **kwargs)

        # Newsletters shown to readers should only contain approved articles.
        self.fields["articles"].queryset = Article.objects.filter(
            approved=True
        ).order_by("-created_at")


class SubscriptionForm(forms.Form):
    """Lets a Reader choose publishers and journalists to follow."""

    publishers = forms.ModelMultipleChoiceField(
        queryset=Publisher.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )
    journalists = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role="journalist"),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )
