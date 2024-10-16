import os
import requests
from flask import Flask, request, jsonify
from google.cloud import storage
from io import BytesIO
from werkzeug.datastructures import FileStorage
import mysql.connector
import logging
from dotenv import load_dotenv
from flask_cors import CORS
from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError


load_dotenv()

timeout = 5.0   



# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# MySQL Database configuration using environment variables
db_config = {                                               # Your MySQL username
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),                   # Your MySQL password 
    'port': os.getenv('DB_PORT'),                           #port whre auth cloud sql proxy is listening 
    'host': os.getenv('DB_HOST'),                           # Your Cloud SQL instance IP or 'localhost' for local MySQL
    'database': os.getenv('DB_NAME')                        # Your MySQL database name
}

# Function to get a database connection
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn




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


# Create a Google Cloud Storage client using hardcoded service account credentials
def get_storage_client():
    return storage.Client.from_service_account_info(SERVICE_ACCOUNT_INFO)


BUCKET_NAME = os.getenv('BUCKET_NAME')

def upload_to_gcs(file, bucket_name, destination_blob_name):
    """Uploads a file to the Google Cloud Storage bucket."""
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file, content_type=file.mimetype)
    return blob.public_url



@app.route('/upload-url', methods=['POST'])
def upload_from_url():
    data = request.get_json()
    if not data or 'image_url' not in data:
        return jsonify({"error": "Missing 'image_url' in request body"}), 400

    image_url = data['image_url']

    try:
        # Download the image from the provided URL
        response = requests.get(image_url)
        response.raise_for_status()  # Ensure the request was successful
        file = BytesIO(response.content)

        # Convert to a FileStorage object (Flask uses this for file handling)
        filename = image_url.split("/")[-1]
        file_storage = FileStorage(file, filename=filename, content_type=response.headers['Content-Type'])

        # Upload to Google Cloud Storage
        public_url = upload_to_gcs(file_storage, BUCKET_NAME, filename)

        # Insert the image details into the Cloud SQL database
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_image_query = (
            "INSERT INTO images (image_name, image_url) "
            "VALUES (%s, %s)"
        )
        cursor.execute(insert_image_query, (filename, public_url))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "File uploaded successfully", "public_url": public_url}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 400
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500

# Pub/Sub Subscriber Setup
subscriber = pubsub_v1.SubscriberClient()
subscription_path = os.getenv('SUBSCRIBER_NAME')

def pubsub_callback(message):
    """Callback function to process Pub/Sub messages."""
    print(f"Received message: {message.data.decode('utf-8')}")
    image_name = message.attributes.get('image_name')
    image_url = message.attributes.get('image_url')

    try:
        # Download the image from the URL
        response = requests.get(image_url)
        response.raise_for_status()
        file = BytesIO(response.content)

        # Convert to FileStorage for Flask
        file_storage = FileStorage(file, filename=image_name, content_type=response.headers['Content-Type'])

        # Upload to Google Cloud Storage
        public_url = upload_to_gcs(file_storage, BUCKET_NAME, image_name)

        # Insert image details into MySQL database
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_image_query = (
            "INSERT INTO images (image_name, image_url) "
            "VALUES (%s, %s)"
        )
        cursor.execute(insert_image_query, (image_name, public_url))
        conn.commit()

        cursor.close()
        conn.close()

        print(f"Image '{image_name}' uploaded successfully.")
        message.ack()  # Acknowledge the message

    except requests.exceptions.RequestException as e:
        print(f"Failed to download image: {e}")
        message.nack()  # Retry message
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        message.nack()  # Retry message

@app.route('/start-subscriber', methods=['POST'])
def start_subscriber():
    """Endpoint to start Pub/Sub subscription."""
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=pubsub_callback)
    print(f"Listening for messages on {subscription_path}...")

    # Keep the subscription active in the background
    try:
        streaming_pull_future.result()
    except TimeoutError:
        streaming_pull_future.cancel()
        print("Subscription cancelled.")
    
    return jsonify({"message": "Subscriber started"}), 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
