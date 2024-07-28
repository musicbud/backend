
import os
import json
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.services.ServiceSelector import get_service

from app.db_models.Parent_User import ParentUser 

from app.db_models.spotify.Spotify_User import SpotifyUser 

@csrf_exempt
async def create_user_seed(request):
    parent_user = ParentUser()

    parent_user.username = 'mahmwood1'
    parent_user.email = '54bao.o1@gmail.com'
    parent_user.password = 'password'
    await parent_user.save()


    service ='spotify'

    user = SpotifyUser()
    
    user.spotify_id = 'fake_user 1',
    user.display_name = 'fake_user 1'
    user.access_token = 'access_token'
    user.refresh_token = 'refresh_token'
    user.expires_at = 15454545.454455
    user.token_type = 'token_type'
    user.expires_in = 5454544.55
    user.token_issue_time = time.time()
    user.is_active = True
    user.service = 'spotify'

    await user.save()

    await parent_user.spotify_account.connect(user)
    #import fake artists
    json_file_path = os.path.join(os.path.dirname(__file__), 'fake_artists.json')
    
    with open(json_file_path, 'r') as file:
            fake_artists_data = json.load(file)
    
    #import fake tracks
    json_file_path = os.path.join(os.path.dirname(__file__), 'fake_tracks.json')
    
    with open(json_file_path, 'r') as file:
            fake_tracks_data = json.load(file)
    
    #import fake genres
    json_file_path = os.path.join(os.path.dirname(__file__), 'fake_genres.json')
    
    with open(json_file_path, 'r') as file:
            fake_genres_data = json.load(file)
    
     #import fake albums
    json_file_path = os.path.join(os.path.dirname(__file__), 'fake_albums.json')
    
    with open(json_file_path, 'r') as file:
            fake_albums_data = json.load(file)
    

# create  top artists


    json_file_path = os.path.join(os.path.dirname(__file__), 'user_top_artists.json')
    
    with open(json_file_path, 'r') as file:
        artists_data = json.load(file)
        data = [
              artists_data[0],
              artists_data[1],
              fake_artists_data[0],
              fake_artists_data[1],
        ]
        await get_service(service).map_to_neo4j(user, 'Artist', data, "top")

# create top tracks

    json_file_path = os.path.join(os.path.dirname(__file__), 'user_top_tracks.json')
    with open(json_file_path, 'r') as file:
        tracks_data = json.load(file)
        data = [
              tracks_data[0],
              tracks_data[1],
              fake_tracks_data[0],
              fake_tracks_data[1]
        ]
        await get_service(service).map_to_neo4j(user, 'Track', data, "top")

# create top genres 

    json_file_path = os.path.join(os.path.dirname(__file__), 'user_top_genres.json')
    with open(json_file_path, 'r') as file:
        genres_data = json.load(file)
        data = [
              genres_data[0],
              genres_data[1],
              fake_genres_data[0],
              fake_genres_data[1]
        ]
        await get_service(service).map_to_neo4j(user, 'Genre', data, "Track")
# create saved artists 


    json_file_path = os.path.join(os.path.dirname(__file__), 'user_followed_artists.json')
    with open(json_file_path, 'r') as file:
        artists_data = json.load(file)
        data = [
              artists_data[0],
              artists_data[1],
              fake_artists_data[0],
              fake_artists_data[1]
        ]
        await get_service(service).map_to_neo4j(user, 'Artist', data, "followed")
# create saved albums


    json_file_path = os.path.join(os.path.dirname(__file__), 'user_saved_tracks.json')
    with open(json_file_path, 'r') as file:
        tracks_data = json.load(file)
        data = [
              tracks_data[0],
              tracks_data[1],
              fake_tracks_data[0],
              fake_tracks_data[1]
        ]
        await get_service(service).map_to_neo4j(user, 'Track', data, "saved")
# create saved albums


    json_file_path = os.path.join(os.path.dirname(__file__), 'user_saved_albums.json')
    with open(json_file_path, 'r') as file:
        saved_albums_data = json.load(file)
        data = [
              saved_albums_data[0],
              saved_albums_data[1],
              fake_albums_data[0],
              fake_albums_data[1]
        ]
        await get_service(service).map_to_neo4j(user, 'Album', data, "saved")



    return JsonResponse({'message':'user create successfully'})