from dash import html, dcc
from config import fifth_color, second_color, first_color
import subprocess
from datetime import datetime

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

layout_atividade = html.Div([

    html.H2("Painel de Atividade", style={
        'color': fifth_color,
        'text-align': 'center',
    }),
    html.Div([
        html.Div([
            html.H3("Dias em atividade contínua", style={
            'text-align': 'center',
            'margin': '0'
            }),
        
            #Contador de dias em atividade
            html.P(get_dias_ativos(), style={
                'color': first_color,
                'text-align': 'center',
                'font-size': '4rem',
                'margin-top': '1rem',
            }),  
        ], style={
            'padding': '1rem', 
            'margin': '3rem'
            }),
        html.Div([
            html.H3("Data da última parada:", style={
            'text-align': 'center',
            'margin': '0'
            }),
            html.P(f"{get_data_ultima_parada()}", style = {'color': first_color,
                'text-align': 'center',
                'font-size': '2rem',
                'margin-top': '1rem'
            }),
        ], style={
            'padding': '1rem', 
            'margin': '3rem'
            }),
    ], style={'background-color': '#2c3034', 'padding': '1rem', 'borderRadius': '12px',  'margin': '0 auto'}),
], style={"boxSizing": "border-box",
        "backgroundColor": "#212529",
        "color": "#f8f9fa",
        "height": "100vh",
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "center",
        "justifyContent": "top",
        "textAlign": "center",
        "padding": "2rem",
        "marginTop": "2rem"
        })