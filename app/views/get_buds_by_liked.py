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

logger = logging.getLogger('app')

class BudsMixin:
    authentication_classes = [AsyncJWTAuthentication]

    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super().dispatch(*args, **kwargs)

    async def get_user_node(self, request):
        user_node = request.parent_user
        if not user_node:
            logger.warning('User not found')
            raise ValueError('User not found')
        return user_node

    async def fetch_buds_data(self, buds_results):
        buds_data = []
        try:
            for bud in buds_results:
                bud_uid, similarity_score = bud
                logger.info(f"Processing bud: {bud_uid} with similarity score: {similarity_score}")
                parent_user = await ParentUser.nodes.get_or_none(uid=bud_uid)
                if parent_user:
                    serialized_parent = await parent_user.serialize()
                    buds_data.append({
                        'bud': serialized_parent,
                        'similarity_score': similarity_score
                    })
                else:
                    logger.warning(f"User with uid {bud_uid} not found")
        except Exception as e:
            logger.error(f'Error in fetch_buds_data: {e}', exc_info=True)
        logger.info(f"Fetched buds data: {buds_data}")
        return buds_data

    async def paginate_response(self, request, buds_data):
        logger.info(f"Paginating response for {len(buds_data)} buds")
        paginator = StandardResultsSetPagination()
        paginated_buds = paginator.paginate_queryset(buds_data, request)
        paginated_response = paginator.get_paginated_response(paginated_buds)
        paginated_response.update({
            'message': 'Fetched buds successfully.' if buds_data else 'No buds found.',
            'code': 200,
            'successful': True,
        })
        logger.info(f"Paginated response: {paginated_response}")
        return paginated_response

class GetBudsByLikedAlbums(BudsMixin, APIView):
    async def post(self, request):
        try:
            user_node = await self.get_user_node(request)
            buds_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(ua)-[:LIKES_ALBUM]->(album)
            MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(oa)-[:LIKES_ALBUM]->(album)
            WHERE other.uid <> u.uid
            WITH DISTINCT other, count(DISTINCT album) AS common_count
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            ORDER BY similarity_score DESC
            LIMIT 50
            """
            buds_results, _ = await sync_to_async(db.cypher_query)(buds_query, {'user_uid': user_node.uid})
            buds_data = await self.fetch_buds_data(buds_results)
            response = await self.paginate_response(request, buds_data)

            logger.info(f'Successfully fetched buds by liked albums for user: uid={user_node.uid}')
            return JsonResponse(response)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByLikedAlbums: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class GetBudsByLikedArtists(BudsMixin, APIView):
    async def post(self, request):
        try:
            user_node = await self.get_user_node(request)
            logger.info(f'Fetching buds for user: {user_node.uid}')
            
            buds_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->()-[:LIKES_ARTIST]->(artist)
            MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->()-[:LIKES_ARTIST]->(artist)
            WHERE other.uid <> u.uid
            WITH DISTINCT other, count(DISTINCT artist) AS common_count
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            ORDER BY similarity_score DESC
            LIMIT 50
            """
            buds_results, _ = await sync_to_async(db.cypher_query)(buds_query, {'user_uid': user_node.uid})
            logger.info(f'Cypher query results: {buds_results}')
            
            buds_data = await self.fetch_buds_data(buds_results)
            logger.info(f'Fetched buds data: {buds_data}')
            
            response = await self.paginate_response(request, buds_data)
            logger.info(f'Paginated response: {response}')

            logger.info(f'Successfully fetched buds by liked artists for user: uid={user_node.uid}')
            return JsonResponse(response)
        except ValueError as e:
            logger.error(f'ValueError in GetBudsByLikedArtists: {e}')
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByLikedArtists: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class GetBudsByLikedGenres(BudsMixin, APIView):
    async def post(self, request):
        try:
            user_node = await self.get_user_node(request)
            buds_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(ua)-[:LIKES_GENRE]->(genre)
            MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(oa)-[:LIKES_GENRE]->(genre)
            WHERE other.uid <> u.uid
            WITH DISTINCT other, count(DISTINCT genre) AS common_count
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            ORDER BY similarity_score DESC
            LIMIT 50
            """
            buds_results, _ = await sync_to_async(db.cypher_query)(buds_query, {'user_uid': user_node.uid})
            logger.info(f"Cypher query results: {buds_results}")
            buds_data = await self.fetch_buds_data(buds_results)
            response = await self.paginate_response(request, buds_data)

            logger.info(f'Successfully fetched buds by liked genres for user: uid={user_node.uid}')
            return JsonResponse(response)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByLikedGenres: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class GetBudsByPlayedTracks(BudsMixin, APIView):
    async def post(self, request):
        try:
            user_node = await self.get_user_node(request)
            buds_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(ua)-[:PLAYED_TRACK]->(track)
            MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(oa)-[:PLAYED_TRACK]->(track)
            WHERE other.uid <> u.uid
            WITH DISTINCT other, count(DISTINCT track) AS common_count
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            ORDER BY similarity_score DESC
            LIMIT 50
            """
            buds_results, _ = await sync_to_async(db.cypher_query)(buds_query, {'user_uid': user_node.uid})
            buds_data = await self.fetch_buds_data(buds_results)
            response = await self.paginate_response(request, buds_data)

            logger.info(f'Successfully fetched buds by played tracks for user: uid={user_node.uid}')
            return JsonResponse(response)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByPlayedTracks: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

class GetBudsByLikedTracks(BudsMixin, APIView):
    async def post(self, request):
        try:
            user_node = await self.get_user_node(request)
            buds_query = """
            MATCH (u:ParentUser {uid: $user_uid})-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(ua)-[:LIKES_TRACK]->(track)
            MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->(oa)-[:LIKES_TRACK]->(track)
            WHERE other.uid <> u.uid
            WITH DISTINCT other, count(DISTINCT track) AS common_count
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            ORDER BY similarity_score DESC
            LIMIT 50
            """
            buds_results, _ = await sync_to_async(db.cypher_query)(buds_query, {'user_uid': user_node.uid})
            buds_data = await self.fetch_buds_data(buds_results)
            response = await self.paginate_response(request, buds_data)

            logger.info(f'Successfully fetched buds by liked tracks for user: uid={user_node.uid}')
            return JsonResponse(response)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByLikedTracks: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

