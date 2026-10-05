from rest_framework import serializers
from .models import Author, BlogPost, Category, Tag, kehem_note

class KehemNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = kehem_note
        fields = '__all__'  # or specify the fields you want to include
        read_only_fields = ('id', 'created_at', 'updated_at')  # example of read-only fields


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")
        read_only_fields = ("id", "slug")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")
        read_only_fields = ("id", "slug")


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = (
            "id", "name", "title", "bio", "avatar", "linkedin", "twitter",
            "website", "created_at",
        )
        read_only_fields = ("id", "created_at")


class BlogPostSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)

    class Meta:
        model = BlogPost
        fields = (
            "id", "title", "slug", "excerpt", "content_markdown", "cover_image",
            "category", "category_name", "author", "author_name", "tags",
            "tags_detail", "meta_title", "meta_description", "canonical_url",
            "og_title", "og_description", "og_image", "no_index", "status",
            "featured", "published_at", "read_time", "views", "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id", "slug", "read_time", "views", "created_at", "updated_at",
        )

    def get_author_name(self, obj):
        return obj.author.name if obj.author else None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    @staticmethod
    def _kehem_team():
        author, _ = Author.objects.get_or_create(
            name="KEHEM Team",
            defaults={
                "title": "KEHEM IT",
                "bio": "Design-led engineers building trusted websites, SaaS products, and business systems.",
            },
        )
        return author

    def create(self, validated_data):
        validated_data["author"] = self._kehem_team()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["author"] = self._kehem_team()
        return super().update(instance, validated_data)
