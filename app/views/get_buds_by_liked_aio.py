from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..db_models.User import User
from ..db_models.Parent_User import ParentUser
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination
import logging

logger = logging.getLogger('app')

class get_buds_by_liked_aio(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_liked_aio, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user_node = request.user

            if not user_node:
                logger.warning('User not found in request')
                return JsonResponse({'error': 'User not found'}, status=404)

            logger.info(f'Received request from user: uid={user_node.uid}')

            # Fetch the user's liked items as a single dictionary
            user_likes = {
                'likes_artists': [],
                'likes_tracks': [],
                'likes_genres': [],
                'likes_albums': []
            }

            for account in user_node.associated_accounts.values():
                if account:  # Check if the account exists
                    likes = await account.get_likes()
                    user_likes['likes_artists'].extend(likes.get('likes_artists', []))
                    user_likes['likes_tracks'].extend(likes.get('likes_tracks', []))
                    user_likes['likes_genres'].extend(likes.get('likes_genres', []))
                    user_likes['likes_albums'].extend(likes.get('likes_albums', []))

            # Fetch common buds based on liked items from associated accounts
            buds = await self.get_common_buds(user_node)

            # Prepare buds data
            buds_data = await self.prepare_buds_data(buds, user_likes,user_node)

            # Paginate the results
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
            logger.error(f'Error in get_buds_by_liked_aio: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    async def get_common_buds(self, user_node):
        """Fetches and returns unique buds based on the liked items from associated accounts."""
        buds = set()  # Initialize buds as a set to avoid duplicates

        try:
            associated_account_uids = {account.uid for account in user_node.associated_accounts.values() if account}

            for account in user_node.associated_accounts.values():
                if account and hasattr(account, 'get_likes'):
                    user_likes = await account.get_likes()
                    logger.debug(f'User likes for account uid={account.uid}: {len(user_likes)}')

                    if len(user_likes):
                        await self.find_common_buds(user_likes, user_node.uid, buds)
                        logger.debug(f'Updated buds after fetching likes from account uid={account.uid}: {len(buds)} buds found')

            # Remove self and associated accounts from buds and ensure uniqueness
            logger.debug(f'Final bud count before removing self: {len(buds)}')

            # Exclude the user node and its associated accounts from buds
            unique_bud_ids = [bud_uid for bud_uid in buds if bud_uid != user_node.uid and bud_uid not in associated_account_uids]
            user_objects = await User.nodes.filter(uid__in=unique_bud_ids).all()  # Assuming User is your model for users

            return user_objects
                
        except Exception as e:
            logger.error(f'Error in get_common_buds for user uid={user_node.uid}: {e}', exc_info=True)
            return []


    async def find_common_buds(self, user_likes, user_uid, buds):
        """Finds and adds users who liked the same artists, tracks, genres, and albums."""
        liked_artists = user_likes.get('likes_artists', [])
        liked_tracks = user_likes.get('likes_tracks', [])
        liked_genres = user_likes.get('likes_genres', [])
        liked_albums = user_likes.get('likes_albums', [])

        logger.debug(f'Finding common buds for user uid={user_uid}...')

        # Process liked artists
        await self._process_liked_items(liked_artists, user_uid, buds, 'artist')

        # Process liked tracks
        await self._process_liked_items(liked_tracks, user_uid, buds, 'track')

        # Process liked genres
        await self._process_liked_items(liked_genres, user_uid, buds, 'genre')

        # Process liked albums
        await self._process_liked_items(liked_albums, user_uid, buds, 'album')

        logger.info(f'Total common buds found for user uid={user_uid}: {len(buds)}')


    async def _process_liked_items(self, items, user_uid, buds, item_type):
        """Helper method to process liked items (artists, tracks, genres, albums)."""
        for item in items:
            item_uid = item.uid
            logger.debug(f'Processing {item_type} uid={item_uid}')

            new_buds = await item.users.exclude(uid=user_uid).all()
            # Add only user IDs to the set
            buds.update(new_bud.uid for new_bud in new_buds if hasattr(new_bud, 'uid'))  
            logger.debug(f'Found {len(new_buds)} new buds from {item_type} uid={item_uid}')

    async def prepare_buds_data(self, buds, user_likes, user_node):
        """Prepares the data for each bud, including common liked items."""
        buds_data = []
        unique_buds = set()  # To ensure uniqueness based on UID
        associated_account_uids = {account.uid for account in user_node.associated_accounts.values() if account}  # Collect UIDs of associated accounts
        logger.debug(f'Preparing data for {len(buds)} buds...')

        for bud in buds:
            # Skip the user node and its associated accounts
            if bud.uid in unique_buds or bud.uid == user_node.uid or bud.uid in associated_account_uids:
                continue  # Skip if this bud has already been processed or is the requesting user

            bud_likes = await bud.get_likes()  # Now bud is a User object
            logger.debug(f'Bud likes for uid={bud.uid}: {bud_likes}')

            # Ensure you pass the user's liked items as a second argument
            common_artists = ParentUser.get_common_items(bud_likes.get('likes_artists', []), user_likes.get('likes_artists', []))
            common_tracks = ParentUser.get_common_items(bud_likes.get('likes_tracks', []), user_likes.get('likes_tracks', []))
            common_genres = ParentUser.get_common_items(bud_likes.get('likes_genres', []), user_likes.get('likes_genres', []))
            common_albums = ParentUser.get_common_items(bud_likes.get('likes_albums', []), user_likes.get('likes_albums', []))

            bud_parent = await bud.parent.all()
            bud_parent_serialized = [await b.without_relations_serialize() for b in bud_parent]

            # Check if the bud is not empty
            if not bud_parent_serialized:
                continue  # Skip empty bud data

            # Add this bud's UID to the unique set
            unique_buds.add(bud.uid)

            buds_data.append({
                'bud': bud_parent_serialized,
                'commonArtistsCount': len(common_artists),
                'commonTracksCount': len(common_tracks),
                'commonGenresCount': len(common_genres),
                'commonAlbumsCount': len(common_albums),
                'commonArtists': [await artist.serialize() for artist in common_artists],
                'commonTracks': [await track.serialize() for track in common_tracks],
                'commonGenres': [await genre.serialize() for genre in common_genres],
                'commonAlbums': [await album.serialize() for album in common_albums]
            })

        logger.info(f'Data preparation complete. Total unique buds data prepared: {len(buds_data)}')
        return buds_data
