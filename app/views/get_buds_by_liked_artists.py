from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from ..db_models.User import User
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication

import logging
logger = logging.getLogger(__name__)

class get_buds_by_liked_artists(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_liked_artists, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user = request.user

            buds = []
            for artist in user.likes_artists.all():
                buds.extend(artist.users.all())

            # Filter out the user and duplicates
            buds = list({bud.uid: bud for bud in buds if bud.uid != user.uid}.values())

            buds_data = []
            total_common_artists_count = 0

            for bud in buds:
                bud_liked_artist_uids = [artist.uid for artist in bud.likes_artists.all()]

                common_artists = user.likes_artists.filter(uid__in=bud_liked_artist_uids)
                common_artists_count = len(common_artists)
                total_common_artists_count += common_artists_count

                buds_data.append({
                    'bud_uid': bud.uid,
                    'common_artists_count': common_artists_count,
                    'common_artists': [artist.serialize() for artist in common_artists]
                })

            return JsonResponse({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'data': {
                    'buds': buds_data,
                    'totalCommonArtistsCount': total_common_artists_count,
                }
            })
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)