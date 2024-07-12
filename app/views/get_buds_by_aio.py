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


class get_buds_by_aio(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_aio, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user = request.user
            user_id = request.user.uid
            user_node = User.nodes.get_or_none(uid=user_id)

            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)

            liked_artists = user_node.likes_artist.all()
            liked_tracks = user_node.likes_track.all()
            liked_genres = user_node.likes_genre.all()

            buds = []
            for artist in liked_artists:
                buds.extend(artist.liked_by.all())
            for track in liked_tracks:
                buds.extend(track.liked_by.all())
            for genre in liked_genres:
                buds.extend(genre.liked_by.all())

            # Filter out the user and duplicates
            buds = [bud for bud in buds if bud.uid != user_id]

            buds_data = []
            artist_ids = []
            track_ids = []
            genre_ids = []

            for bud in buds:
                bud_liked_artist_uids = [artist.uid for artist in bud.likes_artist.all()]
                bud_liked_track_uids = [track.uid for track in bud.likes_track.all()]
                bud_liked_genre_uids = [genre.uid for genre in bud.likes_genre.all()]

                common_artists = user_node.likes_artist.filter(uid__in=bud_liked_artist_uids)
                common_tracks = user_node.likes_track.filter(uid__in=bud_liked_track_uids)
                common_genres = user_node.likes_genre.filter(uid__in=bud_liked_genre_uids)

                common_artists_count = len(common_artists)
                common_tracks_count = len(common_tracks)
                common_genres_count = len(common_genres)

                artist_ids.extend([artist.uid for artist in common_artists])
                track_ids.extend([track.uid for track in common_tracks])
                genre_ids.extend([genre.uid for genre in common_genres])

                bud_data = {
                    'uid': bud.uid,
                    'email': bud.email,
                    'country': bud.country,
                    'display_name': bud.display_name,
                    'bio': bud.bio,
                    'is_active': bud.is_active,
                    'is_authenticated': bud.is_authenticated,
                    'commonArtistsCount': common_artists_count,
                    'commonTracksCount': common_tracks_count,
                    'commonGenresCount': common_genres_count
                }
                buds_data.append(bud_data)

            common_artists_data, common_tracks_data, common_genres_data = fetch_common_artists_tracks_and_genres(user.access_token, artist_ids, track_ids, genre_ids)

            # Map common data to buds_data based on uid
            for bud in buds_data:
                bud_uid = bud['uid']
                bud['commonArtists'] = [artist for artist in common_artists_data if artist['id'] in artist_ids and artist['id'] != bud_uid]
                bud['commonTracks'] = [track for track in common_tracks_data if track['id'] in track_ids and track['id'] != bud_uid]
                bud['commonGenres'] = [genre for genre in common_genres_data if genre['id'] in genre_ids and genre['id'] != bud_uid]

            return JsonResponse({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'data': {
                    'buds': buds_data,
                    'totalCommonArtistsCount': sum(bud['commonArtistsCount'] for bud in buds_data),
                    'totalCommonTracksCount': sum(bud['commonTracksCount'] for bud in buds_data),
                    'totalCommonGenresCount': sum(bud['commonGenresCount'] for bud in buds_data)
                }
            })

        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

         