# -------------------------------------  IMPORT DE BIBLIOTECAS  ---------------------------------------- #
# --- FLASK --- #

import os, json
from datetime import datetime
from flask import Flask
from flask import g, request, send_file
from flask import url_for, abort, render_template, redirect
from peewee import *

# --- DASH --- #

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np

# -------------------------------------  CONFIGURAÇÕES INICIAS  ---------------------------------------- #
# --- FLASK --- #

DATABASE = 'accounting.db'
DEBUG = True
SECRET_KEY = 'hin6bab8ge25*r=x&amp;+5$0kn=-#log$pt^#@vrqjld!^2ci@g*b'
server = Flask(__name__, static_folder='assets')
server.config.from_object(__name__)
database = SqliteDatabase(DATABASE, pragmas={'foreign_keys': 1})

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

# --- VARIAVÉIS DE CORES  --- #

first_color = '#FDC366'
second_color = '#212529'
third_color = '#111111'
fourth_color = '#1E6EFF'
fifth_color = '#EEE'

# ------------------------------------  LEITURA DATABASE - DASH ---------------------------------------- #

year = '2023'
month = 0
x = 0
i = 0

for dataframe in os.listdir('relatorios/' + year):
    month += 1

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

    # --------------------------------- SEÇÃO 1 - SELEÇÃO E GRAF. ANUAL -------------------------------- #
    
    dbc.Col([

        # --- SELEÇÃO DO ANO  --- #
        
        dbc.Col(
            dcc.Dropdown(
                options=[
                    {'label': '2023', 'value': '2023'},
                    {'label': '2022', 'value': '2022'},
                    {'label': '2021', 'value': '2021'},
                    {'label': '2020', 'value': '2020'},
                ],
                value='2023', 
                id='year_dropdown'      
                ),
                width=2, 
                style={'text-align':'center', 'margin': 'auto', 'margin-bottom':'1rem'}
        ),

        # --- GRÁFICO DE UTILIZAÇÃO ANUAL DOS CLUSTERS  --- #

        dbc.Col(
            dbc.Row(
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader('Uso de máquina anual', style={'background-color': first_color, 'color': second_color}),
                        dcc.Graph(
                            id='graph_annual_usage'
                        )],
                        className='shadow text-center',
                        style={'border': 'none'}
                    ), width=10, 
                    className='mx-auto'
                )
            )
            ,
            width=12
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
                    marks={
                            1: {'label': 'Janeiro'},
                            2: {'label': 'Fevereiro'},
                            3: {'label': 'Março'},
                            4: {'label': 'Abril'},
                            5: {'label': 'Maio'},
                            6: {'label': 'Junho'},
                            7: {'label': 'Julho'},
                            8: {'label': 'Agosto'},
                            9: {'label': 'Setembro'},
                            10: {'label': 'Outubro'},
                            11: {'label': 'Novembro'},
                            12: {'label': 'Dezembro'}
                    },
                    included=False
                )
            )],
            style={'margin': '0', 'background-color': third_color, 'padding': '1.25rem', 'margin-top':'1rem', 'border-radius':'.5rem'}
        )],
    style={'margin': '1rem 0'}
    ),

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
                                    html.H5(id='storage_usage', style={'display': 'inline', 'color': 'white'}),
                                    html.Span('GB', style={'color': 'white', 'margin-left': '5px'})
                                ])
                            ]),
                            dbc.Col([
                                html.Span('Disponível'),
                                html.Div([
                                    html.H5(id='storage_availability', style={'display': 'inline', 'color': 'white'}),
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

    # ---------------------------- SEÇÃO 6 - GRAF. PRODUÇÕES CIENTÍFICAS ------------------------------- #

    dbc.Col([
        dbc.Card([
            dbc.CardHeader('Produções científicas por Unidade (2015-2021) ', style={'background-color': fourth_color, 'color': 'white'}),
                dcc.Graph(
                     id='graph_production',
                )],
                className='shadow text-center',
                style={'border': 'none'}
            )
        ],
        width=10, 
        className='mx-auto'
        )
], style={'background-color':second_color, 'padding':'1rem', 'min-width':'700px'}
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
    days = month_days(value)

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
        capacity = 2108 * 24 * month_days(index)
        machine_availability_annual.append(capacity - total_usage)

    df_machine_usage["Disponível"] = machine_availability_annual

    # --- CRIA O GRÁFICO --- #
    graph_annual_usage = px.bar(
        df_machine_usage,
        y=["Máquina em 24x7", "Máquina em Cluster", "Disponível"],
        labels={'value':'Uso (CPU-Hora)', 'variable':'Tipo de uso'}
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
    )                                                          

    # --- CRIA O GRÁFICO DE MÁQUINA EM 24 X 7 POR GRUPO --- #  
    graph_24x7_usage_group = px.line(
        df_machine_usage_24x7, 
        x = 'Mês', 
        y = 'Máquina em 24x7',
        color = 'Projeto'
    )
    
    # ---------------------------- GRÁF. PRODUÇÕES CIENTÍFICAS ----------------------------------------- #

    # --- CRIA UM RELATÓRIO DE PRODUÇÕES - TEMPORÁRIO! --- #
    df_production = pd.read_excel('relatorios/producoes.xlsx')

    # --- CRIA O GRÁFICO DE PRODUÇÕES CIENTÍFICAS --- #
    graph_production = px.bar(
        df_production,
        x="Unidade/Escola",
        y=["Produção Científica", "TCC, Dissertação ou Tese"],
        barmode="group",
        labels={'value':'Quantidade', 'variable':'Tipo de Publicação'},
        text_auto=True
        )

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

def month_days (month):
        
        if (verify_leap_year):
            fev = 29
        else:
            fev = 28

        month_days = {
        1: 31,
        2: fev,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31
        }[month]
        return month_days

def read_database_excel (yearValue, month):
        
        if month == 1:
            df_data = pd.read_excel('relatorios/' + yearValue + '/1-jan.xlsx')
        elif month == 2: 
            df_data = pd.read_excel('relatorios/' + yearValue + '/2-fev.xlsx')
        elif month == 3: 
            df_data = pd.read_excel('relatorios/' + yearValue + '/3-mar.xlsx')
        elif month == 4: 
            df_data = pd.read_excel('relatorios/' + yearValue + '/4-abr.xlsx')
        elif month == 5: 
            df_data = pd.read_excel('relatorios/' + yearValue + '/5-mai.xlsx')
        elif month == 6: 
            df_data = pd.read_excel('relatorios/' + yearValue + '/6-jun.xlsx')
        elif month == 7: 
            df_data = pd.read_excel('relatorios/' + yearValue + '/7-jul.xlsx')
        elif month == 8: 
            df_data = pd.read_excel('relatorios/' + yearValue + '/8-ago.xlsx')
        elif month == 9: 
            df_data = pd.read_excel('relatorios/' + yearValue + '/9-set.xlsx')
        elif month == 10: 
            df_data = pd.read_excel('relatorios/' + yearValue + '/10-out.xlsx')
        elif month == 11: 
            df_data = pd.read_excel('relatorios/' + yearValue + '/11-nov.xlsx')
        elif month == 12:
            df_data = pd.read_excel('relatorios/' + yearValue + '/12-dez.xlsx')
        
        return df_data

# --------------------------------  DEFINIÇÃO DE CLASSES - FLASK --------------------------------------- #

class BaseModel(Model):
    class Meta:
        database = database

class Cluster(BaseModel):
    name = CharField(unique=True)
    description = TextField()
    date_beg = DateField()
    date_end = DateField()
    status = BooleanField()

class Equipamento(BaseModel):
    cluster = ForeignKeyField(Cluster, backref='equipamentos', on_delete='cascade')
    hostname = CharField()
    modelo = CharField()
    tipo = CharField()
    patrimonio = CharField()
    serviceTag = CharField()
    nucleo = IntegerField()
    memoria = IntegerField()
    disco = IntegerField()
    date_beg = DateField()
    date_end = DateField()
    status = BooleanField()
    
class Grupo(BaseModel):
    nome = CharField()
    demanda = IntegerField()
    unidade = CharField()
    coordenador = CharField()
    status = BooleanField()
    date_beg = DateField()
    observacoes = TextField()
    tipo = CharField()

class Usuario(BaseModel):
    grupo = ForeignKeyField(Grupo, backref='usuarios')
    nome = CharField()
    email = CharField()
    date_beg = DateField()
    date_end = DateField()
    observacoes = TextField()
    status = BooleanField()

# --------------------------------  DEFINIÇÃO DE FUNÇÕES - FLASK --------------------------------------- #

def create_tables():
    with database:
        database.create_tables([Cluster, Equipamento, Grupo, Usuario])

def get_object_or_404(model, *expressions):
    try:
        return model.get(*expressions)
    except model.DoesNotExist:
        abort(404)

# def object_list(template_name, qr, var_name='object_list', **kwargs):
#     kwargs[var_name] = qr
#     return render_template(template_name, **kwargs)

@server.before_request
def before_request():
    g.db = database
    g.db.connect()

@server.after_request
def after_request(response):
    g.db.close()
    return response

# -------------------------  DEFINIÇÃO DE ROTAS E DIRECIONAMENTOS - FLASK ------------------------------ #

@server.route('/', methods=['GET', 'POST'])
def homepage():
    lista_cluster = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)
    lista_grupo = Grupo.select().order_by(Grupo.nome).prefetch(Usuario)

    #if request.method == 'POST':
    #    if request.form['desativar']:
    #        with database.atomic():
                #Cluster.delete().where(Cluster.name == request.form['desativar']).execute()
    #            Cluster.update(status=False).where(Cluster.name == request.form['desativar']).execute()
    #        lista_cluster = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)
    #        print(request.form['desativar'])
    #        return object_list('homepage.html', lista_cluster, 'lista_cluster')

    return render_template('homepage.html', lista_cluster=lista_cluster, lista_grupo=lista_grupo)

@server.route("/dash")
def my_dash_app():
    return app.index()

@server.route('/cluster/<clusterName>', methods=['GET', 'POST'])
def cluster(clusterName=None):
    msg=None
    if clusterName == 'cadastro':
        if request.method == 'POST' and request.form['cluster_name']:
            try:
                with database.atomic():
                    Cluster.create(
                        name=request.form['cluster_name'],
                        description=request.form['description'],
                        date_beg=datetime.now().strftime('%d-%m-%Y'),
                        date_end='',
                        status=True
                    )
                return redirect(url_for('homepage'))
            except IntegrityError:
                msg='Cluster já existe'
        return render_template('cluster.html', clusterName='cadastro', msg=msg)
    else:
        if clusterName:
            cluster = get_object_or_404(Cluster, Cluster.name == clusterName)
            if request.method == 'POST' and request.form['cluster_name']:
                try:
                    cluster.name=request.form['cluster_name']
                    cluster.description=request.form['description']
                    if request.form['status'] == 'desativar':
                        cluster.status = False
                        cluster.date_end=datetime.now().strftime('%d-%m-%Y')
                    else:
                        cluster.status = True
                    cluster.save()
                    return redirect(url_for('homepage'))
                except IntegrityError:
                    msg='Cluster já existe'
        return render_template('cluster.html', cluster=cluster, msg=msg)


@server.route('/equipamento/<equipName>', methods=['GET', 'POST'])
def equipamento(equipName=None):
    msg=None
    lista_cluster = Cluster.select().where(Cluster.status == True).order_by(Cluster.name).prefetch(Equipamento)
    if equipName == 'cadastro':
        if request.method == 'POST' and request.form['hostname']:
            try:
                with database.atomic():
                    Equipamento.create(
                        cluster=Cluster.get(Cluster.name == request.form['equip_cluster_name']),
                        hostname=request.form['hostname'],
                        modelo=request.form['modelo'],
                        tipo=request.form['tipo'],
                        patrimonio=request.form['patrimonio'],
                        serviceTag=request.form['serviceTag'],
                        nucleo=request.form['nucleo'],
                        memoria=request.form['memoria'],
                        disco=0,
                        date_beg=datetime.now().strftime('%d-%m-%Y'),
                        date_end='',
                        status=True
                    )
                return redirect(url_for('homepage'))
            except IntegrityError:
                msg='Equipamento já existe'
        return render_template('equipamento.html', equipName='cadastro', msg=msg, lista_cluster=lista_cluster)
    else:
        if equipName:
            equipamento = get_object_or_404(Equipamento, Equipamento.hostname == equipName)
            #print(equipamento)
            if request.method == 'POST' and request.form['hostname']:
                try:
                    equipamento.cluster=Cluster.get(Cluster.name == request.form['equip_cluster_name'])
                    equipamento.hostname=request.form['hostname']
                    equipamento.modelo=request.form['modelo']
                    equipamento.tipo=request.form['tipo']
                    equipamento.patrimonio=request.form['patrimonio']
                    equipamento.serviceTag=request.form['serviceTag']
                    equipamento.nucleo=request.form['nucleo']
                    equipamento.memoria=request.form['memoria']
                    equipamento.disco=0
                    if request.form['status'] == 'desativar':
                        equipamento.status = False
                        equipamento.date_end=datetime.now().strftime('%d-%m-%Y')
                    else:
                        equipamento.status = True
                    equipamento.save()
                    return redirect(url_for('homepage'))
                except IntegrityError:
                    msg='Equipamento já existe'
        return render_template('equipamento.html', equipamento=equipamento, msg=msg, lista_cluster=lista_cluster)


@server.route('/grupo/<groupName>', methods=['GET', 'POST'])
def grupo(groupName=None):
    msg=None
    lista_grupo = Grupo.select().order_by(Grupo.nome)
    if groupName == 'cadastro':
        print('cadastro')
        if request.method == 'POST' and request.form['nome']:
            try:
                with database.atomic():
                    print('grupo')
                    Grupo.create(
                        nome=request.form['nome'],
                        demanda=request.form['demanda'],
                        unidade=request.form['unidade'],
                        coordenador=request.form['coordenador'],
                        observacoes=request.form['observacoes'],
                        tipo=request.form['tipo'],
                        date_beg=datetime.now().strftime('%d-%m-%Y'),
                        date_end='',
                        status=True
                    )
                return redirect(url_for('homepage'))
            except IntegrityError:
                msg='Grupo já existe'
        return render_template('grupo.html', groupName='cadastro', msg=msg, lista_grupo=lista_grupo)
    else:
        if groupName:
            grupo = get_object_or_404(Grupo, Grupo.nome == groupName)
            if request.method == 'POST' and request.form['nome']:
                try:
                    grupo.nome=request.form['nome']
                    grupo.demanda=request.form['demanda']
                    grupo.unidade=request.form['unidade']
                    grupo.coordenador=request.form['coordenador']
                    grupo.observacoes=request.form['observacoes']
                    grupo.tipo=request.form['tipo']
                    if request.form['status'] == 'desativar':
                        grupo.status = False
                        grupo.date_end=datetime.now().strftime('%d-%m-%Y')
                    else:
                        grupo.status = True
                    grupo.save()
                    return redirect(url_for('homepage'))
                except IntegrityError:
                    msg='Grupo já existe'
        return render_template('grupo.html', grupo=grupo, msg=msg, lista_grupo=lista_grupo)


@server.route('/usuario/<userName>', methods=['GET', 'POST'])
def usuario(userName=None):
    msg=None
    lista_grupo = Grupo.select().where(Grupo.status == True).order_by(Grupo.nome).prefetch(Usuario)
    if userName == 'cadastro':
        if request.method == 'POST' and request.form['nome']:
            try:
                with database.atomic():
                    Usuario.create(
                        grupo = Grupo.get(Grupo.nome == request.form['group_name']),
                        nome=request.form['nome'],
                        email=request.form['email'],
                        observacoes=request.form['observacoes'],
                        date_beg=datetime.now().strftime('%d-%m-%Y'),
                        date_end='',
                        status=True
                    )
                return redirect(url_for('homepage'))
            except IntegrityError:
                msg='Usuario já existe'
        return render_template('usuario.html', userName='cadastro', msg=msg, lista_grupo=lista_grupo)
    else:
        if userName:
            usuario = get_object_or_404(Usuario, Usuario.nome == userName)
            if request.method == 'POST' and request.form['nome']:
                try:
                    usuario.grupo=Grupo.get(Grupo.nome == request.form['group_name'])
                    usuario.nome=request.form['nome']
                    usuario.email=request.form['email']
                    usuario.observacoes=request.form['observacoes']
                    if request.form['status'] == 'desativar':
                        usuario.status = False
                        usuario.date_end=datetime.now().strftime('%d-%m-%Y')
                    else:
                        usuario.status = True
                    usuario.save()
                    return redirect(url_for('homepage'))
                except IntegrityError:
                    msg='Usuario já existe'
        return render_template('usuario.html', usuario=usuario, msg=msg, lista_grupo=lista_grupo)

@server.route('/export', methods=['GET'])
def export():

    lista_grupo = [grupo for grupo in Grupo.select().dicts()]
    lista_usuario = [usuario for usuario in Usuario.select().dicts()]
    lista_equipamento = [equipamento for equipamento in Equipamento.select().dicts()]
    lista_cluster = [cluster for cluster in Cluster.select().dicts()]
    
    listageral = {}

    listageral['grupo']=lista_grupo
    listageral['usuario']=lista_usuario
    listageral['equipamento']=lista_equipamento
    listageral['cluster']=lista_cluster
    json_data = json.dumps(listageral, indent=2)
    
    f = open("listageral.json", "w")
    f.write(str(json_data))
    f.close()

    return redirect(url_for('homepage')) and send_file("listageral.json", as_attachment = True)

@server.route('/upload', methods=['GET'])
def upload():
    return render_template('upload.html')

@server.route('/import_json', methods=['POST'])
def import_json():

    file_requested = request.files['file']
    file_path = 'temp.json'
    file_requested.save(file_path)

    with open(file_path) as file:

        data = json.load(file)

        grupos = data['grupo']
        usuarios = data['usuario']
        equipamentos = data['equipamento']
        clusters = data['cluster']

        for dados_grupo in grupos:

            existing_group, created = Grupo.get_or_create(
                id = dados_grupo['id'],
                defaults = {'nome': dados_grupo['nome'], 
                            'demanda': dados_grupo['demanda'],
                            'unidade': dados_grupo['unidade'],
                            'coordenador': dados_grupo['coordenador'],
                            'status': dados_grupo['status'],
                            'date_beg': dados_grupo['date_beg'],
                            'observacoes': dados_grupo['observacoes'],
                            'tipo': dados_grupo['tipo']
                            }
                )

            existing_group.nome = dados_grupo['nome']
            existing_group.demanda = dados_grupo['demanda']
            existing_group.unidade = dados_grupo['unidade']
            existing_group.coordenador = dados_grupo['coordenador']
            existing_group.status = dados_grupo['status']
            existing_group.date_beg = dados_grupo['date_beg']
            existing_group.observacoes = dados_grupo['observacoes']
            existing_group.tipo = dados_grupo['tipo']
            existing_group.save()

        for dados_usuario in usuarios:

            grupo = Grupo.get(Grupo.id == dados_usuario['grupo'])

            existing_user, created = Usuario.get_or_create(
                id = dados_usuario['id'],
                defaults = {'grupo': grupo, 
                            'nome': dados_usuario['nome'],
                            'email': dados_usuario['email'],
                            'date_beg': dados_usuario['date_beg'],
                            'date_end': dados_usuario['date_end'],
                            'observacoes': dados_usuario['observacoes'],
                            'status': dados_usuario['status']
                            }
                )

            existing_user.grupo = grupo
            existing_user.nome = dados_usuario['nome']
            existing_user.email = dados_usuario['email']
            existing_user.date_beg = dados_usuario['date_beg']
            existing_user.date_end = dados_usuario['date_end']
            existing_user.observacoes = dados_usuario['observacoes']
            existing_user.status = dados_usuario['status']
            existing_user.save()

        for dados_cluster in clusters:

            existing_cluster, created = Cluster.get_or_create(
                id = dados_cluster['id'],
                defaults = {'name': dados_cluster['name'], 
                            'description': dados_cluster['description'],
                            'date_beg': dados_cluster['date_beg'],
                            'date_end': dados_cluster['date_end'],
                            'status': dados_cluster['status']
                            }
                )

            existing_cluster.name = dados_cluster['name']
            existing_cluster.description = dados_cluster['description']
            existing_cluster.date_beg = dados_cluster['date_beg']
            existing_cluster.date_end = dados_cluster['date_end']
            existing_cluster.status = dados_cluster['status']
            existing_cluster.save()

        for dados_equipamentos in equipamentos:

            cluster = Cluster.get(Cluster.id == dados_equipamentos['cluster'])

            existing_equipament, created = Equipamento.get_or_create(
                id = dados_equipamentos['id'],
                defaults = {'cluster': cluster,
                            'hostname': dados_equipamentos['hostname'], 
                            'modelo': dados_equipamentos['modelo'],
                            'tipo': dados_equipamentos['tipo'],
                            'patrimonio': dados_equipamentos['patrimonio'],
                            'serviceTag': dados_equipamentos['serviceTag'],
                            'nucleo': dados_equipamentos['nucleo'],
                            'memoria': dados_equipamentos['memoria'],
                            'disco': dados_equipamentos['disco'],
                            'date_beg': dados_equipamentos['date_beg'],
                            'date_end': dados_equipamentos['date_end'],
                            'status': dados_equipamentos['status']
                            }
                )

            existing_equipament.cluster = cluster
            existing_equipament.hostname = dados_equipamentos['hostname']
            existing_equipament.modelo = dados_equipamentos['modelo']
            existing_equipament.tipo = dados_equipamentos['tipo']
            existing_equipament.patrimonio = dados_equipamentos['patrimonio']
            existing_equipament.serviceTag = dados_equipamentos['serviceTag']
            existing_equipament.nucleo = dados_equipamentos['nucleo']
            existing_equipament.memoria = dados_equipamentos['memoria']
            existing_equipament.disco = dados_equipamentos['disco']
            existing_equipament.date_beg = dados_equipamentos['date_beg']
            existing_equipament.date_end = dados_equipamentos['date_end']
            existing_equipament.status = dados_equipamentos['status']
            existing_equipament.save()

    os.remove(file_path)
    return redirect(url_for('homepage'))

@server.route('/clean', methods=['GET'])
def clean():
    database.drop_tables([Cluster, Equipamento, Grupo, Usuario])
    create_tables()
    return redirect(url_for('homepage'))

# ------------------------------------  INICIA A APLICAÇÃO --------------------------------------------- #

if __name__ == '__main__':
    create_tables()
    server.run()
