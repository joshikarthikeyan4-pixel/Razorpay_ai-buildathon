import pandas as pd

from src.db import get_connection


def get_payment_summary():
    query = """
    SELECT
        COUNT(*) AS total_transactions,
        COUNT(*) FILTER (WHERE status = 'SUCCESS') AS successful_transactions,
        COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*),
            2
        ) AS failure_rate,
        ROUND(
            SUM(amount) FILTER (WHERE status = 'FAILED'),
            2
        ) AS failed_transaction_value
    FROM public.transactions;
    """

    conn = get_connection()

    try:
        df = pd.read_sql_query(query, conn)
        return df

    finally:
        conn.close()


def get_bank_payment_analysis():
    query = """
    SELECT
        bank,
        payment_method,
        COUNT(*) AS total_transactions,
        COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*),
            2
        ) AS failure_rate,
        ROUND(
            SUM(amount) FILTER (WHERE status = 'FAILED'),
            2
        ) AS failed_transaction_value
    FROM public.transactions
    GROUP BY bank, payment_method
    ORDER BY failure_rate DESC;
    """

    conn = get_connection()

    try:
        df = pd.read_sql_query(query, conn)
        return df

    finally:
        conn.close()


if __name__ == "__main__":
    print("\n📊 PAYMENT SUMMARY\n")
    print(get_payment_summary())

    print("\n🏦 BANK + PAYMENT METHOD ANALYSIS\n")
    print(get_bank_payment_analysis())