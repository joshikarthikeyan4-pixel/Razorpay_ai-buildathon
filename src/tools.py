import pandas as pd

from src.db import get_connection


def get_payment_health():
    """Return overall payment health metrics."""

    query = """
    SELECT
        COUNT(*) AS total_transactions,

        COUNT(*) FILTER (
            WHERE status = 'SUCCESS'
        ) AS successful_transactions,

        COUNT(*) FILTER (
            WHERE status = 'FAILED'
        ) AS failed_transactions,

        ROUND(
            100.0 *
            COUNT(*) FILTER (
                WHERE status = 'FAILED'
            ) / COUNT(*),
            2
        ) AS failure_rate,

        ROUND(
            SUM(amount) FILTER (
                WHERE status = 'FAILED'
            ),
            2
        ) AS failed_transaction_value

    FROM public.transactions;
    """

    conn = get_connection()

    try:
        df = pd.read_sql_query(query, conn)

        if df.empty:
            return {}

        return df.to_dict(orient="records")[0]

    finally:
        conn.close()


def get_failure_reasons(bank, payment_method):
    """Return failure reasons for a specific bank/payment combination."""

    query = """
    SELECT
        failure_reason,

        COUNT(*) AS failed_transactions,

        ROUND(
            100.0 *
            COUNT(*) /
            SUM(COUNT(*)) OVER (),
            2
        ) AS percentage_of_failures,

        ROUND(
            SUM(amount),
            2
        ) AS failed_transaction_value

    FROM public.transactions

    WHERE status = 'FAILED'
      AND bank = %s
      AND payment_method = %s

    GROUP BY failure_reason

    ORDER BY failed_transactions DESC;
    """

    conn = get_connection()

    try:
        df = pd.read_sql_query(
            query,
            conn,
            params=(bank, payment_method)
        )

        return df.to_dict(orient="records")

    finally:
        conn.close()


def get_daily_trend(bank=None, payment_method=None):
    """Return daily payment failure trends."""

    query = """
    SELECT
        DATE(timestamp) AS transaction_date,
        COUNT(*) AS total_transactions,
        COUNT(*) FILTER (
            WHERE status = 'FAILED'
        ) AS failed_transactions,
        ROUND(
            100.0 *
            COUNT(*) FILTER (
                WHERE status = 'FAILED'
            ) / COUNT(*),
            2
        ) AS failure_rate
    FROM public.transactions
    """

    conditions = []
    params = []

    if bank:
        conditions.append("bank = %s")
        params.append(bank)

    if payment_method:
        conditions.append("payment_method = %s")
        params.append(payment_method)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += """
        GROUP BY DATE(timestamp)
        ORDER BY transaction_date;
    """

    conn = get_connection()

    try:
        df = pd.read_sql_query(
            query,
            conn,
            params=tuple(params)
        )

        return df.to_dict(orient="records")

    finally:
        conn.close()


def get_active_anomalies():
    """Return currently detected payment anomalies."""

    from src.anomaly import detect_anomalies

    anomalies = detect_anomalies()

    if anomalies.empty:
        return []

    return anomalies.to_dict(orient="records")


if __name__ == "__main__":
    print(f"LOADED TOOLS.PY FROM: {__file__}")