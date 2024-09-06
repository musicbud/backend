from datetime import datetime
from adrf.views import APIView
from asgiref.sync import sync_to_async, async_to_sync
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse, HttpResponse
from rest_framework.permissions import AllowAny
from app.forms.registeration import RegistrationForm, LoginForm
from app.db_models.parent_user import ParentUser
from neomodel.exceptions import UniqueProperty, DoesNotExist
import logging
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views import View
import json
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import asyncio
from app.neo4j_utils import update_neo4j_user_sync
from rest_framework.response import Response
from rest_framework import status   

logger = logging.getLogger('app')

@csrf_exempt
@method_decorator(csrf_exempt, name='dispatch')
class Login(APIView):
    permission_classes = [AllowAny]

    def options(self, request, *args, **kwargs):
        response = JsonResponse({'message': 'OK'})
        response['Access-Control-Allow-Origin'] = '*'  # Adjust this in production
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request):
        logger.info("Received POST request for login")
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            logger.debug(f"Login attempt for user: {username}")

            if not username or not password:
                logger.warning("Login attempt with missing username or password")
                return JsonResponse({'error': 'Username and password are required'}, status=400)

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                
                logger.info(f"User {username} logged in successfully")
                logger.debug(f"Refresh token: {str(refresh)}")
                logger.debug(f"Access token: {access_token}")
                
                response = JsonResponse({
                    'refresh': str(refresh),
                    'access': access_token,
                }, status=200)
                response['Access-Control-Allow-Origin'] = '*'  # Adjust this in production
                return response
            else:
                logger.warning(f"Failed login attempt for user: {username}")
                return JsonResponse({'error': 'Invalid credentials'}, status=401)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in login request")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in login: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
class Register(View):
    template_name = 'register.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        content_type = request.content_type
        if content_type == 'application/json':
            return self.handle_json_register(request)
        else:
            return self.handle_form_register(request)

    def handle_json_register(self, request):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if not username or not email or not password:
                return JsonResponse({'error': 'Username, email, and password are required'}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)
            elif User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Email already exists'}, status=400)
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                login(request, user)
                refresh = RefreshToken.for_user(user)
                return JsonResponse({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in registration: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Internal server error'}, status=500)

    def handle_form_register(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            error = 'Username already exists'
        elif User.objects.filter(email=email).exists():
            error = 'Email already exists'
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('home')  # Make sure you have a 'home' URL name defined

        return render(request, self.template_name, {'error': error})

