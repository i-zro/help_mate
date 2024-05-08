from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from secrets_manager import get_secret

def send_slack_message(channel_id, text, thread_ts):
    secrets = json.loads(get_secret("slack_bot_token"))
    slack_token = secrets['SLACK_TOKEN']
    client = WebClient(token=slack_token)
    try:
        response = client.chat_postMessage(channel=channel_id, text=text, thread_ts=thread_ts)
        return response
    except SlackApiError as e:
        logger = setup_logger()
        logger.error(f"Failed to send message: {e.response['error']}")
        raise e

