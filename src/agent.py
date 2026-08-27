import os
import json
import pandas as pd

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.anomaly import detect_anomalies

from src.tools import (
    get_payment_health,
    get_failure_reasons,
    get_daily_trend,
    get_active_anomalies,
)

from src.recovery import (
    get_recovery_action,
    estimate_recovery,
    build_recovery_opportunities,
)


# --------------------------------------------------
# Gemini setup
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=API_KEY)


# --------------------------------------------------
# Tool definitions
# --------------------------------------------------

tools = [
    types.Tool(
        function_declarations=[

            types.FunctionDeclaration(
                name="get_payment_health",
                description=(
                    "Get overall payment health metrics including "
                    "total transactions, failed transactions, "
                    "failure rate, and failed transaction value."
                ),
                parameters=types.Schema(
                    type="OBJECT",
                    properties={},
                ),
            ),

            types.FunctionDeclaration(
                name="get_failure_reasons",
                description=(
                    "Get failure reasons for a specific bank "
                    "and payment method combination."
                ),
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "bank": types.Schema(
                            type="STRING",
                            description="Bank name, for example BANK_X."
                        ),
                        "payment_method": types.Schema(
                            type="STRING",
                            description="Payment method, for example UPI."
                        ),
                    },
                    required=["bank", "payment_method"],
                ),
            ),

            types.FunctionDeclaration(
                name="get_daily_trend",
                description=(
                    "Get the daily transaction and failure trend "
                    "for a bank and payment method."
                ),
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "bank": types.Schema(
                            type="STRING",
                            description="Bank name."
                        ),
                        "payment_method": types.Schema(
                            type="STRING",
                            description="Payment method."
                        ),
                    },
                    required=["bank", "payment_method"],
                ),
            ),

            types.FunctionDeclaration(
                name="get_active_anomalies",
                description=(
                    "Detect and return currently active payment anomalies "
                    "including affected banks, payment methods, failure rates, "
                    "baselines, anomaly multipliers, severity, and revenue impact."
                ),
                parameters=types.Schema(
                    type="OBJECT",
                    properties={},
                ),
            ),
        ]
    )
]


# --------------------------------------------------
# Execute requested tool
# --------------------------------------------------

def execute_tool(function_name, arguments):

    if function_name == "get_payment_health":
        return get_payment_health()

    elif function_name == "get_failure_reasons":
        return get_failure_reasons(
            arguments["bank"],
            arguments["payment_method"]
        )

    elif function_name == "get_daily_trend":
        return get_daily_trend(
            arguments["bank"],
            arguments["payment_method"]
        )

    elif function_name == "get_active_anomalies":
        return get_active_anomalies()

    return {
        "error": f"Unknown tool: {function_name}"
    }


# --------------------------------------------------
# Build recovery context
# --------------------------------------------------

def build_recovery_context(anomalies):

    if anomalies.empty:
        return []

    recovery_context = []

    for _, anomaly in anomalies.iterrows():

        bank = anomaly["bank"]
        payment_method = anomaly["payment_method"]

        failure_data = get_failure_reasons(
            bank,
            payment_method
        )

        failure_df = pd.DataFrame(failure_data)

        if failure_df.empty:
            continue

        recovery_opportunities = (
            build_recovery_opportunities(
                failure_df
            )
        )

        if recovery_opportunities.empty:
            continue

        recovery_context.append({
            "bank": bank,
            "payment_method": payment_method,
            "recovery_opportunities":
                recovery_opportunities.to_dict(
                    orient="records"
                )
        })

    return recovery_context


# --------------------------------------------------
# AI Payment Analyst
# --------------------------------------------------

def ask_agent(question):

    anomalies = detect_anomalies()

    anomaly_context = (
        anomalies.to_dict(
            orient="records"
        )
        if not anomalies.empty
        else []
    )

    recovery_context = build_recovery_context(
        anomalies
    )

    system_prompt = f"""
You are an AI Payment Operations Analyst.

Your job is to investigate payment incidents using
real transaction data from PostgreSQL.

You have access to tools that query the database.

Detected anomalies currently include:

{json.dumps(anomaly_context, default=str, indent=2)}

Recovery opportunities currently include:

{json.dumps(recovery_context, default=str, indent=2)}


IMPORTANT RULES:

1. Use tools when the question requires transaction data.

2. Never invent metrics.

3. Treat database results as the source of truth.

4. Explain the reasoning behind your conclusion.

5. Distinguish between observed facts and recommendations.

6. Do not claim a technical root cause unless the data supports it.

7. If evidence is insufficient, explicitly say so.

8. Give practical recommendations when appropriate.

9. When discussing revenue recovery, use the provided
   recovery opportunity data.

10. Estimated Recovery Opportunity is calculated as:

    failed transaction value × recovery rate

11. When asked which failure reason has the largest
    recovery opportunity, compare estimated_recoverable_value,
    NOT failed_transaction_value.

12. Prioritize recovery actions based on
    estimated recoverable value.

13. Clearly distinguish:

    Revenue at Risk:
    Failed transaction value exposed to loss.

    Estimated Recovery Opportunity:
    A heuristic estimate of potentially recoverable
    failed transaction value.

14. Never present estimated recovery as guaranteed
    recovered revenue.

15. All monetary values are in Indian Rupees (INR).

16. Always display monetary values using ₹, never $.

17. For FRAUD_CHECK failures, recommend investigation
    or manual review.

18. Do not recommend bypassing, weakening, or
    automatically retrying fraud controls.

19. When asked what the payment operations team should do,
    provide a prioritized action plan based on:

    - observed anomaly
    - failure rate
    - baseline
    - anomaly multiplier
    - dominant failure reasons
    - revenue at risk
    - recovery opportunities

20. Always provide a useful answer when sufficient
    database evidence exists.

21. Never return None or an empty response.

22. Structure operational recommendations as:

    - Immediate action
    - Investigation
    - Recovery action
    - Monitoring / next step

23. When discussing a specific bank and payment method,
    use recovery information for that specific combination
    whenever available.

24. Do not assume that the first anomaly in the dataset
    is the anomaly the user is asking about.

25. If the question does not specify a bank or payment method,
    use the available anomaly data and clearly state
    which incident you are analyzing.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            system_prompt,
            question
        ],
        config=types.GenerateContentConfig(
            tools=tools
        )
    )

    # --------------------------------------------------
    # Check whether Gemini requested a tool
    # --------------------------------------------------

    function_calls = response.function_calls

    if function_calls:

        tool_results = []

        for call in function_calls:

            result = execute_tool(
                call.name,
                call.args
            )

            tool_results.append(
                types.Part.from_function_response(
                    name=call.name,
                    response={
                        "result": result
                    }
                )
            )

        # --------------------------------------------------
        # Send tool results back to Gemini
        # --------------------------------------------------

        final_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                system_prompt,
                question,
                response.candidates[0].content,
                *tool_results
            ],
            config=types.GenerateContentConfig(
                tools=tools
            )
        )

        return final_response.text

    return response.text


# --------------------------------------------------
# Local test
# --------------------------------------------------

if __name__ == "__main__":

    question = (
        "How can we recover the revenue at risk "
        "from BANK_X UPI?"
    )

    answer = ask_agent(question)

    print("\n🤖 AI PAYMENT ANALYST\n")
    print(answer)