from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Activates all inactive users'

    def handle(self, *args, **options):
        DjangoParentUser = apps.get_model('app', 'DjangoParentUser')
        inactive_users = DjangoParentUser.objects.filter(is_active=False)
        count = inactive_users.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No inactive users found.'))
            return

        inactive_users.update(is_active=True)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully activated {count} user(s).'))
