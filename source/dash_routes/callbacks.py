from dash import Input, Output, State, html, ctx
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from config import *
from peewee import fn
import calendar
from datetime import timedelta, date, datetime
import os
import glob

from models import Producao, Usuario, MonitoramentoRede, Relatorio

from dash_routes.layout_home import card_style, get_producoes, read_annual_report_with_cache
from dash_routes.layout_armazenamento import dados_simulados, dados_por_storage

# Importa funções do layout_atividade
from dash_routes.layout_atividade import (
    get_dias_ativos,
    get_total_paradas,
    get_paradas_ano,
    get_activity_data_for_year,
    get_available_years,
    get_reboot_history,
    get_data_ultima_parada,
    get_data_retorno_ultima_parada,
    get_duracao_parada
)

cache = Cache(server, config=CACHE_CONFIG)

def register_callbacks(app):
    
    # ============================================================================
    # HOME - DISPONIBILIDADE ANUAL
    # ============================================================================
    @app.callback(
        Output('uptime-percent', 'children'),
        Output('uptime-hours', 'children'),
        Output('downtime-percent', 'children'),
        Output('downtime-hours', 'children'),
        Output('monitoramento-info', 'children'),
        Input('year_dropdown', 'value')
    )
    def update_annual_uptime_summary(selected_year):
        if selected_year is None:
            selected_year = ano_atual
        
        year = int(selected_year)
        total_uptime = 0
        total_possible = 0
        
        activity_data = get_activity_data_for_year(year)
        
        for month_data in activity_data:
            days_in_month = calendar.monthrange(year, month_data['month'])[1]
            horas_possiveis = 24 * days_in_month
            horas_ativas = (month_data['activity_percent'] / 100) * horas_possiveis
            
            total_uptime += horas_ativas
            total_possible += horas_possiveis
        
        if total_possible > 0:
            uptime_percent = (total_uptime / total_possible) * 100
            downtime_percent = 100 - uptime_percent
        else:
            uptime_percent = 0
            downtime_percent = 0
        
        total_downtime = total_possible - total_uptime
        
        uptime_hours_fmt = f"{int(total_uptime):,}".replace(",", ".")
        downtime_hours_fmt = f"{int(total_downtime):,}".replace(",", ".")
        
        info_text = f"Monitoramento baseado nos relatórios Excel de {year}"

        return (
            f"{uptime_percent:.1f}%",
            f"{uptime_hours_fmt} horas",
            f"{downtime_percent:.1f}%",
            f"{downtime_hours_fmt} horas",
            info_text
        )

    # ============================================================================
    # HOME - CARDS DE RESUMO
    # ============================================================================
    @app.callback(
        Output("summary_cards", "children"),
        Input("year_dropdown", "value")
    )
    def update_summary_cards(selected_year):
        if selected_year is None:
            selected_year = str(ano_atual)
        
        # Dados do GitHub (demandas)
        if df.empty or 'Criado em' not in df.columns:
            total_issues = 0
            issues_done = 0
            desempenho = "N/A"
        else:
            df_filtered = df[df["Criado em"].dt.year == int(selected_year)].copy()
            total_issues = len(df_filtered)
            issues_done = len(df_filtered[df_filtered["Status"].str.lower() == "closed"])
            if total_issues == 0:
                desempenho = "N/A"
            else:
                desempenho = f"{(issues_done / total_issues * 100):.1f}%"

        # Total de horas usadas (dos Excel via layout_atividade)
        total_horas = 0
        activity_data = get_activity_data_for_year(int(selected_year))
        for month_data in activity_data:
            days_in_month = calendar.monthrange(int(selected_year), month_data['month'])[1]
            horas_ativas = (month_data['activity_percent'] / 100) * 24 * days_in_month
            total_horas += horas_ativas

        total_horas_fmt = f"{total_horas:,.0f}".replace(",", ".") if total_horas else "0"

        # usuários ativos (do banco - cadastro)
        usuarios_ativos = (
            Usuario.select()
            .where(
                (Usuario.status == True),
                (Usuario.observacoes != "Conta disciplina")
            )
            .count()
        )
        
        dias_ativos = get_dias_ativos()

        return html.Div([
            html.Div([
                html.H3("📊 Atividade", style={"color": first_color}),
                html.P(f"{dias_ativos}", style={"fontSize": "2.5rem", "fontWeight": "bold"}),
                html.Small("Desde o primeiro relatório", style={"color": "#ced4da"})
            ], style=card_style),
            html.Div([
                html.H3("👥 Usuários", style={"color": first_color}),
                html.P(f"{usuarios_ativos}", style={"fontSize": "2.5rem", "fontWeight": "bold"}),
                html.Small("Registrados e ativos", style={"color": "#ced4da"})
            ], style=card_style),
            html.Div([
                html.H3("🎯 Desempenho", style={"color": first_color}),
                html.P(desempenho, style={"fontSize": "2.5rem", "fontWeight": "bold"}),
                html.Small(f"{issues_done} de {total_issues} demandas atendidas", style={"color": "#ced4da"})
            ], style=card_style),
            html.Div([
                html.H3("💻 Horas Usadas", style={"color": first_color}),
                html.P(f"{total_horas_fmt} h", style={"fontSize": "2.5rem", "fontWeight": "bold"}),
                html.Small("Soma de Cluster + 24x7 no ano", style={"color": "#ced4da"})
            ], style=card_style),
            html.Div([
                html.H3("📚 Produções", style={"color": first_color}),
                html.P(f"{get_producoes()}", style={"fontSize": "2.5rem", "fontWeight": "bold"}),
                html.Small("Produções Científicas e Acadêmicas", style={"color": "#ced4da"})
            ], style=card_style),
        ], style={
            "display": "flex",
            "justifyContent": "center",
            "marginTop": "2rem",
            "gap": "1rem",
            "flexWrap": "wrap"
        })
    
    # ============================================================================
    # PAINEL ATIVIDADE - CARDS
    # ============================================================================
    @app.callback(
        Output('paradas-total', 'children'),
        Input('year_dropdown', 'value'),
    )
    def update_total_paradas(selected_year):
        if selected_year is None:
            selected_year = ano_atual
        total = get_total_paradas(selected_year)
        return f"{total}"
    
    @app.callback(
        Output('paradas-title', 'children'),
        Input('year_dropdown', 'value'),
    )
    def update_paradas_title(selected_year):
        if selected_year is None:
            selected_year = ano_atual
        return f"📉 Paradas Registradas em {selected_year}"
    
    @app.callback(
        Output('dias-ativos-display', 'children'),
        Input('year_dropdown', 'value')
    )
    def update_dias_ativos_display(selected_year):
        return get_dias_ativos()
    
    @app.callback(
        Output('ultima-parada', 'children'),
        Input('year_dropdown', 'value')
    )
    def update_ultima_parada(selected_year):
        return get_data_ultima_parada()
    
    @app.callback(
        Output('ultimo-retorno', 'children'),
        Input('year_dropdown', 'value')
    )
    def update_ultimo_retorno(selected_year):
        return get_data_retorno_ultima_parada()
    
    @app.callback(
        Output('duracao-parada', 'children'),
        Input('year_dropdown', 'value')
    )
    def update_duracao_parada(selected_year):
        return get_duracao_parada()
    
    # ============================================================================
    # PAINEL ATIVIDADE - GRÁFICO DE ATIVIDADE (UPTIME) - LINHA DIÁRIA
    # ============================================================================
    @app.callback(
        Output('uptime-line-chart', 'figure'),
        Input('year_dropdown', 'value'),  
        Input('month_dropdown_atividade', 'value')  
    )
    def update_uptime_chart(selected_year, selected_month):
        if selected_year is None:
            selected_year = ano_atual
        if selected_month is None:
            selected_month = datetime.now().month
            
        year = int(selected_year)
        month = int(selected_month)
        
        data = get_reboot_history(year, month)
        
        if not data:
            fig = go.Figure()
            fig.update_layout(
                annotations=[dict(
                    text=f"📭 Nenhum dado de atividade disponível para {month}/{year}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color=COLORS["gray"])
                )],
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"]
            )
            return fig

        def format_hm(decimal_hours):
            horas = int(decimal_hours)
            minutos = int(round((decimal_hours - horas) * 60))
            return f"{horas}h {minutos:02d}min"
        
        days = [d['day'] for d in data]
        uptime = [d['uptime_hours'] for d in data]

        uptime_fmt = [format_hm(h) for h in uptime]
        downtime_fmt = [format_hm(24 - h) for h in uptime]
        customdata = list(zip(uptime_fmt, downtime_fmt))

        colors = ['#00ff00' if h == 24 else '#ff6b6b' for h in uptime]
        last_day = calendar.monthrange(year, month)[1]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days,
            y=uptime,
            mode='lines+markers',
            line=dict(color=first_color, width=3),
            marker=dict(size=10, color=colors, line=dict(width=1, color="white")),
            name="Tempo em Atividade (h)",
            customdata=customdata,
            hovertemplate=
                "<b>📅 Dia %{x}</b><br>" +
                "✅ Em atividade: %{customdata[0]}<br>" +
                "❌ Inativo: %{customdata[1]}<br>" +
                "<extra></extra>"
        ))
        
        fig.add_hline(y=24, line_dash="dash", line_color="gray", opacity=0.5,
                      annotation_text="Meta (24h)", annotation_position="bottom right")
        
        fig.update_layout(
            xaxis_title='📅 Dia do Mês',
            yaxis_title='⏱️ Tempo em Atividade (horas)',
            template='plotly_dark',
            yaxis=dict(range=[0, 26], tickmode='linear', dtick=4),
            xaxis=dict(tickmode='linear', dtick=5, range=[0.5, last_day + 0.5]),
            margin=dict(t=40, b=40, l=60, r=60),
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font={"color": COLORS["text"]},
            hovermode='closest',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig
    
    # ============================================================================
    # PAINEL ATIVIDADE - GRÁFICO DE BARRAS (ATIVIDADE MENSAL)
    # ============================================================================
    @app.callback(
        Output('yearly-activity-chart', 'figure'),
        Input('year_dropdown', 'value')
    )
    def update_yearly_activity_chart(selected_year):
        if selected_year is None:
            selected_year = ano_atual
        
        year = int(selected_year)
        activity_data = get_activity_data_for_year(year)
        
        if not activity_data or all(d['activity_percent'] == 0 for d in activity_data):
            fig = go.Figure()
            fig.update_layout(
                annotations=[dict(
                    text=f"📭 Sem dados de atividade para {year}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color=COLORS["gray"])
                )],
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"]
            )
            return fig
        
        months = [d['month_name'] for d in activity_data]
        activity_percent = [d['activity_percent'] for d in activity_data]
        activity_hours = [d['activity_hours'] for d in activity_data]
        
        colors = []
        for p in activity_percent:
            if p >= 70:
                colors.append('#51cf66')
            elif p >= 40:
                colors.append('#ffd43b')
            else:
                colors.append('#ff6b6b')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=months,
            y=activity_percent,
            name="Atividade (%)",
            marker_color=colors,
            text=[f"{p:.1f}%" for p in activity_percent],
            textposition='outside',
            textfont=dict(color='white', size=11),
            hovertemplate="<b>📅 %{x}</b><br>📊 Atividade: %{y:.1f}%<br>⏱️ Média: %{customdata:.1f} h/dia<extra></extra>",
            customdata=activity_hours
        ))
        
        fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5,
                      annotation_text="Capacidade Máxima", annotation_position="bottom right")
        fig.add_hline(y=70, line_dash="dot", line_color="orange", opacity=0.3,
                      annotation_text="Meta (70%)", annotation_position="bottom left")
        
        fig.update_layout(
            title=f"📈 Atividade do Laboratório - {year}",
            xaxis_title="📅 Mês",
            yaxis_title="📊 Atividade (%)",
            template='plotly_dark',
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font={"color": COLORS["text"]},
            yaxis=dict(range=[0, 110], tickmode='linear', dtick=20),
            xaxis=dict(tickangle=45),
            showlegend=False,
            hovermode='closest'
        )
        return fig

    # ============================================================================
    # PAINEL ATIVIDADE - GRÁFICO DE LINHA (EVOLUÇÃO MENSAL)
    # ============================================================================
    @app.callback(
        Output('activity-line-chart', 'figure'),
        Input('year_dropdown', 'value')
    )
    def update_activity_line_chart(selected_year):
        if selected_year is None:
            selected_year = ano_atual
        
        year = int(selected_year)
        activity_data = get_activity_data_for_year(year)
        
        if not activity_data or all(d['activity_percent'] == 0 for d in activity_data):
            fig = go.Figure()
            fig.update_layout(
                annotations=[dict(
                    text=f"📭 Sem dados de atividade para {year}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color=COLORS["gray"])
                )],
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"]
            )
            return fig
        
        months = [d['month_name'] for d in activity_data]
        activity_percent = [d['activity_percent'] for d in activity_data]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months,
            y=activity_percent,
            mode='lines+markers',
            line=dict(color=first_color, width=4),
            marker=dict(size=12, color=first_color, symbol='circle', line=dict(color='white', width=2)),
            name="Atividade (%)",
            fill='tozeroy',
            fillcolor='rgba(253, 195, 102, 0.15)',
            hovertemplate="<b>📅 %{x}</b><br>📊 Atividade: %{y:.1f}%<extra></extra>"
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=activity_percent,
            mode='text',
            text=[f"{p:.1f}%" for p in activity_percent],
            textposition='top center',
            textfont=dict(color=first_color, size=10),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_hline(y=70, line_dash="dash", line_color="orange", opacity=0.5,
                      annotation_text="Meta (70%)", annotation_position="bottom right")
        
        fig.update_layout(
            title=f"📈 Evolução Mensal da Atividade - {year}",
            xaxis_title="📅 Mês",
            yaxis_title="📊 Atividade (%)",
            template='plotly_dark',
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font={"color": COLORS["text"]},
            yaxis=dict(range=[0, 110], tickmode='linear', dtick=20),
            xaxis=dict(tickangle=45),
            hovermode='closest'
        )
        return fig
    
    # ============================================================================
    # PAINEL ATIVIDADE - GRÁFICO DE PARADAS
    # ============================================================================
    @app.callback(
        Output('paradas-gerais-fig', 'figure'),
        Input('year_dropdown', 'value'),
    )
    def update_paradas_gerais(selected_year):
        if selected_year is None:
            selected_year = ano_atual
        
        paradas = get_paradas_ano(selected_year)
        
        if not paradas:
            return go.Figure().update_layout(
                annotations=[{
                    'text': f"📭 Nenhuma parada registrada em {selected_year}",
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': dict(size=14, color=COLORS["gray"]),
                    'x': 0.5,
                    'y': 0.5
                }],
                template='plotly_dark',
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"]
            )
        
        x_labels = []
        hover_texts = []
        y_values = []

        for p in paradas:
            inicio = p['inicio']
            fim = p['fim']
            duracao = p['duracao']
            
            if (fim - inicio).days >= 1:
                label = f"{inicio.strftime('%d/%m')}"
                hover = (
                    f"<b>📅 Início:</b> {inicio.strftime('%d/%m/%Y - %H:%M')}<br>"
                    f"<b>📅 Retorno:</b> {fim.strftime('%d/%m/%Y - %H:%M')}<br>"
                    f"<b>⏱️ Duração:</b> {int(duracao//24)}d {int(duracao%24)}h"
                )
            else:
                label = inicio.strftime('%d/%m')
                horas = int(duracao)
                minutos = int(round((duracao % 1) * 60))
                hover = (
                    f"<b>📅 Data:</b> {inicio.strftime('%d/%m/%Y')}<br>"
                    f"<b>⏱️ Período:</b> {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}<br>"
                    f"<b>⏱️ Duração:</b> {horas}h {minutos:02d}min"
                )
            x_labels.append(label)
            hover_texts.append(hover)
            y_values.append(duracao)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_labels,
            y=y_values,
            name="Horas de Inatividade",
            marker=dict(color='#ff6b6b', line=dict(color='white', width=1)),
            customdata=hover_texts,
            hovertemplate="%{customdata}<extra></extra>",
            text=[f"{d:.1f}h" for d in y_values],
            textposition='outside',
            textfont=dict(size=10)
        ))

        fig.update_layout(
            xaxis_title="📅 Data da Parada",
            yaxis_title="⏱️ Duração (horas)",
            template='plotly_dark',
            margin=dict(t=40, b=40, l=60, r=60),
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font={"color": COLORS["text"]},
            showlegend=False
        )
        return fig
    
    # ============================================================================
    # GRAF. REDE (Monitoramento)
    # ============================================================================
    @app.callback(
        Output("monitoramento-graph", "figure"),
        Output("monitoramento-status-card", "children"),
        Input("interval-monitoramento", "n_intervals"),
        Input("filtro-data-monitoramento", "date"),
        Input("modo-visualizacao", "value")
    )
    def atualizar_grafico_monitoramento(n_intervals, data_filtro, modo_visualizacao):
        try:
            registros = list(MonitoramentoRede.select().dicts())
            if not registros:
                fig = go.Figure()
                fig.update_layout(
                    annotations=[dict(
                        text="📭 Sem dados de monitoramento de rede",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5,
                        showarrow=False,
                        font=dict(size=14, color=COLORS["gray"])
                    )],
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["background"]
                )
                return fig, html.Div("📭 Sem dados de monitoramento", 
                                    style={"color": "orange", "padding": "25px", "margin": "16px", "textAlign": "center"})

            df = pd.DataFrame(registros)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["latency"] = pd.to_numeric(df["latency"], errors='coerce')
            df["packet_loss"] = pd.to_numeric(df["packet_loss"], errors='coerce')
            df["status"] = df["status"].fillna("Desconhecido")
            
            if data_filtro:
                data_filtro = pd.to_datetime(data_filtro).date()
                df = df[df["timestamp"].dt.date == data_filtro]

            if df.empty:
                fig = go.Figure()
                fig.update_layout(
                    annotations=[dict(
                        text=f"📭 Sem dados para {data_filtro.strftime('%d/%m/%Y') if data_filtro else 'a data selecionada'}",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5,
                        showarrow=False,
                        font=dict(size=14, color=COLORS["gray"])
                    )],
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["background"]
                )
                return fig, html.Div(f"📭 Sem dados para {data_filtro.strftime('%d/%m/%Y')}", 
                                    style={"color": "orange", "padding": "25px", "margin": "16px", "textAlign": "center"})
            
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
            
            df_queda = df[df["status"] == "QUEDA"]
            df_queda_plot = df_queda.copy()
            if not df_queda_plot.empty:
                df_queda_plot["latency_vis"] = df_agg["latency"].max() + 10 if not df_agg["latency"].isna().all() else 100

            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_agg["timestamp_group"], y=df_agg["latency"],
                name="📡 Latência (ms)",
                mode="lines",
                line=dict(color="#00eaff", width=3),
                hovertemplate="<b>Latência:</b> %{y:.1f} ms<extra></extra>"
            ))
            
            fig.add_trace(go.Scatter(
                x=df_agg["timestamp_group"], y=df_agg["packet_loss"],
                name="📉 Perda de Pacotes (%)",
                mode="lines",
                line=dict(color="#ffb300", width=3, dash='dot'),
                yaxis="y2",
                hovertemplate="<b>Perda:</b> %{y:.1f}%<extra></extra>"
            ))
            
            if not df_queda_plot.empty:
                fig.add_trace(go.Scatter(
                    x=df_queda_plot["timestamp"],
                    y=df_queda_plot["latency_vis"],
                    name="⚠️ Queda de Rede",
                    mode="markers",
                    marker=dict(color="red", size=12, symbol="x", line=dict(width=2, color="white")),
                    hovertemplate="<b>⚠️ QUEDA DE REDE</b><br>%{x|%H:%M}<extra></extra>",
                    yaxis="y2"
                ))
                
                for t in df_queda["timestamp"]:
                    fig.add_vrect(
                        x0=t - pd.Timedelta(minutes=2),
                        x1=t + pd.Timedelta(minutes=2),
                        fillcolor="red",
                        opacity=0.15,
                        line_width=0,
                        layer="below"
                    )
            
            fig.add_hline(y=50, line_dash="dash", line_color="orange", opacity=0.5,
                         annotation_text="Alerta (50ms)", annotation_position="bottom right")
            fig.add_hline(y=100, line_dash="dash", line_color="red", opacity=0.5,
                         annotation_text="Crítico (100ms)", annotation_position="bottom right")
            
            fig.update_layout(
                xaxis_title="⏱️ Horário",
                yaxis=dict(title="📡 Latência (ms)", gridcolor="#444", zerolinecolor="#888"),
                yaxis2=dict(title="📉 Perda de Pacotes (%)", overlaying='y', side='right', range=[0, 100], gridcolor="#444"),
                plot_bgcolor=third_color,
                paper_bgcolor=third_color,
                font=dict(color="white"),
                margin=dict(l=60, r=80, t=60, b=60),
                legend=dict(x=0, y=1.12, orientation="h", bgcolor="rgba(0,0,0,0)"),
                hovermode="x unified"
            )

            status_atual = df.iloc[-1]["status"]
            cor_status = {
                "OK": "#51cf66",
                "LENTO": "#ffd43b",
                "QUEDA": "#ff6b6b"
            }.get(status_atual, "gray")
            
            icone_status = {
                "OK": "✅",
                "LENTO": "⚠️",
                "QUEDA": "❌"
            }.get(status_atual, "🔄")

            status_card = html.Div([
                html.Div([
                    html.Span(icone_status, style={"fontSize": "2rem", "marginRight": "1rem"}),
                    html.Div([
                        html.H4("Status da Rede:", style={"margin": "0", "color": "white"}),
                        html.Span(status_atual, style={
                            "fontWeight": "bold",
                            "color": cor_status,
                            "fontSize": "1.2rem"
                        })
                    ])
                ], style={"display": "flex", "alignItems": "center"})
            ], style={
                "backgroundColor": "#343a40",
                "padding": "1rem",
                "margin": "1rem 0",
                "borderLeft": f"8px solid {cor_status}",
                "borderRadius": "1rem",
                "boxShadow": "0 4px 24px rgba(0,0,0,0.4)"
            })

            return fig, status_card

        except Exception as e:
            print(f"Erro no monitoramento: {e}")
            fig = go.Figure()
            fig.update_layout(
                annotations=[dict(
                    text=f"❌ Erro ao carregar dados: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color="red")
                )],
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"]
            )
            return fig, html.Div(f"❌ Erro: {e}", style={"color": "red", "textAlign": "center"})

    @app.callback(
        Output("filtro-data-monitoramento", "date"),
        Input("dia-anterior", "n_clicks"),
        Input("dia-posterior", "n_clicks"),
        State("filtro-data-monitoramento", "date"),
        prevent_initial_call=True
    )
    def navegar_dias(n_ant, n_post, data_atual):
        if data_atual is None:
            return datetime.now().date()
        
        data = pd.to_datetime(data_atual).date()

        if ctx.triggered_id == "dia-anterior":
            return data - timedelta(days=1)
        elif ctx.triggered_id == "dia-posterior":
            return data + timedelta(days=1)
        
        return data

    # ============================================================================
    # PAINEL DEMANDAS (mantido igual)
    # ============================================================================
    @app.callback(
        Output("demand-title", "children"),
        Input("year_dropdown", "value")
    )
    def update_demand_title(selected_year):
        if selected_year is None:
            selected_year = ano_atual
        return f"📋 Painel de Demandas {selected_year}"

    @app.callback(
        Output("pie-chart", "figure"),
        Input("month-dropdown", "value"),
        Input("year_dropdown", "value")
    )
    def update_pie_chart(selected_month, selected_year):
        if demandas_erro.empty:
            return {
                "data": [],
                "layout": go.Layout(
                    annotations=[{
                        "text": "📭 Nenhuma demanda especial registrada",
                        "xref": "paper", "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20, "color": COLORS["gray"]}
                    }],
                    showlegend=False,
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["background"]
                )
            }
        
        if selected_year is None:
            selected_year = str(ano_atual)
        if selected_month is None:
            selected_month = "all"
        
        _, filtered_demandas_erro = filter_data_by_year(selected_year)
        
        if filtered_demandas_erro.empty:
            return {
                "data": [],
                "layout": go.Layout(
                    annotations=[{
                        "text": f"📭 Nenhuma demanda especial em {selected_year}",
                        "xref": "paper", "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20, "color": COLORS["gray"]}
                    }],
                    showlegend=False,
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["background"]
                )
            }
        
        if selected_month != "all" and 'Month' in filtered_demandas_erro.columns:
            filtered_demandas_erro = filtered_demandas_erro[filtered_demandas_erro["Month"] == selected_month]

        if filtered_demandas_erro.empty:
            return {
                "data": [],
                "layout": go.Layout(
                    annotations=[{
                        "text": f"📭 Nenhuma demanda especial em {selected_month}/{selected_year}",
                        "xref": "paper", "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20, "color": COLORS["gray"]}
                    }],
                    showlegend=False,
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["background"]
                )
            }

        names = extract_names_from_titles(filtered_demandas_erro)
        if names:
            name_counts = pd.Series(names).value_counts()
            total_demandas = name_counts.sum()

            return {
                "data": [go.Pie(
                    labels=name_counts.index,
                    values=name_counts.values,
                    hole=0.3,
                    textinfo="percent+value",
                    textposition="auto",
                    marker=dict(colors=px.colors.qualitative.Set3),
                    hovertemplate="<b>👥 Grupo:</b> %{label}<br><b>📊 Quantidade:</b> %{value}<br><b>📈 Percentual:</b> %{percent}<extra></extra>"
                )],
                "layout": go.Layout(
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["background"],
                    font={"color": COLORS["text"]},
                    margin=dict(l=20, r=20, t=20, b=20),
                    annotations=[{
                        "text": f"📊 Total: {total_demandas}",
                        "font": {"size": 14, "color": COLORS["text"]},
                        "showarrow": False,
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.5,
                        "y": 0.5
                    }]
                )
            }
        
        return {
            "data": [],
            "layout": go.Layout(
                annotations=[{
                    "text": "📭 Nenhuma demanda especial no período",
                    "xref": "paper", "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20, "color": COLORS["gray"]}
                }],
                showlegend=False,
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"]
            )
        }

    @app.callback(
        Output("filtered-demands-store", "data"),
        Output("demand-list", "children"),
        Input("month-dropdown", "value"),
        Input("year_dropdown", "value")
    )
    def update_demand_list(selected_month, selected_year):
        if demandas_erro.empty:
            return [], [html.Li("📭 Nenhuma demanda especial registrada", 
                                style={"color": COLORS["gray"], "font-size": "16px", "text-align": "center", "listStyle": "none"})]
        
        if selected_year is None:
            selected_year = str(ano_atual)
        if selected_month is None:
            selected_month = "all"
        
        _, filtered_demandas_erro = filter_data_by_year(selected_year)
        
        if filtered_demandas_erro.empty:
            return [], [html.Li(f"📭 Nenhuma demanda especial em {selected_year}", 
                                style={"color": COLORS["gray"], "font-size": "16px", "text-align": "center", "listStyle": "none"})]
        
        if selected_month != "all" and 'Month' in filtered_demandas_erro.columns:
            filtered_demandas_erro = filtered_demandas_erro[filtered_demandas_erro["Month"] == selected_month]

        if filtered_demandas_erro.empty:
            return [], [html.Li(f"📭 Nenhuma demanda especial em {selected_month}/{selected_year}", 
                                style={"color": COLORS["gray"], "font-size": "16px", "text-align": "center", "listStyle": "none"})]

        demand_list = [
            html.Li(
                html.A(
                    f"📌 {title}", 
                    href=url, 
                    target="_blank", 
                    style={"color": COLORS['text'], "textDecoration": "none"},
                    title="Clique para abrir no GitHub"
                ),
                style={"border-bottom": "1px solid #444", "padding": "0.75rem 0", "listStyle": "none"}
            )
            for title, url in zip(filtered_demandas_erro["Título"], filtered_demandas_erro["URL"])
        ]

        return filtered_demandas_erro.to_dict("records"), demand_list

    @app.callback(
        Output("monthly-bar-chart", "figure"),
        Input("year_dropdown", "value")
    )
    def update_monthly_comparison(selected_year):
        if selected_year is None:
            selected_year = str(ano_atual)
        
        if df.empty or 'Month' not in df.columns:
            return {
                "data": [],
                "layout": go.Layout(
                    annotations=[{
                        "text": "📭 Sem dados de demandas disponíveis",
                        "xref": "paper", "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20, "color": COLORS["gray"]}
                    }],
                    showlegend=False,
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["background"]
                )
            }
        
        filtered_df, filtered_demandas_erro = filter_data_by_year(selected_year)

        if filtered_df.empty or 'Month' not in filtered_df.columns:
            return {
                "data": [],
                "layout": go.Layout(
                    annotations=[{
                        "text": f"📭 Nenhuma demanda em {selected_year}",
                        "xref": "paper", "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20, "color": COLORS["gray"]}
                    }],
                    showlegend=False,
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["background"]
                )
            }

        monthly_counts = filtered_df["Month"].value_counts()
        monthly_error_counts = filtered_demandas_erro["Month"].value_counts() if not filtered_demandas_erro.empty else pd.Series()

        month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        months_with_data = [m for m in month_order if m in monthly_counts.index]
        monthly_counts = monthly_counts.reindex(months_with_data)
        monthly_error_counts = monthly_error_counts.reindex(months_with_data, fill_value=0)

        max_y = max(monthly_counts.max(), monthly_error_counts.max()) if not monthly_counts.empty else 10

        return {
            "data": [
                go.Bar(
                    x=monthly_counts.index,
                    y=monthly_counts.values,
                    name="📋 Demandas Abertas",
                    marker={"color": COLORS["bar1"]},
                    text=monthly_counts.values,
                    textposition="outside",
                    width=0.6,
                    hovertemplate="<b>📅 Mês:</b> %{x}<br><b>📊 Demandas:</b> %{y}<extra></extra>"
                ),
                go.Bar(
                    x=monthly_counts.index,
                    y=monthly_error_counts.values,
                    name="⚠️ Erros de Usuário",
                    marker={"color": COLORS["bar2"]},
                    text=monthly_error_counts.values,
                    textposition="outside",
                    width=0.6,
                    hovertemplate="<b>📅 Mês:</b> %{x}<br><b>⚠️ Erros:</b> %{y}<extra></extra>"
                )
            ],
            "layout": go.Layout(
                xaxis={"title": "📅 Mês", "color": COLORS["text"]},
                yaxis={"title": "📊 Quantidade", "color": COLORS["text"], "range": [0, max_y * 1.1]},
                barmode="overlay",
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"],
                font={"color": COLORS["text"]},
                hovermode="closest",
                margin=dict(l=70, r=30, t=40, b=60)
            )
        }

    @app.callback(
        Output("funnel-chart-title", "children"),
        Input("year_dropdown", "value"),
        Input("month-dropdown", "value")
    )
    def update_funnel_chart_title(selected_year, selected_month):
        if selected_year is None:
            selected_year = ano_atual
        if selected_month is None:
            selected_month = "all"
            
        if selected_month == "all":
            return f"🔄 Evolução das Demandas - {selected_year}"
        else:
            month_names = {
                "Jan": "Janeiro", "Feb": "Fevereiro", "Mar": "Março", "Apr": "Abril",
                "May": "Maio", "Jun": "Junho", "Jul": "Julho", "Aug": "Agosto",
                "Sep": "Setembro", "Oct": "Outubro", "Nov": "Novembro", "Dec": "Dezembro"
            }
            month_name = month_names.get(selected_month, selected_month)
            return f"🔄 Ciclo de Demandas - {month_name} {selected_year}"
        
    @app.callback(
        Output("funnel-chart", "figure"),
        Input("year_dropdown", "value"),
        Input("month-dropdown", "value")
    )
    def update_funnel_chart(selected_year, selected_month):
        if selected_year is None:
            selected_year = str(ano_atual)
        if selected_month is None:
            selected_month = "all"
        
        if df.empty:
            return {
                "data": [],
                "layout": go.Layout(
                    title="📭 Sem dados disponíveis",
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["background"],
                    font={"color": COLORS["text"]}
                )
            }
        
        filtered_df, _ = filter_data_by_year(selected_year)

        if selected_month != "all" and 'Month' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Month"] == selected_month]

        return plot_horizontal_bar_chart(filtered_df)

    @app.callback(
        Output("open-demand-title", "children"),
        Input("open-demands-store", "data")
    )
    def update_open_demand_title(open_demands):
        num_open_demands = len(open_demands) if open_demands else 0
        return f"⏳ Demandas Pendentes ({num_open_demands})"

    @app.callback(
        Output("open-demands-store", "data"),
        Output("open-demand-list", "children"),
        Input("month-dropdown", "value"),
        Input("year_dropdown", "value")
    )
    def update_open_demand_list(selected_month, selected_year):
        if selected_year is None:
            selected_year = str(ano_atual)
        if selected_month is None:
            selected_month = "all"
        
        if df.empty or 'Status' not in df.columns:
            return [], [html.Li("📭 Nenhuma demanda aberta", 
                                style={"color": COLORS["gray"], "font-size": "16px", "text-align": "center", "listStyle": "none"})]
        
        filtered_df, _ = filter_data_by_year(selected_year)
        
        if filtered_df.empty:
            return [], [html.Li(f"📭 Nenhuma demanda aberta em {selected_year}", 
                                style={"color": COLORS["gray"], "font-size": "16px", "text-align": "center", "listStyle": "none"})]
        
        open_demands = filtered_df[filtered_df["Status"].str.lower() == "open"]
        
        if selected_month != "all" and 'Month' in open_demands.columns:
            open_demands = open_demands[open_demands["Month"] == selected_month]

        if open_demands.empty:
            return [], [html.Li(f"📭 Nenhuma demanda aberta em {selected_month}/{selected_year}", 
                                style={"color": COLORS["gray"], "font-size": "16px", "text-align": "center", "listStyle": "none"})]

        open_demand_list = [
            html.Li(
                html.A(
                    f"⏳ {title}", 
                    href=url, 
                    target="_blank", 
                    style={"color": COLORS['text'], "textDecoration": "none"},
                    title="Clique para abrir no GitHub"
                ),
                style={"border-bottom": "1px solid #444", "padding": "0.75rem 0", "listStyle": "none"}
            )
            for title, url in zip(open_demands["Título"], open_demands["URL"])
        ]

        return open_demands.to_dict("records"), open_demand_list
    
    # ============================================================================
    # USO DE MÁQUINAS (mantido do banco)
    # ============================================================================
    @app.callback(
        Output('graph_annual_usage', 'figure'),
        Output('graph_monthly_usage', 'figure'),
        Output('graph_24x7_machine', 'figure'),
        Output('graph_cluster_machine', 'figure'),
        Output('graph_cluster_usage_group', 'figure'),
        Output('graph_24x7_usage_group', 'figure'),
        Output('machine_usage', 'children'),
        Output('machine_availability', 'children'),
        Output('machine_capacity', 'children'),
        Output('month_slider', 'value'),
        Output('month_slider', 'max'),
        Input('year_dropdown', 'value'),
        Input('month_slider', 'value')
    )
    def update_figure(yearValue, selected_month):
        if yearValue is None:
            yearValue = ano_atual
        if selected_month is None:
            selected_month = 1
        
        max_month_data = Relatorio.select(fn.MAX(Relatorio.mes)).where(Relatorio.ano == yearValue).scalar()
        max_month = max_month_data if max_month_data is not None else 12
        current_month = min(selected_month, max_month) if selected_month else 1
        
        if selected_month and selected_month > max_month:
            current_month = max_month
            
        if current_month == 0:
            current_month = 1
            
        days = month_days(current_month, yearValue)

        annual_query = list(Relatorio.select().where(Relatorio.ano == yearValue).dicts())
        df_annual = pd.DataFrame(annual_query)
        
        monthly_query = list(Relatorio.select().where((Relatorio.ano == yearValue) & (Relatorio.mes == current_month)).dicts())
        df_data = pd.DataFrame(monthly_query)

        if not df_annual.empty:
            df_annual.rename(columns=rename_col, inplace=True)
            df_annual[COL_MES] = df_annual[COL_MES].astype(int)
        
        if not df_data.empty:
            df_data.rename(columns=rename_col, inplace=True)
        
        machine_capacity = (2108 * 24 * days)

        if not df_annual.empty and COL_MES in df_annual.columns:
            df_machine_usage = df_annual.groupby([COL_MES]).agg({
                COL_24X7: 'sum', 
                COL_CLUSTER: 'sum'
            })
        else:
            df_machine_usage = pd.DataFrame(columns=[COL_24X7, COL_CLUSTER])

        machine_availability_annual = []

        for index, row in df_machine_usage.iterrows():
            total_usage = row[COL_24X7] + row[COL_CLUSTER]
            capacity = 2108 * 24 * month_days(index, yearValue)
            machine_availability_annual.append(capacity - total_usage)

        if not df_machine_usage.empty:
            df_machine_usage["Disponível"] = machine_availability_annual

        if df_machine_usage.empty:
            graph_annual_usage = go.Figure()
            graph_annual_usage.update_layout(
                annotations=[dict(
                    text="📭 Sem dados disponíveis para o ano selecionado",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color=COLORS["gray"])
                )],
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"]
            )
        else:
            graph_annual_usage = px.bar(
                df_machine_usage,
                y=[COL_24X7, COL_CLUSTER, "Disponível"], 
                labels={'value':'💻 Uso (CPU-Hora)', 'variable':'📊 Tipo de uso', COL_MES: '📅 Mês'},
                color_discrete_map={"Disponível": "white", COL_CLUSTER: "#ef553b", COL_24X7: "#636efa"},
                barmode='stack'
            )
            graph_annual_usage.update_layout(
                xaxis=dict(tickmode='linear', dtick=1, tick0=1, range=[0.5, max_month + 0.5]),
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"],
                font={"color": COLORS["text"]}
            )

        # Gráficos simplificados
        graph_monthly_usage = go.Figure()
        graph_monthly_usage.update_layout(
            annotations=[dict(
                text="📊 Dados carregados com sucesso",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color=COLORS["gray"])
            )],
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"]
        )
        
        graph_24x7_machine = go.Figure()
        graph_24x7_machine.update_layout(plot_bgcolor=COLORS["background"], paper_bgcolor=COLORS["background"])
        
        graph_cluster_machine = go.Figure()
        graph_cluster_machine.update_layout(plot_bgcolor=COLORS["background"], paper_bgcolor=COLORS["background"])
        
        graph_cluster_usage_group = go.Figure()
        graph_cluster_usage_group.update_layout(plot_bgcolor=COLORS["background"], paper_bgcolor=COLORS["background"])
        
        graph_24x7_usage_group = go.Figure()
        graph_24x7_usage_group.update_layout(plot_bgcolor=COLORS["background"], paper_bgcolor=COLORS["background"])

        machine_usage_val = 0
        machine_availability_val = 0
        machine_capacity_val = 0

        if not df_data.empty and COL_24X7 in df_data.columns and COL_CLUSTER in df_data.columns:
            machine_usage_val = df_data[COL_24X7].sum() + df_data[COL_CLUSTER].sum()
            machine_availability_val = machine_capacity - machine_usage_val
            machine_capacity_val = machine_capacity

        return [
            graph_annual_usage, graph_monthly_usage, graph_24x7_machine,
            graph_cluster_machine, graph_cluster_usage_group, graph_24x7_usage_group,
            f"{machine_usage_val:,.0f}".replace(",", ".") if machine_usage_val > 0 else "0",
            f"{machine_availability_val:,.0f}".replace(",", ".") if machine_availability_val > 0 else "0",
            f"{machine_capacity_val:,.0f}".replace(",", ".") if machine_capacity_val > 0 else "0",
            current_month, max_month
        ]

    # ============================================================================
    # ARMAZENAMENTO
    # ============================================================================
    @app.callback(
        Output('grafico-storage', 'figure'),
        Output('grafico-storage-group', 'figure'),
        Output('storage_usage', 'children'),
        Output('storage_availability', 'children'),
        Input('year_dropdown', 'value'),
        Input('month_slider_storage', 'value'),
    )
    def update_storage_graphs(yearValue, month):
        if yearValue is None:
            yearValue = ano_atual
        if month is None:
            month = 1
            
        query = Relatorio.select(
            Relatorio.projeto,
            Relatorio.storage_cluster,
            Relatorio.storage_24x7
        ).where(
            (Relatorio.ano == yearValue) & (Relatorio.mes == month)
        ).dicts()

        df_data = pd.DataFrame(list(query))

        if df_data.empty:
            fig_empty = go.Figure()
            fig_empty.update_layout(
                annotations=[dict(
                    text="📭 Sem dados disponíveis para o período selecionado",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color=COLORS["gray"])
                )],
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"]
            )
            return fig_empty, fig_empty, "N/A", "N/A"

        df_storage = df_data[['projeto', 'storage_cluster', 'storage_24x7']].dropna(thresh=2).fillna(0)
        df_storage['Total'] = df_storage['storage_cluster'] + df_storage['storage_24x7']

        storage_capacity = 134206
        storage_usage = df_storage['Total'].sum()
        storage_availability = storage_capacity - storage_usage

        new_row = pd.DataFrame([['Disponível', 0, 0, storage_availability]], 
                               columns=['projeto', 'storage_cluster', 'storage_24x7', 'Total'])
        df_storage = pd.concat([new_row, df_storage], ignore_index=True)

        storage_usage_percent = round((storage_usage / storage_capacity) * 100, 2)
        annotations = [
            dict(x=0, y=['Total'], text="💾 Utilizado", xanchor="left", showarrow=False),
            dict(x=storage_usage, y=['Total'], text=f"{storage_usage_percent}%", xanchor="auto", showarrow=False)
        ]

        graph_storage = go.Figure(
            data=[
                go.Bar(name='💾 Utilizado', x=[storage_usage], y=['Total'], orientation='h', marker_color='darkorange'),
                go.Bar(name='📀 Disponível', x=[storage_availability], y=['Total'], orientation='h', marker_color='#efefef')
            ]
        )
        graph_storage.update_layout(
            barmode='stack',
            yaxis={'visible': False},
            xaxis={'visible': False},
            height=90,
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=0, b=10, t=0),
            legend=dict(yanchor="top", y=0.5, xanchor="right", x=1.2),
            annotations=annotations
        )

        graph_storage_group = go.Figure(data=[go.Pie(labels=df_storage['projeto'], values=df_storage['Total'], hole=0.3)])
        graph_storage_group.update_traces(textposition='auto', textinfo='label+percent')
        graph_storage_group.update_layout(
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font={"color": COLORS["text"]}
        )

        return graph_storage, graph_storage_group, f"{storage_usage:,.0f}".replace(",", "."), f"{storage_availability:,.0f}".replace(",", ".")

    # ============================================================================
    # PRODUÇÕES CIENTÍFICAS
    # ============================================================================
    @app.callback(
        Output('graph_production_title', 'children'),
        Input('year_dropdown', 'value')
    )
    def update_graph_production_title(_):
        try:
            ultima_atualizacao = Producao.select(fn.MAX(Producao.ano)).scalar() or '----'
        except Exception:
            ultima_atualizacao = '----'
        return f"📚 Produções Científicas por Unidade (2015-{ultima_atualizacao})"

    @app.callback(
        Output('graph_production', 'figure'),
        Input('year_dropdown', 'value')
    )
    def update_graph_production(_):
        producoes = list(Producao.select().dicts())
        if producoes:
            df_production = pd.DataFrame(producoes)
            df_production = df_production.rename(columns={
                'unidade': 'Unidade/Escola',
                'cientifica': 'Produção Científica',
                'tcc': 'TCC, Dissertação ou Tese'
            })
            df_production = df_production.groupby('Unidade/Escola', as_index=False)[['Produção Científica', 'TCC, Dissertação ou Tese']].sum()
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

        if df_production.empty or (df_production['Produção Científica'].sum() == 0 and df_production['TCC, Dissertação ou Tese'].sum() == 0):
            fig = go.Figure()
            fig.update_layout(
                annotations=[dict(
                    text="📭 Sem dados de produção disponíveis",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color=COLORS["gray"])
                )],
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["background"]
            )
            return fig
        
        graph_production = px.bar(
            df_production,
            x="Unidade/Escola",
            y=["Produção Científica", "TCC, Dissertação ou Tese"],
            barmode="group",
            labels={'value':'📊 Quantidade', 'variable':'📚 Tipo de Publicação'},
            text_auto=True
        )
        graph_production.update_layout(
            template='plotly_dark',
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font={"color": COLORS["text"]}
        )
        return graph_production

    print("✅ Todos os callbacks foram registrados com sucesso!")