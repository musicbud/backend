from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.User import User
from ..db_models.Track import Track  
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication

import logging
logger = logging.getLogger(__name__)

class get_buds_by_track(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_track, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user = request.user
            track_id = request.data.get('track_id')

            if not track_id:
                return JsonResponse({'error': 'Track ID not provided'}, status=400)
                
            user_node = User.nodes.get_or_none(uid=user.uid)
            track_node = Track.nodes.get_or_none(uid=track_id)

            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)
                
            if not track_node:
                return JsonResponse({'error': 'Track not found'}, status=404)

            buds = track_node.users.exclude(uid=user.uid)
            print(track_node.users.all())
            buds_data = []
            total_common_tracks_count = 0

            for bud in buds:
                bud_liked_track_uids = [track.uid for track in bud.likes_tracks.all()]
                common_tracks = user_node.likes_tracks.filter(uid__in=bud_liked_track_uids)
                common_tracks_count = len(common_tracks)
                total_common_tracks_count += common_tracks_count

                buds_data.append({
                    'uid': bud.uid,
                    'email': bud.email,
                    'country': bud.country,
                    'display_name': bud.display_name,
                    'bio': bud.bio,
                    'is_active': bud.is_active,
                    'is_authenticated': bud.is_authenticated,
                    'commonTracksCount': common_tracks_count,
                    'commonTracks': [track.serialize() for track in common_tracks]
                })

            return JsonResponse({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'data': {
                    'buds': buds_data,
                    'totalCommonTracksCount': total_common_tracks_count
                }
            })
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
