from dash import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
from dash import html, ctx
from models import Producao, Usuario, MonitoramentoRede
from config import *
from peewee import fn
import calendar
from datetime import timedelta, date

from dash_routes.layout_home import card_style, get_producoes, read_annual_report_with_cache
from dash_routes.layout_armazenamento import dados_simulados
from dash_routes.layout_atividade import monitoramento_atividade, get_reboot_history, get_dias_ativos, get_total_paradas, get_paradas_ano


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
    
    # ---------------------------------------  CALLBACK CARD PARADAS REGISTRADAS LAYOUT_ATIVIDADE
    # --------------------------------------- #
    @app.callback(
        Output('paradas-total', 'children'),
        Input('year_dropdown', 'value'),
    )
    def update_total_paradas(selected_year):
        total = get_total_paradas(selected_year)
        return f"{total}"
    
    @app.callback(
        Output('paradas-title', 'children'),
        Input('year_dropdown', 'value'),
    )
    def update_paradas_title(year):
        return f"Paradas Registradas em {year}"
    
    # ---------------------------------------  CALLBACK GRAF. ATIVIDADE --------------------------------------- #
    @app.callback(
        Output('uptime-line-chart', 'figure'),
        Input('year_dropdown', 'value'),  
        Input('month_dropdown_atividade', 'value')  
    )
    def update_uptime_chart(selected_year, selected_month):
        year = int(selected_year)
        month = int(selected_month)
        data = get_reboot_history(year, month)

        def format_hm(decimal_hours):
            horas = int(decimal_hours)
            minutos = int(round((decimal_hours - horas) * 60))
            return f"{horas}h {minutos:02d}min"
        
        monitoramento_inicio = monitoramento_atividade
        data_filtrada = []

        for d in data:
            data_atual = date(year, month, d['day'])
            if data_atual >= monitoramento_inicio:
                data_filtrada.append(d)
        
        days = [d['day'] for d in data_filtrada]
        uptime = [d['uptime_hours'] for d in data_filtrada]
        downtime = [round(24 - h, 1) for h in uptime] 

        uptime_fmt = [format_hm(h) for h in uptime]
        downtime_fmt = [format_hm(d) for d in downtime]
        customdata = list(zip(uptime_fmt, downtime_fmt))

        colors = ['#00ff00' if h == 24 else '#ff3333' for h in uptime]

        last_day = calendar.monthrange(year, month)[1]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days,
            y=uptime,
            mode='lines+markers',
            line=dict(color="grey", width=3),
            marker=dict(size=10, color=colors),
            name="Uptime (h)",
            customdata=customdata,
            hovertemplate=
                "Dia: %{x}<br>" +
                "Em atividade: %{customdata[0]}<br>" +
                "Inativo: %{customdata[1]}" 
                "<extra></extra>"
        ))
        if year == 2025 and month == 5:
            fig.add_vline(
                x=10,
                line=dict(color='orange', width=2, dash='dash'),
                annotation_text="Início do monitoramento",
                annotation_position="top left",
                annotation_font_color="orange"
            )

        if (year < 2025) or (year == 2025 and month < 5):
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                text="Monitoramento ainda não iniciado nesse mês",
                showarrow=False,
                font=dict(size=14, color="red"),
        )
        fig.update_layout(
            xaxis_title='Dia do mês',
            yaxis_title='Tempo em atividade',
            template='plotly_dark',
            yaxis=dict(range=[0, 24 + 2], tickmode='linear', dtick=12),  
            xaxis=dict(tickmode='linear', dtick=5, range=[0.5, last_day + 0.5]),
            margin=dict(t= 40,b=40),         
        )
        return fig
    
    # ---------------------------------------  CALLBACK GRAF. ANUAL DE PARADAS --------------------------------------- #
    @app.callback(
        Output('paradas-gerais-fig', 'figure'),
        Input('year_dropdown', 'value'),
    )
    def update_paradas_gerais(selected_year):
        paradas = get_paradas_ano(selected_year)
        if not paradas:
            return go.Figure().update_layout(
                annotations=[{
                    'text': "Nenhuma parada registrada no ano selecionado",
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': dict(size=14, color="red"),
                    'x': 0.5,
                    'y': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'middle'
                }],
                template='plotly_dark',
                margin=dict(t=40, b=40)
            )
        x_labels = []
        hover_texts = []
        y_values = []

        for p in paradas:
            inicio = p['inicio']
            fim = p['fim']
            duracao = p['duracao']
            if (fim - inicio).days >= 1:
                label = f"{inicio.strftime('%d/%m')} - {fim.strftime('%d/%m')}"
                hover = (
                    f"<b>Início:</b> {inicio.strftime('%d/%m/%Y - %H:%M')}<br>"
                    f"<b>Retorno:</b> {fim.strftime('%d/%m/%Y - %H:%M')}<br>"
                    f"<b>Duração:</b> {int(duracao//24)}d {int(duracao%24)}h"
                )
            else:
                label = inicio.strftime('%d/%m')
                horas = int(duracao)
                minutos = int(round((duracao % 1) * 60))
                hover = (
                    f"<b>Data:</b> {inicio.strftime('%d/%m/%Y')}<br>"
                    f"<b>Período:</b> {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}<br>"
                    f"<b>Duração:</b> {horas}h {minutos:02d}min"
                )
            x_labels.append(label)
            hover_texts.append(hover)
            y_values.append(duracao)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_labels,
            y=y_values,
            name="Horas de inatividade",
            marker=dict(color='crimson'),
            customdata=hover_texts,
            hovertemplate="%{customdata}<extra></extra>"
        ))

        fig.update_layout(
            xaxis_title="Período da Parada",
            yaxis_title="Duração Total (h)",
            template='plotly_dark',
            margin=dict(t=40, b=40)
        )
        return fig


    # ---------------------------------------  CALLBACK DESEMPENHO ANUAL LAYOUT_HOME --------------------------------------- #
    def get_annual_uptime_summary(year):
        monitoramento_inicio = monitoramento_atividade
        total_uptime = 0
        total_downtime = 0

        for month in range(1, 13):
            monthly_data = get_reboot_history(year, month)
            for day_data in monthly_data:
                day = day_data['day']
                current_date = date(year, month, day)

                if current_date < monitoramento_inicio:
                    continue  # Ignora dias anteriores ao início do monitoramento que foi em 10/05/2025

                uptime = day_data['uptime_hours']
                downtime = 24 - uptime
                total_uptime += uptime
                total_downtime += downtime

        total_hours = total_uptime + total_downtime
        uptime_percent = (total_uptime / total_hours) * 100 if total_hours > 0 else 0
        downtime_percent = 100 - uptime_percent

        return {
            "uptime_hours": total_uptime,
            "downtime_hours": total_downtime,
            "uptime_percent": round(uptime_percent, 1),
            "downtime_percent": round(downtime_percent, 1)
        }
    @app.callback(
        Output('uptime-percent', 'children'),
        Output('uptime-hours', 'children'),
        Output('downtime-percent', 'children'),
        Output('downtime-hours', 'children'),
        Input('year_dropdown', 'value')
    )
    def update_annual_uptime_summary(selected_year):
        year = int(selected_year)
        summary = get_annual_uptime_summary(year)

        return (
            f"{summary['uptime_percent']}%",
            f"{int(summary['uptime_hours'])} horas",
            f"{summary['downtime_percent']}%",
            f"{int(summary['downtime_hours'])} horas"
        )

    # ---------------------------------------  CALLBACK CARD DESEMPENHO LAYOUT_HOME --------------------------------------- #
    @app.callback(
        Output("summary_cards", "children"),
        Input("year_dropdown", "value")
    )
    def update_summary_cards(selected_year):
        df_filtered = df[df["Criado em"].dt.year == int(selected_year)].copy()

        total_issues = len(df_filtered)
        issues_done = len(df_filtered[df_filtered["Status"].str.lower() == "closed"])
        if total_issues == 0:
            desempenho = "N/A"
        else:
            desempenho = f"{(issues_done / total_issues * 100):.1f}%"

        # Total de horas usadas 
        df_annual = read_annual_report_with_cache(selected_year)
        total_horas = 0
        if not df_annual.empty:
            # Tenta somar as duas colunas, se existirem
            col_cluster = [c for c in df_annual.columns if "Cluster" in c]
            col_24x7 = [c for c in df_annual.columns if "24x7" in c]
            if col_cluster and col_24x7:
                total_horas = df_annual[col_cluster[0]].fillna(0).sum() + df_annual[col_24x7[0]].fillna(0).sum()
            elif col_cluster:
                total_horas = df_annual[col_cluster[0]].fillna(0).sum()
            elif col_24x7:
                total_horas = df_annual[col_24x7[0]].fillna(0).sum()
        total_horas_fmt = f"{total_horas:,.0f}".replace(",", ".") if total_horas else "0"

        # usuários ativos
        usuarios_ativos = Usuario.select().where(Usuario.status == True).count()

        return html.Div([
            html.Div([
                 html.H3("Atividade", style={"color": first_color}),
                 html.P(f"{get_dias_ativos()} dias", style={"fontSize": "2.5rem", "fontWeight": "bold"}),
            html.Small("Desde a última parada", style={"color": "#ced4da"})
            ], style=card_style),
            html.Div([
                 html.H3("Usuários", style={"color": first_color}),
                 html.P(f"{usuarios_ativos}", style={"fontSize": "2.5rem", "fontWeight": "bold"}),
            html.Small("Registrados e ativos", style={"color": "#ced4da"})
            ], style=card_style),
            html.Div([
                html.H3("Desempenho", style={"color": first_color}),
                html.P(desempenho, style={"fontSize": "2.5rem", "fontWeight": "bold"}),
                html.Small(f"{issues_done} de {total_issues} demandas atendidas", style={"color": "#ced4da"})
            ], style=card_style),
            html.Div([
                html.H3("Horas Usadas", style={"color": first_color}),
                html.P(f"{total_horas_fmt} h", style={"fontSize": "2.5rem", "fontWeight": "bold"}),
                html.Small("Soma de Cluster + 24x7 no ano", style={"color": "#ced4da"})
            ], style=card_style),
            #html.Div([
                #html.H3("Volume Disponível", style={"color": first_color}),
            #]),
            html.Div([
                html.H3("Produções Totais", style={"color": first_color}),
                html.P(f"{get_producoes()}", style={"fontSize": "2.5rem", "fontWeight": "bold"}),
                html.Small("Produções Científicas e Acadêmicas", style={"color": "#ced4da"})
            ], style=card_style),
        ], style={
            "display": "flex",
            "justifyContent": "center",
            "marginTop": "2rem",
            "gap":"1rem"
        })
    
     
    # ---------------------------------------  CALLBACK GRAF. REDE --------------------------------------- #
    @app.callback(
        Output("monitoramento-graph", "figure"),
        Output("monitoramento-status-card", "children"),
        Input("interval-monitoramento", "n_intervals"),
        Input("filtro-data-monitoramento", "date"),
        Input("modo-visualizacao", "value")
    )
    def atualizar_grafico_monitoramento(n_intervals, data_filtro, modo_visualizacao):
        try:
            # Consulta todos os registros do banco
            registros = list(MonitoramentoRede.select().dicts())
            if not registros:
                return go.Figure(), html.Div("Sem dados de monitoramento", style={"color": "orange", "padding": "25px", "margin": "16px"})

            df = pd.DataFrame(registros)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["latency"] = pd.to_numeric(df["latency"], errors='coerce')
            df["packet_loss"] = pd.to_numeric(df["packet_loss"], errors='coerce')
            df["status"] = df["status"].fillna("Desconhecido")
            
            if data_filtro:
                data_filtro = pd.to_datetime(data_filtro).date()
                df = df[df["timestamp"].dt.date == data_filtro]

            if df.empty:
                return go.Figure(), html.Div("Sem dados para a data selecionada", style={"color": "orange", "padding": "25px", "margin": "16px"})
            
            if modo_visualizacao == "agrupado":
                df["timestamp_group"] = df["timestamp"].dt.floor("5min")
                df_agg = df.groupby("timestamp_group").agg({
                    "latency": "mean",
                    "packet_loss": "mean"
                }).reset_index()
            else:
                df_agg = df[["timestamp", "latency", "packet_loss"]].copy()
                df_agg.rename(columns={"timestamp": "timestamp_group"}, inplace=True)
                df_agg.sort_values("timestamp_group", inplace=True)
            # status de QUEDA
            df_queda = df[df["status"] == "QUEDA"]
            df_queda_plot = df_queda.copy()
            df_queda_plot["latency_vis"] = 96

            # Gráfico
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_agg["timestamp_group"], y=df_agg["latency"],
                name="Latência (ms)",
                mode="lines",
                line=dict(color="#00eaff", width=3),
                marker=dict(size=7, color="#00eaff", line=dict(width=1, color="white")),
                hovertemplate="%{y:.1f}"
            ))
            fig.add_trace(go.Scatter(
                x=df_agg["timestamp_group"], y=df_agg["packet_loss"],
                name="% Perda de Pacotes",
                mode="lines",
                line=dict(color="#ffb300", width=3,),
                marker=dict(size=7, color="#ffb300", line=dict(width=1, color="white")),
                yaxis="y2",
                hovertemplate="%{y:.1f}%"
            ))
            fig.add_trace(go.Scatter(
                x=df_queda_plot["timestamp"],
                y=df_queda_plot["latency_vis"],
                name="Queda de Rede",
                mode="markers",
                marker=dict(color="red", size=12, symbol="x", line=dict(width=2, color="white")),
                hovertemplate="%{x|%H:%M}",
                yaxis="y2"
            ))
            # Destaques visuais 
            for t in df_queda["timestamp"]:
                fig.add_vrect(
                    x0=t - pd.Timedelta(minutes=2),
                    x1=t + pd.Timedelta(minutes=2),
                    fillcolor="red",
                    opacity=0.2,
                    line_width=0,
                    layer="below"
                )
            fig.update_layout(
                xaxis_title="Horário",
                yaxis=dict(title="Latência (ms)", gridcolor="#444", zerolinecolor="#888", range=[0, df_agg["latency"].max() + 10]),
                yaxis2=dict(title="Perda de Pacotes (%)", overlaying='y', side='right', range=[0, 100], gridcolor="#444"),
                plot_bgcolor=third_color,
                paper_bgcolor=third_color,
                font=dict(color="white"),
                margin=dict(l=40, r=40, t=40, b=40),
                legend=dict(x=0, y=1.15, orientation="h", bgcolor="rgba(0,0,0,0)"),
                hovermode="x unified"  
            )

            # Último status
            status_atual = df.iloc[-1]["status"]
            cor_status = {
                "OK": "green",
                "LENTO": "orange",
                "QUEDA": "red"
            }.get(status_atual, "gray")

            status_card = html.Div([
                html.H4("Status da Rede:", style={"margin": "0 10px 0 0"}),
                html.Div([
                    html.Span(status_atual, style={
                        "fontWeight": "bold",
                        "color": cor_status,
                        "textShadow": "0 0 5px black"
                    })
                ])
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "fontSize": "1.5rem",
                "background": "#343a40",
                "padding": "1.5rem",
                "margin": "1rem 0",
                "borderLeft": f"8px solid {cor_status}",
                "borderRadius": "1rem",
                "textAlign": "center",
                "color": "white",
                "boxShadow": "0 4px 24px rgba(0,0,0,0.4)"
            })

            return fig, status_card

        except Exception as e:
            return go.Figure(), html.Div(f"Erro: {e}", style={"color": "red"})

    @app.callback(
        Output("filtro-data-monitoramento", "date"),
        Input("dia-anterior", "n_clicks"),
        Input("dia-posterior", "n_clicks"),
        State("filtro-data-monitoramento", "date"),
        prevent_initial_call=True
    )
    def navegar_dias(n_ant, n_post, data_atual):
        data = pd.to_datetime(data_atual).date()

        if ctx.triggered_id == "dia-anterior":
            return data - timedelta(days=1)
        elif ctx.triggered_id == "dia-posterior":
            return data + timedelta(days=1)
        
        return data
    

    # simulação de dados
    # ---------------------------------------  CALLBACK GRAF. ARMAZENAMENTO --------------------------------------- #
    @app.callback(
        Output('grafico-armazenamento', 'figure'),
        Input('grupo-dropdown', 'value')
    )
    def atualizar_grafico(grupo):
        df = dados_simulados(grupo)

        import plotly.graph_objects as go
        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                xaxis={'visible': False},
                yaxis={'visible': False},
                annotations=[
                    dict(
                        text=f'Nenhum dado de armazenamento encontrado o grupo {grupo}.',
                        xref="paper", yref="paper",
                        showarrow=False,
                        font=dict(size=16)
                    )
                ]
            )
            return fig
    
        fig = go.Figure()
    
        # Usado
        fig.add_trace(go.Bar(
            name='Usado',
            x=df['nome'],
            y=df['usado'],
            marker_color='#d62728', 
        ))
        
        # Disponível
        fig.add_trace(go.Bar(
            name='Disponível',
            x=df['nome'],
            y=df['disponivel'],
            marker_color='#2ca02c',
        ))
        
        # Linha com o valor dedicado
        fig.add_trace(go.Scatter(
            x=df['nome'],
            y=df['dedicado'],
            mode='markers+text',
            name='Dedicado',
            line=dict(color='orange', width=2),
            marker=dict(size=8, color='orange'),
            text=df['dedicado'].apply(lambda x: f'<b>{x:.2f} TB</b>'),
            textposition='top center',
            textfont=dict(color='white')
        ))
        
        fig.update_layout(
            barmode='stack',
            yaxis_title='Volume em TB',
            font=dict(color="#f8f9fa"),
            hovermode="x unified",
            legend_traceorder='reversed'
        )
        return fig