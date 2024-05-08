import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from secrets_manager import get_secret
import logging

logger = logging.getLogger(__name__)

def send_slack_message(channel_id, text, thread_ts):
    secrets = json.loads(get_secret("slack_bot_token"))
    slack_token = secrets['SLACK_TOKEN']
    client = WebClient(token=slack_token)
    
    try:
        # Ensure thread_ts is being logged to verify correct value
        logger.info(f"Sending message to {channel_id}, thread_ts={thread_ts}")
        response = client.chat_postMessage(
            channel=channel_id,
            text=text,
            thread_ts=thread_ts  # This should not be None if you want to reply to a specific message
        )
        return response
    except SlackApiError as e:
        logger.error(f"Failed to send message: {e.response['error']}")
        raise e
