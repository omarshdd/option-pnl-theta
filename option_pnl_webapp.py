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
                    
                    html.Label("Contract Size (number of option contracts):"),
                    dcc.Input(id='contract-size', type='number', value=1, className="form-control"),
                ])
            ], className="shadow-lg p-3 mb-4 bg-white rounded"),

            dbc.Card([
                dbc.CardBody([
                    html.H5("Greeks & Expiry"),
                    html.Label("Delta at Purchase:"),
                    dcc.Input(id='delta-purchase', type='number', value=0.5, className="form-control"),
                    
                    html.Label("Theta at Purchase (enter as positive, automatically adjusted):"),
                    dcc.Input(id='theta-purchase', type='number', value=0.02, className="form-control"),
                    
                    html.Label("Date Purchased:"),
                    dcc.DatePickerSingle(id='date-purchased', date=str(datetime.date.today() - datetime.timedelta(days=10))),
                    
                    html.Label("Expiry Date:"),
                    dcc.DatePickerSingle(id='expiry-date', date=str(datetime.date.today() + datetime.timedelta(days=30))),
                ])
            ], className="shadow-lg p-3 mb-4 bg-white rounded"),
        ], width=4),
        
        dbc.Col([
            html.Label("Stock Price Adjustment (% Change):"),
            dcc.Slider(id='hypothetical-slider', min=-20, max=20, step=1, value=0, 
                       marks={i: f"{i}%" for i in range(-20, 21, 5)}),
            html.Div(id='adjusted-price-display', className="text-center mt-2"),
            dcc.Graph(id='pnl-graph'),
            dcc.Graph(id='candlestick-chart')
        ], width=8)
    ], align="center")
], fluid=True)

# Callback to update P&L graph, stock price display, and fetch stock data
@app.callback(
    [Output('pnl-graph', 'figure'), Output('candlestick-chart', 'figure'), Output('adjusted-price-display', 'children')],
    [Input('ticker-symbol', 'value'),
     Input('underlying-price', 'value'),
     Input('option-premium', 'value'),
     Input('contract-size', 'value'),
     Input('option-type', 'value'),
     Input('delta-purchase', 'value'),
     Input('theta-purchase', 'value'),
     Input('date-purchased', 'date'),
     Input('expiry-date', 'date'),
     Input('hypothetical-slider', 'value')]
)
def update_graph(ticker, underlying, premium, contract_size, option_type, delta, theta, date_purchased, expiry_date, hypo_change):
    if not date_purchased or not expiry_date:
        return go.Figure(), go.Figure(), ""
    
    start_date = datetime.date.fromisoformat(date_purchased)
    end_date = datetime.date.fromisoformat(expiry_date)
    days_to_expiry = (end_date - start_date).days
    market_days = np.array([start_date + datetime.timedelta(days=i) for i in range(days_to_expiry)])
    
    adjusted_price = underlying * (1 + hypo_change / 100)
    option_multiplier = 100  # Standard contract size for options (100 shares per contract)
    total_contracts = contract_size * option_multiplier
    
    # Automatically make Theta negative since it's time decay
    theta = -abs(theta)
    
    # Exponential Theta Decay Model
    theta_decay_factor = np.exp(-np.linspace(0, 3, days_to_expiry))
    extrinsic_value = premium * np.exp(-0.1 * np.arange(days_to_expiry))  # Exponential decay of premium
    intrinsic_value = max(adjusted_price - underlying, 0) if option_type == 'call' else max(underlying - adjusted_price, 0)
    option_value = np.maximum(intrinsic_value, extrinsic_value)
    
    estimated_pnl = (option_value * total_contracts) - (premium * total_contracts)
    pnl_percentage = (estimated_pnl / (premium * total_contracts)) * 100
    
    pnl_fig = go.Figure()
    pnl_fig.add_trace(go.Scatter(x=market_days, y=estimated_pnl, mode='lines', name='Estimated P&L ($)'))
    pnl_fig.add_trace(go.Scatter(x=market_days, y=pnl_percentage, mode='lines', name='P&L (%)', yaxis='y2'))
    pnl_fig.update_layout(
        title="P&L vs. Market Dates to Expiry",
        xaxis_title="Market Date",
        yaxis_title="Estimated P&L ($)",
        yaxis2={"title": "P&L (%)", "overlaying": "y", "side": "right"},
        template="plotly_dark"
    )
    
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
    
    adjusted_price_display = f"Adjusted Stock Price: ${adjusted_price:.2f} ({hypo_change}%)"
    
    return pnl_fig, candlestick_fig, adjusted_price_display

# Run the app with proper port binding for Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render assigns a port dynamically
    app.run_server(host='0.0.0.0', port=port, debug=True)
