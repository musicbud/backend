from django.http import JsonResponse
from neomodel.exceptions import MultipleNodesReturned, DoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.exceptions import PermissionDenied
from .CustomTokenAuthentication import CustomTokenAuthentication
from .models import User
from django.http import JsonResponse
from .models import User
import logging
logger = logging.getLogger(__name__)
from .services.orchestrator import get_service

def login(request):
    service = request.GET.get('service', 'lastfm')  # Default to 'lastfm' if no service is specified
    try:
        authorization_link = get_service(service).create_authorize_url()
        return JsonResponse({
            'message': 'Generated authorization link successfully.',
            'code': 200,
            'status': 'HTTP OK',
            'data': {'authorization_link': authorization_link}
        })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': str(e)}, status=500)

def ytmusic_callback(request):
    try:
        code = request.GET.get('code')
        return JsonResponse({
            'message': 'logged in successfully.',
            'code': 200,
            'status': 'HTTP OK',
            'data': {'accessToken': access_token, 'refreshToken': refresh_token, 'expiresAt': expires_at}
        })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': str(e)}, status=500)
    
def spotify_callback(request):
    try:
        code = request.GET.get('code')
        service = 'spotify'
        strategy = None    
        
        tokens = get_service(service).get_tokens(code)

        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token'] 
        expires_at = tokens['expires_at']

        user_profile = get_service(service).get_user_profile(access_token)
        try:
            user = User.nodes.get(uid=user_profile['id'])
            created = False
        except MultipleNodesReturned:
            return JsonResponse({'error': 'Multiple users found with this uid'}, status=500)
        except DoesNotExist:
            user = User.create_from_spotify_profile(user_profile)
            created = True

        updated_user = User.update_tokens(user_profile['id'], access_token, refresh_token, expires_at)
        if updated_user is None:
            return JsonResponse({'error': 'Error updating tokens'}, status=500)

        return JsonResponse({
            'message': 'logged in successfully.',
            'code': 200,
            'status': 'HTTP OK',
            'data': {'accessToken': access_token, 'refreshToken': refresh_token, 'expiresAt': expires_at}
        })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': str(e)}, status=500)
    

def lastfm_callback(request):
    try:
        token = request.GET.get('token')
        print(token) 
        return JsonResponse({'token':token})


        
        # tokens = get_service(service).strategy.get_tokens()

        # tokens = strategy.get_tokens(code)
        # access_token = tokens['access_token']
        # refresh_token = tokens['refresh_token'] 
        # expires_at = tokens['expires_at']

        # user_profile = get_service(service).strategy.get_user_profile(access_token)
        # try:
        #     user = User.nodes.get(uid=user_profile['id'])
        #     created = False
        # except MultipleNodesReturned:
        #     return JsonResponse({'error': 'Multiple users found with this uid'}, status=500)
        # except DoesNotExist:
        #     user = User.create_from_spotify_profile(user_profile)
        #     created = True

        # updated_user = User.update_tokens(user_profile['id'], access_token, refresh_token, expires_at)
        # if updated_user is None:
        #     return JsonResponse({'error': 'Error updating tokens'}, status=500)

        # return JsonResponse({
        #     'message': 'logged in successfully.',
        #     'code': 200,
        #     'status': 'HTTP OK',
        #     'data': {'accessToken': access_token, 'refreshToken': refresh_token, 'expiresAt': expires_at}
        # })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': str(e)}, status=500)

class spotify_refresh_token(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(refresh_token, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            user = request.user  
            new_data = refresh_access_token(user.refresh_token)
            user.update_tokens(user.uid,new_data['access_token'], new_data['refresh_token'],new_data['expires_at'])

            return JsonResponse({
                'message': 'refreshed successfully.',
                'code': 200,
                'status': 'HTTP OK',
                'data': {
                    'accessToken': new_data['access_token'],
                    'refreshToken': new_data['refresh_token'],
                    'expiresAt': new_data['expires_at']
                }
            })
        except Exception as e:
            print(e)
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
        


class get_my_profile(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_my_profile, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("User not authenticated")
        user_profile = {
            'uid': user.uid,
            'display_name': user.display_name,
            'bio': user.bio,
            'email': user.email,
            'country': user.country
        }
        return Response(user_profile, status=status.HTTP_200_OK)

class update_my_likes(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(update_my_likes, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            user = request.user
            user_top_artists, user_top_tracks = get_user_top_artists_and_tracks(user.access_token)
            
            # Extract artist and track IDs
            artist_ids = [artist['id'] for artist in user_top_artists]
            track_ids = [track['id'] for track in user_top_tracks]

            user.update_likes(user, artist_ids, track_ids)

            return JsonResponse({'message': 'Updated Likes'}, status=200)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
class set_my_bio(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(set_my_bio, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            user = request.user
            bio = request.data.get('bio')

            if bio is None:
                return JsonResponse({
                    'error': 'Bio field is missing.',
                    'code': 400
                }, status=400)

            # Fetch the user node from the Neo4j database
            user_node = User.nodes.get_or_none(uid=user.uid)
            if user_node is None:
                return JsonResponse({'error': 'User not found'}, status=404)

            # Set the bio property of the user node
            user_node.bio = bio
            user_node.save()

            return JsonResponse({
                'message': 'Bio updated successfully.',
                'code': 200,
                'status': 'HTTP OK',
            })
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)



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

            user_node = User.nodes.get_or_none(uid=user.uid)
            bud_node = User.nodes.get_or_none(uid=bud_id)

            if user_node is None or bud_node is None:
                return JsonResponse({'error': 'User or bud not found'}, status=404)


            # Get all artists and tracks liked by the user and the bud
            user_artists = {artist.uid for artist in user_node.likes_artist.all()} 
            bud_artists = {artist.uid for artist in bud_node.likes_artist.all()} 
            user_tracks = {track.uid for track in user_node.likes_track.all()}  # Extracting track IDs
            bud_tracks = {track.uid for track in bud_node.likes_track.all()}    # Extracting track IDs
            user_genres = {genres.uid for genres in user_node.likes_genre.all()}  # Extracting genres IDs
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

class get_buds_by_artists(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_artists, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user = request.user
            user_node = User.nodes.get_or_none(uid=user.uid)

            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)

            buds = []
            for artist in user_node.likes_artist.all():
                buds.extend(artist.liked_by.all())
            
            # Filter out the user and duplicates
            buds = list({bud.uid: bud for bud in buds if bud.uid != user.uid}.values())

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
class get_buds_by_genres(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_genres, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user = request.user
            user_id = request.user.uid
            user_node = User.nodes.get_or_none(uid=user_id)
            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)

            buds = []
            for genre in user_node.likes_genre.all():
                buds.extend(genre.liked_by.all())

            # Filter out the user and duplicates
            buds = list({bud.uid: bud for bud in buds if bud.uid != user_id}.values())

            buds_data = []
            genre_ids = []

            for bud in buds:

                bud_liked_genre_uids = [genre.uid for genre in bud.likes_genre.all()]

                common_genres = user_node.likes_genre.filter(uid__in=bud_liked_genre_uids)

                common_genres_count = len(common_genres)

                 # Extract uid values into a list
                genre_ids = [genre.uid for genre in common_genres]

                bud_data = {
                    'uid': bud.uid,
                    'email': bud.email,
                    'country': bud.country,
                    'display_name': bud.display_name,
                    'bio': bud.bio,
                    'is_active': bud.is_active,
                    'is_authenticated': bud.is_authenticated,
                    'commonGenres': [{'name': genre.name} for genre in common_genres],
                    'commonGenresCount': common_genres_count
                }
                buds_data.append(bud_data)
            common_genres_data = fetch_genres(user.access_token,genre_ids)

            for bud in buds_data:
                bud['commonGenres'] = [genre for genre in common_genres_data if genre['id'] in genre_ids]

            return JsonResponse({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'data': {
                    'buds': buds_data,
                    'totalCommonGenresCount': sum(bud['commonGenresCount'] for bud in buds_data)
                }
            })
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
class get_buds_by_artists_and_tracks_and_genres(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_artists_and_tracks_and_genres, self).dispatch(*args, **kwargs)

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

         
class search_users(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(search_users, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            query = request.data.get('query', '')
            print(query)
            users = User.nodes.filter(display_name__icontains=query)
            return JsonResponse({
                'message': 'Fetched search result successfully.',
                'code': 200,
                'successful': True,
                'collection': {'users': [user.serialize() for user in users]}
            }, status=200)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

def not_found_view(request, exception):
    return JsonResponse({'error': 'Resource not found on this server'}, status=404)

def error_view(request):
    return JsonResponse({'error': 'Internal Server Error'}, status=500)
