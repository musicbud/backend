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
    path('get-buds-by-liked-artists', get_buds_by_liked_artists.as_view(), name='get_buds_by_liked_artists'),
    path('get-buds-by-liked-tracks', get_buds_by_liked_tracks.as_view(), name='get_buds_by_liked_tracks'),
    path('get-buds-by-liked-genres', get_buds_by_liked_genres.as_view(), name='get_buds_by_liked_genres'),
    path('get-buds-by-liked-albums', get_buds_by_liked_albums.as_view(), name='get_buds_by_liked_albums'),
    path('get-buds-by-liked-aio', get_buds_by_liked_aio.as_view(), name='get_buds_by_liked_aio'),
    path('get-buds-by-top-artists', get_buds_by_top_artists.as_view(), name='get_buds_by_top_artists'),
    path('get-buds-by-top-tracks', get_buds_by_top_tracks.as_view(), name='get_buds_by_top_tracks'),
    path('get-buds-by-top-genres', get_buds_by_top_genres.as_view(), name='get_buds_by_top_genres'),
    path('get-buds-by-played-tracks', get_buds_by_played_tracks.as_view(), name='get_buds_by_played_tracks'),
    path('get-buds-by-artist', get_buds_by_artist.as_view(), name='get_buds_by_artist'),
    path('get-buds-by-track', get_buds_by_track.as_view(), name='get_buds_by_track'),
    path('get-buds-by-genre', get_buds_by_genre.as_view(), name='get_buds_by_genre'),

    path('search-channels-and-users', search_users.as_view(), name='search_channels_and_users'),
    path('docs/', TemplateView.as_view(template_name="index.html")),
    # seeders
    path('spotify/create-user-seed', create_user_seed, name='create_user_seed'),


]


# Add error handling views
handler404 = not_found_view
handler500 = error_view

