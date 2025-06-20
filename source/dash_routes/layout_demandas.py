from dash import dcc, html
import dash_bootstrap_components as dbc
from datetime import datetime
from shared import *

layout_demandas = html.Div([

    html.H2("Painel de Demandas", style={
        'color': fifth_color,
        'text-align': 'center',
        'padding': '1rem',
        'font-size': '1.8rem'
    }),

    # Gráfico comparativo anual
    html.H3("Comparativo: Demandas Criadas vs. Erros de Usuário", style={
        'color': third_color,
        'text-align': 'center',
        'background-color': first_color,
        'font-size': '1rem',
        'padding': '0.5rem',
        'border-radius': '0.5rem 0.5rem 0 0'
    }),

    dbc.Card(
        dcc.Graph(
            id="monthly-bar-chart",
            figure=plot_monthly_comparison(),
            style={'height': '320px'}
        ),
        className='shadow text-center',
        style={'background-color': COLORS["background"], 'border': 'none'}
    ),

    html.Br(),

    # Dropdown de mês + gráfico de pizza + lista de demandas
    dbc.Row([
        dbc.Col([
            html.H3("Distribuição de Erros de Usuário por Grupo", style={
                'color': third_color,
                'text-align': 'center',
                'background-color': first_color,
                'font-size': '1rem',
                'padding': '0.5rem',
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0'
            }),

            dbc.Card([
                html.Div([
                    dcc.Dropdown(
                        id="month-dropdown",
                        options=[{"label": "Visão Geral", "value": "all"}] + [
                            {"label": month, "value": month} for month in
                            ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                        ],
                        value=datetime.now().strftime('%b'),
                        className="dropdown-style",
                        style={'width': '40%', 'margin': '0 auto'}
                    )
                ], style={'background-color': COLORS['background'], 'padding': '0.5rem'}),

                dcc.Graph(id="pie-chart", style={'height': '400px'})
            ],
            className='shadow text-center',
            style={'background-color': COLORS['background'], 'border': 'none'})
        ], width=8),

        dbc.Col([
            html.H3("Lista de Demandas Relacionadas a Erros de Usuário", style={
                'color': third_color,
                'text-align': 'center',
                'background-color': first_color,
                'font-size': '1rem',
                'padding': '0.5rem',
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0'
            }),

            dbc.Card([
                dcc.Store(id="filtered-demands-store"),
                html.Ul(id="demand-list", className="demand-list", style={
                    'list-style-type': 'none',
                    'padding': '0',
                    'color': fifth_color,
                    'max-height': '480px',
                    'overflow-y': 'auto',
                    'text-align': 'left'
                })
            ],
            className='shadow text-center',
            style={'background-color': COLORS['background'], 'border': 'none', 'padding': '0 1rem'})
        ], width=4)
    ], style={'margin-top': '2rem'}),

    # Título e gráfico de ciclo
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H3(id="funnel-chart-title", style={
                    'color': third_color,
                    'text-align': 'center',
                    'background-color': first_color,
                    'font-size': '1rem',
                    'padding': '0.5rem',
                    'border-radius': '0.5rem 0.5rem 0 0'
                }), style={'padding': '0'}),
                dcc.Graph(id="funnel-chart", style={"height": "220px"})
            ],
            className='shadow text-center',
            style={'background-color': COLORS['background'], 'border': 'none'})
        ], width=8),

        dbc.Col([
            html.H3("Lista de Demandas Pendentes", id="open-demand-title", style={
                'color': third_color,
                'text-align': 'center',
                'background-color': first_color,
                'font-size': '1rem',
                'padding': '0.5rem',
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0'
            }),

            dbc.Card([
                dcc.Store(id="open-demands-store"),
                html.Ul(id="open-demand-list", className="demand-list", style={
                    'list-style-type': 'none',
                    'padding': '0',
                    'color': fifth_color,
                    'max-height': '400px',
                    'overflow-y': 'auto',
                    'text-align': 'left'
                })
            ],
            className='shadow text-center',
            style={'background-color': COLORS['background'], 'border': 'none', 'padding': '0 1rem'})
        ], width=4)
    ])
], style={'padding': '2rem'})
