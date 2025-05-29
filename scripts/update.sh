#!/bin/bash

LOGFILE="/home/laduser/LAD_Accounting/cron.log"

echo "===============================" >> "$LOGFILE"
echo "$(date): Início da atualização" >> "$LOGFILE"

cd /home/laduser/LAD_Accounting || { echo "Erro: Não foi possível acessar o diretório" >> "$LOGFILE"; exit 1; }

source venv/bin/activate || { echo "Erro: Falha ao ativar o ambiente virtual" >> "$LOGFILE"; exit 1; }

# Mudar para branch producao e trazer atualizações
git checkout producao >> "$LOGFILE" 2>&1 || { echo "Erro: Falha ao mudar para branch producao" >> "$LOGFILE"; exit 1; }

git pull origin producao >> "$LOGFILE" 2>&1 || { echo "Erro: Falha no git pull branch producao" >> "$LOGFILE"; exit 1; }

# Atualizar branches remotas
git fetch origin >> "$LOGFILE" 2>&1 || { echo "Erro: Falha no git fetch" >> "$LOGFILE"; exit 1; }

# Fazer merge da branch main
git merge origin/main --no-edit >> "$LOGFILE" 2>&1 || { echo "Erro: Falha no git merge origin/main" >> "$LOGFILE"; exit 1; }

# Fazer merge da branch demandas
git merge origin/demandas --no-edit >> "$LOGFILE" 2>&1 || { echo "Erro: Falha no git merge origin/demandas" >> "$LOGFILE"; exit 1; }

# Reiniciar o serviço
sudo /bin/systemctl restart lad-dashboard.service >> "$LOGFILE" 2>&1 || { echo "Erro: Falha ao reiniciar o serviço" >> "$LOGFILE"; exit 1; }

echo "$(date): Atualização concluída" >> "$LOGFILE"
echo "===============================" >> "$LOGFILE"
