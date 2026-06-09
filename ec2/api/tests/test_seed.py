import pytest
import sys
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSeed:
    @patch('seed.boto3.resource')
    def test_seed_creates_admin_user(self, mock_boto_resource):
        mock_users_table = MagicMock()
        mock_reports_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.side_effect = lambda name: {
            'users': mock_users_table,
            'reports': mock_reports_table
        }[name]
        mock_boto_resource.return_value = mock_dynamodb

        import importlib
        import seed
        importlib.reload(seed)

        seed.seed()

        put_calls = mock_users_table.put_item.call_args_list
        admin_call = put_calls[0]
        assert admin_call[1]['Item']['email'] == 'admin@valledelsol.cl'
        assert admin_call[1]['Item']['rol'] == 'ADMIN'
        assert 'password_hash' in admin_call[1]['Item']

        vecino_call = put_calls[1]
        assert vecino_call[1]['Item']['email'] == 'vecino@valledelsol.cl'
        assert vecino_call[1]['Item']['rol'] == 'VECINO'

    @patch('seed.boto3.resource')
    def test_seed_creates_test_reports(self, mock_boto_resource):
        mock_users_table = MagicMock()
        mock_reports_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.side_effect = lambda name: {
            'users': mock_users_table,
            'reports': mock_reports_table
        }[name]
        mock_boto_resource.return_value = mock_dynamodb

        import importlib
        import seed
        importlib.reload(seed)

        seed.seed()

        report_calls = mock_reports_table.put_item.call_args_list
        assert len(report_calls) == 3
        estados = [call[1]['Item']['estado'] for call in report_calls]
        assert 'ACTIVO' in estados
        assert 'CONTROLADO' in estados
        assert 'PENDIENTE' in estados

    @patch('seed.boto3.resource')
    def test_seed_handles_dynamodb_error(self, mock_boto_resource):
        mock_users_table = MagicMock()
        mock_users_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_users_table
        mock_boto_resource.return_value = mock_dynamodb

        import importlib
        import seed
        importlib.reload(seed)

        with patch('builtins.print') as mock_print:
            seed.seed()
            error_calls = [c for c in mock_print.call_args_list if 'Error' in str(c)]
            assert len(error_calls) > 0


class TestSeedBcrypt:
    @patch('seed_bcrypt.boto3.resource')
    def test_seed_bcrypt_creates_admin_with_fixed_id(self, mock_boto_resource):
        mock_users_table = MagicMock()
        mock_reports_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.side_effect = lambda name: {
            'users': mock_users_table,
            'reports': mock_reports_table
        }[name]
        mock_boto_resource.return_value = mock_dynamodb

        import importlib
        import seed_bcrypt
        importlib.reload(seed_bcrypt)

        seed_bcrypt.seed()

        admin_call = mock_users_table.put_item.call_args_list[0]
        assert admin_call[1]['Item']['user_id'] == '81d02e8d-375c-40b9-9f1e-968be9a2c5ae'
        assert admin_call[1]['Item']['rol'] == 'ADMIN'

    @patch('seed_bcrypt.boto3.resource')
    def test_encode_geohash(self, mock_boto_resource):
        import seed_bcrypt
        gh = seed_bcrypt.encode_geohash(-33.45, -70.66)
        assert gh == '-33450--70660'

    @patch('seed_bcrypt.boto3.resource')
    def test_seed_bcrypt_handles_error(self, mock_boto_resource):
        mock_users_table = MagicMock()
        mock_users_table.put_item.side_effect = Exception("DB error")
        mock_reports_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.side_effect = lambda name: {
            'users': mock_users_table,
            'reports': mock_reports_table
        }[name]
        mock_boto_resource.return_value = mock_dynamodb

        import importlib
        import seed_bcrypt
        importlib.reload(seed_bcrypt)

        with patch('builtins.print') as mock_print:
            seed_bcrypt.seed()
            error_calls = [c for c in mock_print.call_args_list if 'Error' in str(c)]
            assert len(error_calls) > 0
