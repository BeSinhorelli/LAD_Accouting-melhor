#!/bin/bash

cd /root/LAD_Accounting

source venv/bin/activate

# Ir para a branch de produção
git checkout producao

# Atualizar as branches remotas
git fetch origin

# Fazer merge das atualizações
git merge origin/main --no-edit
git merge origin/demandas --no-edit

# Reiniciar o serviço
systemctl restart lad-dashboard.service

echo "$(date): Atualização concluída" >> /root/LAD_Accounting/cron.log
