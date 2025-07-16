from flask import Flask, jsonify, render_template_string, render_template, request
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

import pandas as pd
import plotly.graph_objs as go
import plotly.offline as pyo
from sqlalchemy import create_engine

import os
from dotenv import load_dotenv

load_dotenv()

# Commends to start app:
# export FLASK_APP=website
# flask run

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # showing sensitive info, instead use .env file

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

    mysql = MySQL(app)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    class Stock(db.Model):
        __tablename__ = "stocks"
        Date = db.Column(db.String(50), primary_key=True)
        Ticker = db.Column(db.String(50), primary_key=True)
        Open = db.Column(db.Numeric(6, 2), nullable=False)
        High = db.Column(db.Numeric(6, 2), nullable=False)
        Low = db.Column(db.Numeric(6, 2), nullable=False)
        Close = db.Column(db.Numeric(6, 2), nullable=False)
        Volume = db.Column(db.Integer, nullable=False)
        Dividends = db.Column(db.Numeric(7, 5), nullable=False)
        Stock_Splits = db.Column(db.Numeric(7, 5), nullable=False)
        Fund_Name = db.Column(db.String(100), nullable=False)
        Sector = db.Column(db.String(100), nullable=False)

    @app.route("/data", methods=["GET"])
    def select_ticker():
        tickers = db.session.query(Stock.Ticker).distinct().all()
        ticker_list = [t[0] for t in tickers]
        ticker_list.sort()
        return render_template("select_ticker.html", tickers=ticker_list)

    def fetch_joined_data(ticker):
        engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])

        df = pd.read_sql_query(
            f"""
                    SELECT a.Date, a.3_Month, a.10_Year, b.Ticker, b.Close, b.Fund_Name
                    FROM yield_rates a
                    JOIN stocks b ON a.Date = LEFT(b.Date, 10)
                    WHERE b.Ticker = "{ticker}"
                    """,
            engine,
        )
        df["10_3_spread"] = df["10_Year"] - df["3_Month"]
        return df

    def create_plotly_chart(ticker):
        df = fetch_joined_data(ticker)

        dates = df["Date"].tolist()
        close = df["Close"].tolist()
        spread = df["10_3_spread"].tolist()

        trace_close = go.Scatter(
            x=dates,
            y=close,
            name="Close Price",
            line=dict(color="blue"),
            yaxis="y1",
        )

        trace_spread = go.Scatter(
            x=dates,
            y=spread,
            name="Yield Curve",
            line=dict(color="red"),
            yaxis="y2",
        )

        fund_name = df["Fund_Name"][0]

        layout = go.Layout(
            title=f"{fund_name} vs. Yield Curve Comparison",
            xaxis=dict(title="Date"),
            yaxis=dict(
                title="Close Price ($)",
                # titlefont=dict(color="blue"),
                tickfont=dict(color="blue"),
            ),
            yaxis2=dict(
                title="Yield Curve (%)",
                # titlefont=dict(color="red"),
                tickfont=dict(color="red"),
                overlaying="y",
                side="right",
            ),
            template="plotly_white",
        )

        fig = go.Figure(data=[trace_close, trace_spread], layout=layout)
        chart_div = pyo.plot(fig, output_type="div", include_plotlyjs="cdn")

        return render_template("plotly_chart.html", chart_div=chart_div)

    @app.route("/graph", methods=["GET"])
    def plotly_view():
        ticker = request.args["ticker"]
        chart_html = create_plotly_chart(ticker)
        return render_template_string(
            """
            <html><body>
                {{ chart|safe }}
            </body></html>
        """,
            chart=chart_html,
        )

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    # from .server import app as main_blueprint
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    with app.app_context():
        db.create_all()

    return app
