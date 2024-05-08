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
