from dash import html, dcc
import dash_bootstrap_components as dbc
from config import fifth_color, second_color, first_color, third_color
import subprocess
from datetime import datetime, timedelta
import calendar
import re

# substituir esse trecho por def get_boot_time(): quando estiver em produção
import paramiko
def get_remote_boot_time():
    try:
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                "accounting",
                username="laduser",
                password="vg5snLeF924uGkZsxP8FDSYEQX2zLDDqx7",
                allow_agent=False,
                look_for_keys=False
            )

            stdin, stdout, _ = ssh.exec_command("uptime -s")
            boot_time_str = stdout.read().decode().strip()
            return datetime.strptime(boot_time_str, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Erro ao conectar via SSH: {e}")
        return None
    ##########
'''
def get_boot_time():
    result = subprocess.run(["uptime", "-s"], capture_output=True, text=True)
    if result.returncode == 0:
        boot_time_str = result.stdout.strip()
        return datetime.strptime(boot_time_str, "%Y-%m-%d %H:%M:%S")
    else:
        return None
'''
def get_dias_ativos():
    boot_time = get_remote_boot_time()
    if not boot_time:
        return "Erro ao obter o tempo de atividade"
    
    dias_ativos = (datetime.now() - boot_time).days
    return f"{dias_ativos}"

def get_data_ultima_parada():
    boot_time = get_remote_boot_time()
    if not boot_time:
        return "Erro ao obter"
    return boot_time.strftime("%d/%m/%Y")

def get_remote_reboot_history(year, month):
    try:
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                "accounting",
                username="laduser",
                password="vg5snLeF924uGkZsxP8FDSYEQX2zLDDqx7",
                allow_agent=False,
                look_for_keys=False
            )
            stdin, stdout, _ = ssh.exec_command("last reboot -F")
            output = stdout.read().decode()
    except Exception as e:
        print(f"Erro ao obter histórico de reboot: {e}")
        return []

    reboot_ranges = []

    for line in output.splitlines():
        if "system boot" not in line:
            continue

        # Match início
        start_match = re.search(r'(\w{3} \w{3}\s+\d+ \d{2}:\d{2}:\d{2} \d{4})', line)
        if not start_match:
            continue

        start_str = start_match.group(1)
        try:
            start_time = datetime.strptime(start_str, "%a %b %d %H:%M:%S %Y")
        except ValueError:
            continue

        # Verifica se tem fim
        end_match = re.search(r'- (\w{3} \w{3}\s+\d+ \d{2}:\d{2}:\d{2} \d{4})', line)
        if end_match:
            end_str = end_match.group(1)
            try:
                end_time = datetime.strptime(end_str, "%a %b %d %H:%M:%S %Y")
            except ValueError:
                continue
        else:
            end_time = datetime.now()

        reboot_ranges.append((start_time, end_time))

    # Uptime diário
    daily_uptime = {}
    for start, end in reboot_ranges:
        current_day = start.date()
        while current_day <= end.date():
            if current_day.year == year and current_day.month == month:
                if current_day not in daily_uptime:
                    daily_uptime[current_day] = 0.0

                day_start_time = max(start, datetime.combine(current_day, datetime.min.time()))
                day_end_time = min(end, datetime.combine(current_day, datetime.max.time()))

                # Calculate uptime for the current day
                delta = (day_end_time - day_start_time).total_seconds() / 3600
                daily_uptime[current_day] += delta

            current_day += timedelta(days=1)

    # Preencher os dias até ATUAL
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

layout_atividade = html.Div([

    html.H2("Painel de Atividade", style={
        'color': fifth_color,
        'text-align': 'center',
    }),
    html.Div([
        html.Div([
            html.H3("Dias em atividade contínua", style={
                'text-align': 'center',
                'margin-bottom': '0.5rem',
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
            'padding': '1rem',
            'margin': '1rem',
            'box-shadow': '0 0 10px rgba(0,0,0,0.3)',
            'flex': '1'
        }),

        html.Div([
            html.H3("Data da última parada:", style={
                'text-align': 'center',
                'margin-bottom': '0.5rem',
                'font-size': '1.5rem'
            }),
            html.P(f"{get_data_ultima_parada()}", style={
                'color': first_color,
                'text-align': 'center',
                'font-size': '1.5rem',
                'margin': '0'
            }),
        ], style={
            'background': '#343a40',
            'border-left': f'6px solid {first_color}',
            'border-radius': '1rem',
            'padding': '1rem',
            'margin': '1rem',
            'box-shadow': '0 0 10px rgba(0,0,0,0.3)',
            'flex': '1'
        }),
    ], style={
        'display': 'flex',
        'flex-direction': 'row',
        'gap': '2rem',
        'justify-content': 'center',
        'width': '100%',
        'max-width': '900px',
        'color':'white'
    }),
    
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

], style={
    'box-sizing': 'border-box',
    'background-color': '#212529',
    'min-height': '100vh',
    'display': 'flex',
    'flex-direction': 'column',
    'align-items': 'center',
    'padding': '2rem',
})