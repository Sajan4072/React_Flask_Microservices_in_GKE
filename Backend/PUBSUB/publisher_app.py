import os 
from google.cloud import pubsub_v1
from dotenv import load_dotenv
# Load environment variables from the .env file in the app directory
load_dotenv(dotenv_path='../app/.env')


SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": os.getenv('GCS_PROJECT_ID'),
    "private_key_id": os.getenv('GCS_PRIVATE_KEY_ID'),
    "private_key": os.getenv('GCS_PRIVATE_KEY').replace('\\n', '\n'),  # Handle newline characters in private key
    "client_email": os.getenv('GCS_CLIENT_EMAIL'),
    "client_id": os.getenv('GCS_CLIENT_ID'),
    "auth_uri": os.getenv('GCS_AUTH_URI'),
    "token_uri": os.getenv('GCS_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('GCS_AUTH_PROVIDER_CERT_URL'),
    "client_x509_cert_url": os.getenv('GCS_CLIENT_CERT_URL'),
}

publisher = pubsub_v1.PublisherClient()
topic_path = os.getenv('TOPIC_NAME')


data = 'New Images are ready'
data = data.encode('utf-8')
attributes = {
    'image_name': 'urban-balcony-gardens-stockcake.jpg',
    'image_url': 'https://images.stockcake.com/public/0/2/f/02f028f2-3e38-41cd-aeba-877109361ba8_large/urban-balcony-gardens-stockcake.jpg' 
}

future = publisher.publish(topic_path, data, **attributes)
print(f'published message id {future.result()}')
  
