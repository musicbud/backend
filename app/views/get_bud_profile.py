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
            user_artists = {artist.uid for artist in user.likes_artist.all()} 
            bud_artists = {artist.uid for artist in bud_node.likes_artist.all()} 
            user_tracks = {track.uid for track in user.likes_track.all()}  # Extracting track IDs
            bud_tracks = {track.uid for track in bud_node.likes_track.all()}    # Extracting track IDs
            user_genres = {genres.uid for genres in user.likes_genre.all()}  # Extracting genres IDs
            bud_genres = {genres.uid for genres in bud_node.likes_genre.all()}    # Extracting genres IDs

            # Find common artists and tracks
            common_artists = user_artists.intersection(bud_artists)
            common_tracks = user_tracks.intersection(bud_tracks)
            common_genres = user_genres.intersection(bud_genres)

            # Check if there are common artists
            if common_artists != {None}:
                # Extract IDs of common artists
                common_artists_ids = [artist for artist in common_artists]
            else:
                # Handle case where there are no common artists
                common_artists_ids = []

            if common_tracks  != {None}:
                # Convert set to list for iteration
                common_tracks_ids = [track for track in common_tracks]
            else:
            # Handle case where there are no common tracks
                common_tracks_ids = []
            if common_genres  != {None}:
                # Convert set to list for iteration
                common_genres_ids = [genre for genre in common_genres]
            else:
            # Handle case where there are no common genres
                common_genres_ids = []


            # Fetch additional details only if there are common artists or tracks
            if common_artists_ids or common_tracks_ids or common_genres_ids:
                # Fetch additional details about common artists and tracks using SpotifyService
                common_artists_data, common_tracks_data , common_genres_data= fetch_common_artists_tracks_and_genres(user_node.access_token, common_artists_ids, common_tracks_ids,common_genres_ids)
            # Return the bud profile as JSON response
            return JsonResponse({
                'message': 'Get Bud Profile',
                'data': {'common_artists_count':len(common_artists_data),'common_artists_data':common_artists_data,'common_tracks_count':len(common_tracks_data),'common_tracks_data':common_tracks_data,'common_genres_count':len(common_genres_data),'common_genres_data':common_genres_data}
            }, status=200)
        except Exception as e:
            # Handle exceptions
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)