from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .node_resolver import custom_install_labels

@receiver(post_migrate)
def run_after_migrations(sender, **kwargs):
    custom_install_labels()
