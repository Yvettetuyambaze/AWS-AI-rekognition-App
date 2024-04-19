# Import necessary libraries
import boto3
import time
from botocore.exceptions import ClientError

# Initialize the Boto3 clients for EC2 and S3 services
ec2_client = boto3.client('ec2')
s3 = boto3.client('s3')

# Check if EC2 instance already exists
def ec2_instance_exists(name):
    response = ec2_client.describe_instances(Filters=[
        {'Name': 'tag:Name', 'Values': [name]}
    ])
    return len(response['Reservations']) > 0

# Check if S3 bucket already exists
def s3_bucket_exists(name):
    response = s3.list_buckets()
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    return name in buckets

# Step 1: Create an EC2 instance with specified tags
ec2_parameters = {
    'ImageId': 'ami-0cf43e890af9e3351',
    'InstanceType': 't2.micro',
    'MinCount': 1,
    'MaxCount': 1,
    'KeyName': 'vockey',
    'TagSpecifications': [
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'MyEC2InstanceNames2110963'
                }
            ]
        }
    ]
}

if not ec2_instance_exists('MyEC2InstanceNames2110963'):
    try:
        # Attempt to launch the EC2 instance with the specified parameters
        response = ec2_client.run_instances(**ec2_parameters)
        instance_id = response['Instances'][0]['InstanceId']
        print(f"EC2 instance was created successfully with the ID: {instance_id}")
    except Exception as e:
        print(f"Error creating EC2 instance please try again: {str(e)}")
else:
    print("EC2 instance already exists. Skipping creation.")

# Pause for 1 second to ensure compliance with AWS API rate limits.
time.sleep(1)

# Step 2: Create an S3 bucket
def create_s3_bucket(bucket_name):
    if not s3_bucket_exists(bucket_name):
        try:
            response = s3.create_bucket(Bucket=bucket_name)
            print(f"Bucket {bucket_name} was created successfully.")
        except Exception as e:
            print(f"Oops, there's an error while creating bucket: {e}")
    else:
        print(f"Bucket {bucket_name} already exists. Skipping creation.")

# Example usage: Create a new S3 bucket
bucket_name = 'mybucket-s2110963'
create_s3_bucket(bucket_name)

# Pause for 1 second to ensure compliance with AWS API rate limits.
time.sleep(1)

# Queue ARN (Replace with a valid queue ARN)
queue_arn = 'arn:aws:sqs:us-east-1:570018071531:MySQSQueueS2110963'

# Step 3: Set up the notification configuration for the S3 bucket
def setup_s3_notification(bucket_name, queue_arn):
    try:
        response = s3.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration={
                'QueueConfigurations': [
                    {
                        'QueueArn': queue_arn,
                        'Events': ['s3:ObjectCreated:*'],
                    }
                ]
            }
        )
        print(f"Notification configuration set up for bucket {bucket_name}.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidArgument':
            print(f"Error setting up notification configuration: Invalid argument.")
        elif error_code == 'AccessDenied':
            print(f"Error setting up notification configuration: Access denied. Check your AWS account permissions.")
        else:
            print(f"Error setting up notification configuration: {e}")

# Set up the notification configuration for the created S3 bucket
setup_s3_notification(bucket_name, queue_arn)

