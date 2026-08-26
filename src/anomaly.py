import pandas as pd
from src.db import get_connection


RECOVERY_RATE = 0.40


def detect_anomalies():
    query = """
    WITH baseline AS (
        SELECT
            bank,
            payment_method,
            COUNT(*) AS baseline_transactions,
            COUNT(*) FILTER (WHERE status = 'FAILED') AS baseline_failed,
            100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*)
                AS baseline_failure_rate
        FROM public.transactions
        WHERE timestamp < '2026-08-17'
        GROUP BY bank, payment_method
    ),

    current_period AS (
        SELECT
            bank,
            payment_method,
            COUNT(*) AS current_transactions,
            COUNT(*) FILTER (WHERE status = 'FAILED') AS current_failed,
            100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*)
                AS current_failure_rate,
            SUM(amount) FILTER (WHERE status = 'FAILED')
                AS failed_transaction_value
        FROM public.transactions
        WHERE timestamp >= '2026-08-17'
        GROUP BY bank, payment_method
    )

    SELECT
        c.bank,
        c.payment_method,

        c.current_transactions,
        c.current_failed,

        ROUND(c.current_failure_rate, 2)
            AS current_failure_rate,

        ROUND(b.baseline_failure_rate, 2)
            AS baseline_failure_rate,

        ROUND(
            c.current_failure_rate - b.baseline_failure_rate,
            2
        ) AS failure_rate_increase,

        ROUND(
            c.current_failure_rate /
            NULLIF(b.baseline_failure_rate, 0),
            2
        ) AS anomaly_multiplier,

        ROUND(c.failed_transaction_value, 2)
            AS failed_transaction_value

    FROM current_period c

    JOIN baseline b
        ON c.bank = b.bank
        AND c.payment_method = b.payment_method

    WHERE c.current_failure_rate >
          b.baseline_failure_rate * 2

    ORDER BY anomaly_multiplier DESC;
    """

    conn = get_connection()

    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    if df.empty:
        return df

    # Estimated potentially recoverable revenue
    df["estimated_revenue_at_risk"] = (
        df["failed_transaction_value"] * RECOVERY_RATE
    ).round(2)

    # Severity classification
    def classify_severity(multiplier):
        if multiplier >= 4:
            return "CRITICAL"
        elif multiplier >= 3:
            return "HIGH"
        else:
            return "MEDIUM"

    df["severity"] = df["anomaly_multiplier"].apply(
        classify_severity
    )

    return df


if __name__ == "__main__":
    anomalies = detect_anomalies()

    if anomalies.empty:
        print("\n No significant anomalies detected.")
    else:
        print("\n DETECTED ANOMALIES\n")
        print(anomalies.to_string(index=False))