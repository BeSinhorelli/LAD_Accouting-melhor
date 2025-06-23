from dash import dcc, html
import dash_bootstrap_components as dbc
from datetime import datetime
from config import *

layout_demandas = html.Div([

        # ----------------------------- TÍTULO ----------------------------- #
    dbc.Col([
    html.H2(
        id="demand-title",
        style={
            'color': fifth_color,  
            'text-align': 'center',  
            'padding': '1rem',  
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

    html.Br(),

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
], style={'margin': '1rem 2rem 0.1rem 2rem'})
], style={'background-color':second_color, 'padding':'1rem', 'min-width':'900px'}
)