import logging
from asgiref.sync import sync_to_async
import asyncio
from django.conf import settings
from neomodel import db
from app.db_models.parent_user import ParentUser  # Import your User model

logger = logging.getLogger(__name__)

class Neo4jService:
    @staticmethod
    async def get_parent_user_async(username):
        try:
            logger.info(f"Attempting to fetch user {username} from Neo4j")
            result = await Neo4jService.get_parent_user(username)
            if result:
                logger.info(f"Successfully fetched user {username} from Neo4j")
            else:
                logger.error(f"User {username} not found in Neo4j")
            return result
        except Exception as e:
            logger.error(f"Unexpected error while fetching user {username} from Neo4j: {str(e)}")
            logger.exception("Full traceback:")
            return None

    @staticmethod
    def get_parent_user(username):
        try:
            logger.info(f"Executing Neo4j query to fetch user {username}")
            user = ParentUser.nodes.get_or_none(username=username)  # Use get_or_none instead of get        
            logger.info(f"Successfully fetched user {username} from Neo4j")
            return user
        except ParentUser.DoesNotExist:
            logger.error(f"User {username} not found in Neo4j")
            return None
        except Exception as e:
            logger.error(f"Error fetching user {username} from Neo4j: {str(e)}")
            logger.exception("Full traceback:")
            return None

    @staticmethod
    async def create_or_update_user_async(user_data):
        try:
            return await Neo4jService.create_or_update_user(user_data)
        except Exception as e:          
            logger.error(f"Error creating/updating user in Neo4j: {str(e)}")
            return None

    @staticmethod
    def create_or_update_user(user_data):
        try:
            user, created = ParentUser.create_or_update(user_data)
            return user
        except Exception as e:
            logger.error(f"Error creating/updating user in Neo4j: {str(e)}")
            return None

    # Add this method to the Neo4jService class
    @staticmethod
    def test_connection():
        try:
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
            result, _ = db.cypher_query("MATCH (n) RETURN COUNT(n) as count")
            count = result[0][0]
            logger.info(f"Successfully connected to Neo4j. Node count: {count}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            return False

    @staticmethod
    def check_user_exists(username):
        try:
            user = ParentUser.nodes.get_or_none(username=username)
            exists = user is not None
            logger.info(f"User {username} exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking if user {username} exists: {str(e)}")
            return False
