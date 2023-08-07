import os, sqlite3, json

from unicodedata import name
from datetime import datetime

from flask import Flask, template_rendered
from flask import g, request, send_file
from flask import url_for, abort, render_template, flash, redirect

from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from playhouse.reflection import generate_models, print_model, print_table_sql

import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np

##########################################################################################

DATABASE = 'accounting.db'
DEBUG = True
SECRET_KEY = 'hin6bab8ge25*r=x&amp;+5$0kn=-#log$pt^#@vrqjld!^2ci@g*b'

server = Flask(__name__, static_folder='assets')
server.config.from_object(__name__)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    server=server,
    assets_folder='assets/images',
    url_base_pathname='/dash/'
    )

pio.templates.default = "plotly_dark"
app.title = "LAD Dashboard"
database = SqliteDatabase(DATABASE, pragmas={'foreign_keys': 1})

##########################################################################################

first_color = '#FDC366'
second_color = '#212529'
third_color = '#111111'
fourth_color = '#1E6EFF'
fifth_color = '#EEE'

# ----------------------------------------------  LEITURA DATABASE  ---------------------------------------------- #

ano = '2023'
qmes = 0
x = 0
i = 0

for dataframe in os.listdir('relatorios/' + ano):
    qmes += 1

# ----------------------------------------------  LAYOUT  ---------------------------------------------- #

app.layout = html.Div([

    # ------------ LOGO ----------------------------------------------- #

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

    # ------------ Seção 1 - SELEÇÃO --------------------------------- #
    
    dbc.Col([
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
        dbc.Col(
            dbc.Row(
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader('Uso de Máquina anual', style={'border-bottom': 'none', 'background-color': first_color, 'color': second_color}),
                        dcc.Graph(
                            id='fig_utilizacao_anual'
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
        dbc.Row([
            dbc.Col(
                dcc.Slider(
                    id='month_slider',
                    min=1,
                    max=qmes,
                    value=qmes,
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

    # ------------ Seção 2 - CARDS (STORAGE E HORAS-NÚCLEO TOTAL) ----------------------------------- #

    dbc.Col(
        dbc.Row([

            dbc.Col(
                dbc.Card([
                    dbc.CardHeader('Storage', style={'border-bottom': 'none','background-color': first_color, 'color' : second_color}),
                    dbc.CardBody([
                        dbc.Col(
                            dcc.Graph(
                                id='fig_storage_card'
                            )
                        ),
                        dbc.Row([
                            dbc.Col([
                                html.Span('Utilizado'),
                                html.Div([
                                    html.H5(id='total_utilizado_storage', style={'display': 'inline', 'color': 'white'}),
                                    html.Span('GB', style={'color': 'white', 'margin-left': '5px'})
                                ])
                            ]),
                            dbc.Col([
                                html.Span('Disponível'),
                                html.Div([
                                    html.H5(id='total_disponivel_storage', style={'display': 'inline', 'color': 'white'}),
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
                    style={'border': 'none','background-color': third_color, 'color': 'white'}
                ), width=6
            ),

            dbc.Col(
                dbc.Card([
                    dbc.CardHeader('Uso de Máquina mensal (CPU-Hora)', style={'border-bottom': 'none', 'background-color': first_color, 'color' : second_color}),
                    dbc.CardBody([
                        dbc.Col(
                            dcc.Graph(
                                id='graph_horas_nucleo_total'
                            )
                        ),
                        dbc.Row([
                            dbc.Col([
                                html.Span('Utilizado'),
                                html.H5(id='total_utilizado_horas_nucleo', style={'color': 'white'}),
                            ]),
                            dbc.Col([
                                html.Span('Disponível'),
                                html.H5(id='total_disponivel_horas_nucleo', style={'color': 'white'})
                            ]),
                            dbc.Col([
                                html.Span('Capacidade'),
                                html.H5(id='capacidade_horas_nucleo', style={'color': 'white'})
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

    # ------------ Seção 3 - MÁQUINAS EM CLUSTER E 24x7 ----------------------- #

    dbc.Col(
        dbc.Row([

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Utilização de Máquina em 24x7 por grupo', style={'border-bottom': 'none', 'background-color': fourth_color, 'color': 'white'}),
                    dcc.Graph(
                        id='graph_maquina24x7',
                    )],
                    className='shadow text-center',
                    style={'border': 'none'}
                )],
                width=6
            ),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Utilização de Máquina em Cluster por grupo', style={'border-bottom': 'none', 'background-color': fourth_color, 'color': 'white'}),
                    dcc.Graph(
                        id='graph_maquina_cluster',
                    )],
                    className='shadow text-center',
                    style={'border': 'none'}
                )],
                width=6
            )

        ]),
        style={'margin': '1rem 0'}
    ),

    # ------------ Seção 4 - STORAGE POR GRUPO E USO DE MÁQUINA EM CLUSTER TOTAL E 24x7 ------------ #

    dbc.Col(
        dbc.Col([

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Utilização de Storage (Cluster + 24x7) por grupo', style={'border-bottom': 'none', 'background-color': first_color, 'color': second_color}),
                    dcc.Graph(
                        id='graph_storage',
                    )],
                    className='shadow text-center',
                    style={'border': 'none'}
                )],
                width=10, 
                className='mx-auto',
                style={'margin': '1rem 0'}
            ),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Utilização de Máquina em Cluster total', style={'border-bottom': 'none', 'background-color': first_color, 'color': second_color}),
                    dcc.Graph(
                        id='graph_total',
                    )],
                    className='shadow text-center',
                    style={'border': 'none', 'margin': '1rem 0'},
                )
            ],
            width=10, 
            className='mx-auto'
            )
        ])
    ),
               
    dbc.Col([
        dbc.Card([
            dbc.CardHeader('Utilização de Máquina em 24x7 total', style={'border-bottom': 'none', 'background-color': fourth_color, 'color': 'white'}),
                dcc.Graph(
                     id='graph_total_24x7',
                )],
                className='shadow text-center',
                style={'border': 'none', 'margin': '1rem 0'}
            )
        ],
        width=10, 
        className='mx-auto'
        ),
    dbc.Col([
        dbc.Card([
            dbc.CardHeader('Produções científicas dos grupos - Geral ', style={'border-bottom': 'none', 'background-color': fourth_color, 'color': 'white'}),
                dcc.Graph(
                     id='graph_producoes',
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


    # ------------ CALLBACK - ORGANIZA AS INFORMAÇÕES DOS GRÁFICOS ------------ #

@app.callback(
    Output('fig_utilizacao_anual', 'figure'),
    Output('fig_storage_card', 'figure'),
    Output('graph_horas_nucleo_total', 'figure'),

    Output('graph_maquina24x7', 'figure'),
    Output('graph_maquina_cluster', 'figure'),
    Output('graph_storage', 'figure'),
    Output('graph_total', 'figure'),
    Output('graph_total_24x7', 'figure'),
    Output('graph_producoes', 'figure'),

    Output('total_utilizado_storage', 'children'),
    Output('total_disponivel_storage', 'children'),
    Output('total_utilizado_horas_nucleo', 'children'),
    Output('total_disponivel_horas_nucleo', 'children'),
    Output('capacidade_horas_nucleo', 'children'),
    Output('month_slider', 'value'),
    Output('month_slider', 'max'),

    Input('year_dropdown', 'value'),
    Input('month_slider', 'value')
)

# ------------ FUNÇÃO PRINCIPAL ------------ #

def update_figure(yearValue, value):
    
    # ------------ CONFIGURAÇÕES -------------- #

    qmes = 0
    global x

    df_relatorio_total = pd.DataFrame()
    
    for dataframe in os.listdir('relatorios/' + yearValue):
        df_relatorio_total = pd.concat([df_relatorio_total, pd.read_excel(os.path.join('relatorios/' + yearValue, dataframe))])
        qmes = qmes + 1
    
    if (qmes < x and qmes < value):
        value = qmes

    x = qmes

    if value == 1:
        df_dados = pd.read_excel('relatorios/' + yearValue + '/1-jan.xlsx')
        mes = 31
    elif value == 2: 
        df_dados = pd.read_excel('relatorios/' + yearValue + '/2-fev.xlsx')
        if (int(yearValue) % 400 == 0 or int(yearValue) % 4 == 0 and int(yearValue) % 100 != 0):
            mes = 29
        else: mes = 28
    elif value == 3: 
        df_dados = pd.read_excel('relatorios/' + yearValue + '/3-mar.xlsx')
        mes = 31
    elif value == 4: 
        df_dados = pd.read_excel('relatorios/' + yearValue + '/4-abr.xlsx')
        mes = 30
    elif value == 5: 
        df_dados = pd.read_excel('relatorios/' + yearValue + '/5-mai.xlsx')
        mes = 31
    elif value == 6: 
        df_dados = pd.read_excel('relatorios/' + yearValue + '/6-jun.xlsx')
        mes = 30
    elif value == 7: 
        df_dados = pd.read_excel('relatorios/' + yearValue + '/7-jul.xlsx')
        mes = 31
    elif value == 8: 
        df_dados = pd.read_excel('relatorios/' + yearValue + '/8-ago.xlsx')
        mes = 31
    elif value == 9: 
        df_dados = pd.read_excel('relatorios/' + yearValue + '/9-set.xlsx')
        mes = 30
    elif value == 10: 
        df_dados = pd.read_excel('relatorios/' + yearValue + '/10-out.xlsx')
        mes = 31
    elif value == 11: 
        df_dados = pd.read_excel('relatorios/' + yearValue + '/11-nov.xlsx')
        mes = 30
    else:
        df_dados = pd.read_excel('relatorios/' + yearValue + '/12-dez.xlsx')
        mes = 31                                      


    df_producoes = pd.read_excel('relatorios/producoes.xlsx')

    # ------------ USO HISTÓRICO DAS MÁQUINAS - ANUAL -------------- #

    df_total_maquina = df_relatorio_total[['Máquina em Cluster', 'Máquina em 24x7', 'Mês']]               
    df_total_maquina = df_total_maquina.sort_values(by=['Mês'], ascending=False)
    df_total_maquina = df_total_maquina.groupby(['Mês']).agg({
        'Máquina em 24x7' : 'sum',
        'Máquina em Cluster' : 'sum'
    })

    capacidade_horas_nucleo = (2108*24*mes)
    
    if (int(yearValue) % 400 == 0 or int(yearValue) % 4 == 0 and int(yearValue) % 100 != 0):
        fev = 29
    else: fev = 28

    valores_calculados = []

    for index, row in df_total_maquina.iterrows():
        uso_total = row['Máquina em 24x7'] + row['Máquina em Cluster']
        dias_mes = {
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
        }[index]
        capacidade_total = 2108 * 24 * dias_mes
        valores_calculados.append(capacidade_total - uso_total)

    df_total_maquina["Disponível"] = valores_calculados

    fig_utilizacao_anual = px.bar(
        df_total_maquina,
        y=["Máquina em 24x7", "Máquina em Cluster", "Disponível"],
        labels={'value':'Uso (CPU-Hora)', 'variable':'Tipo de uso'}
        )
    
    # ------------ Máquina em 24x7 -------------- #

        
    df_maquina24x7 = df_dados[['Projeto', 'Máquina em 24x7']]                         
    df_maquina24x7 = df_maquina24x7.dropna()                                                 
    df_maquina24x7 = df_maquina24x7.sort_values(by=['Máquina em 24x7'], ascending=False)

    total_utilizado_24x7 = df_maquina24x7['Máquina em 24x7'].sum()

    fig_maquina24x7 = px.bar(df_maquina24x7.head(10), x="Projeto", y="Máquina em 24x7", color="Projeto")
    fig_maquina24x7.update(layout_showlegend=False)


    # ------------ Máquina em Cluster ------------ #


    df_maquinaCluster = df_dados[['Projeto', 'Máquina em Cluster']]                         
    df_maquinaCluster = df_maquinaCluster.dropna()                                                 
    df_maquinaCluster = df_maquinaCluster.sort_values(by=['Máquina em Cluster'], ascending=False)

    total_utilizado_cluster = df_maquinaCluster['Máquina em Cluster'].sum()

    fig_maquinaCluster = px.bar(df_maquinaCluster, x="Projeto", y="Máquina em Cluster", color="Projeto")
    fig_maquinaCluster.update(layout_showlegend=False)


    # ------------ Horas nucleo total -------------- #

    total_utilizado_horas_nucleo = total_utilizado_24x7 + total_utilizado_cluster
    total_disponivel_horas_nucleo = capacidade_horas_nucleo - total_utilizado_horas_nucleo
    utilizado_horas_nucleo = (total_utilizado_horas_nucleo / capacidade_horas_nucleo) * 100
    utilizado_horas_nucleo = round(utilizado_horas_nucleo, 2)
    
    fig_horas_nucleo_total = go.Figure(
        data=[
            go.Bar(name='24x7', x=[total_utilizado_24x7], y=['Total'], orientation='h', marker_color='rgb(20, 200, 255)'),
            go.Bar(name='Cluster', x=[total_utilizado_cluster], y=['Total'], orientation='h', marker_color='rgb(30, 110, 255)'),
            go.Bar(name='Disponível', x=[total_disponivel_horas_nucleo], y=['Total'], orientation='h', marker_color='#efefef')
        ]
    )

    fig_horas_nucleo_total.update_layout(barmode='stack', yaxis={'visible': False, 'showticklabels': False}, xaxis={'visible': False, 'showticklabels': False, 'showline': False}, autosize=False,
    height=100, plot_bgcolor='rgba(0,0,0,0)', margin=dict(
        l=10,
        r=0,
        b=10,
        t=0
    ))

    fig_horas_nucleo_total.add_annotation(x=0, y=['Total'],
            text="Utilizado", xanchor="left",
            showarrow=False)

    fig_horas_nucleo_total.add_annotation(x=total_utilizado_24x7+total_utilizado_cluster, y=['Total'],
            text=str(utilizado_horas_nucleo)+'%', xanchor="auto",
            showarrow=False)

    fig_horas_nucleo_total.update_layout(legend=dict(
        yanchor="top",
        y=0.7,
        xanchor="right",
        x=1.2
    ))


    # ------------ Storage ----------------------- #


    df_storage = df_dados[['Projeto', 'Storage em cluster(GB)', 'Storage em 24x7(GB)']]                      
    df_storage= df_storage.dropna(thresh=2)                                                        
    df_storage = df_storage.fillna(0)                                                               
    df_storage['Total'] = df_storage['Storage em cluster(GB)'] + df_storage['Storage em 24x7(GB)']    
    df_storage.loc[-1] = ['Disponível', '', '', 134206 - df_storage['Total'].sum()]                 
    df_storage.index = df_storage.index + 1
    df_storage = df_storage.sort_index()

    total_utilizado_storage = df_storage['Total'].sum() - df_storage.loc[0, 'Total']
    total_disponivel_storage = 134206 - total_utilizado_storage                        


    #-- Gráfico --#


    labels = df_storage['Projeto']
    values = df_storage['Total']

    fig_storage = go.Figure(data=[go.Pie(labels = labels, values = values, pull = [0.1])])
    fig_storage.update_traces(textposition='inside', textinfo = 'label+percent')
    fig_storage.update(layout_showlegend=False)

    fig_storage_card = go.Figure(
        data=[
            go.Bar(name='Utilizado', x=[total_utilizado_storage], y=['Total'], orientation='h', marker_color='darkorange'),
            go.Bar(name='Disponível', x=[total_disponivel_storage], y=['Total'], orientation='h', marker_color='#efefef')
        ]
    )

    fig_storage_card.update_layout(barmode='stack', yaxis={'visible': False, 'showticklabels': False}, xaxis={'visible': False, 'showticklabels': False, 'showline': False}, autosize=False,
    height=100, plot_bgcolor='rgba(0,0,0,0)', margin=dict(
        l=10,
        r=0,
        b=10,
        t=0
    ))

    fig_storage_card.add_annotation(x=0, y=['Total'],
            text="Utilizado", xanchor="left",
            showarrow=False)

    utilizado_storage = (total_utilizado_storage / 134206) * 100
    utilizado_storage = round(utilizado_storage, 2)

    fig_storage_card.add_annotation(x=total_utilizado_storage, y=['Total'],
            text=str(utilizado_storage)+'%', xanchor="auto",
            showarrow=False)

    fig_storage_card.update_layout(legend=dict(
        yanchor="top",
        y=0.5,
        xanchor="right",
        x=1.2
    ))


    # ------------ total ------------------------- #
    

    df_total = df_relatorio_total[['Projeto', 'Máquina em Cluster', 'Mês']]               
    df_total = df_total.dropna()
    df_total = df_total.sort_values(by=['Mês'])                                                          

    fig_total = px.line(df_total, 
                        x = 'Mês', 
                        y = 'Máquina em Cluster',
                        color = 'Projeto'
                        )

    df_total_24x7 = df_relatorio_total[['Projeto', 'Máquina em 24x7', 'Mês']]               
    df_total_24x7 = df_total_24x7.dropna()
    df_total_24x7 = df_total_24x7.sort_values(by=['Mês'])                                                          

    fig_total_24x7 = px.line(df_total_24x7, 
                        x = 'Mês', 
                        y = 'Máquina em 24x7',
                        color = 'Projeto'
                        )
    
    # -------------------- PRODUÇÕES CIENTÍFICAS ----------------- #

    fig_producoes = px.bar(
        df_producoes,
        x="Unidade/Escola",
        y=["Produção Científica", "TCC, Dissertação ou Tese"],
        barmode="group",
        labels={'value':'Quantidade', 'variable':'Tipo de Publicação'},
        text_auto=True
        )

    # -------------------------- RETURN -------------------------- #

    return [
            fig_utilizacao_anual,
            fig_storage_card,
            fig_horas_nucleo_total,

            fig_maquina24x7, 
            fig_maquinaCluster, 
            fig_storage,
            fig_total,
            fig_total_24x7,
            fig_producoes,

            total_utilizado_storage, 
            total_disponivel_storage,
            total_utilizado_horas_nucleo, 
            total_disponivel_horas_nucleo,
            capacidade_horas_nucleo,
            value,
            qmes
           ]

##########################################################################################

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
    #no_break = CharField() 
    #status_no_break = BooleanField() 
    #tipo = CharField() 
    
class Grupo(BaseModel):
    nome = CharField()
    demanda = IntegerField()
    unidade = CharField()
    coordenador = CharField()
    status = BooleanField()
    date_beg = DateField()
    #date_end = DateField()
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
    #quota = ForeignKeyField(Quota, backref='quotas')

##########################################################################################

def create_tables():
    with database:
        database.create_tables([Cluster, Equipamento, Grupo, Usuario])

def get_object_or_404(model, *expressions):
    try:
        return model.get(*expressions)
    except model.DoesNotExist:
        abort(404)

def object_list(template_name, qr, var_name='object_list', **kwargs):
    kwargs[var_name] = qr
    return render_template(template_name, **kwargs)

@server.before_request
def before_request():
    g.db = database
    g.db.connect()

@server.after_request
def after_request(response):
    g.db.close()
    return response

##########################################################################################

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

##########################################################################################

if __name__ == '__main__':
    create_tables()
    server.run()
