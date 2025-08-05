from dash import html, dcc
import dash_bootstrap_components as dbc
from config import *
import subprocess
from datetime import datetime, timedelta
import calendar
import re
import socket
import paramiko
import os

ssh_password = os.getenv("accounting_password")
if not ssh_password:
    raise EnvironmentError("Variável de ambiente accounting_password não encontrada.")

def is_production():
    return socket.gethostname() == "accounting"

# Função auxiliar para executar comandos
def execute_command(cmd):
    try:
        if is_production():
            output = subprocess.check_output(cmd, shell=True).decode()
        else:
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    "accounting", username="laduser", password=ssh_password, allow_agent=False, look_for_keys=False
                )
                stdin, stdout, _ = ssh.exec_command(cmd)
                output = stdout.read().decode()
        return output
    except Exception as e:
        print(f"Erro ao executar o comando '{cmd}': {e}")
        return None

# Coletar data do último reboot
def get_boot_time():
    output = execute_command("/usr/bin/uptime -s")
    if output:
        return datetime.strptime(output.strip(), "%Y-%m-%d %H:%M:%S")
    return None

# Coletar histórico de reboot
def get_reboot_history_raw():
    return execute_command("/usr/bin/last reboot -F")

# Pega o último uptime
def get_dias_ativos():
    boot_time = get_boot_time()
    if not boot_time:
        return "Erro ao obter o tempo de atividade"
    
    dias_ativos = (datetime.now() - boot_time).days
    return f"{dias_ativos}"

# Pega a data de retorno da última parada
def get_data_retorno_ultima_parada():
    boot_time = get_boot_time()
    if not boot_time:
        return "Erro ao obter"
    return boot_time.strftime("%d/%m/%Y - %H:%M")

def get_ultima_parada_datetime():
    output = get_reboot_history_raw()
    if not output:
        return None
        
    end_times = []
    for line in output.splitlines():
        if "system boot" in line:
            end_match = re.search(r'- (\w{3} \w{3}\s+\d+ \d{2}:\d{2}:\d{2} \d{4})', line)
            if end_match:
                try:
                    end_time = datetime.strptime(end_match.group(1), "%a %b %d %H:%M:%S %Y")
                    end_times.append(end_time)
                except ValueError:
                    continue 
    if end_times:
        return end_times[0]  
    return None

# Pega a data da última parada para exibição
def get_data_ultima_parada():
    parada_time = get_ultima_parada_datetime()
    if parada_time:
        return parada_time.strftime("%d/%m/%Y - %H:%M")
    return "Sem paradas registradas"

def get_duracao_parada():
    retorno_time = get_boot_time()
    parada_time = get_ultima_parada_datetime()
    if not retorno_time or not parada_time:
        return "N/A" 
    duracao = retorno_time - parada_time
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

# Coletar o histórico de reboot para o gráfico
def get_reboot_history(year, month):
    output = get_reboot_history_raw()
    if not output:
        return []

    reboot_ranges = []
    for line in output.splitlines():
        if "system boot" not in line:
            continue

        start_match = re.search(r'(\w{3} \w{3}\s+\d+ \d{2}:\d{2}:\d{2} \d{4})', line)
        end_match = re.search(r'- (\w{3} \w{3}\s+\d+ \d{2}:\d{2}:\d{2} \d{4})', line)

        if not start_match:
            continue

        try:
            start_time = datetime.strptime(start_match.group(1), "%a %b %d %H:%M:%S %Y")
            end_time = datetime.strptime(end_match.group(1), "%a %b %d %H:%M:%S %Y") if end_match else datetime.now()
        except ValueError:
            continue

        reboot_ranges.append((start_time, end_time))

    daily_uptime = {}
    for start, end in reboot_ranges:
        current_day = start.date()
        while current_day <= end.date():
            if current_day.year == year and current_day.month == month:
                daily_uptime.setdefault(current_day, 0.0)
                
                day_start_time = max(start, datetime.combine(current_day, datetime.min.time()))
                day_end_time = min(end, datetime.combine(current_day, datetime.max.time()))
                delta = (day_end_time - day_start_time).total_seconds() / 3600
                daily_uptime[current_day] += delta

            current_day += timedelta(days=1)

    today = datetime.now().date()
    last_day = calendar.monthrange(year, month)[1]
    result = []
    for d in range(1, last_day + 1):
        dt = datetime(year, month, d).date()
        if dt > today:
            break
        if dt == today:
            continue
        uptime_hours = daily_uptime.get(dt, 0.0)
        result.append({
            "day": d,
            "uptime_hours": min(round(uptime_hours, 1), 24.0)
        })

    return result

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
            'flex': '0 1 35%',
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
        })
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
