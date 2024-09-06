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
from app.db_models.parent_user import ParentUser
import time

logger = logging.getLogger('app')

class BudsBaseMixin:
    authentication_classes = [AsyncJWTAuthentication]

    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super().dispatch(*args, **kwargs)

    async def get_user_node(self, request):
        user_node = request.user
        if not user_node:
            logger.warning('User not found')
            raise ValueError('User not found')
        return user_node

    async def fetch_buds_data(self, buds_results):
        buds_data = []
        try:
            for bud in buds_results:
                bud_uid, similarity_score = bud
                parent_user = await ParentUser.nodes.get_or_none(uid=bud_uid)
                if not parent_user:
                    neo4j_user = await self.get_user_from_neo4j(bud_uid)
                    if neo4j_user:
                        parent_user = await self.sync_user_to_django(neo4j_user)
                
                if parent_user:
                    serialized_parent = await parent_user.without_relations_serialize()
                    buds_data.append({
                        'bud': serialized_parent,
                        'similarity_score': similarity_score
                    })
                else:
                    logger.warning(f"User with uid {bud_uid} not found in both Django and Neo4j")
            logger.info(f"Fetched data for {len(buds_data)} out of {len(buds_results)} buds")
        except Exception as e:
            logger.error(f'Error in fetch_buds_data: {e}', exc_info=True)
        return buds_data

    async def get_user_from_neo4j(self, uid):
        query = """
        MATCH (u:ParentUser {uid: $uid})
        RETURN u.uid AS uid, u.username AS username, u.is_active AS is_active
        """
        results, _ = await sync_to_async(db.cypher_query)(query, {'uid': uid})
        if results:
            user_data = results[0]
            return {
                'uid': user_data[0],
                'username': user_data[1],
                'is_active': user_data[2]
            }
        return None

    async def sync_user_to_django(self, neo4j_user):
        try:
            django_user, created = await sync_to_async(ParentUser.nodes.get_or_create)(
                uid=neo4j_user['uid'],
                defaults={
                    'username': neo4j_user['username'],
                    'is_active': neo4j_user['is_active']
                }
            )
            if created:
                logger.info(f"Created new ParentUser for uid {neo4j_user['uid']}")
            return django_user
        except Exception as e:
            logger.error(f"Error syncing user to Django: {e}", exc_info=True)
            return None

    async def paginate_response(self, request, buds_data):
        paginator = StandardResultsSetPagination()
        paginated_buds = paginator.paginate_queryset(buds_data, request)
        paginated_response = paginator.get_paginated_response(paginated_buds)
        paginated_response.update({
            'message': 'Fetched buds successfully.' if buds_data else 'No buds found.',
            'code': 200,
            'successful': True,
        })
        logger.info(f"Paginated response: {paginated_response}")  # Add this line
        return paginated_response

    async def post(self, request):
        start_time = time.time()
        try:
            user_node = await self.get_user_node(request)
            buds = await self.get_buds_by_top(user_node)
            
            logger.info(f"Raw buds data: {buds}")  # Add this line
            
            buds_data = await self.fetch_buds_data(buds)
            
            logger.info(f"Processed buds data: {buds_data}")  # Add this line
            
            response = await self.paginate_response(request, buds_data)

            end_time = time.time()
            logger.info(f'Successfully fetched {len(buds)} buds for user: uid={user_node.uid} in {end_time - start_time:.2f} seconds')
            return JsonResponse(response)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in {self.__class__.__name__}: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class GetBudsByTopArtists(BudsBaseMixin, APIView):
    async def get_buds_by_top(self, user_node):
        try:
            buds_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(ua)-[:TOP_ARTIST]->(artist)
            MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(oa)-[:TOP_ARTIST]->(artist)
            WHERE other.uid <> u.uid AND other.is_active = true
            WITH DISTINCT other, count(DISTINCT artist) AS common_count
            ORDER BY common_count DESC
            LIMIT 100
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            """
            buds_results, _ = await sync_to_async(db.cypher_query)(buds_query, {'user_uid': user_node.uid})
            
            if len(buds_results) < 10:
                logger.info(f"Found only {len(buds_results)} buds for user {user_node.uid}. Falling back to genre-based matching.")
                genre_query = """
                MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(ua)-[:LIKES_GENRE]->(genre)
                MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(oa)-[:LIKES_GENRE]->(genre)
                WHERE other.uid <> u.uid AND other.is_active = true
                WITH DISTINCT other, count(DISTINCT genre) AS common_count
                ORDER BY common_count DESC
                LIMIT 50
                RETURN other.uid AS bud_uid, common_count AS similarity_score
                """
                genre_results, _ = await sync_to_async(db.cypher_query)(genre_query, {'user_uid': user_node.uid})
                buds_results.extend(genre_results)
            
            logger.info(f"Found {len(buds_results)} potential buds for user {user_node.uid}")
            
            # Ensure the results are in the correct format
            formatted_results = [(str(bud[0]), float(bud[1])) for bud in buds_results]
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error in get_buds_by_top for user uid={user_node.uid}: {str(e)}", exc_info=True)
            return []

class GetBudsByTopTracks(BudsBaseMixin, APIView):
    async def get_buds_by_top(self, user_node):
        try:
            buds_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(ua)-[:TOP_TRACK]->(track)
            MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(oa)-[:TOP_TRACK]->(track)
            WHERE other.uid <> u.uid AND other.is_active = true
            WITH DISTINCT other, count(DISTINCT track) AS common_count
            ORDER BY common_count DESC
            LIMIT 50
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            """
            buds_results, _ = await sync_to_async(db.cypher_query)(buds_query, {'user_uid': user_node.uid})
            return buds_results
        except Exception as e:
            logger.error(f"Error in get_buds_by_top for user uid={user_node.uid}: {str(e)}", exc_info=True)
            return []

class GetBudsByTopGenres(BudsBaseMixin, APIView):
    async def get_buds_by_top(self, user_node):
        try:
            buds_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(ua)-[:LIKES_GENRE]->(genre)
            MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(oa)-[:LIKES_GENRE]->(genre)
            WHERE other.uid <> u.uid AND other.is_active = true
            WITH DISTINCT other, count(DISTINCT genre) AS common_count
            ORDER BY common_count DESC
            LIMIT 50
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            """
            buds_results, _ = await sync_to_async(db.cypher_query)(buds_query, {'user_uid': user_node.uid})
            return buds_results
        except Exception as e:
            logger.error(f"Error in get_buds_by_top for user uid={user_node.uid}: {str(e)}", exc_info=True)
            return []

class GetBudsByTopManga(BudsBaseMixin, APIView):
    async def get_buds_by_top(self, user_node):
        try:
            buds_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_MAL]->(ma)-[:TOP_MANGA]->(manga)
            MATCH (other:ParentUser)-[:CONNECTED_TO_MAL]->(oma)-[:TOP_MANGA]->(manga)
            WHERE other.uid <> u.uid AND other.is_active = true
            WITH DISTINCT other, count(DISTINCT manga) AS common_count
            ORDER BY common_count DESC
            LIMIT 50
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            """
            buds_results, _ = await sync_to_async(db.cypher_query)(buds_query, {'user_uid': user_node.uid})
            return buds_results
        except Exception as e:
            logger.error(f"Error in get_buds_by_top for user uid={user_node.uid}: {str(e)}", exc_info=True)
            return []

class GetBudsByTopAnime(BudsBaseMixin, APIView):
    async def get_buds_by_top(self, user_node):
        try:
            buds_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_MAL]->(ma)-[:TOP_ANIME]->(anime)
            MATCH (other:ParentUser)-[:CONNECTED_TO_MAL]->(oma)-[:TOP_ANIME]->(anime)
            WHERE other.uid <> u.uid AND other.is_active = true
            WITH DISTINCT other, count(DISTINCT anime) AS common_count
            ORDER BY common_count DESC
            LIMIT 50
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            """
            buds_results, _ = await sync_to_async(db.cypher_query)(buds_query, {'user_uid': user_node.uid})
            return buds_results
        except Exception as e:
            logger.error(f"Error in get_buds_by_top for user uid={user_node.uid}: {str(e)}", exc_info=True)
            return []
