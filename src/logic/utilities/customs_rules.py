# src/logic/utilities/customs_rules.py

class CustomsRules:
    """
    Consolidação da Legislação Aduaneira (Base 2026).
    Fontes: Dec. 6.759/09, Lei 11.898/09, LC 227/2026.
    """
    
    # --- VALORES MONETÁRIOS (USD) ---
    COTA_VIA_TERRESTRE = 500.00
    COTA_FREE_SHOP_ENTRADA = 500.00  # Extra, se comprar na loja BRASILEIRA na volta
    
    # --- ALÍQUOTAS (%) ---
    ALIQUOTA_BAGAGEM = 0.50          # 50% sobre excedente
    ALIQUOTA_MULTA_OFICIO = 0.50     # 50% sobre excedente (Totaliza 100% imposto)
    ALIQUOTA_MULTA_FRAUDE = 1.00     # 100% sobre o imposto devido
    
    # --- RTU (MEI/MICROIMPORTADOR) ---
    ALIQUOTA_RTU_FEDERAL = 0.25      # 25% Unificado
    ICMS_PADRAO_ESTIMADO = 0.07      # Média 7% (Pode variar por estado)
    LIMITES_RTU = {
        "Q1": 18000.00, # Jan-Mar
        "Q2": 18000.00, # Abr-Jun
        "Q3": 37000.00, # Jul-Set
        "Q4": 37000.00  # Out-Dez
    }
    
    # --- LIMITES QUANTITATIVOS (BAGAGEM) ---
    LIMITES_QTD = {
        "bebidas": 12,           # Litros
        "cigarros": 10,          # Maços (Total 200 unid)
        "charutos": 25,          # Unidades
        "fumo": 250,             # Gramas
        "baratos": 20,           # Itens < $5 (Max 10 idênticos)
        "caros": 10,             # Itens >= $5 (Max 3 idênticos)
        "identicos_limite": 3    # O "número mágico" da revenda
    }

    # --- FLAGS DE RISCO ---
    MSG_CRIME = "🔴 CRIME: PERDIMENTO DE BENS + VEÍCULO + PROCESSO PENAL"
    MSG_RETENCAO = "⚠️ RETENÇÃO: BENS PRESOS ATÉ PAGAMENTO DE MULTA"
    MSG_MEI_RISCO = "⚠️ ALERTA MEI: Risco de desenquadramento (Simples Nacional Retroativo)"