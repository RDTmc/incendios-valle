import json
import boto3
import os
import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta

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

        return {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def login(event):
    body = json.loads(event.get('body', '{}'))
    email = body.get('email', '')
    password = body.get('password', '')

    if not email or not password:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Email and password required'})}

    response = users_table.query(
        IndexName='email-index',
        KeyConditionExpression='email = :email',
        ExpressionAttributeValues={':email': email}
    )
    user = response.get('Items', [None])[0]

    if not user or not bcrypt.checkpw(password.encode(), user.get('password_hash', '').encode()):
        return {'statusCode': 401, 'body': json.dumps({'error': 'Invalid credentials'})}

    token = jwt.encode({
        'user_id': user['user_id'],
        'email': user['email'],
        'rol': user.get('rol', 'VECINO'),
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
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
        return {'statusCode': 400, 'body': json.dumps({'error': 'Email and password required'})}

    response = users_table.query(
        IndexName='email-index',
        KeyConditionExpression='email = :email',
        ExpressionAttributeValues={':email': email}
    )
    if response.get('Items'):
        return {'statusCode': 409, 'body': json.dumps({'error': 'User already exists'})}

    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    users_table.put_item(Item={
        'user_id': user_id,
        'email': email,
        'password_hash': password_hash,
        'nombre': nombre,
        'rol': rol,
        'created_at': datetime.now(timezone.utc).isoformat()
    })

    token = jwt.encode({
        'user_id': user_id,
        'email': email,
        'rol': rol,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
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
        return {'statusCode': 404, 'body': json.dumps({'error': 'User not found'})}

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
