import json
import boto3
from botocore.exceptions import ClientError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def get_secret():
    secret_name = "slack_bot_token"
    region_name = "ap-northeast-2"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e

    return response['SecretString']

def lambda_handler(event, context):
    print("Received event:", event)
    try:
        body = json.loads(event['body'])
    except KeyError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Bad Request: Missing body'})
        }

    # 메시지 이벤트에서 봇 자신이 보낸 메시지인지 확인
    if 'user' in body['event'] and body['event']['user'] == 'U06G2F3SND6':
        print("Ignoring bot's own message")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Ignored bot message'})
        }

    channel_id = body['event']['channel']
    thread_ts = body['event']['ts']

    secret = get_secret()
    if not secret:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to get Slack token'})
        }
    secrets = json.loads(secret)
    slack_token = secrets['SLACK_TOKEN']
    client = WebClient(token=slack_token)

    try:
        response = client.chat_postMessage(channel=channel_id, text='확인', thread_ts=thread_ts)
    except SlackApiError as e:
        print(f"Error sending message: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to send message'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Message sent successfully'})
    }