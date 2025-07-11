import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Helper function: Get stock info and object
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    financials = {
        "Name": info.get("shortName", "N/A"),
        "Sector": info.get("sector", "N/A"),
        "Industry": info.get("industry", "N/A"),
        "Market Cap": info.get("marketCap", "N/A"),
        "Trailing P/E": info.get("trailingPE", "N/A"),
        "Return on Equity": info.get("returnOnEquity", "N/A"),
        "Revenue (TTM)": info.get("totalRevenue", "N/A"),
        "Net Income (TTM)": info.get("netIncomeToCommon", "N/A"),
    }
    return financials, stock

# Helper: Get quarterly income

def get_quarterly_income(stock_obj):
    try:
        income_stmt = stock_obj.quarterly_financials.T
        income_stmt = income_stmt[["Total Revenue", "Net Income"]]
        income_stmt.columns = ["Revenue", "Net Income"]
        return income_stmt.dropna()
    except:
        return pd.DataFrame()

# Add growth columns
def add_growth_columns(df):
    df = df.copy()
    df["Revenue Growth %"] = df["Revenue"].pct_change() * 100
    df["Net Income Growth %"] = df["Net Income"].pct_change() * 100
    return df

# Generate summary
def generate_summary(df, financials):
    avg_rev = df["Revenue Growth %"].mean()
    avg_net = df["Net Income Growth %"].mean()
    summary = f"\n📊 Summary for {financials['Name']}\n"
    summary += ("\n• Revenue has shown strong growth." if avg_rev > 5 else
                "\n• Revenue has modest or flat growth." if avg_rev > 0 else
                "\n• Revenue is declining.")
    summary += ("\n• Net income improved significantly." if avg_net > 5 else
                "\n• Net income slightly improved." if avg_net > 0 else
                "\n• Profitability is under pressure.")
    summary += f"\n\n💼 Sector: {financials['Sector']}, Industry: {financials['Industry']}"
    return summary

# Stress test
def stress_test(df, revenue_shock, cost_shock):
    df = df.copy()
    df["Stressed Revenue"] = df["Revenue"] * (1 + revenue_shock)
    df["Estimated Cost"] = df["Revenue"] - df["Net Income"]
    df["Stressed Cost"] = df["Estimated Cost"] * (1 + cost_shock)
    df["Stressed Net Income"] = df["Stressed Revenue"] - df["Stressed Cost"]
    df["Stressed Net Margin (%)"] = (df["Stressed Net Income"] / df["Stressed Revenue"]) * 100
    return df[["Revenue", "Net Income", "Stressed Revenue", "Stressed Net Income", "Stressed Net Margin (%)"]]

# Streamlit App
st.set_page_config(page_title="GenAI Financial Analyst Toolkit", layout="wide")
st.title("📊 GenAI Financial Analyst Toolkit")

ticker = st.text_input("Enter Ticker Symbol (e.g., ITC.NS for India)", value="ITC.NS")

if ticker:
    financials, stock_obj = get_stock_data(ticker)
    st.subheader(f"Overview: {financials['Name']}")
    st.write(financials)

    income_df = get_quarterly_income(stock_obj)

    if not income_df.empty:
        income_df_cleaned = income_df[income_df["Net Income"] < 1e11]
        income_df_growth = add_growth_columns(income_df_cleaned)

        st.subheader("📈 Quarterly Revenue & Net Income")
        st.line_chart(income_df_growth[["Revenue", "Net Income"]])

        st.subheader("📊 Growth Analysis")
        st.dataframe(income_df_growth)

        st.subheader("🧠 Summary")
        summary = generate_summary(income_df_growth, financials)
        st.markdown(summary)

        st.subheader("🔧 Stress Test")
        rev_shock = st.slider("Revenue Shock (%)", -50, 50, -10) / 100
        cost_shock = st.slider("Cost Shock (%)", -50, 50, 5) / 100

        stress_df = stress_test(income_df_cleaned, rev_shock, cost_shock)
        st.dataframe(stress_df)

        latest = stress_df.iloc[-1]
        st.markdown(f"""
        ### 📉 Latest Stress Scenario:
        - **Revenue**: ₹ {latest['Revenue'] / 1e7:.2f} Cr
        - **Stressed Revenue**: ₹ {latest['Stressed Revenue'] / 1e7:.2f} Cr
        - **Net Income**: ₹ {latest['Net Income'] / 1e7:.2f} Cr
        - **Stressed Net Income**: ₹ {latest['Stressed Net Income'] / 1e7:.2f} Cr
        - **Stressed Net Margin**: {latest['Stressed Net Margin (%)']:.2f}%
        """)
    else:
        st.warning("No quarterly income data available.")
