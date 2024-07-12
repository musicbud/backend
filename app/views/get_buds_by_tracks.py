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

class get_buds_by_tracks(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_tracks, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:

            user = request.user
            user_node = User.nodes.get_or_none(uid=user.uid)

            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)

            buds = []
            for track in user_node.likes_track.all():
                buds.extend(track.liked_by.exclude(uid=user.uid))

            buds_data = []
            track_ids = []
            
            for bud in buds:
                bud_liked_track_uids = [track.uid for track in bud.likes_track.all()]

                common_tracks = user_node.likes_track.filter(uid__in=bud_liked_track_uids)

                common_tracks_count = len(common_tracks)
                # Extract uid values into a list
                track_ids = [track.uid for track in common_tracks]
        
                bud_data = {
                    'uid': bud.uid,
                    'email': bud.email,
                    'country': bud.country,
                    'display_name': bud.display_name,
                    'bio': bud.bio,
                    'is_active': bud.is_active,
                    'is_authenticated': bud.is_authenticated,
                    'commonTracksCount': common_tracks_count,
                }
                buds_data.append(bud_data)

            common_tracks_data = fetch_tracks(user.access_token,track_ids)

            for bud in buds_data:
                bud['commonTracks'] = [track for track in common_tracks_data if track['id'] in track_ids]

            return JsonResponse({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'data': {
                    'buds': buds_data,
                    'totalCommonTracksCount': sum(bud['commonTracksCount'] for bud in buds_data)
                }
            })
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)