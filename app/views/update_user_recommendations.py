from django.http import JsonResponse
from app.services.recommendation_service import get_recommendations
from app.db_models import ParentUser as User
from app.middlewares.async_jwt_authentication import AsyncJWTAuthentication
from adrf.views import APIView
from rest_framework.permissions import AllowAny

class UpdateUserRecommendations(APIView):
    authentication_classes = [AsyncJWTAuthentication]
    permission_classes = [AllowAny]

    async def get(self, request, user_id):
        auth_result = await self.authentication_classes[0]().authenticate_async(request)
        if auth_result is None:
            return JsonResponse({'error': 'Authentication failed'}, status=401)
        
        user, _ = auth_result
        # Your existing logic here
        pass