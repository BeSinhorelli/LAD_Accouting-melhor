from shared import *
from dash import dcc, html
import dash_bootstrap_components as dbc

layout_producoes = html.Div([
    # Gráfico de produções científicas
    dbc.Card([
        dbc.CardHeader(id='graph_production_title', style={'background-color': fourth_color, 'color': 'white'}),
        dcc.Graph(id='graph_production')
    ],
    className='shadow text-center', style={'border': 'none'}),
    
    html.Br()
])