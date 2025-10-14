#!/usr/bin/env python3
import subprocess
import os
import time
from datetime import datetime, timedelta
import sys

# Adiciona o caminho da pasta `source` ao sys.path para importar corretamente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'source')))

from models import MonitoramentoRede, database

DESTINO = "8.8.8.8"
INTERVALO_LIMPEZA = 86400
ultimo_limpeza_timestamp = 0

def avaliar_ping():
    result = subprocess.run(['/usr/bin/ping', '-c', '4', DESTINO], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode()
    
    if "0 received" in output or "100% packet loss" in output:
        return {
            "timestamp": datetime.now(),
            "latency": None,
            "packet_loss": 100,
            "status": "QUEDA"
        }

    perda_match = [line for line in output.splitlines() if "packet loss" in line]
    perda_percentual = float(perda_match[0].split("%")[0].split()[-1]) if perda_match else 0

    try:
        lat_line = next((line for line in output.splitlines() if "rtt min" in line or "round-trip min" in line), None)
        latency = float(lat_line.split('=')[1].split('/')[1].strip()) if lat_line else None
    except Exception:
        latency = None

    if perda_percentual > 0:
        status = "LENTO"
    elif latency and latency > 100:
        status = "LENTO"
    else:
        status = "OK"

    return {
        "timestamp": datetime.now(),
        "latency": latency,
        "packet_loss": perda_percentual,
        "status": status
    }

def salvar():
    try:
        dados = avaliar_ping()
        with database.atomic():
            MonitoramentoRede.create(**dados)
        print(f"[✓] Registro salvo: {dados}")
    except Exception as e:
        print(f"[ERRO ao salvar] {e}")

def limpar_dados_antigos():
    """Deleta registros mais antigos que 45 dias."""
    data_limite = datetime.now() - timedelta(days=45)
    
    try:
        query = MonitoramentoRede.delete().where(MonitoramentoRede.timestamp < data_limite)
        registros_deletados = query.execute()
        print(f"[✓] {registros_deletados} registros mais antigos que {data_limite.strftime('%Y-%m-%d')} foram deletados.")
    except Exception as e:
        print(f"[ERRO] Falha ao limpar os dados: {e}")

if __name__ == "__main__":
    if database.is_closed():
        database.connect()

    # Cria a tabela caso não exista
    database.create_tables([MonitoramentoRede], safe=True)
    limpar_dados_antigos()
    ultimo_limpeza_timestamp = time.time()

    while True:
        if time.time() - ultimo_limpeza_timestamp >= INTERVALO_LIMPEZA:
            limpar_dados_antigos()
            ultimo_limpeza_timestamp = time.time()

        salvar()
        time.sleep(10)
