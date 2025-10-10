from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime, date
import calendar
from peewee import fn

from models import Atividade, RebootHistory, database

from config import *

# Definição da data de inicio do monitoramento
monitoramento_atividade = date(2025, 5, 10)
def conectar_banco():
    if database.is_closed():
        database.connect()

# Pega o último uptime
def get_dias_ativos():
    conectar_banco()
    try:
        # Busca o último registro de atividade
        ultima_atividade = Atividade.select().order_by(Atividade.data.desc()).get()
        boot_time_str = ultima_atividade.uptime
        boot_time = datetime.strptime(boot_time_str, "%Y-%m-%d %H:%M:%S")
        
        dias_ativos = (datetime.now() - max(boot_time, datetime.combine(monitoramento_atividade, datetime.min.time()))).days
        return f"{dias_ativos}"
    except Atividade.DoesNotExist:
        return "Nenhum dado de atividade"
    except Exception as e:
        print(f"Erro ao obter dias ativos do banco: {e}")
        return "Erro"

# Pega a data de retorno da última parada
def get_data_retorno_ultima_parada():
    conectar_banco()
    try:
        ultima_atividade = Atividade.select().order_by(Atividade.id.desc()).get()
        boot_time_str = ultima_atividade.uptime
        boot_time = datetime.strptime(boot_time_str, "%Y-%m-%d %H:%M:%S")
        return boot_time.strftime("%d/%m/%Y - %H:%M")
    except Atividade.DoesNotExist:
        return "Erro ao obter"
    except Exception as e:
        print(f"Erro ao obter data de retorno do banco: {e}")
        return "Erro"

def get_data_ultima_parada():
    conectar_banco()
    try:
        ultima_parada = RebootHistory.select().order_by(RebootHistory.data_fim.desc()).get()
        return ultima_parada.data_fim.strftime("%d/%m/%Y - %H:%M")
    except RebootHistory.DoesNotExist:
        return "Sem paradas registradas"
    except Exception as e:
        print(f"Erro ao obter data da última parada do banco: {e}")
        return "Erro"

# Calcula a duração da última parada
def get_duracao_parada():
    conectar_banco()
    try:
        ultima_parada_fim = datetime.strptime(
            Atividade.select().order_by(Atividade.id.desc()).get().uptime,
            "%Y-%m-%d %H:%M:%S"
        )
        ultima_parada_inicio = RebootHistory.select().order_by(RebootHistory.data_fim.desc()).get().data_fim
        
        duracao = ultima_parada_fim - ultima_parada_inicio
        total_seconds = duracao.total_seconds()
        
        dias = int(total_seconds // 86400)
        horas = int((total_seconds % 86400) // 3600)
        minutos = int((total_seconds % 3600) // 60)
        
        parts = []
        if dias > 0:
            parts.append(f"{dias}d")
        if horas > 0:
            parts.append(f"{horas}h")
        if minutos > 0:
            parts.append(f"{minutos}m") 
        return " ".join(parts) if parts else "0m"
    except (Atividade.DoesNotExist, RebootHistory.DoesNotExist):
        return "N/A"
    except Exception as e:
        print(f"Erro ao calcular duração da parada: {e}")
        return "Erro"

# Coletar o histórico de reboot para o gráfico
def get_reboot_history(year, month):
    conectar_banco()
    
    current_date = datetime.now()
    selected_date = datetime(year, month, 1)

    if selected_date > current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0):
        return []

    reboots = RebootHistory.select().where(
        ((fn.strftime('%Y', RebootHistory.data_inicio) == str(year)) | (fn.strftime('%Y', RebootHistory.data_fim) == str(year))) &
        ((fn.strftime('%m', RebootHistory.data_inicio) == f'{month:02d}') | (fn.strftime('%m', RebootHistory.data_fim) == f'{month:02d}')) &
        (RebootHistory.data_inicio >= datetime.combine(monitoramento_atividade, datetime.min.time()))
    ).order_by(RebootHistory.data_inicio)

    # Períodos de parada
    shutdown_periods = []
    try:
        ultima_atividade = Atividade.select().order_by(Atividade.id.desc()).get()
        current_boot_time = datetime.strptime(ultima_atividade.uptime, "%Y-%m-%d %H:%M:%S")
        reboots_list = list(reboots)
        if reboots_list:
            last_reboot_end = reboots_list[-1].data_fim
            shutdown_periods.append((last_reboot_end, current_boot_time))
    except (Atividade.DoesNotExist, RebootHistory.DoesNotExist):
        reboots_list = list(reboots)
    
    # Processa os demais reboots (fora o atual)
    for i in range(len(reboots_list) - 1):
        parada_inicio = reboots_list[i].data_fim
        parada_fim = reboots_list[i+1].data_inicio
        shutdown_periods.append((parada_inicio, parada_fim))
    
    today = datetime.now().date()
    last_day = calendar.monthrange(year, month)[1]
    result = []
    for d in range(1, last_day + 1):
        dt = date(year, month, d)
        
        if dt < monitoramento_atividade:
            continue
        
        if dt > today:
            continue
            
        uptime_hours = 24.0
        
        for parada_inicio, parada_fim in shutdown_periods:
            if dt >= parada_inicio.date() and dt <= parada_fim.date():
                day_start = datetime.combine(dt, datetime.min.time())
                day_end = datetime.combine(dt, datetime.max.time())
                
                parada_interval_start = max(day_start, parada_inicio)
                parada_interval_end = min(day_end, parada_fim)
                
                parada_duration_seconds = (parada_interval_end - parada_interval_start).total_seconds()
                uptime_hours -= parada_duration_seconds / 3600
        
        result.append({
            "day": d,
            "uptime_hours": max(0.0, min(round(uptime_hours, 1), 24.0))
        })

    return result

# Card total de paradas anuais
def get_total_paradas(selected_year):
    conectar_banco()
    year = int(selected_year)
    reboots = RebootHistory.select().where(
        (fn.strftime('%Y', RebootHistory.data_inicio) == str(year)) &
        (RebootHistory.data_inicio >= datetime.combine(monitoramento_atividade, datetime.min.time()))
    ).order_by(RebootHistory.data_inicio)
    
    if not reboots:
        return 0
    
    parada_times = [reboot.data_fim for reboot in reboots]
    
    try:
        current_boot_time = datetime.strptime(
            Atividade.select().order_by(Atividade.id.desc()).get().uptime,
            "%Y-%m-%d %H:%M:%S"
        )
        parada_times.append(current_boot_time)
    except Atividade.DoesNotExist:
        pass
    
    if len(parada_times) < 2:
        return 0
        
    total_paradas = 0
    for i in range(len(parada_times) - 1):
        duracao = parada_times[i+1] - parada_times[i]
        if duracao.total_seconds() > 60:
            total_paradas += 1
            
    return total_paradas

# Gráfico de paradas anuais
def get_paradas_ano(selected_year):
    conectar_banco()
    year = int(selected_year)
    reboots_list = list(RebootHistory.select().where(
        (fn.strftime('%Y', RebootHistory.data_inicio) == str(year)) &
        (RebootHistory.data_inicio >= datetime.combine(monitoramento_atividade, datetime.min.time()))
    ).order_by(RebootHistory.data_inicio))
    
    paradas = []
    # Processa as paradas entre os reboots
    for i in range(len(reboots_list) - 1):
        parada_inicio = reboots_list[i].data_fim
        parada_fim = reboots_list[i+1].data_inicio
        
        duracao_seconds = (parada_fim - parada_inicio).total_seconds()
        if duracao_seconds > 60:
            paradas.append({
                'inicio': parada_inicio,
                'fim': parada_fim,
                'duracao': duracao_seconds / 3600
            })
    # Adiciona a parada atual
    if reboots_list:
        try:
            last_reboot_end = reboots_list[-1].data_fim
            current_boot_time = datetime.strptime(
                Atividade.select().order_by(Atividade.id.desc()).get().uptime,
                "%Y-%m-%d %H:%M:%S"
            )
            duracao_seconds = (current_boot_time - last_reboot_end).total_seconds()
            if duracao_seconds > 60:
                paradas.append({
                    'inicio': last_reboot_end,
                    'fim': current_boot_time,
                    'duracao': duracao_seconds / 3600
                })
        except (Atividade.DoesNotExist, RebootHistory.DoesNotExist):
            pass
    return paradas

# Layout
layout_atividade = html.Div([
    # Título
    html.H2("Painel de Atividade", style={
        'color': fifth_color,
        'text-align': 'center',
    }),
    # Dias em atividade contínua e última ocorrência
    html.Div([
        html.Div([
            html.H3("Dias em Atividade Contínua", style={
                'text-align': 'center',
                'margin-bottom': '1rem',
                'font-size': '1.5rem'
            }),
            html.P(get_dias_ativos(), style={
                'color': first_color,
                'text-align': 'center',
                'font-size': '3rem',
                'font-weight': 'bold',
                'margin': '0',
                'text-shadow': '2px 2px 10px rgba(0,0,0,0.6)',
                'transition': 'all 0.3s ease-in-out'
            }),
        ], style={
            'background': '#343a40',
            'border-left': f'6px solid {first_color}',
            'border-radius': '1rem',
            'padding': '1.5rem',
            'margin': '1rem',
            'box-shadow': '0 0 10px rgba(0,0,0,0.3)',
            'flex': '0 1 20%',
            'min-width': '280px'
        }),

        html.Div([
            html.H3("Última Ocorrência", style={
                'text-align': 'center',
                'margin-bottom': '1rem',
                'font-size': '1.5rem'
            }),
            html.Div([
                html.Div([
                    html.P("Parada", style={'text-align': 'center', 'color': 'lightgray', 'margin-bottom': '0.2rem'}),
                    html.P(get_data_ultima_parada(), style={
                        'color': first_color,
                        'text-align': 'center',
                        'font-size': '1.4rem',
                        'font-weight': 'bold'
                    }),
                ], style={'flex': '1', 'padding': '0 1rem', 'border-right': '1px solid #555'}),

                html.Div([
                    html.P("Retorno", style={'text-align': 'center', 'color': 'lightgray', 'margin-bottom': '0.2rem'}),
                    html.P(get_data_retorno_ultima_parada(), style={
                        'color': first_color,
                        'text-align': 'center',
                        'font-size': '1.4rem',
                        'font-weight': 'bold'
                    }),
                ], style={'flex': '1', 'padding': '0 1rem', 'border-right': '1px solid #555'}),

                html.Div([
                    html.P("Duração", style={'text-align': 'center', 'color': 'lightgray', 'margin-bottom': '0.2rem'}),
                    html.P(get_duracao_parada(), style={  
                        'color': first_color,
                        'text-align': 'center',
                        'font-size': '1.4rem',
                        'font-weight': 'bold'
                    }),
                ], style={'flex': '1'}),
            ], style={
                'display': 'flex',
                'justify-content': 'space-around',
                'align-items': 'center',
                'gap': '0.5rem'
            }),
        ], style={
            'background': '#343a40',
            'border-left': f'6px solid {first_color}',
            'border-radius': '1rem',
            'padding': '1.5rem',
            'margin': '1rem',
            'box-shadow': '0 0 10px rgba(0,0,0,0.3)',
            'flex': '1',
            'min-width': '400px'
        }),
        # Card total de paradas no ano
        html.Div([
            html.H3(id='paradas-title', style={
                'text-align': 'center',
                'margin-bottom': '1rem',
                'font-size': '1.5rem'
            }),
            html.P(id='paradas-total', style={
                'color': first_color,
                'text-align': 'center',
                'font-size': '3rem',
                'font-weight': 'bold',
                'margin': '0',
                'text-shadow': '2px 2px 10px rgba(0,0,0,0.6)',
                'transition': 'all 0.3s ease-in-out'
            }),
        ], style={
            'background': '#343a40',
            'border-left': f'6px solid {first_color}',
            'border-radius': '1rem',
            'padding': '1.5rem',
            'margin': '1rem',
            'box-shadow': '0 0 10px rgba(0,0,0,0.3)',
            'flex': '0 1 20%',
            'min-width': '280px'
        }),
    ], style={
        'display': 'flex',
        'flex-direction': 'row',
        'gap': '2rem',
        'justify-content': 'center',
        'width': '80vw',
        'color':'white',
        'flex-wrap': 'wrap',
    }),
    
    # Seleção do mês
    dbc.Col(
        dcc.Dropdown(
            id='month_dropdown_atividade',
            options=[
                {"label": month, "value": i+1} for i, month in enumerate(
                    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                )
            ],
            value=datetime.now().month,
            clearable=False,
            style={'width': '60%', 'margin': '0 auto'}
        ),
        width=2,
        style={'text-align': 'center', 'margin': '2rem 0 0 0'}
    ),

    # Gráfico de atividade - tempo em atividade X dias do mês
    dbc.Col([
        html.H3(
            "Atividade do Laboratório",
            className="h3-subtitle", 
            style={
                'color': third_color, 
                'text-align': 'center', 
                'background-color': first_color, 
                'font-size': '1rem', 
                'padding': '0.5rem', 
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0',
            }
        ),
        dbc.Card(
            dcc.Graph(
                id='uptime-line-chart',
                style={'height': '300px'}),
            className='shadow text-center',
            style={'background-color': third_color, 
                   'border': 'none', 
                   'margin-top': '0',
                   'width': '80vw',
                }
        )
    ], style={'margin': '1rem 3rem 0 3rem', }),

# Gráfico geral paradas anuais
    dbc.Col([
        html.H3(
            "Paradas Registradas no Ano",
            className="h3-subtitle", 
            style={
                'color': third_color, 
                'text-align': 'center', 
                'background-color': first_color, 
                'font-size': '1rem', 
                'padding': '0.5rem', 
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0',
            }
        ),
        dbc.Card(
            dcc.Graph(
                id='paradas-gerais-fig',
                style={'height': '300px'}
            ),
            className='shadow text-center',
            style={
                'background-color': third_color,
                'border': 'none',
                'margin-top': '0',
                'width': '80vw',
            }
        )
    ], style={'margin': '1rem 3rem 2rem 3rem'}),

    # Monitoramento de rede
    html.Div([
        html.Div([
            html.Div(id="monitoramento-status-card", style={
                "marginTop": "4rem",
                "color": "white",
                "fontSize": "1.1rem", 
                "fontWeight": "bold",
                "textAlign": "center",
                "minWidth": "220px",
            }),
        ], style={
            "display": "flex", 
            "justifyContent": "center",
            "alignItems": "center",
            "gap": "1rem", 
            "flexWrap": "wrap",
        }),

        # Gráfico
        html.H3(
            "Monitoramento de Rede",
            className="h3-subtitle", 
            style={
                'color': third_color, 
                'text-align': 'center', 
                'background-color': first_color, 
                'font-size': '1rem', 
                'padding': '0.5rem', 
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0',
            }
        ),
        # Seleção da data
        html.Div([
            html.Div([
                html.Button("←", id="dia-anterior", n_clicks=0, style={
                    "width": "2.5rem",
                    "height": "2.5rem",
                    "fontSize": "1.5rem",
                    "border": "none",
                    "color": "black",
                    "background": first_color,
                    "borderRadius": "0.5rem",
                    "cursor": "pointer",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                }),
                dcc.DatePickerSingle(
                    id='filtro-data-monitoramento',
                    date=datetime.now().date(),
                    display_format='DD/MM/YYYY',
                    style={
                        "width": "10rem",
                        "height": "2.5rem",
                        "borderRadius": "0.5rem",
                        "textAlign": "center"
                    }
                ),
                html.Button("→", id="dia-posterior", n_clicks=0, style={
                    "width": "2.5rem",
                    "height": "2.5rem",
                    "fontSize": "1.5rem",
                    "border": "none",
                    "color": "black",
                    "background": first_color,
                    "borderRadius": "0.5rem",
                    "cursor": "pointer",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                }),
                
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "width": "100%",
                "backgroundColor": third_color,
                "boxShadow": "0 4px 24px rgba(0,0,0,0.4)",
                "paddingTop": "0.5rem",
            }),

        ], style={
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "width": "100%",
            "color": "white",
        }),
        html.Div([
            html.Label("Modo de Visualização:", style={"color": "white", "marginRight": "10px"}),
            dcc.RadioItems(
                id="modo-visualizacao",
                options=[
                    {"label": "Média (intervalo de 5 min)", "value": "agrupado"},
                    {"label": "Dados Brutos", "value": "bruto"},
                ],
                value="agrupado",
                labelStyle={"display": "inline-block", "marginRight": "20px", "color": "white"},
                inputStyle={"marginRight": "5px"}
            )
        ], style={
            "backgroundColor": third_color,
            "width": "100%",
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "padding": "1rem 0 0 0"
        }),
        dcc.Graph(id="monitoramento-graph", style={"height": "400px"}),
        dcc.Interval(id="interval-monitoramento", interval=60*1000, n_intervals=0)
    ], style={"width": "80vw"})


], style={
    'box-sizing': 'border-box',
    'background-color': '#212529',
    'min-height': '100vh',
    'display': 'flex',
    'flex-direction': 'column',
    'align-items': 'center',
    'padding': '2rem',
})
