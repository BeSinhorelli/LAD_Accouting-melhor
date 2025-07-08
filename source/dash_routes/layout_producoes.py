from dash import dcc, html
import dash_bootstrap_components as dbc
from config import *
from models import *

layout_producoes = html.Div([
    # Gráfico de produções científicas
    html.H2("Produções Científicas", style={
        'color': fifth_color,
        'text-align': 'center',
        'padding': '1rem'
    }),
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
], style={'height': '100vh', 'padding': '1rem'})