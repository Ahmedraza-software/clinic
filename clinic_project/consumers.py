import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Add this connection to the 'dashboard_updates' group
            await self.channel_layer.group_add("dashboard_updates", self.channel_name)
            await self.accept()
            logger.info("WebSocket connected")
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        # Remove this connection from the 'dashboard_updates' group
        try:
            await self.channel_layer.group_discard("dashboard_updates", self.channel_name)
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket disconnection error: {str(e)}")

    async def receive(self, text_data=None, bytes_data=None):
        # Handle incoming WebSocket messages (if needed)
        try:
            if text_data:
                data = json.loads(text_data)
                logger.info(f"Received WebSocket message: {data}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")

    async def patient_update(self, event):
        try:
            # Get the patient data from the event
            patient_data = event.get('patient', {})
            
            # Prepare the data to send to the client
            data = {
                'type': 'patient.update',
                'patient': {
                    'id': patient_data.get('id'),
                    'first_name': patient_data.get('first_name', ''),
                    'last_name': patient_data.get('last_name', ''),
                    'email': patient_data.get('email', ''),
                    'status': 'Active',
                    'last_visit': 'Just now',
                    'initials': f"{patient_data.get('first_name', '')[0]}{patient_data.get('last_name', '')[0]}" if patient_data.get('first_name') and patient_data.get('last_name') else 'P',
                    'full_name': f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}".strip()
                }
            }
            
            # Send the formatted data to the WebSocket
            await self.send(text_data=json.dumps(data))
            logger.info(f"Sent patient update: {data}")
            
        except Exception as e:
            logger.error(f"Error in patient_update: {str(e)}")
            # Try to send an error message to the client
            try:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'An error occurred while processing the patient update.'
                }))
            except:
                pass
