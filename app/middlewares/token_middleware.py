import logging
from django.http import JsonResponse
from spotipy.exceptions import SpotifyException
import json
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

class TokenMixin:
    async def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user and user.is_authenticated:
            parent_user = await self.get_parent_user(user.username)
            request.parent_user = parent_user
        else:
            request.parent_user = None

        if hasattr(request, 'parent_user') and request.parent_user:
            try:
                logger.debug("Calling check_and_refresh_tokens")
                await self.check_and_refresh_tokens(request)
            except ValueError as ve:
                logger.error(f"ValueError in check_and_refresh_tokens: {str(ve)}")
                return JsonResponse({'error': str(ve)}, status=400)
            except TokenExpiredError as tee:
                logger.error(f"TokenExpiredError in check_and_refresh_tokens: {str(tee)}")
                return JsonResponse({'error': str(tee)}, status=401)

        return await super().dispatch(request, *args, **kwargs)

    async def get_parent_user(self, username):
        from app.db_models.parent_user import ParentUser

        try:
            return await ParentUser.nodes.get(username=username)
        except ParentUser.DoesNotExist:
            return None

    async def check_and_refresh_tokens(self, request):
        from app.services.service_selector import get_service
        services = {
            'spotify': 'spotify',
            'ytmusic': 'ytmusic',
            'mal': 'mal',
            'lastfm': 'lastfm'
        }

        # Parse form data if content type is application/x-www-form-urlencoded
        if request.content_type == 'application/x-www-form-urlencoded':
            body_data = parse_qs(request.body.decode('utf-8'))
            body_data = {k: v[0] for k, v in body_data.items()}  # Convert lists to single values
        else:
            # Parse JSON body if present
            try:
                body_data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                body_data = {}

        service_name = body_data.get('service')
        if not service_name or service_name not in services:
            raise ValueError("Invalid or missing service name in request body")

        service = await get_service(service_name)

        try:
            # Retrieve the service user
            service_user = await service.get_service_user(request.parent_user)
            if not service_user:
                raise ValueError(f"No service user found for {service_name} service for user {request.parent_user.username}")

            # Get the access token from the service user
            token = service_user.access_token
            if not token:
                raise ValueError(f"No access token found for {service_name} service user {service_user.username}")

            # Check token validity and refresh if necessary
            try:
                await service.check_token_validity(service_user)
            except SpotifyException as se:
                if se.http_status == 401:
                    logger.info(f"{service_name.capitalize()} token expired for user {request.parent_user.username}. Refreshing token.")
                    try:
                        await service.refresh_access_token(service_user)
                    except Exception as refresh_exception:
                        logger.error(f"Failed to refresh {service_name} token: {str(refresh_exception)}")
                        authorize_url = await service.create_authorize_url()
                        return JsonResponse({'error': 'Token expired and could not be refreshed', 'authorize_url': authorize_url}, status=401)
                else:
                    raise

        except ValueError as ve:
            logger.error(f"{service_name.capitalize()} authentication error: {str(ve)}")
            raise
        except SpotifyException as se:
            if se.http_status == 401:
                logger.error(f"{service_name.capitalize()} token expired: {str(se)}")
                authorize_url = await service.create_authorize_url()
                return JsonResponse({'error': 'Token expired', 'authorize_url': authorize_url}, status=401)
            else:
                logger.error(f"Error checking {service_name} token: {str(se)}")
                raise ValueError(f"Error checking {service_name} token: {str(se)}")
        except Exception as e:
            logger.error(f"Error checking {service_name} token: {str(e)}")
            raise ValueError(f"Error checking {service_name} token: {str(e)}")

class TokenExpiredError(Exception):
    pass