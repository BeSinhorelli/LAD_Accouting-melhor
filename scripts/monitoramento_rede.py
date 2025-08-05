import subprocess
import os
import time
from datetime import datetime
import sys

# Adiciona o caminho da pasta `source` ao sys.path para importar corretamente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'source')))

from models import MonitoramentoRede, database

DESTINO = "8.8.8.8"

def avaliar_ping():
    result = subprocess.run(['ping', '-c', '4', DESTINO], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

if __name__ == "__main__":
    if database.is_closed():
        database.connect()

    # Cria a tabela caso não exista
    database.create_tables([MonitoramentoRede], safe=True)

    while True:
        salvar()
        time.sleep(10)
