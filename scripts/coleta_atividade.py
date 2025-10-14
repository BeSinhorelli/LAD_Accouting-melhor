#!/usr/bin/env python3
import os
import subprocess
import socket
import paramiko
from datetime import datetime, date
import sys
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'source')))
from models import Atividade, RebootHistory, database
ssh_password = os.getenv("accounting_password")
if not ssh_password:
    raise EnvironmentError("Variável de ambiente accounting_password não encontrada.")

def is_production():
    return socket.gethostname() == "accounting"

# Função auxiliar para executar comandos
def execute_command(cmd):
    try:
        if is_production():
            output = subprocess.check_output(cmd, shell=True).decode()
        else:
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    "accounting", username="laduser", password=ssh_password, allow_agent=False, look_for_keys=False
                )
                stdin, stdout, _ = ssh.exec_command(cmd)
                output = stdout.read().decode()
        return output
    except Exception as e:
        print(f"Erro ao executar o comando '{cmd}': {e}")
        return None

# Coletar data do último reboot
def get_boot_time():
    output = execute_command("/usr/bin/uptime -s")
    if output:
        return datetime.strptime(output.strip(), "%Y-%m-%d %H:%M:%S")
    return None

# Coletar histórico de reboot
def get_reboot_history_raw():
    return execute_command("/usr/bin/last reboot -F")

# Salvar atividade atual 
def salvar_atividade(data_hoje, boot_time):
    try:
        boot_time_str = boot_time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            ultimo_uptime_salvo = Atividade.select().order_by(Atividade.id.desc()).get().uptime
            if ultimo_uptime_salvo == boot_time_str:
                print("[INFO] Uptime não mudou. Nenhum novo registro na tabela Atividade.")
                return
        except Atividade.DoesNotExist:
            pass
            with database.atomic():
                Atividade.insert(data=data_hoje, uptime=boot_time.strftime("%Y-%m-%d %H:%M:%S")).on_conflict_replace().execute()
            print(f"[INFO] Atividade atual salva. Uptime: {boot_time}")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar atividade atual: {e}")

# Salvar o histórico de reboots 
def salvar_reboot_history(reboot_data):
    try:
        with database.atomic():
            for inicio, fim in reboot_data:
                if not RebootHistory.select().where(
                    (RebootHistory.data_inicio == inicio) & (RebootHistory.data_fim == fim)
                ).exists():
                    RebootHistory.insert(data_inicio=inicio, data_fim=fim).execute()
                # Se o registro já existe, ignora e continua para o próximo
        print(f"[INFO] Histórico de reboots salvo.")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar histórico de reboots: {e}")

def coletar_e_salvar():
    hoje = date.today()
    # Coleta o boot time
    boot_time_string = get_boot_time()
    if not boot_time_string:
        print("Erro ao obter o tempo de atividade.")
        return
    # Salva o uptime atual
    salvar_atividade(hoje, boot_time_string)

    # Coleta e salva o histórico de reboots
    reboot_history_raw = get_reboot_history_raw()
    if reboot_history_raw:
        reboot_data = []
        for line in reboot_history_raw.splitlines():
            if "still running" in line or "wtmp begins" in line:
                continue
            match = re.search(r'(\w{3}\s+\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\d{4})\s*-\s*(\w{3}\s+\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\d{4})', line)
            if match:
                inicio_str = match.group(1)
                fim_str = match.group(2)
                try:
                    data_inicio = datetime.strptime(inicio_str, "%a %b %d %H:%M:%S %Y")
                    data_fim = datetime.strptime(fim_str, "%a %b %d %H:%M:%S %Y")
                    reboot_data.append((data_inicio, data_fim))
                except ValueError as e:
                    print(f"Erro ao processar linha de reboot: {line} - {e}")
        salvar_reboot_history(reboot_data)

if __name__ == "__main__":
    if database.is_closed():
        database.connect()
    database.create_tables([Atividade, RebootHistory], safe=True)

    coletar_e_salvar()
