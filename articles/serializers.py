from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Category, Tag, Article, ArticleRevision, Comment
from users.serializers import UserSerializer

User = get_user_model()


class CMSCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'color_accent', 'parent', 'order')


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'color_accent', 'parent', 'order', 'subcategories')

    def get_subcategories(self, obj):
        children = obj.subcategories.all()
        return CategorySerializer(children, many=True).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


# ---------------------------------------------------------------------------
# Shared mixin: resolve cover_image to an absolute URL regardless of storage.
# ---------------------------------------------------------------------------

class CoverImageMixin:
    """DRY helper for cover_image URL resolution across serializers."""

    def get_cover_image(self, obj):
        if not obj.cover_image:
            return None
        name = obj.cover_image.name
        # Cloudinary or other absolute URLs
        if name.startswith('http://') or name.startswith('https://'):
            return name
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.cover_image.url)
        return obj.cover_image.url


class ArticleListSerializer(CoverImageMixin, serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = (
            'id', 'title', 'slug', 'subtitle', 'cover_image', 'category', 'tags',
            'author', 'status', 'published_at', 'is_breaking', 'is_featured',
            'is_premium', 'reading_time', 'view_count',
        )


class ArticleRevisionSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = ArticleRevision
        fields = ('id', 'article', 'author', 'title', 'subtitle', 'body', 'created_at')


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'article', 'user', 'parent', 'body', 'status', 'created_at', 'replies')
        read_only_fields = ('id', 'article', 'user', 'status', 'created_at')

    def get_user(self, obj):
        return {
            'username': obj.anonymous_identifier or "Anonymous",
            'first_name': '',
            'last_name': '',
            'avatar': None,
        }

    def get_replies(self, obj):
        approved_replies = obj.replies.filter(status='approved')
        return CommentSerializer(approved_replies, many=True).data


class CMSCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'article', 'user', 'parent', 'body', 'status', 'created_at')
        read_only_fields = ('id', 'user', 'status', 'created_at')


class ArticleDetailSerializer(CoverImageMixin, serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    co_authors = UserSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    revisions = ArticleRevisionSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = (
            'id', 'title', 'slug', 'subtitle', 'body', 'cover_image', 'category', 'tags',
            'author', 'co_authors', 'status', 'published_at', 'is_breaking', 'is_featured',
            'is_premium', 'reading_time', 'view_count', 'seo_title', 'seo_description',
            'created_at', 'updated_at', 'comments', 'revisions',
        )

    def get_comments(self, obj):
        top_level_comments = obj.comments.filter(parent__isnull=True, status='approved')
        return CommentSerializer(top_level_comments, many=True).data


class CMSArticleWriteSerializer(serializers.ModelSerializer):
    """
    Write-only serializer for CMS article create/update.
    Accepts category as an integer PK and tags as a list of integer PKs.
    Boolean fields (is_breaking, is_featured, is_premium) accept string 'true'/'false'
    from multipart/form-data in addition to booleans.
    """
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Article
        fields = (
            'title', 'subtitle', 'body', 'cover_image', 'category', 'tags', 'author',
            'status', 'published_at', 'is_breaking', 'is_featured', 'is_premium',
            'seo_title', 'seo_description',
        )

    def validate(self, attrs):
        """Enforce a sensible relationship between status and publication time."""
        instance = self.instance
        status_value = attrs.get('status', instance.status if instance else 'draft')

        if 'published_at' in attrs:
            published_at = attrs.get('published_at')
        elif instance is not None:
            published_at = instance.published_at
        else:
            published_at = None

        now = timezone.now()

        # Only reject an invalid schedule when the caller is actively setting
        # the schedule. A stored schedule that just became due is auto-published
        # by Article.save(); it should not block unrelated edits.
        touched_schedule = 'status' in attrs or 'published_at' in attrs

        if status_value == 'scheduled' and touched_schedule:
            if not published_at:
                raise serializers.ValidationError({
                    'published_at': 'Choose the date and time when this article should be published.'
                })
            already_scheduled = instance is not None and instance.status == 'scheduled'
            if published_at <= now and not already_scheduled:
                raise serializers.ValidationError({
                    'published_at': 'Scheduled publication time must be in the future.'
                })
        elif status_value == 'published' and not published_at:
            # Publishing immediately without a date uses the current time.
            attrs['published_at'] = now

        return attrs

    def to_internal_value(self, data):
        # Coerce string booleans from multipart form-data to real booleans
        mutable = data.copy() if hasattr(data, 'copy') else dict(data)
        for field in ('is_breaking', 'is_featured', 'is_premium'):
            val = mutable.get(field)
            if isinstance(val, str):
                mutable[field] = val.lower() in ('true', '1', 'yes')
        # Handle empty category string -> None
        if mutable.get('category') in ('', 'null'):
            mutable['category'] = None
        # Handle empty author string -> omit
        if mutable.get('author') in ('', 'null', None):
            mutable.pop('author', None)
        return super().to_internal_value(mutable)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        try:
            article = Article.objects.create(**validated_data)
        except Exception as exc:
            raise serializers.ValidationError({
                'cover_image': f'Media upload failed: {exc}'
            }) from exc
        article.tags.set(tags)
        return article

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
        except Exception as exc:
            raise serializers.ValidationError({
                'cover_image': f'Media upload failed: {exc}'
            }) from exc
        if tags is not None:
            instance.tags.set(tags)
        return instance
