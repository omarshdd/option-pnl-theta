import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import numpy as np
import os
import datetime

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Option P&L Visualizer with Theta Decay"),
    
    html.Label("Underlying Price at Purchase:"),
    dcc.Input(id='underlying-price', type='number', value=100),
    
    html.Label("Option Premium:"),
    dcc.Input(id='option-premium', type='number', value=5),
    
    html.Label("Delta at Purchase:"),
    dcc.Input(id='delta-purchase', type='number', value=0.5),
    
    html.Label("Theta at Purchase (per day):"),
    dcc.Input(id='theta-purchase', type='number', value=0.02),
    
    html.Label("Date Purchased:"),
    dcc.DatePickerSingle(
        id='date-purchased',
        date=str(datetime.date.today() - datetime.timedelta(days=10))
    ),
    
    html.Label("Current Date:"),
    dcc.DatePickerSingle(
        id='current-date',
        date=str(datetime.date.today())
    ),
    
    html.Label("Adjust Hypothetical Price (% Change):"),
    dcc.Slider(id='hypothetical-slider', min=-20, max=20, step=1, value=0,
               marks={i: f"{i}%" for i in range(-20, 21, 5)}),
    
    dcc.Graph(id='pnl-graph'),
])

# Callback to update P&L graph
@app.callback(
    Output('pnl-graph', 'figure'),
    [Input('underlying-price', 'value'),
     Input('option-premium', 'value'),
     Input('delta-purchase', 'value'),
     Input('theta-purchase', 'value'),
     Input('date-purchased', 'date'),
     Input('current-date', 'date'),
     Input('hypothetical-slider', 'value')]
)
def update_graph(underlying, premium, delta, theta, date_purchased, current_date, hypo_change):
    if not date_purchased or not current_date:
        return go.Figure()
    
    days_remaining = (datetime.date.fromisoformat(current_date) - datetime.date.fromisoformat(date_purchased)).days
    price_range = np.linspace(underlying * 0.8, underlying * 1.2, 50)
    estimated_pnl = (price_range - underlying) * delta * 100 - premium * 100 - (theta * days_remaining * 100)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=price_range, y=estimated_pnl, mode='lines',
                             name='Estimated P&L'))
    
    fig.update_layout(title="P&L vs. Hypothetical Stock Price with Theta Decay",
                      xaxis_title="Stock Price",
                      yaxis_title="Estimated P&L")
    return fig

# Run the app with proper port binding for Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))  # Render assigns a port dynamically
    app.run_server(host='0.0.0.0', port=port, debug=False)
