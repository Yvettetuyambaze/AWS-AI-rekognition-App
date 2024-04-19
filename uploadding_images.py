# Import necessary libraries
import boto3
from dotenv import load_dotenv
import os
import time

# Load environment variables from a .env file
load_dotenv()

# Retrieve AWS credentials and session token from environment variables
access_key = os.environ.get('aws_access_key_id')
secret_key = os.environ.get('aws_secret_access_key')
session_key = os.environ.get('aws_session_token')

# Configure the S3 client with the retrieved AWS credentials and region information
s3 = boto3.client('s3', 
                  aws_access_key_id=access_key,
                  aws_secret_access_key=secret_key,
                  region_name='us-east-1',
                  aws_session_token=session_key)

# Configure the SQS client similar to S3 with credentials and region
sqs = boto3.client('sqs', 
                   aws_access_key_id=access_key,
                   aws_secret_access_key=secret_key,
                   region_name='us-east-1',
                   aws_session_token=session_key)

# Define directory to scan for images and the target bucket name
image_dir = 'Images'
bucket_name = 'mybucket-s2110963'

# Define the interval in seconds between uploads
upload_interval = 30

# Specify the URL of the SQS queue to which messages will be sent
queue_url = 'https://sqs.us-east-1.amazonaws.com/570018071531/MySQSQueueS2110963'

# Function to upload an image to S3
def upload_image_to_s3(file_path, bucket_name, file_name):
    try:
        with open(file_path, 'rb') as data:
            s3.upload_fileobj(data, bucket_name, file_name)
        print(f"Image Uploaded successful {file_name} to {bucket_name}")
        return True
    except Exception as e:
        print(f"Image Failed to upload {file_name} to {bucket_name}: {e}")
        return False

# Function to send a message to SQS
def send_sqs_message(queue_url, message_body):
    try:
        sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)
        print(f"Sent an SQS message: {message_body}")
    except Exception as e:
        print(f"Failed to send an SQS message: {e}")

# Main loop to handle uploading images and sending SQS messages
for file in os.listdir(image_dir):
    if file.endswith('.jpg') or file.endswith('.png'):
        file_path = os.path.join(image_dir, file)
        if upload_image_to_s3(file_path, bucket_name, file):
            message = {
                'bucket': bucket_name,
                'key': file
            }
            send_sqs_message(queue_url, str(message))
        time.sleep(upload_interval)  # Wait for the defined interval before processing next file
