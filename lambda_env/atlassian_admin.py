import boto3
import json
import logging
import requests
from requests.auth import HTTPBasicAuth

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

def add_user_to_group(account_id, group_name):
    secrets = get_secret('confluence_credentials')
    if group_name == "confluence":
        group_id = secrets['CONFLUENCE_TEMPO_ADMIN_GROUP']
    elif group_name == "jira":
        group_id = secrets['JIRA_TEMPO_ADMIN_GROUP']
    else:
        raise ValueError(f"Unsupported group_name: {group_name}")
    add_user_url = secrets['CONFLUENCE_ADD_USER_URL'].format(group_id=group_id)
    headers = {"Accept": "application/json"}
    data = {"accountId": account_id}
    
    # Log the URL, headers, and data
    logger.info(f"URL: {add_user_url}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Data: {data}")
    logger.info(f"group_id: {group_name}")

    response = requests.post(add_user_url, headers=headers, json=data, auth=HTTPBasicAuth(secrets['CONFLUENCE_USERNAME'], secrets['CONFLUENCE_API_TOKEN']))

    if response.status_code == 201:
        logger.info("User added to group successfully.")
        return True
    else:
        logger.error(f"Failed to add user to group. Status code: {response.status_code}, Response: {response.text}")
        return False
        
def search_user_by_email(email):
    secrets = get_secret('confluence_credentials')
    search_url = secrets['CONFLUENCE_SEARCH_URL']
    params = {"query": email}
    headers = {"Accept": "application/json"}
    response = requests.get(search_url, headers=headers, params=params,
                            auth=HTTPBasicAuth(secrets['CONFLUENCE_USERNAME'], secrets['CONFLUENCE_API_TOKEN']))

    if response.status_code == 200:
        users = response.json()
        if users:
            account_id = users[0]['accountId']
            logger.info(f"Found user with account ID: {account_id}")
            return account_id
        else:
            logger.info("No user found with the given email address.")
            return None
    else:
        logger.error(f"Failed to search user. Status code: {response.status_code}")
        logger.error(response.text)
        return None
