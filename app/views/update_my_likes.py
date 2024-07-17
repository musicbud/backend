from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication
from app.services.ServiceSelector import get_service

import logging
logger = logging.getLogger(__name__)


class update_my_likes(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @csrf_exempt
    def post(self, request):
        try:
            user = request.user
            service = user.service
            return JsonResponse({'data':get_service(service).save_user_likes(user)})
            return JsonResponse({'message': 'Updated Likes successfully'}, status=200)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)