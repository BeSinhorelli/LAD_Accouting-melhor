from dash import html
from config import *
from models import Producao
from peewee import fn

card_style = {
    "backgroundColor": "#343a40",
    "padding": "1.5rem",
    "borderRadius": "1rem",
    "minWidth": "250px",
    "maxWidth": "280px",
    "color": "#f8f9fa",
    "boxShadow": "0 6px 15px rgba(0,0,0,0.5)",
    "textAlign": "center",
    "transition": "transform 0.3s ease-in-out",
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
                "Este painel reúne os principais indicadores do LAD: atividade do laboratório, análise e desempenho das demandas, uso de máquinas, armazenamento e produções.",
                style={
                    "maxWidth": "800px",
                    "fontSize": "1.2rem",
                    "lineHeight": "1.6",
                    "color": "#ced4da",
                    "margin": "0 auto",
                    "marginBottom":'1rem',
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
        html.Div(id="summary_cards", style={"display": "flex", 
                                            "flexWrap": "wrap", 
                                            "justifyContent": "center", 
                                            "gap": "1.5rem", 
                                            "marginTop": "2rem"})
    ]
)
