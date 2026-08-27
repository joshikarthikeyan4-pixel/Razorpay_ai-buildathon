import pandas as pd


def get_recovery_action(failure_reason):
    """
    Return the recommended recovery action
    based on the payment failure reason.
    """

    actions = {
        "NETWORK_ERROR": {
            "action": "CONTROLLED_RETRY",
            "recommendation": (
                "Retry with exponential backoff after confirming the previous attempt did not succeed."
            )
        },

        "TIMEOUT": {
            "action": "CONTROLLED_RETRY",
            "recommendation": (
                "Retry with safeguards after confirming the previous attempt did not succeed."
            )
        },

        "BANK_DECLINE": {
            "action": "ALTERNATIVE_METHOD",
            "recommendation": (
                "Suggest an alternative payment method "
                "or retry through another route."
            )
        },

        "INSUFFICIENT_FUNDS": {
            "action": "ALTERNATIVE_METHOD",
            "recommendation": (
                "Suggest an alternative payment method."
            )
        },

        "LIMIT_EXCEEDED": {
            "action": "ALTERNATIVE_METHOD",
            "recommendation": (
                "Suggest another payment instrument "
                "or payment method."
            )
        },

        "FRAUD_CHECK": {
            "action": "MANUAL_REVIEW",
            "recommendation": (
                "Do not automatically retry. "
                "Route the transaction for fraud/risk review."
            )
        }
    }

    return actions.get(
        failure_reason,
        {
            "action": "INVESTIGATE",
            "recommendation": (
                "Investigate the failure reason "
                "before attempting recovery."
            )
        }
    )


def estimate_recovery(failure_reason, failed_value):
    """
    Estimate potentially recoverable revenue based
    on the type of payment failure.

    These recovery rates are heuristic assumptions
    used for opportunity estimation, not guaranteed
    recovery outcomes.
    """

    recovery_rates = {
        "NETWORK_ERROR": 0.70,
        "TIMEOUT": 0.65,
        "BANK_DECLINE": 0.40,
        "INSUFFICIENT_FUNDS": 0.25,
        "LIMIT_EXCEEDED": 0.30,
        "FRAUD_CHECK": 0.05,
    }

    rate = recovery_rates.get(
        failure_reason,
        0.20
    )

    estimated_recovery = failed_value * rate

    return {
        "recovery_rate": rate,
        "estimated_recoverable_value": round(
            estimated_recovery,
            2
        )
    }


def build_recovery_opportunities(failure_df):
    """
    Calculate recovery opportunities for
    every failure reason.
    """

    if failure_df.empty:
        return failure_df

    recovery_rows = []

    for _, row in failure_df.iterrows():

        failure_reason = row["failure_reason"]

        failed_value = row["failed_transaction_value"]

        recovery = get_recovery_action(
            failure_reason
        )

        estimate = estimate_recovery(
            failure_reason,
            failed_value
        )

        recovery_rows.append({
            "failure_reason": failure_reason,
            "failed_transactions": row[
                "failed_transactions"
            ],
            "percentage_of_failures": row[
                "percentage_of_failures"],
            "failed_transaction_value": failed_value,
            "recovery_rate": estimate[
                "recovery_rate"
            ],
            "estimated_recoverable_value": estimate[
                "estimated_recoverable_value"
            ],
            "recommended_action": recovery[
                "action"
            ]
        })

    return pd.DataFrame(
        recovery_rows
    )

