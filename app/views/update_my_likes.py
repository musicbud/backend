from typing import Any
from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from ..middlewares.ServiceTokenGetter import service_token_getter
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from app.services.ServiceSelector import get_service
import logging

logger = logging.getLogger('app')

class update_my_likes(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @service_token_getter
    async def post(self, request: Any) -> JsonResponse:
        try:
            service = request.service
            user = request.service_account
            logger.info(f"User: {user.id} is updating likes for service: {user}")
            service = user.service
            
            service_instance = get_service(service)
            await service_instance.save_user_likes(user)
            logger.info(f"Updated likes successfully for user: {user.id} on service: {service}")

            return JsonResponse({'message': 'Updated likes successfully'}, status=200)
        except Exception as e:
            logger.error(f"Error updating likes for user: {request.user.id} on service: {request.user}: {e}")
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
