from django.http import JsonResponse
from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage


from ..forms.set_my_profile import SetMyProfileForm
from ..middlewares.custom_token_auth import CustomTokenAuthentication

import logging
logger = logging.getLogger(__name__)


class SetMyProfile(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(SetMyProfile, self).dispatch(*args, **kwargs)
    
    def post(self, request):
        form = SetMyProfileForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                user = request.user
                bio = form.cleaned_data.get('bio')
                display_name = form.cleaned_data.get('display_name')
                photo = form.cleaned_data.get('photo')

                if bio is not None:
                    user.bio = bio

                if display_name is not None:
                    user.display_name = display_name

                if photo:
                    # Handle photo upload
                    fs = FileSystemStorage()
                    filename = fs.save(photo.name, photo)
                    photo_url = fs.url(filename)
                    user.photo_url = photo_url

                user.save()

                return JsonResponse({
                    'message': 'Profile updated successfully.',
                    'code': 200,
                    'status': 'HTTP OK',
                })
            except Exception as e:
                logger.error(e)
                return JsonResponse({'error': 'Internal Server Error'}, status=500)
        else:
            return JsonResponse({
                'error': 'Invalid data.',
                'details': form.errors
            }, status=400)
