from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.user import User
from ..middlewares.custom_token_auth import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging

logger = logging.getLogger('app')

class BudsMixin:
    authentication_classes = [CustomTokenAuthentication]
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

    async def get_account_ids(self, user_node):
        return [account.uid for account in user_node.associated_accounts.values() if account]

    async def fetch_buds_data(self, unique_buds):
        buds_data = []
        try:
            for bud_uid in unique_buds:
                bud = await User.nodes.get_or_none(uid=bud_uid)
                if bud:
                    bud_parent = await bud.parent.all()
                    parent_serialized = await self.serialize_parent(bud_parent)
                    buds_data.append({'bud': parent_serialized})
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in fetch_buds_data: {e}', exc_info=True)
        return buds_data

    async def serialize_parent(self, bud_parent):
        serialized_data = []
        for parent in bud_parent:
            serialized_data.append(await parent.without_relations_serialize())
        return serialized_data

    async def paginate_response(self, request, buds_data):
        paginator = StandardResultsSetPagination()
        paginated_buds = paginator.paginate_queryset(buds_data, request)
        paginated_response = paginator.get_paginated_response(paginated_buds)
        paginated_response.update({
            'message': 'Fetched buds successfully.',
            'code': 200,
            'successful': True,
        })
        return paginated_response

class GetBudsByLikedAlbums(BudsMixin, APIView):
    async def post(self, request):
        try:
            user_node = await self.get_user_node(request)
            account_ids = await self.get_account_ids(user_node)
            buds = await self.get_buds_by_liked_albums(user_node, account_ids)

            unique_buds = set(bud for bud in buds if bud not in account_ids)
            buds_data = await self.fetch_buds_data(unique_buds)
            response = await self.paginate_response(request, buds_data)

            logger.info(f'Successfully fetched buds by liked albums for user: uid={user_node.uid}')
            return JsonResponse(response)

        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByLikedAlbums: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

    async def get_buds_by_liked_albums(self, user_node, account_ids):
        buds = []
        try:
            for account in user_node.associated_accounts.values():
                if account:
                    liked_albums = await account.likes_albums.all()
                    for album in liked_albums:
                        album_users = await album.users.all()
                        buds.extend(user.uid for user in album_users if hasattr(user, 'uid'))
        except Exception as e:
            logger.error(f'Error in get_buds_by_liked_albums: {e}', exc_info=True)
        return buds

class GetBudsByLikedArtists(BudsMixin, APIView):
    async def post(self, request):
        try:
            user_node = await self.get_user_node(request)
            account_ids = await self.get_account_ids(user_node)
            buds = await self.get_buds_by_liked_artists(user_node, account_ids)

            unique_buds = set(bud for bud in buds if bud not in account_ids)
            buds_data = await self.fetch_buds_data(unique_buds)
            response = await self.paginate_response(request, buds_data)

            logger.info(f'Successfully fetched buds by liked artists for user: uid={user_node.uid}')
            return JsonResponse(response)

        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            logger.error(f'Error in GetBudsByLikedArtists: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

    async def get_buds_by_liked_artists(self, user_node, account_ids):
        buds = []
        try:
            for account in user_node.associated_accounts.values():
                if account:
                    liked_artists = await account.likes_artists.all()
                    for artist in liked_artists:
                        artist_users = await artist.users.all()
                        buds.extend(user.uid for user in artist_users if hasattr(user, 'uid'))
        except Exception as e:
            logger.error(f'Error in get_buds_by_liked_artists: {e}', exc_info=True)
        return buds

class GetBudsByLikedGenres(BudsMixin, APIView):
    async def post(self, request):
        try:
            user_node = await self.get_user_node(request)
            account_ids, liked_genres = await self.get_account_liked_genres(user_node)
            buds = await self.get_buds_by_liked_genres(liked_genres, account_ids)

            buds_data = await self.fetch_buds_data(buds)
            response = await self.paginate_response(request, buds_data)

            logger.info(f'Successfully fetched buds by liked genres for user: uid={user_node.uid}')
            return JsonResponse(response)

        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByLikedGenres: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

    async def get_account_liked_genres(self, user_node):
        account_ids = []
        liked_genres = []
        try:
            for account in user_node.associated_accounts.values():
                if account:
                    account_liked_genres = await account.likes_genres.all()
                    liked_genres.extend(account_liked_genres)
                    account_ids.append(account.uid)
        except Exception as e:
            logger.error(f'Error in get_account_liked_genres: {e}', exc_info=True)
        return account_ids, liked_genres

    async def get_buds_by_liked_genres(self, liked_genres, account_ids):
        buds = set()
        try:
            for genre in liked_genres:
                genre_users = await genre.users.exclude(uid__in=account_ids).all()
                buds.update(user.uid for user in genre_users if hasattr(user, 'uid'))
        except Exception as e:
            logger.error(f'Error in get_buds_by_liked_genres: {e}', exc_info=True)
        return buds

class GetBudsByPlayedTracks(BudsMixin, APIView):
    async def post(self, request):
        try:
            user_node = await self.get_user_node(request)
            account_ids = await self.get_account_ids(user_node)
            buds = await self.get_buds_by_played_tracks(user_node, account_ids)

            unique_buds = set(bud for bud in buds if bud not in account_ids)
            buds_data = await self.fetch_buds_data(unique_buds)
            response = await self.paginate_response(request, buds_data)

            logger.info(f'Successfully fetched buds by played tracks for user: uid={user_node.uid}')
            return JsonResponse(response)

        except ValueError as e:
            error_type = type(e).__name__
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByPlayedTracks: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

    async def get_buds_by_played_tracks(self, user_node, account_ids):
        buds = []
        try:
            for account in user_node.associated_accounts.values():
                if account and hasattr(account, 'played_tracks'):
                    played_tracks = await account.played_tracks.all()
                    for track in played_tracks:
                        track_users = await track.users.exclude(uid__in=account_ids).all()
                        buds.extend(user.uid for user in track_users if hasattr(user, 'uid'))
        except Exception as e:
            logger.error(f'Error in get_buds_by_played_tracks: {e}', exc_info=True)
        return buds
    
class GetBudsByLikedTracks(BudsMixin, APIView):
    async def post(self, request):
        try:
            user_node = await self.get_user_node(request)
            account_ids = await self.get_account_ids(user_node)
            buds = await self.get_buds_by_liked_tracks(user_node, account_ids)

            unique_buds = set(bud for bud in buds if bud not in account_ids)
            buds_data = await self.fetch_buds_data(unique_buds)
            response = await self.paginate_response(request, buds_data)

            logger.info(f'Successfully fetched buds by liked tracks for user: uid={user_node.uid}')
            return JsonResponse(response)

        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'Error in GetBudsByLikedTracks: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)

    async def get_buds_by_liked_tracks(self, user_node, account_ids):
        buds = []
        try:
            for account in user_node.associated_accounts.values():
                if account:
                    liked_tracks = await account.likes_tracks.all()
                    for track in liked_tracks:
                        track_users = await track.users.exclude(uid__in=account_ids).all()
                        buds.extend(user.uid for user in track_users if hasattr(user, 'uid'))
        except Exception as e:
            logger.error(f'Error in get_buds_by_liked_tracks: {e}', exc_info=True)
        return buds