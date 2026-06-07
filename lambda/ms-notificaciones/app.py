import json
import boto3
import os
from datetime import datetime, timezone

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:887513569063:incendios-alerts')
sns = boto3.client('sns')


def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', '')
        alert_type = body.get('alert_type', 'INFO')
        report_id = body.get('report_id', '')
        lat = body.get('latitud', 0)
        lon = body.get('longitud', 0)

        if not message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Message is required'}),
                'headers': {'Content-Type': 'application/json'},
            }

        timestamp = datetime.now(timezone.utc).isoformat()
        sns_message = json.dumps({
            'alert_type': alert_type,
            'message': message,
            'report_id': report_id,
            'latitud': lat,
            'longitud': lon,
            'timestamp': timestamp,
            'source': 'ms-notificaciones',
        })

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=sns_message,
            Subject=f'[Incendios] {alert_type}: {message[:100]}',
            MessageAttributes={
                'alert_type': {
                    'DataType': 'String',
                    'StringValue': alert_type,
                }
            },
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'sent', 'timestamp': timestamp}),
            'headers': {'Content-Type': 'application/json'},
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'},
        }
