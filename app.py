import streamlit as st
import pandas as pd

from src.anomaly import detect_anomalies
from src.agent import ask_agent
from src.recovery import get_recovery_action, estimate_recovery, build_recovery_opportunities


from src.tools import (
    get_payment_health,
    get_daily_trend,
    get_failure_reasons,
)


st.set_page_config(
    page_title="Payment Intelligence",
    page_icon="💳",
    layout="wide",
)
# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.title("🎛️ Filters")

selected_bank = st.sidebar.selectbox(
    "Bank",
    ["All", "BANK_X", "YES_BANK", "SBI", "HDFC", "ICICI", "AXIS", "PNB", "KOTAK"]
)

selected_payment_method = st.sidebar.selectbox(
    "Payment Method",
    ["All", "UPI", "CARD", "WALLET", "NETBANKING"]
)

# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("💳 AI Payment Intelligence")
st.caption(
    "AI-powered payment anomaly detection and investigation"
)


# --------------------------------------------------
# Load data
# --------------------------------------------------

health = get_payment_health()

anomalies = detect_anomalies()



daily_data = get_daily_trend(
    bank=None if selected_bank == "All" else selected_bank,
    payment_method=None if selected_payment_method == "All" else selected_payment_method
)


daily_df = pd.DataFrame(daily_data)


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Transactions",
        f"{health['total_transactions']:,}"
    )

with col2:
    st.metric(
        "Failed Transactions",
        f"{health['failed_transactions']:,}"
    )

with col3:
    st.metric(
        "Failure Rate",
        f"{health['failure_rate']}%"
    )

with col4:
    st.metric(
        "Failed Transaction Value",
        f"₹{health['failed_transaction_value']:,.0f}"
    )


st.divider()


# --------------------------------------------------
# DAILY PAYMENT TREND
# --------------------------------------------------

st.subheader("📈 Daily Payment Failure Trend")

if not daily_df.empty:

    daily_df["transaction_date"] = pd.to_datetime(
        daily_df["transaction_date"]
    )

    chart_df = daily_df.set_index(
        "transaction_date"
    )[["failure_rate"]]

    st.line_chart(chart_df)

else:

    st.info("No trend data available.")


st.divider()


# --------------------------------------------------
# ACTIVE ANOMALIES
# --------------------------------------------------

st.subheader("🚨 Active Payment Incidents")


if anomalies.empty:

    st.success(
        "✅ No significant payment anomalies detected."
    )

else:

    for _, anomaly in anomalies.iterrows():
        if st.button(
            f"🤖 Investigate {anomaly['bank']} / {anomaly['payment_method']}",
            key=f"investigate_{anomaly['bank']}_{anomaly['payment_method']}"
        ):

            question = f"""
            Investigate the {anomaly['bank']} {anomaly['payment_method']} payment incident.

            Explain:
            1. How severe is the anomaly?
            2. What are the dominant failure reasons?
            3. What is the estimated revenue impact?
            4. What should the payment operations team investigate next?
            """

            with st.spinner("🤖 Investigating incident..."):
                answer = ask_agent(question)

            st.markdown("#### 🤖 AI Investigation")
            st.write(answer)

        severity = anomaly["severity"]

        if severity == "CRITICAL":
            icon = "🔴"
        elif severity == "HIGH":
            icon = "🟠"
        else:
            icon = "🟡"

        with st.container(border=True):

            st.markdown(
                f"### {icon} {severity} — "
                f"{anomaly['bank']} / "
                f"{anomaly['payment_method']}"
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Current Failure Rate",
                    f"{anomaly['current_failure_rate']}%"
                )

            with col2:
                st.metric(
                    "Baseline",
                    f"{anomaly['baseline_failure_rate']}%"
                )

            with col3:
                st.metric(
                    "Multiplier",
                    f"{anomaly['anomaly_multiplier']}×"
                )

            with col4:
                st.metric(
                    "Revenue at Risk",
                    f"₹{anomaly['estimated_revenue_at_risk']:,.0f}"
                )


st.divider()

# --------------------------------------------------
# AI PAYMENT ANALYST
# --------------------------------------------------

st.subheader("🤖 AI Payment Analyst")

question = st.text_input(
    "Ask about your payment data",
    placeholder="Why is BANK_X UPI failing?"
)


if st.button(
    "🔍 Investigate",
    type="primary"
):

    if not question.strip():

        st.warning(
            "Please enter a question."
        )

    else:

        with st.spinner(
            "Investigating payment data..."
        ):

            answer = ask_agent(question)

        st.markdown("### 🤖 Analysis")
        st.write(answer)

# --------------------------------------------------
# FAILURE REASON ANALYSIS
# --------------------------------------------------

st.divider()

st.subheader("🔎 Failure Reason Analysis")

if not anomalies.empty:

    # Focus on the most severe anomaly
    top_anomaly = anomalies.iloc[0]

    bank = top_anomaly["bank"]
    payment_method = top_anomaly["payment_method"]


    if selected_bank != "All" and selected_payment_method != "All":

        failure_data = get_failure_reasons(
            selected_bank,
            selected_payment_method
        )

        st.markdown(
            f"Analysis for **{selected_bank} / {selected_payment_method}**"
        )

    else:

        failure_data = get_failure_reasons(
            top_anomaly["bank"],
            top_anomaly["payment_method"]
        )

        st.markdown(
            f"Analysis for **{top_anomaly['bank']} / "
            f"{top_anomaly['payment_method']}**"
        )

    failure_df = pd.DataFrame(failure_data)

    if not failure_df.empty:

        recovery_opportunities = build_recovery_opportunities(failure_df)

        st.markdown("### 💡 Recovery Opportunities")

        total_recovery_opportunity = recovery_opportunities[
            "estimated_recoverable_value"
        ].sum()

        st.metric(
            "Total Estimated Recovery Opportunity",
            f"₹{total_recovery_opportunity:,.0f}"
        )
        st.markdown("#### Recovery Opportunity by Failure Reason")

        recovery_display = recovery_opportunities[[
                "failure_reason",
                "failed_transactions",
                "percentage_of_failures",
                "failed_transaction_value",
                "recovery_rate",
                "estimated_recoverable_value",
                "recommended_action"
            ]].copy()

        recovery_display["recovery_rate"] = (
            recovery_display["recovery_rate"] * 100
        ).round(0).astype(str) + "%"

        recovery_display = recovery_display.rename(
            columns={
                "failure_reason": "Failure Reason",
                "failed_transactions": "Failed Transactions",
                "percentage_of_failures": "Percentage of Failures",
                "failed_transaction_value": "Failed Value",
                "recovery_rate": "Recovery Rate",
                "estimated_recoverable_value": "Estimated Recovery",
                "recommended_action": "Recommended Action",
        
            }
        )

        st.dataframe(
            recovery_display,
            use_container_width=True,
            hide_index=True
        )
        st.markdown("#### Estimated Recovery by Failure Reason")

        recovery_chart_df = recovery_opportunities[
            ["failure_reason", "estimated_recoverable_value"]
        ].set_index("failure_reason")

        st.bar_chart(
            recovery_chart_df
        )
        

    else:
        st.info("No failure reason data available.")

else:
    st.info("No active anomalies to investigate.")
