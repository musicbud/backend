from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.User import User
from ..db_models.Genre import Genre
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging

logger = logging.getLogger('app')

class get_buds_by_genre(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    async def dispatch(self, *args, **kwargs):
        return await super(get_buds_by_genre, self).dispatch(*args, **kwargs)

    async def post(self, request):
        try:
            user = request.user
            genre_id = request.data.get('genre_id')

            if not genre_id:
                return JsonResponse({'error': 'Genre ID not provided'}, status=400)

            account_ids = [account.uid for account in user.associated_accounts.values() if account]  # Use a list for account UIDs

            # Await the call to get the genre node
            genre_node = await Genre.nodes.get_or_none(uid=genre_id)

            if not genre_node:
                return JsonResponse({'error': 'Genre not found'}, status=404)

            # Get users who liked the specified genre, excluding the current user's accounts
            genre_users = await genre_node.users.exclude(uid__in=account_ids).all()

            buds_data = {}
            unique_bud_uids = set()  # Set to track unique bud UIDs

            for bud in genre_users:
                bud_uid = bud.uid
                if bud_uid in unique_bud_uids:
                    continue  # Skip already processed bud

                unique_bud_uids.add(bud_uid)  # Mark this bud as processed

                bud_liked_genre_uids = [genre.uid for genre in await bud.likes_genres.all()]  # Use list for UIDs
                for account in user.associated_accounts.values():
                    if account:
                        common_genres = await account.likes_genres.filter(uid__in=bud_liked_genre_uids).all()
                        common_genres_count = len(common_genres)

                        # Get the parent and serialize it
                        bud_parent = await bud.parent.all()
                        for parent in bud_parent:
                            parent_uid = parent.uid
                            parent_serialized = await parent.without_relations_serialize()

                            if parent_uid not in buds_data:
                                buds_data[parent_uid] = {
                                    'bud': parent_serialized,
                                    'common_genres_count': 0,
                                    'common_genres': []
                                }

                            # Update the aggregated data
                            buds_data[parent_uid]['common_genres_count'] += common_genres_count
                            buds_data[parent_uid]['common_genres'].extend([await genre.serialize() for genre in common_genres])

            # Convert the aggregated data to a list
            aggregated_buds_data = list(buds_data.values())

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(aggregated_buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })

            logger.info(f'Successfully fetched buds by genre for user: uid={user.uid}, genre_id={genre_id}')
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(f'Error in GetBudsByGenre: {e}', exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)