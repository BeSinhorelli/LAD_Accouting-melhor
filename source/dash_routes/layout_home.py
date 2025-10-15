from dash import html, dcc
from peewee import fn
import os
import pandas as pd

from config import *

from models import Producao, Relatorio

annual_reports_cache = {}
card_style = {
    "backgroundColor": "#343a40",
    "padding": "1.5rem",
    "borderRadius": "1rem",
    "minWidth": "250px",
    "maxWidth": "280px",
    "color": "#f8f9fa",
    "boxShadow": "0 6px 15px rgba(0,0,0,0.5)",
    "textAlign": "center",
    "transition": "transform 0.3s ease-in-out",
}
# Card Produções
def get_producoes():
    query = Producao.select(
        fn.SUM(Producao.cientifica).alias("total_cientifica"),
        fn.SUM(Producao.tcc).alias("total_tcc")
    ).dicts().get()

    total = (query["total_cientifica"] or 0) + (query["total_tcc"] or 0)
    return total

# Card Horas Usadas
def read_annual_report_with_cache(yearValue):
    global annual_reports_cache
    #Verifica se o DataFrame para o ano já está no cache
    if yearValue in annual_reports_cache:
        print(f"[CACHE] Retornando dados do cache para o ano {yearValue}")
        return annual_reports_cache[yearValue]
    #Se não estiver no cache, lê do disco
    print(f"[CACHE] Carregando dados do disco para o ano {yearValue}")
    
    query = Relatorio.select().where(Relatorio.ano == yearValue).dicts()
    df_annual = pd.DataFrame(list(query))
    
    annual_reports_cache[yearValue] = df_annual
    return df_annual

layout_home = html.Div(
    style={
        "boxSizing": "border-box",
        "backgroundColor": "#212529",
        "color": "#f8f9fa",
        "height": "100vh",
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "center",
        "justifyContent": "top",
        "textAlign": "center",
        "padding": "2rem",
        "marginTop": "2rem"
    },
    children=[
        html.Div([
            html.H1(
                 "Disponibilidade Anual", 
                 style={
                      'color': first_color,
                      'text-align': 'center',
                      'font-size': '1.5rem'
            }
            ),
            html.Small(
                "Monitoramento iniciado em 10 de maio de 2025",
                style={
                    'color': '#ccc',
                    'textAlign': 'center',
                    'display': 'block',
                    'marginBottom': '1.5rem',
                    'fontStyle': 'italic'
                }
            ),
            html.Div([
               html.Div([
                    html.H4("Uptime", 
                            style={
                                'text-align': 'center', 
                                'margin-bottom': '0.2rem'
                                }),
                    html.P(id='uptime-percent', 
                           style={
                            'font-size': '2rem', 
                            'color': first_color, 
                            'fontWeight': 'bold'
                            }),
                    html.Small(id='uptime-hours')
               ], style={
                    'flex': '1', 
                    'padding': '0 1rem', 
                    'border-right': 
                    '1px solid #555'}),
               html.Div([
                    html.H4("Dowtime", 
                            style={
                                'text-align': 'center', 
                                'margin-bottom': '0.2rem'
                                }),
                    html.P(id='downtime-percent', 
                           style={
                            'font-size': '2rem', 
                            'color': first_color,
                            'fontWeight': 'bold'
                            }),
                    html.Small(id='downtime-hours')
               ], style={
                    'flex': '1', 
                    'padding': 
                    '0 1rem', 
                    }),
            ], style={
                 'display': 'flex', 
                 'justify-content': 'space-around',
                 'align-items': 'center',
                 'gap': '0.5rem'
                 }),
        ],
        style={
            "padding": "2rem",
            "borderRadius": "12px",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.4)",
            "backgroundColor": "#343a40",
            "width": "90%",
            "maxWidth": "900px"
        }),
        # Gráficos em callbaks.py
        dcc.Loading(
            id="loading-summary-cards",
            type="default",
            children=html.Div(id="summary_cards",
                 style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center", "gap": "1.5rem", "marginTop": "2rem"})
        )
        
    ]
)
