from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver

class Command(BaseCommand):
    help = 'List all URL patterns'

    def handle(self, *args, **kwargs):
        self.stdout.write('Registered URL patterns:')
        self._print_urls(get_resolver())

    def _print_urls(self, resolver, prefix=''):
        for pattern in resolver.url_patterns:
            if isinstance(pattern, URLResolver):
                self._print_urls(pattern, prefix + str(pattern.pattern))
            elif isinstance(pattern, URLPattern):
                self.stdout.write(f'{prefix}{pattern.pattern}')
