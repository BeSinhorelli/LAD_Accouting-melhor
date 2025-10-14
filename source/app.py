# -------------------------------------  IMPORT DE BIBLIOTECAS  ---------------------------------------- #
# --- FLASK --- #

from peewee import *

# --- DASH --- #

from dash import dash
import dash_bootstrap_components as dbc
import plotly.io as pio

from config import *
from models import *
from routes import *

from dash_routes.callbacks import register_callbacks
from dash_routes.layout_app import create_layout 

# -------------------------------------  CONFIGURAÇÕES INICIAIS  ---------------------------------------- #
# --- DASH --- #
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    server=server,
    assets_folder='assets/images',
    url_base_pathname='/dash/'
    )

pio.templates.default = "plotly_dark"
app.title = "LAD Dashboard"

# -------------------------------------  CALLBACKS DA APLICAÇÃO ----------------------------------------- #
register_callbacks(app)

# -------------------------------------  LAYOUT DA APLICAÇÃO  ----------------------------------------- #
app.layout = create_layout(app)

# ------------------------------------  INICIA A APLICAÇÃO --------------------------------------------- #

if __name__ == '__main__':
    create_tables()
    server.run(debug=True)