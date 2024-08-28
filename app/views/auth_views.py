from django.contrib.auth import authenticate, login, get_user_model
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from app.forms.registeration import LoginForm
from django.contrib.auth.models import User  # Import User model
from app.views.registeration import Login  # Import Login from registeration.py
import logging
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger('app')

from django.views.decorators.csrf import ensure_csrf_cookie

from django.views.decorators.csrf import csrf_exempt

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login
import logging

logger = logging.getLogger('app')

from django.contrib.auth.hashers import check_password

from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.hashers import check_password

User = get_user_model()

@csrf_exempt
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, 'login.html', {'form': form})
    
    logger.info(f"Received login request. Method: {request.method}")
    logger.info(f"Request POST data: {request.POST}")
    
    form = LoginForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        
        logger.info(f"Login attempt for username: {username}")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            logger.info(f"Successful login for username: {username}")
            return JsonResponse({'success': True, 'message': 'Login successful'})
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render(request, 'login.html', {'form': form, 'error': 'Invalid username or password'})
    else:
        logger.error(f"Login form validation failed. Errors: {form.errors}")
        return render(request, 'login.html', {'form': form, 'error': 'Invalid form submission'})

# Use the Login class from registeration.py
# You can add any additional methods or override existing ones if needed
class AuthLogin(Login):
    pass

# If you need to customize the post method, you can override it like this:
# 
# async def post(self, request):
#     # Custom logic here
#     return await super().post(request)

from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from app.forms.registeration import RegistrationForm
import logging

logger = logging.getLogger('app')
User = get_user_model()

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
