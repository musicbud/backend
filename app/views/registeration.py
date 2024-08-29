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
from neomodel.exceptions import UniqueProperty, DoesNotExist
import logging
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views import View
import json
from django.contrib.auth.models import User  # Add this import
from django.urls import reverse

logger = logging.getLogger('app')

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home page after successful login
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

class Register(View):
    template_name = 'register.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, self.template_name, {'error': 'Passwords do not match'})

        try:
            existing_user = ParentUser.nodes.get(username=username)
            return render(request, self.template_name, {'error': 'Username already exists'})
        except DoesNotExist:
            pass

        try:
            existing_email = ParentUser.nodes.get(email=email)
            return render(request, self.template_name, {'error': 'Email already exists'})
        except DoesNotExist:
            pass

        try:
            hashed_password = make_password(password)
            user = ParentUser(username=username, email=email, password=hashed_password).save()
            return redirect(reverse('login'))
        except Exception as e:
            return render(request, self.template_name, {'error': str(e)})

class Logout(View):
    def get(self, request):
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'}, status=200)

class Login(View):
    template_name = 'login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Change 'home' to your desired redirect URL
        else:
            return render(request, self.template_name, {'error': 'Invalid credentials'})
