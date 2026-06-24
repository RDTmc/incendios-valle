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
        method = event.get('httpMethod')
        path = event.get('path', '').rstrip('/')

        if method == 'POST':
            if path in ('/login', '/register', '/auth'):
                return handle_auth(event)
        elif method == 'GET' and '/users/' in path:
            return get_user(path.split('/')[-1])

        return {'statusCode': 404, 'body': json.dumps({'error': f'Not found: {method} {path}'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def handle_auth(event):
    body = json.loads(event.get('body', '{}'))
    email = body.get('email', '')
    password = body.get('password', '')

    if not email or not password:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Email and password required'})}

    resp = users_table.query(
        IndexName='email-index',
        KeyConditionExpression='email = :email',
        ExpressionAttributeValues={':email': email}
    )
    items = resp.get('Items', [])

    if items:
        user = items[0]
        if not bcrypt.checkpw(password.encode(), user.get('password_hash', '').encode()):
            return {'statusCode': 401, 'body': json.dumps({'error': 'Invalid credentials'})}
    else:
        user_id = str(uuid.uuid4())
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = {
            'user_id': user_id,
            'email': email,
            'password_hash': pw_hash,
            'nombre': body.get('nombre', ''),
            'rol': body.get('rol', 'VECINO'),
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        users_table.put_item(Item=user)

    token = jwt.encode({
        'user_id': user['user_id'],
        'email': user['email'],
        'rol': user.get('rol', 'VECINO'),
        'exp': datetime.now(timezone.utc) + timedelta(hours=24),
    }, SECRET_KEY, algorithm='HS256')

    status = 201 if not items else 200
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'email': user['email'],
                'rol': user.get('rol', 'VECINO'),
                'nombre': user.get('nombre', ''),
            },
        }),
    }


def get_user(user_id):
    resp = users_table.get_item(Key={'user_id': user_id})
    user = resp.get('Item')
    if not user:
        return {'statusCode': 404, 'body': json.dumps({'error': 'User not found'})}
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'user_id': user['user_id'],
            'email': user['email'],
            'rol': user.get('rol', 'VECINO'),
            'nombre': user.get('nombre', ''),
        }),
    }
