import json

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

    # Slack challenge 요청 응답
    if 'challenge' in body:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'challenge': body['challenge']})
        }
    else:
        # challenge 필드가 없는 경우의 처리
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Bad Request: Missing challenge field'})
        }
