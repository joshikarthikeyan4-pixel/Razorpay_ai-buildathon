SELECT COUNT(*) AS total_transactions
FROM public.;

SELECT
    status,
    COUNT(*) AS transaction_count
FROM public.transactions
GROUP BY status
ORDER BY transaction_count DESC;

SELECT
    COUNT(*) FILTER (WHERE transaction_id IS NULL) AS transaction_id_nulls,
    COUNT(*) FILTER (WHERE timestamp IS NULL) AS timestamp_nulls,
    COUNT(*) FILTER (WHERE merchant_id IS NULL) AS merchant_id_nulls,
    COUNT(*) FILTER (WHERE amount IS NULL) AS amount_nulls,
    COUNT(*) FILTER (WHERE payment_method IS NULL) AS payment_method_nulls,
    COUNT(*) FILTER (WHERE bank IS NULL) AS bank_nulls,
    COUNT(*) FILTER (WHERE status IS NULL) AS status_nulls,
    COUNT(*) FILTER (WHERE failure_reason IS NULL) AS failure_reason_nulls
FROM public.transactions;

SELECT
    bank,
    payment_method,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*),
        2
    ) AS failure_rate
FROM public.transactions
GROUP BY bank, payment_method
ORDER BY failure_rate DESC;

-- Overall payment success and failure performance
SELECT
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE status = 'SUCCESS') AS successful_transactions,
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'SUCCESS') / COUNT(*),
        2
    ) AS success_rate,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*),
        2
    ) AS failure_rate
FROM public.transactions;

-- Daily payment performance to identify changes and anomalies
SELECT
    DATE(timestamp) AS transaction_date,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE status = 'SUCCESS') AS successful_transactions,
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*),
        2
    ) AS failure_rate
FROM public.transactions
GROUP BY DATE(timestamp)
ORDER BY transaction_date;

-- Compare payment failure rates across banks
SELECT
    bank,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*),
        2
    ) AS failure_rate
FROM public.transactions
GROUP BY bank
ORDER BY failure_rate DESC;

-- Compare payment failures across payment methods
SELECT
    payment_method,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*),
        2
    ) AS failure_rate
FROM public.transactions
GROUP BY payment_method
ORDER BY failure_rate DESC;

-- Identify high-risk bank + payment method combinations
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

-- Calculate transaction value associated with failed payments
SELECT
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
    ROUND(
        SUM(amount) FILTER (WHERE status = 'FAILED'),
        2
    ) AS failed_transaction_value
FROM public.transactions;

-- Compare BANK_X + UPI failure rates before and during the anomaly
SELECT
    CASE
        WHEN timestamp < '2026-08-17' THEN 'Before anomaly'
        ELSE 'During anomaly'
    END AS period,
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
WHERE bank = 'BANK_X'
  AND payment_method = 'UPI'
GROUP BY period
ORDER BY period;

-- Analyze the reasons behind failed payments
SELECT
    failure_reason,
    COUNT(*) AS failed_transactions,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage_of_failures,
    ROUND(
        SUM(amount),
        2
    ) AS failed_transaction_value
FROM public.transactions
WHERE status = 'FAILED'
GROUP BY failure_reason
ORDER BY failed_transactions DESC;

-- Analyze failure reasons specifically for the BANK_X + UPI segment
SELECT
    failure_reason,
    COUNT(*) AS failed_transactions,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage_of_failures,
    ROUND(
        SUM(amount),
        2
    ) AS failed_transaction_value
FROM public.transactions
WHERE status = 'FAILED'
  AND bank = 'BANK_X'
  AND payment_method = 'UPI'
GROUP BY failure_reason
ORDER BY failed_transactions DESC;

-- Analyze failure reasons specifically for the BANK_X + UPI segment
SELECT
    failure_reason,
    COUNT(*) AS failed_transactions,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage_of_failures,
    ROUND(SUM(amount), 2) AS failed_transaction_value
FROM public.transactions
WHERE status = 'FAILED'
  AND bank = 'BANK_X'
  AND payment_method = 'UPI'
GROUP BY failure_reason
ORDER BY failed_transactions DESC;

-- Identify merchants with unusually high payment failure rates
SELECT
    merchant_id,
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
GROUP BY merchant_id
HAVING COUNT(*) >= 100
ORDER BY failure_rate DESC
LIMIT 20;

-- Identify merchants most affected by the BANK_X + UPI anomaly
SELECT
    merchant_id,
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
WHERE bank = 'BANK_X'
  AND payment_method = 'UPI'
  AND timestamp >= '2026-08-17'
GROUP BY merchant_id
ORDER BY failure_rate DESC, total_transactions DESC
LIMIT 15;

-- Analyze payment failures by hour of day
SELECT
    EXTRACT(HOUR FROM timestamp)::INT AS hour_of_day,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*),
        2
    ) AS failure_rate
FROM public.transactions
GROUP BY EXTRACT(HOUR FROM timestamp)
ORDER BY hour_of_day;

-- Analyze payment failures across transaction amount ranges
SELECT
    CASE
        WHEN amount < 500 THEN '< ₹500'
        WHEN amount < 1000 THEN '₹500–₹999'
        WHEN amount < 5000 THEN '₹1,000–₹4,999'
        WHEN amount < 10000 THEN '₹5,000–₹9,999'
        ELSE '₹10,000+'
    END AS amount_range,
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
GROUP BY amount_range
ORDER BY MIN(amount);

-- Track BANK_X + UPI failures over time
SELECT
    DATE(timestamp) AS transaction_date,
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
WHERE bank = 'BANK_X'
  AND payment_method = 'UPI'
GROUP BY DATE(timestamp)
ORDER BY transaction_date;

-- Detect daily anomalies in bank + payment method combinations
WITH daily_metrics AS (
    SELECT
        DATE(timestamp) AS transaction_date,
        bank,
        payment_method,
        COUNT(*) AS total_transactions,
        COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
        100.0 * COUNT(*) FILTER (WHERE status = 'FAILED') / COUNT(*) AS failure_rate
    FROM public.transactions
    GROUP BY DATE(timestamp), bank, payment_method
),

baseline AS (
    SELECT
        bank,
        payment_method,
        AVG(failure_rate) AS avg_failure_rate,
        STDDEV_POP(failure_rate) AS std_failure_rate
    FROM daily_metrics
    GROUP BY bank, payment_method
)

SELECT
    d.transaction_date,
    d.bank,
    d.payment_method,
    d.total_transactions,
    d.failed_transactions,
    ROUND(d.failure_rate, 2) AS failure_rate,
    ROUND(b.avg_failure_rate, 2) AS baseline_failure_rate,
    ROUND(
        (d.failure_rate - b.avg_failure_rate)
        / NULLIF(b.std_failure_rate, 0),
        2
    ) AS anomaly_score
FROM daily_metrics d
JOIN baseline b
    ON d.bank = b.bank
    AND d.payment_method = b.payment_method
WHERE b.std_failure_rate > 0
  AND (
      (d.failure_rate - b.avg_failure_rate)
      / b.std_failure_rate
  ) >= 3
ORDER BY anomaly_score DESC;

-- Estimate potentially recoverable revenue from failed transactions
SELECT
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
    ROUND(
        SUM(amount) FILTER (WHERE status = 'FAILED'),
        2
    ) AS failed_transaction_value,
    0.40 AS assumed_recovery_rate,
    ROUND(
        SUM(amount) FILTER (WHERE status = 'FAILED') * 0.40,
        2
    ) AS estimated_revenue_at_risk
FROM public.transactions;

-- Estimate revenue at risk specifically for the BANK_X + UPI anomaly
SELECT
    COUNT(*) AS transactions,
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_transactions,
    ROUND(
        SUM(amount) FILTER (WHERE status = 'FAILED'),
        2
    ) AS failed_transaction_value,
    0.40 AS assumed_recovery_rate,
    ROUND(
        SUM(amount) FILTER (WHERE status = 'FAILED') * 0.40,
        2
    ) AS estimated_revenue_at_risk
FROM public.transactions
WHERE bank = 'BANK_X'
  AND payment_method = 'UPI'
  AND timestamp >= '2026-08-17';

-- Create a reusable payment health view for downstream AI analytics
CREATE OR REPLACE VIEW public.payment_health AS
SELECT
    DATE(timestamp) AS transaction_date,
    bank,
    payment_method,
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
FROM public.transactions
GROUP BY
    DATE(timestamp),
    bank,
    payment_method;

	SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'transactions'
ORDER BY ordinal_position;

SELECT
    failure_reason,
    COUNT(*) AS failed_transactions,
    ROUND(SUM(amount), 2) AS failed_value
FROM public.transactions
WHERE status = 'FAILED'
GROUP BY failure_reason
ORDER BY failed_value DESC;

SELECT
    payment_method,
    failure_reason,
    COUNT(*) AS failed_transactions,
    ROUND(SUM(amount), 2) AS failed_value
FROM public.transactions
WHERE status = 'FAILED'
GROUP BY payment_method, failure_reason
ORDER BY failed_value DESC;
	

	