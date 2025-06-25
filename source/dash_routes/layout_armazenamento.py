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
        'BmDR': [
            {'nome': 'bmdr-storage1', 'usado': 3.1, 'disponivel': 2.4},
            {'nome': 'bmdr-storage2', 'usado': 2.5, 'disponivel': 2.1}
        ],
        'ACADDR': [
            {'nome': 'acaddr-storage1', 'usado': 1.2, 'disponivel': 3.3},
            {'nome': 'acaddr-storage2', 'usado': 0.9, 'disponivel': 4.1}
        ],
        'AGES': [
            {'nome': 'ages-storage1', 'usado': 1.2, 'disponivel': 3.3},
            {'nome': 'ages-storage2', 'usado': 0.9, 'disponivel': 4.1}
        ]
    }

    registros = dados.get(grupo, [])
    df = pd.DataFrame(registros)
    df['grupo'] = grupo
    df['tamanho'] = df['usado'] + df['disponivel']
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
], style={'height': '100vh'})