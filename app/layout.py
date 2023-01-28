from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from app.app import app
from app.page_home import HOME_PAGE


# TEMP
DATA_ENTRY_PAGE = "entry"
DATA_CONFIRM_PAGE = "confirm"
RESULTS_PAGE = "results"

# APP LAYOUT
layout = html.Div(
    children=[
        dcc.Location(id="url", refresh=False),
        dbc.Container(
            fluid=True,
            style={"min-height": "100vh", "height": "100vh"},
            id="page-content",
        ),
        html.Footer(
            className="footer",
            children=[
                dbc.Container(
                    children=dbc.Row(
                        className="text-center text-light bg-success fixed-bottom pt-2",
                        children=[
                            html.P(
                                [
                                    "Created By Gavin Grochowski  |  ",
                                    html.A(
                                        "Source Code",
                                        href="https://github.com/gavingro/bandclass",
                                        className="text-white",
                                        target="_blank",
                                    )
                                ]
                            ),
                        ],
                    ),
                )
            ],
        )
    ],
)

# PAGE INDEX
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return HOME_PAGE
    elif pathname == "/entry":
        return DATA_ENTRY_PAGE
    elif pathname == "/confirm":
        return DATA_CONFIRM_PAGE
    elif pathname == "/results":
        return RESULTS_PAGE
    else:
        return "404"
