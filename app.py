from flask import Flask, render_template, request, jsonify
import yfinance as yf
import plotly.graph_objs as go
import plotly.io as pio
import pandas as pd


from pathlib import Path

from chat import get_response  # For chatbot functionality

app = Flask(__name__)

@app.get("/")
def index_get():
    return render_template("base.html")

@app.post("/predict")
def predict():
    text = request.get_json().get("message")
    response = get_response(text)
    message = {"answer": response}
    return jsonify(message)

@app.route("/visualization", methods=["GET", "POST"])
def stock_visualization():
    if request.method == "POST":
        stock_symbol = request.form.get("symbol").upper()
        try:
            stock_data = yf.download(stock_symbol, period="1mo")

            if stock_data.empty:
                return render_template("index.html", error="Stock data not found")

            # Plot Closing Price Over Time
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], mode='lines', name='Close'))
            fig1.update_layout(title=f"Closing Prices of {stock_symbol} Over Time", xaxis_title='Date', yaxis_title='Price')
            plot1 = pio.to_html(fig1, full_html=False)

            # Plot Open, High, Low, Close
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Open'], mode='lines', name='Open'))
            fig2.add_trace(go.Scatter(x=stock_data.index, y=stock_data['High'], mode='lines', name='High'))
            fig2.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Low'], mode='lines', name='Low'))
            fig2.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], mode='lines', name='Close'))
            fig2.update_layout(title=f"{stock_symbol} Stock Metrics", xaxis_title='Date', yaxis_title='Price')
            plot2 = pio.to_html(fig2, full_html=False)

            # Pie Chart for Stock Price Distribution
            avg_open = stock_data['Open'].mean()
            avg_high = stock_data['High'].mean()
            avg_low = stock_data['Low'].mean()
            avg_close = stock_data['Close'].mean()

            fig3 = go.Figure(data=[go.Pie(labels=['Open', 'High', 'Low', 'Close'],
                                         values=[avg_open, avg_high, avg_low, avg_close])])
            fig3.update_layout(title="Stock Price Distribution")
            plot3 = pio.to_html(fig3, full_html=False)

            return render_template("index.html", plot1=plot1, plot2=plot2, plot3=plot3)

        except Exception as e:
            return render_template("index.html", error="Error fetching stock data")
    return render_template("index.html")


# @app.route("/Tolerance", methods=["GET", "POST"])
# def tolerance():
#     return render_template("index2.html")


# Function to get user tolerance (as previously defined)
def get_tolerance(user):
    data = pd.read_csv("calculate_tolerance.csv", delimiter=",", index_col=False)
    
    sal = user['sal']
    age = int(user['age'])
    res = int(user['res'])
    gender = user['gender']
    
    if (sal <= 250000):
        sal_cat = 'L'
    elif (sal > 250000) & (sal <= 1000000):
        sal_cat = 'LM'
    elif (sal > 1000000) & (sal <= 3000000):
        sal_cat = 'UM'
    elif (sal > 3000000):
        sal_cat = 'H'

    temp = data.loc[(data['Age_Min'] <= age) & (data['Age_Max'] >= age)]
    temp1 = temp.loc[(temp['Gender'] == gender) & (temp['Residency'] == res) & (temp['Sal_Cat'] == sal_cat)]

    if temp1.empty:
        raise ValueError("No matching tolerance data found for the given inputs.")
    
    tol_port = temp1['Tol_P'].values[0]
    tol_stock = temp1['Tol_S'].values[0]
    
    if tol_port >= 70 and tol_stock >= 70:
        reason = "The portfolio and stock tolerance are high, it's a good decision to buy."
    elif tol_port < 50 or tol_stock < 50:
        reason = "The portfolio and/or stock tolerance is too low, not a good time to buy."
    else:
        reason = "The tolerance levels are moderate. You may buy, but consider the risks."

    return tol_port, tol_stock, reason

# Function to get stock information and visualizations
def stock_info(ticker, tol):
    tol1 = float((100 + tol) / 100)
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo")

    if hist.empty:
        return {"error": "Invalid stock symbol or no data available"}
    
    last_refreshed = hist.index[-1].strftime('%Y-%m-%d')
    latest_close = hist['Close'].iloc[-1]
    recent_high = hist['High'].max()
    recent_low = hist['Low'].min()
    threshold = tol1 * recent_low
    recommendation = "BUY" if latest_close < threshold else "DON'T BUY"
    
    # Plot Closing Price Over Time
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close'))
    fig1.update_layout(title=f"Closing Prices of {ticker} Over Time", xaxis_title='Date', yaxis_title='Price')
    plot1 = pio.to_html(fig1, full_html=False)

    # Plot Open, High, Low, Close
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=hist.index, y=hist['Open'], mode='lines', name='Open'))
    fig2.add_trace(go.Scatter(x=hist.index, y=hist['High'], mode='lines', name='High'))
    fig2.add_trace(go.Scatter(x=hist.index, y=hist['Low'], mode='lines', name='Low'))
    fig2.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close'))
    fig2.update_layout(title=f"{ticker} Stock Metrics", xaxis_title='Date', yaxis_title='Price')
    plot2 = pio.to_html(fig2, full_html=False)

    # Pie Chart for Stock Price Distribution
    avg_open = hist['Open'].mean()
    avg_high = hist['High'].mean()
    avg_low = hist['Low'].mean()
    avg_close = hist['Close'].mean()

    fig3 = go.Figure(data=[go.Pie(labels=['Open', 'High', 'Low', 'Close'],
                                 values=[avg_open, avg_high, avg_low, avg_close])])
    fig3.update_layout(title="Stock Price Distribution")
    plot3 = pio.to_html(fig3, full_html=False)

    return {
        "last_refreshed": last_refreshed,
        "latest_close": latest_close,
        "recent_high": recent_high,
        "recent_low": recent_low,
        "recommendation": recommendation,
        "plot1": plot1,
        "plot2": plot2,
        "plot3": plot3
    }

# Flask route for tolerance and stock visualization
@app.route("/Tolerance", methods=["GET", "POST"])
def tolerance():
    stock_data = {}
    reason = ""  # Initialize reason variable

    if request.method == "POST":
        username = request.form['username']
        salary = int(request.form['salary'])
        age = int(request.form['age'])
        residency = int(request.form['residency'])
        gender = request.form['gender'].upper()
        symbol = request.form['symbol']
        
        user_info = {'sal': salary, 'age': age, 'res': residency, 'gender': gender}
        
        try:
            tol_portfolio, tol_stockprice, reason = get_tolerance(user_info)
            stock_data = stock_info(symbol, tol_stockprice)
        except ValueError as e:
            stock_data['error'] = str(e)

    return render_template("index2.html", stock_data=stock_data, reason=reason)

if __name__ == "__main__":
    app.run(debug=True)

