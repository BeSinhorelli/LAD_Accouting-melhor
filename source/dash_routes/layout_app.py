from dash import dcc, html
import dash_bootstrap_components as dbc

from config import fifth_color, second_color, tab_style, selected_tab_style, select_anos, year 

from dash_routes.layout_home import layout_home
from dash_routes.layout_demandas import layout_demandas
from dash_routes.layout_usos import layout_usos
from dash_routes.layout_armazenamento import layout_armazenamento
from dash_routes.layout_atividade import layout_atividade
from dash_routes.layout_producoes import layout_producoes


def create_layout(app):
    return html.Div([
        # --- NAVEGAÇÃO  --- #

        html.Div(
            html.Div([
                html.A("LAD Accounting", href="/", style={'color': fifth_color, 'text-decoration':'none', 'font-size':'1.5rem'}),
                
                html.Img(
                    id="logo",
                    src=app.get_asset_url("LabLAD.png"),
                    style={'max-width': '100px'}
                ),
                
                html.A("LAD Dashboard", href="/dash/", style={'color': fifth_color, 'text-decoration':'none', 'font-size':'1.5rem'})
            ], style={'text-align':'center', 'display':'flex', 'gap':'3rem', 'align-items':'center', 'justify-content':'center'}
            ), style={'padding': '2rem', 'background-color': second_color}
        ),
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

        dcc.Tabs([
        dcc.Tab(label='Home', children=[layout_home],
                style=tab_style, selected_style=selected_tab_style),
        dcc.Tab(label='Atividade', children=[layout_atividade],
                style=tab_style, selected_style=selected_tab_style),  
        dcc.Tab(label='Painel de Demandas', children=[layout_demandas],
                style=tab_style, selected_style=selected_tab_style),
        dcc.Tab(label='Uso de Máquinas', children=[layout_usos],
                style=tab_style, selected_style=selected_tab_style),
        dcc.Tab(label='Armazenamento', children=[layout_armazenamento],
                style=tab_style, selected_style=selected_tab_style),
        dcc.Tab(label='Produções Científicas', children=[layout_producoes],
                style=tab_style, selected_style=selected_tab_style),
                
    ], style={
        'backgroundColor': '#343a40',
        'borderRadius': '8px',
        'padding': '0.5rem',
        'margin': '0 auto',
        'width': '95%',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.3)'
    }),
    

    ], style={'background-color':second_color, 'padding':'1rem', 'min-width':'900px'}
    )