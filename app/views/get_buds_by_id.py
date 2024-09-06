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

def serialize_parent_user(parent_user): 
    return {
        'uid': parent_user.uid,
        'username': parent_user.username,
        'email': parent_user.email,
        'display_name': parent_user.display_name,
        # Add any other fields you want to include
    }

class GetBudsByEntity(APIView):
    authentication_classes = [AsyncJWTAuthentication]

    permission_classes = [IsAuthenticated]
    entity_type = None

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super().dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user = request.user
            entity_id_field = f"{self.entity_type}_id" if self.entity_type else "entity_id"
            entity_id = request.data.get(entity_id_field)

            if not entity_id:
                return JsonResponse({'error': f'{entity_id_field.capitalize()} is required'}, status=400)

            if not self.entity_type:
                entity_type = request.data.get('entity_type')
                if not entity_type or entity_type not in ['track', 'artist', 'genre', 'album']:
                    return JsonResponse({'error': 'Invalid or missing entity type'}, status=400)
            else:
                entity_type = self.entity_type

            buds = await self.get_common_buds(user, entity_type, entity_id)
            buds_data = await self._fetch_buds_data(buds)

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)
            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds for user: uid={user.uid}, entity_type={entity_type}, {entity_id_field}={entity_id}')
            return JsonResponse(paginated_response)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByEntity: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

    async def get_common_buds(self, user, entity_type, entity_id):
        try:
            query = f"""
            MATCH (u:ParentUser {{uid: $user_uid}})
            MATCH (entity:{entity_type.capitalize()} {{uid: $entity_id}})
            MATCH (u)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->()-[:LIKES_{entity_type.upper()}]->(entity)
            MATCH (other:ParentUser)-[:CONNECTED_TO_SPOTIFY|CONNECTED_TO_LASTFM|CONNECTED_TO_YTMUSIC]->()-[:LIKES_{entity_type.upper()}]->(entity)
            WHERE other.uid <> u.uid
            WITH DISTINCT other, count(DISTINCT entity) AS common_count
            RETURN other.uid AS bud_uid, common_count AS similarity_score
            ORDER BY similarity_score DESC
            LIMIT 50
            """

            results, _ = await sync_to_async(db.cypher_query)(query, {
                'user_uid': user.uid,
                'entity_id': entity_id
            })

            logger.debug(f"Common buds query results: {results}")

            return results

        except Exception as e:
            logger.error(f'Error in get_common_buds for user uid={user.uid}: {e}', exc_info=True)
            return []

    async def _fetch_buds_data(self, buds):
        buds_data = []
        try:
            for bud in buds:
                bud_uid, similarity_score = bud
                parent_user = await ParentUser.nodes.get_or_none(uid=bud_uid)
                if not parent_user:
                    logger.warning(f"User with uid {bud_uid} not found in Neo4j DB. Skipping.")
                    continue
                
                serialized_parent = serialize_parent_user(parent_user)
                buds_data.append({
                    'bud': serialized_parent,
                    'similarity_score': similarity_score
                })
        except Exception as e:
            logger.error(f'Error in _fetch_buds_data: {e}', exc_info=True)
        
        logger.info(f'Data preparation complete. Total buds data prepared: {len(buds_data)}')
        return buds_data

class GetBudsByArtist(GetBudsByEntity):
    entity_type = 'artist'

class GetBudsByTrack(GetBudsByEntity):
    entity_type = 'track'

class GetBudsByGenre(GetBudsByEntity):
    entity_type = 'genre'

class GetBudsByAlbum(GetBudsByEntity):
    entity_type = 'album'
