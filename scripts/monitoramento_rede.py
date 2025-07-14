import subprocess
import os
import time
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO_SAIDA = os.path.join(BASE_DIR, "source", "monitoramento.json")
DESTINO = "8.8.8.8"

def avaliar_ping():
    result = subprocess.run(['ping', '-c', '4', DESTINO], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode()
    
    if "0 received" in output or "100% packet loss" in output:
        return {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "latency": None,
            "packet_loss": 100,
            "status": "QUEDA"
        }

    # Extrair perda de pacotes
    perda_match = [line for line in output.splitlines() if "packet loss" in line]
    perda_percentual = float(perda_match[0].split("%")[0].split()[-1]) if perda_match else 0

    # Extrair latência média
    try:
        lat_line = next((line for line in output.splitlines() if "rtt min" in line or "round-trip min" in line), None)
        if lat_line:
            try:
                latency = float(lat_line.split('=')[1].split('/')[1].strip())
            except Exception:
                latency = None
        else:
            latency = None
    except Exception:
        latency = None

    # Classificar status
    if perda_percentual > 0:
        status = "LENTO"
    elif latency and latency > 100:
        status = "LENTO"
    else:
        status = "OK"

    return {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "latency": latency,
        "packet_loss": perda_percentual,
        "status": status
    }

def salvar():
    try:
        dados = avaliar_ping()
        try:
            with open(ARQUIVO_SAIDA, 'r') as f:
                historico = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            historico = []

        historico.append(dados)

        with open(ARQUIVO_SAIDA, 'w') as f:
            json.dump(historico, f, indent=4)
    except Exception as e:
        print(f"[ERRO] {e}")

if __name__ == "__main__":
    while True:
        salvar()
        time.sleep(10)  

