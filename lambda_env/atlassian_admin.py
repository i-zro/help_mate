import boto3
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret
    except Exception as e:
        logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
        raise e

def add_user_to_group(account_id, group_id):
    secrets = get_secret('confluence_credentials')
    add_user_url = secrets['CONFLUENCE_ADD_USER_URL'].format(group_id=group_id)
    headers = {"Accept": "application/json"}
    data = {"accountId": account_id}
    response = requests.post(add_user_url, headers=headers, json=data, auth=HTTPBasicAuth(secrets['CONFLUENCE_USERNAME'], secrets['CONFLUENCE_API_TOKEN']), verify=False)

    if response.status_code == 201:
        logger.info("User added to group successfully.")
        return True
    else:
        logger.error(f"Failed to add user to group. Status code: {response.status_code}, Response: {response.text}")
        return False