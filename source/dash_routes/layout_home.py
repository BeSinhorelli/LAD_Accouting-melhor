from dash import html
from config import *
from models import Producao
from peewee import fn

card_style = {
    "backgroundColor": "#343a40",
    "padding": "1.5rem",
    "borderRadius": "1rem",
    "width": "300px",
    "color": "#fff",
    "boxShadow": "0 0 10px rgba(0,0,0,0.3)",
    "textAlign": "center"
}
# Card Produções
def get_producoes():
    query = Producao.select(
        fn.SUM(Producao.cientifica).alias("total_cientifica"),
        fn.SUM(Producao.tcc).alias("total_tcc")
    ).dicts().get()

    total = (query["total_cientifica"] or 0) + (query["total_tcc"] or 0)
    return total

# Card Horas Usadas
def read_annual_report(yearValue):
    #Lê todos os arquivos Excel do ano e concatena em um DataFrame anual.
        relatorio_dir = f'relatorios/{yearValue}'
        if not os.path.exists(relatorio_dir):
            return pd.DataFrame()
        df_annual = pd.DataFrame()
        for file in os.listdir(relatorio_dir):
            if file.endswith('.xlsx'):
                df = pd.read_excel(os.path.join(relatorio_dir, file))
                df_annual = pd.concat([df_annual, df], ignore_index=True)
        return df_annual

layout_home = html.Div(
    style={
        "boxSizing": "border-box",
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
    },
    children=[
        html.Div([
            html.H1("Bem-vindo ao LAD Dashboard", style={
                "marginBottom": "2rem",
                "fontSize": "2.5rem",
                "fontWeight": "700",
                "color": first_color,
                "textShadow": "1px 1px 2px #000"
            }),
            html.P(
                "Este é o painel de controle do Laboratório de Alto Desempenho da PUCRS.",
                style={
                    "maxWidth": "800px",
                    "fontSize": "1.2rem",
                    "lineHeight": "1.6",
                    "color": "#ced4da",
                    "margin": "0 auto",
                    "marginBottom":'1rem',
                }
            ),

            html.P(
                "Aqui você pode acompanhar a atividade do laboratório, informações sobre demandas, uso de máquinas, capacidades de armazenamento e produções científicas, "
                "permitindo uma gestão mais eficiente dos recursos do laboratório.",
                style={
                    "maxWidth": "800px",
                    "fontSize": "1.2rem",
                    "lineHeight": "1.6",
                    "color": "#ced4da",
                    "margin": "0 auto",
                }
            ),
        ],
        style={
            "padding": "2rem",
            "borderRadius": "12px",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.4)",
            "backgroundColor": "#343a40",
            "width": "90%",
            "maxWidth": "1000px"
        }),
        # Gráficos em callbaks.py, linha 346
        html.Div(id="summary_cards", style={"width": "90%"})
    ]
)
