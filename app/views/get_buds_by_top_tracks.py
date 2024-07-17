from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.User import User
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication

import logging
logger = logging.getLogger(__name__)

class get_buds_by_top_tracks(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_top_tracks, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user_node = request.user
            user_id = request.user.uid

            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)

            top_tracks = user_node.top_tracks.all()

            buds = []
            for track in top_tracks:
                buds.extend(track.users.all())
            # Filter out the user and duplicates
            buds = list({bud.uid: bud for bud in buds if bud.uid != user_id}.values())

            buds_data = []
            total_common_tracks_count = 0

            for bud in buds:
                bud_liked_track_uids = [track.uid for track in bud.top_tracks.all()]
                common_tracks = user_node.top_tracks.filter(uid__in=bud_liked_track_uids)
                common_tracks_count = len(common_tracks)
                total_common_tracks_count += common_tracks_count

                buds_data.append({
                    'bud_uid': bud.uid,
                    'common_tracks_count': common_tracks_count,
                    'common_tracks': [track.serialize() for track in common_tracks]
                })

            return JsonResponse({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'data': {
                    'buds': buds_data,
                    'totalCommonTracksCount': total_common_tracks_count,
                }
            })
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
