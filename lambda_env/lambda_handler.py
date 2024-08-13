import json
import base64
import re
from logger_config import setup_logger
from dynamodb_utils import DynamoDBManager
from slack_client import send_slack_message
from get_email import get_user_email
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from common_messages import *
from urllib.parse import parse_qs
from get_email import get_user_email
from atlassian_admin import search_user_by_email, add_user_to_group

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

    admin_request_pattern = re.compile(r'님의 임시 관리자 권한 신청이 정상적으로 신청 완료되었습니다\.', re.IGNORECASE)
    product_request_pattern = re.compile(r':three: 신청제품 : (\w+)', re.IGNORECASE)
    user_mention_pattern = re.compile(r'<@([A-Z0-9]+)>')

    if admin_request_pattern.search(message_text):
        logger.info("Detected admin rights request completion message.")
        product_match = product_request_pattern.search(message_text)
        user_mention_match = user_mention_pattern.search(message_text)

        if product_match and user_mention_match:
            product_name = product_match.group(1)
            user_id = user_mention_match.group(1)
            logger.info(f"Detected product request for {product_name} by user {user_id}.")

            # Fetch user email
            try:
                user_email = get_user_email(user_id)
            except SlackApiError as e:
                return create_response(500, f"Failed to fetch user email: {e.response['error']}")

            if product_name.lower() == "confluence":
                # Use the jira_utils functions
                account_id = search_user_by_email(user_email)
                if account_id:
                    group_id = "8a70cb45-d9e1-47b8-a825-075dc383f192"  # Replace with your actual group ID
                    if add_user_to_group(account_id, group_id):
                        response_message = f"컨플: User added to group successfully. ({user_email})"
                    else:
                        response_message = f"컨플: Failed to add user to group. ({user_email})"
                else:
                    response_message = f"컨플: No user found with the given email address. ({user_email})"
            
            elif product_name.lower() == "jira":
                response_message = f"지라 ({user_email})"
            
            if response_message:
                try:
                    logger.info(f"Sending response '{response_message}' to channel {channel_id}")
                    send_slack_message(channel_id, response_message, body['event']['ts'])
                    return create_response(200, f"Response sent: {response_message}")
                except SlackApiError as e:
                    logger.error(f"Failed to send message: {e.response['error']}")
                    return create_response(500, f"Failed to send message: {e.response['error']}")

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
    
    okta_pattern = re.compile(r'\b(okta|옥타)\b', re.IGNORECASE)
    if okta_pattern.search(message_text):
        logger.info("Message contains keywords, sending response")
        # 테스트 채널용 코드
        if channel_id in ["C072GNL8A90", "C04CNA12Y6N", "C06DZTAJH0X"]:
            try:
                logger.info(f"Sending OKTA_MESSAGE to channel {channel_id}")
                send_slack_message(channel_id, OKTA_MESSAGE, body['event']['ts']) 
                return create_response(200, f"Response sent: {OKTA_MESSAGE}")
            except SlackApiError as e:
                logger.error(f"Failed to send message: {e.response['error']}")
                return create_response(500, f"Failed to send message: {e.response['error']}")

    return create_response(200, 'No action required')
    
def create_response(status_code, message):
    return {'statusCode': status_code, 'body': json.dumps({'message': message})}

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    return handle_event(event)
