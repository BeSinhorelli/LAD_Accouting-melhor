from dash import dcc, html
import dash_bootstrap_components as dbc
from datetime import datetime
from shared import *

layout_usos = html.Div([

    html.H2("Painel de Utilização de Recursos", style={
        'color': fifth_color,
        'text-align': 'center',
        'padding': '1rem'
    }),

    # Dropdown de ano
    dbc.Col(
        dcc.Dropdown(
            options=[{'label': str(ano), 'value': str(ano)} for ano in select_anos],
            value=year,
            id='year_dropdown'
        ),
        width=2,
        style={'text-align': 'center', 'margin': 'auto', 'margin-bottom': '1rem'}
    ),

    # Gráfico de uso anual
    dbc.Col(
        dbc.Card([
            dbc.CardHeader('Uso de máquina anual', style={'background-color': first_color, 'color': second_color}),
            dcc.Graph(id='graph_annual_usage')
        ],
        className='shadow text-center',
        style={'border': 'none'}),
        width=10, className='mx-auto'
    ),

    # Slider de mês
    dbc.Row([
        dbc.Col(
            dcc.Slider(
                id='month_slider',
                min=1,
                max=month,
                step=1,
                value=month,
                marks={i: {'label': m} for i, m in enumerate([
                    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
                ], 1)},
                included=False
            )
        )
    ], style={'background-color': third_color, 'padding': '1rem', 'border-radius': '.5rem'}),

    html.Br(),

    # Gráfico de storage e máquina mensal
    dbc.Row([

        dbc.Col(dbc.Card([
            dbc.CardHeader('Uso de Storage', style={'background-color': first_color, 'color': second_color}),
            dcc.Graph(id='graph_storage'),
            html.Div([
                html.Span("Utilizado: "), html.Span(id='storage_usage', style={'color': 'white'}),
                html.Span(" | Disponível: "), html.Span(id='storage_availability', style={'color': 'white'})
            ], style={'text-align': 'center', 'color': 'white', 'margin-bottom': '1rem'})
        ],
        className='shadow text-center', style={'background-color': third_color, 'color': 'white'}), width=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader('Uso de máquina mensal (CPU-Hora)', style={'background-color': first_color, 'color': second_color}),
            dcc.Graph(id='graph_monthly_usage'),
            html.Div([
                html.Span("Utilizado: "), html.Span(id='machine_usage', style={'color': 'white'}),
                html.Span(" | Disponível: "), html.Span(id='machine_availability', style={'color': 'white'}),
                html.Span(" | Capacidade: "), html.Span(id='machine_capacity', style={'color': 'white'})
            ], style={'text-align': 'center', 'color': 'white', 'margin-bottom': '1rem'})
        ],
        className='shadow text-center', style={'background-color': third_color, 'color': 'white'}), width=6)
    ]),

    html.Br(),

    # Gráficos por grupo: máquina em 24x7 e cluster
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader('Uso de máquina em 24x7 por grupo', style={'background-color': fourth_color, 'color': 'white'}),
            dcc.Graph(id='graph_24x7_machine')
        ],
        className='shadow text-center', style={'border': 'none'}), width=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader('Uso de máquina em Cluster por grupo', style={'background-color': fourth_color, 'color': 'white'}),
            dcc.Graph(id='graph_cluster_machine')
        ],
        className='shadow text-center', style={'border': 'none'}), width=6)
    ]),

    html.Br(),

    # Gráfico de storage por grupo
    dbc.Card([
        dbc.CardHeader('Uso de Storage (Cluster + 24x7) por grupo', style={'background-color': first_color, 'color': second_color}),
        dcc.Graph(id='graph_storage_group')
    ],
    className='shadow text-center', style={'border': 'none'}),
    html.Br(),

    # Gráficos de uso anual por grupo
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader('Uso anual de máquina em Cluster por grupo', style={'background-color': first_color, 'color': second_color}),
            dcc.Graph(id='graph_cluster_usage_group')
        ],
        className='shadow text-center', style={'border': 'none'}), width=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader('Uso anual de máquina em 24x7 por grupo', style={'background-color': fourth_color, 'color': 'white'}),
            dcc.Graph(id='graph_24x7_usage_group')
        ],
        className='shadow text-center', style={'border': 'none'}), width=6)
    ]),

    html.Br(),

], style={'padding': '2rem'})
