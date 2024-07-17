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

class get_buds_by_artists(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_artists, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user = request.user

            buds = []
            for artist in user.likes_artist.all():
                buds.extend(artist.users.all())
            
            # Filter out the user and duplicates
            buds = list({bud: bud for bud in buds if bud.uid != user.uid}.values())
            
            buds_data = []
            artist_ids = []
            track_ids = []
            for bud in buds:

                bud_liked_artist_uids = [artist.uid for artist in bud.likes_artist.all()]

                common_artists = user_node.likes_artist.filter(uid__in=bud_liked_artist_uids)


                common_artists_count = len(common_artists)

                artist_ids.extend([artist.uid for artist in common_artists])

                bud_data = {
                    'uid': bud.uid,
                    'email': bud.email,
                    'country': bud.country,
                    'display_name': bud.display_name,
                    'bio': bud.bio,
                    'is_active': bud.is_active,
                    'is_authenticated': bud.is_authenticated,
                    'commonArtistsCount': common_artists_count,
                }
                buds_data.append(bud_data)

            common_artists_data = fetch_artists(user.access_token,artist_ids)

            for bud in buds_data:
                bud['commonArtists'] = common_artists_data

            return JsonResponse({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'data': {
                    'buds': buds_data,
                    'totalCommonArtistsCount': sum(bud['commonArtistsCount'] for bud in buds_data),
                }
            })
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)