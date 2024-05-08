import json
import boto3
from botocore.exceptions import ClientError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from common_messages import DX_TOOL_GUIDE_MESSAGE

def get_secret():
    secret_name = "slack_bot_token"
    region_name = "ap-northeast-2"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error("Failed to retrieve secret: %s", e)
        raise e

    return response['SecretString']

def lambda_handler(event, context):
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

    event_type = body['event'].get('type')
    channel_id = body['event'].get('channel')
    message_text = body['event'].get('text', '')  # Slack에서 보내진 메시지 텍스트

    if event_type == 'message_deleted':
        logger.info("Received a message_deleted event, ignoring.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message delete event received, no action taken'})
        }

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
    
    try:
        # LG유플러스 CTO에 대한 요청일 경우 거절 메시지 전송
        if '님이 LG유플러스 CTO에 한 사람을 초대하도록 요청했습니다.' in message_text.lower():
            response = client.chat_postMessage(channel=channel_id, text="죄송하지만 LG유플러스 CTO님은 현재 초대가 어렵습니다.")
            logger.info("LG유플러스 CTO 초대 요청에 대한 거절 메시지 전송")
        else:
            response = client.chat_postMessage(channel=channel_id, text="oktahelper", thread_ts=thread_ts)
            logger.info("Oktahelper response sent successfully")
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

