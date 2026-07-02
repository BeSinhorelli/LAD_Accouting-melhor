import pandas as pd
from flask import Flask
import plotly.graph_objs as go
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
import re
from peewee import SqliteDatabase
from flask_caching import Cache

load_dotenv()

# --- CACHE CONFIG --- #
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',  
    'CACHE_DEFAULT_TIMEOUT': 7200  
}

# --- CORES --- #
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

# --- ESTILOS DOS TABS --- #
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

# Nomes das colunas
COL_CLUSTER_DB = 'maquina_cluster'
COL_24X7_DB = 'maquina_24x7'
COL_STORAGE_CLUSTER_DB = 'storage_cluster' 
COL_STORAGE_24X7_DB = 'storage_24x7' 
COL_SERVICO_DB = 'servico'
COL_PROJETO_DB = 'projeto'
COL_MES_DB = 'mes'

# Rename
COL_CLUSTER = 'Máquina em Cluster'
COL_24X7 = 'Máquina em 24x7'
COL_STORAGE_CLUSTER = 'Storage em cluster(GB)'
COL_STORAGE_24X7 = 'Storage em 24x7(GB)'
COL_SERVICO = 'Serviço'
COL_PROJETO = 'Projeto'
COL_MES = 'Mês'

rename_col = {
    COL_CLUSTER_DB: COL_CLUSTER,
    COL_24X7_DB: COL_24X7,
    COL_SERVICO_DB: COL_SERVICO,
    COL_PROJETO_DB: COL_PROJETO,
    COL_MES_DB: COL_MES,
    COL_STORAGE_CLUSTER_DB: COL_STORAGE_CLUSTER,
    COL_STORAGE_24X7_DB: COL_STORAGE_24X7
}

# --- CONFIGURAÇÕES --- #
def verify_leap_year(yearValue):
    return int(yearValue) % 400 == 0 or (int(yearValue) % 4 == 0 and int(yearValue) % 100 != 0)

def month_days(month, yearValue):
    fev = 29 if verify_leap_year(yearValue) else 28
    month_days = {
        1: 31, 2: fev, 3: 31, 4: 30,
        5: 31, 6: 30, 7: 31, 8: 31,
        9: 30, 10: 31, 11: 30, 12: 31
    }[month]
    return month_days

def read_database_excel(yearValue, month):
    month_names = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    month_name = month_names[month - 1]
    file_path = f'relatorios/{yearValue}/{month}-{month_name}.xlsx'
    try:
        df_data = pd.read_excel(file_path)
        return df_data
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao ler {file_path}: {e}")
        return pd.DataFrame()

# --- APLICAÇÕES --- #
def get_aplicacoes():
    file_path = os.path.join(os.path.dirname(__file__), 'relatorios', 'aplicacao.xlsx')
    try:
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
        df = df.fillna("")
        
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
    except FileNotFoundError:
        print(f"Arquivo de aplicações não encontrado: {file_path}")
        return []
    except Exception as e:
        print(f"Erro ao ler arquivo de aplicações: {e}")
        return []

# --- CONFIGURAÇÕES API GITHUB --- #
GITHUB_REPO = "LAD-PUCRS/LAD-Management"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# Configurações do Flask e banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'accounting.db')
DEBUG = True
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
server = Flask(__name__, static_folder='assets')
server.config.from_object(__name__)
database = SqliteDatabase(DATABASE, pragmas={'foreign_keys': 1})

# --- VARIÁVEIS GLOBAIS --- #
ano_atual = datetime.now().year
select_anos = list(range(2020, ano_atual + 1))
year = str(ano_atual) 
month = 0

relatorio_path = os.path.join(BASE_DIR, "relatorios", year)
if os.path.exists(relatorio_path):
    for dataframe in os.listdir(relatorio_path):
        month += 1
else:
    print(f"Diretório {relatorio_path} não existe. Ignorando leitura dos relatórios.")

# --- FUNÇÕES DO GITHUB --- #
def fetch_all_issues():
    issues = []
    page = 1
    
    if not GITHUB_REPO:
        print("Repositório GitHub não configurado")
        return []
    
    while True:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=all&per_page=100&page={page}"
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 404:
                print(f"Repositório {GITHUB_REPO} não encontrado.")
                return []
            elif response.status_code == 401:
                print("Erro de autenticação. Verifique seu token do GitHub.")
                return []
            elif response.status_code != 200:
                print(f"Erro ao acessar o GitHub: {response.status_code}")
                return []
            
            data = response.json()
            
            if not data:
                break
                
            issues.extend(data)
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão com o GitHub: {e}")
            return []
        except Exception as e:
            print(f"Erro inesperado: {e}")
            return []
    
    return issues

# Buscar issues do GitHub
print("Buscando issues do GitHub...")
issues = fetch_all_issues()

# Processa os dados do GitHub ou cria dados mockados
if issues:
    print(f"Encontradas {len(issues)} issues")
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
    
    df = pd.DataFrame(data)
    
    if not df.empty:
        df["Criado em"] = pd.to_datetime(df["Criado em"])
        df["Month"] = df["Criado em"].dt.strftime('%b')
        demandas_erro = df[df["Labels"].str.contains("_USER", na=False)].copy()
        print(f"Demandas de erro encontradas: {len(demandas_erro)}")
    else:
        df = pd.DataFrame()
        demandas_erro = pd.DataFrame()
else:
    print("Nenhuma issue encontrada. Criando dados mockados para demonstração...")
    
    # Dados mockados para teste
    import random
    mock_data = []
    
    anos = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
    grupos = ['LAD', 'HSLBI', 'Bioinfo', 'Neuro', 'Genomica', 'Metagenomica', 'Plumes', 'LabGenoma']
    tipos = ['bug', 'feature', 'documentation', '_USER', 'enhancement']
    
    for ano in anos:
        for mes in range(1, 13):
            num_demandas = random.randint(10, 30)
            for j in range(num_demandas):
                grupo = random.choice(grupos)
                tipo = random.choice(tipos)
                status = random.choice(['open', 'closed'])
                
                mock_data.append({
                    "ID": f"{ano}{mes:02d}{j}",
                    "Título": f"[{grupo}] {random.choice(['Análise de dados', 'Processamento', 'Storage', 'Backup', 'Manutenção', 'Instalação'])} {j+1}",
                    "Status": status,
                    "Criado em": f"{ano}-{mes:02d}-{random.randint(1, 28)}",
                    "Labels": tipo,
                    "URL": "#"
                })
    
    df = pd.DataFrame(mock_data)
    df["Criado em"] = pd.to_datetime(df["Criado em"])
    df["Month"] = df["Criado em"].dt.strftime('%b')
    demandas_erro = df[df["Labels"].str.contains("_USER", na=False)].copy()
    
    print(f"✅ Dados mockados criados: {len(df)} demandas, {len(demandas_erro)} erros de usuário")

# --- FUNÇÕES DE GRÁFICOS --- #
def filter_data_by_year(selected_year):
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    try:
        filtered_df = df[df["Criado em"].dt.year == int(selected_year)].copy()
        filtered_demandas_erro = filtered_df[filtered_df["Labels"].str.contains("_USER", na=False)].copy()
        return filtered_df, filtered_demandas_erro
    except Exception as e:
        print(f"Erro ao filtrar dados por ano: {e}")
        return pd.DataFrame(), pd.DataFrame()

def plot_monthly_comparison():
    if df.empty:
        return {
            "data": [],
            "layout": go.Layout(
                title="Sem dados disponíveis",
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"],
                font={"color": COLORS["text"]},
                xaxis={"title": "Mês"},
                yaxis={"title": "Quantidade de Demandas Criadas"}
            )
        }
    
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_counts = df["Month"].value_counts()
    monthly_error_counts = demandas_erro["Month"].value_counts() if not demandas_erro.empty else pd.Series()
    
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

def extract_names_from_titles(df):
    pattern = re.compile(r"\[(.*?)\]")
    return [match.group(1) for title in df["Título"] if (match := pattern.search(title))]

def plot_pie_chart(month):
    if demandas_erro.empty:
        return [go.Pie(labels=["Sem dados"], values=[1], hole=0.3, 
                      marker=dict(colors=[COLORS["gray"]]),
                      textinfo="none", hoverinfo="none")]
    
    filtered_data = demandas_erro[demandas_erro["Month"] == month]
    if filtered_data.empty:
        return [go.Pie(labels=["Sem dados neste mês"], values=[1], hole=0.3,
                      marker=dict(colors=[COLORS["gray"]]),
                      textinfo="none", hoverinfo="none")]
    
    names = extract_names_from_titles(filtered_data)
    if names:
        name_counts = pd.Series(names).value_counts()
        return [go.Pie(labels=name_counts.index, values=name_counts.values, hole=0.3)]
    
    return [go.Pie(labels=["Sem dados"], values=[1], hole=0.3,
                  marker=dict(colors=[COLORS["gray"]]),
                  textinfo="none", hoverinfo="none")]

def plot_horizontal_bar_chart(filtered_df):
    if filtered_df.empty:
        return {
            "data": [],
            "layout": go.Layout(
                title="Sem dados disponíveis para o período selecionado",
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"],
                font={"color": COLORS["text"]},
                xaxis={"title": "Quantidade"},
                yaxis={"title": "Status"}
            )
        }
    
    total_open_demandas = len(filtered_df)
    filtered_df["Status"] = filtered_df["Status"].str.strip().str.title()
    closed_count = filtered_df["Status"].value_counts().get("Closed", 0)
    
    return {
        "data": [
            go.Bar(
                x=[total_open_demandas],
                y=[""],
                name="Total Abertas",
                orientation="h",
                marker=dict(color="#4e9054"),
                text=[f"{total_open_demandas}"],
                textposition="inside",
                insidetextanchor="end",
                hovertemplate="<b>Total Abertas:</b> %{x}<extra></extra>",
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
            xaxis=dict(title="Quantidade", color=COLORS["text"]),
            yaxis=dict(title="Status", color=COLORS["text"], showticklabels=False),
            barmode="overlay",
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font={"color": COLORS["text"]},
            margin=dict(l=100, r=50, t=20, b=50),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        ),
    }