
from neomodel import(StructuredNode, 
      IntegerProperty,db,BooleanProperty,ZeroOrMore 
      ,StructuredNode, StringProperty, IntegerProperty 
      , RelationshipTo,ArrayProperty)
from neomodel.exceptions import MultipleNodesReturned, DoesNotExist
from .Artist import Artist
from .Track import Track
from .Genre import Genre
from .Band import Band
from .Album import Album
from .Played_Track import PlayedTrack
from .Loved_Track import LovedTrack
from .Top_Item_Rel import TopItemRel
from .Library_Item_Rel import LibraryItemRel
import time




class User(StructuredNode):
    uid = StringProperty(unique_index=True)
    username = StringProperty(unique_index=True)
    channel_handle = StringProperty()
    account_name = StringProperty()
    email = StringProperty(unique_index=True, email=True, min_length=1, max_length=255)
    country = StringProperty()
    display_name = StringProperty(min_length=1, max_length=255)
    access_token = StringProperty()
    refresh_token = StringProperty()
    expires_at = IntegerProperty()
    expires_in = IntegerProperty()
    token_issue_time = StringProperty()
    bio = StringProperty()
    is_active = BooleanProperty()
    is_authenticated = BooleanProperty()
    scope = ArrayProperty()
    token_type = StringProperty()
    source =  StringProperty()

    top_artists = RelationshipTo(Artist, 'TOP_ARTIST', model=TopItemRel)
    top_tracks = RelationshipTo(Track, 'TOP_TRACK', model=TopItemRel)
    top_genres = RelationshipTo(Genre, 'TOP_GENRE', model=TopItemRel)
    top_albums = RelationshipTo(Album, 'TOP_ALBUM', model=TopItemRel)
    top_bands = RelationshipTo(Band, 'TOP_BAND', model=TopItemRel)

    library_items = RelationshipTo(Artist, 'LIBRARY_ITEM', model=LibraryItemRel)
    played_tracks = RelationshipTo(PlayedTrack, 'PLAYED')
    loved_tracks = RelationshipTo(LovedTrack, 'LOVED')

    likes_artist = RelationshipTo(Artist, 'LIKES_ARTIST',cardinality=ZeroOrMore)
    likes_track = RelationshipTo(Track, 'LIKES_TRACK',cardinality=ZeroOrMore)
    likes_genre = RelationshipTo(Genre, 'LIKES_GENRE',cardinality=ZeroOrMore)

    def serialize(self):
        return {
            'uid': self.uid,
            'username':self.username,
            'channel_handle':self.channel_handle,
            'account_name':self.account_name,
            'email': self.email,
            'country': self.country,
            'display_name': self.display_name,
            'bio': self.bio,
            'is_active': self.is_active,
            'is_authenticated': self.is_authenticated,
        }
    
    @classmethod
    def update_spotify_tokens(cls, user,tokens):
        user.access_token = tokens['access_token']
        user.refresh_token = tokens['refresh_token']
        user.expires_at = tokens['expires_at']
        user.token_type = tokens['token_type']
        user.expires_in = tokens['expires_in']
        user.token_issue_time = time.time()
        user.is_active= True

        user.save()
        return user
    @classmethod
    def update_ytmusic_tokens(cls, user,tokens):
        user.access_token = tokens['access_token']
        user.refresh_token = tokens['refresh_token']
        user.expires_at = tokens['expires_at']
        user.token_issue_time = time.time()
        user.token_type = tokens['token_type']
        user.expires_in = tokens['expires_in']
        user.expires_at = tokens['expires_at']
        user.scope = tokens['scope']
        user.is_active= True

        user.save()
        return user
    @classmethod
    def update_lastfm_tokens(cls, profile, token):
        """
        Update LastFM tokens for the user.
        """
        try:
            user = cls.nodes.get(username=profile['username'])
        except MultipleNodesReturned:
            # Handle the case where multiple users are found
            print(f"Multiple users found with username: {profile['username']}")
            return None
        except DoesNotExist:
            # If the user does not exist, create a new user
            user = cls.create_from_lastfm_profile(profile,token)

        user.access_token = token
        user.token_issue_time = str(time.time())
        user.is_active = True
        user.save()
        return user

    @classmethod
    def set_and_update_bio(cls, user_id, bio):
        user = cls.nodes.get_or_none(uid=user_id)
        if user:
            user.bio = bio
            user.save()
            return True
        return False
    @classmethod
    def get_profile(cls, user_id):
        # Assuming user_id is the unique identifier for the user
        user = cls.nodes.filter(id=user_id).first()
        return user
    # Define relationships
    likes_artist = RelationshipTo('Artist', 'LIKES_ARTIST')
    likes_track = RelationshipTo('Track', 'LIKES_TRACK')

    @classmethod
    def get_bud_profile(cls, user_id, bud_id, limit=50, skip=0):
        # Define the Cypher query
        cypher_query = f"""
            MATCH (user {{id: '{user_id}'}})-[:LIKES]->(user_artists:ARTIST)
            WITH user, user_artists, collect(user_artists) as user_artists_coll
            MATCH (bud {{id: '{bud_id}'}})-[:LIKES]->(common_artists:ARTIST)
            WHERE common_artists IN user_artists_coll
            WITH user, bud, common_artists 
            MATCH (user)-[:LIKES]->(user_tracks:TRACK)
            WITH bud, common_artists, collect(user_tracks) as user_tracks_coll
            MATCH (bud)-[:LIKES]->(common_tracks:TRACK)
            WHERE common_tracks IN user_tracks_coll 
            WITH bud, common_artists, common_tracks
            RETURN bud, 
                   collect(DISTINCT common_artists.id)[{skip}..{skip}+{limit}] as common_artists, 
                   count(DISTINCT common_artists) as common_artists_count, 
                   collect(DISTINCT common_tracks.id)[{skip}..{skip}+{limit}] as common_tracks, 
                   count(DISTINCT common_tracks) as common_tracks_count, 
                   count(DISTINCT common_artists) + count(DISTINCT common_tracks) as common_count 
            ORDER BY common_count DESC
        """

        # Execute the Cypher query
        results, meta = cls.cypher_query(cypher_query)

        # Process the query result
        bud_profile = {}
        if results:
            # Extract data from the result
            # Adjust this part based on your query result structure
            bud_profile['user'] = results[0][0]
            bud_profile['common_artists'] = results[0][1]
            bud_profile['common_artists_count'] = results[0][2]
            bud_profile['common_tracks'] = results[0][3]
            bud_profile['common_tracks_count'] = results[0][4]
            bud_profile['common_count'] = results[0][5]

        return bud_profile

    @classmethod
    def get_buds_by_artist(cls, artist_id):
        # Define the Cypher query to find users who like the given artist
        cypher_query = f"""
            MATCH (user:User)-[:LIKES_ARTIST]->(artist:Artist {{uid: '{artist_id}'}})
            RETURN user
        """

        # Execute the Cypher query
        results, _ = db.cypher_query(cypher_query)

        # Process the query result and extract user nodes
        buds = [record[0] for record in results]

        return buds

    @classmethod
    def get_buds_by_track(cls, track_id):
        # Define the Cypher query to find users who like the given track
        cypher_query = f"""
            MATCH (user:User)-[:LIKES_TRACK]->(track:Track {{uid: '{track_id}'}})
            RETURN user
        """

        # Execute the Cypher query
        results, _ = db.cypher_query(cypher_query)

        # Process the query result and extract user nodes
        buds = [record[0] for record in results]

        return buds
    @classmethod
    def create_from_spotify_profile(cls, profile,tokens):
        # Extract relevant data from the Spotify profile
        user_data = {
            'uid': profile.get('id', None),
            'birth_date' : profile.get('birth_date', None),
            'country' : profile.get('country', None),
            'display_name' : profile.get('display_name', None),
            'email' : profile.get('email', None),
            'access_token' : tokens['access_token'],
            'refresh_token' : tokens['refresh_token'],
            'expires_in' : tokens['expires_in'],
            'expires_at' : tokens['expires_at']

                }
        
        # Create a new user instance with the extracted data
        user = cls(**user_data)
        user.save()
        return user
    
    @classmethod
    def create_from_ytmusic_profile(cls, profile,tokens):
        # Extract relevant data from the Spotify profile
        user_data = {
            'account_name' : profile['accountName'] ,
            'channel_handle': profile['channelHandle'],
             'access_token' :tokens['access_token'],
            'refresh_token' :tokens['refresh_token'],
            'expires_at' :tokens['expires_at'],
            'token_issue_time' :time.time(),
            'token_type' :tokens['token_type'],
            'expires_in' :tokens['expires_in'],
            'expires_at' :tokens['expires_at'],
            'scope' :tokens['scope']
                }
        
        # Create a new user instance with the extracted data
        user = cls(**user_data)
        user.save()
        return user
    
    @classmethod
    def create_from_lastfm_profile(cls, profile,token):
        # Extract relevant data from the Spotify profile
        user_data = {
            'username': profile['username'],
            'access_token': token,
                }
        
        # Create a new user instance with the extracted data
        user = cls(**user_data)
        user.save()
        
        return user
    
    

