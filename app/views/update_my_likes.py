from typing import Any
from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..middlewares.custom_token_auth import CustomTokenAuthentication
from ..middlewares.service_token_getter import service_token_getter
from ..services.spotify_service import SpotifyService  # Ensure correct import path
from app.services.service_selector import get_service
import logging

logger = logging.getLogger('app')

class UpdateMyLikes(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @service_token_getter
    async def post(self, request: Any) -> JsonResponse:
        try:
            service = request.service
            user = request.service_account
            logger.info(f"User: {user.id} is updating likes for service: {service}")

            service_instance = get_service(service)
            
            if isinstance(service_instance, SpotifyService):
                # Clear existing likes before updating
                await service_instance.clear_user_likes(user)
                logger.info(f"Cleared existing likes successfully for user: {user.id} on service: {service}")

                # Save new likes
                await service_instance.save_user_likes(user)
                logger.info(f"Updated likes successfully for user: {user.id} on service: {service}")

                return JsonResponse({'message': 'Updated likes successfully'}, status=200)
            else:
                raise Exception("Invalid service instance.")
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error updating likes for user: {request.user.id} on service: {request.user}: {e}")
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)
