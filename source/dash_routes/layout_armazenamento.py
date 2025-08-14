from dash import html, dcc
import dash_bootstrap_components as dbc
from config import *
import sqlite3

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
        {'nome': 'BmDRarea', 'usado': 0, 'dedicado': 1},
    ],
    'CPBMF': [
        {'nome': 'cpbmfarea', 'usado': 1.8, 'dedicado': 1.9},
    ],
    'INVESTGENOMICA-METAGENOMIC': [
        {'nome': 'investgenomicaarea', 'usado': 5.7, 'dedicado': 6},
        {'nome': 'metagenomicarea', 'usado': 0.352, 'dedicado': 0.590},
    ],
    'LABGENOMA': [
        {'nome': 'labgenomaarea', 'usado': 4.8, 'dedicado':5.4},
        {'nome': 'eduardoSarea', 'usado': 2.9, 'dedicado': 4.5},
    ],
    'NIMED-NANOFIS': [
        {'nome': 'nanofisarea', 'usado': 0.108, 'dedicado': 1},
    ],
    'PLUMES': [
        {'nome': 'plumesarea', 'usado': 9.5, 'dedicado':10},
        {'nome': 'DAMAREA', 'usado': 11, 'dedicado': 11},
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
    style={'margin-top': '10px', 'margin-bottom': '10px'}
)

layout_armazenamento = html.Div([

    html.H2("Painel de Armazenamento", style={
        'color': fifth_color,
        'text-align': 'center',
        'padding': '1rem'
    }),
    dbc.Col(
        dbc.Card([
            dbc.CardHeader('Volumes por grupo', style={'background-color': first_color, 'color': second_color}),
            dropdown_grupos,
            dcc.Graph(id='grafico-armazenamento')
        ],
        className='shadow text-center',
        style={'border': 'none'}),
        width=10, className='mx-auto'
    ),
], style={'height': '100vh', 'padding': '1rem'})