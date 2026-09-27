import html
import os
from datetime import date

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


# =========================================================
# Claude-inspired visual theme
# =========================================================

st.markdown(
    """
    <style>
        :root {
            --background: #f7f6f2;
            --sidebar: #efede7;
            --surface: #ffffff;
            --surface-soft: #f1efe9;
            --border: #dedbd3;
            --text: #292824;
            --muted: #6f6c64;
            --accent: #d97757;
            --accent-dark: #bd6044;
            --success: #427a5b;
        }

        html, body, [class*="css"] {
            font-family: Inter, ui-sans-serif, -apple-system,
                BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp {
            background: var(--background);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: rgba(247, 246, 242, 0.92);
            border-bottom: 1px solid var(--border);
        }

        [data-testid="stSidebar"] {
            background: var(--sidebar);
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] * {
            color: var(--text);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 3.2rem;
            padding-bottom: 5rem;
        }

        h1, h2, h3 {
            color: var(--text) !important;
            letter-spacing: -0.025em;
        }

        p, label, .stCaption {
            color: var(--muted);
        }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            margin: 0.4rem 0 1.7rem;
        }

        .sidebar-logo {
            width: 35px;
            height: 35px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 11px;
            background: var(--accent);
            color: white !important;
            font-size: 1.15rem;
            font-weight: 800;
        }

        .sidebar-title {
            color: var(--text) !important;
            font-size: 1.05rem;
            font-weight: 700;
        }

        .sidebar-subtitle {
            color: var(--muted) !important;
            font-size: 0.76rem;
        }

        .connection-card {
            background: rgba(255, 255, 255, 0.60);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.9rem 1rem;
            margin-top: 1.3rem;
        }

        .online {
            color: var(--success) !important;
            font-size: 0.85rem;
            font-weight: 700;
        }

        .bank-name {
            color: var(--muted) !important;
            font-size: 0.75rem;
            margin-top: 0.35rem;
        }

        .welcome {
            max-width: 760px;
            margin: 2rem auto 2.2rem;
            text-align: center;
        }

        .welcome-mark {
            width: 48px;
            height: 48px;
            margin: auto auto 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 15px;
            background: #ead8ce;
            color: var(--accent);
            font-size: 1.45rem;
            font-weight: 800;
        }

        .welcome h1 {
            margin: 0;
            font-family: Georgia, "Times New Roman", serif;
            font-size: clamp(2rem, 4vw, 3.3rem);
            font-weight: 500;
            line-height: 1.08;
        }

        .welcome p {
            max-width: 650px;
            margin: 1rem auto 0;
            font-size: 1.02rem;
            line-height: 1.65;
        }

        div[data-testid="stForm"] {
            padding: 1.4rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 22px;
            box-shadow: 0 5px 18px rgba(65, 57, 45, 0.05);
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"],
        textarea {
            background: #fbfaf7 !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
            border-radius: 12px !important;
        }

        input, textarea {
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
        }

        input::placeholder, textarea::placeholder {
            color: #9b978e !important;
            -webkit-text-fill-color: #9b978e !important;
        }

        div[data-baseweb="select"] span {
            color: var(--text) !important;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            min-height: 46px;
            border: 1px solid var(--accent);
            border-radius: 12px;
            background: var(--accent);
            color: white !important;
            font-weight: 700;
            box-shadow: none;
        }

        .stButton > button p,
        .stFormSubmitButton > button p {
            color: white !important;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background: var(--accent-dark);
            border-color: var(--accent-dark);
        }

        div[role="radiogroup"] {
            gap: 0.3rem;
        }

        div[role="radiogroup"] label {
            padding: 0.65rem 0.7rem;
            border-radius: 10px;
        }

        div[role="radiogroup"] label:hover {
            background: rgba(255, 255, 255, 0.65);
        }

        .section-heading {
            margin-bottom: 1.2rem;
        }

        .section-heading h2 {
            margin-bottom: 0.3rem;
            font-family: Georgia, "Times New Roman", serif;
            font-weight: 500;
        }

        .comparison-label {
            display: inline-block;
            margin-bottom: 0.65rem;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .without-memory {
            background: #ece9e2;
            color: #6f6c64;
        }

        .with-memory {
            background: #ead8ce;
            color: #a64f36;
        }

        .memory-card {
            padding: 1rem;
            margin-bottom: 0.75rem;
            border: 1px solid var(--border);
            border-radius: 14px;
            background: var(--surface-soft);
            color: var(--text);
            line-height: 1.55;
        }

        .memory-label {
            margin-bottom: 0.4rem;
            color: var(--accent);
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        div[data-testid="stMetric"] {
            padding: 1rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
        }

        div[data-testid="stMetricLabel"] p {
            color: var(--muted) !important;
        }

        div[data-testid="stMetricValue"] {
            color: var(--text) !important;
        }

        .flow-card {
            min-height: 170px;
            padding: 1.25rem;
            border: 1px solid var(--border);
            border-radius: 17px;
            background: var(--surface);
        }

        .flow-number {
            display: inline-flex;
            width: 30px;
            height: 30px;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.8rem;
            border-radius: 9px;
            background: #ead8ce;
            color: var(--accent);
            font-weight: 800;
        }

        .footer-note {
            padding-top: 2rem;
            color: var(--muted);
            font-size: 0.78rem;
        }

        [data-testid="stAlert"] {
            border-radius: 14px;
        }

        code {
            color: var(--text) !important;
            background: var(--surface-soft) !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Configuration
# =========================================================

def get_setting(name):
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
    st.info("Add the missing values to your local .env file.")
    st.stop()


# =========================================================
# Agent functions
# =========================================================

def recall_memories(query, limit=5):
    client = Hindsight(
        base_url=HINDSIGHT_API_URL,
        api_key=HINDSIGHT_API_KEY,
    )

    try:
        response = client.recall(
            bank_id=HINDSIGHT_BANK_ID,
            query=query,
        )
        return [memory.text for memory in response.results[:limit]]
    finally:
        client.close()


def generate_investigation_brief(current_incident, memories):
    memory_context = (
        "\n".join(f"- {memory}" for memory in memories)
        if memories
        else "No relevant historical memories were found."
    )

    prompt = f"""
CURRENT INCIDENT:
{current_incident}

HISTORICAL MEMORIES:
{memory_context}

Create a concise software incident investigation brief.

RULES:
- Current facts must contain only information explicitly provided.
- Mark missing scope, logs, impact, actions, and root cause as unknown.
- Historical memories are evidence, not proof.
- Multiple memories may be extracted from one incident.
- Merge overlapping memory fragments into one historical incident summary.
- Never mention that an incident was recorded twice.
- Never describe overlapping memories as separate or independent evidence.
- Ignore historical memories unrelated to the current service or symptoms.
- Do not mention an unrelated memory merely because it was retrieved.
- Never invent facts, logs, causes, systems, or completed actions.
- Use concise Markdown bullets.
- Keep the response below 450 words.

Use these sections:
1. Confirmed current facts
2. Unknown information
3. Relevant historical evidence
4. Top three investigation steps
5. Uncertainty warning
"""

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful software incident-response agent. "
                    "Historical memory is evidence, never proof."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_completion_tokens=1000,
    )
    return response.choices[0].message.content


def generate_baseline_brief(current_incident):
    prompt = f"""
CURRENT INCIDENT:
{current_incident}

Create a concise software incident investigation brief using only the
current incident information.

RULES:
- Do not use or assume any historical incident knowledge.
- Include only facts explicitly provided.
- Mark missing scope, logs, impact, actions, and root cause as unknown.
- Never invent facts, logs, causes, systems, or completed actions.
- Recommend exactly three general investigation steps.
- Use concise Markdown bullets.
- Keep the response below 350 words.

Use these sections:
1. Confirmed current facts
2. Unknown information
3. Top three general investigation steps
4. Uncertainty warning
"""

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful software incident-response agent. "
                    "You have no historical memory for this response."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_completion_tokens=800,
    )
    return response.choices[0].message.content


def store_confirmed_resolution(memory_content):
    client = Hindsight(
        base_url=HINDSIGHT_API_URL,
        api_key=HINDSIGHT_API_KEY,
    )

    try:
        client.retain(
            bank_id=HINDSIGHT_BANK_ID,
            content=memory_content,
        )
    finally:
        client.close()


# =========================================================
# Sidebar navigation
# =========================================================

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo">✦</div>
            <div>
                <div class="sidebar-title">Incident Memory</div>
                <div class="sidebar-subtitle">Engineering intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        ["New investigation", "Record resolution", "How it works"],
        label_visibility="collapsed",
    )

    st.markdown(
        f"""
        <div class="connection-card">
            <div class="online">● Systems connected</div>
            <div class="bank-name">
                Memory bank: {html.escape(HINDSIGHT_BANK_ID)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="footer-note">
            Hindsight persistent memory<br>
            Groq reasoning engine
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# New investigation
# =========================================================

if page == "New investigation":
    st.markdown(
        """
        <div class="welcome">
            <div class="welcome-mark">✦</div>
            <h1>What incident are we investigating?</h1>
            <p>
                Compare generic incident guidance with an answer grounded
                in your team's persistent Hindsight memory.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("investigation_form"):
        column_one, column_two, column_three = st.columns(3)

        with column_one:
            service_name = st.text_input(
                "Service",
                placeholder="notification-service",
            )

        with column_two:
            environment = st.selectbox(
                "Environment",
                ["Production", "Staging", "Development", "Unknown"],
            )

        with column_three:
            severity = st.selectbox(
                "Severity",
                ["Unknown", "SEV-1", "SEV-2", "SEV-3", "SEV-4"],
            )

        incident_details = st.text_area(
            "Describe the current incident",
            height=180,
            placeholder=(
                "Transaction confirmation emails stopped being delivered "
                "after today's deployment. The root cause is not confirmed."
            ),
        )

        investigate = st.form_submit_button(
            "Compare without memory vs with Hindsight",
            type="primary",
            use_container_width=True,
        )

    if investigate:
        if not service_name.strip() or not incident_details.strip():
            st.warning("Enter the service name and current incident details.")
        else:
            current_incident = f"""
Service: {service_name.strip()}
Environment: {environment}
Reported severity: {severity}
Current details: {incident_details.strip()}
""".strip()

            try:
                with st.spinner(
                    "Comparing general guidance with memory-powered guidance..."
                ):
                    baseline_brief = generate_baseline_brief(
                        current_incident
                    )
                    memories = recall_memories(current_incident)
                    memory_brief = generate_investigation_brief(
                        current_incident,
                        memories,
                    )

                st.session_state["investigation_result"] = {
                    "service": service_name.strip(),
                    "environment": environment,
                    "severity": severity,
                    "memories": memories,
                    "baseline_brief": baseline_brief,
                    "memory_brief": memory_brief,
                }
            except Exception as error:
                st.error(f"Investigation failed: {error}")

    if "investigation_result" in st.session_state:
        result = st.session_state["investigation_result"]

        st.markdown("---")
        st.markdown(
            """
            <div class="section-heading">
                <h2>Memory impact comparison</h2>
                <p>
                    The same incident is analyzed once without historical
                    memory and once with Hindsight memory.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_one, metric_two, metric_three = st.columns(3)
        metric_one.metric("Service", result["service"])
        metric_two.metric("Severity", result["severity"])
        metric_three.metric("Memories retrieved", len(result["memories"]))

        baseline_column, hindsight_column = st.columns(2)

        with baseline_column:
            st.markdown(
                '<div class="comparison-label without-memory">'
                'Without memory</div>',
                unsafe_allow_html=True,
            )
            st.markdown("### Generic investigation")
            with st.container(border=True):
                st.markdown(result["baseline_brief"])

        with hindsight_column:
            st.markdown(
                '<div class="comparison-label with-memory">'
                'With Hindsight</div>',
                unsafe_allow_html=True,
            )
            st.markdown("### Memory-powered investigation")
            with st.container(border=True):
                st.markdown(result["memory_brief"])

        st.success(
            "Hindsight adds organization-specific historical context while "
            "preserving uncertainty about the current root cause."
        )

        with st.expander(
            f"View {len(result['memories'])} retrieved memory candidates"
        ):
            if result["memories"]:
                for index, memory in enumerate(
                    result["memories"],
                    start=1,
                ):
                    safe_memory = html.escape(memory).replace("\n", "<br>")
                    st.markdown(
                        f"""
                        <div class="memory-card">
                            <div class="memory-label">
                                Retrieved memory {index}
                            </div>
                            {safe_memory}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No historical memories were retrieved.")

        st.warning(
            "Retrieved memory is supporting evidence, not proof of the "
            "current root cause. Engineers must verify it using live data."
        )


# =========================================================
# Record resolution
# =========================================================

elif page == "Record resolution":
    st.markdown(
        """
        <div class="section-heading">
            <h2>Teach the agent what happened</h2>
            <p>
                Record only confirmed incident information. This becomes
                reusable memory for future investigations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("resolution_form"):
        left_column, right_column = st.columns(2)

        with left_column:
            resolution_service = st.text_input(
                "Service",
                placeholder="checkout-service",
            )
            incident_date = st.date_input(
                "Incident date",
                value=date.today(),
            )
            resolution_environment = st.selectbox(
                "Environment",
                ["Production", "Staging", "Development", "Unknown"],
                key="resolution_environment",
            )

        with right_column:
            resolution_severity = st.selectbox(
                "Confirmed severity",
                ["Unknown", "SEV-1", "SEV-2", "SEV-3", "SEV-4"],
            )
            symptoms = st.text_area(
                "Observed symptoms",
                height=109,
                placeholder="What was observed?",
            )

        impact = st.text_area(
            "Confirmed impact",
            placeholder="Who or what was affected?",
        )
        root_cause = st.text_area(
            "Confirmed root cause",
            placeholder="Enter only the verified root cause.",
        )
        resolution_applied = st.text_area(
            "Resolution applied",
            placeholder="What action successfully resolved the incident?",
        )
        prevention = st.text_area(
            "Prevention or follow-up",
            placeholder="Monitoring, tests, alerts, or process improvements.",
        )

        save_resolution = st.form_submit_button(
            "Save to incident memory",
            type="primary",
            use_container_width=True,
        )

    if save_resolution:
        required_fields = {
            "service": resolution_service.strip(),
            "symptoms": symptoms.strip(),
            "impact": impact.strip(),
            "root cause": root_cause.strip(),
            "resolution": resolution_applied.strip(),
        }
        missing_fields = [
            name for name, value in required_fields.items() if not value
        ]

        if missing_fields:
            st.warning("Complete these fields: " + ", ".join(missing_fields))
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
Prevention or follow-up action: {prevention.strip() or "Not provided"}

The root cause and resolution were confirmed by the engineering team.
""".strip()

            try:
                with st.spinner("Saving confirmed incident memory..."):
                    store_confirmed_resolution(memory_content)
                st.success(
                    "Resolution saved. The agent learned this incident."
                )
                st.toast("New incident memory created.")
            except Exception as error:
                st.error(f"Could not save the resolution: {error}")


# =========================================================
# How it works
# =========================================================

else:
    st.markdown(
        """
        <div class="section-heading">
            <h2>How the memory agent works</h2>
            <p>
                A transparent three-stage workflow for safer incident
                investigation.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    first, second, third = st.columns(3)

    with first:
        st.markdown(
            """
            <div class="flow-card">
                <div class="flow-number">1</div>
                <h3>Recall</h3>
                <p>
                    Hindsight retrieves historically relevant incidents
                    from persistent memory.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with second:
        st.markdown(
            """
            <div class="flow-card">
                <div class="flow-number">2</div>
                <h3>Reason</h3>
                <p>
                    Groq compares current facts with historical evidence
                    and suggests investigation steps.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with third:
        st.markdown(
            """
            <div class="flow-card">
                <div class="flow-number">3</div>
                <h3>Learn</h3>
                <p>
                    Confirmed root causes and resolutions are stored for
                    future incident response.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        "The agent never treats a historical match as proof. "
        "Engineers must verify the current root cause."
    )
