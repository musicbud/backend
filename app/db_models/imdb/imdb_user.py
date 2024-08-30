from neomodel import AsyncStructuredNode, StringProperty, RelationshipTo


class ImdbUser(AsyncStructuredNode):
    user_id = StringProperty(unique_index=True, required=True)
    username = StringProperty(required=True)
    email = StringProperty()
    
    # Relationships
    likes_movies = RelationshipTo('app.db_models.imdb.imdb_movie.ImdbMovie', 'LIKES')
    watched_movies = RelationshipTo('app.db_models.imdb.imdb_movie.ImdbMovie', 'WATCHED')
    rated_movies = RelationshipTo('app.db_models.imdb.imdb_movie.ImdbMovie', 'RATED')
    watchlist = RelationshipTo('app.db_models.imdb.imdb_movie.ImdbMovie', 'WANTS_TO_WATCH')
