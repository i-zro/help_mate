import json

def lambda_handler(event, context):
    body = json.loads(event['body'])
    
    if 'challenge' in body:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'challenge': body['challenge']})
        }
