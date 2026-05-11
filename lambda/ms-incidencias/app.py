import json
import boto3
import os
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
incidencias_table = dynamodb.Table('incidencias')

def lambda_handler(event, context):
    try:
        http_method = event.get('httpMethod')
        path = event.get('path', '')
        
        if http_method == 'POST':
            if path == '/incidencias':
                return create_incidencia(event)
        
        elif http_method == 'GET':
            if path == '/incidencias':
                return list_incidencias(event)
            elif '/incidencias/' in path:
                inc_id = path.split('/')[-1]
                return get_incidencia(inc_id)
        
        elif http_method == 'PUT':
            if '/incidencias/' in path:
                inc_id = path.split('/')[-1]
                return update_incidencia(inc_id, event)
        
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Not found'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def create_incidencia(event):
    body = json.loads(event.get('body', '{}'))
    
    incidente_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'id': incidente_id,
        'user_id': body.get('user_id', ''),
        'tipo': body.get('tipo', 'INCENDIO'),
        'latitud': str(body.get('latitud', 0)),
        'longitud': str(body.get('longitud', 0)),
        'descripcion': body.get('descripcion', ''),
        'estado': 'PENDIENTE',
        'created_at': timestamp,
        'updated_at': timestamp
    }
    
    incidencias_table.put_item(Item=item)
    
    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'id': incidente_id,
            'estado': 'PENDIENTE',
            'created_at': timestamp
        })
    }

def list_incidencias(event):
    query_params = event.get('queryStringParameters', {})
    estado = query_params.get('estado', '')
    user_id = query_params.get('user_id', '')
    
    kwargs = {}
    if estado:
        kwargs['FilterExpression'] = '#estado = :estado'
        kwargs['ExpressionAttributeNames'] = {'#estado': 'estado'}
        kwargs['ExpressionAttributeValues'] = {':estado': estado}
    
    response = incidencias_table.scan(**kwargs)
    items = response.get('Items', [])
    
    if user_id:
        items = [i for i in items if i.get('user_id') == user_id]
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(items)
    }

def get_incidencia(incidencia_id):
    response = incidencias_table.get_item(Key={'id': incidencia_id})
    item = response.get('Item')
    
    if not item:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Incidence not found'})
        }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(item)
    }

def update_incidencia(incidencia_id, event):
    body = json.loads(event.get('body', {}))
    
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
        incidencias_table.update_item(
            Key={'id': incidencia_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names if expr_names else None
        )
        
        response = incidencias_table.get_item(Key={'id': incidencia_id})
        
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