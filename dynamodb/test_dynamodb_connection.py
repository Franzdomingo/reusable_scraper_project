"""
Test DynamoDB connection - local or AWS
Verifies connectivity and lists available tables
"""

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
import sys


def test_dynamodb_connection(local=True, access_key=None, secret_key=None):
    """
    Test connection to DynamoDB

    Args:
        local: If True, connects to DynamoDB Local on localhost:8000
        access_key: AWS Access Key ID (optional for local)
        secret_key: AWS Secret Access Key (optional for local)
    """
    try:
        if local:
            print("Testing connection to DynamoDB Local (http://localhost:8000)...")

            # For local DynamoDB, credentials can be fake or use provided ones
            if access_key and secret_key:
                dynamodb = boto3.resource(
                    'dynamodb',
                    endpoint_url='http://localhost:8000',
                    region_name='us-east-1',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key
                )
            else:
                dynamodb = boto3.resource(
                    'dynamodb',
                    endpoint_url='http://localhost:8000',
                    region_name='us-east-1',
                    aws_access_key_id='fakeAccessKeyId',
                    aws_secret_access_key='fakeSecretAccessKey'
                )
        else:
            print("Testing connection to AWS DynamoDB...")
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Test connection by listing tables
        client = dynamodb.meta.client
        response = client.list_tables()

        print("✓ Connection successful!")
        print(f"\nDynamoDB Info:")
        print(f"  Endpoint: {'http://localhost:8000' if local else 'AWS DynamoDB'}")
        print(f"  Region: us-east-1")

        # List tables
        tables = response.get('TableNames', [])
        if tables:
            print(f"\nFound {len(tables)} table(s):")
            for table_name in tables:
                table = dynamodb.Table(table_name)
                try:
                    # Get table details
                    table.load()
                    item_count = table.item_count
                    status = table.table_status
                    print(f"  - {table_name}")
                    print(f"      Status: {status}")
                    print(f"      Items: {item_count}")

                    # Show key schema
                    key_schema = table.key_schema
                    partition_key = [k['AttributeName'] for k in key_schema if k['KeyType'] == 'HASH'][0]
                    print(f"      Partition Key: {partition_key}")

                except ClientError as e:
                    print(f"  - {table_name} (error loading details: {e})")
        else:
            print("\n⚠ No tables found")
            print("  Run 'python setup_dynamodb_tables.py' to create tables")

        return True

    except EndpointConnectionError:
        print("✗ Connection failed!")
        print("\nPossible issues:")
        if local:
            print("  1. DynamoDB Local is not running")
            print("  2. DynamoDB Local is running on a different port")
            print("\nTo start DynamoDB Local:")
            print("  cd C:\\Users\\orste\\Downloads\\dynamodb_local_latest")
            print('  java -D"java.library.path=./DynamoDBLocal_lib" -jar DynamoDBLocal.jar -sharedDb')
        else:
            print("  1. No internet connection")
            print("  2. AWS credentials not configured")
            print("  3. Wrong region")
        return False

    except ClientError as e:
        print(f"✗ DynamoDB error: {e}")
        print(f"\nError code: {e.response['Error']['Code']}")
        print(f"Error message: {e.response['Error']['Message']}")
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_table_operations(local=True):
    """Test basic table operations (read/write)"""
    try:
        if local:
            dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url='http://localhost:8000',
                region_name='us-east-1',
                aws_access_key_id='jqin3h',
                aws_secret_access_key='bgb8ki'
            )
        else:
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        print("\n=== Testing Table Operations ===\n")

        # Check if Models table exists
        tables = dynamodb.meta.client.list_tables()['TableNames']
        if 'Models' not in tables:
            print("⚠ Models table not found. Create tables first with:")
            print("  python setup_dynamodb_tables.py")
            return False

        # Test write operation
        table = dynamodb.Table('Models')
        print("Testing write operation...")

        test_item = {
            'id': 999999,
            'ref': 'test/model',
            'title': 'Test Model',
            'slug': 'test-model',
            'author': 'test-author',
            'description': 'This is a test model',
            'url': 'https://example.com/test-model'
        }

        table.put_item(Item=test_item)
        print("✓ Write successful")

        # Test read operation
        print("Testing read operation...")
        response = table.get_item(Key={'id': 999999})

        if 'Item' in response:
            print("✓ Read successful")
            print(f"\nRetrieved item:")
            print(f"  Title: {response['Item']['title']}")
            print(f"  Author: {response['Item']['author']}")

            # Clean up test item
            table.delete_item(Key={'id': 999999})
            print("✓ Test item deleted")

            return True
        else:
            print("✗ Read failed - item not found")
            return False

    except ClientError as e:
        print(f"✗ Table operation error: {e}")
        return False


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Test DynamoDB connection')
    parser.add_argument('--aws', action='store_true', help='Test AWS DynamoDB instead of local')
    parser.add_argument('--test-ops', action='store_true', help='Test read/write operations')
    parser.add_argument('--access-key', default='jqin3h', help='AWS Access Key ID')
    parser.add_argument('--secret-key', default='bgb8ki', help='AWS Secret Access Key')

    args = parser.parse_args()

    print("=== DynamoDB Connection Test ===\n")

    # Test connection
    success = test_dynamodb_connection(
        local=not args.aws,
        access_key=args.access_key,
        secret_key=args.secret_key
    )

    if not success:
        sys.exit(1)

    # Test operations if requested
    if args.test_ops:
        test_table_operations(local=not args.aws)

    print("\n=== Test Complete ===")


if __name__ == '__main__':
    main()
