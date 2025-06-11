# -------------------------------------  IMPORT DE BIBLIOTECAS  ---------------------------------------- #
# --- FLASK --- #

import os, json
from datetime import datetime
from flask import Flask, g, request, send_file, url_for, abort, render_template, redirect, flash
from peewee import *

# --- DASH --- #

from dash import dcc, html, dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

# --- BIBLIOTECAS PARA DEMANDAS--- #
import requests
import re
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# -------------------------------------  CONFIGURAÇÕES INICIAS  ---------------------------------------- #
# --- FLASK --- #

DATABASE = 'accounting.db'
DEBUG = True
SECRET_KEY = 'hin6bab8ge25*r=x&amp;+5$0kn=-#log$pt^#@vrqjld!^2ci@g*b'
server = Flask(__name__, static_folder='assets')
server.config.from_object(__name__)
database = SqliteDatabase(DATABASE, pragmas={'foreign_keys': 1})

# --- DASH --- #

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    server=server,
    assets_folder='assets/images',
    url_base_pathname='/dash/'
    )

pio.templates.default = "plotly_dark"
app.title = "LAD Dashboard"

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

# Configurações
GITHUB_REPO = "LAD-PUCRS/LAD-Management"
GITHUB_TOKEN = "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"  # Token do GitHub
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

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

# ---------------------------  FINAL CONFIGURAÇÕES PARA DASHBOARDS DE DEMANDAS  --------------------------- #



# ------------------------------------  LEITURA DATABASE - DASH ---------------------------------------- #

# 
ano_atual = datetime.now().year # definir ano atual
select_anos = list(range(2020, ano_atual + 1)) # Gerar lista de seleção de anos automaticamente (de 2020 até ano atual) 
year = str(ano_atual) 
month = 0
x = 0
i = 0

for dataframe in os.listdir('relatorios/' + year):
    month += 1

# ----------------------------------------  LAYOUT - DASH ---------------------------------------------- #

app.layout = html.Div([

    # --- NAVEGAÇÃO  --- #

    html.Div(
        html.Div([
            html.A("LAD Accounting", href="/", style={'color': fifth_color, 'text-decoration':'none', 'font-size':'1.5rem'}),
            
            html.Img(
                id="logo",
                src=app.get_asset_url("LabLAD.png"),
                style={'max-width': '100px'}
            ),
            
            html.A("LAD Dashboard", href="/dash/", style={'color': fifth_color, 'text-decoration':'none', 'font-size':'1.5rem'})
        ], style={'text-align':'center', 'display':'flex', 'gap':'3rem', 'align-items':'center', 'justify-content':'center'}
        ), style={'padding': '2rem', 'background-color': second_color}
    ),
    # --- NAVEGAÇÃO PARA PAINEL DE DEMANDAS  --- #
    html.Div([
        html.A("Painel de Demandas", href="#demand-title", style={'color': fifth_color, 'text-decoration': 'none', 'margin': '0 1rem'}),
    ], style={'display': 'flex', 'gap': '1rem', 'align-items': 'center', 'justify-content': 'center'}),

   # --------------------------------- SEÇÃO 1 - SELEÇÃO E GRAF. ANUAL -------------------------------- #
    dbc.Col([

        # --- SELEÇÃO DO ANO  --- #
        
        dbc.Col(
            dcc.Dropdown(
                options=[{'label': str(ano), 'value': str(ano)} for ano in select_anos],
                value=year, 
                id='year_dropdown'      
                ),
                width=2, 
                style={'text-align':'center', 'margin': 'auto', 'margin-bottom':'1rem'}
        ),

        # --- GRÁFICO DE UTILIZAÇÃO ANUAL DOS CLUSTERS  --- #

        dbc.Col(
            dbc.Row(
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader('Uso de máquina anual', style={'background-color': first_color, 'color': second_color}),
                        dcc.Graph(
                            id='graph_annual_usage'
                        )],
                        className='shadow text-center',
                        style={'border': 'none'}
                    ), width=10, 
                    className='mx-auto'
                )
            )
            ,
            width=12
        ),

        # --- SELEÇÃO DO MÊS  --- #

        dbc.Row([
            dbc.Col(
                dcc.Slider(
                    id='month_slider',
                    min=1,
                    max=month,
                    step=1,
                    value=month,
                    marks={
                            1: {'label': 'Janeiro'},
                            2: {'label': 'Fevereiro'},
                            3: {'label': 'Março'},
                            4: {'label': 'Abril'},
                            5: {'label': 'Maio'},
                            6: {'label': 'Junho'},
                            7: {'label': 'Julho'},
                            8: {'label': 'Agosto'},
                            9: {'label': 'Setembro'},
                            10: {'label': 'Outubro'},
                            11: {'label': 'Novembro'},
                            12: {'label': 'Dezembro'}
                    },
                    included=False
                )
            )],
            style={'margin': '0', 'background-color': third_color, 'padding': '1.25rem', 'margin-top':'1rem', 'border-radius':'.5rem'}
        )],
    style={'margin': '1rem 0'}
    ),

    # ------------------------------ SEÇÃO 2 - GRAF. STORAGE E USO MENSAL ------------------------------ #

    dbc.Col(
        dbc.Row([

            # --- GRÁFICO DE USO DO STORAGE --- #

            dbc.Col(
                dbc.Card([
                    dbc.CardHeader('Storage', style={'background-color': first_color, 'color' : second_color}),
                    dbc.CardBody([
                        dbc.Col(
                            dcc.Graph(
                                id='graph_storage'
                            )
                        ),
                        dbc.Row([
                            dbc.Col([
                                html.Span('Utilizado'),
                                html.Div([
                                    html.H5(id='storage_usage', style={'display': 'inline', 'color': 'white'}),
                                    html.Span('GB', style={'color': 'white', 'margin-left': '5px'})
                                ])
                            ]),
                            dbc.Col([
                                html.Span('Disponível'),
                                html.Div([
                                    html.H5(id='storage_availability', style={'display': 'inline', 'color': 'white'}),
                                    html.Span('GB', style={'color': 'white', 'margin-left': '5px'}),
                                ])
                                
                            ]),
                            dbc.Col([
                                html.Span('Capacidade'),
                                html.Div([
                                    html.H5('134206', style={'display': 'inline', 'color': 'white'}),
                                    html.Span('GB', style={'color': 'white', 'margin-left': '5px'}),
                                ])
                            ])
                        ])
                    ], style={'padding-top':'0'}
                    )
                    ],
                    className='shadow text-center', 
                    style={'background-color': third_color, 'color': 'white'}
                ), width=6
            ),

            # --- GRÁFICO DE USO MENSAL DOS CLUSTERS  --- #

            dbc.Col(
                dbc.Card([
                    dbc.CardHeader('Uso de máquina mensal (CPU-Hora)', style={'background-color': first_color, 'color' : second_color}),
                    dbc.CardBody([
                        dbc.Col(
                            dcc.Graph(
                                id='graph_monthly_usage'
                            )
                        ),
                        dbc.Row([
                            dbc.Col([
                                html.Span('Utilizado'),
                                html.H5(id='machine_usage', style={'color': 'white'}),
                            ]),
                            dbc.Col([
                                html.Span('Disponível'),
                                html.H5(id='machine_availability', style={'color': 'white'})
                            ]),
                            dbc.Col([
                                html.Span('Capacidade'),
                                html.H5(id='machine_capacity', style={'color': 'white'})
                            ])
                        ])
                    ], style={'padding-top':'0'}
                    )

                    ],
                    className='shadow text-center', 
                    style={'border': 'none', 'background-color': third_color, 'color': 'white'}
                ), width=6
            )
            
        ])
    ),

    # ------------------------ SEÇÃO 3 - GRAF. CLUSTER E EM 24 X 7 POR GRUPO --------------------------- #

    dbc.Col(
        dbc.Row([

            # --- GRÁFICO DE USO DE MÁQUINA EM 24 X 7 POR GRUPO  --- #

            dbc.Col(
                dbc.Card([
                    dbc.CardHeader('Uso de máquina em 24x7 por grupo', style={'background-color': fourth_color, 'color': 'white'}),
                    dcc.Graph(
                        id='graph_24x7_machine',
                    )],
                    className='shadow text-center',
                    style={'border': 'none'}
                ),
                width=6
            ),
            
            # --- GRÁFICO DE USO DE MÁQUINA EM CLUSTER POR GRUPO  --- #

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Uso de máquina em Cluster por grupo', style={'background-color': fourth_color, 'color': 'white'}),
                    dcc.Graph(
                        id='graph_cluster_machine',
                    )],
                    className='shadow text-center',
                    style={'border': 'none'}
                )],
                width=6
            )

        ]),
        style={'margin': '1rem 0'}
    ),

    # ----------------------------- SEÇÃO 4 - GRAF. STORAGE POR GRUPO ---------------------------------- #

    dbc.Col(
        dbc.Card([
            dbc.CardHeader('Uso de Storage (Cluster + 24x7) por grupo', style={'background-color': first_color, 'color': second_color}),
            dcc.Graph(
                id='graph_storage_group',
            )],
            className='shadow text-center',
            style={'border': 'none'}
        ),
        width=10, 
        className='mx-auto',
        style={'margin': '1rem 0'}
    ),
    
    # ----------------------- SEÇÃO 5 - GRAF. ANUAL (CLUSTER + 24X7) POR GRUPO  ------------------------ #

    dbc.Col([

        # --- GRÁFICO DE USO ANUAL DE MÁQUINA EM CLUSTER POR GRUPO  --- #

        dbc.Col([
            dbc.Card([
                dbc.CardHeader('Uso anual de máquina em Cluster por grupo', style={'background-color': first_color, 'color': second_color}),
                dcc.Graph(
                    id='graph_cluster_usage_group',
                )],
                className='shadow text-center',
                style={'border': 'none', 'margin': '1rem 0'},
            )],
            width=10, 
            className='mx-auto'
        ),

        # --- GRÁFICO DE USO ANUAL DE MÁQUINA EM 24 X 7 POR GRUPO  --- #
               
        dbc.Col([
            dbc.Card([
                dbc.CardHeader('Uso anual de máquina em 24x7 por grupo', style={'background-color': fourth_color, 'color': 'white'}),
                dcc.Graph(
                     id='graph_24x7_usage_group',
                )],
                className='shadow text-center',
                style={'border': 'none', 'margin': '1rem 0'}    
            )],
            width=10, 
            className='mx-auto'
        )]
    ),

    # ---------------------------- SEÇÃO 6 - GRAF. PRODUÇÕES CIENTÍFICAS ------------------------------- #

    dbc.Col([
        dbc.Card([
            dbc.CardHeader(id='graph_production_title', style={'background-color': fourth_color, 'color': 'white'}),
                dcc.Graph(
                     id='graph_production',
                )],
                className='shadow text-center',
                style={'border': 'none'}
            )
        ],
        width=10, 
        className='mx-auto'
        ),


    # -----------------------------SEÇÃO 7 - PAINEL DE DEMANDAS ----------------------------- #
    
    # ----------------------------- TÍTULO ----------------------------- #
    dbc.Col([
    html.H2(
        id="demand-title",
        style={
            'color': fifth_color,  
            'text-align': 'center',  
            'padding': '0.5rem',  
            'margin': '4rem 0 0 0',  
            'font-size': '1.5rem'  
        }
    )
]),
    # ----------------------------- GRÁFICO COMPARATIVO ANUAL ----------------------------- #

    dbc.Col([
        html.H3(
            "Comparativo: Demandas Criadas vs. Erros de Usuário", 
            className="h3-subtitle", 
            style={
                'color': third_color, 
                'text-align': 'center', 
                'background-color': first_color, 
                'font-size': '1rem', 
                'padding': '0.5rem', 
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0'
            }
        ),
        dbc.Card(
            dcc.Graph(
                id="monthly-bar-chart",
                figure=plot_monthly_comparison(),
                style={'height': '320px'}
            ),
            className='shadow text-center',
            style={'background-color': third_color, 
                   'border': 'none', 
                   'margin-top': '0'}
        )
    ], style={'margin': '0 3rem 0 3rem'}),

    # ----------------------------- GRAFICO DISTRIBUIÇÃO DE ERROS DE USUÁRIO POR GRUPO ----------------------------- #
    dbc.Row([
        dbc.Col([
            html.H3(
                "Distribuição de Erros de Usuário por Grupo", 
                className="h3-subtitle", 
                style={
                    'color': third_color, 
                    'text-align': 'center', 
                    'background-color': first_color, 
                    'font-size': '1rem', 
                    'padding': '0.5rem', 
                    'border-radius': '0.5rem 0.5rem 0 0',
                    'margin-bottom': '0'
                }
            ),
            dbc.Card([
                html.Div([
                    dcc.Dropdown(
                        id="month-dropdown",
                        options=[{"label": "Visão Geral", "value": "all"}] + [
                            {"label": month, "value": month} for month in 
                            ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                        ],
                        value=datetime.now().strftime('%b'),
                        className="dropdown-style",
                        style={'width': '40%', 
                               'margin': '0 auto'}
                    )
                ], style={'background-color': COLORS['background'], 
                          'width': '100%', 
                          'padding': '0.5rem'}),
                dcc.Graph(
                    id="pie-chart",
                    style={'height': '400px'} 
                )
            ],
            className='shadow text-center',
            style={'background-color': third_color, 
                   'border': 'none', 
                   'height': '250px', 
                   'margin-top': '0'})
        ], width=8),

        # ----------------------------- LISTA DE DEMANDAS RELACIONADAS A ERROS DE USUÁRIO ----------------------------- #
        dbc.Col([
            html.H3(
                "Lista de Demandas Relacionadas a Erros de Usuário", 
                className="h3-subtitle", 
                style={
                    'color': third_color, 
                    'text-align': 'center', 
                    'background-color': first_color, 
                    'font-size': '1rem', 
                    'padding': '0.5rem', 
                    'border-radius': '0.5rem 0.5rem 0 0',
                    'margin-bottom': '0'
                }
            ),
            dbc.Card([
                dcc.Store(id="filtered-demands-store"),
                html.Ul(
                    id="demand-list", 
                    className="demand-list", 
                    style={
                        'list-style-type': 'none',
                        'padding': '0',
                        'color': fifth_color,
                        'max-height': '480px',  
                        'overflow-y': 'auto',
                        'text-align': 'left',
                        'margin-top': '0'
                    }
                )
            ],
            className='shadow text-center',
            style={
                'background-color': third_color, 
                'border': 'none', 
                'padding': '0 1rem 0 1rem', 
                'height': '250px'
            })
        ], width=4)
    ], style={'margin': '1rem 2rem 0.1rem 2rem'}),

    # ----------------------------- GRÁFICO DE EVOLUÇAO DE DEMANDAS E LISTA DE DEMANDAS PENDENTES ----------------------------- #
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(
                    html.H3(
                        id="funnel-chart-title", 
                        style={
                            'color': third_color, 
                            'text-align': 'center', 
                            'background-color': first_color, 
                            'font-size': '1rem', 
                            'padding': '0.5rem', 
                            'border-radius': '0.5rem 0.5rem 0 0',
                            'margin-bottom': '0',
                            'border': 'none'
                        }
                    ),
                    style={
                        'padding': '0',
                        'border': 'none',
                    }
                ), 
                dcc.Graph(
                    id="funnel-chart",
                    style={"height": "220px"} 
                )
            ],
            className='shadow text-center',
            style={
                'background-color': third_color, 
                'border': 'none', 
                'margin': '0',
            })
        ], width=8), 

        # LISTA DE DEMANDAS PENDENTES
        dbc.Col([
            html.H3(
                "Lista de Demandas Pendentes", 
                id="open-demand-title",
                className="h3-subtitle", 
                style={
                    'color': third_color, 
                    'text-align': 'center', 
                    'background-color': first_color, 
                    'font-size': '1rem', 
                    'padding': '0.5rem', 
                    'border-radius': '0.5rem 0.5rem 0 0',
                    'margin-bottom': '0'
                }
            ),
            dbc.Card([
                dcc.Store(id="open-demands-store"),
                html.Ul(
                    id="open-demand-list", 
                    className="demand-list", 
                    style={
                        'list-style-type': 'none',
                        'padding': '0',
                        'color': fifth_color,
                        'max-height': '400px',  
                        'overflow-y': 'auto',
                        'text-align': 'left',
                        'margin-top': '0'
                    }
                )
            ],
            className='shadow text-center',
            style={
                'background-color': third_color, 
                'border': 'none', 
                'padding': '0 1rem 0 1rem', 
                'height': '220px'
            })
        ], width=4) 
    ], style={'margin': '1rem 2rem 0.1rem 2rem'}),

    # ----------------------------- FINAL GRÁFICOS DEMANDAS ----------------------------- #

    # SCROLL TO TOP
    html.Div([
        html.A("↑", href="#", style={
            'color': second_color,
            'text-decoration': 'none',
            'background-color': first_color,
            'padding': '0.3rem 1rem',
            'border-radius': '50%',
            'font-size': '1.4rem',
            'display': 'flex',
            'align-items': 'center',
            'justify-content': 'center',
            'box-shadow': '0 6px 12px rgba(0, 0, 0, 0.2)',
            'position': 'fixed',
            'bottom': '20px',
            'right': '20px',
            'z-index': '1000',
            'cursor': 'pointer',
    }, title="Voltar ao Início")
    ], style={'text-align': 'center'}),

], style={'background-color':second_color, 'padding':'1rem', 'min-width':'900px'}
)

# ---------------------------------------  CALLBACK - DASH --------------------------------------------- #

@app.callback(
    # --- GRÁFICOS DO LAYOUT (EM ORDEM)  --- #
    Output('graph_annual_usage', 'figure'),
    Output('graph_storage', 'figure'),
    Output('graph_monthly_usage', 'figure'),
    Output('graph_24x7_machine', 'figure'),
    Output('graph_cluster_machine', 'figure'),
    Output('graph_storage_group', 'figure'),
    Output('graph_cluster_usage_group', 'figure'),
    Output('graph_24x7_usage_group', 'figure'),
    Output('graph_production', 'figure'),

    # --- VALORES USADOS EM GRÁFICOS  --- #
    Output('storage_usage', 'children'),
    Output('storage_availability', 'children'),
    Output('machine_usage', 'children'),
    Output('machine_availability', 'children'),
    Output('machine_capacity', 'children'),

    # --- SELEÇÃO DE MÊS E ANO  --- #
    Output('month_slider', 'value'),
    Output('month_slider', 'max'),
    Input('year_dropdown', 'value'),
    Input('month_slider', 'value')
)

# -----------------------------------  FUNÇÃO PRINCIPAL - DASH ----------------------------------------- #

def update_figure(yearValue, value):
    
    # ------------------------------------- CONFIGURAÇÕES ---------------------------------------------- #
    month = 0
    global x
    df_annual = pd.DataFrame()
    days = month_days(value, yearValue)

    # --- CRIA UM RELATÓRIO ANUAL --- #
    for dataframe in os.listdir('relatorios/' + yearValue):
        df_annual = pd.concat([df_annual, pd.read_excel(os.path.join('relatorios/' + yearValue, dataframe))])
        month += 1

    # --- EVITA QUE TENTE ACESSAR UM MÊS QUE AINDA NÃO CHEGOU --- #
    if (month < value):
        value = month    

    x = month

    # --- CRIA UM RELATÓRIO MENSAL --- #
    df_data = read_database_excel(yearValue, value)

    # ---------------------- USO DAS MÁQUINAS EM CLUSTER E 24 X 7- ANUAL ------------------------------- #

    # --- CÁLCULO SIMPLES (CORES - HORAS/DIA - DIA/MÊS) --- #
    machine_capacity = (2108*24*days)

    # --- CRIA UM RELATÓRIO DE USO DE MÁQUINA, AGRUPADO POR MÊS --- #
    df_machine_usage = df_annual[['Máquina em Cluster', 'Máquina em 24x7', 'Mês']].sort_values(by=['Mês'], ascending=False)               
    df_machine_usage = df_machine_usage.groupby(['Mês']).agg({
        'Máquina em 24x7' : 'sum',
        'Máquina em Cluster' : 'sum'
    })

    # --- CRIA UMA COLUNA DE DISPONIBILIDADE --- #
    machine_availability_annual = []

    for index, row in df_machine_usage.iterrows():
        total_usage = row['Máquina em 24x7'] + row['Máquina em Cluster']
        capacity = 2108 * 24 * month_days(index, yearValue)
        machine_availability_annual.append(capacity - total_usage)

    df_machine_usage["Disponível"] = machine_availability_annual

    # --- CRIA O GRÁFICO --- #
    graph_annual_usage = px.bar(
        df_machine_usage,
        y=["Máquina em 24x7", "Máquina em Cluster", "Disponível"],
        labels={'value':'Uso (CPU-Hora)', 'variable':'Tipo de uso'},
        color_discrete_map={"Disponível": "white", "Máquina em Cluster": "#ef553b", "Máquina em 24x7": "#636efa"} 
        ) 
 
    # ------------------ USO DE STORAGE (CLUSTER E 24 X 7) MENSAL E EM GRUPO --------------------------- #

    # --- CRIA UM RELATÓRIO COM AS COLUNAS DE STORAGE --- #
    # --- TAMBÉM AS LINHAS COM MENOS DE DOIS VALORES E ADICIONA UM ZERO NAS CASAS VAZIAS --- #
    df_storage = df_data[['Projeto', 'Storage em cluster(GB)', 'Storage em 24x7(GB)']].dropna(thresh=2).fillna(0)  

    # --- ADICIONA UMA COLUNA DE TOTAL (Cluster + 24x7) --- #                                                                              
    df_storage['Total'] = df_storage['Storage em cluster(GB)'] + df_storage['Storage em 24x7(GB)']
    
    # --- DEFINÇÕES DO STORAGE --- #      
    storage_capacity = 134206
    storage_usage = df_storage['Total'].sum()
    storage_availability = storage_capacity - storage_usage

    # --- ADICIONA UMA LINHA DE DISPONIBILIDADE --- #  
    new_row = pd.DataFrame([['Disponível', '', '', storage_availability]], columns=df_storage.columns)
    df_storage = pd.concat([new_row, df_storage], ignore_index=True)   

    # --- CRIA O GRÁFICO MENSAL --- #
    storage_usage_percent = round((storage_usage / storage_capacity) * 100, 2)
    annotations = [
        dict(x=0, y=['Total'], text="Utilizado", xanchor="left", showarrow=False),
        dict(x=storage_usage, y=['Total'], text=f"{storage_usage_percent}%", xanchor="auto", showarrow=False)
    ]

    graph_storage = go.Figure(
        data=[
            go.Bar(name='Utilizado', x=[storage_usage], y=['Total'], orientation='h', marker_color='darkorange'),
            go.Bar(name='Disponível', x=[storage_availability], y=['Total'], orientation='h', marker_color='#efefef')
        ]
    )
    graph_storage.update_layout(
        barmode='stack',
        yaxis={'visible': False, 'showticklabels': False},
        xaxis={'visible': False, 'showticklabels': False, 'showline': False},
        height=100,
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=0, b=10, t=0),
        legend=dict(yanchor="top", y=0.5, xanchor="right", x=1.2),
        annotations=annotations
    )

    # --- CRIA O GRÁFICO DE GRUPOS --- # 
    labels = df_storage['Projeto']
    values = df_storage['Total']

    graph_storage_group = go.Figure(
        data=[
            go.Pie(labels = labels, values = values, pull = [0.1])
        ],
        layout_showlegend=False
    )
    graph_storage_group.update_traces(textposition='inside', textinfo = 'label+percent')

    # ------------------ USO DE MÁQUINA MENSAL E POR GRUPO (24X7 E CLUSTER) ---------------------------- #
    
    # --- DEFINIÇÃO DA MÁQUINA EM 24 X 7 --- # 
    df_machine_24x7 = df_data[['Projeto', 'Máquina em 24x7']].dropna().sort_values(by=['Máquina em 24x7'], ascending=False)   
    machine_usage_24x7 = df_machine_24x7['Máquina em 24x7'].sum()

    # --- DEFINIÇÃO DA MÁQUINA EM CLUSTER --- # 
    df_machine_cluster = df_data[['Projeto', 'Máquina em Cluster']].dropna().sort_values(by=['Máquina em Cluster'], ascending=False)
    machine_usage_cluster = df_machine_cluster['Máquina em Cluster'].sum()

    # --- DEFINIÇÃO DA MÁQUINA MENSAL --- # 
    machine_usage = machine_usage_24x7 + machine_usage_cluster
    machine_availability = machine_capacity - machine_usage
    machine_usage_percent = round((machine_usage / machine_capacity) * 100, 2)

    # --- CRIA O GRÁFICO DE USO DE MÁQUINA MENSAL --- #
    annotations = [
        dict(x=0, y=['Total'], text="Utilizado", xanchor="left", showarrow=False),
        dict(x=machine_usage_24x7+machine_usage_cluster, y=['Total'], text=str(machine_usage_percent)+'%', xanchor="auto", showarrow=False)
    ]

    graph_monthly_usage = go.Figure(
        data=[
            go.Bar(name='24x7', x=[machine_usage_24x7], y=['Total'], orientation='h', marker_color='rgb(20, 200, 255)'),
            go.Bar(name='Cluster', x=[machine_usage_cluster], y=['Total'], orientation='h', marker_color='rgb(30, 110, 255)'),
            go.Bar(name='Disponível', x=[machine_availability], y=['Total'], orientation='h', marker_color='#efefef')
        ]
    )

    graph_monthly_usage.update_layout(
        barmode='stack',
        yaxis={'visible': False, 'showticklabels': False},
        xaxis={'visible': False, 'showticklabels': False, 'showline': False},
        height=100,
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=0, b=10, t=0),
        legend=dict(yanchor="top", y=0.7, xanchor="right", x=1.2),
        annotations=annotations
    )

    # --- CRIA O GRÁFICO DE MÁQUINA EM 24 X 7 POR GRUPO --- # 
    graph_24x7_machine = px.bar(
        df_machine_24x7.head(10),
        x="Projeto",
        y="Máquina em 24x7",
        color="Projeto"
    ).update(layout_showlegend=False)

    # --- CRIA O GRÁFICO DE MÁQUINA EM CLUSTER POR GRUPO --- #
    graph_cluster_machine = px.bar(
        df_machine_cluster,
        x="Projeto",
        y="Máquina em Cluster",
        color="Projeto"
        ).update(layout_showlegend=False)

    # -------------------- USO DE MÁQUINA ANUAL POR GRUPO (24X7 E CLUSTER) ----------------------------- #

    # --- DEFINIÇÃO DA MÁQUINA ANUAL EM CLUSTER POR GRUPO --- #
    df_machine_usage_cluster = df_annual[['Projeto', 'Máquina em Cluster', 'Mês']].dropna().sort_values(by=['Mês']) 

    # --- DEFINIÇÃO DA MÁQUINA ANUAL EM 24 X 7 POR GRUPO --- #
    df_machine_usage_24x7 = df_annual[['Projeto', 'Máquina em 24x7', 'Mês']].dropna().sort_values(by=['Mês'])

    # --- CRIA O GRÁFICO DE MÁQUINA EM CLUSTER POR GRUPO --- #        
    graph_cluster_usage_group = px.line(
        df_machine_usage_cluster, 
        x = 'Mês', 
        y = 'Máquina em Cluster',
        color = 'Projeto'
    )                                                          

    # --- CRIA O GRÁFICO DE MÁQUINA EM 24 X 7 POR GRUPO --- #  
    graph_24x7_usage_group = px.line(
        df_machine_usage_24x7, 
        x = 'Mês', 
        y = 'Máquina em 24x7',
        color = 'Projeto'
    )
    
    # ---------------------------- GRÁF. PRODUÇÕES CIENTÍFICAS ----------------------------------------- #
        # --- CRIA UM RELATÓRIO DE PRODUÇÕES - TEMPORÁRIO! --- #
    # df_production = pd.read_excel('relatorios/producoes.xlsx')

    # --- LÊ O ARQUIVO JSON EXPORT.JSON E CRIA UM DATAFRAME COM AS PRODUÇÕES CIENTÍFICAS --- #
    # Agora os dados de produção científica são lidos diretamente do export.json,
    # facilitando a atualização sem necessidade de editar o arquivo producoes.xlsx.
    with open('export.json', 'r', encoding='utf-8') as f:
        export_data = json.load(f)
    producao = export_data.get('producao', [])
    df_production = pd.DataFrame(producao)

    # --- CRIA O GRÁFICO DE PRODUÇÕES CIENTÍFICAS --- #
    graph_production = px.bar(
        df_production,
        x="Unidade/Escola",
        y=["Produção Científica", "TCC, Dissertação ou Tese"],
        barmode="group",
        labels={'value':'Quantidade', 'variable':'Tipo de Publicação'},
        text_auto=True
        )

    # TEMPORÁRIO! - CALCULA AS HORAS DE SERVIÇO, CONFORME O ANO 

    sum_service = df_annual[['Serviço']].dropna().sum()
    print(sum_service.to_string())
    sum_machine = df_annual[['Máquina em Cluster']].dropna().sum()
    print(sum_machine.to_string())
    sum_24x7 = df_annual[['Máquina em 24x7']].dropna().sum()
    print(sum_24x7.to_string())

    # --------------------------------- RETORNO DA FUNÇÃO ---------------------------------------------- #

    return [
        # --- GRÁFICOS DO LAYOUT (EM ORDEM)  --- #
        graph_annual_usage,
        graph_storage,
        graph_monthly_usage,
        graph_24x7_machine, 
        graph_cluster_machine, 
        graph_storage_group,
        graph_cluster_usage_group,
        graph_24x7_usage_group,
        graph_production,

        # --- VALORES USADOS EM GRÁFICOS  --- #
        storage_usage, 
        storage_availability,
        machine_usage, 
        machine_availability,
        machine_capacity,

        # --- SELEÇÃO DE MÊS E ANO  --- #
        value,
        month
    ]

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

# ---------------------------  CALLBACK - DEMANDAS --------------------------- #

# ATUALIZAR O TITULO
@app.callback(
    Output("demand-title", "children"),
    [Input("year_dropdown", "value")]
)
def update_demand_title(selected_year):
    return f"Painel de Demandas {selected_year}"

# ATUALIZAR O GRAFICO DE GRUṔOS
@app.callback(
    Output("pie-chart", "figure"),
    [Input("month-dropdown", "value"),
     Input("year_dropdown", "value")]
)
def update_pie_chart(selected_month, selected_year):
    # Filtrar os dados com base no ano selecionado
    filtered_df, filtered_demandas_erro = filter_data_by_year(selected_year)
    # Filtrar os dados com base no mês selecionado
    if selected_month != "all":
        filtered_demandas_erro = filtered_demandas_erro[filtered_demandas_erro["Month"] == selected_month]

    # Extrair os nomes dos grupos
    names = extract_names_from_titles(filtered_demandas_erro)
    if names:
        name_counts = pd.Series(names).value_counts()
        total_demandas = name_counts.sum()

        return {
            "data": [
                go.Pie(
                    labels=name_counts.index,
                    values=name_counts.values,
                    hole=0.3,
                    textinfo="percent+value",
                    hovertemplate="<b>Grupo:</b> %{label}<br><b>Quantidade:</b> %{value}<br><b>Percentual:</b> %{percent}<extra></extra>"
                )
            ],
            "layout": go.Layout(
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"],
                font={"color": COLORS["text"]},
                margin=dict(l=20, r=20, t=20, b=20),
                annotations=[
                    {
                        "text": f"Total: {total_demandas}",
                        "font": {"size": 14, "color": COLORS["text"]},
                        "showarrow": False,
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.5,
                        "y": 0.5,
                    }
                ]
            )
        }
    # Se não houver dados, retornar um gráfico vazio
    return {
        "data": [],
        "layout": go.Layout(
            annotations=[
                {
                    "text": "Nenhuma demanda especial registrada no mês selecionado",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20, "color": COLORS["gray"]},
                }
            ],
            showlegend=False,
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
        )
    }

# ATUALIZAR A LISTA DE DEMANDAS COM BASE NO MES SELECIONADO
@app.callback(
    [Output("filtered-demands-store", "data"),
     Output("demand-list", "children")],
    [Input("month-dropdown", "value"),
     Input("year_dropdown", "value")]
)
def update_demand_list(selected_month, selected_year):
    # Filtrar os dados com base no ano selecionado
    _, filtered_demandas_erro = filter_data_by_year(selected_year)
    # Filtrar os dados com base no mês selecionado
    if selected_month != "all":
        filtered_demandas_erro = filtered_demandas_erro[filtered_demandas_erro["Month"] == selected_month]

    # Verificar se há dados filtrados
    if filtered_demandas_erro.empty:
        return [], [html.Li("Nenhuma demanda especial registrada no mês e ano selecionados", 
                            style={"color": COLORS["gray"], "font-size": "16px", "text-align": "center"})]

    # Criar a lista de demandas
    demand_list = [
        html.Li(
            html.A(
                title, 
                href=url, 
                target="_blank", 
                className="demand-list-a",  
                title="Clique para abrir no GitHub",
                style={
                "color": COLORS['text'],  
                  
            }
            ),
            className="demand-list-li" ,
            style={"border-bottom": "1px solid gray", 
                   "padding": "0.5rem 0"} 
        )
        for title, url in zip(filtered_demandas_erro["Título"], filtered_demandas_erro["URL"])
    ]

    # Retornar os dados filtrados e a lista de demandas
    return filtered_demandas_erro.to_dict("records"), demand_list

# ATUALIZAR O GRAFICO DE BARRAS
@app.callback(
    Output("monthly-bar-chart", "figure"),
    [Input("year_dropdown", "value")]
)
def update_monthly_comparison(selected_year):
    # Filtrar os dados com base no ano selecionado
    filtered_df, filtered_demandas_erro = filter_data_by_year(selected_year)

    # Criar os gráficos com os dados filtrados
    monthly_counts = filtered_df["Month"].value_counts()
    monthly_error_counts = filtered_demandas_erro["Month"].value_counts()

    # Ordenar os meses
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    months_with_data = [m for m in month_order if m in monthly_counts.index]
    monthly_counts = monthly_counts.reindex(months_with_data)
    monthly_error_counts = monthly_error_counts.reindex(months_with_data, fill_value=0)

    return {
        "data": [
            go.Bar(
                x=monthly_counts.index,
                y=monthly_counts.values,
                name="Demandas Abertas no mês",
                marker={"color": COLORS["bar1"]},
                text=monthly_counts.values,
                textposition="outside",
                width=0.6,
                hovertemplate="<b>Mês:</b> %{x}<br><b>Demandas Abertas:</b> %{y}<extra></extra>"
            ),
            go.Bar(
                x=monthly_counts.index,
                y=monthly_error_counts.values,
                name="Erros de Usuário",
                marker={"color": COLORS["bar2"]},
                text=monthly_error_counts.values,
                textposition="outside",
                width=0.6,
                hovertemplate="<b>Mês:</b> %{x}<br><b>Erros de Usuário:</b> %{y}<extra></extra>"
            )
        ],
        "layout": go.Layout(
            xaxis={"title": "Mês", "color": COLORS["text"]},
            yaxis={"title": "Quantidade de Demandas Abertas", 
                   "color": COLORS["text"],
                   "automargin": True,
                   "range": [0, max(monthly_counts.max(), monthly_error_counts.max()) * 1.1]},
            barmode="overlay",
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font={"color": COLORS["text"]},
            hovermode="closest",
            margin=dict(l=70, r=30, t=40, b=60),
        )
    }

# ATUALIZAR O TÍTULO DO GRAF. EVOLUÇAO DAS DEMANDAS COM O ANO SELECIONADO
@app.callback(
    Output("funnel-chart-title", "children"),
    [Input("year_dropdown", "value"),
     Input("month-dropdown", "value")]
)
def update_funnel_chart_title(selected_year, selected_month):
    if selected_month == "all":
        return f"Evolução das Demandas - {selected_year}"
    else:
        month_names = {
            "Jan": "Janeiro", "Feb": "Fevereiro", "Mar": "Março", "Apr": "Abril",
            "May": "Maio", "Jun": "Junho", "Jul": "Julho", "Aug": "Agosto",
            "Sep": "Setembro", "Oct": "Outubro", "Nov": "Novembro", "Dec": "Dezembro"
        }
        month_name = month_names.get(selected_month, selected_month)
        return f"Ciclo de Demandas - {month_name} {selected_year}"
    
# Callback para atualizar o gráfico de ciclos
@app.callback(
    Output("funnel-chart", "figure"),
    [Input("year_dropdown", "value"),
     Input("month-dropdown", "value")]
)
def update_funnel_chart(selected_year, selected_month):
    # Filtrar os dados com base no ano selecionado
    filtered_df, _ = filter_data_by_year(selected_year)

    # Filtrar os dados com base no mês selecionado
    if selected_month != "all":
        filtered_df = filtered_df[filtered_df["Month"] == selected_month]

    # Gerar o gráfico de funil com os dados filtrados
    return plot_horizontal_bar_chart(filtered_df)

# ATUALIZAR O TÍTULO DA LISTA DE DEMANDAS PENDENTES COM A QUANTIDADE DE DEMANDAS
@app.callback(
    Output("open-demand-title", "children"),
    [Input("open-demands-store", "data")]
)
def update_open_demand_title(open_demands):
    # Verificar se há demandas pendentes
    num_open_demands = len(open_demands) if open_demands else 0
    return f"Lista de Demandas Pendentes ({num_open_demands})"

# ATUALIZAR A LISTA DE DEMANDAS PENDENTES
@app.callback(
    [Output("open-demands-store", "data"),
     Output("open-demand-list", "children")],
    [Input("month-dropdown", "value"),
     Input("year_dropdown", "value")]
)
def update_open_demand_list(selected_month, selected_year):
    # Filtrar os dados com base no ano selecionado
    filtered_df, _ = filter_data_by_year(selected_year)
    
    # Filtrar as demandas abertas
    open_demands = filtered_df[filtered_df["Status"].str.lower() == "open"]
    
    # Filtrar os dados com base no mês selecionado
    if selected_month != "all":
        open_demands = open_demands[open_demands["Month"] == selected_month]

    # Verificar se há dados filtrados
    if open_demands.empty:
        return [], [html.Li("Nenhuma demanda aberta registrada no mês e ano selecionados", 
                            style={"color": COLORS["gray"], "font-size": "16px", "text-align": "center"})]

    # Criar a lista de demandas pendentes
    open_demand_list = [
        html.Li(
            html.A(
                title, 
                href=url, 
                target="_blank", 
                className="demand-list-a",  
                title="Clique para abrir no GitHub",
                style={
                    "color": COLORS['text'],  
                }
            ),
            className="demand-list-li",
            style={"border-bottom": "1px solid gray", 
                   "padding": "0.5rem 0"} 
        )
        for title, url in zip(open_demands["Título"], open_demands["URL"])
    ]

    # Retornar os dados filtrados e a lista de demandas abertas
    return open_demands.to_dict("records"), open_demand_list

# ---------------------------  FINAL CALLBACK - DASH DEMANDAS --------------------------- #

# ---------------------------------------  CALLBACK PRODUÇÕES - ATUALIZAÇÃO AUTOMÁTICA DO TÍTULO --------------------------------------- #
# Atualiza o título do gráfico de produções científicas com base no ano mais recente registrado.
@app.callback(
    Output('graph_production_title', 'children'),
    [Input('year_dropdown', 'value')]
)
def update_graph_production_title(_):
    with open('export.json', 'r', encoding='utf-8') as f:
        export_data = json.load(f)
    ultima_atualizacao = export_data.get('ultima_atualizacao', 0)
    return f"Produções científicas por Unidade (2015-{ultima_atualizacao})"

# --------------------------------  DEFINIÇÃO DE CLASSES - FLASK --------------------------------------- #

class BaseModel(Model):
    class Meta:
        database = database

class Cluster(BaseModel):
    name = CharField(unique=True)
    description = TextField()
    date_beg = DateField()
    date_end = DateField()
    status = BooleanField()

class Equipamento(BaseModel):
    cluster = ForeignKeyField(Cluster, backref='equipamentos', on_delete='cascade')
    hostname = CharField()
    modelo = CharField()
    tipo = CharField()
    patrimonio = CharField()
    serviceTag = CharField()
    nucleo = IntegerField()
    memoria = IntegerField()
    disco = IntegerField()
    date_beg = DateField()
    date_end = DateField()
    status = BooleanField()
    
class Grupo(BaseModel):
    nome = CharField(unique=True)
    demanda = IntegerField()
    unidade = CharField()
    coordenador = CharField()
    status = BooleanField()
    date_beg = DateField()
    observacoes = TextField()
    tipo = CharField()

class Usuario(BaseModel):
    grupo = ForeignKeyField(Grupo, backref='usuarios')
    nome = CharField()
    email = CharField()
    date_beg = DateField()
    date_end = DateField()
    observacoes = TextField()
    status = BooleanField()

class Producao(BaseModel):
    ano = IntegerField()
    unidade = CharField()
    cientifica = IntegerField()
    tcc = IntegerField()

# --------------------------------  DEFINIÇÃO DE FUNÇÕES - FLASK --------------------------------------- #

def create_tables():
    with database:
        database.create_tables([Cluster, Equipamento, Grupo, Usuario, Producao])

def drop_tables():
    with database:
        database.drop_tables([Cluster, Equipamento, Grupo, Usuario])

def get_object_or_404(model, *expressions):
    try:
        return model.get(*expressions)
    except model.DoesNotExist:
        abort(404)

@server.before_request
def before_request():
    g.db = database
    g.db.connect()

@server.after_request
def after_request(response):
    g.db.close()
    return response

# -------------------------  DEFINIÇÃO DE ROTAS E DIRECIONAMENTOS - FLASK ------------------------------ #
# --- HOMEPAGE  --- #
@server.route('/', methods=['GET', 'POST'])
def homepage():
    lista_cluster = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)
    lista_grupo = Grupo.select().where(Grupo.status == True).order_by(Grupo.nome).prefetch(Usuario)

    return render_template('homepage.html', lista_cluster=lista_cluster, lista_grupo=lista_grupo)

# --- DASH APP  --- #
@server.route("/dash")
def dash_app():
    return app.index()

# --- CONFIGURAÇÕES DE CLUSTERS  --- #
@server.route('/cluster/<clusterName>', methods=['GET', 'POST'])
def cluster(clusterName=None):
    mensagem = None
    form = request.form

    # --- CASO SEJA CADASTRO DE CLUSTER  --- #
    if clusterName == 'cadastro':
        if request.method == 'POST':
            name = form['cluster_name']

            if name:
                if create_cluster(name, form['description']):
                    return redirect(url_for('homepage'))
                else: mensagem = 'Cluster já existe'

        return render_template('cluster.html', clusterName='cadastro', msg=mensagem)

    # --- CASO SEJA ATUALIZAÇÃO DE CLUSTER  --- #
    else:
        if clusterName:
            cluster = get_object_or_404(Cluster, Cluster.name == clusterName)

            if request.method == 'POST':
                name = form['cluster_name']
                description = form['description']
                status = form['status']

                if name:
                    if update_cluster(cluster, name, description, status):
                        return redirect(url_for('homepage'))
                    else:
                        mensagem = 'Cluster já existe'

        return render_template('cluster.html', cluster=cluster, msg=mensagem)

def create_cluster(name, description):
    try:
        with database.atomic():
            Cluster.create(
                name=name,
                description=description,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False

def update_cluster(cluster, name, description, status):
    try:
        cluster.name = name
        cluster.description = description
        if status == 'desativar':
            cluster.status = False
            cluster.date_end = datetime.now().strftime('%d-%m-%Y')
        else:
            cluster.status = True
        cluster.save()
        return True
    except IntegrityError:
        return False

# --- CONFIGURAÇÕES DE EQUIPAMENTOS  --- #
@server.route('/equipamento/<equipName>', methods=['GET', 'POST'])
def equipamento(equipName=None):
    mensagem = None
    lista_cluster = Cluster.select().where(Cluster.status == True).order_by(Cluster.name).prefetch(Equipamento)
    form = request.form

    # --- CASO SEJA CADASTRO DE EQUIPAMENTO --- #
    if equipName == 'cadastro':
        if request.method == 'POST':

            cluster = Cluster.get(Cluster.name == form['equip_cluster_name'])
            hostname = form['hostname']

            if hostname:
                if create_equipamento(cluster, hostname, form['modelo'], form['tipo'], form['patrimonio'], form['serviceTag'], form['nucleo'], form['memoria']):
                    redirect(url_for('homepage'))
                else: mensagem = 'Equipamento já existe'

        return render_template('equipamento.html', equipName='cadastro', msg=mensagem, lista_cluster=lista_cluster)
    
    # --- CASO SEJA ATUALIZAÇÃO DE EQUIPAMENTO --- #
    else:
        if equipName:
            equipamento = get_object_or_404(Equipamento, Equipamento.hostname == equipName)
            if request.method == 'POST':

                cluster = Cluster.get(Cluster.name == request.form['equip_cluster_name'])
                hostname = form['hostname']
            
                if hostname:
                    if update_equipamento(equipamento, cluster, hostname, form['modelo'], form['tipo'], form['patrimonio'], form['serviceTag'], form['nucleo'], form['memoria'], form['status']):
                        return redirect(url_for('homepage'))
                    else: mensagem='Equipamento já existe'

        return render_template('equipamento.html', equipamento=equipamento, msg=mensagem, lista_cluster=lista_cluster)
    
def create_equipamento(cluster, hostname, modelo, tipo, patrimonio, serviceTag, nucleo, memoria):
    try:
        with database.atomic():
            Equipamento.create(
                cluster=cluster,
                hostname=hostname,
                modelo=modelo,
                tipo=tipo,
                patrimonio=patrimonio,
                serviceTag=serviceTag,
                nucleo=nucleo,
                memoria=memoria,
                disco=0,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False

def update_equipamento(equipamento, cluster, hostname, modelo, tipo, patrimonio, serviceTag, nucleo, memoria, status):
    try:
        equipamento.cluster = cluster
        equipamento.hostname = hostname
        equipamento.modelo = modelo
        equipamento.tipo = tipo
        equipamento.patrimonio = patrimonio
        equipamento.serviceTag = serviceTag
        equipamento.nucleo = nucleo
        equipamento.memoria = memoria

        if status == 'desativar':
            equipamento.status = False
            equipamento.date_end=datetime.now().strftime('%d-%m-%Y')
        else:
            equipamento.status = True

        equipamento.save()
        return True
    except IntegrityError:
        return False
    
# --- CONFIGURAÇÕES DE GRUPOS  --- #
@server.route('/grupo/<groupName>', methods=['GET', 'POST'])
def grupo(groupName=None):
    mensagem = None
    form = request.form
    lista_grupo = Grupo.select().order_by(Grupo.nome)

    # --- CASO SEJA CADASTRO DE GRUPO --- #
    if groupName == 'cadastro':
        if request.method == 'POST':

            nome = form['nome']

            if nome:
                if create_grupo(nome, form['demanda'], form['unidade'], form['coordenador'], form['observacoes'], form['tipo']):
                    return redirect(url_for('homepage'))
                else: mensagem = 'Grupo já existe'

        return render_template('grupo.html', groupName='cadastro', msg=mensagem, lista_grupo=lista_grupo)
    
    # --- CASO SEJA ATUALIZAÇÃO DE GRUPO --- #
    else:
        if groupName:
            grupo = get_object_or_404(Grupo, Grupo.nome == groupName)
            if request.method == 'POST':

                nome = form['nome']

                if nome:
                    if update_grupo(grupo, nome, form['demanda'], form['unidade'], form['coordenador'], form['observacoes'], form['tipo'], form['status']):
                        return redirect(url_for('homepage'))
                    else: mensagem = 'Grupo já existe'
                    
        return render_template('grupo.html', grupo=grupo, msg=mensagem, lista_grupo=lista_grupo)

def create_grupo(nome, demanda, unidade, coordenador, observacoes, tipo):
    try:
        with database.atomic():
            Grupo.create(
                nome = nome,
                demanda = demanda,
                unidade = unidade,
                coordenador = coordenador,
                observacoes = observacoes,
                tipo = tipo,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False
    
def update_grupo(grupo, nome, demanda, unidade, coordenador, observacoes, tipo, status):
    try:
        grupo.nome = nome
        grupo.demanda = demanda
        grupo.unidade = unidade
        grupo.coordenador = coordenador
        grupo.observacoes = observacoes
        grupo.tipo = tipo

        if status == 'desativar':
            grupo.status = False
            grupo.date_end=datetime.now().strftime('%d-%m-%Y')
        else: grupo.status = True

        grupo.save()
        return True
    except IntegrityError:
        return False

# --- LISTA DE USUÁRIOS POR GRUPO  --- #  
@server.route('/grupo/<groupName>/usuarios')
def lista_usuarios(groupName):
    grupo = Grupo.get_or_none(Grupo.nome == groupName)
    if not grupo:
        abort(404)
    usuarios = Usuario.select().where(Usuario.grupo == grupo)
    return render_template('lista_usuarios.html', grupo=grupo, usuarios=usuarios)

# --- CONFIGURAÇÕES DE USUÁRIOS  --- #
@server.route('/usuario/<userName>', methods=['GET', 'POST'])
def usuario(userName=None):
    mensagem=None
    form = request.form
    lista_grupo = Grupo.select().where(Grupo.status == True).order_by(Grupo.nome).prefetch(Usuario)
    
    # --- CASO SEJA CADASTRO DE USUÁRIO --- #
    if userName == 'cadastro':
        if request.method == 'POST':
            
            grupo = Grupo.get(Grupo.nome == request.form['group_name'])
            nome = form['nome']

            if nome:
                print("ESTOU AQUI")
                if (create_usuario(grupo, nome, form['email'], form['observacoes'])):
                    return redirect(url_for('homepage'))
                else: mensagem = 'Usuario já existe'

        return render_template('usuario.html', userName='cadastro', msg=mensagem, lista_grupo=lista_grupo)
    
    # --- CASO SEJA ATUALIZAÇÃO DE USUÁRIO --- #
    else:
        if userName:
            usuario = get_object_or_404(Usuario, Usuario.nome == userName)
            if request.method == 'POST':

                grupo = Grupo.get(Grupo.nome == form['group_name'])
                nome = form['nome']

                if nome:
                    if (update_usuario(usuario, grupo, nome, form['email'], form['observacoes'], form['status'])):
                        return redirect(url_for('homepage'))
                    else: mensagem = 'Usuario já existe'

        return render_template('usuario.html', usuario=usuario, msg=mensagem, lista_grupo=lista_grupo)

def create_usuario(grupo, nome, email, observacoes):
    try:
        with database.atomic():
            Usuario.create(
                grupo=grupo,
                nome=nome,
                email=email,
                observacoes=observacoes,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False

def update_usuario(usuario, grupo, nome, email, observacoes, status):
    try:
        usuario.grupo = grupo
        usuario.nome = nome
        usuario.email = email
        usuario.observacoes = observacoes
        if status == 'desativar':
            usuario.status = False
            usuario.date_end=datetime.now().strftime('%d-%m-%Y')
        else: 
            usuario.status = True
        usuario.save()
        return True
    except IntegrityError:
        return False
    
# --- CONFIGURAÇÕES DE REGISTRO DE PRODUÇÕES --- #
@server.route('/producao', methods=['GET', 'POST'])    
def registrar_producao():
    if request.method == 'POST':
        unidade = request.form['unidade']
        cientifica = int(request.form['cientifica'])
        tcc = int(request.form['tcc'])
        ano = int(request.form['ano'])

        # Salva no banco de dados
        prod, created = Producao.get_or_create(
            ano=ano,
            unidade=unidade,
            defaults={'cientifica': cientifica, 'tcc': tcc}
        )
        if not created:
            prod.cientifica += cientifica
            prod.tcc += tcc
            prod.save()
            
        # Lê o arquivo export.json
        with open('export.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        producao = data.get('producao', [])

        # Atualiza o campo "ano" se o ano postado for maior
        ano = int(request.form['ano'])
        ultima_atualizacao = data.get('ultima_atualizacao', 0)
        if ano > ultima_atualizacao:
            data['ultima_atualizacao'] = ano

        # Soma as produções na unidade especificada
        for item in producao:
            if item['Unidade/Escola'] == unidade:
                item['Produção Científica'] += cientifica
                item['TCC, Dissertação ou Tese'] += tcc
                break
        else:
            producao.append({
                'Unidade/Escola': unidade,
                'Produção Científica': cientifica,
                'TCC, Dissertação ou Tese': tcc
            })
        data['producao'] = producao

        # Salva as alterações no export.json
        with open('export.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Exibe uma mensagem de sucesso 
        flash('Registro bem sucedido!')
        return redirect(url_for('registrar_producao'))
    # exibe as produções 
    with open('export.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        producao = data.get('producao', [])
        json_keys = list(data.keys())
        return render_template('producao.html', producao=producao, json_keys=json_keys, now=datetime.now)

# --- CONFIGURAÇÕES GERAIS  --- #
@server.route('/config', methods=['GET'])
def config():
    return render_template('config.html')

@server.route('/exportar', methods=['GET'])
def exportar():

    group_list = list(Grupo.select().dicts())
    user_list = list(Usuario.select().dicts())
    equip_list = list(Equipamento.select().dicts())
    cluster_list = list(Cluster.select().dicts())
    
    export = {
        'grupo': group_list,
        'usuario': user_list,
        'equipamento': equip_list,
        'cluster': cluster_list
    }

    json_data = json.dumps(export, indent=2)
    
    with open("export.json", "w") as f:
        f.write(json_data)

    return redirect(url_for('homepage')) and send_file("export.json", as_attachment = True)

@server.route('/importar', methods=['POST'])
def importar():

    # --- CRIAÇÃO DE ARQUIVO TEMPORÁRIO POIS O DIRETO RESULTA EM ERRO --- #
    file_requested = request.files['file']
    file_path = 'temp.json'
    file_requested.save(file_path)

    with open(file_path) as file:

        # --- ORGANIZAÇÃO DOS DADOS --- #
        data = json.load(file)
        groups = data['grupo']
        users = data['usuario']
        equipments = data['equipamento']
        clusters = data['cluster']

        # --- LOOPS DE CRIAÇÃO E ATUALIZAÇÃO DO BANCO DE DADOS --- #
        for group_data in groups:

            nome = group_data['nome']
            demanda = group_data['demanda']
            unidade = group_data['unidade']
            coordenador = group_data['coordenador']
            status = group_data['status']
            date_beg = group_data['date_beg']
            observacoes = group_data['observacoes']
            tipo = group_data['tipo']

            group, created = Grupo.get_or_create(
                id = group_data['id'],
                defaults = {
                    'nome': nome, 'demanda': demanda,
                    'unidade': unidade, 'coordenador': coordenador,
                    'status': status, 'date_beg': date_beg,
                    'observacoes': observacoes, 'tipo': tipo
                    }
                )

            update_grupo(group, nome, demanda, unidade, coordenador, observacoes, tipo, status)
            group.date_beg = date_beg
            group.save()

        for user_data in users:

            grupo = Grupo.get(Grupo.id == user_data['grupo'])
            nome = user_data['nome']
            email = user_data['email']
            date_beg = user_data['date_beg']
            date_end = user_data['date_end']
            observacoes = user_data['observacoes']
            status = user_data['status']


            user, created = Usuario.get_or_create(
                id = user_data['id'],
                defaults = {
                    'grupo': grupo, 'nome': nome, 'email': email,
                    'date_beg': date_beg, 'date_end': date_end,
                    'observacoes': observacoes, 'status': status
                    }
                )

            update_usuario(user, grupo, nome, email, observacoes, status)
            user.date_beg = date_beg
            user.date_end = date_end
            user.save()

        for cluster_data in clusters:

            name = cluster_data['name']
            description = cluster_data['description']
            date_beg = cluster_data['date_beg']
            date_end = cluster_data['date_end']
            status = cluster_data['status']

            cluster, created = Cluster.get_or_create(
                id = cluster_data['id'],
                defaults = {
                    'name': name, 'description': description,
                    'date_beg': date_beg, 'date_end': date_end, 'status': status
                    }
                )

            update_cluster(cluster, name, description, status)
            cluster.date_beg = date_beg
            cluster.date_end = date_end
            cluster.save()

        for equip_data in equipments:

            cluster = Cluster.get(Cluster.id == equip_data['cluster'])
            hostname = equip_data['hostname']
            modelo = equip_data['modelo']
            tipo = equip_data['tipo']
            patrimonio = equip_data['patrimonio']
            serviceTag = equip_data['serviceTag']
            nucleo = equip_data['nucleo']
            memoria = equip_data['memoria']
            disco = equip_data['disco']
            date_beg = equip_data['date_beg']
            date_end = equip_data['date_end']
            status = equip_data['status']

            equipment, created = Equipamento.get_or_create(
                id = equip_data['id'],
                defaults = {
                    'cluster': cluster, 'hostname': hostname,  'modelo': modelo,
                    'tipo': tipo, 'patrimonio': patrimonio, 'serviceTag': serviceTag,
                    'nucleo': nucleo, 'memoria': memoria, 'disco': disco,
                    'date_beg': date_beg, 'date_end': date_end, 'status': status
                    }
                )

            update_equipamento(equipment, cluster, hostname, modelo, tipo, patrimonio, serviceTag, nucleo, memoria, status)
            equipment.date_beg = equip_data['date_beg']
            equipment.date_end = equip_data['date_end']
            equipment.save()

    os.remove(file_path)
    return redirect(url_for('homepage'))

@server.route('/delete', methods=['POST'])
def delete():
    # --- DERRUBA AS TABELAS ANTIGAS E CRIA NOVAS --- #
    drop_tables()
    create_tables()
    return redirect(url_for('homepage'))

# ------------------------------------  INICIA A APLICAÇÃO --------------------------------------------- #

if __name__ == '__main__':
    create_tables()
    server.run(debug=True)
