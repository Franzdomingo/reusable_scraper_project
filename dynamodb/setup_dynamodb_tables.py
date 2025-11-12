"""
Setup DynamoDB tables for LLM Metadata Scraper
Run this script to create all necessary tables in DynamoDB Local or AWS
"""

import boto3
from botocore.exceptions import ClientError


def get_dynamodb_resource(local=True):
    """
    Get DynamoDB resource - local or AWS

    Args:
        local: If True, connects to DynamoDB Local on localhost:8000
    """
    if local:
        return boto3.resource(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='fakeAccessKeyId',
            aws_secret_access_key='fakeSecretAccessKey'
        )
    else:
        # For AWS deployment
        return boto3.resource('dynamodb', region_name='us-east-1')


def create_models_table(dynamodb):
    """Create the main Models table"""
    table_name = 'Models'

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'N'  # Number
                },
                {
                    'AttributeName': 'slug',
                    'AttributeType': 'S'  # String
                },
                {
                    'AttributeName': 'author',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'slug-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'slug',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'author-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'author',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        print(f"Creating table {table_name}...")
        table.wait_until_exists()
        print(f"✓ Table {table_name} created successfully")
        return table

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table {table_name} already exists")
        else:
            print(f"✗ Error creating table {table_name}: {e}")
            raise


def create_instances_table(dynamodb):
    """Create the Instances table (model variations/versions)"""
    table_name = 'Instances'

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'slug',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'model_id',
                    'AttributeType': 'N'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'slug-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'slug',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'model_id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'model_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        print(f"Creating table {table_name}...")
        table.wait_until_exists()
        print(f"✓ Table {table_name} created successfully")
        return table

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table {table_name} already exists")
        else:
            print(f"✗ Error creating table {table_name}: {e}")
            raise


def create_tags_table(dynamodb):
    """Create the Tags table"""
    table_name = 'Tags'

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'ref',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'ref',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'name-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'name',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        print(f"Creating table {table_name}...")
        table.wait_until_exists()
        print(f"✓ Table {table_name} created successfully")
        return table

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table {table_name} already exists")
        else:
            print(f"✗ Error creating table {table_name}: {e}")
            raise


def list_tables(dynamodb):
    """List all tables in DynamoDB"""
    client = dynamodb.meta.client
    response = client.list_tables()
    return response.get('TableNames', [])


def delete_all_tables(dynamodb):
    """Delete all tables (use with caution!)"""
    tables = list_tables(dynamodb)

    if not tables:
        print("No tables to delete")
        return

    print(f"\nFound {len(tables)} tables: {', '.join(tables)}")
    confirm = input("Are you sure you want to delete all tables? (yes/no): ")

    if confirm.lower() == 'yes':
        for table_name in tables:
            try:
                table = dynamodb.Table(table_name)
                table.delete()
                print(f"✓ Deleted table {table_name}")
            except ClientError as e:
                print(f"✗ Error deleting table {table_name}: {e}")
    else:
        print("Deletion cancelled")


def main():
    """Main function to setup all tables"""
    import argparse

    parser = argparse.ArgumentParser(description='Setup DynamoDB tables for LLM Metadata Scraper')
    parser.add_argument('--aws', action='store_true', help='Use AWS DynamoDB instead of local')
    parser.add_argument('--list', action='store_true', help='List all tables')
    parser.add_argument('--delete-all', action='store_true', help='Delete all tables (use with caution!)')

    args = parser.parse_args()

    # Connect to DynamoDB
    dynamodb = get_dynamodb_resource(local=not args.aws)

    if args.aws:
        print("Connecting to AWS DynamoDB...")
    else:
        print("Connecting to DynamoDB Local (http://localhost:8000)...")

    # List tables
    if args.list:
        tables = list_tables(dynamodb)
        if tables:
            print(f"\nExisting tables ({len(tables)}):")
            for table_name in tables:
                print(f"  - {table_name}")
        else:
            print("\nNo tables found")
        return

    # Delete all tables
    if args.delete_all:
        delete_all_tables(dynamodb)
        return

    # Create tables
    print("\n=== Creating DynamoDB Tables ===\n")

    try:
        create_models_table(dynamodb)
        create_instances_table(dynamodb)
        create_tags_table(dynamodb)

        print("\n=== Table Creation Complete ===")
        print("\nCreated tables:")
        for table_name in list_tables(dynamodb):
            print(f"  - {table_name}")

    except Exception as e:
        print(f"\n✗ Error during table creation: {e}")
        raise


if __name__ == '__main__':
    main()
