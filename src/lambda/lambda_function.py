import json
import os
import uuid
from datetime import datetime

import boto3

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

DEST_BUCKET = os.environ.get("DEST_BUCKET")
TABLE_NAME = os.environ.get("TABLE_NAME")

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Triggered by an S3 ObjectCreated event.

    Workflow:
    1. Read bucket and object key from the event.
    2. Copy the object to a processed S3 bucket.
    3. Store metadata in DynamoDB.
    4. Log execution details to CloudWatch.
    """

    print("Received event:")
    print(json.dumps(event, indent=2))

    try:
        record = event["Records"][0]
        source_bucket = record["s3"]["bucket"]["name"]
        source_key = record["s3"]["object"]["key"]

        image_id = str(uuid.uuid4())
        original_file_name = source_key.split("/")[-1]
        processed_key = f"processed-{original_file_name}"

        print(f"Source bucket: {source_bucket}")
        print(f"Source key: {source_key}")
        print(f"Destination bucket: {DEST_BUCKET}")
        print(f"Processed key: {processed_key}")

        # Copy the file to the processed bucket
        s3.copy_object(
            CopySource={
                "Bucket": source_bucket,
                "Key": source_key,
            },
            Bucket=DEST_BUCKET,
            Key=processed_key,
        )

        print("File successfully copied to processed bucket.")

        # Store metadata in DynamoDB
        timestamp = datetime.utcnow().isoformat() + "Z"

        item = {
            "imageId": image_id,
            "originalFileName": original_file_name,
            "originalBucket": source_bucket,
            "processedBucket": DEST_BUCKET,
            "originalKey": source_key,
            "processedKey": processed_key,
            "processedAt": timestamp,
        }

        table.put_item(Item=item)

        print("Metadata written to DynamoDB:")
        print(item)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "File processed successfully",
                    "imageId": image_id,
                }
            ),
        }

    except Exception as error:
        print("ERROR during processing:")
        print(str(error))

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": str(error),
                }
            ),
        }
