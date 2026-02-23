import os
import shutil
from pathlib import Path

def clean_project_caches(root_path):
    """
    Varre recursivamente o diretório raiz fornecido em busca de:
    1. Diretórios chamados '__pycache__'
    2. Arquivos com extensão '.pyc' (caso estejam fora das pastas de cache)
    """
    root = Path(root_path)
    print("=" * 50)
    print(f"🧹 INICIANDO LIMPEZA DE CACHE")
    print(f"📂 Diretório Raiz: {root.resolve()}")
    print("=" * 50)

    dirs_removed = 0
    files_removed = 0

    # 1. Varredura por diretórios __pycache__
    # O rglob faz a busca recursiva em todas as subpastas
    for p in root.rglob('__pycache__'):
        if p.is_dir():
            try:
                # relative_to deixa o log mais limpo, mostrando apenas o caminho a partir da raiz
                rel_path = p.relative_to(root)
                shutil.rmtree(p)
                print(f"   [DEL DIR]  {rel_path}")
                dirs_removed += 1
            except Exception as e:
                print(f"   [ERRO] Não foi possível remover {p}: {e}")

    # 2. Varredura por arquivos .pyc soltos (Orfãos)
    for p in root.rglob('*.pyc'):
        if p.is_file():
            try:
                # Verifica se o arquivo ainda existe (pode ter sido apagado junto com a pasta acima)
                if p.exists():
                    rel_path = p.relative_to(root)
                    os.remove(p)
                    print(f"   [DEL FILE] {rel_path}")
                    files_removed += 1
            except Exception as e:
                print(f"   [ERRO] Não foi possível remover {p}: {e}")

    print("-" * 50)
    print("✅ LIMPEZA CONCLUÍDA")
    print(f"   Pastas removidas: {dirs_removed}")
    print(f"   Arquivos removidos: {files_removed}")
    print("=" * 50)

if __name__ == "__main__":
    # Define o diretório onde este script está salvo como a raiz da busca
    current_directory = os.path.dirname(os.path.abspath(__file__))
    clean_project_caches(current_directory)