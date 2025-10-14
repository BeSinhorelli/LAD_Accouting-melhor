from dash import html, dcc
import dash_bootstrap_components as dbc
import sqlite3
import pandas as pd

from config import *

# ------------------ VOLUMES POR GRUPO --------------------------- #
# Obter os grupos ativos do banco de dados
def obter_grupos_ativos():
    conn = sqlite3.connect("accounting.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM grupo WHERE status = 1 ORDER BY nome")
    grupos = [linha[0] for linha in cursor.fetchall()]
    conn.close()
    return grupos

dados = {
    'BmDR': [
        {'nome': 'BmDRarea', 'storage': 'hnstorage', 'usado': 0, 'dedicado': 1},
    ],
    'CPBMF': [
        {'nome': 'cpbmfarea', 'storage': 'cpbmf-storage', 'usado': 1.8, 'dedicado': 3},
    ],
    'INVESTGENOMICA-METAGENOMIC': [
        {'nome': 'investgenomicaarea', 'storage': 'hnstorage', 'usado': 5.7, 'dedicado': 6},
        {'nome': 'metagenomicarea', 'storage': 'hnstorage', 'usado': 0.488, 'dedicado': 0.590},
    ],
    'LABGENOMA': [
        {'nome': 'labgenomaarea', 'storage': 'labgenoma-storage', 'usado': 5.1, 'dedicado':10},
        {'nome': 'eduardoSarea', 'storage': 'hnstorage', 'usado': 2.9, 'dedicado': 4.5},
    ],
    'NIMED-NANOFIS': [
        {'nome': 'nanofisarea', 'storage': 'hnstorage', 'usado': 0.108, 'dedicado': 1},
    ],
    'PLUMES': [
        {'nome': 'plumesarea', 'storage': 'plumes-storage', 'usado': 9.5, 'dedicado':10},
        {'nome': 'DAMAREA', 'storage': 'dam-storage', 'usado': 11, 'dedicado': 40},
    ],
    'HOME': [
        {'nome': 'HOME', 'storage': 'home-storage', 'usado': 3.7, 'dedicado':6},
    ],
    'USRLOCALPANTANAL': [
        {'nome': 'USRLOCALPANTANAL', 'storage': 'usrlocal-storage', 'usado': 0.415, 'dedicado':0.500},
    ],
}

def dados_simulados(grupo):
    if grupo == 'Geral':
        todos_registros = []
        for g, registros in dados.items():
            for reg in registros:
                todos_registros.append(reg)
        if not todos_registros:
            return pd.DataFrame()
        df = pd.DataFrame(todos_registros)
    else:
        registros = dados.get(grupo, [])
        if not registros:
            return pd.DataFrame()
        df = pd.DataFrame(registros)
    df['disponivel'] = df['dedicado'] - df['usado']
    return df

# Filtrar dos grupos ativos apenas os que possuem dados
grupos_ativos = obter_grupos_ativos()
grupos_com_dados = dados.keys()
grupos_com_dados_ativos = [g for g in grupos_ativos if g in grupos_com_dados]
opcoes_grupos = [{'label': 'Geral', 'value': 'Geral'}] + \
                [{'label': g, 'value': g} for g in grupos_com_dados_ativos]
dropdown_grupos = dcc.RadioItems(
    id='grupo-dropdown',
    options=opcoes_grupos,
    value='Geral',
    labelStyle={'display': 'inline-block', 'margin-right': '20px'},
    style={'padding-top': '10px', 'padding-bottom': '10px', 'background-color': third_color, 'color': 'white'}
)

# Gráfico de uso de volumes por storage
def dados_por_storage(grupo):
    if grupo == 'Geral':
        todos_registros = []
        for g, registros in dados.items():
            todos_registros.extend(registros)
        if not todos_registros:
            return pd.DataFrame()
        df = pd.DataFrame(todos_registros)
    else:
        registros = dados.get(grupo, [])
        if not registros:
            return pd.DataFrame()
        df = pd.DataFrame(registros)
    
    df['disponivel'] = df['dedicado'] - df['usado']
    
    return df

layout_armazenamento = html.Div([

    html.H2("Painel de Armazenamento", style={
        'color': fifth_color,
        'text-align': 'center',
        'padding': '1rem'
    }),
    dbc.Col(
        dbc.Card([
            dbc.CardHeader('Uso de Storage Total', style={'background-color': first_color, 'color': second_color}),
            dbc.CardBody([
                dbc.Col(
                    dcc.Graph(
                        id='grafico-storage', 
                        config={'responsive': False, 'displayModeBar': False 
                                }, style={'height': '90px'} 
                    )
                ),
                dbc.Row([
                    dbc.Col([
                        html.Span('Utilizado',  style={'color': 'white'}),
                        html.Div([
                            html.H5(id='storage_usage', style={'display': 'inline', 'color': 'white'}),
                            html.Span('GB', style={'color': 'white', 'margin-left': '5px'})
                        ])
                    ]),
                    dbc.Col([
                        html.Span('Disponível',  style={'color': 'white'}),
                        html.Div([
                            html.H5(id='storage_availability', style={'display': 'inline', 'color': 'white'}),
                            html.Span('GB', style={'color': 'white', 'margin-left': '5px'}),
                        ])
                        
                    ]),
                    dbc.Col([
                        html.Span('Capacidade',  style={'color': 'white'}),
                        html.Div([
                            html.H5('134206', style={'display': 'inline', 'color': 'white'}),
                            html.Span('GB', style={'color': 'white', 'margin-left': '5px'}),
                        ])
                    ])
                ])
            ]),
        ],
        className='shadow text-center',
        style={'border': 'none', 'background-color': third_color}),
        width=10, className='mx-auto'
    ),
    # --- SELEÇÃO DO MÊS --- #
    dbc.Col(
        dbc.Card([
            dbc.CardBody([
                dcc.Slider(
                    id='month_slider_storage',
                    min=1,
                    max=month,
                    step=1,
                    value=month,
                    marks={
                        i: m for i, m in enumerate([
                            'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                            'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
                        ], 1)
                    },
                    included=False
                )
            ], style={'padding': '1.25rem', 'background-color': third_color})
        ],
        className='shadow text-center',
        style={'border': 'none'}),
        width=10, className='mx-auto'
    ),
    dbc.Col(
        dbc.Card([
            dbc.CardHeader('Uso de Storage por Grupo', style={'background-color': first_color, 'color': second_color}),
            dcc.Graph(id='grafico-storage-group')
        ],
        className='shadow text-center',
        style={'border': 'none', 'margin-top': '30px'}),
        width=10, className='mx-auto'
    ),
    dbc.Col(
        dbc.Card([
            dbc.CardHeader('Uso de Volumes por Grupo', style={'background-color': first_color, 'color': second_color}),
            dropdown_grupos,
            dcc.Graph(id='grafico-armazenamento')
        ],
        className='shadow text-center',
        style={'border': 'none', 'margin-bottom': '0', 'margin-top': '30px'}),
        width=10
    ),
    dbc.Col(
        dbc.Card([
            dbc.CardHeader('Uso de Volumes por Storage', style={'background-color': first_color, 'color': second_color}),
            dcc.Graph(id='grafico-storage-servidor')
        ],
        className='shadow text-center',
        style={'border': 'none', 'margin-top': '30px'}),
        width=10, className='mx-auto'
    ),
    dbc.Col(
        dbc.Card([
            dbc.CardHeader('Distribuição dos arquivos por período de acesso', style={'background-color': first_color, 'color': second_color}),
            dcc.Graph(id='grafico-acesso-tempo')
        ],
        className='shadow text-center',
        style={'border': 'none', 'margin-bottom': '0', 'margin-top': '30px'}),
        width=10, className='mx-auto'
    )

], style={'box-sizing': 'border-box',
    'background-color': '#212529',
    'min-height': '100vh',
    'display': 'flex',
    'flex-direction': 'column',
    'align-items': 'center',
    'padding': '2rem'})

