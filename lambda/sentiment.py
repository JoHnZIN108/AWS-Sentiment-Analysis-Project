import boto3
import json
import base64
import os
import uuid
from decimal import Decimal  # Import Decimal

# Initialize AWS clients
comprehend = boto3.client('comprehend')
dynamodb = boto3.resource('dynamodb')

# Getting the DynamoDB table name from environment variable
sentiment_table_name = os.environ['SENTIMENT_TABLE_NAME']
sentiment_table = dynamodb.Table(sentiment_table_name)

def lambda_handler(event, context):
    for record in event['Records']:
        # Decode the base64-encoded Kinesis data
        data = json.loads(base64.b64decode(record['kinesis']['data']).decode('utf-8'))

        # Perform sentiment analysis
        response = comprehend.detect_sentiment(
            Text=data['text'],
            LanguageCode='en'
        )

        # Extract sentiment and sentiment score
        sentiment = response['Sentiment']
        sentiment_score = response['SentimentScore']

        # Log the results
        print(f"Processed comment: {data['text']}")
        print(f"Sentiment: {sentiment}, Sentiment Score: {sentiment_score}")

        # Unique ID for the entry in DynamoDB
        sentiment_id = str(uuid.uuid4())

        # Store the results in DynamoDB
        sentiment_table.put_item(
            Item={
                'id': sentiment_id,
                'comment': data['text'],
                'likes_count': data.get('likes_count', 0),
                'sentiment': sentiment,
                'positive_score': Decimal(str(sentiment_score['Positive'])),
                'negative_score': Decimal(str(sentiment_score['Negative'])),
                'neutral_score': Decimal(str(sentiment_score['Neutral'])),
                'mixed_score': Decimal(str(sentiment_score['Mixed']))  
            }
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Sentiment analysis completed')
    }
