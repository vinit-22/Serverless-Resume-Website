import json
import boto3

# Name of the DynamoDB table created in Step 2
TABLE_NAME = "VisitorCount"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Increments the visitor count in DynamoDB by 1 and returns the new count.
    Triggered by API Gateway on GET /count.
    """
    try:
        response = table.update_item(
            Key={"id": "counter"},
            UpdateExpression="ADD #c :incr",
            ExpressionAttributeNames={"#c": "count"},
            ExpressionAttributeValues={":incr": 1},
            ReturnValues="UPDATED_NEW",
        )

        new_count = int(response["Attributes"]["count"])

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
                "Content-Type": "application/json",
            },
            "body": json.dumps({"count": new_count}),
        }

    except Exception as e:
        print(f"Error updating visitor count: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": "Could not update visitor count"}),
        }
