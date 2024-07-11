# Store data using neomodel
from myapp.db_models.User import User
from myapp.db_models.Artist import Artist
from myapp.db_models.Played_Track import PlayedTrack
from datetime import datetime
from .LastfmService import LastFmService
from django.conf import settings

import asyncio


async def store_top_artists(service: LastFmService, username: str):
    top_artists = await service.fetch_top_artists(username)
    user = User.nodes.get_or_none(username=username)
    if not user:
        user = User(username=username).save()
    
    for item in top_artists:
        artist, _ = Artist.get_or_create({'name': item.item.name})
        user.top_artists.connect(artist, {'weight': item.weight})

async def store_top_tracks(service: LastFmService, username: str):
    top_tracks = await service.fetch_top_tracks(username)
    user = User.nodes.get_or_none(username=username)
    if not user:
        user = User(username=username).save()

    for item in top_tracks:
        played_track = PlayedTrack(
            track=item.item.title,
            album=item.item.get_album().title if item.item.get_album() else "",
            playback_date=datetime.now(),  # Add actual playback date if available
            timestamp=int(datetime.now().timestamp())
        ).save()
        user.played_tracks.connect(played_track)

async def store_library(service: LastFmService, username: str):
    library_items = await service.fetch_library(username)
    user = User.nodes.get_or_none(username=username)
    if not user:
        user = User(username=username).save()

    for item in library_items:
        artist, _ = Artist.get_or_create({'name': item.item.name})
        user.library_items.connect(artist, {'playcount': item.playcount, 'tagcount': item.tagcount})

async def store_top_charts(service: LastFmService):
    top_tracks, top_artists = await service.fetch_top_charts()

    for item in top_tracks:
        played_track = PlayedTrack(
            track=item.item.title,
            album=item.item.get_album().title if item.item.get_album() else "",
            playback_date=datetime.now(),  # Add actual playback date if available
            timestamp=int(datetime.now().timestamp())
        ).save()
        # Store the track as a global top track if necessary

    for item in top_artists:
        artist, _ = Artist.get_or_create({'name': item.item.name})
        # Store the artist as a global top artist if necessary

# Initialize and run async tasks
async def main(username):

    service = LastFmService(settings.LASTFM_API_KEY, settings.LASTFM_API_SECRET)

    await store_top_artists(service, username)
    await store_top_tracks(service, username)
    await store_library(service, username)
    await store_top_charts(service)
    if __name__ == '__main__':
        asyncio.run(main(username))