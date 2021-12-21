import os
import json
import boto3
from aws_lambda_powertools import Tracer, Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# Enable Observability
tracer = Tracer()
logger = Logger()
metrics = Metrics()

# Bring in Env Vars
region_name = os.getenv('Region')
table_name = os.getenv('Table_Name') 

@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
@logger.inject_lambda_context

def lambda_handler(event, context):
    '''
    Handle Incoming Event
    '''   
    logger.info(f"Strava Activity Handler Activated with event {json.dumps(event)}")

    # Extra Object ID from Event    
    event_body = json.loads(event['body'])
    aspect_type = event_body['aspect_type']
    
    try: 
        if aspect_type == 'create':
            logger.info(f"Attempting to store new activity in: {table_name}")            
            
            # Populate Activity Details in Dynamo
            response = write_to_dynamo(event_body)    

            metrics.add_metric(name="ActivityLogged", unit=MetricUnit.Count, value=1)
            logger.info(f"New Activity Written to GFP Activities Table")

            return {
                "body": json.dumps({
                    "message": response,
                    })
            }

        else: 
            logger.info("Dropping as not NEW event")

    except:
         logger.exception("Something failed right here..")


def write_to_dynamo(activity):
    '''
    Writing Actvity Details to Strava Activities Dynamo DB Table.
    '''    
    dynamodb = boto3.client('dynamodb')

    new_item = {
        "object_id": {"S": str(activity['object_id'])},
        "activity_type": {"S": str(activity['type'])},
        "activity_avg_speed": {"S": str(activity['average_speed'])},
        "activity_distance": {"S": str(activity['distance'])}
    }

    response = dynamodb.put_item(
        TableName=table_name, 
        Item=new_item
        )

    return response