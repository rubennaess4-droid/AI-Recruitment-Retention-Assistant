
import os
import json
import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.set_page_config(
    page_title="Recruitment Retention Assistant",
    page_icon="🤝",
    layout="wide"
)

st.title("🤝 Recruitment Retention Assistant")
st.caption(
    "Decision-support for recruiters: identify early attrition risks, ask better questions, "
    "and plan follow-up. This tool must not be used to automatically reject or rank candidates."
)

with st.expander("Important use policy", expanded=False):
    st.write(
        """
        This prototype estimates **early retention risk**, not candidate quality or employability.
        Recruiters remain responsible for all decisions. Do not enter special-category personal data
        or use this tool to make automatic hiring, rejection, or ranking decisions.
        """
    )

ROLE_RISK = {
    "Customer service / call centre": 2,
    "Outbound sales / telemarketing": 3,
    "Sales": 2,
    "Marketing": 1,
    "Technical / specialist": 0,
    "Other": 1,
}

def calculate_risk(data):
    score = 0
    reasons = []

    if data["relocation_required"]:
        score += 1
        reasons.append("International relocation adds practical and emotional adjustment risk.")

    if data["first_time_abroad"] and data["relocation_required"]:
        score += 2
        reasons.append("This is the candidate's first experience living abroad.")

    savings_points = {
        "Less than 1 month": 3,
        "1–2 months": 2,
        "2–3 months": 1,
        "3+ months": 0,
        "Unknown": 1,
    }[data["financial_buffer"]]
    score += savings_points
    if savings_points >= 2:
        reasons.append("The candidate has a limited financial buffer for relocation/start-up costs.")
    elif data["financial_buffer"] == "Unknown":
        reasons.append("Financial readiness has not yet been verified.")

    score += ROLE_RISK.get(data["role_type"], 1)
    if ROLE_RISK.get(data["role_type"], 1) >= 2:
        reasons.append("The role type is treated as higher-risk because of pressure, workload or pay expectations.")

    expectation_points = {
        "Very clear and realistic": 0,
        "Mostly clear": 1,
        "Some uncertainty": 2,
        "Unclear / overly optimistic": 3,
        "Not checked": 2,
    }[data["expectations"]]
    score += expectation_points
    if expectation_points >= 2:
        reasons.append("Job, salary, destination or lifestyle expectations need stronger alignment.")

    motivation_points = {
        "Strong and specific": 0,
        "Generally positive": 1,
        "Mixed / vague": 2,
        "Mostly destination-driven": 3,
        "Not checked": 2,
    }[data["motivation"]]
    score += motivation_points
    if motivation_points >= 2:
        reasons.append("Motivation is not yet specific enough or may be driven mainly by the destination.")

    readiness_points = {
        "Housing arranged": 0,
        "Actively arranging": 1,
        "No plan yet": 2,
        "Not applicable": 0,
    }[data["housing"]]
    score += readiness_points
    if readiness_points >= 2 and data["relocation_required"]:
        reasons.append("Accommodation planning is not yet sufficiently developed.")

    if data["candidate_has_open_concerns"]:
        score += 2
        reasons.append("The candidate has unresolved concerns that should be discussed before placement.")

    if score <= 4:
        level = "LOW"
    elif score <= 9:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return score, level, reasons

def deterministic_actions(data, level):
    questions = []
    actions = []

    if data["financial_buffer"] in ["Less than 1 month", "1–2 months", "Unknown"]:
        questions.append("How will you cover rent, travel and living costs until your first salary is paid?")
        actions.append("Complete a financial-readiness check before final presentation to the client.")

    if data["relocation_required"] and data["first_time_abroad"]:
        questions.append("What do you expect will be the hardest part of moving abroad, and how would you handle it?")
        actions.append("Discuss relocation reality, support options and a concrete arrival plan.")

    if data["expectations"] != "Very clear and realistic":
        questions.append("What are your expectations about the day-to-day job, salary, schedule and life in the destination?")
        actions.append("Give a realistic job preview and explicitly confirm the candidate's understanding.")

    if data["motivation"] in ["Mixed / vague", "Mostly destination-driven", "Not checked"]:
        questions.append("Why this specific job and employer, apart from the destination itself?")
        actions.append("Re-test job-specific motivation before moving forward.")

    if data["housing"] in ["Actively arranging", "No plan yet"] and data["relocation_required"]:
        questions.append("What is your accommodation plan for the first weeks after arrival?")
        actions.append("Confirm housing status before start date.")

    if data["candidate_has_open_concerns"]:
        questions.append("What would make you reconsider the move or leave within your first three months?")
        actions.append("Resolve the candidate's stated concerns and document the outcome.")

    if not questions:
        questions.append("What could realistically make you leave during the first three months?")
    if not actions:
        actions.append("Maintain expectation alignment and document a normal post-placement follow-up.")

    if level == "HIGH":
        followup = ["Before client presentation", "After offer acceptance", "7 days before start", "Day 3", "Day 14", "Day 30"]
    elif level == "MEDIUM":
        followup = ["After offer acceptance", "7 days before start", "Day 7", "Day 30"]
    else:
        followup = ["After offer acceptance", "Day 7", "Day 30"]

    return questions[:5], actions[:5], followup

def generate_ai_coaching(data, score, level, reasons, questions, actions, followup):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    system = """
You are an internal recruitment retention-support assistant.
Your job is to help a human recruiter reduce early post-placement attrition.

Rules:
- Never recommend rejecting, excluding, ranking, or deprioritising a candidate.
- Never infer protected or sensitive personal traits.
- Treat the provided risk level as retention-support intensity, not candidate quality.
- The rule-based score is authoritative; do not change it.
- Be practical, concise, professional and empathetic.
- Focus on expectation management, financial readiness, relocation readiness,
  screening clarity, trust, realistic job preview and structured post-placement follow-up.
- Highlight what the recruiter should verify or discuss.
"""

    payload = {
        "candidate_case": data,
        "rule_based_score": score,
        "retention_risk_level": level,
        "identified_reasons": reasons,
        "recommended_questions": questions,
        "recommended_actions": actions,
        "follow_up_schedule": followup,
    }

    prompt = f"""
Create a recruiter coaching summary based only on the case below.

{json.dumps(payload, indent=2)}

Return:
1. A 2-3 sentence assessment.
2. The 3 most important recruiter actions.
3. One sentence the recruiter can use to introduce a difficult expectation-management conversation.
4. One short note explaining that this is decision-support, not an automated hiring decision.
"""

    try:
        response = client.responses.create(
            model=model,
            instructions=system,
            input=prompt,
        )
        return response.output_text
    except Exception as e:
        return f"AI coaching unavailable: {e}"

with st.sidebar:
    st.header("Prototype settings")
    st.write("The base risk assessment works without an API key.")
    if os.getenv("OPENAI_API_KEY"):
        st.success("OpenAI API key detected")
    else:
        st.info("No API key detected — rule-based mode is active.")

left, right = st.columns(2)

with left:
    st.subheader("Candidate & role")
    role_type = st.selectbox(
        "Role type",
        list(ROLE_RISK.keys())
    )
    destination = st.text_input("Job destination", placeholder="e.g. Greece")
    relocation_required = st.checkbox("International relocation required", value=True)
    first_time_abroad = st.checkbox("First time living abroad", value=False)

    financial_buffer = st.selectbox(
        "Financial buffer",
        ["Unknown", "Less than 1 month", "1–2 months", "2–3 months", "3+ months"]
    )

with right:
    st.subheader("Readiness & expectations")
    expectations = st.selectbox(
        "Expectation alignment",
        [
            "Not checked",
            "Unclear / overly optimistic",
            "Some uncertainty",
            "Mostly clear",
            "Very clear and realistic",
        ]
    )
    motivation = st.selectbox(
        "Job-specific motivation",
        [
            "Not checked",
            "Mostly destination-driven",
            "Mixed / vague",
            "Generally positive",
            "Strong and specific",
        ]
    )
    housing = st.selectbox(
        "Accommodation readiness",
        ["Not applicable", "No plan yet", "Actively arranging", "Housing arranged"]
    )
    candidate_has_open_concerns = st.checkbox("Candidate has unresolved concerns", value=False)

st.subheader("Recruiter notes")
notes = st.text_area(
    "Optional notes",
    placeholder="Example: Candidate is excited about moving but seems surprised by salary and has not checked rental costs."
)

if st.button("Assess retention support needs", type="primary"):
    data = {
        "role_type": role_type,
        "destination": destination,
        "relocation_required": relocation_required,
        "first_time_abroad": first_time_abroad,
        "financial_buffer": financial_buffer,
        "expectations": expectations,
        "motivation": motivation,
        "housing": housing,
        "candidate_has_open_concerns": candidate_has_open_concerns,
        "recruiter_notes": notes,
    }

    score, level, reasons = calculate_risk(data)
    questions, actions, followup = deterministic_actions(data, level)

    st.divider()
    a, b = st.columns([1, 3])
    with a:
        st.metric("Retention support score", f"{score}")
        if level == "LOW":
            st.success("LOW")
        elif level == "MEDIUM":
            st.warning("MEDIUM")
        else:
            st.error("HIGH")
    with b:
        st.markdown(
            "**Interpretation:** Higher scores mean the placement may need more preparation "
            "and follow-up. The score does **not** indicate whether the candidate should be hired."
        )

    st.subheader("Why this case needs attention")
    for reason in reasons or ["No major predefined retention risk indicators were triggered."]:
        st.write(f"• {reason}")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Questions to ask")
        for q in questions:
            st.write(f"• {q}")

    with c2:
        st.subheader("Recruiter actions")
        for action in actions:
            st.write(f"• {action}")

    st.subheader("Suggested follow-up")
    st.write(" → ".join(followup))

    ai_text = generate_ai_coaching(data, score, level, reasons, questions, actions, followup)
    if ai_text:
        st.subheader("AI recruiter coaching")
        st.write(ai_text)

    st.caption(
        "Prototype logic is intended for research/pilot use. Validate thresholds against historical ATS outcomes "
        "and company feedback before operational deployment."
    )
