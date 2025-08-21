from dash import dcc, html
import dash_bootstrap_components as dbc
from datetime import datetime
from config import *

layout_usos = html.Div([

    html.H2("Painel de Uso de Máquinas", style={
        'color': fifth_color,
        'text-align': 'center',
        'padding': '1rem'
    }),

       # --------------------------------- SEÇÃO 1 - SELEÇÃO E GRAF. ANUAL -------------------------------- #
    dbc.Col(
        dbc.Card([
            dbc.CardHeader('Uso de máquina anual', style={'background-color': first_color, 'color': second_color}),
            dcc.Graph(id='graph_annual_usage')
        ],
        className='shadow text-center',
        style={'border': 'none'}),
        width=12, className='mx-auto'
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
                marks={i: {'label': m} for i, m in enumerate([
                    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
                ], 1)},
                included=False
            )
        )
    ], style={'margin': '0', 'background-color': third_color, 'padding': '1,25rem', 'border-radius': '0 0 0.5rem 0.5rem'}),

    html.Br(),

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
                                    html.H5(id='', style={'display': 'inline', 'color': 'white'}),
                                    html.Span('GB', style={'color': 'white', 'margin-left': '5px'})
                                ])
                            ]),
                            dbc.Col([
                                html.Span('Disponível'),
                                html.Div([
                                    html.H5(id='', style={'display': 'inline', 'color': 'white'}),
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

    html.Br(),

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

    html.Br(),

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

    html.Br(),

], style={'padding': '1rem'})
