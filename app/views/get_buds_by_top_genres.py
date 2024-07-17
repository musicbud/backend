from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..db_models.User import User
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication

import logging
logger = logging.getLogger(__name__)

class get_buds_by_top_genres(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_top_genres, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user_node = request.user
            user_id = request.user.uid

            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)

            top_genres = user_node.top_genres.all()

            buds = []
            for genre in top_genres:
                buds.extend(genre.users.all())
            # Filter out the user and duplicates
            buds = list({bud.uid: bud for bud in buds if bud.uid != user_id}.values())

            buds_data = []
            total_common_genres_count = 0

            for bud in buds:
                bud_liked_genre_uids = [genre.uid for genre in bud.top_genres.all()]
                common_genres = user_node.top_genres.filter(uid__in=bud_liked_genre_uids)
                common_genres_count = len(common_genres)
                total_common_genres_count += common_genres_count

                buds_data.append({
                    'bud_uid': bud.uid,
                    'common_genres_count': common_genres_count,
                    'common_genres': [genre.serialize() for genre in common_genres]
                })

            return JsonResponse({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'data': {
                    'buds': buds_data,
                    'totalCommonGenresCount': total_common_genres_count,
                }
            })
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)