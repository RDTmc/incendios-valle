import json
import boto3
import hashlib
import os
import jwt
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('users')

SECRET_KEY = os.environ.get('JWT_SECRET', 'incendios-valle-secret-key')

def lambda_handler(event, context):
    try:
        http_method = event.get('httpMethod')
        path = event.get('path', '')
        
        if http_method == 'POST':
            if path == '/login':
                return login(event)
            elif path == '/register':
                return register(event)
        
        elif http_method == 'GET':
            if '/users/' in path:
                user_id = path.split('/')[-1]
                return get_user(user_id)
        
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Not found'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def login(event):
    body = json.loads(event.get('body', '{}'))
    email = body.get('email', '')
    password = body.get('password', '')
    
    if not email or not password:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Email and password required'})
        }
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Buscar por email usando GSI
    response = users_table.query(
        IndexName='email-index',
        KeyConditionExpression='email = :email',
        ExpressionAttributeValues={':email': email}
    )
    
    user = response.get('Items', [None])[0]
    
    if not user or user.get('password_hash') != password_hash:
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Invalid credentials'})
        }
    
    token = jwt.encode({
        'user_id': user['user_id'],
        'email': user['email'],
        'rol': user.get('rol', 'VECINO'),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm='HS256')
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'email': user['email'],
                'rol': user.get('rol', 'VECINO'),
                'nombre': user.get('nombre', '')
            }
        })
    }

def register(event):
    body = json.loads(event.get('body', '{}'))
    email = body.get('email', '')
    password = body.get('password', '')
    nombre = body.get('nombre', '')
    rol = body.get('rol', 'VECINO')
    
    if not email or not password:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Email and password required'})
        }
    
    # Verificar si email ya existe
    response = users_table.query(
        IndexName='email-index',
        KeyConditionExpression='email = :email',
        ExpressionAttributeValues={':email': email}
    )
    
    if response.get('Items'):
        return {
            'statusCode': 409,
            'body': json.dumps({'error': 'User already exists'})
        }
    
    import uuid
    user_id = str(uuid.uuid4())
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    users_table.put_item(Item={
        'user_id': user_id,
        'email': email,
        'password_hash': password_hash,
        'nombre': nombre,
        'rol': rol,
        'created_at': datetime.utcnow().isoformat()
    })
    
    token = jwt.encode({
        'user_id': user_id,
        'email': email,
        'rol': rol,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm='HS256')
    
    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'token': token,
            'user': {
                'user_id': user_id,
                'email': email,
                'rol': rol,
                'nombre': nombre
            }
        })
    }

def get_user(user_id):
    response = users_table.get_item(Key={'user_id': user_id})
    user = response.get('Item')
    
    if not user:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'User not found'})
        }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'user_id': user['user_id'],
            'email': user['email'],
            'rol': user.get('rol', 'VECINO'),
            'nombre': user.get('nombre', '')
        })
    }