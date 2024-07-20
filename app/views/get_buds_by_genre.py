from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.User import User
from ..db_models.Track import Track
from ..db_models.Genre import Genre  # Ensure you import the Genre model
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging
logger = logging.getLogger(__name__)

class get_buds_by_genre(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_genre, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user = request.user
            genre_id = request.data.get('genre_id')
            
            if not genre_id:
                return JsonResponse({'error': 'Genre ID not provided'}, status=400)
                
            user_node = User.nodes.get_or_none(uid=user.uid)
            genre_node = Genre.nodes.get_or_none(uid=genre_id)

            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)
                
            if not genre_node:
                return JsonResponse({'error': 'Genre not found'}, status=404)

            # Find tracks by the specified genre
            genre_tracks = genre_node.tracks.all()
            if not genre_tracks:
                return JsonResponse({'error': 'No tracks found for this genre'}, status=404)

            # Find users who liked tracks by this genre
            buds = set()
            for track in genre_tracks:
                buds.update(track.users.exclude(uid=user.uid))

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

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
