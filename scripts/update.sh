#!/bin/bash

# Script de atualização automática do deploy da branch 'producao'
# NÃO usar em ambiente de desenvolvimento

cd /root/LAD_Accounting || exit

# Ativar o ambiente virtual
source venv/bin/activate

# Ir para a branch de produção
git checkout producao

# Atualizar as branches remotas
git fetch origin

# Fazer merge das atualizações
git merge origin/main --no-edit
git merge origin/demandas --no-edit

# Reiniciar o Gunicorn
pkill gunicorn

sleep 3

cd source || exit
gunicorn app:server --bind 0.0.0.0:8000 &

echo "$(date): Atualização concluída" >> /root/LAD_Accounting/cron.log
