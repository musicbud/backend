import logging
from neomodel import (AsyncStructuredNode, BooleanProperty, StringProperty, UniqueIdProperty,
                      AsyncRelationshipTo, AsyncRelationshipFrom)

logger = logging.getLogger('app')  # Make sure to configure logging in your Django settings

class ParentUser(AsyncStructuredNode):
    uid = UniqueIdProperty()
    username = StringProperty(unique_index=True, required=True)
    email = StringProperty(unique_index=True, required=True)
    password = StringProperty(required=True)
    photo_url = StringProperty()
    bio = StringProperty()
    display_name = StringProperty(min_length=1, max_length=255)
    is_active = BooleanProperty()
    is_authenticated = BooleanProperty()
    access_token = StringProperty()
    refresh_token = StringProperty()
    access_token_expires_at = StringProperty()
    refresh_token_expires_at = StringProperty()

    spotify_account = AsyncRelationshipTo('.User.User', 'CONNECTED_TO_SPOTIFY')
    ytmusic_account = AsyncRelationshipTo('.User.User', 'CONNECTED_TO_YTMUSIC')
    lastfm_account = AsyncRelationshipTo('.User.User', 'CONNECTED_TO_LASTFM')
    
    async def associated_accounts(self):
        return {
            'spotify_account': await self.spotify_account.get_or_none(),
            'ytmusic_account': await self.ytmusic_account.get_or_none(),
            'lastfm_account': await self.lastfm_account.get_or_none() 
        }
    
    @staticmethod
    def get_common_items(user_items, bud_items):
        # Handle potential None values
        if user_items is None:
            user_items = []
        if bud_items is None:
            bud_items = []

        # Extract IDs from user_items and bud_items
        user_ids = set(item.id if hasattr(item, 'id') else item for item in user_items)  # Use item directly if it's a string
        bud_ids = set(item.id if hasattr(item, 'id') else item for item in bud_items)  # Use item directly if it's a string

        # Find common IDs
        common_ids = user_ids.intersection(bud_ids)

        # Retrieve common items from bud_items
        common_items = [item for item in bud_items if (item.id if hasattr(item, 'id') else item) in common_ids]

        return common_items
        
    async def serialize(self):
        # Fetch connected accounts
        spotify_accounts = await self.spotify_account.all()
        ytmusic_accounts = await self.ytmusic_account.all()
        lastfm_accounts = await self.lastfm_account.all()


        return {
            'uid': self.uid,
            'username': self.username,
            'email': self.email,
            'photo_url': self.photo_url,
            'bio': self.bio,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'is_authenticated': self.is_authenticated,
            'spotify_account': [await account.serialize() for account in spotify_accounts] if spotify_accounts else None,
            'ytmusic_account': [await account.serialize() for account in ytmusic_accounts] if ytmusic_accounts else None,
            'lastfm_account': [await account.serialize() for account in lastfm_accounts] if lastfm_accounts else None,
        }
    
    async def without_relations_serialize(self):
        # Fetch connected accounts
        

        return {
            'uid': self.uid,
            'username': self.username,
            'email': self.email,
            'photo_url': self.photo_url,
            'bio': self.bio,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'is_authenticated': self.is_authenticated,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'access_token_expires_at': self.access_token_expires_at,
            'refresh_token_expires_at': self.refresh_token_expires_at,
            
        }

    async def add_spotify_account(self, user):
        logger.info(f"Connecting Spotify account for user: {self.username}")
        await self.spotify_account.connect(user)
        logger.info(f"Connected Spotify account for user: {self.username}")

    async def add_ytmusic_account(self, user):
        logger.info(f"Connecting YouTube Music account for user: {self.username}")
        await self.ytmusic_account.connect(user)
        logger.info(f"Connected YouTube Music account for user: {self.username}")

    async def add_lastfm_account(self, user):
        logger.info(f"Connecting Last.fm account for user: {self.username}")
        await self.lastfm_account.connect(user)
        logger.info(f"Connected Last.fm account for user: {self.username}")

    async def remove_spotify_account(self, user):
        logger.info(f"Disconnecting Spotify account for user: {self.username}")
        await self.spotify_account.disconnect(user)
        logger.info(f"Disconnected Spotify account for user: {self.username}")

    async def remove_ytmusic_account(self, user):
        logger.info(f"Disconnecting YouTube Music account for user: {self.username}")
        await self.ytmusic_account.disconnect(user)
        logger.info(f"Disconnected YouTube Music account for user: {self.username}")

    async def remove_lastfm_account(self, user):
        logger.info(f"Disconnecting Last.fm account for user: {self.username}")
        await self.lastfm_account.disconnect(user)
        logger.info(f"Disconnected Last.fm account for user: {self.username}")
