from neomodel import AsyncStructuredNode, StringProperty, IntegerProperty, FloatProperty, RelationshipFrom

class ImdbMovie(AsyncStructuredNode):
    imdb_id = StringProperty(unique_index=True, required=True)
    title = StringProperty(required=True)
    year = IntegerProperty()
    rating = FloatProperty()
    genres = StringProperty(multiple=True)
    plot = StringProperty()
    director = StringProperty()
    
    # Relationships
    liked_by = RelationshipFrom('app.db_models.imdb.imdb_user.ImdbUser', 'LIKES')
    watched_by = RelationshipFrom('app.db_models.imdb.imdb_user.ImdbUser', 'WATCHED')
    rated_by = RelationshipFrom('app.db_models.imdb.imdb_user.ImdbUser', 'RATED')
    in_watchlist_of = RelationshipFrom('app.db_models.imdb.imdb_user.ImdbUser', 'WANTS_TO_WATCH')
