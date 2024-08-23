from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from ..db_models.user import User
from ..middlewares.custom_token_auth import CustomTokenAuthentication
from ..forms.search_user import SearchUsersForm
import logging
logger = logging.getLogger(__name__)


class SearchUsers(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(SearchUsers, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            query = request.data.query
            users = User.nodes.filter(display_name__icontains=query)
            return JsonResponse({
                'message': 'Fetched search result successfully.',
                'code': 200,
                'successful': True,
                'collection': {'users': [user.serialize() for user in users]}
            }, status=200)
        except Exception as e:
            error_type = type(e).__name__
            logger.error(e)
            return JsonResponse({'error': 'Internal Server Error', 'type': error_type}, status=500)
