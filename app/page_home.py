from dash import dcc, html
import dash_bootstrap_components as dbc

from app.app import app

HOME_PAGE = [
    dbc.Col(
        class_name="col-xxl-auto px-4 py-5",
        children=[
            dbc.Row(
                class_name="flex-lg-row-reverse g-5 py-5",
                align="center",
                children=[
                    # Image
                    dbc.Col(
                        class_name="text-right",
                        width=10,
                        sm=8,
                        lg=6,
                        children=[
                            html.Img(
                                className="d-block mx-lg-auto img-fluid",
                                width=500,
                                height=500,
                                alt="Stock band class photo.",
                                src=app.get_asset_url("bandphoto.jpg"),
                            ),
                        ],
                    ),
                    # Text and Upload
                    dbc.Col(
                        lg=6,
                        align="center",
                        children=[
                            html.H1(
                                "BandClass",
                                className="fw-bold lh-1 mb-3",
                            ),
                            html.P(
                                children=[
                                    "This is a tool to help assign the ideal band class instrumentation using math.",
                                    html.Br(),
                                    "Using this tool, you can balance your own instrumentation preferences with the students' "
                                    "individual instrument preferences to create the ideal band.",
                                    html.Br(),
                                    html.Br(),
                                    "First, download the example ",
                                    html.A(
                                        ".csv files",
                                        id="exampletooltip",
                                        style={
                                            "textDecoration": "underline",
                                            "cursor": "pointer",
                                        },
                                    ),
                                    " to serve as examples of how to upload your own data.",
                                    html.Br(),
                                    "Then, fill in your own student preferences and instrumentation preferences, and upload the results to continue.",
                                    dbc.Tooltip(
                                        html.P(
                                            [
                                                "These .csv files will show the format that this app is expecting the data in.",
                                                html.Br(),
                                                html.Br(),
                                                "They can be opened and edited in Microsoft Excel or Google Sheets.",
                                            ]
                                        ),
                                        target="exampletooltip",
                                    ),
                                ],
                                className="lead",
                            ),
                            html.Div(
                                className="d-grid gap-3 d-md-flex flex-column justify-content-md-center",
                                children=[
                                    html.Div(
                                        className="d-grid gap-2 d-md-flex justify-content-md-center",
                                        children=[
                                            dcc.Upload(
                                                children=[
                                                    dbc.Button(
                                                        "Upload Instrumentation Preferences (.CSV)",
                                                        class_name="btn btn-success btn-md px-4 me-md-2",
                                                    )
                                                ],
                                                id="instrumentation-preferences-upload",
                                                max_size=9e7,
                                                accept="image/*",
                                            ),
                                            dbc.Button(
                                                "Download Example Instrumentation Preferences (.CSV)",
                                                class_name="btn btn-secondary btn-md px-4 me-md-2",
                                                id="instrumentation-preferences-download",
                                                # download="filename"
                                            ),
                                            html.Div(
                                                className="d-flex flex-columns align-self-center",
                                                children=[
                                                    dbc.Spinner(
                                                        dbc.Switch(
                                                            id="standalone-switch-success success",
                                                            value=False,
                                                            disabled=True,
                                                        ),
                                                    )
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="d-grid gap-2 d-md-flex justify-content-md-center",
                                        children=[
                                            dcc.Upload(
                                                children=[
                                                    dbc.Button(
                                                        "Upload Student Preferences (.CSV)",
                                                        class_name="btn btn-success btn-md px-4 me-md-2",
                                                    )
                                                ],
                                                id="student-preferences-upload",
                                                max_size=9e7,
                                                accept="image/*",
                                            ),
                                            dbc.Button(
                                                "Download Example Student Preferences (.CSV)",
                                                class_name="btn btn-secondary btn-md px-4 me-md-2",
                                                id="student-preferences-download",
                                                # download="filename"
                                            ),
                                            html.Div(
                                                className="d-flex flex-columns align-self-center",
                                                children=[
                                                    dbc.Spinner(
                                                        dbc.Switch(
                                                            id="standalone-switch",
                                                            value=False,
                                                            disabled=True,
                                                        ),
                                                    )
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    ),
]
