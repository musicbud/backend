from django.urls import path
from .views import (
    not_found_view,
    error_view,
    login, refresh_token, callback,
    update_my_likes, set_my_bio,
    get_my_profile, get_bud_profile,
    get_buds_by_artist,
    get_buds_by_track,
    get_buds_by_artist_and_track,
    search_channels_and_users_view
)
urlpatterns = [
    path('login', login, name='login'),
    path('refresh-token', refresh_token.as_view(), name='refresh_token'),
    path('callback', callback, name='callback'),
    path('update-my-likes', update_my_likes.as_view(), name='update_my_likes'),
    path('set-my-bio', set_my_bio, name='set_my_bio'),
    path('get-my-profile', get_my_profile.as_view(), name='get_my_profile'),
    path('get-bud-profile', get_bud_profile, name='get_bud_profile'), 
    path('get-buds-by-artist', get_buds_by_artist, name='get_buds_by_artist'),
    path('get-buds-by-track', get_buds_by_track, name='get_buds_by_track'),
    path('get-buds-by-artist-and-track', get_buds_by_artist_and_track, name='get_buds_by_artist_and_track'),
    path('search-channels-and-users', search_channels_and_users_view, name='search_channels_and_users'),
]


# Add error handling views
handler404 = not_found_view
handler500 = error_view