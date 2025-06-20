import pandas as pd
import plotly.graph_objs as go
import requests
from datetime import datetime
import os

# --- VARIAVÉIS DE CORES  --- #

first_color = '#FDC366'
second_color = '#212529'
third_color = '#111111'
fourth_color = '#1E6EFF'
fifth_color = '#EEE'
# ---------------------------------  CONFIGURAÇÕES PARA DASHBOARDS DE DEMANDAS  --------------------------------- #

# Configuração de cores para demandas
COLORS = {
    "background": "black",
    "text": "white",
    "bar1": "#2c6e9e", 
    "bar2": "#e74c3c", 
    "link": "#007bff",
    "gray": "gray",
}
GITHUB_REPO = "LAD-PUCRS/LAD-Management"
GITHUB_TOKEN = "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"  # Token do GitHub
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

ano_atual = datetime.now().year # definir ano atual
select_anos = list(range(2020, ano_atual + 1)) # Gerar lista de seleção de anos automaticamente (de 2020 até ano atual) 
year = str(ano_atual) 
month = 0
x = 0
i = 0

for dataframe in os.listdir('relatorios/' + year):
    month += 1

def fetch_all_issues():
    issues = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=all&per_page=100&page={page}"
        response = requests.get(url, headers=HEADERS) 

        if response.status_code != 200:
            print("Erro ao acessar o GitHub:", response.status_code)
            return []

        data = response.json()

        if not data:  # Se não há mais issues, para de buscar
            break

        issues.extend(data)
        page += 1  # Próxima página

    return issues

# Buscar todas as issues
issues = fetch_all_issues()

# Verifica se há issues
if not issues:
    print("Nenhuma issue encontrada. Verifique suas credenciais ou repositório.")
    issues = []

# Lista com os dados relevantes
data = []
for issue in issues:
    data.append({
        "ID": issue["number"],
        "Título": issue["title"],
        "Status": issue["state"],
        "Criado em": issue["created_at"][:10],
        "Labels": ", ".join([label["name"] for label in issue["labels"]]),
        "URL": issue["html_url"]  
    })

# Converte para um DataFrame
df = pd.DataFrame(data)
df["Criado em"] = pd.to_datetime(df["Criado em"])

# Criar coluna de mês
df["Month"] = df["Criado em"].dt.strftime('%b')  

# Filtrar dados com base no ano selecionado
def filter_data_by_year(selected_year):
    filtered_df = df[df["Criado em"].dt.year == int(selected_year)].copy()
    filtered_demandas_erro = filtered_df[filtered_df["Labels"].str.contains("_USER", na=False)].copy()
    return filtered_df, filtered_demandas_erro

# Filtrar demandas com label "_USER"
demandas_erro = df[df["Labels"].str.contains("_USER", na=False)].copy()


def plot_monthly_comparison():
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_counts = df["Month"].value_counts()
    monthly_error_counts = demandas_erro["Month"].value_counts()
    months_with_data = [m for m in month_order if m in monthly_counts.index]
    monthly_counts = monthly_counts.reindex(months_with_data)
    monthly_error_counts = monthly_error_counts.reindex(months_with_data, fill_value=0)

    return {
        "data": [
            go.Bar(
                x=monthly_counts.index,
                y=monthly_counts.values,
                name="Total",
                marker={"color": COLORS["bar1"]},
                text=monthly_counts.values,
                width=0.6,
                hovertemplate="<b>Mês:</b> %{x}<br><b>Total:</b> %{y}<extra></extra>"
            ),
            go.Bar(
                x=monthly_counts.index,
                y=monthly_error_counts.values,
                name="Erros de Usuário",
                marker={"color": COLORS["bar2"]},
                text=monthly_error_counts.values,
                width=0.6,
                hovertemplate="<b>Mês:</b> %{x}<br><b>Erros de Usuário:</b> %{y}<extra></extra>"
            )
        ],
        "layout": go.Layout(
            xaxis={"title": "Mês", "color": COLORS["text"]},
            yaxis={"title": "Quantidade de Demandas Criadas", "color": COLORS["text"]},
            barmode="overlay",
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font={"color": COLORS["text"]},
            hovermode="closest",
        )
    }

