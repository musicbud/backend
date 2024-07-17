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
from .views.get_buds_by_artists import get_buds_by_artists
from .views.get_buds_by_tracks import get_buds_by_tracks
from .views.get_buds_by_genres import get_buds_by_genres
from .views.get_buds_by_aio import get_buds_by_aio
from .views.search_users import search_users

from .seeders.spotify.create_user_seed import create_user_seed

router = DefaultRouter()

urlpatterns = [path('login', login, name='login'),
    path('spotify/callback', spotify_callback, name='spotify_callback'),
    path('ytmusic/callback', ytmusic_callback, name='ytmusic_callback'),
    path('lastfm/callback', lastfm_callback, name='lastfm_callback'),
    path('ytmusic/refresh-token', ytmusic_refresh_token.as_view(), name='ytmusic_refresh_token'),
    path('spotify/refresh-token', spotify_refresh_token.as_view(), name='spotify_refresh_token'),
    path('update-my-likes', update_my_likes.as_view(), name='update_my_likes'),
    path('get-my-profile', get_my_profile.as_view(), name='get_my_profile'),
    path('set-my-bio', set_my_bio.as_view(), name='set_my_bio'),
    path('get-bud-profile', get_bud_profile.as_view(), name='get_bud_profile'), 
    path('get-buds-by-artists', get_buds_by_artists.as_view(), name='get_buds_by_artist'),
    path('get-buds-by-tracks', get_buds_by_tracks.as_view(), name='get_buds_by_track'),
    path('get-buds-by-genres', get_buds_by_genres.as_view(), name='get_buds_by_genres'),
    path('get-buds-by-aio', get_buds_by_aio.as_view(), name='get_buds_by_aio'),
    path('search-channels-and-users', search_users.as_view(), name='search_channels_and_users'),
    path('docs/', TemplateView.as_view(template_name="index.html")),
    # seeders
    path('spotify/create-user-seed', create_user_seed, name='create_user_seed'),


]


# Add error handling views
handler404 = not_found_view
handler500 = error_view

