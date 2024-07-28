from datetime import datetime
from adrf.views import APIView
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from app.forms.registeration import RegistrationForm,LoginForm
from app.db_models.Parent_User import ParentUser
from neomodel.exceptions import UniqueProperty
import logging


logger = logging.getLogger('app')

class Register(APIView):
    permission_classes = [AllowAny]

    async def post(self, request):
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            photo = form.cleaned_data['photo']

            try:
                # Check if username already exists
                existing_user = await ParentUser.nodes.filter(username=username)
                if existing_user:
                    logger.warning(f"Username already exists: {username}")
                    return JsonResponse({'error': 'Username already exists.'}, status=400)

                # Check if email already exists
                existing_email = await ParentUser.nodes.filter(email=email)
                if existing_email:
                    logger.warning(f"Email already exists: {email}")
                    return JsonResponse({'error': 'Email already exists.'}, status=400)

                hashed_password = make_password(password)

                # Handle photo upload
                photo_url = None
                if photo:
                    fs = FileSystemStorage()
                    filename = fs.save(photo.name, photo)
                    photo_url = fs.url(filename)

                # Save user asynchronously
                user = ParentUser(
                    username=username,
                    email=email,
                    password=hashed_password,
                    photo_url=photo_url
                )
                await user.save()  # Ensure `save` is async if using async ORM methods

                # Generate tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                 # Extract token expiration times
                access_token_expires_at = datetime.fromtimestamp(refresh.access_token.payload['exp'])
                refresh_token_expires_at = datetime.fromtimestamp(refresh.payload['exp'])

                # Save tokens to the user
                user.access_token = access_token
                user.refresh_token = refresh_token
                user.access_token_expires_at = access_token_expires_at.timestamp()
                user.refresh_token_expires_at = refresh_token_expires_at.timestamp()
                user.is_active = True

                await user.save()  # Ensure tokens are saved


                logger.debug(f"User registered successfully: {username}")
                return JsonResponse({
                    'message': 'Registration successful. Please log in.',
                    'data': {
                        'refresh_token': refresh_token,
                        'access_token': access_token,
                    }
                }, status=201)

            except UniqueProperty:
                logger.warning(f"Username or email already exists: {username}, {email}")
                return JsonResponse({'error': 'Username or email already exists.'}, status=400)
            except Exception as e:
                logger.error(f"Unexpected error during registration: {str(e)}")
                return JsonResponse({'error': 'Unexpected error occurred.'}, status=500)
        else:
            logger.warning(f"Invalid registration data: {form.errors}")
            return JsonResponse({'error': 'Invalid data.', 'details': form.errors}, status=400)

class Login(APIView):
    permission_classes = [AllowAny]

    async def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                user = await ParentUser.nodes.get(username=username)
                if check_password(password, user.password):
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)

                     # Extract token expiration times
                    access_token_expires_at = datetime.fromtimestamp(refresh.access_token.payload['exp'])
                    refresh_token_expires_at = datetime.fromtimestamp(refresh.payload['exp'])

                     # Save tokens to the user
                    user.access_token = access_token
                    user.refresh_token = refresh_token
                    user.access_token_expires_at = access_token_expires_at.timestamp()
                    user.refresh_token_expires_at = refresh_token_expires_at.timestamp()
                    user.is_active = True
                    await user.save()  # Ensure tokens are saved

                    logger.debug(f"User logged in successfully: {username}")
                    return JsonResponse({
                        'message':'Logged in successfully.',
                        'data':
                        {
                            'refresh_token': str(refresh_token),
                            'access_token': str(access_token),
                        }
                    })
                else:
                    logger.warning(f"Invalid login attempt for username: {username}")
                    return JsonResponse({'error': 'Invalid username or password.'}, status=400)
            except ParentUser.DoesNotExist:
                logger.warning(f"User does not exist: {username}")
                return JsonResponse({'error': 'Invalid username or password.'}, status=400)
        else:
            logger.warning(f"Invalid login data: {form.errors}")
            return JsonResponse({'error': 'Invalid data.', 'details': form.errors}, status=400)

        logger.warning("Invalid login request method")
        return JsonResponse({'error': 'Invalid request method.'}, status=405)


class Logout(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            logger.debug(f"User logged out successfully: {request.user}")
            return JsonResponse({'message': 'Logged out successfully.'}, status=200)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return JsonResponse({'error': 'Logout failed.'}, status=400)
