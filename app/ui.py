import time

import pandas as pd
import streamlit as st

from text_to_sql import answer_question

st.set_page_config(page_title="Logistics Data Agent", layout="wide")

# ---------- Texts in both languages ----------
TEXT = {
    "ar": {
        "title": "محلل بيانات الشحنات الذكي",
        "subtitle": "اسأل عن بيانات الشحنات بالعربي أو الإنجليزي، والوكيل يكتب الاستعلام وينفذه ويشرح لك النتيجة.",
        "examples_header": "أسئلة مقترحة",
        "demo": "تجربة التصحيح الذاتي",
        "demo_help": "يخرّب أول استعلام بقصد عشان تشوف الوكيل يصلّح نفسه",
        "clear": "مسح المحادثة",
        "details": "إظهار التفاصيل التقنية",
        "input": "اكتب سؤالك هنا...",
        "thinking": "جاري تحليل البيانات...",
        "error": "ما قدرت أجاوب على هذا السؤال:",
        "model": "النموذج",
        "fixes": "التصحيحات الذاتية",
        "time": "الوقت",
        "seconds": "ث",
        "data": "البيانات",
        "sql": "استعلام SQL",
        "failed": "محاولات فاشلة تم تصحيحها",
        "attempt": "محاولة",
        "examples": [
            "كم شحنة عندنا هذا الشهر؟",
            "أي شركة نقل عندها أعلى نسبة تأخير؟",
            "ما هي أكثر أسباب التأخير؟",
            "أي مدينة وصول فيها أكثر شحنات متأخرة؟",
            "كم إجمالي تكلفة الشحن لكل نوع عميل؟",
        ],
    },
    "en": {
        "title": "Logistics Data Agent",
        "subtitle": "Ask about shipment data in Arabic or English. The agent writes the query, runs it, and explains the result.",
        "examples_header": "Suggested questions",
        "demo": "Self-correction demo",
        "demo_help": "Breaks the first query on purpose so you can watch the agent fix itself",
        "clear": "Clear chat",
        "details": "Show technical details",
        "input": "Type your question...",
        "thinking": "Analyzing the data...",
        "error": "I couldn't answer this question:",
        "model": "Model",
        "fixes": "Self-corrections",
        "time": "Time",
        "seconds": "s",
        "data": "Data",
        "sql": "SQL query",
        "failed": "Failed attempts that were fixed",
        "attempt": "Attempt",
        "examples": [
            "How many shipments this month?",
            "Which carrier has the highest delay rate?",
            "What are the most common delay reasons?",
            "Which destination city has the most late shipments?",
            "Which carrier has the best on-time rate?",
        ],
    },
}

if "history" not in st.session_state:
    st.session_state.history = []
if "lang" not in st.session_state:
    st.session_state.lang = "ar"

# ---------- Sidebar ----------
with st.sidebar:
    choice = st.radio(
        "Language",
        ["العربية", "English"],
        index=0 if st.session_state.lang == "ar" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.lang = "ar" if choice == "العربية" else "en"
    T = TEXT[st.session_state.lang]

    st.markdown(f"<div class='side-title'>{T['examples_header']}</div>", unsafe_allow_html=True)
    for example in T["examples"]:
        if st.button(example, key=f"ex_{example}"):
            st.session_state.pending = example

    st.divider()
    show_details = st.toggle(T["details"], value=False)
    demo_error = st.toggle(T["demo"], help=T["demo_help"])
    if st.button(T["clear"], key="clear"):
        st.session_state.history = []
        st.rerun()

# ---------- Style: dark background with blue grid lines ----------
direction = "rtl" if st.session_state.lang == "ar" else "ltr"
align = "right" if direction == "rtl" else "left"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600&display=swap');

    html, body, .stApp, button, input, textarea {{
        font-family: 'IBM Plex Sans Arabic', sans-serif !important;
    }}

    .stApp {{
        background-color: #05070d;
        background-image:
            radial-gradient(circle at 15% 0%, rgba(37, 99, 235, 0.20), transparent 45%),
            radial-gradient(circle at 90% 100%, rgba(14, 165, 233, 0.12), transparent 40%),
            linear-gradient(rgba(59, 130, 246, 0.07) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59, 130, 246, 0.07) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 44px 44px, 44px 44px;
        background-attachment: fixed;
    }}

    [data-testid="stHeader"] {{ background: transparent; }}

    /* Main content direction */
    .main .block-container, [data-testid="stChatMessage"], [data-testid="stMarkdownContainer"],
    [data-testid="stCaptionContainer"], h1, p, label {{
        direction: {direction};
        text-align: {align};
    }}
    .block-container {{ max-width: 920px; padding-top: 2.5rem; }}

    /* Code and tables always left-to-right */
    code, pre, [data-testid="stCode"], [data-testid="stDataFrame"] {{
        direction: ltr !important;
        text-align: left !important;
    }}

    /* Title */
    h1 {{
        font-weight: 600 !important;
        font-size: 2rem !important;
        background: linear-gradient(90deg, #e5e7eb, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    /* Narrow sidebar */
    section[data-testid="stSidebar"] {{
        width: 250px !important;
        min-width: 250px !important;
        max-width: 250px !important;
        background: rgba(5, 8, 16, 0.92);
        border-right: 1px solid rgba(59, 130, 246, 0.25);
    }}
    section[data-testid="stSidebar"] * {{ direction: {direction}; text-align: {align}; }}
    .side-title {{
        color: #60a5fa;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        margin: 0.6rem 0 0.4rem;
    }}
    section[data-testid="stSidebar"] .stButton button {{
        width: 100%;
        font-size: 0.8rem;
        padding: 0.35rem 0.6rem;
        min-height: 0;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(59, 130, 246, 0.25);
        color: #cbd5e1;
        justify-content: flex-start;
    }}
    section[data-testid="stSidebar"] .stButton button:hover {{
        border-color: #3b82f6;
        color: #ffffff;
        background: rgba(37, 99, 235, 0.15);
    }}

    /* Chat cards */
    [data-testid="stChatMessage"] {{
        background: rgba(11, 18, 32, 0.75);
        border: 1px solid rgba(59, 130, 246, 0.18);
        border-radius: 14px;
        padding: 0.9rem 1rem;
        backdrop-filter: blur(4px);
    }}

    /* Hide chat avatars */
    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"],
    [data-testid="stChatMessageAvatarCustom"],
    [data-testid^="chatAvatarIcon"] {{
        display: none !important;
    }}

    /* User question bubble: blue tint */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
        background: rgba(37, 99, 235, 0.16);
        border-color: rgba(59, 130, 246, 0.45);
    }}

    /* Metrics smaller */
    [data-testid="stMetricValue"] {{ font-size: 1.05rem !important; color: #93c5fd; }}
    [data-testid="stMetricLabel"] p {{ font-size: 0.75rem !important; color: #94a3b8; }}

    /* Expanders */
    [data-testid="stExpander"] details {{
        border: 1px solid rgba(59, 130, 246, 0.18) !important;
        border-radius: 10px;
        background: rgba(5, 8, 16, 0.5);
    }}

    /* Chat input */
    [data-testid="stChatInput"] {{
        direction: {direction};
        border: 1px solid rgba(59, 130, 246, 0.35);
        border-radius: 12px;
    }}
    [data-testid="stBottom"] > div {{ background: transparent; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.title(T["title"])
st.caption(T["subtitle"])


def render(item):
    with st.chat_message("user"):
        st.write(item["question"])

    if item.get("status") == "pending":
        return

    with st.chat_message("assistant"):
        if "error" in item:
            st.error(f"{T['error']} {item['error']}")
            return

        st.write(item["answer"])

        if not show_details:
            return

        col1, col2, col3 = st.columns(3)
        col1.metric(T["model"], item["model"] or "-")
        col2.metric(T["fixes"], len(item["failed_attempts"]))
        col3.metric(T["time"], f"{item['seconds']:.1f} {T['seconds']}")

        if item["rows"]:
            with st.expander(T["data"]):
                st.dataframe(pd.DataFrame(item["rows"], columns=item["columns"]))

        with st.expander(T["sql"]):
            st.code(item["sql"], language="sql")

        if item["failed_attempts"]:
            with st.expander(f"{T['failed']} ({len(item['failed_attempts'])})"):
                for i, attempt in enumerate(item["failed_attempts"], 1):
                    st.markdown(f"**{T['attempt']} {i}**")
                    st.code(attempt["sql"], language="sql")
                    st.caption(attempt["error"])


for item in st.session_state.history:
    render(item)

# ---------- New question ----------
question = st.chat_input(T["input"])
if not question and st.session_state.get("pending"):
    question = st.session_state.pop("pending")

if question:
    # Step 1: show the question in the chat right away
    st.session_state.history.append({"question": question, "status": "pending", "demo": demo_error})
    st.rerun()

history = st.session_state.history
if history and history[-1].get("status") == "pending":
    # Step 2: the question is already on screen, now get the answer
    item = history[-1]
    with st.chat_message("assistant"):
        with st.spinner(T["thinking"]):
            start = time.time()
            try:
                result = answer_question(item["question"], demo_error=item["demo"])
                result["seconds"] = time.time() - start
            except Exception as e:
                result = {"question": item["question"], "error": str(e)}
    history[-1] = result
    st.rerun()