from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from app.middlewares.async_jwt_authentication import AsyncJWTAuthentication
from ..pagination import StandardResultsSetPagination
import logging
from neomodel import db
from asgiref.sync import sync_to_async
from ..db_models.parent_user import ParentUser

logger = logging.getLogger('app')

class GetBudsByLikedAio(APIView):
    authentication_classes = [AsyncJWTAuthentication]

    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(GetBudsByLikedAio, self).dispatch(*args, **kwargs)

    async def _fetch_buds_data(self, buds):
        """Prepares the data for each bud."""
        buds_data = []
        logger.debug(f"Fetching data for {len(buds)} buds")
        for bud in buds:
            bud_user = bud['user']
            similarity_score = bud['similarity_score']
            
            # Serialize the user data
            serialized_user = await self._serialize_user(bud_user)
            
            buds_data.append({
                'bud': serialized_user,
                'similarity_score': similarity_score
            })
            logger.info(f"Prepared bud: uid={serialized_user['uid']}, similarity_score={similarity_score}")
        
        logger.info(f'Data preparation complete. Total buds data prepared: {len(buds_data)}')
        return buds_data

    async def _serialize_user(self, user_node):
        """Serialize a user node into a dictionary."""
        return {
            'uid': user_node['uid'],
            'username': user_node.get('username'),
            'display_name': user_node.get('display_name'),
            'photo_url': user_node.get('photo_url'),
            'bio': user_node.get('bio'),
            # Add any other fields you want to include
        }

    async def get_user_by_uid(self, uid):
        query = """
        MATCH (u:ParentUser {uid: $uid})
        RETURN u
        """
        results, _ = await sync_to_async(db.cypher_query)(query, {'uid': uid})
        if results:
            user_data = results[0][0]
            logger.info(f"Retrieved user data for uid {uid}: {user_data}")
            return user_data
        else:
            logger.warning(f"No user found with uid {uid}")
            return None

    async def get_common_buds(self, user_node):
        try:
            # First, verify the requesting user exists
            user_data = await self.get_user_by_uid(user_node.uid)
            if not user_data:
                logger.error(f"Requesting user {user_node.uid} not found in the database")
                return []

            # Check the user's connections
            await self.check_user_connections(user_node.uid)

            # Check active users in the database
            active_users = await self.check_active_users()
            if not active_users:
                logger.warning("No active users found in the database")
                return []

            # Proceed with the original logic...
            similar_tastes_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY]->(uSpotify:SpotifyUser)
            MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY]->(otherSpotify:SpotifyUser)
            WHERE other.uid <> u.uid AND other.is_active = true

            OPTIONAL MATCH (uSpotify)-[:LIKES_GENRE]->(genre:Genre)<-[:LIKES_GENRE]-(otherSpotify)
            WITH u, other, count(DISTINCT genre) AS sharedGenres

            OPTIONAL MATCH (uSpotify)-[:LIKES_ARTIST]->(artist:Artist)<-[:LIKES_ARTIST]-(otherSpotify)
            WITH u, other, sharedGenres, count(DISTINCT artist) AS sharedArtists

            OPTIONAL MATCH (uSpotify)-[:PLAYED_TRACK]->(track:Track)<-[:PLAYED_TRACK]-(otherSpotify)
            WITH other, sharedGenres * 3 + sharedArtists * 2 + count(DISTINCT track) AS similarityScore

            RETURN other.uid AS bud_uid, similarityScore
            ORDER BY similarityScore DESC
            LIMIT 20
            """

            similar_tastes_results, _ = await sync_to_async(db.cypher_query)(similar_tastes_query, {
                'user_uid': user_node.uid
            })

            logger.info(f"Found {len(similar_tastes_results)} potential buds for user {user_node.uid}")

            # Process potential buds
            buds = []
            for result in similar_tastes_results:
                bud_uid = result[0]
                bud_user = await self.get_user_by_uid(bud_uid)
                if bud_user:
                    buds.append({
                        'user': bud_user,
                        'similarity_score': result[1],
                    })

            if not buds:
                logger.warning(f"No valid buds found for user {user_node.uid}. Falling back to popular users.")
                buds = await self.get_popular_users(limit=10)

            if not buds:
                logger.warning(f"No popular users found. Falling back to any active users.")
                buds = await self.get_any_active_users(limit=10)

            return buds

        except Exception as e:
            logger.error(f'Error in get_common_buds for user uid={user_node.uid}: {e}', exc_info=True)
            return []

    async def get_popular_users(self, limit=10):
        popular_users_query = """
        MATCH (u:ParentUser)-[:CONNECTED_TO_SPOTIFY]->(s:SpotifyUser)
        WHERE u.is_active = true
        WITH u, size((s)-[:LIKES_GENRE]->()) + size((s)-[:LIKES_ARTIST]->()) + size((s)-[:PLAYED_TRACK]->()) AS activity
        WHERE activity > 0
        RETURN u.uid AS bud_uid, activity
        ORDER BY activity DESC
        LIMIT $limit
        """
        results, _ = await sync_to_async(db.cypher_query)(popular_users_query, {'limit': limit})
        
        logger.info(f"Found {len(results)} popular users")
        
        buds = []
        for result in results:
            bud_uid, activity = result
            bud_user = await self.get_user_by_uid(bud_uid)
            if bud_user:
                buds.append({
                    'user': bud_user,
                    'similarity_score': activity,  # Use activity as a proxy for similarity
                })
            else:
                logger.warning(f"Popular user with uid {bud_uid} not found in the database.")
        return buds

    async def get_any_active_users(self, limit=10):
        active_users_query = """
        MATCH (u:ParentUser)-[:CONNECTED_TO_SPOTIFY]->(s:SpotifyUser)
        WHERE u.is_active = true
        RETURN u.uid AS bud_uid
        LIMIT $limit
        """
        results, _ = await sync_to_async(db.cypher_query)(active_users_query, {'limit': limit})
        
        logger.info(f"Found {len(results)} active users")
        
        buds = []
        for result in results:
            bud_uid = result[0]
            bud_user = await self.get_user_by_uid(bud_uid)
            if bud_user:
                buds.append({
                    'user': bud_user,
                    'similarity_score': 0,  # Indicate that this is a last-resort recommendation
                })
            else:
                logger.warning(f"Active user with uid {bud_uid} not found in the database.")
        return buds

    async def check_active_users(self):
        query = """
        MATCH (u:ParentUser)-[:CONNECTED_TO_SPOTIFY]->(s:SpotifyUser)
        WHERE u.is_active = true
        RETURN u.uid, u.username, u.display_name
        """
        results, _ = await sync_to_async(db.cypher_query)(query)
        for result in results:
            logger.info(f"Active user: uid={result[0]}, username={result[1]}, display_name={result[2]}")
        return results

    async def check_user_connections(self, uid):
        query = """
        MATCH (u:ParentUser {uid: $uid})-[:CONNECTED_TO_SPOTIFY]->(s:SpotifyUser)
        OPTIONAL MATCH (s)-[:LIKES_GENRE]->(g:Genre)
        OPTIONAL MATCH (s)-[:LIKES_ARTIST]->(a:Artist)
        OPTIONAL MATCH (s)-[:PLAYED_TRACK]->(t:Track)
        RETURN count(DISTINCT g) as genres, count(DISTINCT a) as artists, count(DISTINCT t) as tracks
        """
        results, _ = await sync_to_async(db.cypher_query)(query, {'uid': uid})
        if results:
            genres, artists, tracks = results[0]
            logger.info(f"User {uid} connections: {genres} genres, {artists} artists, {tracks} tracks")
        else:
            logger.warning(f"No connections found for user {uid}")

    async def post(self, request):
        try:
            user_node = request.user
            if not user_node:
                logger.warning('User not found in request')
                return JsonResponse({'error': 'User not found'}, status=404)

            logger.info(f'Received request from user: uid={user_node.uid}')

            # Check if parent user exists in the database
            parent_user_query = """
            MATCH (u)
            WHERE u.uid = $user_uid
            RETURN u, labels(u) as labels
            """
            parent_user_results, _ = await sync_to_async(db.cypher_query)(parent_user_query, {
                'user_uid': user_node.uid
            })
            logger.debug(f"Parent user check: {parent_user_results}")

            if not parent_user_results:
                logger.error(f"Parent user with UID {user_node.uid} not found in the database")
                return JsonResponse({'error': 'Parent user not found in database'}, status=404)

            parent_user, labels = parent_user_results[0]
            logger.debug(f"Parent user labels: {labels}")

            buds = await self.get_common_buds(user_node)
            buds_data = await self._fetch_buds_data(buds)

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)
            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds for user: uid={user_node.uid}, buds_count={len(buds)}')
            return JsonResponse(paginated_response)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByLikedAio: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

    async def cleanup_invalid_users(self):
        query = """
        MATCH (u:User)
        WHERE NOT EXISTS(u.uid)
        DETACH DELETE u
        """
        await sync_to_async(db.cypher_query)(query)

    async def calculate_basic_similarity(self, user1_uid, user2_uid):
        query = """
        MATCH (u1:User {uid: $user1_uid})-[:LIKES]->(item)<-[:LIKES]-(u2:User {uid: $user2_uid})
        RETURN count(item) as common_items
        """
        results, _ = await sync_to_async(db.cypher_query)(query, {'user1_uid': user1_uid, 'user2_uid': user2_uid})
        return results[0][0] if results else 0

