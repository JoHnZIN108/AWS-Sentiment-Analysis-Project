import googleapiclient.discovery
import json
import logging
import boto3
import os

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Kinesis client
kinesis = boto3.client('kinesis')
stream_name = os.environ['KINESIS_STREAM_NAME']

# YouTube API configurations
api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = ""  

def lambda_handler(event, context):
    # Initialize YouTube client
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)

    # Request to fetch comments from a specific video
    request = youtube.commentThreads().list(
        part="snippet",
        videoId="MAm5OCgZ6so",  # Replace with the desired video ID
        maxResults=15  # Adjust based on your need
    )
    response = request.execute()

    for item in response['items']:
        comment = item['snippet']['topLevelComment']['snippet']
        likes_count = comment['likeCount']
        text = comment['textDisplay']
        
        
        # Create a record to send to kinesis
        record = {
            'text': text,
            'likes_count': likes_count
        }

        
        logger.info(f"Sending record to Kinesis: {record}")

        # Send the record to Kinesis
        kinesis.put_record(
            StreamName=stream_name,
            Data=json.dumps(record),
            PartitionKey='partition_key'
        )


        # Log the comments and their likes to cloudwatch
        logger.info(comment)
            
    # Return the results as JSON
    return {
        'statusCode': 200,
        'body': json.dumps("Comments sent to Kinesis stream successfully")
    }
