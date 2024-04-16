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
        print("body:", body)
    except KeyError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Bad Request: Missing body'})
        }

    # 메시지 이벤트에서 봇 자신이 보낸 메시지인지 확인
    if 'bot_id' in body['event']:
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Ignored bot message'})
        }

    else:
        # 스레드 메시지 중 최상위 메시지만 처리
        event_ts = body['event'].get('ts')
        thread_ts = body['event'].get('thread_ts', event_ts)
    
        if thread_ts != event_ts:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Ignored sub-thread message'})
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

        message_text = (
            "*문의 전 채널 상단에 있는 'DX협업툴 가이드'를 꼭 참고해 주세요.*\n"
            "DX협업툴(Jira, Confluence) 사용 중 단순 문의나 오류 발생 시, 다음의 기술지원 센터를 통해 1차 기술 지원을 활용해 주세요:\n"
            "<https://sweplateer.atlassian.net/servicedesk/customer/portal/34|기술지원 센터> (SEN Number: SEN-23769245)\n"
            "관리자 권한이 필요한 업무들은 해당 채널에 남겨주시면 지원하도록 하겠습니다.\n"
            "(요청사항은 가급적 개인DM, 메일, 전화 연락보다는 채널 활용 부탁드립니다.)\n"
            "Okta 관련 문의는 <mailto:oktahelper@lguplus.co.kr|oktahelper@lguplus.co.kr>로 문의 주세요."
        )

        try:
            response = client.chat_postMessage(channel=channel_id, text=message_text, thread_ts=thread_ts)
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
