import logging

from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Category, Tag, Article, ArticleRevision, Comment
from .serializers import (
    CategorySerializer, TagSerializer, ArticleListSerializer,
    ArticleDetailSerializer, CommentSerializer,
    CMSArticleWriteSerializer, CMSCommentSerializer,
)
from users.permissions import IsJournalist, IsEditor

logger = logging.getLogger(__name__)

# ================= PUBLIC API VIEWS =================


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
    serializer_class = CategorySerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None  # Categories are small; return all


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None  # Tags are small; return all


class ArticlePagination(PageNumberPagination):
    """Pagination that lets public pages request the number of articles they
    actually display (frontend sections can show up to 50)."""

    page_size = 50
    page_size_query_param = 'limit'
    max_page_size = 200


class ArticleListView(generics.ListAPIView):
    serializer_class = ArticleListSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = ArticlePagination

    def get_queryset(self):
        # Promote due scheduled articles before listing. This keeps the public
        # site accurate without requiring Celery beat to be running.
        Article.publish_due_scheduled()

        queryset = (
            Article.objects
            .filter(status='published')
            .filter(
                Q(published_at__lte=timezone.now()) |
                Q(published_at__isnull=True)
            )
            .select_related('author', 'category')
            .prefetch_related('tags')
        )

        # Filtering
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        tag_slug = self.request.query_params.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        author_username = self.request.query_params.get('author')
        if author_username:
            queryset = queryset.filter(author__username=author_username)

        is_breaking = self.request.query_params.get('is_breaking')
        if is_breaking is not None:
            queryset = queryset.filter(is_breaking=is_breaking.lower() == 'true')

        is_featured = self.request.query_params.get('is_featured')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')

        is_premium = self.request.query_params.get('is_premium')
        if is_premium is not None:
            queryset = queryset.filter(is_premium=is_premium.lower() == 'true')

        # Search
        search_query = self.request.query_params.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(subtitle__icontains=search_query) |
                Q(body__icontains=search_query)
            )

        return queryset.distinct()


class ArticleDetailView(generics.RetrieveAPIView):
    serializer_class = ArticleDetailSerializer
    lookup_field = 'slug'
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        # Make an article visible as soon as its scheduled time is reached.
        Article.publish_due_scheduled()
        return (
            Article.objects
            .filter(status='published')
            .filter(
                Q(published_at__lte=timezone.now()) |
                Q(published_at__isnull=True)
            )
            .select_related('author', 'category')
            .prefetch_related('tags', 'co_authors', 'revisions__author')
        )

    def get_object(self):
        obj = super().get_object()
        # Atomic view count increment (no race condition)
        Article.objects.filter(pk=obj.pk).update(view_count=F('view_count') + 1)
        obj.refresh_from_db(fields=['view_count'])
        return obj


class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        article_slug = self.kwargs.get('slug')
        article = get_object_or_404(Article, slug=article_slug)
        serializer.save(user=self.request.user, article=article, status='approved')


class ArticleCommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None  # Comments per-article are typically small

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        return (
            Comment.objects
            .filter(article__slug=slug, parent__isnull=True, status='approved')
            .select_related('user')
            .prefetch_related('replies__user')
        )


# ================= CMS (ADMIN/STAFF) API VIEWS =================


class CMSArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleDetailSerializer
    permission_classes = (IsJournalist,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'subtitle']
    ordering_fields = ['created_at', 'published_at', 'view_count']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CMSArticleWriteSerializer
        return ArticleDetailSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Article.objects.select_related('author', 'category').prefetch_related('tags', 'co_authors')
        if user.role in ('admin', 'editor') or user.is_superuser:
            return qs
        return qs.filter(Q(author=user) | Q(co_authors=user)).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        if (user.role == 'admin' or user.is_superuser) and serializer.validated_data.get('author'):
            serializer.save()
        else:
            serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.instance
        old_title = instance.title
        old_subtitle = instance.subtitle
        old_body = instance.body
        user = self.request.user

        # Only admin accounts can change the author of an article
        if not (user.role == 'admin' or user.is_superuser) and 'author' in serializer.validated_data:
            serializer.validated_data.pop('author')

        # Publication date/status consistency is handled by
        # CMSArticleWriteSerializer.validate() and Article.save().

        article = serializer.save()

        if old_title != article.title or old_subtitle != article.subtitle or old_body != article.body:
            ArticleRevision.objects.create(
                article=article,
                author=self.request.user,
                title=old_title,
                subtitle=old_subtitle,
                body=old_body,
            )

    @action(detail=False, methods=['get'])
    def authors(self, request):
        user = request.user
        if not (user.role in ('admin', 'editor') or user.is_superuser):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        users_qs = UserModel.objects.filter(is_active=True).order_by('first_name', 'username')
        authors_data = [
            {
                'id': u.id,
                'username': u.username,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'full_name': u.get_full_name() or u.username,
                'email': u.email,
                'role': u.role,
                'avatar': u.avatar.url if u.avatar else None,
            }
            for u in users_qs
        ]
        return Response(authors_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsEditor])
    def change_author(self, request, pk=None):
        """Reassign an article to another active author (used by the CMS list)."""
        article = self.get_object()
        author_id = request.data.get('author_id')

        if not author_id:
            return Response(
                {'detail': 'author_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        try:
            new_author = UserModel.objects.get(pk=author_id, is_active=True)
        except (UserModel.DoesNotExist, ValueError, TypeError):
            return Response(
                {'detail': 'Author not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        article.author = new_author
        article.save(update_fields=['author'])
        return Response(
            self.get_serializer(article).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsEditor])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.status = 'published'
        article.published_at = timezone.now()
        article.save(update_fields=['status', 'published_at'])
        return Response({'status': 'article published'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsEditor])
    def reject(self, request, pk=None):
        article = self.get_object()
        article.status = 'draft'
        article.save(update_fields=['status'])
        return Response({'status': 'article returned to draft'}, status=status.HTTP_200_OK)


class CMSCategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('order', 'id')
    serializer_class = CategorySerializer
    permission_classes = (IsEditor,)
    pagination_class = None


class CMSTagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = (IsEditor,)
    pagination_class = None


class CMSCommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('user', 'article').all()
    serializer_class = CMSCommentSerializer
    permission_classes = (IsEditor,)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        comment = self.get_object()
        comment.status = 'approved'
        comment.save(update_fields=['status'])
        return Response({'status': 'comment approved'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        comment = self.get_object()
        comment.status = 'flagged'
        comment.save(update_fields=['status'])
        return Response({'status': 'comment flagged'}, status=status.HTTP_200_OK)
