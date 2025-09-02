import pandas as pd
from flask import Flask
import plotly.graph_objs as go
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
import re
from peewee import SqliteDatabase

load_dotenv()

# ---  CORES  --- #

first_color = '#FDC366'
second_color = '#212529'
third_color = '#111111'
fourth_color = '#1E6EFF'
fifth_color = '#EEE'

COLORS = {
    "background": "black",
    "text": "white",
    "bar1": "#2c6e9e", 
    "bar2": "#e74c3c", 
    "link": "#007bff",
    "gray": "gray",
}

# ---  ESTILOS DOS TABS PARA MENU DO DASHBOARD --- #
tab_style = {
    'backgroundColor': '#2c3034',
    'color': fifth_color,
    'fontWeight': 'bold',
    'padding': '10px',
    'border': '1px solid #3a3f44',
    'borderBottom': 'none',
    'borderTopLeftRadius': '6px',
    'borderTopRightRadius': '6px',
    'textAlign': 'center',
    'transition': '0.3s',
    'cursor': 'pointer'
}

selected_tab_style = {
    'backgroundColor': fifth_color,
    'color': 'black',
    'fontWeight': 'bold',
    'padding': '10px',
    'border': '1px solid #3a3f44',
    'borderBottom': '3px solid #2c3034',
    'borderTopLeftRadius': '6px',
    'borderTopRightRadius': '6px',
    'textAlign': 'center',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.2)'
}

# ---  CONFIGURAÇÕES  --- #
def verify_leap_year (yearValue):
    return int(yearValue) % 400 == 0 or int(yearValue) % 4 == 0 and int(yearValue) % 100 != 0

def month_days (month, yearValue):
        
        fev = 29 if verify_leap_year(yearValue) else 28

        month_days = {
        1: 31, 2: fev, 3: 31, 4: 30,
        5: 31, 6: 30, 7: 31, 8: 31,
        9: 30, 10: 31, 11: 30, 12: 31
        }[month]
        return month_days

def read_database_excel (yearValue, month):
        
    month_names = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    month_name = month_names[month - 1]
    file_path = f'relatorios/{yearValue}/{month}-{month_name}.xlsx'
    df_data = pd.read_excel(file_path)
    return df_data

# ---  APLICAÇÕES  --- #
# Função para ler o arquivo de aplicações
def get_aplicacoes():
    file_path = os.path.join(os.path.dirname(__file__), 'relatorios', 'aplicacao.xlsx')
    df = pd.read_excel(file_path)
    df = df.rename(columns={
        "Aplicação": "nome",
        "Versão": "versao",
        "Tipo": "tipo",
        "Área": "area",
        "Função Principal": "descricao",
        "Host": "host",
        "Grupo": "grupo",
        "Dependências de": "dependencia",
        "Site": "site",
    })
    df = df.fillna("")  # Preencher NaN com string vazia
    
    aplicacoes_agrupadas = {}

    for _, row in df.iterrows():
        nome_app = row['nome']
        
        if nome_app not in aplicacoes_agrupadas:
            aplicacoes_agrupadas[nome_app] = {
                'nome': nome_app,
                'tipo': row['tipo'],
                'area': row['area'],
                'descricao': row['descricao'],
                'grupo': row['grupo'],
                'dependencia': row['dependencia'],
                'site': row['site'],
                'versoes_e_hosts': {}
            }
        
        versao = str(row['versao']).strip()
        host = str(row['host']).strip()

        if versao == "" and host == "":
            continue  

        if host not in aplicacoes_agrupadas[nome_app]['versoes_e_hosts']:
            aplicacoes_agrupadas[nome_app]['versoes_e_hosts'][host] = []

        if versao and versao not in aplicacoes_agrupadas[nome_app]['versoes_e_hosts'][host]:
            aplicacoes_agrupadas[nome_app]['versoes_e_hosts'][host].append(versao)

    # Converte para lista final
    for nome_app in aplicacoes_agrupadas:
        versoes_e_hosts_lista = []
        for host, versoes in aplicacoes_agrupadas[nome_app]['versoes_e_hosts'].items():
            if not versoes and not host:
                continue
            versoes_e_hosts_lista.append({
                'host': host if host else "",
                'versao': ', '.join([v for v in versoes if v])
            })
        aplicacoes_agrupadas[nome_app]['versoes_e_hosts'] = versoes_e_hosts_lista

    return list(aplicacoes_agrupadas.values())


# ---  CONFIGURAÇÕES  API GITHUB --- #
GITHUB_REPO = "LAD-PUCRS/LAD-Management"
GITHUB_TOKEN = "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"  # Token do GitHub
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# Configurações do Flask e banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'accounting.db')
DEBUG = True
SECRET_KEY = 'hin6bab8ge25*r=x&amp;+5$0kn=-#log$pt^#@vrqjld!^2ci@g*b'
server = Flask(__name__, static_folder='assets')
server.config.from_object(__name__)
database = SqliteDatabase(DATABASE, pragmas={'foreign_keys': 1})

# ---  VARIÁVEIS GLOBAIS  --- #
ano_atual = datetime.now().year # definir ano atual
select_anos = list(range(2020, ano_atual + 1)) # Gerar lista de seleção de anos automaticamente (de 2020 até ano atual) 
year = str(ano_atual) 
month = 0
x = 0
i = 0

relatorio_path = os.path.join(BASE_DIR, "relatorios", year)
if os.path.exists(relatorio_path):
    for dataframe in os.listdir(relatorio_path):
        month += 1
else:
    print(f"Diretório {relatorio_path} não existe. Ignorando leitura dos relatórios.")

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

# Gráfico anual
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

# Extrair nomes dos grupos das demandas de label "_USER"
def extract_names_from_titles(df):
    pattern = re.compile(r"\[(.*?)\]")
    return [match.group(1) for title in df["Título"] if (match := pattern.search(title))]

# Função para plotar o gráfico de pizza por mês
def plot_pie_chart(month):
    # Filtrar demandas de erro pelo mês fornecido
    filtered_data = demandas_erro[demandas_erro["Month"] == month]
    names = extract_names_from_titles(filtered_data)
    if names:
        name_counts = pd.Series(names).value_counts()
        return [go.Pie(labels=name_counts.index, values=name_counts.values, hole=0.3)]
    return []  # Retorna um gráfico vazio se não houver dados para o mês

# Função para plotar o gráfico de ciclos
def plot_horizontal_bar_chart(filtered_df):
    # Contar o número total de demandas abertas no mês
    total_open_demandas = len(filtered_df)

    # Padronizar os valores de status
    filtered_df["Status"] = filtered_df["Status"].str.strip().str.title()

    # Contar o número de demandas fechadas
    closed_count = filtered_df["Status"].value_counts().get("Closed", 0)

    # Dados para o gráfico de ciclo
    stages = ["Fechadas", "Total Abertas"]
    values = [
        closed_count,
        total_open_demandas,
    ]

    # Criar o gráfico ciclos
    return {
        "data": [
            go.Bar(
                x=[total_open_demandas],
                y=[""],
                name="Total",
                orientation="h",
                marker=dict(color="#4e9054"),
                text=[f"{total_open_demandas}"],
                textposition="inside",
                insidetextanchor="end",
                hovertemplate="<b>Total:</b> %{x}<extra></extra>",
            ),
            go.Bar(
                x=[closed_count],
                y=[""],
                name="Fechadas",
                orientation="h",
                marker=dict(color="#7c60b7"),
                text=[f"{closed_count}"],
                textposition="inside",
                insidetextanchor="end",
                hovertemplate="<b>Fechadas:</b> %{x}<extra></extra>",
            ),
        ],
        "layout": go.Layout(
            xaxis=dict(title="Quantidade"),
            yaxis=dict(title="Status"),
            barmode="overlay",  
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font={"color": COLORS["text"]},
            margin=dict(l=100, r=50, t=20, b=50),
        ),
    }
