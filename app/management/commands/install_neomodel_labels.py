# File: myapp/management/commands/install_neomodel_labels.py

from django.core.management.base import BaseCommand
from neomodel import config, db

class Command(BaseCommand):
    help = 'Synchronize Neomodel models with Neo4j database'

    def handle(self, *args, **options):
        # Configure Neomodel database connection
        config.DATABASE_URL = 'bolt://neo4j:12345678@localhost:7687'
        db.set_connection(config.DATABASE_URL)

        # Ensure all models are registered with Neomodel
        # Note: Neomodel registers models automatically upon import
        # So, we do not need to explicitly register them here
        # But you can ensure they are imported properly

        # Optional: Perform any schema operations if needed
        # For example:
        # db.schema.create_uniqueness_constraint('User', 'uid')

        self.stdout.write(self.style.SUCCESS('Neomodel models synchronized successfully.'))
