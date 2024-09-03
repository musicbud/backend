from django.core.management.base import BaseCommand
from app.db_models.node_resolver import custom_install_labels

class Command(BaseCommand):
    help = 'Create constraints for Neomodel nodes'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting to create constraints...")
        custom_install_labels()
        self.stdout.write(self.style.SUCCESS('Successfully created constraints'))
