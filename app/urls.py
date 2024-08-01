from django.urls import path
from rest_framework.routers import DefaultRouter  # Import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from app.views.registeration import (
    Register,
    Login,
    Logout
    ) 

from .views.connect import (
    NotFoundView,
    ErrorView,
    Login as ConnectLogin,
    SpotifyCallback,
    SpotifyConnect,
    YtmusicCallback,
    YtmusicConnect,
    LastfmCallback,
    LastfmConnect,
    MalCallback,
    MalConnect
)

from .views.get_common import (
    GetCommonLikedArtists,
    GetCommonLikedTracks,
    GetCommonLikedAlbums,
    GetCommonLikedGenres,
    GetCommonPlayedTracks,
    GetCommonTopArtists,
    GetCommonTopTracks,
    GetCommonTopGenres,
    GetCommonTopAnime,
    GetCommonTopManga
)

from .views.get_profile import (
    GetLikedArtists,
    GetLikedTracks,
    GetLikedAlbums,
    GetLikedGenres,
    GetPlayedTracks,
    GetTopArtists,
    GetTopTracks,
    GetTopGenres,
    GetTopAnime,
    GetTopManga
)

from .views.spotify_refresh_token import SpotifyRefreshToken
from .views.ytmusic_refresh_token import YtmusicRefreshToken

from .views.update_my_likes import UpdateMyLikes

from .views.get_my_profile import GetMyProfile
from .views.get_bud_profile import GetBudProfile

from .views.get_buds_by_liked_aio import GetBudsByLikedAio
from .views.get_buds_by_top import (
    GetBudsByTopArtists,
    GetBudsByTopTracks,
    GetBudsByTopGenres,
    GetBudsByTopAnime,
    GetBudsByTopManga
)

from .views.get_buds_by_liked import (
    GetBudsByLikedArtists,
    GetBudsByLikedTracks,
    GetBudsByLikedGenres,
    GetBudsByLikedAlbums,
    GetBudsByPlayedTracks
)

from .views.get_buds_by_id import (
    GetBudsByArtist,
    GetBusdByTrack,
    GetBudsByGenre,
    GetBudsByAlbum
)

from .views.search_users import SearchUsers
from .views.set_my_profile import SetMyProfile


from .seeders.spotify.create_user_seed import create_user_seed
from .views.merge_similars import merge_similars


router = DefaultRouter()

urlpatterns = [
    path('register', Register.as_view(), name='register'),
    path('login', Login.as_view(), name='login'),
    path('logout', Logout.as_view(), name='logout'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    path('service/login', ConnectLogin.as_view(), name='connect'),
    path('spotify/callback', SpotifyCallback.as_view(), name='spotify_callback'),
    path('ytmusic/callback', YtmusicCallback.as_view(), name='ytmusic_callback'),
    path('lastfm/callback', LastfmCallback.as_view(), name='lastfm_callback'),
    path('mal/callback', MalCallback.as_view(), name='lastfm_callback'),

    
    path('spotify/connect', SpotifyConnect.as_view(), name='spotify_connect'),
    path('ytmusic/connect', YtmusicConnect.as_view(), name='ytmusic_connect'),
    path('lastfm/connect', LastfmConnect.as_view(), name='lastfm_connect'),
    path('mal/connect', MalConnect.as_view(), name='lastfm_connect'),

    path('ytmusic/token/refresh', YtmusicRefreshToken.as_view(), name='ytmusic_refresh_token'),
    path('spotify/token/refresh', SpotifyRefreshToken.as_view(), name='spotify_refresh_token'),
    
    path('me/likes/update', UpdateMyLikes.as_view(), name='update_my_likes'),
    path('me/profile', GetMyProfile.as_view(), name='get_my_profile'),
    path('me/profile/set', SetMyProfile.as_view(), name='set_my_profile'),
    

    path('bud/common/liked/artists', GetCommonLikedArtists.as_view(), name='get_bud_profile'), 
    path('bud/common/liked/tracks', GetCommonLikedTracks.as_view(), name='get_common_liked_tracks'), 
    path('bud/common/liked/genres', GetCommonLikedGenres.as_view(), name='get_common_liked_genres'), 
    path('bud/common/liked/albums', GetCommonLikedAlbums.as_view(), name='get_common_liked_albums'), 
    path('bud/common/played/tracks', GetCommonPlayedTracks.as_view(), name='get_common_played_tracks'), 
    path('bud/common/top/artists', GetCommonTopArtists.as_view(), name='get_common_played_tracks'), 
    path('bud/common/top/tracks', GetCommonTopTracks.as_view(), name='get_common_top_tracks'), 
    path('bud/common/top/genres', GetCommonTopGenres.as_view(), name='get_common_top_genres'), 
    path('bud/common/top/anime', GetCommonTopAnime.as_view(), name='get_common_anime'), 
    path('bud/common/top/manga', GetCommonTopManga.as_view(), name='get_common_manga'), 


    path('me/liked/artists', GetLikedArtists.as_view(), name='get_bud_profile'), 
    path('me/liked/tracks', GetLikedTracks.as_view(), name='get_liked_tracks'), 
    path('me/liked/genres', GetLikedGenres.as_view(), name='get_liked_genres'), 
    path('me/liked/albums', GetLikedAlbums.as_view(), name='get_liked_albums'), 
    path('me/played/tracks', GetPlayedTracks.as_view(), name='get_played_tracks'), 
    path('me/top/artists', GetTopArtists.as_view(), name='get_played_tracks'), 
    path('me/top/tracks', GetTopTracks.as_view(), name='get_top_tracks'), 
    path('me/top/genres', GetTopGenres.as_view(), name='get_top_genres'), 
    path('me/top/anime', GetTopAnime.as_view(), name='get_top_anime'), 
    path('me/top/manga', GetTopManga.as_view(), name='get_top_manga'), 


    path('bud/profile', GetBudProfile.as_view(), name='get_bud_profile'), 

    path('bud/liked/artists', GetBudsByLikedArtists.as_view(), name='get_buds_by_liked_artists'),
    path('bud/liked/tracks', GetBudsByLikedTracks.as_view(), name='get_buds_by_liked_tracks'),
    path('bud/liked/genres', GetBudsByLikedGenres.as_view(), name='get_buds_by_liked_genres'),
    path('bud/liked/albums', GetBudsByLikedAlbums.as_view(), name='get_buds_by_liked_albums'),
    path('bud/liked/aio', GetBudsByLikedAio.as_view(), name='get_buds_by_liked_aio'),
    path('bud/top/artists', GetBudsByTopArtists.as_view(), name='get_buds_by_top_artists'),
    path('bud/top/tracks', GetBudsByTopTracks.as_view(), name='get_buds_by_top_tracks'),
    path('bud/top/genres', GetBudsByTopGenres.as_view(), name='get_buds_by_top_genres'),
    path('bud/top/anime', GetBudsByTopAnime.as_view(), name='get_buds_by_top_anime'),
    path('bud/top/manga', GetBudsByTopManga.as_view(), name='get_buds_by_top_manga'),
    path('bud/played/tracks', GetBudsByPlayedTracks.as_view(), name='get_buds_by_played_tracks'),
    path('bud/artist', GetBudsByArtist.as_view(), name='get_buds_by_artist'),
    path('bud/track', GetBusdByTrack.as_view(), name='get_buds_by_track'),
    path('bud/genre', GetBudsByGenre.as_view(), name='get_buds_by_genre'),
    path('bud/album', GetBudsByAlbum.as_view(), name='get_buds_by_album'),
  
    path('bud/search', SearchUsers.as_view(), name='search_users'),
    
    path('spotify/seed/user/create', create_user_seed, name='create_user_seed'),

    path('merge-similars', merge_similars, name='merge_similars'),
]





# Add error handling views
handler404 = NotFoundView.as_view()
handler500 = ErrorView.as_view()

