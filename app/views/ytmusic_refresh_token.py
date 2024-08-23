from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..middlewares.custom_token_auth import CustomTokenAuthentication
from django.http import JsonResponse

from app.services.service_selector import get_service

import logging
logger = logging.getLogger(__name__)

class YtmusicRefreshToken(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(YtmusicRefreshToken, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            service = 'ytmusic'
            user = request.user  
            tokens = get_service(service).refresh_token(user)
            user.update_ytmusic_tokens(user,tokens)

            return JsonResponse({
                'message': 'refreshed successfully.',
                'code': 200,
                'status': 'HTTP OK',
                'data': {
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'expires_at': tokens['expires_at'],
                    'expires_in': tokens['expires_in']

                }
            })
        except Exception as e:
            error_type = type(e).__name__
            print(e)
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)
