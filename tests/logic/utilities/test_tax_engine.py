import pytest
from unittest.mock import patch
from src.logic.utilities.tax_engine import TaxEngine
from src.logic.utilities.customs_rules import CustomsRules

class TestTaxEngine:

    def test_calculate_scenarios_zero_or_negative_value(self):
        # Valor 0
        result = TaxEngine.calculate_scenarios(0, manual_rate=5.0)

        assert "meta" in result
        assert "scenarios" in result

        meta = result["meta"]
        assert meta["dolar_usado"] == 5.0
        assert meta["cota_usd"] == 500.0

        scenarios = result["scenarios"]

        # Via Legal
        assert scenarios[0]["imposto"] == 0.0
        assert scenarios[0]["multa"] == 0.0
        assert scenarios[0]["total_geral"] == 0.0

        # Não Declarou
        assert scenarios[1]["imposto"] == 0.0
        assert scenarios[1]["multa"] == 0.0
        assert scenarios[1]["total_geral"] == 0.0

        # Fraude
        assert scenarios[2]["imposto"] == 0.0
        assert scenarios[2]["multa"] == 0.0
        assert scenarios[2]["total_geral"] == 0.0

        # RTU
        assert scenarios[3]["imposto"] == 0.0
        assert scenarios[3]["multa"] == 0.0
        assert scenarios[3]["total_geral"] == 0.0

        # Valor negativo
        result_neg = TaxEngine.calculate_scenarios(-100, manual_rate=5.0)
        assert result_neg["scenarios"][0]["imposto"] == 0.0

    def test_calculate_scenarios_within_limit_500(self):
        # Valor exato da cota: 500
        result = TaxEngine.calculate_scenarios(500, manual_rate=5.0)
        scenarios = result["scenarios"]

        # Excedente = 0, imposto = 0
        assert scenarios[0]["imposto"] == 0.0
        assert scenarios[0]["multa"] == 0.0
        assert scenarios[0]["total_geral"] == 2500.0  # 500 * 5.0 + 0

        assert scenarios[1]["imposto"] == 0.0
        assert scenarios[1]["multa"] == 0.0
        assert scenarios[1]["total_geral"] == 2500.0

        assert scenarios[2]["imposto"] == 0.0
        assert scenarios[2]["multa"] == 0.0
        assert scenarios[2]["total_geral"] == 2500.0

        # RTU sempre é taxado pelo total (não tem cota)
        imposto_fed = 2500.0 * CustomsRules.ALIQUOTA_RTU_FEDERAL # 2500 * 0.25 = 625.0
        icms_estimado = (2500.0 + imposto_fed) * CustomsRules.ICMS_PADRAO_ESTIMADO # (2500 + 625) * 0.07 = 3125 * 0.07 = 218.75
        expected_rtu_imposto = imposto_fed + icms_estimado # 843.75
        expected_rtu_total = 2500.0 + expected_rtu_imposto # 3343.75

        assert scenarios[3]["imposto"] == expected_rtu_imposto
        assert scenarios[3]["multa"] == 0.0
        assert scenarios[3]["total_geral"] == expected_rtu_total

    def test_calculate_scenarios_exceed_limit_500_01(self):
        # Valor: 500.01 (taxado)
        rate = 5.0
        result = TaxEngine.calculate_scenarios(500.01, manual_rate=rate)
        scenarios = result["scenarios"]

        valor_compra_brl = 500.01 * rate # 2500.05
        excedente_usd = 0.01
        excedente_brl = 0.05

        imposto_legal = excedente_brl * CustomsRules.ALIQUOTA_BAGAGEM # 0.05 * 0.50 = 0.025

        # Via Legal
        assert scenarios[0]["imposto"] == pytest.approx(imposto_legal)
        assert scenarios[0]["multa"] == 0.0
        assert scenarios[0]["total_geral"] == pytest.approx(valor_compra_brl + imposto_legal)

        # Não Declarou
        multa_oficio = excedente_brl * CustomsRules.ALIQUOTA_MULTA_OFICIO # 0.05 * 0.50 = 0.025
        assert scenarios[1]["imposto"] == pytest.approx(imposto_legal)
        assert scenarios[1]["multa"] == pytest.approx(multa_oficio)
        assert scenarios[1]["total_geral"] == pytest.approx(valor_compra_brl + imposto_legal + multa_oficio)

        # Fraude
        multa_qualificada = imposto_legal * CustomsRules.ALIQUOTA_MULTA_FRAUDE # 0.025 * 1.0 = 0.025
        assert scenarios[2]["imposto"] == pytest.approx(imposto_legal)
        assert scenarios[2]["multa"] == pytest.approx(multa_qualificada)
        assert scenarios[2]["total_geral"] == pytest.approx(valor_compra_brl + imposto_legal + multa_qualificada)

    @patch('src.logic.utilities.tax_engine.FinanceService')
    def test_calculate_scenarios_mock_finance_service_success(self, mock_finance_service):
        mock_finance_service.RATES_DISPLAY = {"USD": {"val": 5.50}}

        result = TaxEngine.calculate_scenarios(100)

        meta = result["meta"]
        assert meta["dolar_usado"] == 5.50
        assert meta["origem"] == "AwesomeAPI"

    @patch('src.logic.utilities.tax_engine.FinanceService')
    def test_calculate_scenarios_mock_finance_service_fallback(self, mock_finance_service):
        mock_finance_service.RATES_DISPLAY = {}

        result = TaxEngine.calculate_scenarios(100)

        meta = result["meta"]
        assert meta["dolar_usado"] == 5.90
        assert meta["origem"] == "Estimado (API Offline)"
