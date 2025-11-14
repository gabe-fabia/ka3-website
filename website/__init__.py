from flask import (
    Flask,
    jsonify,
    render_template_string,
    render_template,
    request,
    send_file,
)
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
import plotly.offline as pyo
from sqlalchemy import create_engine
import datetime

import yfinance as yf
import openpyxl
from openpyxl import load_workbook
import io

import os
from dotenv import load_dotenv

load_dotenv()

# Commends to start app:
# source website/venv/bin/activate
# export FLASK_APP=website
# flask run

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # showing sensitive info, instead use .env file

    # app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.db"

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
    def test_graph():
        y_tr_rec = pd.read_csv("website/temporary_data/y_tr_rec.csv")
        a = y_tr_rec["periods"].isna()
        b = a == False
        c = list(y_tr_rec.loc[b, "Date"])
        c
        # y_tr_rec = pd.read_csv("temporary_data/y_tr_rec.csv")
        y_tr_rec["Date"] = pd.to_datetime(y_tr_rec["Date"])

        fig = px.line(
            y_tr_rec,
            x="Date",
            y=y_tr_rec.loc[:, ("T10Y3M", "spline")].columns,
            hover_data="Date",
            title="Treasury Spread  with spline",
        )
        for i in range(0, len(c), 2):
            fig.add_vline(x=c[i], line_color="blue", line_dash="dash")
            fig.add_annotation(
                x=c[0],
                y=0.05,  # position
                xref="x",
                yref="y",
                text="Recession Beg.",  # text
                align="left",
                showarrow=False,
            )

            fig.add_vline(x=c[i + 1], line_color="blue", line_dash="solid")
            fig.add_annotation(
                x=c[1],
                y=-2,  # position
                text="Recession End",  # text
                align="right",
                showarrow=False,
            )
        fig.update_xaxes(dtick="M1", tickformat="\n%Y")
        # chart_div = px.line(fig, output_type="div", include_plotlyjs="cdn")
        plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
        return render_template("plotly_chart.html", chart_div=plot_html)
        # fig.show()

    def plot_etfs_single(df_yc, i):  # bd_dict_dict

        no_nans = df_yc["ticker"].isna() == False

        ticker_list = list(df_yc.loc[no_nans, "ticker"].unique())
        ticker1 = f"{ticker_list[i]}"  # i'th ticker
        a = df_yc["ticker"] == ticker1

        yc_dt_rng = min(df_yc[a]["date"])  # inception date of the i'th ticker

        t = df_yc["date"] >= yc_dt_rng
        df_yc = df_yc[
            t
        ]  # treasury spread, all ticker prices from the day of the i'th ticker inception

        b = (
            df_yc["periods"] == "beg"
        )  # boolean indicating beginning if all recession periods with respect to ticker i's inception
        e = df_yc["periods"] == "end"

        return b, e, ticker1, df_yc

    @app.route("/testing", methods=["GET"])
    def plotly_graph_test():

        from plotly.subplots import make_subplots

        dat = pd.read_csv("website/temporary_data/df_yield.csv")

        fig = make_subplots(specs=[[{"secondary_y": True}]])  # secondary y_axis
        b, e, ticker1, df_yc_ticker = plot_etfs_single(dat, 1)
        """#b_ticker = df_yc['ticker'] == ticker1
        #df_yc_ticker['date'] """
        x = pd.to_datetime(df_yc_ticker["date"], errors="coerce")
        y = pd.to_numeric(df_yc_ticker["T10Y3M"], errors="coerce")

        fig.add_trace(go.Scatter(x=x, y=y, name="Treasury Spread"), secondary_y=False)

        # hover_data = 'date', title = f'Treasury Spread with recessions and {ticker1}'))

        if sum(b) != 0:
            recession_start_dates = pd.to_datetime(df_yc_ticker.loc[b, "date"].unique())
            recession_end_dates = pd.to_datetime(df_yc_ticker.loc[e, "date"].unique())

            for date in recession_start_dates:
                fig.add_vline(x=date, line_color="black", line_dash="dash")
                fig.add_trace(
                    go.Scatter(
                        x=[date],
                        y=[y.min()],
                        mode="text",
                        text=["recession_start"],
                        showlegend=False,
                    )
                )

            for date in recession_end_dates:
                fig.add_vline(x=date, line_color="black", line_dash="solid")
                fig.add_trace(
                    go.Scatter(
                        x=[date],
                        y=[y.max()],
                        mode="text",
                        text=["recession_end"],
                        showlegend=False,
                    )
                )

        fig.add_scatter(
            x=df_yc_ticker["date"],
            y=np.zeros(df_yc_ticker.shape[0]),
            name="null spread",
        )

        # Closing price of the i'th ticker; namely, ticker1
        b_close = (
            df_yc_ticker["ticker"] == ticker1
        )  # boolean indicating presence of ticker1
        y_close = pd.to_numeric(
            df_yc_ticker.loc[b_close, "close"], errors="coerce"
        )  # closing price
        y_open = pd.to_numeric(
            df_yc_ticker.loc[b_close, "open"], errors="coerce"
        )  # opening price
        y_low = pd.to_numeric(
            df_yc_ticker.loc[b_close, "low"], errors="coerce"
        )  # lowest price
        y_high = pd.to_numeric(
            df_yc_ticker.loc[b_close, "high"], errors="coerce"
        )  # highest price

        fig.add_trace(
            go.Candlestick(
                x=df_yc_ticker.loc[b_close, "date"],
                open=y_open,
                low=y_low,
                high=y_high,
                close=y_close,
                increasing_line_color="cyan",
                decreasing_line_color="gray",
                name=f"prices of {ticker1}",
            ),
            secondary_y=True,
        )

        # set y-axes titles
        fig.update_yaxes(
            title_text="<b>primary</b>  Treasury Spread", secondary_y=False
        )
        fig.update_yaxes(
            title_text="<b>secondary</b> " f"Stock Ticker: {ticker1}", secondary_y=True
        )
        fig.update_xaxes(dtick="M12", tickformat="\n%Y")
        fig.update_layout(
            title_text=f'Equity:{ticker1} in Sector:{list(df_yc_ticker.loc[:, "sector"])[1]}',
            xaxis_tickformat="%d %B (%a)<br>%Y",
        )

        plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
        return render_template("plotly_chart.html", chart_div=plot_html)

    class one_step_pred(object):

        def __init__(self, df_yc, ticker):
            self.df_yc = df_yc
            self.df_yc.loc[:, "date"] = pd.to_datetime(self.df_yc.loc[:, "date"])
            self.ticker = ticker
            self.dat = df_yc[df_yc["ticker"] == self.ticker]
            self.sector = list(
                # df_yc[df_yc["ticker"] == self.ticker, "sector"].unique()
                df_yc[df_yc["ticker"] == self.ticker]["sector"].unique()
            )[0]
            self.dat.loc[:, "date"] = pd.to_datetime(self.dat.loc[:, "date"])
            yc_dt_rng = min(
                self.dat.loc[:, "date"]
            )  # inception date of the stock ticker

            t = self.df_yc["date"] >= yc_dt_rng
            self.df_yc = self.df_yc[
                t
            ]  # treasury spread, all ticker prices from the day of the stock ticker inception

            self.b = (
                df_yc["periods"] == "beg"
            )  # boolean indicating beginning if all recession periods with respect to the ticker inception
            self.e = df_yc["periods"] == "end"

        # Generating mean predictions of stock ticker
        def pred_prices(self):

            # Use all the data in the  dataset :

            pred_updates = []  # Calculating the mean updates
            pos = self.dat.index[-1]
            split_date = self.dat.loc[pos, "date"]

            dat_train = self.dat.loc[self.dat["date"] <= split_date, :]

            train_returns = (
                100 * dat_train["close"].pct_change().dropna()
            )  # 100 is a scale factor

            from arch import arch_model

            g_model = arch_model(train_returns, vol="GARCH", p=1, o=1, q=1, dist="t")
            res = g_model.fit(update_freq=0, disp="off")
            split_date = self.dat.loc[pos, "date"].date()
            a = res.forecast(horizon=1, start=split_date)
            pos_prev = self.dat.index[-1]
            pred_pct_change = (a.residual_variance.loc[pos_prev, "h.1"] ** 0.5) * (
                a.mean.loc[pos_prev, "h.1"]
            )
            prediction = (
                (pred_pct_change * dat_train.loc[pos_prev, "close"]) / 100
            ) + dat_train.loc[pos_prev, "close"]
            prediction = round(prediction, ndigits=2)
            pred_updates.append(prediction)
            return pred_updates

        def graph_plotly(self):

            from plotly.subplots import make_subplots

            fig = make_subplots(specs=[[{"secondary_y": True}]])  # secondary y_axis

            x = pd.to_datetime(self.df_yc["date"], errors="coerce")
            y = pd.to_numeric(self.df_yc["T10Y3M"], errors="coerce")

            fig.add_trace(
                go.Scatter(x=x, y=y, name="Treasury Spread"), secondary_y=False
            )

            if sum(self.b) != 0:
                recession_start_dates = pd.to_datetime(
                    self.df_yc.loc[self.b, "date"].unique()
                )
                recession_end_dates = pd.to_datetime(
                    self.df_yc.loc[self.e, "date"].unique()
                )
                # print(recession_end_dates)
                for date in recession_start_dates:
                    fig.add_vline(x=date, line_color="black", line_dash="dash")
                    fig.add_trace(
                        go.Scatter(
                            x=[date],
                            y=[y.min()],
                            mode="text",
                            text=["recession_start"],
                            showlegend=False,
                        )
                    )

                for date in recession_end_dates:
                    fig.add_vline(x=date, line_color="black", line_dash="solid")
                    fig.add_trace(
                        go.Scatter(
                            x=[date],
                            y=[y.max()],
                            mode="text",
                            text=["recession_end"],
                            showlegend=False,
                        )
                    )

            fig.add_scatter(
                x=self.df_yc["date"],
                y=np.zeros(self.df_yc.shape[0]),
                name="null spread",
            )

            # Closing price of the stock

            y_close = pd.to_numeric(
                self.dat.loc[:, "close"], errors="coerce"
            )  # closing price
            y_open = pd.to_numeric(
                self.dat.loc[:, "open"], errors="coerce"
            )  # opening price
            y_low = pd.to_numeric(self.dat.loc[:, "low"], errors="coerce")  # low price
            y_high = pd.to_numeric(
                self.dat.loc[:, "high"], errors="coerce"
            )  # high price

            fig.add_trace(
                go.Candlestick(
                    x=self.dat.loc[:, "date"],
                    open=y_open,
                    low=y_low,
                    high=y_high,
                    close=y_close,
                    increasing_line_color="cyan",
                    decreasing_line_color="gray",
                    name=f"prices of { self.ticker }",
                ),
                secondary_y=True,
            )
            # print(self.dat['date'].max())
            x_point = max(self.dat.loc[:, "date"]) + datetime.timedelta(days=7)
            y_point = self.pred_prices()
            fig.add_scatter(
                x=[x_point],
                y=y_point,
                text=["mean prediction"],
                showlegend=False,
                secondary_y=True,
            )  # fillcolor = 'darkorange'

            # set y-axes titles
            fig.update_yaxes(
                title_text="<b>primary</b>  Treasury Spread", secondary_y=False
            )
            fig.update_yaxes(
                title_text="<b>secondary</b> " f"Stock Ticker: {self.ticker}",
                secondary_y=True,
            )
            fig.update_xaxes(dtick="M12", tickformat="\n%Y")
            fig.update_layout(
                {"title": {"text": f"Equity:{ self.ticker } in Sector:{self.sector}"}},
                overwrite=True,
                xaxis_tickformat="%d %B (%a)<br>%Y",
            )

            # fig.show()
            return fig

    @app.route("/testing_2", methods=["GET"])
    def graph_astep():
        astep = one_step_pred(
            df_yc=pd.read_csv("website/temporary_data/df_yield.csv"), ticker="IYH"
        )
        fig = astep.graph_plotly()
        plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
        return render_template("plotly_chart.html", chart_div=plot_html)

    @app.route("/testing_3", methods=["GET"])
    def graph_astep_2():
        astep = one_step_pred(
            df_yc=pd.read_csv("website/temporary_data/df_yield.csv"), ticker="IXJ"
        )
        fig = astep.graph_plotly()
        plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
        return render_template("plotly_chart.html", chart_div=plot_html)

    @app.route("/testing_4", methods=["GET"])
    def graph_tstep():
        tstep = one_step_pred(
            df_yc=pd.read_csv("website/temporary_data/df_us_evolve.csv"),
            ticker="LIFE.TO",
        )
        fig = tstep.graph_plotly()
        plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
        return render_template("plotly_chart.html", chart_div=plot_html)

    def scraped_yf_df(ticker_str):
        ticker = yf.Ticker(ticker_str)
        # ticker.reset_index(inplace = True)

        income_statement = ticker.income_stmt

        financials = ticker.ttm_financials
        # ttm_revenue = financials.loc["Total Revenue"].T
        ttm_balance_sheet = ticker.quarterly_balance_sheet.iloc[:, 0:1]
        balance_sheet = ticker.balancesheet
        cash_and_equivalents = pd.concat(
            [
                ttm_balance_sheet.loc["Cash And Cash Equivalents"],
                balance_sheet.loc["Cash And Cash Equivalents"],
            ],
            ignore_index=True,
        )
        # long_term_debt = pd.concat([ttm_balance_sheet.loc['Long Term Debt'], balance_sheet.loc['Long Term Debt']], ignore_index=True)
        long_term_debt = pd.concat(
            [
                ttm_balance_sheet.loc["Long Term Debt And Capital Lease Obligation"],
                balance_sheet.loc["Long Term Debt And Capital Lease Obligation"],
            ],
            ignore_index=True,
        )

        stockholders_equity = pd.concat(
            [
                ttm_balance_sheet.loc["Stockholders Equity"],
                balance_sheet.loc["Stockholders Equity"],
            ],
            ignore_index=True,
        )

        dates = financials.columns.append(income_statement.columns)

        s1 = financials.loc["Total Revenue"]
        s2 = income_statement.loc["Total Revenue"]
        type(pd.concat([s1, s2]))
        revenue = pd.concat([s1, s2], ignore_index=True)

        cost_of_revenue = pd.concat(
            [
                financials.loc["Cost Of Revenue"],
                income_statement.loc["Cost Of Revenue"],
            ],
            ignore_index=True,
        )

        operating_income = pd.concat(
            [
                financials.loc["Operating Income"],
                income_statement.loc["Operating Income"],
            ],
            ignore_index=True,
        )

        diluted_eps = pd.concat(
            [financials.loc["Diluted EPS"], income_statement.loc["Diluted EPS"]],
            ignore_index=True,
        )

        diluted_avg_shares = pd.concat(
            [
                financials.loc["Diluted Average Shares"],
                income_statement.loc["Diluted Average Shares"],
            ],
            ignore_index=True,
        )
        interest_expense = pd.concat(
            [
                financials.loc["Interest Expense"],
                income_statement.loc["Interest Expense"],
            ],
            ignore_index=True,
        )

        ttm_cash_flow = ticker.ttm_cash_flow
        cash_flow = ticker.cash_flow

        operating_cash_flow = pd.concat(
            [
                ttm_cash_flow.loc["Operating Cash Flow"],
                cash_flow.loc["Operating Cash Flow"],
            ],
            ignore_index=True,
        )
        free_cash_flow = pd.concat(
            [ttm_cash_flow.loc["Free Cash Flow"], cash_flow.loc["Free Cash Flow"]],
            ignore_index=True,
        )

        final_df = pd.DataFrame(
            columns=[
                "Date",
                "Total Revenue",
                "Cost Of Revenue",
                "Operating Income",
                "Diluted EPS",
                "Diluted Average Shares",
                "Interest Expense",
                "Cash And Cash Equivalents",
                "Long Term Debt",
                "Stockholders Equity",
                "Operating Cash Flow",
                "Free Cash Flow",
            ]
        )
        final_df["Date"] = dates

        final_df["Total Revenue"] = revenue
        final_df["Cost Of Revenue"] = cost_of_revenue
        final_df["Operating Income"] = operating_income
        final_df["Diluted EPS"] = diluted_eps
        final_df["Diluted Average Shares"] = diluted_avg_shares
        final_df["Interest Expense"] = interest_expense

        final_df["Cash And Cash Equivalents"] = cash_and_equivalents
        final_df["Long Term Debt"] = long_term_debt
        final_df["Stockholders Equity"] = stockholders_equity

        final_df["Operating Cash Flow"] = operating_cash_flow
        final_df["Free Cash Flow"] = free_cash_flow

        return final_df

    @app.route("/download_template")
    def download_template():
        return send_file()

    # @app.route("/data", methods=["GET"])
    # def select_ticker():
    #     tickers = db.session.query(Stock.Ticker).distinct().all()
    #     ticker_list = [t[0] for t in tickers]
    #     ticker_list.sort()
    #     return render_template("select_ticker.html", tickers=ticker_list)

    # def fetch_joined_data(ticker):
    #     engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])

    #     df = pd.read_sql_query(
    #         f"""
    #                 SELECT a.Date, a.3_Month, a.10_Year, b.Ticker, b.Close, b.Fund_Name
    #                 FROM yield_rates a
    #                 JOIN stocks b ON a.Date = LEFT(b.Date, 10)
    #                 WHERE b.Ticker = "{ticker}"
    #                 """,
    #         engine,
    #     )
    #     df["10_3_spread"] = df["10_Year"] - df["3_Month"]
    #     return df

    # def create_plotly_chart(ticker):
    #     df = fetch_joined_data(ticker)

    #     dates = df["Date"].tolist()
    #     close = df["Close"].tolist()
    #     spread = df["10_3_spread"].tolist()

    #     trace_close = go.Scatter(
    #         x=dates,
    #         y=close,
    #         name="Close Price",
    #         line=dict(color="blue"),
    #         yaxis="y1",
    #     )

    #     trace_spread = go.Scatter(
    #         x=dates,
    #         y=spread,
    #         name="Yield Curve",
    #         line=dict(color="red"),
    #         yaxis="y2",
    #     )

    #     fund_name = df["Fund_Name"][0]

    #     layout = go.Layout(
    #         title=f"{fund_name} vs. Yield Curve Comparison",
    #         xaxis=dict(title="Date"),
    #         yaxis=dict(
    #             title="Close Price ($)",
    #             # titlefont=dict(color="blue"),
    #             tickfont=dict(color="blue"),
    #         ),
    #         yaxis2=dict(
    #             title="Yield Curve (%)",
    #             # titlefont=dict(color="red"),
    #             tickfont=dict(color="red"),
    #             overlaying="y",
    #             side="right",
    #         ),
    #         template="plotly_white",
    #     )

    #     fig = go.Figure(data=[trace_close, trace_spread], layout=layout)
    #     chart_div = pyo.plot(fig, output_type="div", include_plotlyjs="cdn")

    #     return render_template("plotly_chart.html", chart_div=chart_div)

    # @app.route("/graph", methods=["GET"])
    # def plotly_view():
    #     ticker = request.args["ticker"]
    #     chart_html = create_plotly_chart(ticker)
    #     return render_template_string(
    #         """
    #         <html><body>
    #             {{ chart|safe }}
    #         </body></html>
    #     """,
    #         chart=chart_html,
    #     )

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
