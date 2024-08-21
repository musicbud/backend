from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from app.services.recommendation_service import get_recommendations, save_recommendations
from app.middlewares.custom_token_auth import CustomTokenAuthentication
from adrf.views import APIView
from rest_framework.permissions import AllowAny

@require_http_methods(["GET"])


class Login(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    async def update_user_recommendations(request, user_id):
        try:
            recommendations = await get_recommendations(user_id)
            await save_recommendations(user_id, recommendations)
            return JsonResponse({'status': 'success', 'recommendations': recommendations})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
