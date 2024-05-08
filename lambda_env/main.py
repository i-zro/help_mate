import json
import boto3
from botocore.exceptions import ClientError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
import re
from common_messages import *
from boto3.dynamodb.conditions import Key

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

def check_event(event_ts):
    dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
    table_name = 'SlackEvents'
    table = dynamodb.Table(table_name)

    try:
        response = table.get_item(Key={'event_ts': event_ts})
    except ClientError as e:
        logger.error(f"Error accessing DynamoDB: {e}")
        raise e

    return 'Item' in response

def store_event(event_ts):
    dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
    table_name = 'SlackEvents'
    table = dynamodb.Table(table_name)

    try:
        table.put_item(Item={'event_ts': event_ts})
    except ClientError as e:
        logger.error(f"Error storing event in DynamoDB: {e}")
        raise e

def create_table_if_not_exists():
    dynamodb = boto3.client('dynamodb', region_name='ap-northeast-2')
    table_name = 'SlackEvents'
    try:
        dynamodb.describe_table(TableName=table_name)
    except dynamodb.exceptions.ResourceNotFoundException:
        # 테이블이 존재하지 않으면 생성
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': 'event_ts', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'event_ts', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        logger.info(f"Table {table_name} created successfully.")
        # 테이블 생성 후 활성화될 때까지 대기
        dynamodb.get_waiter('table_exists').wait(TableName=table_name)

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

    event_ts = body['event'].get('ts')
    create_table_if_not_exists()
    if check_event(event_ts):
        logger.info("Duplicate event detected, ignoring...")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Duplicate event ignored'})
        }
    store_event(event_ts)

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
