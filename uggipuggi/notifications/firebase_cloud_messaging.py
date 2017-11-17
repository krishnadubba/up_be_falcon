import requests
from oauth2client.service_account import ServiceAccountCredentials
from constants import GCLOUD_SERVICE_CREDS, FCM_SERVER_KEY


def _get_access_token():
    """Retrieve a valid access token that can be used to authorize requests.

    :return: Access token.
    """
    FCM_SCOPE = ['https://www.googleapis.com/auth/firebase.messaging']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
                                     GCLOUD_SERVICE_CREDS, FCM_SCOPE)
    access_token_info = credentials.get_access_token()
    return access_token_info.access_token

def send_notification(registration_id, message, fcm_rest_url='https://fcm.googleapis.com/fcm/send'):
    headers = {
        'Authorization': 'Bearer ' + _get_access_token(),
        'Content-Type': 'application/json; UTF-8',
    }
    message_body = {
                    "to" : registration_id,
                    "data" : message
                   }    
    res = requests.post(fcm_rest_url, headers=headers, json=message_body)