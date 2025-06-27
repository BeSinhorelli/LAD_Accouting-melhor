from dash import html
from config import first_color

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
                "Aqui você pode acompanhar informações sobre demandas, uso de máquinas, capacidades de armazenamento e produções científicas, "
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
            "backgroundColor": "#2c3034",
            "width": "90%",
            "maxWidth": "1000px"
        })
    ]
)
