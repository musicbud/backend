from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from ..db_models.User import User
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging
logger = logging.getLogger(__name__)


class get_buds_by_liked_aio(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_liked_aio, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user_node = request.user
            user_id = request.user.uid

            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)

            liked_artists = user_node.likes_artists.all()
            liked_tracks = user_node.likes_tracks.all()
            liked_genres = user_node.likes_genres.all()
            liked_albums = user_node.likes_albums.all()

            buds = []
            for artist in liked_artists:
                buds.extend(artist.users.all())
            for track in liked_tracks:
                buds.extend(track.users.all())
            for genre in liked_genres:
                buds.extend(genre.users.all())
            for album in liked_albums:
                buds.extend(album.users.all())

            # Filter out the user and duplicates
            buds = list({bud.uid: bud for bud in buds if bud.uid != user_id}.values())

            buds_data = []
            artist_ids = []
            track_ids = []
            genre_ids = []
            album_ids = []

            for bud in buds:
                bud_liked_artist_uids = [artist.uid for artist in bud.likes_artists.all()]
                bud_liked_track_uids = [track.uid for track in bud.likes_tracks.all()]
                bud_liked_genre_uids = [genre.uid for genre in bud.likes_genres.all()]
                bud_liked_album_uids = [album.uid for album in bud.likes_albums.all()]

                common_artists = user_node.likes_artists.filter(uid__in=bud_liked_artist_uids)
                common_tracks = user_node.likes_tracks.filter(uid__in=bud_liked_track_uids)
                common_genres = user_node.likes_genres.filter(uid__in=bud_liked_genre_uids)
                common_albums = user_node.likes_albums.filter(uid__in=bud_liked_album_uids)

                common_artists_count = len(common_artists)
                common_tracks_count = len(common_tracks)
                common_genres_count = len(common_genres)
                common_albums_count = len(common_albums)

                artist_ids.extend([artist.uid for artist in common_artists])
                track_ids.extend([track.uid for track in common_tracks])
                genre_ids.extend([genre.uid for genre in common_genres])
                album_ids.extend([album.uid for album in common_albums])



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
                    'commonGenresCount': common_genres_count,
                    'commonAlbumsCount': common_albums_count
                }
                buds_data.append(bud_data)


            # Map common data to buds_data based on uid
            for bud in buds_data:
                bud_uid = bud['uid']
                bud['commonArtists'] = [artist.serialize() for artist in common_artists if artist['uid'] in artist_ids and artist['uid'] != bud_uid]
                bud['commonTracks'] = [track.serialize() for track in common_tracks if track['uid'] in track_ids and track['uid'] != bud_uid]
                bud['commonGenres'] = [genre.serialize() for genre in common_genres if genre['uid'] in genre_ids and genre['uid'] != bud_uid]
                bud['commonAlbums'] = [album.serialize() for album in common_albums if album.uid in album_ids and album.uid != bud_uid]

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
         