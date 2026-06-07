import uuid
from datetime import datetime, timezone
from fastapi import HTTPException


def encode_geohash(lat: float, lng: float, precision: int = 6) -> str:
    lat_range, lng_range = [-90, 90], [-180, 180]
    chars = '0123456789bcdefghjkmnpqrstuvwxyz'
    geohash = []
    is_lng = True
    bits = 0
    bit_count = 0
    for _ in range(precision * 5):
        if is_lng:
            mid = (lng_range[0] + lng_range[1]) / 2
            if lng >= mid:
                bits = (bits << 1) | 1
                lng_range[0] = mid
            else:
                bits = bits << 1
                lng_range[1] = mid
        else:
            mid = (lat_range[0] + lat_range[1]) / 2
            if lat >= mid:
                bits = (bits << 1) | 1
                lat_range[0] = mid
            else:
                bits = bits << 1
                lat_range[1] = mid
        is_lng = not is_lng
        bit_count += 1
        if bit_count == 5:
            geohash.append(chars[bits])
            bits = 0
            bit_count = 0
    return ''.join(geohash)


class ReportRepository:
    def __init__(self, table):
        self.table = table

    def create(self, data: dict) -> dict:
        report_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        item = {
            'reports_id': report_id,
            'report_id': report_id,
            'user_id': data.get('user_id', 'ANONIMO'),
            'device_id': data.get('device_id', ''),
            'tipo': data.get('tipo', 'FORESTAL'),
            'latitud': str(data.get('latitud', 0)),
            'longitud': str(data.get('longitud', 0)),
            'geohash': encode_geohash(data.get('latitud', 0), data.get('longitud', 0)),
            'descripcion': data.get('descripcion', ''),
            'foto_url': data.get('foto_url', ''),
            'estado': 'PENDIENTE',
            'created_at': timestamp,
            'updated_at': timestamp,
        }
        self.table.put_item(Item=item)
        return item

    def find_by_id(self, report_id: str) -> dict | None:
        response = self.table.get_item(Key={'reports_id': report_id})
        item = response.get('Item')
        if item:
            item['report_id'] = item.get('reports_id', '')
        return item

    def find_by_user(self, user_id: str, estado: str | None = None) -> list[dict]:
        response = self.table.query(
            IndexName='user-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id},
        )
        items = response.get('Items', [])
        if estado:
            items = [i for i in items if i.get('estado') == estado]
        for item in items:
            item['report_id'] = item.get('reports_id', '')
        return items

    def find_all(self, estado: str | None = None) -> list[dict]:
        response = self.table.scan()
        items = response.get('Items', [])
        if estado:
            items = [i for i in items if i.get('estado') == estado]
        for item in items:
            item['report_id'] = item.get('reports_id', '')
        return items

    def update(self, report_id: str, estado: str | None = None, descripcion: str | None = None) -> dict:
        update_expr = "SET "
        expr_values = {}
        expr_names = {}

        if estado:
            update_expr += "#estado = :estado, "
            expr_values[':estado'] = estado
            expr_names['#estado'] = 'estado'
        if descripcion:
            update_expr += "descripcion = :descripcion, "
            expr_values[':descripcion'] = descripcion

        update_expr += "updated_at = :updated_at"
        expr_values[':updated_at'] = datetime.now(timezone.utc).isoformat()

        kwargs = {
            'Key': {'reports_id': report_id},
            'UpdateExpression': update_expr,
            'ExpressionAttributeValues': expr_values,
        }
        if expr_names:
            kwargs['ExpressionAttributeNames'] = expr_names

        self.table.update_item(**kwargs)
        return self.find_by_id(report_id) or {}

    def find_in_bbox(self, min_lat: float, max_lat: float, min_lng: float, max_lng: float) -> list[dict]:
        items = self.find_all()
        result = []
        for item in items:
            try:
                lat = float(item.get('latitud', 0))
                lng = float(item.get('longitud', 0))
                if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                    result.append(item)
            except (ValueError, TypeError):
                continue
        return result
