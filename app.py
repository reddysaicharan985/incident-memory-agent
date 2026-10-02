import hashlib
import hmac
import html
import os
import re
from datetime import date, datetime, timezone

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight


load_dotenv()

st.set_page_config(
    page_title="Incident Memory Agent",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# Claude-inspired interface
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
        :root {
            --canvas: #f7f6f2;
            --sidebar: #efede7;
            --surface: #fffdfa;
            --surface-2: #f2f0ea;
            --ink: #25241f;
            --muted: #6f6b62;
            --line: #ddd8ce;
            --accent: #d97757;
            --accent-dark: #b8583e;
            --accent-soft: #f1ddd4;
            --green: #3f7455;
            --green-soft: #deeee3;
            --yellow-soft: #f7efc9;
            --red-soft: #f5ded9;
        }

        html, body, [class*="css"] {
            font-family: Inter, ui-sans-serif, -apple-system,
                BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp {
            background: var(--canvas);
            color: var(--ink);
        }

        [data-testid="stHeader"] {
            background: rgba(247, 246, 242, 0.92);
            border-bottom: 1px solid var(--line);
        }

        [data-testid="stSidebar"] {
            background: var(--sidebar);
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.15rem;
        }

        [data-testid="stSidebar"] * {
            color: var(--ink);
        }

        .block-container {
            max-width: 1220px;
            padding-top: 2.5rem;
            padding-bottom: 5rem;
        }

        h1, h2, h3, h4 {
            color: var(--ink) !important;
            letter-spacing: -0.025em;
        }

        p, label, .stCaption {
            color: var(--muted);
        }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 0.2rem 0 1.65rem;
            padding-bottom: 1.25rem;
            border-bottom: 1px solid var(--line);
        }

        .brand-mark {
            width: 38px;
            height: 38px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            background: var(--accent);
            color: white !important;
            font-size: 1.2rem;
            font-weight: 800;
        }

        .brand-title {
            font-size: 1.03rem;
            font-weight: 750;
            color: var(--ink) !important;
        }

        .brand-subtitle {
            margin-top: 0.08rem;
            font-size: 0.72rem;
            color: var(--muted) !important;
        }

        .nav-label {
            margin: 0 0 0.55rem 0.15rem;
            color: #8a857b !important;
            font-size: 0.65rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] {
            gap: 0.34rem;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] > label {
            min-height: 42px;
            margin: 0;
            padding: 0.62rem 0.72rem;
            border: 1px solid transparent;
            border-radius: 11px;
            transition: background 120ms ease, border-color 120ms ease;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
            border-color: var(--line);
            background: rgba(255, 253, 250, 0.62);
        }

        [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
            border-color: #e8cabc;
            background: var(--accent-soft);
        }

        [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
            color: var(--accent-dark) !important;
            font-weight: 760;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
            display: none;
        }

        .status-card {
            margin-top: 1.65rem;
            padding: 1rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: rgba(255, 253, 250, 0.82);
            box-shadow: 0 5px 16px rgba(54, 46, 34, 0.035);
        }

        .status-online {
            font-size: 0.82rem;
            font-weight: 750;
            color: var(--green) !important;
        }

        .status-caption {
            margin-top: 0.35rem;
            font-size: 0.72rem;
            color: var(--muted) !important;
            overflow-wrap: anywhere;
        }

        .status-row {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            margin-top: 0.65rem;
            padding-top: 0.65rem;
            border-top: 1px solid var(--line);
            font-size: 0.71rem;
        }

        .status-row span:first-child {
            color: #8a857b !important;
        }

        .status-row span:last-child {
            max-width: 155px;
            color: var(--ink) !important;
            font-weight: 650;
            text-align: right;
            overflow-wrap: anywhere;
        }

        .safety-note {
            display: flex;
            gap: 0.65rem;
            margin-top: 0.85rem;
            padding: 0.78rem 0.85rem;
            border-radius: 12px;
            background: #e8e5de;
            color: var(--muted) !important;
            font-size: 0.7rem;
            line-height: 1.5;
        }

        .safety-icon {
            color: var(--green) !important;
            font-weight: 850;
        }

        .feedback-progress {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.65rem;
            margin-bottom: 1.1rem;
        }

        .feedback-progress-item {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.72rem 0.8rem;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: #faf8f4;
            color: var(--muted) !important;
            font-size: 0.75rem;
            font-weight: 700;
        }

        .feedback-progress-item.done {
            border-color: #bed8c6;
            background: var(--green-soft);
            color: var(--green) !important;
        }

        .progress-number {
            display: inline-flex;
            width: 25px;
            height: 25px;
            flex: 0 0 25px;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: #e7e3da;
            color: var(--muted) !important;
            font-size: 0.7rem;
        }

        .feedback-progress-item.done .progress-number {
            background: var(--green);
            color: white !important;
        }

        .feedback-card-title {
            margin: 0.2rem 0 0.15rem;
            color: var(--ink) !important;
            font-size: 0.9rem;
            font-weight: 780;
        }

        .feedback-card-copy {
            margin: 0 0 0.75rem;
            color: var(--muted) !important;
            font-size: 0.73rem;
            line-height: 1.5;
        }

        .feedback-complete {
            margin-top: 1rem;
            padding: 0.9rem 1rem;
            border: 1px solid #bed8c6;
            border-radius: 12px;
            background: var(--green-soft);
            color: var(--green) !important;
            font-size: 0.79rem;
            font-weight: 720;
        }

        .eyebrow {
            margin-bottom: 0.75rem;
            color: var(--accent) !important;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }

        .hero {
            max-width: 820px;
            margin-bottom: 2rem;
        }

        .hero h1 {
            margin: 0;
            font-family: Georgia, "Times New Roman", serif;
            font-size: clamp(2.25rem, 5vw, 4.35rem);
            font-weight: 500;
            line-height: 1.02;
        }

        .hero p {
            max-width: 720px;
            margin-top: 1rem;
            font-size: 1.03rem;
            line-height: 1.7;
        }

        .section-head {
            margin: 2rem 0 1rem;
        }

        .section-head h2 {
            margin-bottom: 0.3rem;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 2rem;
            font-weight: 500;
        }

        .panel {
            height: 100%;
            padding: 1.25rem;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: var(--surface);
            box-shadow: 0 5px 18px rgba(54, 46, 34, 0.035);
        }

        .panel h3 {
            margin: 0.2rem 0 0.45rem;
            font-size: 1.05rem;
        }

        .panel p {
            margin: 0;
            line-height: 1.6;
        }

        .step-number {
            display: inline-flex;
            width: 31px;
            height: 31px;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.65rem;
            border-radius: 9px;
            background: var(--accent-soft);
            color: var(--accent-dark);
            font-weight: 800;
        }

        .tag {
            display: inline-block;
            margin-bottom: 0.7rem;
            padding: 0.32rem 0.68rem;
            border-radius: 999px;
            font-size: 0.69rem;
            font-weight: 800;
            letter-spacing: 0.065em;
            text-transform: uppercase;
        }

        .tag-neutral {
            background: #ebe8e1;
            color: #666159;
        }

        .tag-accent {
            background: var(--accent-soft);
            color: var(--accent-dark);
        }

        .tag-success {
            background: var(--green-soft);
            color: var(--green);
        }

        .memory-card {
            margin-bottom: 0.8rem;
            padding: 1rem 1.05rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: var(--surface-2);
            color: var(--ink);
            line-height: 1.58;
        }

        .memory-card-title {
            margin-bottom: 0.4rem;
            color: var(--accent-dark);
            font-size: 0.71rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .callout {
            padding: 1rem 1.1rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: var(--surface);
        }

        .callout strong {
            color: var(--ink);
        }

        div[data-testid="stForm"] {
            padding: 1.35rem;
            border: 1px solid var(--line);
            border-radius: 20px;
            background: var(--surface);
            box-shadow: 0 5px 18px rgba(54, 46, 34, 0.035);
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"],
        textarea {
            border-color: var(--line) !important;
            border-radius: 12px !important;
            background: #fbfaf7 !important;
            color: var(--ink) !important;
        }

        input, textarea {
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
        }

        input::placeholder, textarea::placeholder {
            color: #9b978e !important;
            -webkit-text-fill-color: #9b978e !important;
        }

        div[data-baseweb="select"] span {
            color: var(--ink) !important;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            min-height: 44px;
            border: 1px solid var(--accent);
            border-radius: 12px;
            background: var(--accent);
            color: white !important;
            font-weight: 720;
            box-shadow: none;
        }

        .stButton > button p,
        .stFormSubmitButton > button p {
            color: white !important;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            border-color: var(--accent-dark);
            background: var(--accent-dark);
        }

        div[data-testid="stMetric"] {
            min-height: 112px;
            padding: 1rem;
            border: 1px solid var(--line);
            border-radius: 15px;
            background: var(--surface);
        }

        div[data-testid="stMetricLabel"] p {
            color: var(--muted) !important;
        }

        div[data-testid="stMetricValue"] {
            color: var(--ink) !important;
            font-family: Georgia, "Times New Roman", serif;
        }

        [data-testid="stAlert"] {
            border-radius: 14px;
        }

        code {
            color: var(--ink) !important;
            background: var(--surface-2) !important;
        }

        .footer-note {
            margin-top: 2rem;
            font-size: 0.74rem;
            line-height: 1.55;
            color: var(--muted) !important;
        }

        @media (max-width: 760px) {
            .block-container {
                padding-top: 1.5rem;
            }

            .hero h1 {
                font-size: 2.35rem;
            }

            .feedback-progress {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Configuration and session state
# -----------------------------------------------------------------------------

def get_setting(name: str):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets[name]
    except Exception:
        return None


HINDSIGHT_API_URL = get_setting("HINDSIGHT_API_URL")
HINDSIGHT_API_KEY = get_setting("HINDSIGHT_API_KEY")
HINDSIGHT_BANK_ID = get_setting("HINDSIGHT_BANK_ID")
GROQ_API_KEY = get_setting("GROQ_API_KEY")
ADMIN_PASSWORD = get_setting("ADMIN_PASSWORD")
GROQ_MODEL = get_setting("GROQ_MODEL") or "openai/gpt-oss-120b"

required_settings = {
    "HINDSIGHT_API_URL": HINDSIGHT_API_URL,
    "HINDSIGHT_API_KEY": HINDSIGHT_API_KEY,
    "HINDSIGHT_BANK_ID": HINDSIGHT_BANK_ID,
    "GROQ_API_KEY": GROQ_API_KEY,
}

missing_settings = [
    name for name, value in required_settings.items() if not value
]

if missing_settings:
    st.error("Missing configuration: " + ", ".join(missing_settings))
    st.info(
        "Add the missing values to `.env` locally or to your deployment "
        "secrets. Never commit real keys to GitHub."
    )
    st.stop()


SESSION_DEFAULTS = {
    "investigation_result": None,
    "investigation_count": 0,
    "feedback_count": 0,
    "last_feedback": None,
    "relevance_feedback_saved": False,
    "outcome_feedback_saved": False,
}

for session_key, default_value in SESSION_DEFAULTS.items():
    if session_key not in st.session_state:
        st.session_state[session_key] = default_value


# -----------------------------------------------------------------------------
# Utilities and agent services
# -----------------------------------------------------------------------------

SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(password\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+"), r"\1[REDACTED]"),
    (re.compile(r"\b(gsk|sk|hsk)_[A-Za-z0-9_\-]{12,}\b"), "[REDACTED_API_KEY]"),
]


def redact_sensitive_text(value: str) -> str:
    cleaned = value.strip()
    for pattern, replacement in SECRET_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


def new_hindsight_client() -> Hindsight:
    return Hindsight(
        base_url=HINDSIGHT_API_URL,
        api_key=HINDSIGHT_API_KEY,
    )


def recall_memories(query: str, limit: int = 6) -> list[dict]:
    client = new_hindsight_client()
    try:
        response = client.recall(
            bank_id=HINDSIGHT_BANK_ID,
            query=redact_sensitive_text(query),
        )
        results = []
        for item in response.results[:limit]:
            results.append(
                {
                    "text": getattr(item, "text", ""),
                    "type": getattr(item, "type", None),
                    "context": getattr(item, "context", None),
                    "document_id": getattr(item, "document_id", None),
                }
            )
        return results
    finally:
        client.close()


def retain_memory(content: str) -> None:
    client = new_hindsight_client()
    try:
        client.retain(
            bank_id=HINDSIGHT_BANK_ID,
            content=redact_sensitive_text(content),
        )
    finally:
        client.close()


def ask_groq(system_message: str, prompt: str, max_tokens: int) -> str:
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_completion_tokens=max_tokens,
    )
    return response.choices[0].message.content


def generate_baseline_brief(current_incident: str) -> str:
    prompt = f"""
CURRENT INCIDENT:
{current_incident}

Create a concise software incident investigation brief using only the current
incident information.

STRICT RULES:
- Do not use or assume historical incident knowledge.
- Include only facts explicitly provided.
- Mark missing scope, logs, impact, actions and root cause as unknown.
- Never invent facts, logs, causes, systems or completed actions.
- Recommend exactly three general investigation steps.
- Use concise Markdown bullets.
- Keep the answer below 350 words.

Use these sections:
1. Confirmed current facts
2. Unknown information
3. Top three general investigation steps
4. Uncertainty warning
"""
    return ask_groq(
        "You are a careful software incident-response assistant with no "
        "historical memory. Never invent operational facts.",
        prompt,
        850,
    )


def generate_memory_brief(current_incident: str, memories: list[dict]) -> str:
    if memories:
        memory_context = "\n\n".join(
            f"MEMORY {index}:\n{item['text']}"
            for index, item in enumerate(memories, start=1)
        )
    else:
        memory_context = "No historical memories were retrieved."

    prompt = f"""
CURRENT INCIDENT:
{current_incident}

RETRIEVED MEMORY CANDIDATES:
{memory_context}

Create a concise, evidence-grounded software incident investigation brief.

STRICT RULES:
- Current facts must contain only information explicitly provided in CURRENT
  INCIDENT.
- Historical memories are evidence, never proof of the current root cause.
- Evaluate whether each memory is genuinely applicable using service,
  environment, symptoms, recent changes, confirmed outcome and contradictions.
- Use only applicable memories in the historical-evidence section.
- Mention misleading but superficially similar memories only in the memory
  applicability section and explain why they were rejected.
- Merge overlapping fragments that describe the same historical incident.
- Never invent facts, logs, causes, systems, users or completed actions.
- If no memory is applicable, say so clearly and provide cautious steps.
- Use concise Markdown bullets and keep the answer below 500 words.

Use these sections:
1. Confirmed current facts
2. Unknown information
3. Memory applicability
4. Relevant historical evidence
5. Top three investigation steps
6. Uncertainty warning
"""
    return ask_groq(
        "You are a careful incident-response agent. Historical memory is "
        "supporting evidence, never proof. Reject false-friend memories.",
        prompt,
        1200,
    )


def investigation_fingerprint(service: str, details: str) -> str:
    value = f"{service.lower()}::{details.lower()}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()[:12]


def save_feedback(category: str, label: str, notes: str = "") -> None:
    result = st.session_state.get("investigation_result")
    if not result:
        raise RuntimeError("Run an investigation before recording feedback.")

    content = f"""
Incident investigation feedback.

Recorded at: {datetime.now(timezone.utc).isoformat()}
Investigation ID: {result['investigation_id']}
Service: {result['service']}
Environment: {result['environment']}
Severity: {result['severity']}
Current incident: {result['current_incident']}
Feedback category: {category}
Feedback result: {label}
Engineer notes: {notes.strip() or 'Not provided'}

This feedback was explicitly provided by the human operator and should guide
future use of similar incident memories.
""".strip()

    retain_memory(content)
    st.session_state["feedback_count"] += 1
    st.session_state["last_feedback"] = f"{category}: {label}"


def safe_html(value) -> str:
    return html.escape(str(value or ""))


def render_memory_cards(memories: list[dict]) -> None:
    if not memories:
        st.info("No historical memory candidates were retrieved.")
        return

    for index, item in enumerate(memories, start=1):
        metadata = []
        if item.get("type"):
            metadata.append(str(item["type"]))
        if item.get("document_id"):
            metadata.append(str(item["document_id"]))
        meta_text = " · ".join(metadata) or "Hindsight memory"
        memory_text = safe_html(item.get("text")).replace("\n", "<br>")
        st.markdown(
            f"""
            <div class="memory-card">
                <div class="memory-card-title">
                    Candidate {index} · {safe_html(meta_text)}
                </div>
                {memory_text}
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-mark">✦</div>
            <div>
                <div class="brand-title">Incident Memory</div>
                <div class="brand-subtitle">Evidence-grounded response</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="nav-label">Workspace</div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Investigate",
            "Record resolution",
            "Memory explorer",
            "How it works",
        ],
        label_visibility="collapsed",
    )

    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-online">● Systems configured</div>
            <div class="status-row">
                <span>Memory bank</span>
                <span>{safe_html(HINDSIGHT_BANK_ID)}</span>
            </div>
            <div class="status-row">
                <span>Reasoning model</span>
                <span>{safe_html(GROQ_MODEL)}</span>
            </div>
        </div>
        <div class="safety-note">
            <span class="safety-icon">✓</span>
            <span>Human approval required. The agent never executes production actions.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Overview
# -----------------------------------------------------------------------------

if page == "Overview":
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Persistent operational intelligence</div>
            <h1>Every resolved incident improves the next response.</h1>
            <p>
                Investigate software failures with evidence from confirmed
                historical incidents. Compare generic guidance against
                Hindsight-grounded reasoning, then teach the system what
                actually worked.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_one, metric_two, metric_three, metric_four = st.columns(4)
    metric_one.metric(
        "Investigations this session",
        st.session_state["investigation_count"],
    )
    last_result = st.session_state.get("investigation_result") or {}
    metric_two.metric(
        "Last recall candidates",
        len(last_result.get("memories", [])),
    )
    metric_three.metric(
        "Feedback events",
        st.session_state["feedback_count"],
    )
    metric_four.metric("Safety mode", "Human verified")

    st.markdown(
        """
        <div class="section-head">
            <h2>A focused learning loop</h2>
            <p>One workflow, with memory visible at every important step.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    first, second, third = st.columns(3)
    with first:
        st.markdown(
            """
            <div class="panel">
                <div class="step-number">1</div>
                <h3>Investigate</h3>
                <p>Capture the current symptoms without assuming a cause.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with second:
        st.markdown(
            """
            <div class="panel">
                <div class="step-number">2</div>
                <h3>Recall and compare</h3>
                <p>Retrieve prior incidents and reject misleading matches.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with third:
        st.markdown(
            """
            <div class="panel">
                <div class="step-number">3</div>
                <h3>Confirm and learn</h3>
                <p>Store the verified cause, resolution and human outcome.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="section-head">
            <h2>What makes the memory trustworthy</h2>
        </div>
        <div class="callout">
            <strong>Evidence, not certainty.</strong> A matching incident is
            presented with its source context and never treated as automatic
            proof. The engineer remains responsible for confirming the current
            root cause using live logs and system data.
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Investigate
# -----------------------------------------------------------------------------

elif page == "Investigate":
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">New investigation</div>
            <h1>What happened?</h1>
            <p>
                Describe the observable facts. The same incident will be
                analyzed without memory and with Hindsight memory.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("investigation_form"):
        field_one, field_two, field_three = st.columns(3)
        with field_one:
            service_name = st.text_input(
                "Service",
                placeholder="report-service",
            )
        with field_two:
            environment = st.selectbox(
                "Environment",
                ["Production", "Staging", "Development", "Unknown"],
            )
        with field_three:
            severity = st.selectbox(
                "Reported severity",
                ["Unknown", "SEV-1", "SEV-2", "SEV-3", "SEV-4"],
            )

        incident_details = st.text_area(
            "Current incident details",
            height=190,
            placeholder=(
                "State only what is currently observed: symptoms, errors, "
                "time, affected scope and recent changes."
            ),
        )
        investigate = st.form_submit_button(
            "Compare without memory vs with Hindsight",
            type="primary",
            use_container_width=True,
        )

    if investigate:
        if not service_name.strip() or not incident_details.strip():
            st.warning("Enter both the service name and incident details.")
        else:
            clean_service = redact_sensitive_text(service_name)
            clean_details = redact_sensitive_text(incident_details)
            current_incident = f"""
Service: {clean_service}
Environment: {environment}
Reported severity: {severity}
Current details: {clean_details}
""".strip()

            try:
                with st.spinner(
                    "Recalling evidence and preparing both investigations..."
                ):
                    memories = recall_memories(current_incident)
                    baseline_brief = generate_baseline_brief(current_incident)
                    memory_brief = generate_memory_brief(
                        current_incident,
                        memories,
                    )

                st.session_state["investigation_count"] += 1
                st.session_state["relevance_feedback_saved"] = False
                st.session_state["outcome_feedback_saved"] = False
                st.session_state["last_feedback"] = None
                st.session_state["investigation_result"] = {
                    "investigation_id": investigation_fingerprint(
                        clean_service,
                        clean_details,
                    ),
                    "service": clean_service,
                    "environment": environment,
                    "severity": severity,
                    "current_incident": current_incident,
                    "memories": memories,
                    "baseline_brief": baseline_brief,
                    "memory_brief": memory_brief,
                }
            except Exception as error:
                st.error(f"Investigation failed: {error}")

    result = st.session_state.get("investigation_result")
    if result:
        st.markdown(
            """
            <div class="section-head">
                <h2>Memory impact comparison</h2>
                <p>The same current facts, with one controlled difference.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_one, metric_two, metric_three, metric_four = st.columns(4)
        metric_one.metric("Service", result["service"])
        metric_two.metric("Environment", result["environment"])
        metric_three.metric("Severity", result["severity"])
        metric_four.metric("Recall candidates", len(result["memories"]))

        baseline_column, memory_column = st.columns(2)
        with baseline_column:
            st.markdown(
                '<span class="tag tag-neutral">Without memory</span>',
                unsafe_allow_html=True,
            )
            st.subheader("Generic investigation")
            with st.container(border=True):
                st.markdown(result["baseline_brief"])

        with memory_column:
            st.markdown(
                '<span class="tag tag-accent">With Hindsight</span>',
                unsafe_allow_html=True,
            )
            st.subheader("Memory-grounded investigation")
            with st.container(border=True):
                st.markdown(result["memory_brief"])

        st.success(
            "Hindsight supplied historical evidence while preserving "
            "uncertainty about the current root cause."
        )

        with st.expander(
            f"Inspect {len(result['memories'])} raw recall candidates"
        ):
            render_memory_cards(result["memories"])

        st.warning(
            "A retrieved memory is supporting evidence, not proof. Verify "
            "recommendations against current logs and production data."
        )

        st.markdown(
            """
            <div class="section-head">
                <h2>Human feedback</h2>
                <p>
                    Complete both checks to improve future incident recall and
                    recommendation quality.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        relevance_done = st.session_state["relevance_feedback_saved"]
        outcome_done = st.session_state["outcome_feedback_saved"]
        relevance_class = " done" if relevance_done else ""
        outcome_class = " done" if outcome_done else ""
        relevance_marker = "✓" if relevance_done else "1"
        outcome_marker = "✓" if outcome_done else "2"
        st.markdown(
            f"""
            <div class="feedback-progress">
                <div class="feedback-progress-item{relevance_class}">
                    <span class="progress-number">{relevance_marker}</span>
                    Evidence relevance
                </div>
                <div class="feedback-progress-item{outcome_class}">
                    <span class="progress-number">{outcome_marker}</span>
                    Recommendation outcome
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        feedback_notes = st.text_input(
            "Engineer note (optional)",
            placeholder="What made the recommendation useful or misleading?",
            key="investigation_feedback_notes",
        )

        st.markdown(
            """
            <div class="feedback-card-title">1. Was the recalled evidence relevant?</div>
            <div class="feedback-card-copy">
                Judge the historical evidence—not whether the final fix worked.
            </div>
            """,
            unsafe_allow_html=True,
        )
        relevance_one, relevance_two = st.columns(2)
        with relevance_one:
            useful_clicked = st.button(
                "✓ Useful evidence",
                use_container_width=True,
                disabled=st.session_state["relevance_feedback_saved"],
            )
        with relevance_two:
            misleading_clicked = st.button(
                "✕ Misleading evidence",
                use_container_width=True,
                disabled=st.session_state["relevance_feedback_saved"],
            )

        if useful_clicked or misleading_clicked:
            label = "Useful" if useful_clicked else "Misleading"
            try:
                with st.spinner("Saving relevance feedback..."):
                    save_feedback("Memory relevance", label, feedback_notes)
                st.session_state["relevance_feedback_saved"] = True
                st.success(f"Memory relevance recorded as {label.lower()}.")
            except Exception as error:
                st.error(f"Could not save feedback: {error}")

        st.markdown(
            """
            <div class="feedback-card-title" style="margin-top:1rem;">
                2. Did the recommendation help resolve the incident?
            </div>
            <div class="feedback-card-copy">
                Record the observed result after an engineer verified the action.
            </div>
            """,
            unsafe_allow_html=True,
        )
        outcome_one, outcome_two = st.columns(2)
        with outcome_one:
            worked_clicked = st.button(
                "✓ Recommendation worked",
                use_container_width=True,
                disabled=st.session_state["outcome_feedback_saved"],
            )
        with outcome_two:
            failed_clicked = st.button(
                "✕ Recommendation failed",
                use_container_width=True,
                disabled=st.session_state["outcome_feedback_saved"],
            )

        if worked_clicked or failed_clicked:
            label = "Worked" if worked_clicked else "Failed"
            try:
                with st.spinner("Saving outcome feedback..."):
                    save_feedback(
                        "Recommendation outcome",
                        label,
                        feedback_notes,
                    )
                st.session_state["outcome_feedback_saved"] = True
                st.success(f"Recommendation outcome recorded as {label.lower()}.")
            except Exception as error:
                st.error(f"Could not save feedback: {error}")

        if relevance_done and outcome_done:
            st.markdown(
                """
                <div class="feedback-complete">
                    ✓ Feedback complete — both signals were saved to persistent memory.
                </div>
                """,
                unsafe_allow_html=True,
            )


# -----------------------------------------------------------------------------
# Record a confirmed resolution
# -----------------------------------------------------------------------------

elif page == "Record resolution":
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Verified learning</div>
            <h1>Teach the agent what actually happened.</h1>
            <p>
                This protected workflow writes confirmed operational knowledge
                into persistent memory. Record only verified information.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not ADMIN_PASSWORD:
        st.error(
            "Admin access is not configured. Add `ADMIN_PASSWORD` to `.env` "
            "or deployment secrets."
        )
        st.stop()

    entered_password = st.text_input(
        "Admin password",
        type="password",
        placeholder="Enter the admin password",
        key="resolution_admin_password",
    )

    if not entered_password:
        st.info("Authentication is required before writing confirmed memory.")
        st.stop()

    if not hmac.compare_digest(entered_password, str(ADMIN_PASSWORD)):
        st.error("Incorrect admin password.")
        st.stop()

    st.success("Admin access granted.")

    with st.form("resolution_form", clear_on_submit=True):
        left, middle, right = st.columns(3)
        with left:
            resolution_service = st.text_input(
                "Service",
                placeholder="report-service",
            )
        with middle:
            incident_date = st.date_input("Incident date", value=date.today())
        with right:
            resolution_environment = st.selectbox(
                "Environment",
                ["Production", "Staging", "Development", "Unknown"],
                key="resolution_environment",
            )

        resolution_severity = st.selectbox(
            "Confirmed severity",
            ["Unknown", "SEV-1", "SEV-2", "SEV-3", "SEV-4"],
        )
        symptoms = st.text_area(
            "Observed symptoms",
            placeholder="What was directly observed?",
        )
        impact = st.text_area(
            "Confirmed impact",
            placeholder="Who or what was affected?",
        )
        root_cause = st.text_area(
            "Confirmed root cause",
            placeholder="Enter only the root cause verified by the team.",
        )
        resolution_applied = st.text_area(
            "Resolution applied",
            placeholder="What action resolved the incident?",
        )
        prevention = st.text_area(
            "Prevention or follow-up",
            placeholder="Monitoring, tests, alerts or process improvements.",
        )

        save_resolution = st.form_submit_button(
            "Save confirmed resolution",
            type="primary",
            use_container_width=True,
        )

    if save_resolution:
        required_fields = {
            "service": resolution_service.strip(),
            "observed symptoms": symptoms.strip(),
            "confirmed impact": impact.strip(),
            "confirmed root cause": root_cause.strip(),
            "resolution": resolution_applied.strip(),
        }
        empty_fields = [
            name for name, value in required_fields.items() if not value
        ]

        if empty_fields:
            st.warning("Complete these fields: " + ", ".join(empty_fields))
        else:
            memory_content = f"""
Confirmed software incident record.

Incident date: {incident_date.isoformat()}
Service: {resolution_service.strip()}
Environment: {resolution_environment}
Severity: {resolution_severity}
Observed symptoms: {symptoms.strip()}
Confirmed impact: {impact.strip()}
Confirmed root cause: {root_cause.strip()}
Resolution applied: {resolution_applied.strip()}
Prevention or follow-up: {prevention.strip() or 'Not provided'}
Outcome: Resolved

The root cause, resolution and outcome were confirmed by a human engineer.
""".strip()

            try:
                with st.spinner("Saving verified incident memory..."):
                    retain_memory(memory_content)
                st.success(
                    "Resolution saved. Future investigations can now use "
                    "this confirmed experience."
                )
            except Exception as error:
                st.error(f"Could not save the resolution: {error}")


# -----------------------------------------------------------------------------
# Memory explorer
# -----------------------------------------------------------------------------

elif page == "Memory explorer":
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Transparent evidence</div>
            <h1>Explore what the agent remembers.</h1>
            <p>
                Search the Hindsight bank in natural language and inspect the
                raw memory candidates returned to the agent.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("memory_search_form"):
        memory_query = st.text_input(
            "Memory search",
            placeholder=(
                "What previously caused PDF generation to fail after deployment?"
            ),
        )
        search_memory = st.form_submit_button(
            "Search memory",
            type="primary",
            use_container_width=True,
        )

    if search_memory:
        if not memory_query.strip():
            st.warning("Enter a memory-search question.")
        else:
            try:
                with st.spinner("Searching persistent memory..."):
                    explorer_results = recall_memories(memory_query, limit=10)
                st.markdown(
                    f'<span class="tag tag-success">{len(explorer_results)} '
                    "candidates retrieved</span>",
                    unsafe_allow_html=True,
                )
                render_memory_cards(explorer_results)
            except Exception as error:
                st.error(f"Memory search failed: {error}")


# -----------------------------------------------------------------------------
# How it works
# -----------------------------------------------------------------------------

else:
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">System design</div>
            <h1>Memory is part of the decision, not decoration.</h1>
            <p>
                Hindsight retains verified experience and retrieves relevant
                evidence. Groq converts current facts and selected memories
                into a structured investigation. Human feedback closes the
                learning loop.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    first, second, third = st.columns(3)
    with first:
        st.markdown(
            """
            <div class="panel">
                <div class="step-number">1</div>
                <h3>Retain</h3>
                <p>
                    Confirmed incidents, successful resolutions and failed
                    recommendations become persistent organizational memory.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with second:
        st.markdown(
            """
            <div class="panel">
                <div class="step-number">2</div>
                <h3>Recall and reason</h3>
                <p>
                    Similar experiences are retrieved, checked for
                    applicability and used as evidence in the investigation.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with third:
        st.markdown(
            """
            <div class="panel">
                <div class="step-number">3</div>
                <h3>Verify and improve</h3>
                <p>
                    Engineers confirm outcomes and flag useful or misleading
                    memories, improving future incident handling.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="section-head"><h2>Safety boundaries</h2></div>
        """,
        unsafe_allow_html=True,
    )
    boundary_one, boundary_two = st.columns(2)
    with boundary_one:
        st.markdown(
            """
            <div class="panel">
                <span class="tag tag-success">The agent does</span>
                <p>
                    Recall prior evidence, expose uncertainty, suggest
                    investigation steps and remember human-confirmed outcomes.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with boundary_two:
        st.markdown(
            """
            <div class="panel">
                <span class="tag tag-neutral">The agent does not</span>
                <p>
                    Execute production changes, claim an unverified root cause
                    or replace the judgment of the responsible engineer.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
