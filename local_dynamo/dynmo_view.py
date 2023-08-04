import boto3

# # Create a DynamoDB client
# dynamodb = boto3.client('dynamodb', endpoint_url="http://localhost:8000", region_name="us-east-1")

# # List all tables
# table_list = dynamodb.list_tables()['TableNames']

# # Print the table names
# for table_name in table_list:
#     print(table_name)


sqs = boto3.client('sqs', endpoint_url="http://localhost:9324",  region_name="us-east-1")

sqs.create_queue(QueueName = "tickets")
sqs.create_queue(QueueName = "concerts")