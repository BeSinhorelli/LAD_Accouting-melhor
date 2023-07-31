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
import os

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
pio.templates.default = "plotly_dark"

first_color = '#FDC366'
second_color = '#212529'
third_color = '#111111'
fourth_color = '#1E6EFF'


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
        dbc.Row([
            dbc.Col(
                html.Img(id="logo", src=app.get_asset_url("LabLAD.png"),
                style={'max-width': '100px'}
                ),
                style={'max-width': '100px'}
            ),
            dbc.Col(
                html.H2("LAD Accounting Dashboard"),
                style={'color':'white', 'margin': 'auto 0 auto 10px'},
                width=4
            )
            ],
            style={'margin': 'auto', 'justify-content':'center'}
        ),
        style={'padding': '2rem', 'background-color': second_color}
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
                style={'border': 'none'}
            )
        ],
        width=10, 
        className='mx-auto'
        )
], style={'background-color':second_color, 'padding':'1rem'}
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


    # ------------ USO HISTÓRICO DAS MÁQUINAS - ANUAL -------------- #

    df_total_maquina = df_relatorio_total[['Máquina em Cluster', 'Máquina em 24x7', 'Mês']]               
    df_total_maquina = df_total_maquina.sort_values(by=['Mês'], ascending=False)
    df_total_maquina = df_total_maquina.groupby(['Mês']).agg({
        'Máquina em 24x7' : 'sum',
        'Máquina em Cluster' : 'sum'
    })

    fig_utilizacao_anual = px.bar(
        df_total_maquina, 
        y=["Máquina em 24x7", "Máquina em Cluster"],
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
    total_disponivel_horas_nucleo = (2108*24*mes) - total_utilizado_horas_nucleo
    capacidade_horas_nucleo = (2108*24*mes)

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

    return [
            fig_utilizacao_anual,
            fig_storage_card,
            fig_horas_nucleo_total,

            fig_maquina24x7, 
            fig_maquinaCluster, 
            fig_storage,
            fig_total,
            fig_total_24x7,

            total_utilizado_storage, 
            total_disponivel_storage,
            total_utilizado_horas_nucleo, 
            total_disponivel_horas_nucleo,
            capacidade_horas_nucleo,
            value,
            qmes
           ]
        

if __name__ == '__main__':
    app.run_server(debug=True)
