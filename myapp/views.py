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
    
from neomodel import db, Q
from .models import User


def create_user(request):
    # Extract data from request
    email = request.data.get('email')
    password = request.data.get('password')
    birth_date = request.data.get('birth_date')
    country = request.data.get('country')
    display_name = request.data.get('display_name')

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
            user_top_artists, user_top_tracks = spotify_service.get_user_top_artists_and_tracks()
            
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
            user_artists = set(user_node.likes_artist.all())
            bud_artists = set(bud_node.likes_artist.all())
            user_tracks = set(user_node.likes_track.all())
            bud_tracks = set(bud_node.likes_track.all())

            # Find common artists and tracks
            common_artists = user_artists.intersection(bud_artists)
            common_tracks = user_tracks.intersection(bud_tracks)

            common_artists_ids = [artist.uid for artist in common_artists]
            common_tracks_ids = [track.uid for track in common_tracks]

            # Fetch additional details about common artists and tracks using SpotifyService
            common_artists_data, common_tracks_data = spotify_service.fetch_common_artists_and_tracks(user_node.access_token, common_artists_ids, common_tracks_ids)

            # Return the bud profile as JSON response
            return JsonResponse({
                'message': 'Get Bud Profile',
                'data': {'common_artists_data':common_artists_data,'common_tracks_data':common_tracks_data}
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

            # Retrieve the user from the database
            user_node = User.nodes.get_or_none(uid=user.uid)
            if user_node:
                # Retrieve the list of artists liked by the user
                liked_artists = user_node.likes_artist.all()
                liked_artists_ids = [artist.uid for artist in liked_artists]

                if not liked_artists_ids:
                    return JsonResponse({'error': 'No liked artists found for user'}, status=404)

                # Construct a Cypher query to find buds who like the same artists
                cypher_query = (
                    "MATCH (bud:User)-[:LIKES_ARTIST]->(artist:Artist) "
                    "WHERE artist.uid IN $liked_artists_ids "
                    "AND bud.uid <> $user_uid "
                    "RETURN DISTINCT bud "
                    "LIMIT 30"
                )

                # Execute the Cypher query
                results, meta = db.cypher_query(cypher_query, params={'liked_artists_ids': liked_artists_ids, 'user_uid': user.uid})

                # Extract buds from the query result
                buds = [User.inflate(record[0]) for record in results]

                data = {
                    'buds': [bud.serialize() for bud in buds],
                    'commonArtistsCount': len(liked_artists)
                }

                return JsonResponse({'message': 'Fetched buds successfully.', 'code': 200, 'successful': True, 'data': data})
            else:
                return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': str(e)}, status=500)        

class get_buds_by_tracks(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_tracks, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user = request.user

            # Retrieve the user from the database
            user_node = User.nodes.get_or_none(uid=user.uid)
            if user_node:
                # Retrieve the list of tracks liked by the user
                liked_tracks = user_node.likes_track.all()
                liked_tracks_ids = [track.uid for track in liked_tracks]

                if not liked_tracks_ids:
                    return JsonResponse({'error': 'No liked tracks found for user'}, status=404)

                # Construct a Cypher query to find buds who like the same tracks
                cypher_query = (
                    "MATCH (bud:User)-[:LIKES_TRACK]->(track:Track) "
                    "WHERE track.uid IN $liked_tracks_ids "
                    "AND bud.uid <> $user_uid "
                    "RETURN DISTINCT bud "
                    "LIMIT 30"
                )

                # Execute the Cypher query
                results, meta = db.cypher_query(cypher_query, params={'liked_tracks_ids': liked_tracks_ids, 'user_uid': user.uid})

                # Extract buds from the query result
                buds = [User.inflate(record[0]) for record in results]

                data = {
                    'buds': [bud.serialize() for bud in buds],
                    'commonTracksCount': len(liked_tracks)
                }

                return JsonResponse({'message': 'Fetched buds successfully.', 'code': 200, 'successful': True, 'data': data})
            else:
                return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': str(e)}, status=500)

class get_buds_by_artists_and_tracks_and_genres(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_artists_and_tracks_and_genres, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user_id = request.user.uid  # Get the user's UID
            user_node = User.nodes.get_or_none(uid=user_id)

            if user_node:
                # Retrieve the list of artists, tracks, and genres liked by the user
                liked_artists = user_node.likes_artist.all()
                liked_tracks = user_node.likes_track.all()
                liked_genres = user_node.likes_genre.all()

                liked_artists_ids = [artist.uid for artist in liked_artists]
                liked_tracks_ids = [track.uid for track in liked_tracks]
                liked_genres_names = [genre.name for genre in liked_genres]

                if not liked_artists_ids and not liked_tracks_ids and not liked_genres_names:
                    return JsonResponse({'error': 'No liked artists, tracks, or genres found for user'}, status=404)

                # Construct a Cypher query to find buds who like the same artists, tracks, or genres
                cypher_query = (
                    "MATCH (bud:User)-[:LIKES_ARTIST]->(artist:Artist), "
                    "(bud)-[:LIKES_TRACK]->(track:Track), "
                    "(bud)-[:LIKES_GENRE]->(genre:Genre) "
                    "WHERE (artist.uid IN $liked_artists_ids OR track.uid IN $liked_tracks_ids OR genre.name IN $liked_genres_names) "
                    "AND bud.uid <> $user_uid "
                    "RETURN DISTINCT bud "
                    "LIMIT 30"
                )

                # Execute the Cypher query
                results, meta = db.cypher_query(cypher_query, params={
                    'liked_artists_ids': liked_artists_ids,
                    'liked_tracks_ids': liked_tracks_ids,
                    'liked_genres_names': liked_genres_names,
                    'user_uid': user_id
                })

                # Extract buds from the query result
                buds = [User.inflate(record[0]) for record in results]

                data = {
                    'buds': [bud.serialize() for bud in buds],
                    'commonArtistsCount': len(liked_artists),
                    'commonTracksCount': len(liked_tracks),
                    'commonGenresCount': len(liked_genres),
                    'commonCount': len(liked_artists) + len(liked_tracks) + len(liked_genres)
                }

                return JsonResponse({'message': 'Fetched buds successfully.', 'code': 200, 'successful': True, 'data': data})
            else:
                return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': str(e)}, status=500)
class get_buds_by_genres(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_genres, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user_id = request.user.uid  # Get the user's UID
            user_node = User.nodes.get_or_none(uid=user_id)

            if user_node:
                # Retrieve the genres liked by the user
                liked_genres = user_node.likes_genre.all()
                liked_genres_names = [genre.name for genre in liked_genres]

                if not liked_genres_names:
                    return JsonResponse({'error': 'No liked genres found for user'}, status=404)

                # Construct a Cypher query to find buds who like the same genres
                cypher_query = (
                    "MATCH (bud:User)-[:LIKES_GENRE]->(genre:Genre) "
                    "WHERE genre.name IN $liked_genres_names "
                    "AND bud.uid <> $user_uid "
                    "RETURN DISTINCT bud "
                    "LIMIT 30"
                )

                # Execute the Cypher query
                results, meta = db.cypher_query(cypher_query, params={
                    'liked_genres_names': liked_genres_names,
                    'user_uid': user_id
                })

                # Extract buds from the query result
                buds = [User.inflate(record[0]) for record in results]

                data = {
                    'buds': [bud.serialize() for bud in buds],
                    'commonGenresCount': len(liked_genres)
                }

                return JsonResponse({'message': 'Fetched buds successfully.', 'code': 200, 'successful': True, 'data': data})
            else:
                return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': str(e)}, status=500)
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
