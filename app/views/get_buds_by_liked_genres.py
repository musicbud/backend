from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from ..db_models.User import User
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication

import logging
logger = logging.getLogger(__name__)

class get_buds_by_liked_genres(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_buds_by_liked_genres, self).dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user = request.user
            user_id = request.user.uid
            user_node = User.nodes.get_or_none(uid=user_id)
            
            if not user_node:
                return JsonResponse({'error': 'User not found'}, status=404)

            buds = []
            for genre in user_node.likes_genres.all():
                buds.extend(genre.users.all())

            # Filter out the user and duplicates
            buds = list({bud.uid: bud for bud in buds if bud.uid != user_id}.values())

            buds_data = []
            genre_ids = []

            for bud in buds:
                bud_liked_genre_uids = [genre.uid for genre in bud.likes_genres.all()]
                common_genres = user_node.likes_genres.filter(uid__in=bud_liked_genre_uids)
                common_genres_count = len(common_genres)
                genre_ids.extend([genre.uid for genre in common_genres])

                bud_data = {
                    'uid': bud.uid,
                    'email': bud.email,
                    'country': bud.country,
                    'display_name': bud.display_name,
                    'bio': bud.bio,
                    'is_active': bud.is_active,
                    'is_authenticated': bud.is_authenticated,
                    'commonGenres': [genre.serialize() for genre in common_genres],
                    'commonGenresCount': common_genres_count
                }
                buds_data.append(bud_data)


            # Update buds_data with additional genre information if fetched
            # for bud in buds_data:
            #     bud['commonGenres'] = [genre for genre in common_genres_data if genre['id'] in genre_ids]

            return JsonResponse({
                'message': 'Fetched buds successfully.',
                'code': 200,
                'successful': True,
                'data': {
                    'buds': buds_data,
                    'totalCommonGenresCount': sum(bud['commonGenresCount'] for bud in buds_data)
                }
            })
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)