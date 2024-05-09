import json
from logger_config import setup_logger
from dynamodb_utils import DynamoDBManager
from slack_client import send_slack_message
import re
from common_messages import *

logger = setup_logger()

def handle_event(event):
    try:
        body = json.loads(event['body'])
    except KeyError:
        logger.warning("No body in the request")
        return create_response(400, 'Bad Request: Missing body')
        
    event_ts = body['event'].get('ts')
    db_manager = DynamoDBManager()
    
    try:
        db_manager.create_table_if_not_exists()
        if db_manager.check_event(event_ts):
            logger.info("Duplicate event detected, ignoring...")
            return create_response(200, 'Duplicate event ignored')
        db_manager.store_event(event_ts)
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        return create_response(500, 'Database operation failed')

    return process_slack_event(body)
    
def process_slack_event(body):
    event_type = body['event'].get('type')
    channel_id = body['event'].get('channel')
    message_text = body['event'].get('text', '')
    thread_ts = body['event'].get('ts', None)

    logger.info(f"Event Type: {event_type}, Channel ID: {channel_id}, thread_ts: {thread_ts}")

    if thread_ts is None:
        logger.info("thread_ts is missing; cannot reply in thread")

    if body['event'].get('bot_id'):
        logger.info("This is a bot message, no thread_ts expected unless it's a reply.")
        return create_response(200, 'Ignored non-user or non-message event')

    # 테스트 채널용 코드
    if channel_id == "C072GNL8A90" and message_text.strip().lower() == "루피":
        try:
            send_slack_message(channel_id, '루피!', thread_ts)  # Respond with "루피!"
            return create_response(200, 'Response sent: 루피!')
        except SlackApiError as e:
            logger.error(f"Failed to send message: {e.response['error']}")
            return create_response(500, f"Failed to send message: {e.response['error']}")

    # 테스트 채널용 코드
    # C072GNL8A90 - test방 C04CNA12Y6N - 도협방
    if channel_id in ["C072GNL8A90", "C04CNA12Y6N"]:
        try:
            send_slack_message(channel_id, DX_TOOL_GUIDE_MESSAGE, thread_ts)  # Respond with "루피!"
            return create_response(200, 'Response sent: {DX_TOOL_GUIDE_MESSAGE}')
        except SlackApiError as e:
            logger.error(f"Failed to send message: {e.response['error']}")
            return create_response(500, f"Failed to send message: {e.response['error']}")

    pattern = r'.*LG유플러스 CTO에 한 사람을 초대하도록 요청했습니다.*'
    if re.match(pattern, message_text, re.IGNORECASE):
        try:
            send_slack_message(channel_id, CTO_DIRECT_INVITE, thread_ts)
            return create_response(200, 'Message processed successfully')
        except SlackApiError as e:
            logger.error(f"Failed to send message: {e.response['error']}")
            return create_response(500, f"Failed to send message: {e.response['error']}")

    return create_response(200, 'No action required')

def create_response(status_code, message):
    return {'statusCode': status_code, 'body': json.dumps({'message': message})}

def lambda_handler(event, context):
    logger.info("Received event: %s", event)
    return handle_event(event)
