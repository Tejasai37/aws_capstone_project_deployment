import os
import sys
import boto3
from moto import mock_aws

# Mock Credentials (must be set before imports)
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_SESSION_TOKEN'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Start Moto Mock (intercepts all boto3 calls)
mock = mock_aws()
mock.start()

# Import App (after mock setup)
from app_aws import app
import app_aws

def setup_infrastructure():
    print(">>> Creating Mocked AWS Resources (DynamoDB Tables & SNS)...")
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    sns = boto3.client('sns', region_name='us-east-1')

    # Tables matches what app_aws.py expects
    tables = ['Users', 'AdminUsers', 'Projects', 'Enrollments']
    
    # Tables have different keys
    # Users: username
    dynamodb.create_table(
        TableName='Users',
        KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )
    # AdminUsers: username
    dynamodb.create_table(
        TableName='AdminUsers',
        KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )
    # Projects: id
    dynamodb.create_table(
        TableName='Projects',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )
    # Enrollments: username
    dynamodb.create_table(
        TableName='Enrollments',
        KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    # SNS
    response = sns.create_topic(Name='aws_capstone_topic')
    app_aws.SNS_TOPIC_ARN = response['TopicArn']
    
    print(f">>> Mock Environment Ready. SNS Topic ARN: {app_aws.SNS_TOPIC_ARN}")

if __name__ == '__main__':
    try:
        setup_infrastructure()
        print("\n>>> Starting Flask Server at http://localhost:5000")
        print(">>> Stop with CTRL+C. Mock data will be lost on exit.")
        # use_reloader=False prevents spawning a new process that loses mock state
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    finally:
        mock.stop()
