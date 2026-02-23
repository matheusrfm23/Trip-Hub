import datetime
from src.logic.utilities.customs_rules import CustomsRules
from src.logic.finance_service import FinanceService

class TaxEngine:
    
    @staticmethod
    def calculate_scenarios(valor_compra_usd, manual_rate=None):
        """
        Gera matriz de decisão.
        manual_rate: Se informado, usa este valor. Se None, tenta pegar da API.
        """
        
        # 1. Definição da Cotação
        if manual_rate and manual_rate > 0:
            dolar_rate = manual_rate
            origem_cambio = "Manual"
        else:
            # Tenta pegar da API via FinanceService
            rates = FinanceService.RATES_DISPLAY
            rate_api = rates.get("USD", {}).get("val", 0.0)
            
            if rate_api > 0:
                dolar_rate = rate_api
                origem_cambio = "AwesomeAPI"
            else:
                # Fallback de segurança se a API falhar
                dolar_rate = 5.90 
                origem_cambio = "Estimado (API Offline)"
        
        # Conversões Base
        valor_total_brl = valor_compra_usd * dolar_rate
        cota_usd = CustomsRules.COTA_VIA_TERRESTRE
        
        # Cálculo do Excedente (Parte crítica que estava dando zero)
        excedente_usd = max(0, valor_compra_usd - cota_usd)
        excedente_brl = excedente_usd * dolar_rate
        
        # --- CENÁRIO 1: O "CORRETO" (DECLARAÇÃO ESPONTÂNEA) ---
        imposto_legal = excedente_brl * CustomsRules.ALIQUOTA_BAGAGEM
        total_legal = valor_total_brl + imposto_legal
        
        scenario_legal = {
            "titulo": "Via Legal (Declarando)",
            "cor": "green",
            "imposto": imposto_legal,
            "multa": 0.0,
            "total_geral": total_legal,
            "risco": "Nenhum. Liberação imediata.",
            "obs": "Isento de IBS/CBS em 2026."
        }

        # --- CENÁRIO 2: O "ARISCO" (NÃO DECLAROU + PEGO) ---
        multa_oficio = excedente_brl * CustomsRules.ALIQUOTA_MULTA_OFICIO
        total_risco_leve = valor_total_brl + imposto_legal + multa_oficio
        
        scenario_risco_leve = {
            "titulo": "Não Declarou (Pego na Aduana)",
            "cor": "orange",
            "imposto": imposto_legal,
            "multa": multa_oficio,
            "total_geral": total_risco_leve,
            "risco": "Retenção dos bens. Multa de ofício.",
            "obs": "Multa de 50% sobre o excedente."
        }

        # --- CENÁRIO 3: A "FRAUDE" (DECLARAÇÃO FALSA) ---
        multa_qualificada = imposto_legal * CustomsRules.ALIQUOTA_MULTA_FRAUDE
        total_risco_grave = valor_total_brl + imposto_legal + multa_qualificada
        
        scenario_risco_grave = {
            "titulo": "Declaração Falsa (Fraude)",
            "cor": "red",
            "imposto": imposto_legal,
            "multa": multa_qualificada,
            "total_geral": total_risco_grave,
            "risco": "Perda da primariedade. Multa de 100%.",
            "obs": "Multa de 100% sobre o imposto devido."
        }

        # --- CENÁRIO 4: RTU (MICROIMPORTADOR) ---
        imposto_fed = valor_total_brl * CustomsRules.ALIQUOTA_RTU_FEDERAL
        icms_estimado = (valor_total_brl + imposto_fed) * CustomsRules.ICMS_PADRAO_ESTIMADO
        total_rtu = valor_total_brl + imposto_fed + icms_estimado
        
        scenario_rtu = {
            "titulo": "RTU (Comercial/MEI)",
            "cor": "blue",
            "imposto": imposto_fed + icms_estimado,
            "multa": 0.0,
            "total_geral": total_rtu,
            "risco": "Monitorar limite anual de R$ 81k (MEI).",
            "obs": "Permite revenda legal."
        }

        return {
            "meta": {
                "dolar_usado": dolar_rate,
                "origem": origem_cambio,
                "cota_usd": cota_usd
            },
            "scenarios": [scenario_legal, scenario_risco_leve, scenario_risco_grave, scenario_rtu]
        }

    @staticmethod
    def check_criminal_risk(ocultacao=False, quantidade_excessiva=False, reincidente=False):
        if ocultacao:
            return {
                "nivel": "CRÍTICO",
                "msg": CustomsRules.MSG_CRIME,
                "detalhe": "Fundo falso ou ocultação gera PERDIMENTO do carro e prisão.",
                "cor": "red_900"
            }
        
        if quantidade_excessiva:
            return {
                "nivel": "ALTO",
                "msg": "DESCARACTERIZAÇÃO DE BAGAGEM",
                "detalhe": "Quantidade comercial presume revenda. Sem RTU, perde-se tudo.",
                "cor": "red"
            }
            
        if reincidente:
            return {
                "nivel": "MÉDIO",
                "msg": "INSIGNIFICÂNCIA NEGADA",
                "detalhe": "Reincidência afasta o princípio da insignificância. Risco penal.",
                "cor": "orange"
            }
            
        return None