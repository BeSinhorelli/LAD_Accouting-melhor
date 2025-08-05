# -------------------------------------  IMPORT DE BIBLIOTECAS  ---------------------------------------- #
# --- FLASK --- #

import os
from peewee import *

# --- DASH --- #

from dash import dcc, html, dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
from config import server, select_anos, year, fifth_color, second_color, tab_style, selected_tab_style

from dash_routes.layout_home import layout_home
from dash_routes.layout_demandas import layout_demandas
from dash_routes.layout_usos import layout_usos
from dash_routes.layout_armazenamento import layout_armazenamento
from dash_routes.layout_atividade import layout_atividade

from dash_routes.layout_producoes import layout_producoes
from dash_routes.callbacks import register_callbacks
from models import *
from routes import *

# --- BIBLIOTECAS PARA DEMANDAS--- #
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# -------------------------------------  CONFIGURAÇÕES INICIAS  ---------------------------------------- #
# --- DASH --- #
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    server=server,
    assets_folder='assets/images',
    url_base_pathname='/dash/'
    )

pio.templates.default = "plotly_dark"
app.title = "LAD Dashboard"

register_callbacks(app)

# ----------------------------------------  LAYOUT - DASH ---------------------------------------------- #

app.layout = html.Div([
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
            style=tab_style, selected_style=selected_tab_style)
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

# ---------------------------------------  CALLBACK - DASH --------------------------------------------- #

@app.callback(
    # --- GRÁFICOS DO LAYOUT (EM ORDEM)  --- #
    Output('graph_annual_usage', 'figure'),
    Output('graph_storage', 'figure'),
    Output('graph_monthly_usage', 'figure'),
    Output('graph_24x7_machine', 'figure'),
    Output('graph_cluster_machine', 'figure'),
    Output('graph_storage_group', 'figure'),
    Output('graph_cluster_usage_group', 'figure'),
    Output('graph_24x7_usage_group', 'figure'),
    Output('graph_production', 'figure'),

    # --- VALORES USADOS EM GRÁFICOS  --- #
    Output('storage_usage', 'children'),
    Output('storage_availability', 'children'),
    Output('machine_usage', 'children'),
    Output('machine_availability', 'children'),
    Output('machine_capacity', 'children'),

    # --- SELEÇÃO DE MÊS E ANO  --- #
    Output('month_slider', 'value'),
    Output('month_slider', 'max'),
    Input('year_dropdown', 'value'),
    Input('month_slider', 'value')
)

# -----------------------------------  FUNÇÃO PRINCIPAL - DASH ----------------------------------------- #

def update_figure(yearValue, value):
    
    # ------------------------------------- CONFIGURAÇÕES ---------------------------------------------- #
    month = 0
    global x
    df_annual = pd.DataFrame()
    days = month_days(value, yearValue)

    # --- CRIA UM RELATÓRIO ANUAL --- #
    for dataframe in os.listdir('relatorios/' + yearValue):
        df_annual = pd.concat([df_annual, pd.read_excel(os.path.join('relatorios/' + yearValue, dataframe))])
        month += 1

    # --- EVITA QUE TENTE ACESSAR UM MÊS QUE AINDA NÃO CHEGOU --- #
    if (month < value):
        value = month    

    x = month

    # --- CRIA UM RELATÓRIO MENSAL --- #
    df_data = read_database_excel(yearValue, value)

    # ---------------------- USO DAS MÁQUINAS EM CLUSTER E 24 X 7- ANUAL ------------------------------- #

    # --- CÁLCULO SIMPLES (CORES - HORAS/DIA - DIA/MÊS) --- #
    machine_capacity = (2108*24*days)

    # --- CRIA UM RELATÓRIO DE USO DE MÁQUINA, AGRUPADO POR MÊS --- #
    df_machine_usage = df_annual[['Máquina em Cluster', 'Máquina em 24x7', 'Mês']].sort_values(by=['Mês'], ascending=False)               
    df_machine_usage = df_machine_usage.groupby(['Mês']).agg({
        'Máquina em 24x7' : 'sum',
        'Máquina em Cluster' : 'sum'
    })

    # --- CRIA UMA COLUNA DE DISPONIBILIDADE --- #
    machine_availability_annual = []

    for index, row in df_machine_usage.iterrows():
        total_usage = row['Máquina em 24x7'] + row['Máquina em Cluster']
        capacity = 2108 * 24 * month_days(index, yearValue)
        machine_availability_annual.append(capacity - total_usage)

    df_machine_usage["Disponível"] = machine_availability_annual

    # --- CRIA O GRÁFICO --- #
    graph_annual_usage = px.bar(
        df_machine_usage,
        y=["Máquina em 24x7", "Máquina em Cluster", "Disponível"],
        labels={'value':'Uso (CPU-Hora)', 'variable':'Tipo de uso'},
        color_discrete_map={"Disponível": "white", "Máquina em Cluster": "#ef553b", "Máquina em 24x7": "#636efa"} 
        ) 
 
    # ------------------ USO DE STORAGE (CLUSTER E 24 X 7) MENSAL E EM GRUPO --------------------------- #

    # --- CRIA UM RELATÓRIO COM AS COLUNAS DE STORAGE --- #
    # --- TAMBÉM AS LINHAS COM MENOS DE DOIS VALORES E ADICIONA UM ZERO NAS CASAS VAZIAS --- #
    df_storage = df_data[['Projeto', 'Storage em cluster(GB)', 'Storage em 24x7(GB)']].dropna(thresh=2).fillna(0)  

    # --- ADICIONA UMA COLUNA DE TOTAL (Cluster + 24x7) --- #                                                                              
    df_storage['Total'] = df_storage['Storage em cluster(GB)'] + df_storage['Storage em 24x7(GB)']
    
    # --- DEFINÇÕES DO STORAGE --- #      
    storage_capacity = 134206
    storage_usage = df_storage['Total'].sum()
    storage_availability = storage_capacity - storage_usage

    # --- ADICIONA UMA LINHA DE DISPONIBILIDADE --- #  
    new_row = pd.DataFrame([['Disponível', '', '', storage_availability]], columns=df_storage.columns)
    df_storage = pd.concat([new_row, df_storage], ignore_index=True)   

    # --- CRIA O GRÁFICO MENSAL --- #
    storage_usage_percent = round((storage_usage / storage_capacity) * 100, 2)
    annotations = [
        dict(x=0, y=['Total'], text="Utilizado", xanchor="left", showarrow=False),
        dict(x=storage_usage, y=['Total'], text=f"{storage_usage_percent}%", xanchor="auto", showarrow=False)
    ]

    graph_storage = go.Figure(
        data=[
            go.Bar(name='Utilizado', x=[storage_usage], y=['Total'], orientation='h', marker_color='darkorange'),
            go.Bar(name='Disponível', x=[storage_availability], y=['Total'], orientation='h', marker_color='#efefef')
        ]
    )
    graph_storage.update_layout(
        barmode='stack',
        yaxis={'visible': False, 'showticklabels': False},
        xaxis={'visible': False, 'showticklabels': False, 'showline': False},
        height=100,
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=0, b=10, t=0),
        legend=dict(yanchor="top", y=0.5, xanchor="right", x=1.2),
        annotations=annotations
    )

    # --- CRIA O GRÁFICO DE GRUPOS --- # 
    labels = df_storage['Projeto']
    values = df_storage['Total']

    graph_storage_group = go.Figure(
        data=[
            go.Pie(labels = labels, values = values, pull = [0.1])
        ],
        layout_showlegend=False
    )
    graph_storage_group.update_traces(textposition='inside', textinfo = 'label+percent')

    # ------------------ USO DE MÁQUINA MENSAL E POR GRUPO (24X7 E CLUSTER) ---------------------------- #
    
    # --- DEFINIÇÃO DA MÁQUINA EM 24 X 7 --- # 
    df_machine_24x7 = df_data[['Projeto', 'Máquina em 24x7']].dropna().sort_values(by=['Máquina em 24x7'], ascending=False)   
    machine_usage_24x7 = df_machine_24x7['Máquina em 24x7'].sum()

    # --- DEFINIÇÃO DA MÁQUINA EM CLUSTER --- # 
    df_machine_cluster = df_data[['Projeto', 'Máquina em Cluster']].dropna().sort_values(by=['Máquina em Cluster'], ascending=False)
    machine_usage_cluster = df_machine_cluster['Máquina em Cluster'].sum()

    # --- DEFINIÇÃO DA MÁQUINA MENSAL --- # 
    machine_usage = machine_usage_24x7 + machine_usage_cluster
    machine_availability = machine_capacity - machine_usage
    machine_usage_percent = round((machine_usage / machine_capacity) * 100, 2)

    # --- CRIA O GRÁFICO DE USO DE MÁQUINA MENSAL --- #
    annotations = [
        dict(x=0, y=['Total'], text="Utilizado", xanchor="left", showarrow=False),
        dict(x=machine_usage_24x7+machine_usage_cluster, y=['Total'], text=str(machine_usage_percent)+'%', xanchor="auto", showarrow=False)
    ]

    graph_monthly_usage = go.Figure(
        data=[
            go.Bar(name='24x7', x=[machine_usage_24x7], y=['Total'], orientation='h', marker_color='rgb(20, 200, 255)'),
            go.Bar(name='Cluster', x=[machine_usage_cluster], y=['Total'], orientation='h', marker_color='rgb(30, 110, 255)'),
            go.Bar(name='Disponível', x=[machine_availability], y=['Total'], orientation='h', marker_color='#efefef')
        ]
    )

    graph_monthly_usage.update_layout(
        barmode='stack',
        yaxis={'visible': False, 'showticklabels': False},
        xaxis={'visible': False, 'showticklabels': False, 'showline': False},
        height=100,
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=0, b=10, t=0),
        legend=dict(yanchor="top", y=0.7, xanchor="right", x=1.2),
        annotations=annotations
    )

    # --- CRIA O GRÁFICO DE MÁQUINA EM 24 X 7 POR GRUPO --- # 
    graph_24x7_machine = px.bar(
        df_machine_24x7.head(10),
        x="Projeto",
        y="Máquina em 24x7",
        color="Projeto"
    ).update(layout_showlegend=False)

    # --- CRIA O GRÁFICO DE MÁQUINA EM CLUSTER POR GRUPO --- #
    graph_cluster_machine = px.bar(
        df_machine_cluster,
        x="Projeto",
        y="Máquina em Cluster",
        color="Projeto"
        ).update(layout_showlegend=False)

    # -------------------- USO DE MÁQUINA ANUAL POR GRUPO (24X7 E CLUSTER) ----------------------------- #
    
    # --- CONVERSÃO PARA INTEIRO PARA EVITAR MESES QUEBRADOS --- #
    df_annual['Mês'] = df_annual['Mês'].astype(int)

    # --- DEFINIÇÃO DA MÁQUINA ANUAL EM CLUSTER POR GRUPO --- #
    df_machine_usage_cluster = df_annual[['Projeto', 'Máquina em Cluster', 'Mês']].dropna().sort_values(by=['Mês']) 

    # --- DEFINIÇÃO DA MÁQUINA ANUAL EM 24 X 7 POR GRUPO --- #
    df_machine_usage_24x7 = df_annual[['Projeto', 'Máquina em 24x7', 'Mês']].dropna().sort_values(by=['Mês'])

    # --- CRIA O GRÁFICO DE MÁQUINA EM CLUSTER POR GRUPO --- #        
    graph_cluster_usage_group = px.line(
        df_machine_usage_cluster, 
        x = 'Mês', 
        y = 'Máquina em Cluster',
        color = 'Projeto'
    ).update_layout(
    xaxis=dict(tickmode='linear', dtick=1)
)                                    

    # --- CRIA O GRÁFICO DE MÁQUINA EM 24 X 7 POR GRUPO --- #  
    graph_24x7_usage_group = px.line(
        df_machine_usage_24x7, 
        x = 'Mês', 
        y = 'Máquina em 24x7',
        color = 'Projeto'
    ).update_layout(
    xaxis=dict(tickmode='linear', dtick=1)
)
    
    # ---------------------------- GRÁF. PRODUÇÕES CIENTÍFICAS ----------------------------------------- #
        # --- CRIA UM RELATÓRIO DE PRODUÇÕES - TEMPORÁRIO! --- #
    # df_production = pd.read_excel('relatorios/producoes.xlsx')

# --- LÊ OS DADOS DE PRODUÇÃO DO BANCO DE DADOS --- #
    producoes = list(Producao.select().dicts())
    if producoes:
        df_production = pd.DataFrame(producoes)
        df_production = df_production.rename(columns={
            'unidade': 'Unidade/Escola',
            'cientifica': 'Produção Científica',
            'tcc': 'TCC, Dissertação ou Tese'
        })
        # Agrupa por unidade, somando os valores
        df_production = df_production.groupby('Unidade/Escola', as_index=False)[['Produção Científica', 'TCC, Dissertação ou Tese']].sum()
        # Adiciona linha de total
        total_cientifica = df_production['Produção Científica'].sum()
        total_tcc = df_production['TCC, Dissertação ou Tese'].sum()
        total_row = pd.DataFrame([{
            'Unidade/Escola': 'Total',
            'Produção Científica': total_cientifica,
            'TCC, Dissertação ou Tese': total_tcc
        }])
        df_production = pd.concat([df_production, total_row], ignore_index=True)
    else:
        df_production = pd.DataFrame(columns=['Unidade/Escola', 'Produção Científica', 'TCC, Dissertação ou Tese'])

    # --- CRIA O GRÁFICO DE PRODUÇÕES CIENTÍFICAS --- #
    graph_production = px.bar(
        df_production,
        x="Unidade/Escola",
        y=["Produção Científica", "TCC, Dissertação ou Tese"],
        barmode="group",
        labels={'value':'Quantidade', 'variable':'Tipo de Publicação'},
        text_auto=True
    )

    # TEMPORÁRIO! - CALCULA AS HORAS DE SERVIÇO, CONFORME O ANO 

    sum_service = df_annual[['Serviço']].dropna().sum()
    print(sum_service.to_string())
    sum_machine = df_annual[['Máquina em Cluster']].dropna().sum()
    print(sum_machine.to_string())
    sum_24x7 = df_annual[['Máquina em 24x7']].dropna().sum()
    print(sum_24x7.to_string())

    # --------------------------------- RETORNO DA FUNÇÃO ---------------------------------------------- #

    return [
        # --- GRÁFICOS DO LAYOUT (EM ORDEM)  --- #
        graph_annual_usage,
        graph_storage,
        graph_monthly_usage,
        graph_24x7_machine, 
        graph_cluster_machine, 
        graph_storage_group,
        graph_cluster_usage_group,
        graph_24x7_usage_group,
        graph_production,

        # --- VALORES USADOS EM GRÁFICOS  --- #
        storage_usage, 
        storage_availability,
        machine_usage, 
        machine_availability,
        machine_capacity,

        # --- SELEÇÃO DE MÊS E ANO  --- #
        value,
        month
    ]

def verify_leap_year (yearValue):
    return int(yearValue) % 400 == 0 or int(yearValue) % 4 == 0 and int(yearValue) % 100 != 0

def month_days (month, yearValue):
        
        fev = 29 if verify_leap_year(yearValue) else 28

        month_days = {
        1: 31, 2: fev, 3: 31, 4: 30,
        5: 31, 6: 30, 7: 31, 8: 31,
        9: 30, 10: 31, 11: 30, 12: 31
        }[month]
        return month_days

def read_database_excel (yearValue, month):
        
    month_names = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    month_name = month_names[month - 1]
    file_path = f'relatorios/{yearValue}/{month}-{month_name}.xlsx'
    df_data = pd.read_excel(file_path)
    return df_data

# ------------------------------------  INICIA A APLICAÇÃO --------------------------------------------- #

if __name__ == '__main__':
    create_tables()
    server.run(debug=True)
