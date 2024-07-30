from datetime import datetime
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
import time
import logging
from app.db_models.Parent_User import ParentUser

# Set up logging
logger = logging.getLogger('app')

class CustomTokenAuthentication(TokenAuthentication):

    async def authenticate(self, request):
        auth = request.headers.get('Authorization')
        if auth and auth.startswith('Bearer '):
            auth = auth.split('Bearer ')[1]
        if not auth:
            logger.warning('No authorization token provided')
            return None
        
        logger.debug('Authenticating token')
        try:
            parent_user, token_string = await self.authenticate_credentials(auth)
            request.parent_user = parent_user
            logger.info('Authentication successful')
            return parent_user, token_string
        except AuthenticationFailed as e:
            logger.error(f'Authentication failed: {str(e)}')
            raise

    async def authenticate_credentials(self, token):
        token_string = token.decode('utf-8') if isinstance(token, bytes) else token
        logger.debug(f'Authenticating credentials with token: {token_string}')
        
        try:
            parent_user = await ParentUser.nodes.get_or_none(access_token=token_string)
            if parent_user:
                logger.debug(f'ParentUser found: {parent_user}')
            else:
                logger.warning('ParentUser not found for token')
        except Exception as e:
            logger.error(f'Error retrieving parent_user: {str(e)}')
            raise AuthenticationFailed(f'Error retrieving parent_user: {str(e)}')
        
        if parent_user is None:
            raise AuthenticationFailed('Invalid token.')
        if not parent_user.is_active:
            raise AuthenticationFailed('User inactive or deleted.')

        # Check if token is expired
        if self.is_token_expired(parent_user.access_token_expires_at):
            logger.warning('Parent User access token expired')
            raise AuthenticationFailed('Parent User Access token expired.')

        parent_user.is_authenticated = True
        await parent_user.save()  # Save user changes asynchronously
        logger.debug('ParentUser saved with is_authenticated set to True')

        # Fetch associated accounts
        associated_accounts = {}
        if parent_user:
            logger.debug('Fetching associated accounts')
            associated_accounts = {
            'spotify_account': (await parent_user.spotify_account.all())[0] if await parent_user.spotify_account.all() else None,
            'ytmusic_account': (await parent_user.ytmusic_account.all())[0] if await parent_user.ytmusic_account.all() else None,
            'lastfm_account': (await parent_user.lastfm_account.all())[0] if await parent_user.lastfm_account.all() else None,
            'mal_account': (await parent_user.mal_account.all())[0] if await parent_user.mal_account.all() else None
            }
            logger.debug(f'Associated accounts: {associated_accounts}')
        parent_user.associated_accounts = associated_accounts
        return parent_user, token_string
    
    def is_token_expired(self, expires_at):
        if not expires_at:
            return True
                
        current_time = time.time()
        expired = current_time >= float(expires_at)
        if expired:
            logger.debug('Token is expired')
        return expired
