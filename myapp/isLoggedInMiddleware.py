import time
from django.http import JsonResponse
from myapp.models import User  # Ensure your User model is correctly defined

def send_error_response(request, code, message):
    return JsonResponse({
        'defaultResponse': {
            'message': message,
            'code': code,
            'successful': False,
        }
    }, status=code)

def validate_access_token(access_token):
    user = User.nodes.get_or_none(access_token=access_token)
    return user

def is_token_expired(user):
    current_time = time.time()
    issue_time = user.token_issue_time  # Assuming you have a field to store the token issue time
    expires_in = user.expires_in  # Assuming you have a field to store the expiration duration

    # Calculate the expiration time by adding the issue time and expiration duration
    expiration_time = issue_time + expires_in

    return current_time >= expiration_time

def is_logged_in_middleware(get_response):
    def middleware(request):
        excluded_paths = ['/login', '/login/', '/', '/callback']
        if request.path_info in excluded_paths:
            return get_response(request)
        
        try:
            access_token = request.headers.get('Authorization')

            user = validate_access_token(access_token)
            if not user:
                return send_error_response(request, 401, "Invalid access token")

            if is_token_expired(user):
                return send_error_response(request, 401, "Access token expired")

            # Attach the user object to the request
            request.user = user

            # Proceed to the view function
            return get_response(request)

        except AttributeError as e:
            return send_error_response(request, 401, "Authorization header not found")

        except Exception as e:
            return send_error_response(request, 500, "Internal server error")

    return middleware
    