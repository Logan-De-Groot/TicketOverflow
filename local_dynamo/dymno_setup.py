import boto3
import time

# Define the tables to be created
tables = [
    {
        'TableName': 'concerts',
        'KeySchema': [
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        'AttributeDefinitions': [
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    },
    {
        'TableName': 'tickets',
        'KeySchema': [
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        'AttributeDefinitions': [
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    },
    {
        'TableName': 'concerts_svg',
        'KeySchema': [
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        'AttributeDefinitions': [
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    },
    {
        'TableName': 'tickets_svg',
        'KeySchema': [
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        'AttributeDefinitions': [
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    }
]

# Create a DynamoDB resource
db = boto3.resource('dynamodb', endpoint_url="http://localhost:8000", region_name="us-east-1")

# Create the tables
for table in tables:
    db.create_table(
        TableName=table['TableName'],
        KeySchema=table['KeySchema'],
        AttributeDefinitions=table['AttributeDefinitions'],
        BillingMode=table['BillingMode']
    )

# Wait for the tables to be created
for table in tables:
    db.Table(table['TableName']).wait_until_exists()