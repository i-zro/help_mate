import boto3
from botocore.exceptions import ClientError

class DynamoDBManager:
    def __init__(self, region_name='ap-northeast-2'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.region_name = region_name # Ensure this attribute is set
        self.table_name = 'SlackEvents'

    def check_event(self, event_ts):
        table = self.dynamodb.Table(self.table_name)
        try:
            response = table.get_item(Key={'event_ts': event_ts})
            return 'Item' in response
        except ClientError as e:
            logger = setup_logger()
            logger.error(f"Error accessing DynamoDB: {e}")
            raise e

    def store_event(self, event_ts):
        table = self.dynamodb.Table(self.table_name)
        try:
            table.put_item(Item={'event_ts': event_ts})
        except ClientError as e:
            logger = setup_logger()
            logger.error(f"Error storing event in DynamoDB: {e}")
            raise e

    def create_table_if_not_exists(self):
        client = boto3.client('dynamodb', region_name='ap-northeast-2')
        try:
            client.describe_table(TableName=self.table_name)
        except client.exceptions.ResourceNotFoundException:
            # 테이블 생성
            client.create_table(
                TableName=self.table_name,
                KeySchema=[{'AttributeName': 'event_ts', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'event_ts', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            logger = setup_logger()
            logger.info(f"Table {self.table_name} created successfully.")
            client.get_waiter('table_exists').wait(TableName=self.table_name)


