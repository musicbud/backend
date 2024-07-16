from neomodel import (StructuredNode, IntegerProperty, db, BooleanProperty, ZeroOrMore,
                      StringProperty, RelationshipTo, ArrayProperty, UniqueIdProperty)
from .Artist import Artist
from .Track import Track
from .Genre import Genre
from .Album import Album
from .Top_Item_Rel import TopItemRel


class User(StructuredNode):
    uid = UniqueIdProperty()
   
    email = StringProperty(unique_index=True, email=True, min_length=1, max_length=255)
    country = StringProperty()
    display_name = StringProperty(min_length=1, max_length=255)
    bio = StringProperty()
    is_active = BooleanProperty()
    is_authenticated = BooleanProperty()
    service = StringProperty()

    access_token = StringProperty()
    refresh_token = StringProperty()
    expires_at = IntegerProperty()
    expires_in = IntegerProperty()
    token_issue_time = StringProperty()
    token_type = StringProperty()
    scope = ArrayProperty()

    @classmethod
    def set_and_update_bio(cls, user_id, bio):
        user = cls.nodes.get_or_none(uid=user_id)
        if user:
            user.bio = bio
            user.save()
            return True
        return False
    
    @classmethod
    def get_bud_profile(cls, user_id, bud_id, limit=50, skip=0):
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
        results, meta = cls.cypher_query(cypher_query)
        bud_profile = {}
        if results:
            bud_profile['user'] = results[0][0]
            bud_profile['common_artists'] = results[0][1]
            bud_profile['common_artists_count'] = results[0][2]
            bud_profile['common_tracks'] = results[0][3]
            bud_profile['common_tracks_count'] = results[0][4]
            bud_profile['common_count'] = results[0][5]
        return bud_profile

    @classmethod
    def get_buds_by_artist(cls, artist_id):
        cypher_query = f"""
            MATCH (user:User)-[:LIKES_ARTIST]->(artist:Artist {{uid: '{artist_id}'}})
            RETURN user
        """
        results, _ = db.cypher_query(cypher_query)
        buds = [record[0] for record in results]
        return buds

    @classmethod
    def get_buds_by_track(cls, track_id):
        cypher_query = f"""
            MATCH (user:User)-[:LIKES_TRACK]->(track:Track {{uid: '{track_id}'}})
            RETURN user
        """
        results, _ = db.cypher_query(cypher_query)
        buds = [record[0] for record in results]
        return buds


