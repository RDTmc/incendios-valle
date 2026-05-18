#!/usr/bin/env python3
"""
Seed script para crear usuario admin y datos de prueba en DynamoDB.
Ejecutar en la EC2 o localmente con credenciales AWS configuradas.
"""

import boto3
import hashlib
import uuid
from datetime import datetime, timezone

def seed():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    users_table = dynamodb.Table('users')
    reports_table = dynamodb.Table('reports')

    # Crear usuario admin
    admin_id = str(uuid.uuid4())
    password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    timestamp = datetime.now(timezone.utc).isoformat()

    print("Creando usuario admin...")
    try:
        users_table.put_item(Item={
            'user_id': admin_id,
            'email': 'admin@valledelsol.cl',
            'password_hash': password_hash,
            'nombre': 'Administrador',
            'rol': 'ADMIN',
            'created_at': timestamp
        })
        print(f"✅ Admin creado: admin@valledelsol.cl / admin123")
        print(f"   user_id: {admin_id}")
    except Exception as e:
        print(f"❌ Error creando admin: {e}")

    # Crear usuario vecino de prueba
    vecino_id = str(uuid.uuid4())
    password_hash_vecino = hashlib.sha256('vecino123'.encode()).hexdigest()

    print("\nCreando usuario vecino...")
    try:
        users_table.put_item(Item={
            'user_id': vecino_id,
            'email': 'vecino@valledelsol.cl',
            'password_hash': password_hash_vecino,
            'nombre': 'Juan Pérez',
            'rol': 'VECINO',
            'created_at': timestamp
        })
        print(f"✅ Vecino creado: vecino@valledelsol.cl / vecino123")
        print(f"   user_id: {vecino_id}")
    except Exception as e:
        print(f"❌ Error creando vecino: {e}")

    # Crear reportes de prueba para el mapa
    print("\nCreando reportes de prueba...")
    focos_prueba = [
        {'lat': -33.45, 'lng': -70.66, 'tipo': 'FORESTAL', 'estado': 'ACTIVO'},
        {'lat': -33.48, 'lng': -70.70, 'tipo': 'URBANO', 'estado': 'CONTROLADO'},
        {'lat': -33.44, 'lng': -70.65, 'tipo': 'FORESTAL', 'estado': 'PENDIENTE'},
    ]

    for foco in focos_prueba:
        report_id = str(uuid.uuid4())
        geohash = f"{int(foco['lat'] * 1000)}-{int(foco['lng'] * 1000)}"
        try:
            reports_table.put_item(Item={
                'report_id': report_id,
                'user_id': vecino_id,
                'tipo': foco['tipo'],
                'latitud': str(foco['lat']),
                'longitud': str(foco['lng']),
                'geohash': geohash,
                'descripcion': f"Reporte de prueba {foco['tipo']}",
                'estado': foco['estado'],
                'created_at': timestamp,
                'updated_at': timestamp
            })
            print(f"✅ Reporte {foco['estado']}: {foco['lat']}, {foco['lng']}")
        except Exception as e:
            print(f"❌ Error creando reporte: {e}")

    print("\n🎉 Seed completado!")
    print("\nCredenciales de prueba:")
    print("  Admin:   admin@valledelsol.cl / admin123")
    print("  Vecino:  vecino@valledelsol.cl / vecino123")

if __name__ == '__main__':
    seed()
