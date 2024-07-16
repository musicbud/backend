from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.exceptions import PermissionDenied
from django.http import JsonResponse

from app.services.ServiceSelector import get_service
from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication

import logging
logger = logging.getLogger(__name__)

class get_my_profile(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(get_my_profile, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        user = request.user
        user_profile = user.get_profile(user);

        return JsonResponse({
            'message': 'fetched user profile successfully',
            'data':user_profile
            }, status=200)
