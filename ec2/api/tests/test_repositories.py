import pytest
import os
import bcrypt
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


class TestUserRepository:
    @pytest.fixture
    def mock_table(self):
        return MagicMock()

    @pytest.fixture
    def repo(self, mock_table):
        from repositories import UserRepository
        return UserRepository(mock_table)

    @pytest.mark.fast
    def test_find_by_email_found(self, repo, mock_table):
        mock_table.query.return_value = {'Items': [{'user_id': 'u1', 'email': 'a@b.com'}]}
        result = repo.find_by_email('a@b.com')
        assert result['user_id'] == 'u1'
        mock_table.query.assert_called_once()

    @pytest.mark.fast
    def test_find_by_email_not_found(self, repo, mock_table):
        mock_table.query.return_value = {'Items': []}
        result = repo.find_by_email('a@b.com')
        assert result is None

    @pytest.mark.fast
    def test_find_by_id(self, repo, mock_table):
        mock_table.get_item.return_value = {'Item': {'user_id': 'u1'}}
        result = repo.find_by_id('u1')
        assert result['user_id'] == 'u1'

    @pytest.mark.fast
    def test_create_user(self, repo, mock_table):
        mock_table.query.return_value = {'Items': []}
        result = repo.create('a@b.com', 'password123', 'Test User')
        assert result['email'] == 'a@b.com'
        assert result['nombre'] == 'Test User'
        assert result['rol'] == 'VECINO'
        assert 'user_id' in result
        mock_table.put_item.assert_called_once()

    @pytest.mark.fast
    def test_create_duplicate_email(self, repo, mock_table):
        mock_table.query.return_value = {'Items': [{'user_id': 'existing'}]}
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            repo.create('a@b.com', 'password123')
        assert exc.value.status_code == 409

    @pytest.mark.fast
    def test_authenticate_success(self, repo, mock_table):
        pw_hash = bcrypt.hashpw('pass123'.encode(), bcrypt.gensalt()).decode()
        mock_table.query.return_value = {'Items': [{'user_id': 'u1', 'email': 'a@b.com', 'password_hash': pw_hash, 'rol': 'VECINO'}]}
        result = repo.authenticate('a@b.com', 'pass123')
        assert 'token' in result
        assert result['user']['user_id'] == 'u1'

    @pytest.mark.fast
    def test_authenticate_invalid_password(self, repo, mock_table):
        pw_hash = bcrypt.hashpw('correct'.encode(), bcrypt.gensalt()).decode()
        mock_table.query.return_value = {'Items': [{'user_id': 'u1', 'password_hash': pw_hash}]}
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            repo.authenticate('a@b.com', 'wrong')
        assert exc.value.status_code == 401


class TestReportRepository:
    @pytest.fixture
    def mock_table(self):
        return MagicMock()

    @pytest.fixture
    def repo(self, mock_table):
        from repositories import ReportRepository
        return ReportRepository(mock_table)

    @pytest.mark.fast
    def test_create_report(self, repo, mock_table):
        result = repo.create({'tipo': 'FORESTAL', 'latitud': -33.45, 'longitud': -70.67, 'user_id': 'u1'})
        assert 'reports_id' in result
        assert result['tipo'] == 'FORESTAL'
        assert result['estado'] == 'PENDIENTE'
        mock_table.put_item.assert_called_once()

    @pytest.mark.fast
    def test_find_by_id(self, repo, mock_table):
        mock_table.get_item.return_value = {'Item': {'reports_id': 'r1', 'estado': 'PENDIENTE'}}
        result = repo.find_by_id('r1')
        assert result['report_id'] == 'r1'

    @pytest.mark.fast
    def test_find_by_id_not_found(self, repo, mock_table):
        mock_table.get_item.return_value = {'Item': None}
        result = repo.find_by_id('r1')
        assert result is None

    @pytest.mark.fast
    def test_find_by_user(self, repo, mock_table):
        mock_table.query.return_value = {'Items': [{'reports_id': 'r1', 'user_id': 'u1'}, {'reports_id': 'r2', 'user_id': 'u1'}]}
        result = repo.find_by_user('u1')
        assert len(result) == 2

    @pytest.mark.fast
    def test_find_all(self, repo, mock_table):
        mock_table.scan.return_value = {'Items': [{'reports_id': 'r1'}, {'reports_id': 'r2'}]}
        result = repo.find_all()
        assert len(result) == 2

    @pytest.mark.fast
    def test_find_all_with_estado_filter(self, repo, mock_table):
        mock_table.scan.return_value = {'Items': [{'reports_id': 'r1', 'estado': 'PENDIENTE'}, {'reports_id': 'r2', 'estado': 'VALIDADO'}]}
        result = repo.find_all(estado='VALIDADO')
        assert len(result) == 1
        assert result[0]['report_id'] == 'r2'

    @pytest.mark.fast
    def test_update_report(self, repo, mock_table):
        mock_table.get_item.return_value = {'Item': {'reports_id': 'r1', 'estado': 'VALIDADO'}}
        result = repo.update('r1', estado='VALIDADO')
        assert result['estado'] == 'VALIDADO'
        mock_table.update_item.assert_called_once()

    @pytest.mark.fast
    def test_find_in_bbox(self, repo, mock_table):
        mock_table.scan.return_value = {
            'Items': [
                {'reports_id': 'r1', 'latitud': '-33.0', 'longitud': '-70.0'},
                {'reports_id': 'r2', 'latitud': '-35.0', 'longitud': '-68.0'},
            ]
        }
        result = repo.find_in_bbox(-34.5, -32.5, -71.5, -69.5)
        assert len(result) == 1
        assert result[0]['reports_id'] == 'r1'
