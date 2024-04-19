# Import necessary libraries
import json
import boto3
from decimal import Decimal

# Initialize the Rekognition service client
rekognition_client = boto3.client('rekognition')
# Initialize the DynamoDB resource client
dynamodb = boto3.resource('dynamodb')

# Specify the DynamoDB table names
entry_table_name = 'EntriesTableS2110963'
vehicle_table_name = 'VehiclesTableS2110963'


def send_sns_message_with_subject(message, subject):
    # Create an SNS service client
    sns_client = boto3.client('sns')
    topic_arn = "arn:aws:sns:us-east-1:570018071531:MyTopicS2110963"
    try:
        # Publish the message with a subject to the specified SNS topic
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject
        )
        print(
            f"Message sent to SNS topic {topic_arn}. Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Failed to send message to SNS topic {topic_arn}: {e}")


def scan_vehicle_table(detected_text):
    table = dynamodb.Table(vehicle_table_name)
    response = table.scan()
    items = response['Items']
    match_found = False

    # Convert the detected text list to a single string
    detected_text_str = ' '.join(detected_text)

    for item in items:
        if item['vehiclecar_id'] in detected_text_str:
            if item['Blacklisted']:
                # Print a message for blacklisted vehicle
                print(
                    f"Blacklisted vehicle detected with vehiclecar_id: {item['vehiclecar_id']}")
                match_found = True
                # Send an SNS message for blacklisted vehicle
                send_sns_message_with_subject(
                    message=f"Blacklisted vehicle detected with vehiclecar_id: {item['vehiclecar_id']}",
                    subject="Blacklisted Vehicle Detected"
                )
            else:
                print(
                    f"Match found for vehiclecar_id: {item['vehiclecar_id']}, but it is not blacklisted.")
                match_found = True

    if not match_found:
        print("No match was found for the current entry.")

# Function to detect image labels using Amazon Rekognition
def detect_labels(images_name, bucket_name, max_labels=10, min_confidence=70):
    try:
        response = rekognition_client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': 'mybucket-s2110963',
                    'Name': images_name
                }
            },
            MaxLabels=max_labels,
            MinConfidence=min_confidence
        )
        return [{'Name': label['Name'], 'Confidence': Decimal(str(label['Confidence']))} for label in response['Labels']]
    except rekognition_client.exceptions.InvalidS3ObjectException as e:
        print(f"Invalid S3 object: {e}")
        return []
    except Exception as e:
        print(f"Failed to detect labels: {e}")
        return []

# Function to detect text in an image using Amazon Rekognition
def detect_text(images_name, bucket_name):
    try:
        response = rekognition_client.detect_text(
            Image={
                'S3Object': {
                    'Bucket': 'mybucket-s2110963',
                    'Name': images_name
                }
            }
        )
        return [text['DetectedText'] for text in response['TextDetections']]
    except rekognition_client.exceptions.InvalidS3ObjectException as e:
        print(f"Invalid S3 object: {e}")
        return []
    except Exception as e:
        print(f"Failed to detect text: {e}")
        return []

# Function to detect labels and text in an image
def detect_labels_and_text(images_name, bucket_name='mybucket-s2110963'):
    labels = detect_labels(images_name, bucket_name)
    detected_text = detect_text(images_name, bucket_name)
    return labels, detected_text

# Function to save the detected labels and text to the DynamoDB table
def save_to_dynamodb(images_name, labels, detected_text):
    """
    Saves the detected labels and texts to the specified DynamoDB table.
    """
    table = dynamodb.Table(entry_table_name)
    try:
        table.put_item(
            Item={
                'images_name': images_name,
                'Labels': labels,
                'DetectedText': detected_text
            }
        )
        print(f"Successfully saved data for {images_name} to DynamoDB.")
    except Exception as e:
        print(f"Failed to save data to DynamoDB: {e}")

# Function to process the SQS message
def process_sqs_message(event):
    try:
        # Extract the SQS message body
        sqs_body = event['Records'][0]['body']
        
        # Parse the SQS message body as JSON
        try:
            sqs_message = json.loads(sqs_body)
        except json.JSONDecodeError as e:
            print(f"Failed to parse SQS message body as JSON: {e}")
            return {
                'statusCode': 400,
                'body': 'Invalid SQS message format'
            }

        # Extract the S3 event from the SQS message
        s3_event = sqs_message['Records'][0]

        # Extract the image name from the S3 event
        images_name = s3_event['s3']['object']['key']

        # Print the S3 event and image name for debugging purposes
        print("SQS Message Body:", s3_event)
        print("Image Name:", images_name)

        # Perform image analysis on the uploaded image
        labels, detected_text = detect_labels_and_text(images_name, 'mybucket-s2110963')
        print("Labels:", labels)
        print("Detected Text:", detected_text)

        # Save the detected labels and texts to DynamoDB for future reference
        save_to_dynamodb(images_name, labels, detected_text)

        # Scan the vehicle table with the detected text to identify potential matches
        scan_vehicle_table(detected_text)

        # Print a success message to indicate the successful processing of the event
        print("Uploaded image file successfully")

        # Return a success response to indicate the successful processing of the event
        return {
            'statusCode': 200,
            'body': 'Message processing completed successfully'
        }
    except KeyError as e:
        print(f"Missing required key in SQS message: {e}")
        return {
            'statusCode': 400,
            'body': 'Missing required key in SQS message'
        }
    except Exception as e:
        print(f"Failed to process SQS message: {e}")
        return {
            'statusCode': 500,
            'body': 'Message processing failed'
        }

# Lambda function handler
def handler(event, context):
    # Process the SQS message
    return process_sqs_message(event)