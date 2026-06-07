import pytest


class TestReportFactory:
    def test_create_forestal_report(self):
        from factories import ReportFactory, ForestalReport
        report = ReportFactory.create_report('FORESTAL')
        assert isinstance(report, ForestalReport)
        assert report.tipo == 'FORESTAL'
        assert report.get_priority() == 1
        assert report.get_default_estado() == 'PENDIENTE'

    def test_create_urbano_report(self):
        from factories import ReportFactory, UrbanoReport
        report = ReportFactory.create_report('URBANO')
        assert isinstance(report, UrbanoReport)
        assert report.tipo == 'URBANO'
        assert report.get_priority() == 2
        assert report.get_default_estado() == 'PENDIENTE'

    def test_create_invalid_tipo(self):
        from factories import ReportFactory
        with pytest.raises(ValueError) as exc:
            ReportFactory.create_report('MARINO')
        assert 'no soportado' in str(exc.value)

    def test_forestal_to_item(self):
        from factories import ReportFactory
        report = ReportFactory.create_report('FORESTAL')
        report.user_id = 'u1'
        report.latitud = -33.45
        report.longitud = -70.67
        item = report.to_item()
        assert item['tipo'] == 'FORESTAL'
        assert item['latitud'] == -33.45
        assert item['longitud'] == -70.67

    def test_urbano_to_item(self):
        from factories import ReportFactory
        report = ReportFactory.create_report('URBANO')
        report.user_id = 'u1'
        item = report.to_item()
        assert item['tipo'] == 'URBANO'
        assert item['user_id'] == 'u1'
