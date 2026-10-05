from django import forms
from .models import Task, ShortURL, BlogPost, Category, Tag, Author
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['task', 'date', 'completed']


class URLForm(forms.ModelForm):
    class Meta:
        model = ShortURL
        fields = ['original_url']



class BlogPostForm(forms.ModelForm):

    published_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local"
            },
            format="%Y-%m-%dT%H:%M"
        )
    )

    class Meta:
        model = BlogPost

        exclude = [
            "slug",
            "content_html",
            "read_time",
            "views",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk and self.instance.published_at:
            self.initial["published_at"] = (
                self.instance.published_at.strftime(
                    "%Y-%m-%dT%H:%M"
                )
            )

        self.helper = FormHelper()
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            Fieldset(
                "Content",
                "title",
                "excerpt",
                "content_markdown",
                "cover_image",
            ),
            Fieldset(
                "Organization",
                "category",
                "author",
                "tags",
            ),
            Fieldset(
                "SEO",
                "meta_title",
                "meta_description",
                "canonical_url",
                "og_title",
                "og_description",
                "og_image",
                "no_index",
            ),
            Fieldset(
                "Publishing",
                "status",
                "featured",
                "published_at",
            ),
            Submit(
                "submit",
                "Save Post"
            )
        )

    def clean_meta_title(self):
        value = self.cleaned_data.get(
            "meta_title"
        )

        if value and len(value) > 60:
            raise forms.ValidationError(
                "Meta title should be less than 60 characters."
            )

        return value

    def clean_meta_description(self):
        value = self.cleaned_data.get(
            "meta_description"
        )

        if value and len(value) > 160:
            raise forms.ValidationError(
                "Meta description should be less than 160 characters."
            )

        return value


class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ["name"]


class TagForm(forms.ModelForm):

    class Meta:
        model = Tag
        fields = ["name"]


class AuthorForm(forms.ModelForm):

    class Meta:
        model = Author

        fields = [
            "name",
            "title",
            "bio",
            "avatar",
            "linkedin",
            "twitter",
            "website",
        ]