from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Article, Category, Comment

User = get_user_model()


class ArticleModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', email='a@a.com', password='pw', role='journalist')
        self.category = Category.objects.create(name='News', slug='news')

    def test_article_slug_auto_generation(self):
        article = Article.objects.create(title='Hello World Test', author=self.user)
        self.assertEqual(article.slug, 'hello-world-test')

    def test_article_reading_time_calculation(self):
        body = "word " * 400
        article = Article.objects.create(title='Long Article', body=body, author=self.user)
        self.assertEqual(article.reading_time, 2)

    def test_published_at_auto_set(self):
        article = Article.objects.create(title='Draft', author=self.user, status='draft')
        self.assertIsNone(article.published_at)
        article.status = 'published'
        article.save()
        self.assertIsNotNone(article.published_at)

    def test_comment_anonymous_identifier(self):
        article = Article.objects.create(title='Title', author=self.user)
        comment = Comment.objects.create(article=article, user=self.user, body='Hello')
        self.assertTrue(comment.anonymous_identifier.startswith('COM'))


class ArticleAPITests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin', email='ad@m.com', password='pw', role='admin')
        self.editor = User.objects.create_user(username='editor', email='ed@m.com', password='pw', role='editor')
        self.journalist = User.objects.create_user(
            username='journo', email='j@m.com', password='pw', role='journalist')
        self.reader = User.objects.create_user(username='reader', email='r@m.com', password='pw', role='reader')

        self.category = Category.objects.create(name='Tech', slug='tech')
        self.article = Article.objects.create(
            title='Tech News',
            slug='tech-news',
            body='Some content',
            author=self.journalist,
            category=self.category,
            status='published',
            published_at=timezone.now()
        )
        self.comment = Comment.objects.create(
            article=self.article,
            user=self.reader,
            body='Great news',
            status='approved'
        )

    def test_list_articles_public(self):
        url = reverse('public-articles')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_article_detail_public(self):
        url = reverse('public-article-detail', kwargs={'slug': self.article.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Tech News')

    def test_comments_list_public(self):
        url = reverse('public-article-comments', kwargs={'slug': self.article.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['body'], 'Great news')

    def test_create_comment_authenticated(self):
        self.client.force_authenticate(user=self.reader)
        url = reverse('public-create-comment', kwargs={'slug': self.article.slug})
        response = self.client.post(url, {'body': 'New comment'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_comment_unauthenticated(self):
        url = reverse('public-create-comment', kwargs={'slug': self.article.slug})
        response = self.client.post(url, {'body': 'New comment'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cms_list_articles_permission_denied_for_reader(self):
        self.client.force_authenticate(user=self.reader)
        url = reverse('cms-articles-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cms_list_articles_success_for_journalist(self):
        self.client.force_authenticate(user=self.journalist)
        url = reverse('cms-articles-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cms_create_article_editor(self):
        self.client.force_authenticate(user=self.editor)
        url = reverse('cms-articles-list')
        data = {
            'title': 'New Draft',
            'body': 'Draft body',
            'status': 'draft',
            'category': self.category.id,
            'is_breaking': 'true'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.count(), 2)

    def test_cms_update_article_editor(self):
        self.client.force_authenticate(user=self.editor)
        url = reverse('cms-articles-detail', kwargs={'pk': self.article.pk})
        data = {
            'title': 'Updated Tech News'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated Tech News')

    def test_cms_delete_article_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('cms-articles-detail', kwargs={'pk': self.article.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Article.objects.count(), 0)

    def test_cms_publish_action_editor(self):
        draft = Article.objects.create(title='To Publish', author=self.journalist, status='draft')
        self.client.force_authenticate(user=self.editor)
        url = reverse('cms-articles-publish', kwargs={'pk': draft.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        draft.refresh_from_db()
        self.assertEqual(draft.status, 'published')
        self.assertIsNotNone(draft.published_at)

    def test_cms_reject_action_editor(self):
        review_article = Article.objects.create(title='In Review', author=self.journalist, status='in_review')
        self.client.force_authenticate(user=self.editor)
        url = reverse('cms-articles-reject', kwargs={'pk': review_article.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review_article.refresh_from_db()
        self.assertEqual(review_article.status, 'draft')
