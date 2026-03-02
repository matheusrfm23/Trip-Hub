# ARQUIVO: src/logic/finance_service.py
import json
import asyncio
import uuid
import logging
import aiohttp 
from datetime import datetime
from src.data.database import Database
from src.core.config import SSL_VERIFY

logger = logging.getLogger("TripHub.Finance")

class FinanceService:
    
    # Taxas padrão (Fallback seguro)
    RATES_DISPLAY = {
        "BRL": {"flag": "🇧🇷", "name": "Real", "val": 1.0, "symbol": "R$"},
        "USD": {"flag": "🇺🇸", "name": "Dólar", "val": 5.80, "symbol": "U$"},
        "ARS": {"flag": "🇦🇷", "name": "Blue", "val": 0.005, "symbol": "$"},
        "PYG": {"flag": "🇵🇾", "name": "Guarani", "val": 0.0007, "symbol": "₲"}
    }

    # [CORREÇÃO] Migrado para AwesomeAPI (igual ao Smart Banner) para garantir valores corretos
    API_AWESOME = "https://economia.awesomeapi.com.br/last/USD-BRL,BRL-PYG"
    API_BLUE = "https://api.bluelytics.com.ar/v2/latest"

    # --- API DE TAXAS (BLINDADA) ---
    @classmethod
    async def update_rates(cls):
        """
        Busca taxas online usando AwesomeAPI (mesma fonte do Banner) e Bluelytics.
        """
        logger.info("Iniciando atualização de câmbio (AwesomeAPI + Bluelytics)...")
        
        # Headers para evitar bloqueio (WAF)
        headers = {
            "User-Agent": "TripHub-App/1.0 (Linux; Docker)",
            "Accept": "application/json"
        }
        
        timeout = aiohttp.ClientTimeout(total=10)

        # Loga um alerta severo se a verificação SSL estiver desativada
        if not SSL_VERIFY:
            logger.warning("🚨 ALERTA DE SEGURANÇA: Verificação SSL está desativada (SSL_VERIFY=False). Use isso apenas no ambiente Docker/Dev local!")

        connector = aiohttp.TCPConnector(ssl=SSL_VERIFY)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
            # --- 1. AwesomeAPI (Dólar e Guarani) ---
            try:
                logger.info(f"Consultando: {cls.API_AWESOME}")
                async with session.get(cls.API_AWESOME) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Atualiza Dólar (USD -> BRL)
                        # Awesome retorna: "USDBRL": {"bid": "5.75"}
                        if "USDBRL" in data:
                            val_usd = float(data["USDBRL"]["bid"])
                            cls.RATES_DISPLAY["USD"]["val"] = val_usd
                            logger.info(f"✅ Dólar Oficial (Awesome): R$ {val_usd:.3f}")
                        
                        # Atualiza Guarani (BRL -> PYG)
                        # Awesome retorna: "BRLPYG": {"bid": "1350.00"} (1 Real vale X Guaranis)
                        # O sistema guarda o INVERSO (Quanto custa 1 Guarani em Reais)
                        if "BRLPYG" in data:
                            guaranis_per_real = float(data["BRLPYG"]["bid"])
                            if guaranis_per_real > 0:
                                cls.RATES_DISPLAY["PYG"]["val"] = 1.0 / guaranis_per_real
                                logger.info(f"✅ Guarani (Awesome): 1 BRL = {guaranis_per_real:.0f} PYG")
                    else:
                        logger.warning(f"⚠️ AwesomeAPI retornou erro: {response.status}")
            
            except asyncio.TimeoutError:
                logger.warning("⏳ Timeout na AwesomeAPI (Verifique conexão).")
            except Exception as e:
                logger.error(f"❌ Erro na AwesomeAPI: {e}")

            # --- 2. Bluelytics (Peso Blue Argentina) ---
            try:
                async with session.get(cls.API_BLUE) as response:
                    if response.status == 200:
                        data = await response.json()
                        blue_sell = data["blue"]["value_sell"]
                        if blue_sell > 0:
                            # Ajuste: Cotação relativa ao Dólar do dia
                            # Se 1 USD vale 6 Reais e 1 USD vale 1200 Pesos
                            # Então 1 Real vale 200 Pesos.
                            usd_val = cls.RATES_DISPLAY["USD"]["val"]
                            val_peso_em_reais = usd_val / blue_sell
                            
                            cls.RATES_DISPLAY["ARS"]["val"] = val_peso_em_reais
                            
                            logger.info(f"✅ Peso Blue Atualizado: 1 USD = ${blue_sell:.0f} ARS")
            except Exception as e: 
                logger.error(f"❌ Erro no Bluelytics: {e}")
                
        return True

    @staticmethod
    def convert_value(amount, from_curr, to_curr):
        rate_from = FinanceService.RATES_DISPLAY.get(from_curr, {}).get("val", 1.0)
        rate_to = FinanceService.RATES_DISPLAY.get(to_curr, {}).get("val", 1.0)
        if rate_to == 0: return 0.0
        return (amount * rate_from) / rate_to

    # --- HELPER SQLITE ---
    @staticmethod
    def _row_to_dict(row):
        d = dict(row)
        try:
            d['involved_ids'] = json.loads(d['involved_ids']) if d.get('involved_ids') else []
        except: d['involved_ids'] = []
        try:
            d['contested_by'] = json.loads(d['contested_by']) if d.get('contested_by') else []
        except: d['contested_by'] = []
        return d

    # --- GARBAGE COLLECTOR ---
    @staticmethod
    async def clean_orphaned_finances(valid_user_ids):
        await asyncio.sleep(0.01)
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM expenses")
            rows = cursor.fetchall()
            changes = 0
            for row in rows:
                tx_id = row["id"]
                payer_id = str(row["payer_id"])
                if payer_id not in valid_user_ids:
                    cursor.execute("DELETE FROM expenses WHERE id=?", (tx_id,))
                    changes += 1
                    continue
                raw_involved = row["involved_ids"]
                involved = json.loads(raw_involved) if raw_involved else []
                new_involved = [uid for uid in involved if str(uid) in valid_user_ids]
                raw_contested = row["contested_by"]
                contested = json.loads(raw_contested) if raw_contested else []
                new_contested = [uid for uid in contested if str(uid) in valid_user_ids]
                if len(involved) != len(new_involved) or len(contested) != len(new_contested):
                    cursor.execute(
                        "UPDATE expenses SET involved_ids=?, contested_by=? WHERE id=?", 
                        (json.dumps(new_involved), json.dumps(new_contested), tx_id)
                    )
                    changes += 1
            conn.commit()
            if changes > 0:
                logger.info(f"Limpeza financeira: {changes} registros ajustados.")
        except Exception as e:
            logger.error(f"Erro crítico na limpeza financeira: {e}")
        finally:
            conn.close()

    # --- CRUD OPERACIONAL ---
    @staticmethod
    async def add_expense(data):
        conn = Database.get_connection()
        new_id = str(uuid.uuid4())
        today = datetime.now().strftime("%d/%m")
        try:
            val = float(data["amount"])
            rate = FinanceService.RATES_DISPLAY.get(data["currency"], {}).get("val", 1.0)
            amount_brl = val * rate
            conn.execute('''
                INSERT INTO expenses (id, date, description, amount, currency, amount_brl, category, payer_id, payer_name, involved_ids, contested_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_id, today, data["description"], val, data["currency"], amount_brl,
                data["category"], data["payer_id"], data["payer_name"],
                json.dumps(data["involved_ids"]), json.dumps([])
            ))
            conn.commit()
            asyncio.create_task(FinanceService._notify_new_expense(data, val))
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar despesa: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    async def _notify_new_expense(data, val):
        try:
            from src.logic.notification_service import NotificationService
            payer_id = str(data["payer_id"])
            desc = data["description"]
            formatted_val = f"{data['currency']} {val:,.2f}"
            for uid in data["involved_ids"]:
                if str(uid) != payer_id:
                    msg = f"Você foi incluído na despesa '{desc}' ({formatted_val}) por {data['payer_name']}."
                    await NotificationService.send_notification(
                        sender_name="Sistema Financeiro",
                        target_id=uid,
                        title="Nova Dívida",
                        message=msg,
                        type="finance"
                    )
        except Exception as e:
            logger.warning(f"Falha ao enviar notificação de despesa: {e}")

    @staticmethod
    async def update_expense(tx_id, new_data):
        conn = Database.get_connection()
        try:
            val = float(new_data["amount"])
            rate = FinanceService.RATES_DISPLAY.get(new_data["currency"], {}).get("val", 1.0)
            amount_brl = val * rate
            conn.execute('''
                UPDATE expenses 
                SET description=?, amount=?, currency=?, amount_brl=?, category=?, involved_ids=?
                WHERE id=?
            ''', (
                new_data["description"], val, new_data["currency"], amount_brl,
                new_data["category"], json.dumps(new_data["involved_ids"]), tx_id
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar despesa {tx_id}: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    async def delete_expense(tx_id):
        conn = Database.get_connection()
        try:
            conn.execute("DELETE FROM expenses WHERE id=?", (tx_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar despesa {tx_id}: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    async def toggle_contest(tx_id, user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        user_id = str(user_id)
        try:
            cursor.execute("SELECT contested_by FROM expenses WHERE id=?", (tx_id,))
            row = cursor.fetchone()
            if not row: return False
            raw_data = row['contested_by']
            current_list = json.loads(raw_data) if raw_data else []
            if user_id in current_list:
                current_list.remove(user_id)
            else:
                current_list.append(user_id)
            cursor.execute("UPDATE expenses SET contested_by=? WHERE id=?", (json.dumps(current_list), tx_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erro ao contestar despesa: {e}")
            return False
        finally:
            conn.close()

    # --- LEITURAS ---
    @staticmethod
    async def get_notifications(user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        notifications = []
        try:
            cursor.execute("SELECT * FROM expenses")
            rows = cursor.fetchall()
            for row in rows:
                exp = FinanceService._row_to_dict(row)
                if exp.get("contested_by"):
                    notifications.append({
                        "type": "finance", 
                        "title": "Dívida Contestada",
                        "sender": "Sistema",
                        "message": f"A despesa '{exp.get('description')}' foi sinalizada.",
                        "timestamp": "Hoje",
                        "id": f"fin_{exp['id']}", 
                        "read_by": [] 
                    })
            return notifications
        except Exception as e:
            logger.error(f"Erro ao buscar notificações: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    async def get_report(user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        user_id = str(user_id)
        try:
            cursor.execute("SELECT * FROM expenses")
            rows = cursor.fetchall()
            all_txs = [FinanceService._row_to_dict(row) for row in rows]
            my_txs = []
            total_group = 0.0
            my_bal = 0.0
            for tx in all_txs:
                val_brl = tx["amount_brl"]
                total_group += val_brl
                payer = str(tx["payer_id"])
                consumers = [str(x) for x in tx["involved_ids"]]
                if payer == user_id or user_id in consumers:
                    my_txs.append(tx)
                if not consumers: continue
                split = val_brl / len(consumers)
                if payer == user_id: my_bal += val_brl
                if user_id in consumers: my_bal -= split
            return {
                "transactions": list(reversed(my_txs)),
                "group_total": total_group,
                "my_balance": my_bal,
                "rates": FinanceService.RATES_DISPLAY
            }
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            return {"transactions": [], "group_total": 0, "my_balance": 0, "rates": FinanceService.RATES_DISPLAY}
        finally:
            conn.close()

    @staticmethod
    async def get_debt_contacts(user_id):
        conn = Database.get_connection()
        try:
            rows = conn.execute("SELECT * FROM expenses").fetchall()
            transactions = [FinanceService._row_to_dict(row) for row in rows]
        finally:
            conn.close()
        user_id = str(user_id)
        balances = {}
        interacted_users = set()
        for tx in transactions:
            payer = str(tx["payer_id"])
            consumers = [str(x) for x in tx["involved_ids"]]
            amount = tx["amount_brl"]
            if not consumers: continue
            split_amount = amount / len(consumers)
            if payer == user_id:
                for consumer in consumers:
                    if consumer != user_id:
                        interacted_users.add(consumer)
                        balances[consumer] = balances.get(consumer, 0.0) + split_amount
            elif user_id in consumers:
                interacted_users.add(payer)
                balances[payer] = balances.get(payer, 0.0) - split_amount
        result = []
        for uid in interacted_users:
            bal = balances.get(uid, 0.0)
            result.append({"id": uid, "balance": bal})
        return result

    @staticmethod
    async def get_pairwise_history(user_id, other_id):
        conn = Database.get_connection()
        try:
            rows = conn.execute("SELECT * FROM expenses").fetchall()
            transactions = [FinanceService._row_to_dict(row) for row in rows]
        finally:
            conn.close()
        user_id = str(user_id)
        other_id = str(other_id)
        history = []
        for tx in transactions:
            payer = str(tx["payer_id"])
            consumers = [str(x) for x in tx["involved_ids"]]
            amount_brl = tx["amount_brl"]
            orig_amount = tx["amount"]
            curr = tx["currency"]
            if not consumers: continue
            split = amount_brl / len(consumers)
            if payer == user_id and other_id in consumers:
                history.append({
                    "type": "credit",
                    "desc": tx["description"],
                    "date": tx["date"],
                    "total": orig_amount,
                    "split_brl": split,
                    "currency": curr
                })
            elif payer == other_id and user_id in consumers:
                history.append({
                    "type": "debit",
                    "desc": tx["description"],
                    "date": tx["date"],
                    "total": orig_amount,
                    "split_brl": split,
                    "currency": curr
                })
        return list(reversed(history))

    @staticmethod
    async def calculate_balances(profiles):
        return {"total": 0, "transfers": []}

    @staticmethod
    async def get_p2p_status(user_id, target_id):
        history = await FinanceService.get_pairwise_history(user_id, target_id)
        balance = 0.0
        for item in history:
            if item["type"] == "credit":
                balance += item["split_brl"]
            else:
                balance -= item["split_brl"]
        return balance