

#
# (c) Ricky Macharm, MScFE
# https://SisengAI.com
#


from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import dash
import dash_core_components as dcc
import dash_html_components as html

# Create the FastAPI application
app = FastAPI()

# Mount the Plotly Dash application as a sub-application
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dash')

# Define the layout of the Plotly Dash application
dash_app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),
    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization'
            }
        }
    )
])

# Serve the Plotly Dash application as an HTML response
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return dash_app.index()

# Serve static files (if any) from the "static" directory
app.mount("/static", StaticFiles(directory="static"), name="static")
