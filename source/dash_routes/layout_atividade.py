from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime, date
import calendar
from peewee import fn
import pandas as pd
import os
import glob

from models import Atividade, RebootHistory, database
from config import *

# ============================================================================
# FUNÇÕES PARA LER DADOS DOS EXCEL (ATIVIDADE)
# ============================================================================

def get_all_excel_files():
    """Retorna todos os arquivos Excel de relatórios"""
    excel_files = []
    base_path = os.path.join(os.path.dirname(__file__), '..', 'relatorios')
    
    if not os.path.exists(base_path):
        print(f"⚠️ Diretório não encontrado: {base_path}")
        return []
    
    for year_dir in sorted(os.listdir(base_path)):
        year_path = os.path.join(base_path, year_dir)
        if os.path.isdir(year_path) and year_dir.isdigit():
            for excel_file in sorted(glob.glob(os.path.join(year_path, '*.xlsx'))):
                nome_arquivo = os.path.basename(excel_file)
                try:
                    mes = int(nome_arquivo.split('-')[0])
                except:
                    mes = 1
                excel_files.append({
                    'path': excel_file,
                    'year': int(year_dir),
                    'file': nome_arquivo,
                    'month': mes
                })
    
    return sorted(excel_files, key=lambda x: (x['year'], x['month']))

def read_excel_file(file_path):
    """Lê um arquivo Excel e retorna os dados"""
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"Erro ao ler {file_path}: {e}")
        return None

def calculate_activity_from_excel(year, month):
    """
    Calcula a atividade percentual do laboratório baseado no uso das máquinas.
    Retorna um valor percentual (0-100) de atividade para o mês.
    """
    month_names = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    month_name = month_names[month - 1]
    base_path = os.path.join(os.path.dirname(__file__), '..', 'relatorios')
    file_path = os.path.join(base_path, str(year), f'{month}-{month_name}.xlsx')
    
    if not os.path.exists(file_path):
        print(f"⚠️ Arquivo não encontrado: {file_path}")
        return 0
    
    try:
        df = pd.read_excel(file_path)
        
        # Procura colunas de uso de máquina
        machine_cols = []
        for col in df.columns:
            col_lower = col.lower()
            if 'horas núcleo' in col_lower or 'máquina em cluster' in col_lower or 'maquina_cluster' in col_lower:
                machine_cols.append(col)
            elif 'horas núcleo 24x7' in col_lower or 'máquina em 24x7' in col_lower or 'maquina_24x7' in col_lower:
                machine_cols.append(col)
        
        if not machine_cols:
            return 0
        
        # Calcula uso total de máquinas no mês
        uso_total = 0
        for col in machine_cols:
            try:
                valores = pd.to_numeric(df[col], errors='coerce').fillna(0)
                uso_total += valores.sum()
            except Exception as e:
                print(f"Erro na coluna {col}: {e}")
        
        # Capacidade máxima mensal (2108 núcleos * 24h * dias do mês)
        days_in_month = calendar.monthrange(year, month)[1]
        capacidade_maxima = 2108 * 24 * days_in_month
        
        if capacidade_maxima > 0:
            atividade_percent = (uso_total / capacidade_maxima) * 100
        else:
            atividade_percent = 0
        
        atividade_percent = min(100, atividade_percent)
        
        return atividade_percent
        
    except Exception as e:
        print(f"❌ Erro ao calcular atividade para {year}/{month}: {e}")
        return 0

def get_activity_data_for_year(year):
    """Retorna dados de atividade para todos os meses de um ano"""
    activity_data = []
    for month in range(1, 13):
        atividade = calculate_activity_from_excel(year, month)
        activity_data.append({
            'month': month,
            'month_name': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][month-1],
            'activity_percent': atividade,
            'activity_hours': (atividade / 100) * 24
        })
    return activity_data

def get_available_years():
    """Retorna lista de anos disponíveis nos Excel"""
    excel_files = get_all_excel_files()
    years = sorted(set(f['year'] for f in excel_files))
    return years if years else [ano_atual]

def get_reboot_history(year, month):
    """
    Retorna dados de uptime diário para o mês/ano especificado.
    Compatível com os callbacks existentes.
    """
    atividade_percent = calculate_activity_from_excel(year, month)
    horas_por_dia = (atividade_percent / 100) * 24
    
    last_day = calendar.monthrange(year, month)[1]
    result = []
    for day in range(1, last_day + 1):
        result.append({
            "day": day,
            "uptime_hours": round(horas_por_dia, 1)
        })
    return result

# ============================================================================
# FUNÇÕES DO BANCO DE DADOS (PARA PARADAS E OUTROS)
# ============================================================================

def conectar_banco():
    if database.is_closed():
        database.connect()

def get_dias_ativos():
    """Calcula dias desde o primeiro relatório Excel"""
    excel_files = get_all_excel_files()
    if not excel_files:
        return "0"
    primeiro = min(excel_files, key=lambda x: (x['year'], x['month']))
    primeira_data = date(primeiro['year'], primeiro['month'], 1)
    dias = (datetime.now().date() - primeira_data).days
    return f"{max(0, dias)}"

def get_data_ultima_parada():
    conectar_banco()
    try:
        ultima_parada = RebootHistory.select().order_by(RebootHistory.data_fim.desc()).get()
        return ultima_parada.data_fim.strftime("%d/%m/%Y - %H:%M")
    except RebootHistory.DoesNotExist:
        return "Sem paradas registradas"
    except Exception as e:
        print(f"Erro ao obter data da última parada: {e}")
        return "Erro"

def get_data_retorno_ultima_parada():
    conectar_banco()
    try:
        ultima_atividade = Atividade.select().order_by(Atividade.id.desc()).get()
        boot_time_str = ultima_atividade.uptime
        boot_time = datetime.strptime(boot_time_str, "%Y-%m-%d %H:%M:%S")
        return boot_time.strftime("%d/%m/%Y - %H:%M")
    except Atividade.DoesNotExist:
        return "Sem dados de retorno"
    except Exception as e:
        print(f"Erro ao obter data de retorno: {e}")
        return "Erro"

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

def get_total_paradas(selected_year):
    if selected_year is None:
        return 0
    
    conectar_banco()
    try:
        year = int(selected_year)
    except (ValueError, TypeError):
        return 0
    
    try:
        reboots = RebootHistory.select().where(
            fn.strftime('%Y', RebootHistory.data_inicio) == str(year)
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
    except Exception as e:
        print(f"Erro ao calcular total de paradas: {e}")
        return 0

def get_paradas_ano(selected_year):
    if selected_year is None:
        return []
    
    conectar_banco()
    try:
        year = int(selected_year)
    except (ValueError, TypeError):
        return []
    
    try:
        reboots_list = list(RebootHistory.select().where(
            fn.strftime('%Y', RebootHistory.data_inicio) == str(year)
        ).order_by(RebootHistory.data_inicio))
        
        paradas = []
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
    except Exception as e:
        print(f"Erro ao obter paradas do ano: {e}")
        return []

# ============================================================================
# LAYOUT
# ============================================================================

layout_atividade = html.Div([
    # Título
    html.H2("📊 Painel de Atividade", style={
        'color': first_color,
        'text-align': 'center',
        'margin-bottom': '2rem',
        'font-weight': 'bold'
    }),
    
    # Cards de métricas
    html.Div([
        html.Div([
            html.H3("📅 Dias em Atividade", style={'text-align': 'center', 'color': '#ccc', 'font-size': '1.2rem'}),
            html.P(id='dias-ativos-display', children=get_dias_ativos(), style={
                'color': first_color, 'text-align': 'center', 'font-size': '3rem', 'font-weight': 'bold'
            }),
            html.Small("Desde o primeiro relatório", style={'color': '#888'})
        ], style={'background': '#343a40', 'border-radius': '1rem', 'padding': '1rem', 'margin': '0.5rem', 'flex': '1'}),
        
        html.Div([
            html.H3("🕐 Última Ocorrência", style={'text-align': 'center', 'color': '#ccc', 'font-size': '1.2rem'}),
            html.Div([
                html.Div([html.P("⏹️ Parada", style={'color': '#ff6b6b'}), html.P(id='ultima-parada', style={'color': first_color})], style={'flex': '1'}),
                html.Div([html.P("▶️ Retorno", style={'color': '#51cf66'}), html.P(id='ultimo-retorno', style={'color': first_color})], style={'flex': '1'}),
                html.Div([html.P("⏱️ Duração", style={'color': '#ffd43b'}), html.P(id='duracao-parada', style={'color': first_color})], style={'flex': '1'}),
            ], style={'display': 'flex', 'margin-top': '1rem'}),
        ], style={'background': '#343a40', 'border-radius': '1rem', 'padding': '1rem', 'margin': '0.5rem', 'flex': '2'}),
        
        html.Div([
            html.H3(id='paradas-title', children="Paradas no Ano", style={'text-align': 'center', 'color': '#ccc', 'font-size': '1.2rem'}),
            html.P(id='paradas-total', children="0", style={'color': first_color, 'text-align': 'center', 'font-size': '3rem', 'font-weight': 'bold'}),
        ], style={'background': '#343a40', 'border-radius': '1rem', 'padding': '1rem', 'margin': '0.5rem', 'flex': '1'}),
    ], style={'display': 'flex', 'flex-wrap': 'wrap', 'width': '90%', 'margin-bottom': '2rem'}),
    
    # Gráfico de Atividade Mensal (Barras)
    html.Div([
        html.H3(
            "📈 Atividade Mensal do Laboratório",
            style={
                'color': third_color, 
                'text-align': 'center', 
                'background-color': first_color, 
                'font-size': '1.2rem', 
                'padding': '0.75rem', 
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0',
                'font-weight': 'bold'
            }
        ),
        dbc.Card(
            dcc.Graph(
                id='yearly-activity-chart',
                config={'displayModeBar': True, 'responsive': True},
                style={'height': '450px'}
            ),
            className='shadow',
            style={'background-color': third_color, 'border': 'none', 'margin-top': '0', 'width': '100%'}
        )
    ], style={'margin': '1rem 0', 'width': '90%'}),
    
    # Gráfico de Linha da Atividade
    html.Div([
        html.H3(
            "📊 Evolução Mensal da Atividade",
            style={
                'color': third_color, 
                'text-align': 'center', 
                'background-color': first_color, 
                'font-size': '1.2rem', 
                'padding': '0.75rem', 
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0',
                'font-weight': 'bold'
            }
        ),
        dbc.Card(
            dcc.Graph(
                id='activity-line-chart',
                config={'displayModeBar': True, 'responsive': True},
                style={'height': '400px'}
            ),
            className='shadow',
            style={'background-color': third_color, 'border': 'none', 'margin-top': '0', 'width': '100%'}
        )
    ], style={'margin': '2rem 0', 'width': '90%'}),
    
    # Gráfico Diário de Atividade (Uptime)
    html.Div([
        html.H3(
            "📊 Atividade Diária do Laboratório",
            style={
                'color': third_color, 
                'text-align': 'center', 
                'background-color': first_color, 
                'font-size': '1.2rem', 
                'padding': '0.75rem', 
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0',
                'font-weight': 'bold'
            }
        ),
        dbc.Card(
            dcc.Graph(
                id='uptime-line-chart',
                config={'displayModeBar': True, 'responsive': True},
                style={'height': '400px'}
            ),
            className='shadow',
            style={'background-color': third_color, 'border': 'none', 'margin-top': '0', 'width': '100%'}
        )
    ], style={'margin': '2rem 0', 'width': '90%'}),
    
    # Gráfico de Paradas Anuais
    html.Div([
        html.H3(
            "📉 Paradas Registradas no Ano",
            style={
                'color': third_color, 
                'text-align': 'center', 
                'background-color': first_color, 
                'font-size': '1.2rem', 
                'padding': '0.75rem', 
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0',
                'font-weight': 'bold'
            }
        ),
        dbc.Card(
            dcc.Graph(
                id='paradas-gerais-fig',
                config={'displayModeBar': True, 'responsive': True},
                style={'height': '400px'}
            ),
            className='shadow',
            style={'background-color': third_color, 'border': 'none', 'margin-top': '0', 'width': '100%'}
        )
    ], style={'margin': '2rem 0', 'width': '90%'}),
    
    # Seleção do mês para o gráfico diário
    html.Div([
        html.Label("📅 Selecione o Mês para Visualização Diária:", style={'color': 'white', 'margin-right': '1rem', 'font-weight': 'bold'}),
        dcc.Dropdown(
            id='month_dropdown_atividade',
            options=[
                {"label": "Janeiro", "value": 1},
                {"label": "Fevereiro", "value": 2},
                {"label": "Março", "value": 3},
                {"label": "Abril", "value": 4},
                {"label": "Maio", "value": 5},
                {"label": "Junho", "value": 6},
                {"label": "Julho", "value": 7},
                {"label": "Agosto", "value": 8},
                {"label": "Setembro", "value": 9},
                {"label": "Outubro", "value": 10},
                {"label": "Novembro", "value": 11},
                {"label": "Dezembro", "value": 12}
            ],
            value=datetime.now().month,
            clearable=False,
            style={'width': '250px', 'backgroundColor': '#343a40', 'color': 'white'}
        ),
    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'margin': '2rem 0', 'flex-wrap': 'wrap', 'gap': '1rem'}),
    
    # Monitoramento de Rede
    html.Div([
        html.H3(
            "🌐 Monitoramento de Rede",
            style={
                'color': third_color, 
                'text-align': 'center', 
                'background-color': first_color, 
                'font-size': '1.2rem', 
                'padding': '0.75rem', 
                'border-radius': '0.5rem 0.5rem 0 0',
                'margin-bottom': '0',
                'font-weight': 'bold'
            }
        ),
        
        html.Div(id="monitoramento-status-card", style={
            "marginTop": "1rem",
            "color": "white",
            "fontSize": "1.1rem", 
            "fontWeight": "bold",
            "textAlign": "center",
        }),
        
        html.Div([
            html.Button("◀", id="dia-anterior", n_clicks=0, style={
                "width": "2.5rem",
                "height": "2.5rem",
                "fontSize": "1.2rem",
                "border": "none",
                "color": "black",
                "background": first_color,
                "borderRadius": "0.5rem",
                "cursor": "pointer",
                "fontWeight": "bold"
            }),
            dcc.DatePickerSingle(
                id='filtro-data-monitoramento',
                date=datetime.now().date(),
                display_format='DD/MM/YYYY',
                style={
                    "width": "12rem",
                    "height": "2.5rem",
                    "borderRadius": "0.5rem",
                    "textAlign": "center",
                    "margin": "0 1rem"
                }
            ),
            html.Button("▶", id="dia-posterior", n_clicks=0, style={
                "width": "2.5rem",
                "height": "2.5rem",
                "fontSize": "1.2rem",
                "border": "none",
                "color": "black",
                "background": first_color,
                "borderRadius": "0.5rem",
                "cursor": "pointer",
                "fontWeight": "bold"
            }),
        ], style={
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "margin": "1rem 0",
            "flexWrap": "wrap"
        }),
        
        html.Div([
            html.Label("📊 Modo de Visualização:", style={"color": "white", "marginRight": "1rem"}),
            dcc.RadioItems(
                id="modo-visualizacao",
                options=[
                    {"label": " Média (5 min)", "value": "agrupado"},
                    {"label": " Dados Brutos", "value": "bruto"},
                ],
                value="agrupado",
                labelStyle={"display": "inline-block", "marginRight": "1.5rem", "color": "white"},
                inputStyle={"marginRight": "0.5rem"}
            )
        ], style={
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "margin": "1rem 0",
            "flexWrap": "wrap"
        }),
        
        dcc.Graph(id="monitoramento-graph", style={"height": "450px"}),
        dcc.Interval(id="interval-monitoramento", interval=60*1000, n_intervals=0)
        
    ], style={"width": "90%", "margin": "1rem 0"})

], style={
    'box-sizing': 'border-box',
    'background-color': '#212529',
    'min-height': '100vh',
    'display': 'flex',
    'flex-direction': 'column',
    'align-items': 'center',
    'padding': '2rem',
})