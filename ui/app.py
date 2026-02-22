from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def _landing_submit() -> None:
    st.session_state.landing_submit = True


def _init_session_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pet_profile" not in st.session_state:
        st.session_state.pet_profile = {
            "species": "",
            "age": "",
            "weight": "",
            "breed": "",
            "medical_conditions": "",
        }
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    if "is_loading" not in st.session_state:
        st.session_state.is_loading = False
    if "landing_input" not in st.session_state:
        st.session_state.landing_input = ""
    if "landing_submit" not in st.session_state:
        st.session_state.landing_submit = False


def _set_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600&family=Source+Serif+4:wght@400;600&display=swap');

html, body, [class*="css"]  {
  font-family: 'IBM Plex Sans', sans-serif;
  background: linear-gradient(180deg, #f7fbff 0%, #f2f6fb 100%);
  color: #0b1a2a;
}

.app-title {
  font-family: 'Source Serif 4', serif;
  font-size: 2.2rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.status-pill {
  display: inline-block;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-green { background: #e6f7ef; color: #0b7a4b; }
.status-yellow { background: #fff3cd; color: #8a6d1a; }
.status-red { background: #fdecea; color: #b42318; }

.section-card {
  background: #ffffff;
  border: 1px solid #e5eaf0;
  border-radius: 12px;
  padding: 1rem 1.2rem;
  margin-bottom: 1rem;
  box-shadow: 0 6px 18px rgba(13, 38, 76, 0.06);
}

.alert-banner {
  background: #fff1f1;
  border: 1px solid #f3b4b4;
  color: #8a1f1f;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  margin-bottom: 0.8rem;
  font-weight: 600;
}

.highlight-box {
  background: #f6f9ff;
  border: 1px dashed #9cb5ff;
  padding: 0.8rem 1rem;
  border-radius: 10px;
}

.badge {
  display: inline-block;
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  background: #eef2ff;
  color: #2f3a6f;
  font-weight: 600;
}

.context-badge {
  background: #eef6ff;
  color: #234;
}

.disclaimer {
  font-size: 0.75rem;
  color: #5a6b7f;
}

.landing-input input {
  padding-right: 2.2rem !important;
  background-repeat: no-repeat !important;
  background-position: right 0.7rem center !important;
  background-size: 1.1rem 1.1rem !important;
  /* Inline SVG (send icon) */
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%232b3a55' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 2L11 13'/%3E%3Cpath d='M22 2L15 22L11 13L2 9L22 2Z'/%3E%3C/svg%3E") !important;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _render_top_nav(system_state: Dict[str, Any]) -> None:
    col1, col2, col3 = st.columns([2.5, 1.2, 1.2])
    with col1:
        st.markdown("<div class='app-title'>Veterinary AI Assistant</div>", unsafe_allow_html=True)
        st.markdown("AI-powered veterinary guidance system", unsafe_allow_html=True)
    with col2:
        status = system_state.get("status", "ready")
        if status == "emergency":
            label = "<span class='status-pill status-red'>Emergency Mode</span>"
        elif status == "live_search":
            label = "<span class='status-pill status-yellow'>Live Search Active</span>"
        else:
            label = "<span class='status-pill status-green'>System Ready</span>"
        st.markdown(label, unsafe_allow_html=True)
    with col3:
        with st.expander("Legal Disclaimer"):
            st.write(
                "This system provides general guidance and is not a substitute for a licensed veterinarian."
            )


def _render_sidebar() -> None:
    st.sidebar.header("Pet Profile")
    with st.sidebar.form("pet-profile-form"):
        st.session_state.pet_profile["species"] = st.text_input(
            "Species (required)", st.session_state.pet_profile.get("species", "")
        )
        st.session_state.pet_profile["age"] = st.text_input(
            "Age", st.session_state.pet_profile.get("age", "")
        )
        st.session_state.pet_profile["weight"] = st.text_input(
            "Weight", st.session_state.pet_profile.get("weight", "")
        )
        st.session_state.pet_profile["breed"] = st.text_input(
            "Breed", st.session_state.pet_profile.get("breed", "")
        )
        st.session_state.pet_profile["medical_conditions"] = st.text_area(
            "Known Medical Conditions",
            st.session_state.pet_profile.get("medical_conditions", ""),
            height=80,
        )
        st.markdown(
            "<span class='disclaimer'>Information is used to personalize responses. "
            "Session data is cleared after inactivity.</span>",
            unsafe_allow_html=True,
        )
        st.form_submit_button("Save Profile")

    st.sidebar.subheader("File Uploads (Coming Soon)")
    uploaded = st.sidebar.file_uploader(
        "Upload reports (PDF, TXT)", type=["pdf", "txt"], accept_multiple_files=True
    )
    if uploaded:
        st.session_state.uploaded_files = [f.name for f in uploaded]
    if st.session_state.uploaded_files:
        st.sidebar.write("Uploaded:")
        for name in st.session_state.uploaded_files:
            st.sidebar.write(f"- {name}")
    st.sidebar.info("Document interpretation feature coming soon.")

    st.sidebar.subheader("Session Controls")
    if st.sidebar.button("Reset Conversation"):
        st.session_state.chat_history = []
    if st.sidebar.button("Clear Pet Profile"):
        st.session_state.pet_profile = {
            "species": "",
            "age": "",
            "weight": "",
            "breed": "",
            "medical_conditions": "",
        }
    if st.sidebar.button("Clear Uploaded Files"):
        st.session_state.uploaded_files = []


def _empty_state() -> Optional[str]:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='app-title'>Veterinary AI Assistant</div>", unsafe_allow_html=True)
    st.markdown("AI-powered veterinary guidance system")
    st.markdown("Try one of these:")
    suggestions = [
        "Puppy vaccination schedule",
        "My dog is vomiting",
        "Explain rabies vaccine",
        "Emergency signs in cats",
    ]
    cols = st.columns(2)
    clicked = None
    for idx, suggestion in enumerate(suggestions):
        if cols[idx % 2].button(suggestion):
            clicked = suggestion
    st.markdown("<div class='landing-input'>", unsafe_allow_html=True)
    st.text_input(
        "Ask me",
        key="landing_input",
        placeholder="Ask me",
        label_visibility="collapsed",
        on_change=_landing_submit,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    return clicked


def _render_citations(citations: List[Dict[str, Any]]) -> None:
    if not citations:
        return
    with st.expander("Sources"):
        for cite in citations:
            title = cite.get("source_title") or "Unknown Source"
            org = cite.get("organization") or "Unknown Organization"
            year = cite.get("publication_year") or "N/A"
            section = cite.get("section_reference") or ""
            url = cite.get("url") or ""
            st.markdown(f"**{title}**  \n{org} • {year}")
            if section:
                st.markdown(f"Section: {section}")
            if url:
                st.markdown(url)
            st.markdown("---")


def _render_structured_response(vet_response: Dict[str, Any]) -> None:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("**Answer**")
    st.write(vet_response.get("answer", ""))
    st.markdown("**Possible Causes**")
    st.write(vet_response.get("possible_causes", ""))
    st.markdown("**Warning Signs**")
    st.write(vet_response.get("warning_signs", ""))
    st.markdown("**When to See a Vet**")
    st.write(vet_response.get("vet_visit_guidance", ""))
    care = vet_response.get("care_tips")
    if care:
        st.markdown("**Care Tips**")
        st.write(care)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_response(message: Dict[str, Any]) -> None:
    response_mode = (message.get("response_mode") or "").lower()
    response_style = (message.get("response_style") or "").lower()
    query_context = (message.get("query_context") or "").upper()

    if message.get("emergency_flag") or message.get("emergency"):
        st.markdown("<div class='alert-banner'>⚠️ EMERGENCY ALERT</div>", unsafe_allow_html=True)
        if message.get("map_link"):
            st.link_button("Find Nearby Veterinary Care", message["map_link"])

    if message.get("live_search_flag"):
        st.markdown("<span class='badge'>Live Search Augmented Response</span>", unsafe_allow_html=True)

    if query_context:
        label = {
            "ACADEMIC": "Academic Context",
            "GENERAL": "Educational Context",
            "CLINICAL_SPECIFIC": "Case-Specific Clinical Context",
        }.get(query_context, query_context)
        st.markdown(f"<span class='badge context-badge'>{label}</span>", unsafe_allow_html=True)

    if response_style == "educational":
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.write(message.get("text", ""))
        st.markdown("</div>", unsafe_allow_html=True)
        _render_citations(message.get("citations", []))
        return

    if response_mode == "hybrid_partial":
        _render_structured_response(message.get("vet_response") or {"answer": message.get("text", "")})
        st.markdown("<div class='highlight-box'>", unsafe_allow_html=True)
        st.markdown("Before giving more specific advice, I need to know:")
        for q in message.get("follow_up_questions", []):
            st.markdown(f"- {q}")
        st.markdown("</div>", unsafe_allow_html=True)
        _render_citations(message.get("citations", []))
        return

    if response_mode == "clarification_required":
        st.markdown("<div class='highlight-box'>", unsafe_allow_html=True)
        st.markdown("More Information Needed:")
        for q in message.get("follow_up_questions", []):
            st.markdown(f"- {q}")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if response_style == "clinical":
        if query_context == "CLINICAL_SPECIFIC" and message.get("vet_response"):
            _render_structured_response(message["vet_response"])
        else:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.write(message.get("text", ""))
            st.markdown("</div>", unsafe_allow_html=True)
        _render_citations(message.get("citations", []))
        return

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.write(message.get("text", ""))
    st.markdown("</div>", unsafe_allow_html=True)


def _send_message(message: str) -> Dict[str, Any]:
    payload = {
        "session_id": st.session_state.session_id,
        "message": message,
        "pet_profile": st.session_state.pet_profile,
    }
    response = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def main() -> None:
    st.set_page_config(page_title="Veterinary AI Assistant", page_icon="🐾", layout="wide")
    _init_session_state()
    _set_styles()

    _render_sidebar()

    def handle_user_message(message: str) -> None:
        st.session_state.chat_history.append({"role": "user", "content": message})
        with st.spinner("Thinking..."):
            try:
                payload = _send_message(message)
                st.session_state.chat_history.append({"role": "assistant", "content": payload})
            except requests.RequestException:
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": {
                            "text": (
                                "Unable to access knowledge sources at the moment. "
                                "Please consult a veterinarian if symptoms persist."
                            ),
                            "response_style": "clinical",
                            "response_mode": "fallback",
                        },
                    }
                )
        st.rerun()

    landing_mode = len(st.session_state.chat_history) == 0

    if landing_mode:
        suggestion = _empty_state()
        if suggestion:
            handle_user_message(suggestion)
        if st.session_state.landing_submit and st.session_state.landing_input.strip():
            message = st.session_state.landing_input.strip()
            st.session_state.landing_input = ""
            st.session_state.landing_submit = False
            handle_user_message(message)
        return

    system_state = {"status": "ready"}
    last = st.session_state.chat_history[-1]
    if last.get("emergency") or last.get("emergency_flag"):
        system_state["status"] = "emergency"
    elif last.get("live_search_flag"):
        system_state["status"] = "live_search"

    _render_top_nav(system_state)
    st.markdown("---")

    for item in st.session_state.chat_history:
        role = item.get("role")
        if role == "user":
            with st.chat_message("user"):
                st.write(item.get("content", ""))
        else:
            with st.chat_message("assistant"):
                _render_response(item.get("content", {}))

    user_input = st.chat_input("Ask me")
    if user_input:
        handle_user_message(user_input.strip())


if __name__ == "__main__":
    main()
