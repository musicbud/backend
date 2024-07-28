import logging
import time
from functools import wraps
from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger('app')

def service_token_getter(view_func):
    @wraps(view_func)
    async def _wrapped_view(self, request, *args, **kwargs):

        service = request.data.get('service') if hasattr(request, 'data') else request.POST.get('service')

        if not service:
            logger.error('Service not specified.')
            return JsonResponse({'error': 'Service not specified.'}, status=400)

        parent_user = request.parent_user
        if not parent_user:
            logger.error('User not authenticated.')
            return JsonResponse({'error': 'User not authenticated.'}, status=401)
        service_account = parent_user.associated_accounts.get(f"{service}_account", None)
        if not service_account:
            logger.error(f'No account associated with the service: {service}')
            return JsonResponse({'error': f'No account associated with the service: {service}'}, status=401)

        expires_at = service_account.expires_at
        if not expires_at:
            logger.warning('Token expiration time not provided.')
            return JsonResponse({'error': 'Token expiration time not provided.'}, status=401)

        current_time = time.time()
        if current_time >= float(expires_at):
            logger.error(f'{service} Access token expired.')
            return JsonResponse({'error': f'{service} Access token expired.'}, status=401)

        request.service= service
        request.service_account = service_account
        logger.info(f"Authenticated service account for service: {service}")

        return await view_func(self, request, *args, **kwargs)

    return _wrapped_view
