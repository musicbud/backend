from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..middlewares.custom_token_auth import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination
import logging
from ..db_models.genre import Genre
from ..db_models.track import Track
from ..db_models.artist import Artist
from ..db_models.album import Album

from app.forms.get_by_id import GetByIdForm



logger = logging.getLogger('app')

class GetBudsBase(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(GetBudsBase, self).dispatch(*args, **kwargs)

    async def post(self, request):

        form = GetByIdForm(request.data)

        if not form.is_valid():
            return JsonResponse({'error': 'Invalid input', 'details': form.errors}, status=400)
        
        try:
            user = request.user
            identifier = self.get_identifier(request)

            if not identifier:
                return JsonResponse({'error': f'{self.get_identifier_name()} not provided'}, status=400)

            account_ids = [account.uid for account in user.associated_accounts.values() if account]
            node = await self.get_node(identifier)

            if not node:
                return JsonResponse({'error': f'{self.get_identifier_name()} not found'}, status=404)

            # Get users who liked the specified item, excluding the current user's accounts
            users = await node.users.exclude(uid__in=account_ids).all()

            # Fetch buds data
            buds_data = await self._fetch_buds_data(users)

            # Pagination
            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by {self.get_identifier_name()} for user: uid={user.uid}, {self.get_identifier_name()}_id={identifier}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsBase: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    def get_identifier(self, request):
        """Returns the identifier from the request data."""
        raise NotImplementedError("Subclasses must implement get_identifier() method.")

    def get_identifier_name(self):
        """Returns the name of the identifier."""
        raise NotImplementedError("Subclasses must implement get_identifier_name() method.")

    async def get_node(self, identifier):
        """Fetches the node based on the identifier."""
        raise NotImplementedError("Subclasses must implement get_node() method.")

    async def _fetch_buds_data(self, users):
        buds_data = []

        try:
            for bud in users:
                bud_parent = await bud.parent.all()
                parent_serialized = await self._serialize_parent(bud_parent)

                buds_data.append({
                    'bud': parent_serialized,
                })

        except Exception as e:
            logger.error(f'Error in _fetch_buds_data: {e}', exc_info=True)

        logger.debug(f'Prepared buds data list with {len(buds_data)} entries.')
        return buds_data

    async def _serialize_parent(self, bud_parent):
        serialized_data = []
        for parent in bud_parent:
            serialized_data.append(await parent.without_relations_serialize())
        return serialized_data


class GetBusdByTrack(GetBudsBase):
    def get_identifier(self, request):
        return request.data.get('track_id')

    def get_identifier_name(self):
        return 'track_id'

    async def get_node(self, identifier):
        return await Track.nodes.get_or_none(uid=identifier)
    
class GetBudsByArtist(GetBudsBase):
    def get_identifier(self, request):
        return request.data.get('artist_id')

    def get_identifier_name(self):
        return 'artist_id'

    async def get_node(self, identifier):
        return await Artist.nodes.get_or_none(uid=identifier)
    
class GetBudsByGenre(GetBudsBase):
    def get_identifier(self, request):
        return request.data.get('genre_id')

    def get_identifier_name(self):
        return 'genre_id'

    async def get_node(self, identifier):
        return await Genre.nodes.get_or_none(uid=identifier)
    
class GetBudsByAlbum(GetBudsBase):
    def get_identifier(self, request):
        return request.data.get('album_id')

    def get_identifier_name(self):
        return 'album_id'

    async def get_node(self, identifier):
        return await Album.nodes.get_or_none(uid=identifier)