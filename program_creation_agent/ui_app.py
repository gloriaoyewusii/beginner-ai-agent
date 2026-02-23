import json
import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Program Builder Prototype", layout="wide")

st.title("Program Builder (Prototype)")
st.caption("Non-technical UI for generating structured programs via the agent.")

with st.sidebar:
    st.header("Settings")
    model = st.text_input("Model", value="qwen2.5:3b")
    timeout_s = st.slider("Request timeout (seconds)", 180, 300, 360)

st.subheader("Create a Program")

col1, col2 = st.columns([2, 1])
with col1:
    program_name = st.text_input("Program name", value="Introduction to object oriented programming")
with col2:
    complexity_level = st.selectbox("Complexity level", ["beginner", "intermediate", "advanced"])

generate = st.button("Generate program", type="primary")

if generate:
    if not program_name.strip():
        st.error("Please enter a program name.")
        st.stop()

    payload = {
        "program_name": program_name.strip(),
        "complexity_level": complexity_level,
    }

    try:
        with st.spinner("Generating..."):
            r = requests.post(
                f"{API_BASE}/program",
                params={"model": model},
                json=payload,
                timeout=timeout_s,
            )
        if r.status_code != 200:
            st.error("Agent returned an error.")
            st.code(r.text)
            st.stop()

        data = r.json()

        st.success("Program generated!")

        # Pretty display
        st.markdown("### Program Description")
        st.write(data.get("program_description", ""))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Learning Outcomes")
            for x in data.get("learning_outcomes", []):
                st.write(f"• {x}")
        with c2:
            st.markdown("### Learning Objectives")
            for x in data.get("learning_objectives", []):
                st.write(f"• {x}")

        st.markdown("### Prerequisites")
        prereq = data.get("prerequisites", [])
        if prereq:
            for x in prereq:
                st.write(f"• {x}")
        else:
            st.write("None")

        st.markdown("### Career Pathway")
        pathways = data.get("career_pathway", [])
        if pathways:
            st.write(", ".join(pathways))
        else:
            st.write("None")

        st.markdown("### Raw JSON (for QA / debugging)")
        st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json")

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Is FastAPI running on http://127.0.0.1:8000 ?")
    except requests.exceptions.Timeout:
        st.error("Request timed out. Try increasing timeout or using a smaller model.")
    except Exception as e:
        st.error("Unexpected error")
        st.code(str(e))
