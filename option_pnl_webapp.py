import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import numpy as np
import os
import datetime
import yfinance as yf

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server  # Ensure Gunicorn can recognize the Flask server

# Layout with improved UX
app.layout = dbc.Container([
    html.H1("Option P&L Visualizer", className="text-center mt-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Stock & Option Details"),
                    html.Label("Ticker Symbol:"),
                    dcc.Input(id='ticker-symbol', type='text', value='AAPL', className="form-control"),
                    
                    html.Label("Underlying Price at Purchase:"),
                    dcc.Input(id='underlying-price', type='number', value=100, className="form-control"),
                    
                    html.Label("Option Type:"),
                    dcc.RadioItems(id='option-type', options=[
                        {'label': 'Call', 'value': 'call'},
                        {'label': 'Put', 'value': 'put'}
                    ], value='call', inline=True),
                    
                    html.Label("Option Premium:"),
                    dcc.Input(id='option-premium', type='number', value=5, className="form-control"),
                    
                    html.Label("Contract Size:"),
                    dcc.Input(id='contract-size', type='number', value=100, className="form-control"),
                ])
            ], className="shadow-lg p-3 mb-4 bg-white rounded"),

            dbc.Card([
                dbc.CardBody([
                    html.H5("Greeks & Expiry"),
                    html.Label("Delta at Purchase:"),
                    dcc.Slider(id='delta-purchase', min=-1, max=1, step=0.01, value=0.5, 
                               marks={-1: "-1", 0: "0", 1: "1"}),
                    
                    html.Label("Theta at Purchase (per day):"),
                    dcc.Slider(id='theta-purchase', min=-1, max=0, step=0.01, value=-0.02, 
                               marks={-1: "-1", 0: "0"}),
                    
                    html.Label("Date Purchased:"),
                    dcc.DatePickerSingle(id='date-purchased', date=str(datetime.date.today() - datetime.timedelta(days=10))),
                    
                    html.Label("Current Date:"),
                    dcc.DatePickerSingle(id='current-date', date=str(datetime.date.today())),
                    
                    html.Label("Expiry Date:"),
                    dcc.DatePickerSingle(id='expiry-date', date=str(datetime.date.today() + datetime.timedelta(days=30))),
                ])
            ], className="shadow-lg p-3 mb-4 bg-white rounded"),
        ], width=4),
        
        dbc.Col([
            dcc.Graph(id='pnl-graph'),
            dcc.Graph(id='candlestick-chart')
        ], width=8)
    ], align="center")
], fluid=True)

# Callback to update P&L graph and fetch stock data
@app.callback(
    [Output('pnl-graph', 'figure'), Output('candlestick-chart', 'figure')],
    [Input('ticker-symbol', 'value'),
     Input('underlying-price', 'value'),
     Input('option-premium', 'value'),
     Input('contract-size', 'value'),
     Input('option-type', 'value'),
     Input('delta-purchase', 'value'),
     Input('theta-purchase', 'value'),
     Input('date-purchased', 'date'),
     Input('current-date', 'date'),
     Input('expiry-date', 'date')]
)
def update_graph(ticker, underlying, premium, contract_size, option_type, delta, theta, date_purchased, current_date, expiry_date):
    if not date_purchased or not current_date or not expiry_date:
        return go.Figure(), go.Figure()
    
    days_to_expiry = (datetime.date.fromisoformat(expiry_date) - datetime.date.fromisoformat(current_date)).days
    price_range = np.linspace(underlying * 0.8, underlying * 1.2, 50)
    estimated_pnl = (price_range - underlying) * delta * contract_size - premium * contract_size - (theta * days_to_expiry * contract_size)
    
    pnl_fig = go.Figure()
    pnl_fig.add_trace(go.Scatter(x=price_range, y=estimated_pnl, mode='lines', name='Estimated P&L'))
    pnl_fig.update_layout(title="P&L vs. Hypothetical Stock Price with Theta Decay",
                          xaxis_title="Stock Price",
                          yaxis_title="Estimated P&L",
                          template="plotly_dark")
    
    try:
        stock_data = yf.Ticker(ticker).history(period='1mo')
        candlestick_fig = go.Figure(data=[go.Candlestick(
            x=stock_data.index,
            open=stock_data['Open'],
            high=stock_data['High'],
            low=stock_data['Low'],
            close=stock_data['Close']
        )])
        candlestick_fig.update_layout(title=f"{ticker} Candlestick Chart", template="plotly_dark")
    except:
        candlestick_fig = go.Figure()
        candlestick_fig.update_layout(title="Stock Data Unavailable", template="plotly_dark")
    
    return pnl_fig, candlestick_fig

# Run the app with proper port binding for Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))  # Render assigns a port dynamically
    app.run_server(host='0.0.0.0', port=port, debug=False)
