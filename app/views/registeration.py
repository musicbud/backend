from datetime import datetime
from adrf.views import APIView
from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from app.forms.registeration import RegistrationForm, LoginForm
from app.db_models.parent_user import ParentUser
from neomodel.exceptions import UniqueProperty
import logging
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views import View
import json

logger = logging.getLogger('app')

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('user_list')  # Redirect to the chat user list after login
            else:
                return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

class Register(APIView):
    permission_classes = [AllowAny]

    async def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        form = RegistrationForm(data)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            photo = request.FILES.get('photo')

            try:
                # Check if username already exists
                existing_user = await ParentUser.nodes.filter(username=username).first()
                if existing_user:
                    logger.warning(f"Username already exists: {username}")
                    return JsonResponse({'error': 'Username already exists.'}, status=400)

                # Check if email already exists
                existing_email = await ParentUser.nodes.filter(email=email).first()
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

                # Store user ID in the session
                await sync_to_async(request.session.__setitem__)('user_id', user.uid)

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
        else:
            logger.error(f"Form errors: {form.errors}")
        return JsonResponse({'error': 'Invalid form data'}, status=400)

class Logout(View):
    def get(self, request):
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'}, status=200)

class Login(APIView):
    permission_classes = [AllowAny]

    async def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'message': 'Login successful'}, status=200)
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=400)
        return JsonResponse({'error': 'Invalid form data'}, status=400)
