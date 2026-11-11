from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Campus,
    FaithSection,
    GalleryImage,
    LeadershipTeam,
    MinistryExpression,
    SiteArticle,
    SiteEvent,
    SiteProfile,
    Testimonial,
    ThursdaySession,
)
from .serializers import (
    CampusSerializer,
    FaithSectionSerializer,
    GalleryImageSerializer,
    LeadershipTeamSerializer,
    MinistryExpressionSerializer,
    SiteArticleSerializer,
    SiteEventSerializer,
    SiteProfileSerializer,
    TestimonialSerializer,
    ThursdaySessionSerializer,
)


class PublicSiteContentView(APIView):
    """Return every content collection the website renders in one payload.

    The keys match the frontend's content modules, so a page can consume the
    response without reshaping it.
    """

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        profile = SiteProfile.objects.first() or SiteProfile()
        payload = {
            'site': SiteProfileSerializer(profile).data,
            'nav': profile.nav,
            'ministryExpressions': MinistryExpressionSerializer(
                MinistryExpression.objects.all(), many=True
            ).data,
            'campuses': CampusSerializer(Campus.objects.all(), many=True).data,
            'events': SiteEventSerializer(
                SiteEvent.objects.all(), many=True
            ).data,
            'thursdaySessions': ThursdaySessionSerializer(
                ThursdaySession.objects.all(), many=True
            ).data,
            'gallery': GalleryImageSerializer(
                GalleryImage.objects.all(), many=True
            ).data,
            'testimonials': TestimonialSerializer(
                Testimonial.objects.all(), many=True
            ).data,
            'leadershipTeams': LeadershipTeamSerializer(
                LeadershipTeam.objects.all(), many=True
            ).data,
            'articles': SiteArticleSerializer(
                SiteArticle.objects.all(), many=True
            ).data,
            'statementOfFaith': FaithSectionSerializer(
                FaithSection.objects.all(), many=True
            ).data,
        }

        response = Response(payload)
        response['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=3600'
        return response
