from dash import html, dcc
from peewee import fn
import os
import pandas as pd
from datetime import datetime, date
import calendar

from config import *
from models import Producao, Relatorio

# Importa funções do layout_atividade em vez do excel_loader
from dash_routes.layout_atividade import (
    get_all_excel_files,
    get_activity_data_for_year,
    calculate_activity_from_excel
)

card_style = {
    "backgroundColor": "#343a40",
    "padding": "1.5rem",
    "borderRadius": "1rem",
    "minWidth": "250px",
    "maxWidth": "280px",
    "color": "#f8f9fa",
    "boxShadow": "0 6px 15px rgba(0,0,0,0.5)",
    "textAlign": "center",
    "transition": "transform 0.3s ease-in-out",
}

def get_producoes():
    """Obtém total de produções do arquivo Excel"""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'relatorios', 'producoes.xlsx')
    try:
        df = pd.read_excel(file_path)
        # Tenta diferentes nomes de colunas
        if 'Produção Científica' in df.columns and 'TCC, Dissertação ou Tese' in df.columns:
            return df['Produção Científica'].sum() + df['TCC, Dissertação ou Tese'].sum()
        elif 'cientifica' in df.columns and 'tcc' in df.columns:
            return df['cientifica'].sum() + df['tcc'].sum()
        return 0
    except:
        return 0

def read_annual_report_with_cache(yearValue):
    """Lê relatório anual do banco (para compatibilidade)"""
    if yearValue is None:
        return pd.DataFrame()
    
    query = Relatorio.select().where(Relatorio.ano == yearValue).dicts()
    return pd.DataFrame(list(query))

def get_dias_ativos_por_ano(ano):
    """Calcula dias ativos para um ano específico baseado nos Excel"""
    excel_files = get_all_excel_files()
    if not excel_files:
        return "0"
    
    # Filtra arquivos do ano selecionado
    arquivos_ano = [f for f in excel_files if f['year'] == ano]
    if not arquivos_ano:
        return "0"
    
    # Pega o primeiro arquivo do ano
    primeiro = min(arquivos_ano, key=lambda x: x['month'])
    primeira_data = date(primeiro['year'], primeiro['month'], 1)
    
    # Pega o último arquivo do ano
    ultimo = max(arquivos_ano, key=lambda x: x['month'])
    ultimo_dia = calendar.monthrange(ultimo['year'], ultimo['month'])[1]
    ultima_data = date(ultimo['year'], ultimo['month'], ultimo_dia)
    
    # Calcula dias entre primeiro e último relatório do ano
    dias = (ultima_data - primeira_data).days + 1
    return f"{max(0, dias)}"

def get_dias_ativos():
    """Calcula dias desde o primeiro relatório Excel (todos os anos)"""
    excel_files = get_all_excel_files()
    if not excel_files:
        return "0"
    primeiro = min(excel_files, key=lambda x: (x['year'], x['month']))
    primeira_data = date(primeiro['year'], primeiro['month'], 1)
    dias = (datetime.now().date() - primeira_data).days
    return f"{max(0, dias)}"

layout_home = html.Div(
    style={
        "boxSizing": "border-box",
        "backgroundColor": "#212529",
        "color": "#f8f9fa",
        "height": "100vh",
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "center",
        "justifyContent": "top",
        "textAlign": "center",
        "padding": "2rem",
        "marginTop": "2rem"
    },
    children=[
        html.Div([
            html.H1(
                "Disponibilidade Anual", 
                style={
                    'color': first_color,
                    'text-align': 'center',
                    'font-size': '1.5rem'
                }
            ),
            html.Small(
                id="monitoramento-info",
                style={
                    'color': '#ccc',
                    'textAlign': 'center',
                    'display': 'block',
                    'marginBottom': '1.5rem',
                    'fontStyle': 'italic'
                }
            ),
            html.Div([
                html.Div([
                    html.H4("Uptime", style={'text-align': 'center', 'margin-bottom': '0.2rem'}),
                    html.P(id='uptime-percent', style={'font-size': '2rem', 'color': first_color, 'fontWeight': 'bold'}),
                    html.Small(id='uptime-hours')
                ], style={'flex': '1', 'padding': '0 1rem', 'border-right': '1px solid #555'}),
                html.Div([
                    html.H4("Downtime", style={'text-align': 'center', 'margin-bottom': '0.2rem'}),
                    html.P(id='downtime-percent', style={'font-size': '2rem', 'color': first_color, 'fontWeight': 'bold'}),
                    html.Small(id='downtime-hours')
                ], style={'flex': '1', 'padding': '0 1rem'}),
            ], style={'display': 'flex', 'justify-content': 'space-around', 'align-items': 'center', 'gap': '0.5rem'}),
        ], style={"padding": "2rem", "borderRadius": "12px", "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.4)", "backgroundColor": "#343a40", "width": "90%", "maxWidth": "900px"}),
        dcc.Loading(id="loading-summary-cards", type="default", children=html.Div(id="summary_cards", style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center", "gap": "1.5rem", "marginTop": "2rem"}))
    ]
)