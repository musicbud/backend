class SpotifyService:
    def __init__(self, spotify_api):
        self.spotify_api = spotify_api

    async def get_user_top_artists_and_tracks(self):
        user_top_artists_items = await self.spotify_api.get_my_top_artists(time_range="long_term")
        user_top_artists = [item.id for item in user_top_artists_items.body.items]

        user_top_tracks_items = await self.spotify_api.get_my_top_tracks(time_range="long_term")
        user_top_tracks = [item.id for item in user_top_tracks_items.body.items]
       
        return user_top_artists,user_top_tracks
    

    
    