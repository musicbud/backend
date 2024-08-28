from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from app.forms.registeration import LoginForm
from app.views.registeration import Login  # Import Login from registeration.py
import logging

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

# Use the Login class from registeration.py
# You can add any additional methods or override existing ones if needed
class AuthLogin(Login):
    pass

# If you need to customize the post method, you can override it like this:
# 
# async def post(self, request):
#     # Custom logic here
#     return await super().post(request)
