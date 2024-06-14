
from neomodel import StructuredNode, StringProperty,Relationship,RelationshipTo, IntegerProperty,db,RelationshipFrom,BooleanProperty,ZeroOrMore
from neomodel.exceptions import MultipleNodesReturned, DoesNotExist
import time



class LikedItem(StructuredNode):
    uid = StringProperty(required=True, unique_index=True)

    def serialize(self):
        return {
            'uid': self.uid,
        }

class Artist(LikedItem):
    href = StringProperty(required=True, unique_index=True, max_length=255)
    name = StringProperty(required=True, max_length=255)
    popularity = IntegerProperty(required=True, min_value=1, max_value=255)
    type = StringProperty(required=True, max_length=255)
    uri = StringProperty(required=True, max_length=255)
    liked_by = RelationshipFrom('User', 'LIKES_ARTIST',cardinality=ZeroOrMore)

    def serialize(self):
        return {
            'uid': self.uid,
            'href': self.href,
            'name': self.name,
            'popularity': self.popularity,
            'type': self.type,
            'uri': self.uri
        }

class Track(LikedItem):
    href = StringProperty(required=True, min_length=1, max_length=255)
    name = StringProperty(required=True, min_length=1, max_length=255)
    popularity = IntegerProperty(required=True, min_value=1, max_value=255)
    type = StringProperty(required=True, min_length=1, max_length=255)
    uri = StringProperty(required=True, min_length=1, max_length=255)
    liked_by = RelationshipFrom('User', 'LIKES_TRACK',cardinality=ZeroOrMore)

    def serialize(self):
        return {
            'uid': self.uid,
            'href': self.href,
            'name': self.name,
            'popularity': self.popularity,
            'type': self.type,
            'uri': self.uri
        }

class Genre(LikedItem):
    href = StringProperty(required=True, min_length=1, max_length=255)
    name = StringProperty(required=True, min_length=1, max_length=255)
    popularity = IntegerProperty(required=True, min_value=1, max_value=255)
    type = StringProperty(required=True, min_length=1, max_length=255)
    uri = StringProperty(required=True, min_length=1, max_length=255)
    liked_by = RelationshipFrom('User', 'LIKES_GENRE',cardinality=ZeroOrMore)

    def serialize(self):
        return {
            'uid': self.uid,
            'href': self.href,
            'name': self.name,
            'popularity': self.popularity,
            'type': self.type,
            'uri': self.uri
        }

class User(StructuredNode):
    uid = StringProperty(required=True, unique_index=True)
    email = StringProperty(unique_index=True, email=True, min_length=1, max_length=255)
    country = StringProperty()
    display_name = StringProperty(required=True, min_length=1, max_length=255)
    access_token = StringProperty()
    refresh_token = StringProperty()
    expires_at = IntegerProperty()
    token_issue_time = IntegerProperty()
    bio = StringProperty()
    is_active = BooleanProperty()
    is_authenticated = BooleanProperty()

    likes_artist = RelationshipTo(Artist, 'LIKES_ARTIST',cardinality=ZeroOrMore)
    likes_track = RelationshipTo(Track, 'LIKES_TRACK',cardinality=ZeroOrMore)
    likes_genre = RelationshipTo(Genre, 'LIKES_GENRE',cardinality=ZeroOrMore)

    def serialize(self):
        return {
            'uid': self.uid,
            'email': self.email,
            'country': self.country,
            'display_name': self.display_name,
            'bio': self.bio,
            'is_active': self.is_active,
            'is_authenticated': self.is_authenticated,
        }
    
    @classmethod
    def update_tokens(cls, user_id, access_token, refresh_token, expires_at):
        try:
            user = cls.nodes.get(uid=user_id)
        except MultipleNodesReturned:
            # Handle the case where multiple users are found
            print(f"Multiple users found with uid: {user_id}")
            return None
        except DoesNotExist:
            # Handle the case where no user is found
            print(f"No user found with uid: {user_id}")
            return None

        if user:
            user.access_token = access_token
            user.refresh_token = refresh_token
            user.expires_at = expires_at
            user.token_issue_time = time.time()
            user.is_active= True

            user.save()
            return user
        else:
            print("User not found")
            return None 
    @classmethod
    def update_likes(self, user_instance, user_top_artists, user_top_tracks):

        # Get existing likes
        existing_artist_likes = {rel.uid for rel in user_instance.likes_artist.all()}
        existing_track_likes = {rel.uid for rel in user_instance.likes_track.all()}

        # Create new likes relationships for top artists
        for artist_id in user_top_artists:
            if artist_id not in existing_artist_likes:
                artist_node = Artist.nodes.get_or_none(uid=artist_id)
                if artist_node is None:
                    # Create a new artist node
                    artist_node = Artist(uid=artist_id).save()
                    
                user_instance.likes_artist.connect(artist_node)

        # Create new likes relationships for top tracks
        for track_id in user_top_tracks:
            if track_id not in existing_track_likes:
                track_node = Track.nodes.get_or_none(uid=track_id)
                if track_node is None:
                    # Create a new track node
                    track_node = Track(uid=track_id).save()
                
                user_instance.likes_track.connect(track_node)
    @classmethod
    def get_user_top_artists_ids(self):
        return [artist.id for artist in self.likes.filter(_class='Artist')]
    @classmethod
    def get_user_top_tracks_ids(self):
        return [track.id for track in self.likes.filter(_class='Track')]
    
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
    def create_from_spotify_profile(cls, spotify_profile):
        # Extract relevant data from the Spotify profile
        user_data = {
            'uid': spotify_profile.get('id', None),
            'birth_date' : spotify_profile.get('birth_date', None),
            'country' : spotify_profile.get('country', None),
            'display_name' : spotify_profile.get('display_name', None),
            'email' : spotify_profile.get('email', None),

                }
        
        # Create a new user instance with the extracted data
        user = cls(**user_data)
        user.save()
        
        return user

