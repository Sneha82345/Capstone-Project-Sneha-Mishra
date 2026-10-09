import json
import os
import calendar
from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"   # if "model not found", use the Flash model listed in AI Studio


def month_name(month_text):
    return calendar.month_name[int(month_text.split("-")[1])]   # "2026-03" -> "March"


# ---------------- TASK 4: offline fallback ----------------
def generate_scr_narrative_offline(findings):
    rr = findings["return_rate_by_payment"]
    seg = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    infl = findings["outlier_inflated_month"]

    narrative = (
        "SITUATION\n"
        f"After cleaning the order data, Mamaearth's verified revenue is INR "
        f"{findings['cleaned_total_revenue_inr']:,.2f}. This is INR "
        f"{findings['duplicate_reconciliation_delta_inr']:,.2f} lower than the raw figure of INR "
        f"{findings['raw_total_revenue_inr']:,.2f}, because of duplicate double-submit orders.\n\n"
        "COMPLICATION\n"
        f"Cash on Delivery returns at {rr['COD']}% compared with {rr['CARD']}% for Card and "
        f"{rr['UPI']}% for UPI. The highest-risk segment is {seg['payment_method']} in "
        f"Tier-{seg['city_tier']} cities at {seg['return_rate_pct']}%. "
        f"{month_name(infl['month'])} looked like the best month "
        f"(INR {infl['apparent_revenue_inr']:,.2f}) only because of two bulk orders; without them "
        f"it is INR {infl['corrected_revenue_inr']:,.2f}, and {month_name(peak['month'])} is the "
        f"true peak at INR {peak['revenue_inr']:,.2f}.\n\n"
        "RESOLUTION\n"
        f"Add stronger controls for {seg['payment_method']} orders in Tier-{seg['city_tier']} "
        f"cities, block duplicate submissions at checkout, and plan campaigns around the "
        f"{month_name(peak['month'])} peak."
    )
    return {"status": "success", "narrative": narrative, "tokens": 0}


# ---------------- TASK 2 + 3: main function ----------------
def generate_scr_narrative(findings):
    # Task 4: no API key -> offline path
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return generate_scr_narrative_offline(findings)

    # Task 2: system instruction (role + structure + no invented numbers)
    system_instruction = (
        "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
        "Write a narrative of about 250 words with exactly three labeled sections: "
        "Situation, Complication, Resolution. "
        "Every number in your output must come from the supplied findings and appear with "
        "the same value. Do not invent any statistics."
    )

    # Task 2: user prompt, interpolated from the findings argument
    rr = findings["return_rate_by_payment"]
    seg = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    infl = findings["outlier_inflated_month"]
    prompt = (
        "Write the narrative using only these findings:\n"
        f"- Cleaned total revenue: INR {findings['cleaned_total_revenue_inr']:,.2f}\n"
        f"- Raw total revenue: INR {findings['raw_total_revenue_inr']:,.2f}\n"
        f"- Duplicate reconciliation delta: INR {findings['duplicate_reconciliation_delta_inr']:,.2f}\n"
        f"- Return rate by payment method (%): {rr}\n"
        f"- Highest-risk segment: {seg['payment_method']}, Tier-{seg['city_tier']} cities, "
        f"{seg['return_rate_pct']}%\n"
        f"- True peak month: {month_name(peak['month'])}, INR {peak['revenue_inr']:,.2f}\n"
        f"- {month_name(infl['month'])} looked highest at INR {infl['apparent_revenue_inr']:,.2f} "
        f"but is INR {infl['corrected_revenue_inr']:,.2f} after removing two bulk orders\n"
    )

    # Task 3: whole call inside try/except, dict returned in both branches
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(          # Task 2: the API call
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                # temperature 0.0: factual business report, not creative writing,
                # so we want deterministic output with no embellishment.
                temperature=0.0,
                max_output_tokens=2048,                         # explicit, at least 300
                thinking_config=types.ThinkingConfig(thinking_budget=0),  # keeps tokens for the text
                http_options=types.HttpOptions(timeout=30000),  # 30,000 ms = 30 s (at least 10 s)
            ),
        )
        result = {"status": "success",
                  "narrative": response.text,
                  "tokens": response.usage_metadata.total_token_count}
    except Exception as err:
        result = {"status": "error", "narrative": None, "message": str(err)}

    # Task 4: API error -> offline path
    if result["status"] == "error":
        print("API error:", result["message"], "-> using offline narrative")
        return generate_scr_narrative_offline(findings)

    return result


# ---------------- TASK 5: checker ----------------
def check_figures(narrative, findings):
    text = narrative.replace(",", "")   # normalize commas: 97,358.30 -> 97358.30

    checks = {
        "97,358.30 (cleaned total revenue)": "97358.3" in text,
        "44.4 (COD return rate)": "44.4" in text,
        "54.5 (COD + Tier-2 rate)": "54.5" in text,
        "2,501.90 (duplicate delta)": "2501.9" in text,
        "March + 20,318.90 (true peak)": ("March" in narrative) and ("20318.9" in text),
    }
    for name, ok in checks.items():
        print("PASS" if ok else "FAIL", "-", name)
    return all(checks.values())


# ---------------- Run ----------------
if __name__ == "__main__":
    with open("narrator/findings.json") as f:
        findings = json.load(f)

    result = generate_scr_narrative(findings)
    print(result["narrative"])
    print("\nTokens:", result["tokens"])
    print("\nChecker:")
    all_ok = check_figures(result["narrative"], findings)

    # Save the Gemini output as the sample (tokens > 0 means it came from Gemini, not offline)
    if all_ok and result["tokens"] > 0:
        with open("narrator/sample_output.txt", "w") as f:
            f.write(result["narrative"])
        print("\nSaved narrator/sample_output.txt")
