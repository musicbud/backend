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
            user_top_artists = list(user.top_artists.all()) 
            bud_top_artists = list(bud_node.top_artists.all()) 
            user_top_tracks = list(user.top_tracks.all())  
            bud_top_tracks = list(bud_node.top_tracks.all())    
            user_top_genres = list(user.top_genres.all())  
            bud_top_genres = list(bud_node.top_genres.all())

            user_likes_artists = list(user.likes_artists.all())  
            bud_likes_artists = list(bud_node.likes_artists.all())

            user_likes_tracks = list(user.likes_tracks.all())  
            bud_likes_tracks = list(bud_node.likes_tracks.all())  
            
            user_likes_albums = list(user.likes_albums.all())
            bud_likes_albums = list(bud_node.likes_albums.all())



            # Convert to sets of unique identifiers
            user_top_artist_ids = set(artist.id for artist in user_top_artists)
            bud_top_artist_ids = set(artist.id for artist in bud_top_artists)
            user_top_track_ids = set(track.id for track in user_top_tracks)
            bud_top_track_ids = set(track.id for track in bud_top_tracks)
            user_top_genre_ids = set(genre.id for genre in user_top_genres)
            bud_top_genre_ids = set(genre.id for genre in bud_top_genres)

            user_likes_artist_ids = set(artist.id for artist in user_likes_artists)
            bud_likes_artist_ids = set(artist.id for artist in bud_likes_artists)
            user_likes_track_ids = set(track.id for track in user_likes_tracks)
            bud_likes_track_ids = set(track.id for track in bud_likes_tracks)
            user_likes_album_ids = set(album.id for album in user_likes_albums)
            bud_likes_album_ids = set(album.id for album in bud_likes_albums)


            # Find common artists, tracks, and genres by unique identifiers
            common_top_artist_ids = user_top_artist_ids.intersection(bud_top_artist_ids)
            common_top_track_ids = user_top_track_ids.intersection(bud_top_track_ids)
            common_top_genre_ids = user_top_genre_ids.intersection(bud_top_genre_ids)

            common_likes_artist_ids = user_likes_artist_ids.intersection(bud_likes_artist_ids)
            common_likes_track_ids = user_likes_track_ids.intersection(bud_likes_track_ids)
            common_likes_album_ids = user_likes_album_ids.intersection(bud_likes_album_ids)

            # Convert back to original objects
            common_top_artists = [artist for artist in user_top_artists if artist.id in common_top_artist_ids]
            common_top_tracks = [track for track in user_top_tracks if track.id in common_top_track_ids]
            common_top_genres = [genre for genre in user_top_genres if genre.id in common_top_genre_ids]

            common_likes_artists = [artist for artist in user_likes_artists if artist.id in common_likes_artist_ids]
            common_likes_tracks = [track for track in user_likes_tracks if track.id in common_likes_track_ids]
            common_likes_albums = [album for album in user_likes_albums if album.id in common_likes_album_ids]

            return JsonResponse({
                'message': 'Fetched Bud Profile Successfully',
                'data': {
                    'common_top_artists_data': [artist.serialize() for artist in common_top_artists],
                    'common_top_tracks_data': [track.serialize() for track in common_top_tracks],
                    'common_top_genres_data': [genre.serialize() for genre in common_top_genres],
                    'common_likes_artists_data': [artist.serialize() for artist in common_likes_artists],
                    'common_likes_tracks_data': [track.serialize() for track in common_likes_tracks],
                    'common_likes_albums_data': [album.serialize() for album in common_likes_albums]
                }
            }, status=200)
        
        except Exception as e:
            # Handle exceptions
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)