from django.urls import path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter  # Import DefaultRouter
from .views.auth import (
    not_found_view,
    error_view,
    login,
    spotify_callback,
    ytmusic_callback,
    lastfm_callback
)
from .views.spotify_refresh_token import spotify_refresh_token
from .views.ytmusic_refresh_token import ytmusic_refresh_token
from .views.update_my_likes import update_my_likes
from .views.set_my_bio import set_my_bio
from .views.get_my_profile import get_my_profile
from .views.get_bud_profile import get_bud_profile
from .views.get_buds_by_liked_artists import get_buds_by_liked_artists
from .views.get_buds_by_liked_tracks import get_buds_by_liked_tracks
from .views.get_buds_by_liked_genres import get_buds_by_liked_genres
from .views.get_buds_by_liked_albums import get_buds_by_liked_albums
from .views.get_buds_by_liked_aio import get_buds_by_liked_aio
from .views.get_buds_by_top_artists import get_buds_by_top_artists
from .views.get_buds_by_top_tracks import get_buds_by_top_tracks
from .views.get_buds_by_top_genres import get_buds_by_top_genres
from .views.get_buds_by_played_tracks import get_buds_by_played_tracks
from .views.get_buds_by_artist import get_buds_by_artist
from .views.get_buds_by_track import get_buds_by_track
from .views.get_buds_by_genre import get_buds_by_genre


from .views.search_users import search_users

from .seeders.spotify.create_user_seed import create_user_seed

router = DefaultRouter()

urlpatterns = [
    path('login', login, name='login'),
    path('spotify/callback', spotify_callback, name='spotify_callback'),
    path('ytmusic/callback', ytmusic_callback, name='ytmusic_callback'),
    path('lastfm/callback', lastfm_callback, name='lastfm_callback'),
    
    path('ytmusic/refresh-token', ytmusic_refresh_token.as_view(), name='ytmusic_refresh_token'),
    path('spotify/refresh-token', spotify_refresh_token.as_view(), name='spotify_refresh_token'),
    
    path('me/update-likes', update_my_likes.as_view(), name='update_my_likes'),
    path('me/profile', get_my_profile.as_view(), name='get_my_profile'),
    path('me/bio', set_my_bio.as_view(), name='set_my_bio'),
    
    path('bud/profile', get_bud_profile.as_view(), name='get_bud_profile'), 
    path('bud/liked-artists', get_buds_by_liked_artists.as_view(), name='get_buds_by_liked_artists'),
    path('bud/liked-tracks', get_buds_by_liked_tracks.as_view(), name='get_buds_by_liked_tracks'),
    path('bud/liked-genres', get_buds_by_liked_genres.as_view(), name='get_buds_by_liked_genres'),
    path('bud/liked-albums', get_buds_by_liked_albums.as_view(), name='get_buds_by_liked_albums'),
    path('bud/liked-aio', get_buds_by_liked_aio.as_view(), name='get_buds_by_liked_aio'),
    path('bud/top-artists', get_buds_by_top_artists.as_view(), name='get_buds_by_top_artists'),
    path('bud/top-tracks', get_buds_by_top_tracks.as_view(), name='get_buds_by_top_tracks'),
    path('bud/top-genres', get_buds_by_top_genres.as_view(), name='get_buds_by_top_genres'),
    path('bud/played-tracks', get_buds_by_played_tracks.as_view(), name='get_buds_by_played_tracks'),
    path('bud/artist', get_buds_by_artist.as_view(), name='get_buds_by_artist'),
    path('bud/track', get_buds_by_track.as_view(), name='get_buds_by_track'),
    path('bud/genre', get_buds_by_genre.as_view(), name='get_buds_by_genre'),

    path('search/channels-users', search_users.as_view(), name='search_channels_and_users'),
    
    path('spotify/create-user-seed', create_user_seed, name='create_user_seed'),
]





# Add error handling views
handler404 = not_found_view
handler500 = error_view

