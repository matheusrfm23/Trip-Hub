#!/usr/bin/env python3
import json
import os
import sys
import shutil

CONFIG_FILE = "log_config.json"
LOG_DIR = "logs"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "console_enabled": True,
            "file_enabled": True,
            "retention_days": 7,
            "log_level": "INFO"
        }
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print("✅ Configuração salva com sucesso.")

def print_menu(config):
    print("\n" + "="*40)
    print("📊 TRIP-HUB LOG MANAGER")
    print("="*40)

    console_status = "🟢 ON" if config.get("console_enabled") else "🔴 OFF"
    file_status = "🟢 ON" if config.get("file_enabled") else "🔴 OFF"
    retention = config.get("retention_days", 7)
    level = config.get("log_level", "INFO")

    print(f"1. Toggle Console Logs  [{console_status}]")
    print(f"2. Toggle File Logs     [{file_status}]")
    print(f"3. Set Retention Days   [{retention} days]")
    print(f"4. Set Log Level        [{level}]")
    print(f"5. 🗑️  CLEAR ALL LOGS")
    print(f"0. Exit")
    print("="*40)

def clear_logs():
    confirm = input("⚠️  ATENÇÃO: Isso apagará TODOS os arquivos de log. Confirmar? (y/N): ")
    if confirm.lower() == 'y':
        if os.path.exists(LOG_DIR):
            try:
                shutil.rmtree(LOG_DIR)
                os.makedirs(LOG_DIR)
                print("✅ Logs apagados com sucesso.")
            except Exception as e:
                print(f"❌ Erro ao apagar logs: {e}")
        else:
            print("ℹ️  Diretório de logs não existe.")
    else:
        print("Operação cancelada.")

def main():
    config = load_config()

    if len(sys.argv) > 1:
        # Modo CLI Direto (Argumentos)
        cmd = sys.argv[1]
        if cmd == "clear":
            clear_logs()
        elif cmd == "console-on":
            config["console_enabled"] = True
            save_config(config)
        elif cmd == "console-off":
            config["console_enabled"] = False
            save_config(config)
        elif cmd == "file-on":
            config["file_enabled"] = True
            save_config(config)
        elif cmd == "file-off":
            config["file_enabled"] = False
            save_config(config)
        else:
            print(f"Comando desconhecido: {cmd}")
        return

    # Modo Interativo
    while True:
        print_menu(config)
        choice = input("Opção: ")

        if choice == "1":
            config["console_enabled"] = not config.get("console_enabled", True)
            save_config(config)
        elif choice == "2":
            config["file_enabled"] = not config.get("file_enabled", True)
            save_config(config)
        elif choice == "3":
            try:
                days = int(input("Dias de retenção: "))
                if days > 0:
                    config["retention_days"] = days
                    save_config(config)
            except: print("Valor inválido.")
        elif choice == "4":
            lvl = input("Nível (DEBUG, INFO, WARNING, ERROR): ").upper()
            if lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                config["log_level"] = lvl
                save_config(config)
            else:
                print("Nível inválido.")
        elif choice == "5":
            clear_logs()
        elif choice == "0":
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
