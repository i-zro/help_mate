import json
import base64
import re
from logger_config import setup_logger
from dynamodb_utils import DynamoDBManager
from slack_client import send_slack_message
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from common_messages import *
from urllib.parse import parse_qs

logger = setup_logger()

def handle_event(event):
    try:
        logger.info("Handling event")
        if event.get('isBase64Encoded'):
            body = base64.b64decode(event['body']).decode('utf-8')
        else:
            body = event['body']
        
        body_json = json.loads(body)
        logger.info(f"Parsed body: {json.dumps(body_json, indent=2, ensure_ascii=False)}")
    except KeyError:
        logger.warning("No body in the request")
        return create_response(400, 'Bad Request: Missing body')
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {str(e)}")
        return create_response(400, 'Bad Request: JSON decoding error')
    except Exception as e:
        logger.error(f"Error processing body: {str(e)}")
        return create_response(500, 'Internal Server Error')
    
    if 'event' in body_json:
        logger.info(f"Event received: {body_json['event']}")
        
        # bot_id가 있으면 무시
        if 'bot_id' in body_json['event']:
            logger.info("Event from a bot detected, ignoring...")
            return create_response(200, 'Event from a bot ignored')
        
        event_ts = body_json['event'].get('ts')
        event_id = body_json.get('event_id')  # 이벤트 ID를 사용하여 중복 확인
        db_manager = DynamoDBManager()
        
        try:
            db_manager.create_table_if_not_exists()
            if db_manager.check_event(event_id):
                logger.info("Duplicate event detected, ignoring...")
                return create_response(200, 'Duplicate event ignored')
            db_manager.store_event(event_id)
            logger.info("Event stored successfully")
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            return create_response(500, 'Database operation failed')

        return process_slack_event(body_json)

    return create_response(200, 'No action required')

def process_slack_event(body):
    event_type = body['event'].get('type')
    channel_id = body['event'].get('channel')
    message_text = body['event'].get('text', '')
    thread_ts = body['event'].get('thread_ts')

    logger.info(f"Event Type: {event_type}, Channel ID: {channel_id}, thread_ts: {thread_ts}")

    # thread_ts가 None인 경우에만 메시지 전송 (스레드의 첫 번째 메시지일 때만 반응)
    if thread_ts is not None:
        logger.info("This message is part of a thread; no action taken.")
        return create_response(200, 'Message is part of a thread; no action taken.')

    if body['event'].get('bot_id'):
        logger.info("This is a bot message, ignoring.")
        return create_response(200, 'Ignored bot message')

    # 특정 단어가 포함된 메시지 필터링 (대소문자 구분 없이)
    keywords_pattern = re.compile(r'\b(jira|confluence|지라|컨플)\b', re.IGNORECASE)
    if keywords_pattern.search(message_text):
        logger.info("Message contains keywords, sending response")
        # 테스트 채널용 코드
        if channel_id in ["C072GNL8A90", "C04CNA12Y6N", "C06DZTAJH0X"]:
            try:
                logger.info(f"Sending DX_TOOL_GUIDE_MESSAGE to channel {channel_id}")
                send_slack_message(channel_id, DX_TOOL_GUIDE_MESSAGE, body['event']['ts']) 
                return create_response(200, f"Response sent: {DX_TOOL_GUIDE_MESSAGE}")
            except SlackApiError as e:
                logger.error(f"Failed to send message: {e.response['error']}")
                return create_response(500, f"Failed to send message: {e.response['error']}")
    
    okta_pattern = re.compile(r'\b(|옥타|okta)\b', re.IGNORECASE)
    if okta_pattern.search(message_text):
        logger.info("Message contains keywords, sending response")
        # 테스트 채널용 코드
        if channel_id in ["C072GNL8A90", "C04CNA12Y6N", "C06DZTAJH0X"]:
            try:
                logger.info(f"Sending DX_TOOL_GUIDE_MESSAGE to channel {channel_id}")
                send_slack_message(channel_id, OKTA_MESSAGE, body['event']['ts']) 
                return create_response(200, f"Response sent: {OKTA_MESSAGE}")
            except SlackApiError as e:
                logger.error(f"Failed to send message: {e.response['error']}")
                return create_response(500, f"Failed to send message: {e.response['error']}")
    
    confluence_admin_pattern = re.compile(r'\b임시관리자 권한\b', re.IGNORECASE)
    product_confluence_pattern = re.compile(r'\b신청제품 : Confluence\b', re.IGNORECASE)
    if confluence_admin_pattern.search(message_text) and product_confluence_pattern.search(message_text):
        logger.info("Message contains specific terms for admin rights and product request")
        # Define the channels to respond to
        if channel_id in ["C04FHDRMZ9V", "C06DZTAJH0X"]:
            try:
                logger.info(f"Sending a custom response to channel {channel_id}")
                send_slack_message(channel_id, "컨플임", body['event']['ts'])
                return create_response(200, "Response sent: 컨플임")
            except SlackApiError as e:
                logger.error(f"Failed to send message: {e.response['error']}")
                return create_response(500, f"Failed to send message: {e.response['error']}")            
    return create_response(200, 'No action required')

def create_response(status_code, message):
    return {'statusCode': status_code, 'body': json.dumps({'message': message})}

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    return handle_event(event)
