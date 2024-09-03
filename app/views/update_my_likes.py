from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app.services.service_selector import get_service_instance
from app.middlewares.custom_token_auth import CustomTokenAuthentication
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class UpdateMyLikes(APIView):
    authentication_classes = [CustomTokenAuthentication]

    async def post(self, request):
        try:
            parent_user = request.user
            service = request.data.get('service')
            
            if not parent_user or not service:
                return JsonResponse({'error': 'User or service not provided'}, status=400)

            service_instance = get_service_instance(service)
            if not service_instance:
                return JsonResponse({'error': 'Invalid service'}, status=400)

            user_likes = await service_instance.get_user_likes(parent_user)
            await service_instance.save_user_likes(parent_user, user_likes)

            return JsonResponse({'message': 'Likes updated successfully'}, status=200)
        except ValueError as ve:
            logger.error(f"Error updating likes for user: {parent_user.uid} on service: {service}: {str(ve)}")
            return JsonResponse({'error': str(ve)}, status=400)
        except Exception as e:
            logger.error(f"Error updating likes for user: {parent_user.uid} on service: {service}: {str(e)}")
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

