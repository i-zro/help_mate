import json
import boto3
from botocore.exceptions import ClientError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def get_secret():
    secret_name = "slack_bot_token"
    region_name = "ap-northeast-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    return get_secret_value_response['SecretString']

    # Your code goes here.

# challenge 확인용 코드
# def lambda_handler(event, context):
#     # API Gateway의 HTTP 요청 처리를 위해 이벤트 구조 확인
#     print("Received event:", event)  # 로그에 입력 이벤트 출력
#     try:
#         body = json.loads(event['body'])
#     except KeyError:
#         # event['body']가 없는 경우, 적절한 JSON 응답 반환
#         return {
#             'statusCode': 400,
#             'headers': {'Content-Type': 'application/json'},
#             'body': json.dumps({'error': 'Bad Request: Missing body'})
#         }

#     # Slack challenge 요청 응답
#     if 'challenge' in body:
#         return {
#             'statusCode': 200,
#             'headers': {'Content-Type': 'application/json'},
#             'body': json.dumps({'challenge': body['challenge']})
#         }
#     else:
#         # challenge 필드가 없는 경우의 처리
#         return {
#             'statusCode': 400,
#             'headers': {'Content-Type': 'application/json'},
#             'body': json.dumps({'error': 'Bad Request: Missing challenge field'})
#         }

def lambda_handler(event, context):
    # API Gateway의 HTTP 요청 처리를 위해 이벤트 구조 확인
    print("Received event:", event)  # 로그에 입력 이벤트 출력
    try:
        body = json.loads(event['body'])
    except KeyError:
        # event['body']가 없는 경우, 적절한 JSON 응답 반환
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Bad Request: Missing body'})
        }

    # Slack에서 보낸 이벤트의 채널 ID를 추출
    channel_id = body['event']['channel']

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
        # 받은 이벤트의 채널로 응답 메시지 보내기
        response = client.chat_postMessage(
            channel=channel_id,
            text='확인'
        )
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