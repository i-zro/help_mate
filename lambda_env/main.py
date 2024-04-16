import json
 
def lambda_handler(event, context):
    body = json.loads(event['body'])
    
    # Challenge 요청을 확인하고 응답
    if 'challenge' in body:
        return {
            'statusCode': 200,
            'body': json.dumps({'challenge': body['challenge']})
        }