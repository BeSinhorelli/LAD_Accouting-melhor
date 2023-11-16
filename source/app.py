# -------------------------------------  IMPORT DE BIBLIOTECAS  ---------------------------------------- #
# --- FLASK --- #

import os, json
from datetime import datetime
from flask import Flask, g, request, send_file, url_for, abort, render_template, redirect
from peewee import *

# --- DASH --- #

from dash import dcc, html, dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

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
            dbc.CardHeader('Produções científicas por Unidade (2015-2022) ', style={'background-color': fourth_color, 'color': 'white'}),
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
    nome = CharField(unique=True)
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

def drop_tables():
    with database:
        database.drop_tables([Cluster, Equipamento, Grupo, Usuario])

def get_object_or_404(model, *expressions):
    try:
        return model.get(*expressions)
    except model.DoesNotExist:
        abort(404)

@server.before_request
def before_request():
    g.db = database
    g.db.connect()

@server.after_request
def after_request(response):
    g.db.close()
    return response

# -------------------------  DEFINIÇÃO DE ROTAS E DIRECIONAMENTOS - FLASK ------------------------------ #
# --- HOMEPAGE  --- #
@server.route('/', methods=['GET', 'POST'])
def homepage():
    lista_cluster = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)
    lista_grupo = Grupo.select().order_by(Grupo.nome).prefetch(Usuario)

    return render_template('homepage.html', lista_cluster=lista_cluster, lista_grupo=lista_grupo)

# --- DASH APP  --- #
@server.route("/dash")
def dash_app():
    return app.index()

# --- CONFIGURAÇÕES DE CLUSTERS  --- #
@server.route('/cluster/<clusterName>', methods=['GET', 'POST'])
def cluster(clusterName=None):
    mensagem = None
    form = request.form

    # --- CASO SEJA CADASTRO DE CLUSTER  --- #
    if clusterName == 'cadastro':
        if request.method == 'POST':
            name = form['cluster_name']

            if name:
                if create_cluster(name, form['description']):
                    return redirect(url_for('homepage'))
                else: mensagem = 'Cluster já existe'

        return render_template('cluster.html', clusterName='cadastro', msg=mensagem)

    # --- CASO SEJA ATUALIZAÇÃO DE CLUSTER  --- #
    else:
        if clusterName:
            cluster = get_object_or_404(Cluster, Cluster.name == clusterName)

            if request.method == 'POST':
                name = form['cluster_name']
                description = form['description']
                status = form['status']

                if name:
                    if update_cluster(cluster, name, description, status):
                        return redirect(url_for('homepage'))
                    else:
                        mensagem = 'Cluster já existe'

        return render_template('cluster.html', cluster=cluster, msg=mensagem)

def create_cluster(name, description):
    try:
        with database.atomic():
            Cluster.create(
                name=name,
                description=description,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False

def update_cluster(cluster, name, description, status):
    try:
        cluster.name = name
        cluster.description = description
        if status == 'desativar':
            cluster.status = False
            cluster.date_end = datetime.now().strftime('%d-%m-%Y')
        else:
            cluster.status = True
        cluster.save()
        return True
    except IntegrityError:
        return False

# --- CONFIGURAÇÕES DE EQUIPAMENTOS  --- #
@server.route('/equipamento/<equipName>', methods=['GET', 'POST'])
def equipamento(equipName=None):
    mensagem = None
    lista_cluster = Cluster.select().where(Cluster.status == True).order_by(Cluster.name).prefetch(Equipamento)
    form = request.form

    # --- CASO SEJA CADASTRO DE EQUIPAMENTO --- #
    if equipName == 'cadastro':
        if request.method == 'POST':

            cluster = Cluster.get(Cluster.name == form['equip_cluster_name'])
            hostname = form['hostname']

            if hostname:
                if create_equipamento(cluster, hostname, form['modelo'], form['tipo'], form['patrimonio'], form['serviceTag'], form['nucleo'], form['memoria']):
                    redirect(url_for('homepage'))
                else: mensagem = 'Equipamento já existe'

        return render_template('equipamento.html', equipName='cadastro', msg=mensagem, lista_cluster=lista_cluster)
    
    # --- CASO SEJA ATUALIZAÇÃO DE EQUIPAMENTO --- #
    else:
        if equipName:
            equipamento = get_object_or_404(Equipamento, Equipamento.hostname == equipName)
            if request.method == 'POST':

                cluster = Cluster.get(Cluster.name == request.form['equip_cluster_name'])
                hostname = form['hostname']
            
                if hostname:
                    if update_equipamento(equipamento, cluster, hostname, form['modelo'], form['tipo'], form['patrimonio'], form['serviceTag'], form['nucleo'], form['memoria'], form['status']):
                        return redirect(url_for('homepage'))
                    else: mensagem='Equipamento já existe'

        return render_template('equipamento.html', equipamento=equipamento, msg=mensagem, lista_cluster=lista_cluster)
    
def create_equipamento(cluster, hostname, modelo, tipo, patrimonio, serviceTag, nucleo, memoria):
    try:
        with database.atomic():
            Equipamento.create(
                cluster=cluster,
                hostname=hostname,
                modelo=modelo,
                tipo=tipo,
                patrimonio=patrimonio,
                serviceTag=serviceTag,
                nucleo=nucleo,
                memoria=memoria,
                disco=0,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False

def update_equipamento(equipamento, cluster, hostname, modelo, tipo, patrimonio, serviceTag, nucleo, memoria, status):
    try:
        equipamento.cluster = cluster
        equipamento.hostname = hostname
        equipamento.modelo = modelo
        equipamento.tipo = tipo
        equipamento.patrimonio = patrimonio
        equipamento.serviceTag = serviceTag
        equipamento.nucleo = nucleo
        equipamento.memoria = memoria

        if status == 'desativar':
            equipamento.status = False
            equipamento.date_end=datetime.now().strftime('%d-%m-%Y')
        else:
            equipamento.status = True

        equipamento.save()
        return True
    except IntegrityError:
        return False
    
# --- CONFIGURAÇÕES DE GRUPOS  --- #
@server.route('/grupo/<groupName>', methods=['GET', 'POST'])
def grupo(groupName=None):
    mensagem = None
    form = request.form
    lista_grupo = Grupo.select().order_by(Grupo.nome)

    # --- CASO SEJA CADASTRO DE GRUPO --- #
    if groupName == 'cadastro':
        if request.method == 'POST':

            nome = form['nome']

            if nome:
                if create_grupo(nome, form['demanda'], form['unidade'], form['coordenador'], form['observacoes'], form['tipo']):
                    return redirect(url_for('homepage'))
                else: mensagem = 'Grupo já existe'

        return render_template('grupo.html', groupName='cadastro', msg=mensagem, lista_grupo=lista_grupo)
    
    # --- CASO SEJA ATUALIZAÇÃO DE GRUPO --- #
    else:
        if groupName:
            grupo = get_object_or_404(Grupo, Grupo.nome == groupName)
            if request.method == 'POST':

                nome = form['nome']

                if nome:
                    if update_grupo(grupo, nome, form['demanda'], form['unidade'], form['coordenador'], form['observacoes'], form['tipo'], form['status']):
                        return redirect(url_for('homepage'))
                    else: mensagem = 'Grupo já existe'
                    
        return render_template('grupo.html', grupo=grupo, msg=mensagem, lista_grupo=lista_grupo)

def create_grupo(nome, demanda, unidade, coordenador, observacoes, tipo):
    try:
        with database.atomic():
            Grupo.create(
                nome = nome,
                demanda = demanda,
                unidade = unidade,
                coordenador = coordenador,
                observacoes = observacoes,
                tipo = tipo,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False
    
def update_grupo(grupo, nome, demanda, unidade, coordenador, observacoes, tipo, status):
    try:
        grupo.nome = nome
        grupo.demanda = demanda
        grupo.unidade = unidade
        grupo.coordenador = coordenador
        grupo.observacoes = observacoes
        grupo.tipo = tipo

        if status == 'desativar':
            grupo.status = False
            grupo.date_end=datetime.now().strftime('%d-%m-%Y')
        else: grupo.status = True

        grupo.save()
        return True
    except IntegrityError:
        return False

# --- CONFIGURAÇÕES DE USUÁRIOS  --- #
@server.route('/usuario/<userName>', methods=['GET', 'POST'])
def usuario(userName=None):
    mensagem=None
    form = request.form
    lista_grupo = Grupo.select().where(Grupo.status == True).order_by(Grupo.nome).prefetch(Usuario)
    
    # --- CASO SEJA CADASTRO DE USUÁRIO --- #
    if userName == 'cadastro':
        if request.method == 'POST':
            
            grupo = Grupo.get(Grupo.nome == request.form['group_name'])
            nome = form['nome']

            if nome:
                print("ESTOU AQUI")
                if (create_usuario(grupo, nome, form['email'], form['observacoes'])):
                    return redirect(url_for('homepage'))
                else: mensagem = 'Usuario já existe'

        return render_template('usuario.html', userName='cadastro', msg=mensagem, lista_grupo=lista_grupo)
    
    # --- CASO SEJA ATUALIZAÇÃO DE USUÁRIO --- #
    else:
        if userName:
            usuario = get_object_or_404(Usuario, Usuario.nome == userName)
            if request.method == 'POST':

                grupo = Grupo.get(Grupo.nome == form['group_name'])
                nome = form['nome']

                if nome:
                    if (update_usuario(usuario, grupo, nome, form['email'], form['observacoes'], form['status'])):
                        return redirect(url_for('homepage'))
                    else: mensagem = 'Usuario já existe'

        return render_template('usuario.html', usuario=usuario, msg=mensagem, lista_grupo=lista_grupo)

def create_usuario(grupo, nome, email, observacoes):
    try:
        with database.atomic():
            Usuario.create(
                grupo=grupo,
                nome=nome,
                email=email,
                observacoes=observacoes,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False

def update_usuario(usuario, grupo, nome, email, observacoes, status):
    try:
        usuario.grupo = grupo
        usuario.nome = nome
        usuario.email = email
        usuario.observacoes = observacoes
        if status == 'desativar':
            usuario.status = False
            usuario.date_end=datetime.now().strftime('%d-%m-%Y')
        else: 
            usuario.status = True
        usuario.save()
        return True
    except IntegrityError:
        return False

# --- CONFIGURAÇÕES GERAIS  --- #
@server.route('/config', methods=['GET'])
def config():
    return render_template('config.html')

@server.route('/exportar', methods=['GET'])
def exportar():

    group_list = list(Grupo.select().dicts())
    user_list = list(Usuario.select().dicts())
    equip_list = list(Equipamento.select().dicts())
    cluster_list = list(Cluster.select().dicts())
    
    export = {
        'grupo': group_list,
        'usuario': user_list,
        'equipamento': equip_list,
        'cluster': cluster_list
    }

    json_data = json.dumps(export, indent=2)
    
    with open("export.json", "w") as f:
        f.write(json_data)

    return redirect(url_for('homepage')) and send_file("export.json", as_attachment = True)

@server.route('/importar', methods=['POST'])
def importar():

    # --- CRIAÇÃO DE ARQUIVO TEMPORÁRIO POIS O DIRETO RESULTA EM ERRO --- #
    file_requested = request.files['file']
    file_path = 'temp.json'
    file_requested.save(file_path)

    with open(file_path) as file:

        # --- ORGANIZAÇÃO DOS DADOS --- #
        data = json.load(file)
        groups = data['grupo']
        users = data['usuario']
        equipments = data['equipamento']
        clusters = data['cluster']

        # --- LOOPS DE CRIAÇÃO E ATUALIZAÇÃO DO BANCO DE DADOS --- #
        for group_data in groups:

            nome = group_data['nome']
            demanda = group_data['demanda']
            unidade = group_data['unidade']
            coordenador = group_data['coordenador']
            status = group_data['status']
            date_beg = group_data['date_beg']
            observacoes = group_data['observacoes']
            tipo = group_data['tipo']

            group, created = Grupo.get_or_create(
                id = group_data['id'],
                defaults = {
                    'nome': nome, 'demanda': demanda,
                    'unidade': unidade, 'coordenador': coordenador,
                    'status': status, 'date_beg': date_beg,
                    'observacoes': observacoes, 'tipo': tipo
                    }
                )

            update_grupo(group, nome, demanda, unidade, coordenador, observacoes, tipo, status)
            group.date_beg = date_beg
            group.save()

        for user_data in users:

            grupo = Grupo.get(Grupo.id == user_data['grupo'])
            nome = user_data['nome']
            email = user_data['email']
            date_beg = user_data['date_beg']
            date_end = user_data['date_end']
            observacoes = user_data['observacoes']
            status = user_data['status']


            user, created = Usuario.get_or_create(
                id = user_data['id'],
                defaults = {
                    'grupo': grupo, 'nome': nome, 'email': email,
                    'date_beg': date_beg, 'date_end': date_end,
                    'observacoes': observacoes, 'status': status
                    }
                )

            update_usuario(user, grupo, nome, email, observacoes, status)
            user.date_beg = date_beg
            user.date_end = date_end
            user.save()

        for cluster_data in clusters:

            name = cluster_data['name']
            description = cluster_data['description']
            date_beg = cluster_data['date_beg']
            date_end = cluster_data['date_end']
            status = cluster_data['status']

            cluster, created = Cluster.get_or_create(
                id = cluster_data['id'],
                defaults = {
                    'name': name, 'description': description,
                    'date_beg': date_beg, 'date_end': date_end, 'status': status
                    }
                )

            update_cluster(cluster, name, description, status)
            cluster.date_beg = date_beg
            cluster.date_end = date_end
            cluster.save()

        for equip_data in equipments:

            cluster = Cluster.get(Cluster.id == equip_data['cluster'])
            hostname = equip_data['hostname']
            modelo = equip_data['modelo']
            tipo = equip_data['tipo']
            patrimonio = equip_data['patrimonio']
            serviceTag = equip_data['serviceTag']
            nucleo = equip_data['nucleo']
            memoria = equip_data['memoria']
            disco = equip_data['disco']
            date_beg = equip_data['date_beg']
            date_end = equip_data['date_end']
            status = equip_data['status']

            equipment, created = Equipamento.get_or_create(
                id = equip_data['id'],
                defaults = {
                    'cluster': cluster, 'hostname': hostname,  'modelo': modelo,
                    'tipo': tipo, 'patrimonio': patrimonio, 'serviceTag': serviceTag,
                    'nucleo': nucleo, 'memoria': memoria, 'disco': disco,
                    'date_beg': date_beg, 'date_end': date_end, 'status': status
                    }
                )

            update_equipamento(equipment, cluster, hostname, modelo, tipo, patrimonio, serviceTag, nucleo, memoria, status)
            equipment.date_beg = equip_data['date_beg']
            equipment.date_end = equip_data['date_end']
            equipment.save()

    os.remove(file_path)
    return redirect(url_for('homepage'))

@server.route('/delete', methods=['POST'])
def delete():
    # --- DERRUBA AS TABELAS ANTIGAS E CRIA NOVAS --- #
    drop_tables()
    create_tables()
    return redirect(url_for('homepage'))

# ------------------------------------  INICIA A APLICAÇÃO --------------------------------------------- #

if __name__ == '__main__':
    create_tables()
    server.run()
