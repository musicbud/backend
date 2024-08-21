from django.core.management.base import BaseCommand
from app.services.recommendation_service import get_recommendations, save_recommendations
from app.db_models import User

class Command(BaseCommand):
    help = 'Update user recommendations in Neo4j'

    async def handle(self, *args, **options):
        users = await User.nodes.all()
        for user in users:
            try:
                user_id = user.uid
                recommendations = await get_recommendations(user_id)
                await save_recommendations(user_id, recommendations)
                self.stdout.write(self.style.SUCCESS(f'Successfully updated recommendations for user {user_id}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating recommendations for user {user_id}: {str(e)}'))
