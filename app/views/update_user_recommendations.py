from django.http import JsonResponse
from app.services.recommendation_service import get_recommendations
from app.db_models import ParentUser as User
from app.middlewares.custom_token_auth import CustomTokenAuthentication
from adrf.views import APIView
from rest_framework.permissions import AllowAny

class UpdateUserRecommendations(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    async def get(self, request, user_id):
        # try:
        #     recommendations = await get_recommendations(user_id)
        #     await save_recommendations(user_id, recommendations)
        #     return JsonResponse({'status': 'success', 'recommendations': recommendations})
        # except Exception as e:
        #     error_type = type(e).__name__
        #     return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)
        pass