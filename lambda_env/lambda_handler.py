import json
from logger_config import setup_logger
from dynamodb_utils import DynamoDBManager
from slack_client import send_slack_message

def lambda_handler(event, context):
    logger = setup_logger()
    logger.info("Received event: %s", event)
    try:
        body = json.loads(event['body'])
        logger.info("Parsed body: %s", body)
    except KeyError:
        logger.warning("No body in the request")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Bad Request: Missing body'})
        }

    event_ts = body['event'].get('ts')
    db_manager = DynamoDBManager()
    db_manager.create_table_if_not_exists()
    if db_manager.check_event(event_ts):
        logger.info("Duplicate event detected, ignoring...")
        return {'statusCode': 200, 'body': json.dumps({'message': 'Duplicate event ignored'})}
    db_manager.store_event(event_ts)

    # 메시지 처리 로직
[200~import json
from logger_config import setup_logger
from dynamodb_utils import DynamoDBManager
from slack_client import send_slack_message

def lambda_handler(event, context):
    logger = setup_logger()
    logger.info("Received event: %s", event)
    try:
        body = json.loads(event['body'])
        logger.info("Parsed body: %s", body)
    except KeyError:
        logger.warning("No body in the request")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Bad Request: Missing body'})
        }

    event_ts = body['event'].get('ts')
    db_manager = DynamoDBManager()
    db_manager.create_table_if_not_exists()
    if db_manager.check_event(event_ts):
        logger.info("Duplicate event detected, ignoring...")
        return {'statusCode': 200, 'body': json.dumps({'message': 'Duplicate event ignored'})}
    db_manager.store_event(event_ts)

    # 메시지 처리 로직
    event_type = body['event'].get('type')
    channel_id = body['event'].get('channel')
    message_text = body['event'].get('text', '')  # Slack에서 보내진 메시지 텍스트

    if body['event'].get('bot_id'):
        logger.info("Ignoring bot message")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Ignored bot message'})
        }

    event_ts = body['event'].get('ts')
    thread_ts = body['event'].get('thread_ts', event_ts)

    if thread_ts != event_ts:
        logger.info("Ignoring sub-thread message")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Ignored sub-thread message'})
        }

    secret = get_secret()
    if not secret:
        logger.error("Failed to get Slack token")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to get Slack token'})
        }
    secrets = json.loads(secret)
    slack_token = secrets['SLACK_TOKEN']
    client = WebClient(token=slack_token)
   
    # LG유플러스 CTO에 대한 요청을 확인하는 정규 표현식 패턴
    pattern = r'.*LG유플러스 CTO에 한 사람을 초대하도록 요청했습니다.*' 
    
    try:
        # LG유플러스 CTO에 대한 요청일 경우 거절 메시지 전송
        if re.match(pattern, message_text, re.IGNORECASE):
            response = client.chat_postMessage(channel=channel_id, text=CTO_DIRECT_INVITE, thread_ts=thread_ts)
            logger.info("LG유플러스 CTO 초대 요청에 대한 거절 메시지 전송")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message processed successfully'})
        }
    except SlackApiError as e:
        logger.error(f"Failed to send message: {e.response['error']}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Failed to send message: {e.response['error']}"})
        }
