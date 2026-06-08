import json
import boto3
import os
import uuid
from datetime import datetime
import math

dynamodb = boto3.resource('dynamodb')
reports_table = dynamodb.Table('reports')

def lambda_handler(event, context):
    try:
        http_method = event.get('httpMethod')
        path = event.get('path', '')
        
        if http_method == 'POST':
            if path == '/reports':
                return create_report(event)
        
        elif http_method == 'GET':
            if path == '/reports':
                return list_reports(event)
            elif '/reports/' in path:
                report_id = path.split('/')[-1]
                return get_report(report_id)
        
        elif http_method == 'PUT':
            if '/reports/' in path:
                report_id = path.split('/')[-1]
                return update_report(report_id, event)
        
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Not found'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def encode_geohash(lat, lon):
    """Simple geohash encoding for location queries"""
    lat_hash = int(lat * 1000000)
    lon_hash = int(lon * 1000000)
    return f"{lat_hash // 1000}-{lon_hash // 1000}"

def create_report(event):
    body = json.loads(event.get('body', '{}'))
    
    report_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    lat = body.get('latitud', 0)
    lon = body.get('longitud', 0)
    
    item = {
        'reports_id': report_id,
        'user_id': body.get('user_id', ''),
        'tipo': body.get('tipo', 'INCENDIO'),
        'latitud': str(lat),
        'longitud': str(lon),
        'geohash': encode_geohash(lat, lon),
        'descripcion': body.get('descripcion', ''),
        'estado': 'PENDIENTE',
        'created_at': timestamp,
        'updated_at': timestamp
    }
    
    reports_table.put_item(Item=item)
    
    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'reports_id': report_id,
            'estado': 'PENDIENTE',
            'created_at': timestamp
        })
    }

def list_reports(event):
    query_params = event.get('queryStringParameters', {}) or {}
    estado = query_params.get('estado', '')
    user_id = query_params.get('user_id', '')
    
    if user_id:
        # Usar GSI user-index
        response = reports_table.query(
            IndexName='user-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        items = response.get('Items', [])
    else:
        # Scan completo
        response = reports_table.scan()
        items = response.get('Items', [])
    
    if estado:
        items = [i for i in items if i.get('estado') == estado]
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(items)
    }

def get_report(report_id):
    response = reports_table.query(
        KeyConditionExpression='reports_id = :rid',
        ExpressionAttributeValues={':rid': report_id}
    )
    items = response.get('Items', [])
    
    if not items:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Report not found'})
        }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(items[0])
    }

def update_report(report_id, event):
    body = json.loads(event.get('body', {}))
    
    # Primero obtener created_at (RANGE key)
    query_resp = reports_table.query(
        KeyConditionExpression='reports_id = :rid',
        ExpressionAttributeValues={':rid': report_id}
    )
    items = query_resp.get('Items', [])
    if not items:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Report not found'})
        }
    
    created_at = items[0]['created_at']
    
    update_expr = 'SET '
    expr_values = {}
    expr_names = {}
    
    if 'estado' in body:
        update_expr += '#estado = :estado, '
        expr_values[':estado'] = body['estado']
        expr_names['#estado'] = 'estado'
    
    if 'descripcion' in body:
        update_expr += 'descripcion = :descripcion, '
        expr_values[':descripcion'] = body['descripcion']
    
    update_expr += 'updated_at = :updated_at'
    expr_values[':updated_at'] = datetime.utcnow().isoformat()
    
    try:
        reports_table.update_item(
            Key={'reports_id': report_id, 'created_at': created_at},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names if expr_names else None
        )
        
        response = reports_table.get_item(Key={'reports_id': report_id, 'created_at': created_at})
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response.get('Item', {}))
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }