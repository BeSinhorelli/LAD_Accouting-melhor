from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from config import *
import sqlite3

def obter_grupos_ativos():
    conn = sqlite3.connect("accounting.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM grupo WHERE status = 1 ORDER BY nome")
    grupos = [linha[0] for linha in cursor.fetchall()]
    conn.close()
    return grupos

grupos_ativos = obter_grupos_ativos()
dropdown_grupos = dcc.Dropdown(
    id='grupo-dropdown',
    options=[{'label': g, 'value': g} for g in grupos_ativos],
    value=grupos_ativos[0] if grupos_ativos else None,
    clearable=False
    )

# simulação de dados
def dados_simulados(grupo):
    dados = {
        'AGES': [
            {'nome': 'Host de virtualização (patrimônio 3329729)', 'usado': 0, 'dedicado': 1},
        ],
        'BmDR': [
            {'nome': 'hnstorage', 'usado': 0, 'dedicado': 1},
        ],
        'CPBMF': [
            {'nome': 'cpbmf-storage', 'usado': 0, 'dedicado': 2},
        ],
        'GRIN': [
            {'nome': 'iSCSI PowerVault ME5012', 'usado': 0, 'dedicado': 11},
        ],
        'ImunoCOVID': [
            {'nome': 'imunorepository.lad.pucrs.br', 'usado': 0, 'dedicado': 1},
        ],
        'INSCER': [
            {'nome': 'host inscer.lad.pucrs.br', 'usado': 0, 'dedicado': 12},
        ],
        'INVESTGENOMICA-METAGENOMIC': [
            {'nome': 'investgenomica-storage', 'usado': 0, 'dedicado': 6},
            {'nome': 'metagenomic-storage', 'usado': 0, 'dedicado': 0.6},
            {'nome': 'host angiostrongylus.lad.pucrs.br', 'usado': 0, 'dedicado': 0.1},
        ],
        'LABGENOMA': [
            {'nome': 'labgenoma-storage', 'usado': 0, 'dedicado':5.56},
            {'nome': 'eduardos-storage', 'usado': 0, 'dedicado': 4.6},
        ],
        'NIMED-NANOFIS': [
            {'nome': 'nanofis-storage', 'usado': 0, 'dedicado': 1},
            {'nome': 'host pacs.lad.pucrs.br', 'usado': 0, 'dedicado': 0.256},
        ],
        'PLUMES': [
            {'nome': 'plumes-storage.lad.pucrs.br', 'usado': 0, 'dedicado':10},
            {'nome': 'dam-storage.lad.pucrs.br', 'usado': 0, 'dedicado': 11},
            {'nome': 'laset.lad.pucrs.br ', 'usado': 0, 'dedicado': 0.2},
        ],
        'UsaLAB': [
            {'nome': 'host usalab', 'usado': 0, 'dedicado':0.5},
            {'nome': 'host sgpusalab', 'usado': 0, 'dedicado': 0.5},
        ],
        'VHLab': [
            {'nome': 'VM vhlab.lad.pucrs.br', 'usado': 0, 'dedicado':0.04},
        ],
    }

    registros = dados.get(grupo, [])
    if not registros:
        return pd.DataFrame()
    df = pd.DataFrame(registros)
    df['grupo'] = grupo
    df['disponivel'] = df['dedicado'] - df['usado']
    return df

layout_armazenamento = html.Div([

    html.H2("Painel de Armazenamento por grupo", style={
        'color': fifth_color,
        'text-align': 'center',
        'padding': '1rem'
    }),
    dbc.Col(
        dbc.Card([
            dbc.CardHeader('Armazenamento por grupo', style={'background-color': first_color, 'color': second_color}),
            dropdown_grupos,
            dcc.Graph(id='grafico-armazenamento')
        ],
        className='shadow text-center',
        style={'border': 'none'}),
        width=10, className='mx-auto'
    ),
], style={'height': '100vh', 'padding': '1rem'})