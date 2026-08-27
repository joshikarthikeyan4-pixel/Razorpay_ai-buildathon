# 💳 AI Payment Intelligence

> AI-powered payment failure analytics, anomaly detection, and intelligent investigation for digital payment systems.

## 🎯 Problem Statement

Digital payment platforms process thousands of transactions across multiple banks and payment methods. When payment failures increase, operations teams need to quickly answer questions such as:

- Which bank or payment method is experiencing the problem?
- How severe is the increase in failures?
- What are the dominant reasons behind the failures?
- How much transaction value is being affected?
- Is the failure rate significantly higher than the normal baseline?
- What should the operations team investigate next?

Traditional dashboards often provide raw transaction counts and failure percentages, but they do not always connect these metrics to **actionable investigation**.

### Official Problem Statement

> **[INSERT THE OFFICIAL PROBLEM STATEMENT TEXT HERE]**

Our solution addresses this problem by combining SQL-based payment analytics, anomaly detection, interactive visualization, and a Generative-AI-powered payment analyst.

---

# 💡 My Solution

I built **AI Payment Intelligence**, an interactive analytics and investigation dashboard that connects payment data with automated anomaly detection and AI-assisted investigation.

The system:

1. Connects to a PostgreSQL payment database.
2. Analyzes transaction and failure data using SQL.
3. Calculates payment failure rates and trends.
4. Compares current payment performance against a historical baseline.
5. Detects significant anomalies automatically.
6. Estimates the potential revenue impact of failed transactions.
7. Allows users to filter analysis by bank and payment method.
8. Identifies the dominant failure reasons.
9. Provides an AI Payment Analyst that can investigate incidents and explain the results in natural language.

The goal is not just to show **what happened**, but also help answer:

> **"Why is this happening, how serious is it, and what should we investigate next?"**

---

# ✨ Key Features

## 📊 Payment Health Dashboard

The dashboard provides an overall view of payment performance:

- Total transactions
- Failed transactions
- Overall failure rate
- Failed transaction value

This gives the operations team an immediate understanding of the health of the payment system.

---

## 🎛️ Interactive Filters

Users can filter the analysis by:

### Bank
- BANK_X
- YES_BANK
- SBI
- HDFC
- ICICI
- AXIS
- PNB
- KOTAK

### Payment Method
- UPI
- CARD
- WALLET
- NETBANKING

The charts and incident analysis update according to the selected filters.

This was important because an overall failure rate can hide problems affecting a specific bank/payment-method combination.

---

# 📈 Daily Payment Failure Trend

The dashboard visualizes the daily failure rate using an interactive line chart.

This helps identify:

- Increasing failure rates
- Sudden spikes
- Periods of instability
- Changes in payment behaviour over time

Instead of looking only at a single aggregate number, users can understand how payment reliability changes over time.

---

# 🚨 Automated Anomaly Detection

One of the core components of the system is automated payment anomaly detection.

Instead of using an arbitrary fixed failure-rate threshold, we compare:

### Historical Baseline

The system calculates the historical failure rate for each:

```text
Bank + Payment Method
