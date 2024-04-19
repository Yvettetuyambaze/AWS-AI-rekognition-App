# Import necessary libraries
import boto3
from dotenv import load_dotenv
import os

# Load environment variables from a .env file, which stores sensitive information securely
load_dotenv()

# Retrieve AWS credentials and session token from environment variables for secure API access
access_key = os.environ.get('aws_access_key_id')
secret_key = os.environ.get('aws_secret_access_key')
session_token = os.environ.get('aws_session_token')

# Initialize the SNS client with the retrieved AWS credentials and specify the region
sns_client = boto3.client('sns',
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key,
                          region_name='us-east-1',
                          aws_session_token=session_token)

# Define the name of the SNS topic to be created
topic_name = 'MyTopicS2110963'

# Function to create an SNS topic and return its ARN
def create_sns_topic(topic_name):
    try:
        # Attempt to create the topic and capture the response
        response = sns_client.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']  # Extract the topic ARN from the response
        print(f'SNS Topic {topic_name} created successfully. ARN: {topic_arn}')
        return topic_arn
    except Exception as e:
        # Handle exceptions that occur during topic creation
        print(f'Failed while creating SNS topic {topic_name}: {e}')
        return None

# Function to subscribe an endpoint to an SNS topic
def subscribe_to_topic(topic_arn, protocol, endpoint):
    try:
        # Attempt to subscribe the specified endpoint to the topic
        response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol=protocol,  # Communication protocol, e.g., 'email'
            Endpoint=endpoint   # Receiver's endpoint, such as an email address
        )
        subscription_arn = response['SubscriptionArn']  # Extract the subscription ARN
        print(f'Subscribed sucessfully  {endpoint} to SNS topic {topic_arn}. Your Subscription ARN: {subscription_arn}')
    except Exception as e:
        # Handle exceptions that occur during subscription
        print(f'Oopps failed to subscribe to SNS topic {topic_arn}: {e}')

# Main execution block: Attempt to create the SNS topic
topic_arn = create_sns_topic(topic_name)

# If the topic is successfully created, proceed to subscribe to the topic
if topic_arn:
    # Subscribe the user's email to the newly created SNS topic
    subscribe_to_topic(topic_arn, 'email', 'y.tuyambaze@alustudent.com')
