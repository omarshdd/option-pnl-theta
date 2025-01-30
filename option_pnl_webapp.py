import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import numpy as np
import os
import datetime

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server  # Ensure Gunicorn can recognize the Flask server

# Layout with modern UI
app.layout = dbc.Container([
    html.H1("Option P&L Visualizer with Theta Decay", className="text-center mt-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label("Ticker Symbol:"),
                    dcc.Input(id='ticker-symbol', type='text', value='AAPL', className="form-control"),
                    
                    html.Label("Underlying Price at Purchase:"),
                    dcc.Input(id='underlying-price', type='number', value=100, className="form-control"),
                    
                    html.Label("Option Premium:"),
                    dcc.Input(id='option-premium', type='number', value=5, className="form-control"),
                    
                    html.Label("Delta at Purchase:"),
                    dcc.Input(id='delta-purchase', type='number', value=0.5, className="form-control"),
                    
                    html.Label("Theta at Purchase (per day):"),
                    dcc.Input(id='theta-purchase', type='number', value=0.02, className="form-control"),
                    
                    html.Label("Date Purchased:"),
                    dcc.DatePickerSingle(id='date-purchased', date=str(datetime.date.today() - datetime.timedelta(days=10))),
                    
                    html.Label("Current Date:"),
                    dcc.DatePickerSingle(id='current-date', date=str(datetime.date.today())),
                    
                    html.Label("Expiry Date:"),
                    dcc.DatePickerSingle(id='expiry-date', date=str(datetime.date.today() + datetime.timedelta(days=30))),
                    
                    html.Label("Adjust Hypothetical Price (% Change):"),
                    dcc.Slider(id='hypothetical-slider', min=-20, max=20, step=1, value=0, 
                               marks={i: f"{i}%" for i in range(-20, 21, 5)}),
                ])
            ], className="shadow-lg p-3 mb-5 bg-white rounded")
        ], width=4),
        
        dbc.Col([
            dcc.Graph(id='pnl-graph')
        ], width=8)
    ], align="center")
], fluid=True)

# Callback to update P&L graph
@app.callback(
    Output('pnl-graph', 'figure'),
    [Input('underlying-price', 'value'),
     Input('option-premium', 'value'),
     Input('delta-purchase', 'value'),
     Input('theta-purchase', 'value'),
     Input('date-purchased', 'date'),
     Input('current-date', 'date'),
     Input('expiry-date', 'date'),
     Input('hypothetical-slider', 'value')]
)
def update_graph(underlying, premium, delta, theta, date_purchased, current_date, expiry_date, hypo_change):
    if not date_purchased or not current_date or not expiry_date:
        return go.Figure()
    
    days_to_expiry = (datetime.date.fromisoformat(expiry_date) - datetime.date.fromisoformat(current_date)).days
    hypothetical_price = underlying * (1 + hypo_change / 100)
    estimated_pnl = (hypothetical_price - underlying) * delta * 100 - premium * 100 - (theta * days_to_expiry * 100)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[hypothetical_price], y=[estimated_pnl], mode='markers',
                             marker=dict(size=10, color='red'), name='Current Estimate'))
    
    price_range = np.linspace(underlying * 0.8, underlying * 1.2, 50)
    pnl_range = (price_range - underlying) * delta * 100 - premium * 100 - (theta * days_to_expiry * 100)
    fig.add_trace(go.Scatter(x=price_range, y=pnl_range, mode='lines', name='Estimated P&L'))
    
    fig.update_layout(title="P&L vs. Hypothetical Stock Price with Theta Decay",
                      xaxis_title="Stock Price",
                      yaxis_title="Estimated P&L",
                      template="plotly_dark")
    return fig

# Run the app with proper port binding for Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))  # Render assigns a port dynamically
    app.run_server(host='0.0.0.0', port=port, debug=False)
