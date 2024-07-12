from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from ..middlewares.CustomTokenAuthentication import CustomTokenAuthentication

import logging
logger = logging.getLogger(__name__)


class set_my_bio(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(set_my_bio, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            user = request.user
            bio = request.data.get('bio')

            if bio is None:
                return JsonResponse({
                    'error': 'Bio field is missing.',
                    'code': 400
                }, status=400)

            # Set the bio property of the user
            user.bio = bio
            user.save()

            return JsonResponse({
                'message': 'Bio updated successfully.',
                'code': 200,
                'status': 'HTTP OK',
            })
        except Exception as e:
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

