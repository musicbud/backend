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


class get_bud_profile(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_bud_profile, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            # Extract user id and bud id from request
            user = request.user
            bud_id = request.data.get('bud_id')

            bud_node = User.nodes.get_or_none(uid=bud_id)

            if user is None or bud_node is None:
                return JsonResponse({'error': 'User or bud not found'}, status=404)

            # Get all artists and tracks liked by the user and the bud
            user_artists = list(user.top_artists.all()) 
            bud_artists = list(bud_node.top_artists.all()) 
            user_tracks = list(user.top_tracks.all())  
            bud_tracks = list(bud_node.top_tracks.all())    
            user_genres = list(user.top_genres.all())  
            bud_genres = list(bud_node.top_genres.all())


            # Convert to sets of unique identifiers
            user_artist_ids = set(artist.id for artist in user_artists)
            bud_artist_ids = set(artist.id for artist in bud_artists)
            user_track_ids = set(track.id for track in user_tracks)
            bud_track_ids = set(track.id for track in bud_tracks)
            user_genre_ids = set(genre.id for genre in user_genres)
            bud_genre_ids = set(genre.id for genre in bud_genres)

            # Find common artists, tracks, and genres by unique identifiers
            common_artist_ids = user_artist_ids.intersection(bud_artist_ids)
            common_track_ids = user_track_ids.intersection(bud_track_ids)
            common_genre_ids = user_genre_ids.intersection(bud_genre_ids)

            # Convert back to original objects
            common_artists = [artist for artist in user_artists if artist.id in common_artist_ids]
            common_tracks = [track for track in user_tracks if track.id in common_track_ids]
            common_genres = [genre for genre in user_genres if genre.id in common_genre_ids]

            return JsonResponse({
                'message': 'Get Bud Profile',
                'data': {
                    'common_artists_data': [artist.serialize() for artist in common_artists],
                    'common_tracks_data': [track.serialize() for track in common_tracks],
                    'common_genres_data': [genre.serialize() for genre in common_genres]
                }
            }, status=200)
        
        except Exception as e:
            # Handle exceptions
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)