from neomodel import db

# Drop all constraints and indexes
db.cypher_query("CALL db.constraints() YIELD name CALL db.constraint.drop(name) RETURN name")
db.cypher_query("CALL db.indexes() YIELD name CALL db.index.drop(name) RETURN name")

# Create constraints and indexes based on current model definitions
db.cypher_query("CREATE CONSTRAINT ON (t:Track) ASSERT t.uid IS UNIQUE")
db.cypher_query("CREATE CONSTRAINT ON (u:User) ASSERT u.uid IS UNIQUE")
db.cypher_query("CREATE CONSTRAINT ON (u:User) ASSERT u.email IS UNIQUE")
