from adrf.views import APIView
from rest_framework import status
from rest_framework.response import Response
from app.services.service_selector import get_service
import logging
import asyncio
from app.middlewares.async_jwt_authentication import AsyncJWTAuthentication
from rest_framework.permissions import IsAuthenticated  

logger = logging.getLogger(__name__)

class UpdateMyLikes(APIView):
    authentication_classes = [AsyncJWTAuthentication]
    permission_classes = [IsAuthenticated]

    async def post(self, request, *args, **kwargs):
        try:
            parent_user = request.parent_user
            if not parent_user:
                logger.error(f"Parent user not found in request for user: {request.user.username}")
                return Response({"error": "Parent user not found"}, status=status.HTTP_404_NOT_FOUND)

            spotify_service = await get_service('spotify')
            if not spotify_service:
                return Response({"error": "Failed to initialize Spotify service"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                success = await asyncio.wait_for(spotify_service.save_user_likes(parent_user), timeout=120.0)
                if success:
                    logger.info(f"Likes updated successfully for user: {request.user.username}")
                    return Response({"success": True, "message": "Likes updated successfully"}, status=status.HTTP_200_OK)
                else:
                    logger.error(f"Failed to update likes for user: {request.user.username}")
                    return Response({"error": "Failed to update likes. Check logs for details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except asyncio.TimeoutError:
                logger.error(f"Timeout while updating likes for user: {request.user.username}")
                return Response({"error": "Timeout while updating likes. The operation took too long to complete."}, status=status.HTTP_504_GATEWAY_TIMEOUT)

        except Exception as e:
            logger.error(f"Error updating likes for user: {request.user.username} - {str(e)}")
            return Response({"error": f"An error occurred while updating likes: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

