from dash import html

layout_home = html.Div(
    style={
        "background-color": "#212529",
        "color": "white",
        "min-height": "100vh",
        "display": "flex",
        "flex-direction": "column",
        "align-items": "center",
        "justify-content": "center",
        "text-align": "center",
        
    },
    children=[
        html.H1("Bem-vindo ao LAD Dashboard", style={"margin-bottom": "2rem"}),
        html.P(
            "Este é o painel de controle do Laboratório de Análise de Dados da PUCRS. "
            "Aqui você pode visualizar informações sobre demandas, uso de máquinas e produções científicas.",
            style={"margin-bottom": "2rem"}
        ),
    ]
)
