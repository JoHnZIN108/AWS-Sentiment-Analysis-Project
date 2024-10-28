from aws_cdk import (
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    Stack,
    aws_kinesis as kinesis,
    aws_lambda_event_sources as _lambda_event_sources,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    Duration  
)
from constructs import Construct

class CdkProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # kinesis stream
        kinesis_stream = kinesis.Stream(
            self, "Kinesis_stream",
            stream_name= "Youtube_Comment_Stream",
            shard_count=1
            )

        # DynamoDB table for storing comments and their sentiment
        sentiment_table = dynamodb.Table(
            self, "SentimentResultsTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            )
        )

        # lambda comment scraper
        scraper = _lambda_python.PythonFunction(
            self,
            "scraper",
            entry="./lambda/",
            runtime=_lambda.Runtime.PYTHON_3_9,
            index="scraper.py",
            handler="lambda_handler",
            environment={
                'KINESIS_STREAM_NAME': kinesis_stream.stream_name
            }
        )

        # lambda sentiment analysis
        sentiment = _lambda.Function(
            self,
            "sentiment",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("./lambda/"),
            handler="sentiment.lambda_handler",
            environment={
                'SENTIMENT_TABLE_NAME': sentiment_table.table_name
            }
        )

        # Add Kinesis stream as a trigger for lambda sentiment
        sentiment.add_event_source(
            _lambda_event_sources.KinesisEventSource(
                kinesis_stream,
                starting_position=_lambda.StartingPosition.LATEST,
                retry_attempts=1
            )
        )

        # Create an EventBridge rule to trigger lambda scraper every 1 minutes
        rule = events.Rule(
            self, "TriggerScraperRule",
            schedule=events.Schedule.rate(Duration.minutes(2))
        )
        rule.add_target(targets.LambdaFunction(scraper))


        # Grant lambda scraper permission to write to kinesis
        kinesis_stream.grant_write(scraper)
        # Grant lambda sentiment permission to comprehend and write to DynamoDB
        sentiment.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=["comprehend:DetectSentiment"],
                resources=["*"]
            )
        )
        sentiment_table.grant_write_data(sentiment)

        # Grant lambda scraper permission to write to kinesis
        scraper.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=["kinesis:PutRecord"],
                resources=[kinesis_stream.stream_arn]
            )
        )

