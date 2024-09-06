from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from app.forms.registeration import LoginForm, RegistrationForm
from django.contrib.auth.models import User
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import logging
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from app.middlewares.async_jwt_authentication import AsyncJWTAuthentication

logger = logging.getLogger('app')

@method_decorator(csrf_exempt, name='dispatch')
class AuthLogin(APIView):
    authentication_classes = [AsyncJWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        content_type = request.content_type.lower()

        if content_type == 'application/json':
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        elif content_type == 'application/x-www-form-urlencoded':
            username = request.POST.get('username')
            password = request.POST.get('password')
        else:
            return JsonResponse({
                "success": False,
                "message": "Unsupported content type"
            }, status=415)

        if not username or not password:
            return JsonResponse({
                "success": False,
                "message": "Both username and password are required"
            }, status=400)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                "success": True,
                "message": "Login successful",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh)
            })
        else:
            return JsonResponse({
                "success": False,
                "message": "Invalid credentials"
            }, status=401)

@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            if User.objects.filter(username=username).exists():
                return render(request, 'register.html', {'form': form, 'error': 'Username already exists'})
            
            if User.objects.filter(email=email).exists():
                return render(request, 'register.html', {'form': form, 'error': 'Email already exists'})
            
            user = User.objects.create_user(username=username, email=email, password=password)
            logger.info(f"New user registered: {username}")
            return redirect('login')
        else:
            logger.error(f"Registration form validation failed. Errors: {form.errors}")
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

@method_decorator(csrf_exempt, name='dispatch')
class Logout(View):
    def get(self, request):
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'}, status=200)

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            if request.content_type == 'application/x-www-form-urlencoded':
                username = request.POST.get('username')
                password = request.POST.get('password')
            elif request.content_type == 'application/json':
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
            else:
                return JsonResponse({
                    "success": False,
                    "message": "Unsupported content type"
                }, status=415)
            
            if not username or not password:
                return JsonResponse({
                    "success": False,
                    "message": "Both username and password are required"
                }, status=400)
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                refresh = RefreshToken.for_user(user)
                return JsonResponse({
                    "success": True,
                    "message": "Login successful",
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh)
                })
            else:
                return JsonResponse({
                    "success": False,
                    "message": "Invalid credentials"
                }, status=401)
        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "message": "Invalid JSON in request body"
            }, status=400)
    else:
        return JsonResponse({
            "success": False,
            "message": "Only POST method is allowed"
        }, status=405)

@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenView(APIView):
    def post(self, request):
        content_type = request.content_type.lower()

        if content_type == 'application/json':
            refresh_token = request.data.get('refresh_token')
        elif content_type == 'application/x-www-form-urlencoded':
            refresh_token = request.POST.get('refresh_token')
        else:
            return Response({
                'success': False,
                'message': 'Unsupported content type'
            }, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response({
                'success': True,
                'message': 'Token refresh successful',
                'access_token': access_token
            })
        except TokenError:
            return Response({
                'success': False,
                'message': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_likes(request):
    service = request.data.get('service')
    if not service:
        return Response({
            'success': False,
            'message': 'Service parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Here, implement the logic to update likes for the authenticated user
    # You can access the authenticated user with request.user
    user = request.user
    
    # Example: Update user's preferred service
    user.profile.preferred_service = service
    user.profile.save()

    return Response({
        'success': True,
        'message': f'Likes updated for service: {service}'
    })
