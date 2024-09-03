from django.core.management.base import BaseCommand
from neomodel import db

class Command(BaseCommand):
    help = 'Check if a user exists in Neo4j'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)

    def handle(self, *args, **options):
        username = options['username']
        query = "MATCH (u:ParentUser {username: $username}) RETURN u"
        results, _ = db.cypher_query(query, {'username': username})
        if results:
            self.stdout.write(self.style.SUCCESS(f'User {username} found in Neo4j'))
        else:
            self.stdout.write(self.style.ERROR(f'User {username} not found in Neo4j'))
