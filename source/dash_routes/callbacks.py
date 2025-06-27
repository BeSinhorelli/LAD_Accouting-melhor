from dash import Input, Output
import plotly.graph_objs as go
import pandas as pd
from dash import html
from models import Producao
from config import *
from peewee import fn

from dash_routes.layout_armazenamento import dados_simulados
from dash_routes.layout_atividade import get_remote_reboot_history

def register_callbacks(app):
    # ATUALIZAR O TITULO
    @app.callback(
        Output("demand-title", "children"),
        [Input("year_dropdown", "value")]
    )
    def update_demand_title(selected_year):
        return f"Painel de Demandas {selected_year}"

    # ATUALIZAR O GRAFICO DE GRUṔOS
    @app.callback(
        Output("pie-chart", "figure"),
        [Input("month-dropdown", "value"),
        Input("year_dropdown", "value")]
    )
    def update_pie_chart(selected_month, selected_year):
        # Filtrar os dados com base no ano selecionado
        filtered_df, filtered_demandas_erro = filter_data_by_year(selected_year)
        # Filtrar os dados com base no mês selecionado
        if selected_month != "all":
            filtered_demandas_erro = filtered_demandas_erro[filtered_demandas_erro["Month"] == selected_month]

        # Extrair os nomes dos grupos
        names = extract_names_from_titles(filtered_demandas_erro)
        if names:
            name_counts = pd.Series(names).value_counts()
            total_demandas = name_counts.sum()

            return {
                "data": [
                    go.Pie(
                        labels=name_counts.index,
                        values=name_counts.values,
                        hole=0.3,
                        textinfo="percent+value",
                        hovertemplate="<b>Grupo:</b> %{label}<br><b>Quantidade:</b> %{value}<br><b>Percentual:</b> %{percent}<extra></extra>"
                    )
                ],
                "layout": go.Layout(
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["background"],
                    font={"color": COLORS["text"]},
                    margin=dict(l=20, r=20, t=20, b=20),
                    annotations=[
                        {
                            "text": f"Total: {total_demandas}",
                            "font": {"size": 14, "color": COLORS["text"]},
                            "showarrow": False,
                            "xref": "paper",
                            "yref": "paper",
                            "x": 0.5,
                            "y": 0.5,
                        }
                    ]
                )
            }
        # Se não houver dados, retornar um gráfico vazio
        return {
            "data": [],
            "layout": go.Layout(
                annotations=[
                    {
                        "text": "Nenhuma demanda especial registrada no mês selecionado",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20, "color": COLORS["gray"]},
                    }
                ],
                showlegend=False,
                xaxis={"visible": False},
                yaxis={"visible": False},
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"],
            )
        }

    # ATUALIZAR A LISTA DE DEMANDAS COM BASE NO MES SELECIONADO
    @app.callback(
        [Output("filtered-demands-store", "data"),
        Output("demand-list", "children")],
        [Input("month-dropdown", "value"),
        Input("year_dropdown", "value")]
    )
    def update_demand_list(selected_month, selected_year):
        # Filtrar os dados com base no ano selecionado
        _, filtered_demandas_erro = filter_data_by_year(selected_year)
        # Filtrar os dados com base no mês selecionado
        if selected_month != "all":
            filtered_demandas_erro = filtered_demandas_erro[filtered_demandas_erro["Month"] == selected_month]

        # Verificar se há dados filtrados
        if filtered_demandas_erro.empty:
            return [], [html.Li("Nenhuma demanda especial registrada no mês e ano selecionados", 
                                style={"color": COLORS["gray"], "font-size": "16px", "text-align": "center"})]

        # Criar a lista de demandas
        demand_list = [
            html.Li(
                html.A(
                    title, 
                    href=url, 
                    target="_blank", 
                    className="demand-list-a",  
                    title="Clique para abrir no GitHub",
                    style={
                    "color": COLORS['text'],  
                    
                }
                ),
                className="demand-list-li" ,
                style={"border-bottom": "1px solid gray", 
                    "padding": "0.5rem 0"} 
            )
            for title, url in zip(filtered_demandas_erro["Título"], filtered_demandas_erro["URL"])
        ]

        # Retornar os dados filtrados e a lista de demandas
        return filtered_demandas_erro.to_dict("records"), demand_list

    # ATUALIZAR O GRAFICO DE BARRAS
    @app.callback(
        Output("monthly-bar-chart", "figure"),
        [Input("year_dropdown", "value")]
    )
    def update_monthly_comparison(selected_year):
        # Filtrar os dados com base no ano selecionado
        filtered_df, filtered_demandas_erro = filter_data_by_year(selected_year)

        # Criar os gráficos com os dados filtrados
        monthly_counts = filtered_df["Month"].value_counts()
        monthly_error_counts = filtered_demandas_erro["Month"].value_counts()

        # Ordenar os meses
        month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        months_with_data = [m for m in month_order if m in monthly_counts.index]
        monthly_counts = monthly_counts.reindex(months_with_data)
        monthly_error_counts = monthly_error_counts.reindex(months_with_data, fill_value=0)

        return {
            "data": [
                go.Bar(
                    x=monthly_counts.index,
                    y=monthly_counts.values,
                    name="Demandas Abertas no mês",
                    marker={"color": COLORS["bar1"]},
                    text=monthly_counts.values,
                    textposition="outside",
                    width=0.6,
                    hovertemplate="<b>Mês:</b> %{x}<br><b>Demandas Abertas:</b> %{y}<extra></extra>"
                ),
                go.Bar(
                    x=monthly_counts.index,
                    y=monthly_error_counts.values,
                    name="Erros de Usuário",
                    marker={"color": COLORS["bar2"]},
                    text=monthly_error_counts.values,
                    textposition="outside",
                    width=0.6,
                    hovertemplate="<b>Mês:</b> %{x}<br><b>Erros de Usuário:</b> %{y}<extra></extra>"
                )
            ],
            "layout": go.Layout(
                xaxis={"title": "Mês", "color": COLORS["text"]},
                yaxis={"title": "Quantidade de Demandas Abertas", 
                    "color": COLORS["text"],
                    "automargin": True,
                    "range": [0, max(monthly_counts.max(), monthly_error_counts.max()) * 1.1]},
                barmode="overlay",
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"],
                font={"color": COLORS["text"]},
                hovermode="closest",
                margin=dict(l=70, r=30, t=40, b=60),
            )
        }

    # ATUALIZAR O TÍTULO DO GRAF. EVOLUÇAO DAS DEMANDAS COM O ANO SELECIONADO
    @app.callback(
        Output("funnel-chart-title", "children"),
        [Input("year_dropdown", "value"),
        Input("month-dropdown", "value")]
    )
    def update_funnel_chart_title(selected_year, selected_month):
        if selected_month == "all":
            return f"Evolução das Demandas - {selected_year}"
        else:
            month_names = {
                "Jan": "Janeiro", "Feb": "Fevereiro", "Mar": "Março", "Apr": "Abril",
                "May": "Maio", "Jun": "Junho", "Jul": "Julho", "Aug": "Agosto",
                "Sep": "Setembro", "Oct": "Outubro", "Nov": "Novembro", "Dec": "Dezembro"
            }
            month_name = month_names.get(selected_month, selected_month)
            return f"Ciclo de Demandas - {month_name} {selected_year}"
        
    # Callback para atualizar o gráfico de ciclos
    @app.callback(
        Output("funnel-chart", "figure"),
        [Input("year_dropdown", "value"),
        Input("month-dropdown", "value")]
    )
    def update_funnel_chart(selected_year, selected_month):
        # Filtrar os dados com base no ano selecionado
        filtered_df, _ = filter_data_by_year(selected_year)

        # Filtrar os dados com base no mês selecionado
        if selected_month != "all":
            filtered_df = filtered_df[filtered_df["Month"] == selected_month]

        # Gerar o gráfico de funil com os dados filtrados
        return plot_horizontal_bar_chart(filtered_df)

    # ATUALIZAR O TÍTULO DA LISTA DE DEMANDAS PENDENTES COM A QUANTIDADE DE DEMANDAS
    @app.callback(
        Output("open-demand-title", "children"),
        [Input("open-demands-store", "data")]
    )
    def update_open_demand_title(open_demands):
        # Verificar se há demandas pendentes
        num_open_demands = len(open_demands) if open_demands else 0
        return f"Lista de Demandas Pendentes ({num_open_demands})"

    # ATUALIZAR A LISTA DE DEMANDAS PENDENTES
    @app.callback(
        [Output("open-demands-store", "data"),
        Output("open-demand-list", "children")],
        [Input("month-dropdown", "value"),
        Input("year_dropdown", "value")]
    )
    def update_open_demand_list(selected_month, selected_year):
        # Filtrar os dados com base no ano selecionado
        filtered_df, _ = filter_data_by_year(selected_year)
        
        # Filtrar as demandas abertas
        open_demands = filtered_df[filtered_df["Status"].str.lower() == "open"]
        
        # Filtrar os dados com base no mês selecionado
        if selected_month != "all":
            open_demands = open_demands[open_demands["Month"] == selected_month]

        # Verificar se há dados filtrados
        if open_demands.empty:
            return [], [html.Li("Nenhuma demanda aberta registrada no mês e ano selecionados", 
                                style={"color": COLORS["gray"], "font-size": "16px", "text-align": "center"})]

        # Criar a lista de demandas pendentes
        open_demand_list = [
            html.Li(
                html.A(
                    title, 
                    href=url, 
                    target="_blank", 
                    className="demand-list-a",  
                    title="Clique para abrir no GitHub",
                    style={
                        "color": COLORS['text'],  
                    }
                ),
                className="demand-list-li",
                style={"border-bottom": "1px solid gray", 
                    "padding": "0.5rem 0"} 
            )
            for title, url in zip(open_demands["Título"], open_demands["URL"])
        ]

        # Retornar os dados filtrados e a lista de demandas abertas
        return open_demands.to_dict("records"), open_demand_list

    # ---------------------------------------  CALLBACK PRODUÇÕES - ATUALIZAÇÃO AUTOMÁTICA DO TÍTULO --------------------------------------- #
    # Atualiza o título do gráfico de produções científicas com base no ano mais recente registrado.
    @app.callback(
        Output('graph_production_title', 'children'),
        [Input('year_dropdown', 'value')]
    )
    def update_graph_production_title(_):
    # Busca o maior ano registrado no banco de dados
        try:
            ultima_atualizacao = Producao.select(fn.MAX(Producao.ano)).scalar() or '----'
        except Exception:
            ultima_atualizacao = '----'
        return f"Produções científicas por Unidade (2015-{ultima_atualizacao})"
    
    # ---------------------------------------  CALLBACK GRAF. ATIVIDADE --------------------------------------- #
    @app.callback(
        Output('uptime-line-chart', 'figure'),
        Input('year_dropdown', 'value'),  # ano global
        Input('month_dropdown_atividade', 'value')  # mês local
    )
    def update_uptime_chart(selected_year, selected_month):
        year = int(selected_year)
        month = int(selected_month)
        data = get_remote_reboot_history(year, month)
        
        days = [d['day'] for d in data]
        uptime = [d['uptime_hours'] for d in data]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days,
            y=uptime,
            mode='lines+markers',
            line=dict(color=first_color, width=3),
            marker=dict(size=8),
            name="Uptime (h)"
        ))

        fig.update_layout(
            xaxis_title='Dia do mês',
            yaxis_title='Horas em atividade',
            template='plotly_dark',
            yaxis=dict(range=[0, 24 + 2])
        )
        return fig
    
    # simulação de dados
    # ---------------------------------------  CALLBACK GRAF. ARMAZENAMENTO --------------------------------------- #
    @app.callback(
        Output('grafico-armazenamento', 'figure'),
        Input('grupo-dropdown', 'value')
    )
    def atualizar_grafico(grupo):
        df = dados_simulados(grupo)

        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Usado', x=df['nome'], y=df['usado']))
        fig.add_trace(go.Bar(name='Disponível', x=df['nome'], y=df['disponivel']))
        fig.update_layout(
            barmode='stack',
            yaxis_title='TB'
        )
        return fig