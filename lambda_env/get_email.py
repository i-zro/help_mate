import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from secrets_manager import get_secret
import logging

logger = logging.getLogger(__name__)

def get_user_email(user_id):
    """
    Retrieves the email address of a Slack user given their user ID.

    Args:
        user_id (str): The Slack user ID.

    Returns:
        str: The email address of the user.

    Raises:
        SlackApiError: If the Slack API request fails.
    """
    secrets = json.loads(get_secret("slack_bot_token"))
    slack_token = secrets['SLACK_TOKEN']
    client = WebClient(token=slack_token)
    
    try:
        logger.info(f"Fetching email for user ID: {user_id}")
        user_info = client.users_info(user=user_id)
        user_email = user_info['user']['profile']['email']
        logger.info(f"Email for user {user_id} is {user_email}")
        return user_email
    except SlackApiError as e:
        logger.error(f"Failed to fetch user info: {e.response['error']}")
        raise e