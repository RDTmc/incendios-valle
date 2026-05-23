import boto3
import bcrypt
import uuid
from datetime import datetime, timezone

def encode_geohash(lat, lon):
    lat_hash = int(lat * 1000000)
    lon_hash = int(lon * 1000000)
    return f"{lat_hash // 1000}-{lon_hash // 1000}"

def seed():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    users_table = dynamodb.Table('users')
    reports_table = dynamodb.Table('reports')

    admin_id = '81d02e8d-375c-40b9-9f1e-968be9a2c5ae'
    password_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
    timestamp = datetime.now(timezone.utc).isoformat()

    print("Creando usuario admin con hash robusto...")
    try:
        users_table.put_item(Item={
            'user_id': admin_id,
            'email': 'admin@valledelsol.cl',
            'password_hash': password_hash,
            'nombre': 'Administrador',
            'rol': 'ADMIN',
            'created_at': timestamp
        })
        print(f"Admin creado: admin@valledelsol.cl / admin123")
    except Exception as e:
        print(f"Error creando admin: {e}")

    vecino_id = str(uuid.uuid4())
    password_hash_vecino = bcrypt.hashpw('vecino123'.encode(), bcrypt.gensalt()).decode()

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
        print(f"Vecino creado: vecino@valledelsol.cl / vecino123")
    except Exception as e:
        print(f"Error creando vecino: {e}")

    print("\nCreando reportes de prueba...")
    focos_prueba = [
        {'lat': -33.45, 'lng': -70.66, 'tipo': 'FORESTAL', 'estado': 'ACTIVO'},
        {'lat': -33.48, 'lng': -70.70, 'tipo': 'URBANO', 'estado': 'CONTROLADO'},
        {'lat': -33.44, 'lng': -70.65, 'tipo': 'FORESTAL', 'estado': 'PENDIENTE'},
    ]

    for foco in focos_prueba:
        report_id = str(uuid.uuid4())
        geohash = encode_geohash(foco['lat'], foco['lng'])
        try:
            reports_table.put_item(Item={
                'reports_id': report_id,
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
            print(f"Reporte {foco['estado']} insertado (Geohash: {geohash})")
        except Exception as e:
            print(f"Error creando reporte: {e}")

    print("\nSeed completado con hashing bcrypt estándar!")

if __name__ == '__main__':
    seed()
