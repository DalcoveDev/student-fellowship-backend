import logging

from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Category, Tag, Article, ArticleRevision, Comment
from .serializers import (
    CategorySerializer, TagSerializer, ArticleListSerializer,
    ArticleDetailSerializer, CommentSerializer, ArticleRevisionSerializer,
    CMSArticleWriteSerializer, CMSCommentSerializer,
)
from users.permissions import IsJournalist, IsEditor, IsAdmin

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


class ArticleListView(generics.ListAPIView):
    serializer_class = ArticleListSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = (
            Article.objects
            .filter(status='published', published_at__lte=timezone.now())
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
    queryset = (
        Article.objects
        .filter(status='published')
        .select_related('author', 'category')
        .prefetch_related('tags', 'co_authors', 'revisions__author')
    )
    serializer_class = ArticleDetailSerializer
    lookup_field = 'slug'
    permission_classes = (permissions.AllowAny,)

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
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.instance
        old_title = instance.title
        old_subtitle = instance.subtitle
        old_body = instance.body

        article = serializer.save()

        if old_title != article.title or old_subtitle != article.subtitle or old_body != article.body:
            ArticleRevision.objects.create(
                article=article,
                author=self.request.user,
                title=old_title,
                subtitle=old_subtitle,
                body=old_body,
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
