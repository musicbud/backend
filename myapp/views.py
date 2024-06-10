from django.http import JsonResponse
from .models import User
from .services import SpotifyService
import logging
from neomodel import db
from .utils.spotify_client import spotify_client as spotify_service
from neomodel.exceptions import MultipleNodesReturned, DoesNotExist

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.exceptions import PermissionDenied
from .CustomTokenAuthentication import CustomTokenAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
logger = logging.getLogger(__name__)


def create_user(request):
    # Extract data from request
    email = request.POST.get('email')
    password = request.POST.get('password')
    birth_date = request.POST.get('birth_date')
    country = request.POST.get('country')
    display_name = request.POST.get('display_name')

    # Create a new User node
    user = User(email=email, password=password, birthDate=birth_date, country=country, displayName=display_name)  # Adjust field names according to your NeoModel User model
    user.save()

    return JsonResponse({'message': 'User created successfully'})


def login(request):
    try:
        authorization_link = spotify_service.create_authorize_url()
        return JsonResponse({
            'message': 'generated authorization link successfully.',
            'code': 200,
            'status': 'HTTP OK',
            'data': {'authorization_link': authorization_link}
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def callback(request):
    try:
        code = request.GET.get('code')

        tokens = spotify_service.get_spotify_tokens(code)
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token'] 
        expires_at = tokens['expires_at']

        
        
        user_profile = spotify_service.get_current_user_profile(access_token)
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
        return JsonResponse({'error': str(e)}, status=500)

class refresh_token(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(refresh_token, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            user = request.user  
            new_data = spotify_service.refresh_access_token(user.refresh_token)
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
    
def updateUserProfile(request):
    try:
        user = request.user
        user_top_artists, user_top_tracks = spotify_service.get_user_top_artists_and_tracks(user.access_token)

        user.update_likes(user_top_artists, user_top_tracks)

        return JsonResponse({
            'message': 'updated successfully.',
            'code': 200,
            'status': 'HTTP OK',
        })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)
def getUserProfile(request):
    try:
        user = request.user
        limit = request.POST.get('limit', 30)
        skip = request.POST.get('skip', 0)

        user = User.find_by_id(user.id)
        if not user:
            return JsonResponse({'message': 'User profile not found'}, status=404)

        user = User.nodes.get_or_none(id=user.id)
        if user:
            user_top_artists_ids = user.get_user_top_artists_ids()
            user_top_tracks_ids = user.get_user_top_tracks_ids()
        else:
            # Handle case where user with given id does not exist
            pass  # You can raise an exception or handle it according to your application logic



        user_top_artists, user_top_tracks = spotify_service.fetch_top_artists_and_tracks(user.access_token, user_top_artists_ids, user_top_tracks_ids)

        return JsonResponse({
            'message': 'Fetched profile successfully.',
            'code': 200,
            'status': 'HTTP OK',
            'data': {
                'user': user.serialize(),
                'userTopArtists': user_top_artists,
                'userTopTracks': user_top_tracks
            }
        })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

def setAndUpdateUserBio(request):
    try:
        user_id = request.user.id
        bio = request.POST.get('bio')

        if bio is not None:
            if User.set_and_update_bio(user_id, bio):
                return JsonResponse({
                    'message': 'Updated bio successfully.',
                    'code': 200,
                    'successful': True
                })
            else:
                return JsonResponse({
                    'error': 'User not found or unable to update bio.',
                    'code': 404
                }, status=404)
        else:
            return JsonResponse({
                'error': 'Bio field is missing.',
                'code': 400
            }, status=400)
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

def get_bud_profile(request):
    try:
        user = request.user
        bud_id = request.POST.get('budId')
        limit = int(request.POST.get('limit', 30))
        skip = int(request.POST.get('skip', 0))

        # Fetch common artists and tracks from the Neo4j database using neomodel
        user_node = User.nodes.get_or_none(id=user.id)
        bud_node = User.nodes.get_or_none(id=bud_id)
        if user_node is None or bud_node is None:
            return JsonResponse({'error': 'User or bud not found'}, status=404)

        common_artists = user_node.likes.is_liked_by.filter(Q(is_liked_by=bud_node))
        common_tracks = user_node.likes.likes_track.filter(Q(likes_track=bud_node))

        common_artists_ids = [artist.id for artist in common_artists]
        common_tracks_ids = [track.id for track in common_tracks]

        # Fetch additional details about common artists and tracks using SpotifyService
        spotify_service = SpotifyService()
        common_artists_data, common_tracks_data = spotify_service.fetch_common_artists_and_tracks(user.access_token, common_artists_ids, common_tracks_ids)

        return JsonResponse({
            'message': 'Fetched common successfully.',
            'code': 200,
            'status': 'HTTP OK',
            'data': {
                'user': user.serialize(),  # Assuming you have a serialize method in your User model
                'commonArtists': common_artists_data,
                'commonTracks': common_tracks_data
            }
        })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)
class update_my_likes(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(update_my_likes, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            user = request.user
            user_top_artists, user_top_tracks = spotify_service.get_user_top_artists_and_tracks()
            
            # Extract artist and track IDs
            artist_ids = [artist['id'] for artist in user_top_artists]
            track_ids = [track['id'] for track in user_top_tracks]

            user.update_likes(user, artist_ids, track_ids)

            return JsonResponse({'message': 'Updated Likes'}, status=200)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
def set_my_bio(request):
    try:
        user = request.user
        bio = request.POST.get('bio')

        # Fetch the user node from the Neo4j database
        user_node = User.nodes.get_or_none(id=user.id)
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
def get_bud_profile(request):
    try:
        # Extract user id and bud id from request
        user_id = request.user.id
        bud_id = request.POST.get('bud_id')

        # Retrieve the bud profile using NeoModel
        user = User.nodes.get(id=user_id)
        bud_profile = user.get_bud_profile(bud_id)

        # Return the bud profile as JSON response
        return JsonResponse({
            'message': 'Get Bud Profile',
            'data': bud_profile
        }, status=200)
    except Exception as e:
        # Handle exceptions
        logger.error(e)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)


def get_buds_by_artist(request):
    try:
        user = request.user
        artist_id = request.POST.get('artist_id')
        buds = user.get_buds_by_artist(artist_id)

        return JsonResponse({
            'message': 'Get Buds by Artist',
            'data': buds
        }, status=200)
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

def get_buds_by_track(request):
    try:
        user = request.user
        track_id = request.POST.get('track_id')
        buds = user.get_buds_by_track(track_id)

        return JsonResponse({
            'message': 'Get Buds by Track',
            'data': buds
        }, status=200)
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

def get_buds_by_artist_and_track(request):
    try:
        user = request.user
        artist_id = request.POST.get('artist_id')
        track_id = request.POST.get('track_id')
        buds = user.get_buds_by_artist_and_track(artist_id, track_id)

        return JsonResponse({
            'message': 'Get Buds by Artist and Track',
            'data': buds
        }, status=200)
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

def get_buds_by_artists(user_id):
    try:
        # Retrieve the user from the database
        user = User.nodes.get_or_none(id=user_id)
        
        if user:
            # Retrieve the list of artists liked by the user
            liked_artists = user.likes_artists.all()

            # Construct a Cypher query to find buds who like the same artists
            cypher_query = (
                "MATCH (bud:User)-[:LIKES_ARTIST]->(artist:Artist) "
                "WHERE artist IN $liked_artists "
                "AND ID(bud) <> $user_id "
                "RETURN DISTINCT bud "
                "LIMIT 30"
            )

            # Execute the Cypher query
            results, meta = db.cypher_query(cypher_query, params={'liked_artists': liked_artists, 'user_id': user_id})

            # Extract buds from the query result
            buds = [User.inflate(record[0]) for record in results]

            # Count the common artists between the user and buds
            common_artists_count = len(liked_artists)

            data = {
                'buds': [bud.serialize() for bud in buds],
                'commonArtistsCount': common_artists_count
            }

            return {'message': 'Fetched buds successfully.', 'code': 200, 'successful': True, 'data': data}
        else:
            return {'error': 'User not found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500
    
from neomodel import db, Q
from .models import User

def get_buds_by_tracks(request):
    try:
        user_id = request.user.id
        user = User.nodes.get_or_none(uid=user_id)
        
        if user:
            buds = User.nodes.filter(likes__tracks__in=user.likes.tracks).exclude(uid=user_id).limit(30)
            common_tracks_count = len(user.likes.tracks)
            data = {
                'buds': [bud.serialize() for bud in buds],
                'commonTracksCount': common_tracks_count
            }
            return JsonResponse({'message': 'Fetched buds successfully.', 'code': 200, 'successful': True, 'data': data})
        else:
            return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_buds_by_artists_and_tracks(request):
    try:
        user_id = request.user.id
        user = User.nodes.get_or_none(uid=user_id)
        
        if user:
            buds = User.nodes.filter(Q(likes__artists__in=user.likes.artists) & Q(likes__tracks__in=user.likes.tracks)).exclude(uid=user_id).limit(30)
            common_artists_count = len(user.likes.artists)
            common_tracks_count = len(user.likes.tracks)
            common_count = common_artists_count + common_tracks_count
            data = {
                'buds': [bud.serialize() for bud in buds],
                'commonArtistsCount': common_artists_count,
                'commonTracksCount': common_tracks_count,
                'commonCount': common_count
            }
            return JsonResponse({'message': 'Fetched buds successfully.', 'code': 200, 'successful': True, 'data': data})
        else:
            return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def search_channels_and_users_view(request):
    try:
        query = request.POST.get('query', '')
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

# def buds_route(request):
#     # Invoke your buds route logic here
#     return JsonResponse({'message': 'Buds route'})

# def user_profile_route(request):
#     # Invoke your user profile route logic here
#     return JsonResponse({'message': 'User profile route'})

# def chat_route(request):
#     # Invoke your chat route logic here
#     return JsonResponse({'message': 'Chat route'})

# def search_route(request):
#     # Invoke your search route logic here
#     return JsonResponse({'message': 'Search route'})