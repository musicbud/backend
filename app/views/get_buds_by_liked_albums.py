from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.User import User
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..pagination import StandardResultsSetPagination

import logging
logger = logging.getLogger(__name__)

class get_buds_by_liked_albums(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_liked_albums, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user_node = request.user
            user_id = request.user.uid

            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)

            liked_albums = user_node.likes_albums.all()

            buds = []
            for album in liked_albums:
                buds.extend(album.users.all())

            # Filter out the user and duplicates
            buds = list({bud.uid: bud for bud in buds if bud.uid != user_id}.values())

            buds_data = []
            total_common_albums_count = 0

            for bud in buds:
                bud_liked_album_uids = [album.uid for album in bud.likes_albums.all()]
                common_albums = user_node.likes_albums.filter(uid__in=bud_liked_album_uids)
                common_albums_count = len(common_albums)
                total_common_albums_count += common_albums_count

                buds_data.append({
                    'bud_uid': bud.uid,
                    'common_albums_count': common_albums_count,
                    'common_albums': [album.serialize() for album in common_albums]
                })

            paginator = StandardResultsSetPagination()
            paginated_buds = paginator.paginate_queryset(buds_data, request)

            paginated_response = paginator.get_paginated_response(paginated_buds)
            paginated_response.update({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
            })
            return JsonResponse(paginated_response)

        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
