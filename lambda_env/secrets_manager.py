import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name="ap-northeast-2"):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        logger = setup_logger()
        logger.error("Failed to retrieve secret: %s", e)
        raise e

