from app.db_models.parent_user import ParentUser as Neo4jParentUser
import asyncio
import logging

logger = logging.getLogger(__name__)

async def update_neo4j_user(username, access_token):
    try:
        neo4j_user = await Neo4jParentUser.nodes.get_or_none(username=username)
        if neo4j_user:
            neo4j_user.access_token = access_token
            await neo4j_user.save()
            logger.info(f"Updated existing Neo4j user: {username}")
        else:
            neo4j_user = Neo4jParentUser(username=username, access_token=access_token)
            await neo4j_user.save()
            logger.info(f"Created new Neo4j user: {username}")
    except Exception as e:
        logger.error(f"Error updating Neo4j user: {str(e)}", exc_info=True)

def update_neo4j_user_sync(username, access_token):
    asyncio.run(update_neo4j_user(username, access_token))
