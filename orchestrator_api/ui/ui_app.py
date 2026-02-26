import json
import requests
import streamlit as st

st.set_page_config(page_title="Learning Content Pipeline (Prototype)", layout="wide")

# -----------------------------
# Sidebar (Global Settings)
# -----------------------------
with st.sidebar:
    st.header("Settings")
    API_BASE = st.text_input("Orchestrator API Base URL", value="http://127.0.0.1:8000")
    model = st.text_input("Model", value="qwen2.5:3b")
    timeout_s = st.slider("Request timeout (seconds)", 30, 600, 240)

st.title("Learning Content Pipeline (Prototype)")
st.caption("Program → Course → Modules → Lessons (via Orchestrator API)")

# -----------------------------
# Session State (Pipeline Memory)
# -----------------------------
if "program" not in st.session_state:
    st.session_state["program"] = None
if "course" not in st.session_state:
    st.session_state["course"] = None
if "modules" not in st.session_state:
    st.session_state["modules"] = None
if "lessons" not in st.session_state:
    st.session_state["lessons"] = None


# -----------------------------
# HTTP Helpers
# -----------------------------
def post_json(path: str, payload: dict):
    url = f"{API_BASE}{path}"
    r = requests.post(url, params={"model": model}, json=payload, timeout=timeout_s)
    return r


def show_error(r: requests.Response):
    st.error("API returned an error.")
    try:
        st.json(r.json())
    except Exception:
        st.code(r.text)


def show_raw_json_block(data: dict, title: str = "Raw JSON (QA / debugging)"):
    with st.expander(title):
        st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json")


# -----------------------------
# Display Helpers
# -----------------------------
def render_program(data: dict):
    st.success("Program generated ✅")

    st.markdown("### Program Name")
    st.write(data.get("program_name", "(not provided)"))

    st.markdown("### Complexity Level")
    st.write(data.get("complexity_level", "(not provided)"))

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
    st.write(", ".join(pathways) if pathways else "None")

    show_raw_json_block(data)


def render_course(data: dict):
    st.success("Course generated ✅")

    st.markdown("### Course Title")
    st.write(data.get("course_title", ""))

    st.markdown("### Course Description")
    st.write(data.get("course_description", ""))

    st.markdown("### Learning Objectives")
    for x in data.get("learning_objectives", []):
        st.write(f"• {x}")


    st.markdown("### Intended Learners")
    st.write(data.get("learners_description", ""))

    st.markdown("### Prerequisites")
    prereq = data.get("prerequisites", [])
    if prereq:
        for x in prereq:
            st.write(f"• {x}")
    else:
        st.write("None")

    st.markdown("### Career Pathway")
    pathways = data.get("career_pathway", [])
    st.write(", ".join(pathways) if pathways else "None")

    show_raw_json_block(data)


# -----------------------------
# Tabs
# -----------------------------
tab_program, tab_course, tab_modules, tab_lessons = st.tabs(
    ["1) Program", "2) Course", "3) Modules (coming)", "4) Lessons (coming)"]
)

# ============================================================
# 1) PROGRAM TAB
# ============================================================
with tab_program:
    st.subheader("Create a Program")

    col1, col2 = st.columns([2, 1])
    with col1:
        program_name = st.text_input(
            "Program name",
            value="Introduction to Object Oriented Programming",
        )
    with col2:
        complexity_level = st.selectbox(
            "Complexity level",
            ["beginner", "intermediate", "advanced"],
            index=0,
        )

    if st.button("Generate program", type="primary"):
        if not program_name.strip():
            st.error("Please enter a program name.")
            st.stop()

        payload = {"program_name": program_name.strip(), "complexity_level": complexity_level}

        try:
            with st.spinner("Generating program..."):
                r = post_json("/program", payload)

            if r.status_code != 200:
                show_error(r)
                st.stop()

            data = r.json()
            st.session_state["program"] = data

            # reset downstream when program changes
            st.session_state["course"] = None
            st.session_state["modules"] = None
            st.session_state["lessons"] = None

            render_program(data)

        except requests.exceptions.ConnectionError:
            st.error(f"Could not connect to the API. Is Orchestrator running on {API_BASE}?")
        except requests.exceptions.Timeout:
            st.error("Request timed out. Try increasing timeout or using a smaller model.")
        except Exception as e:
            st.error("Unexpected error")
            st.code(str(e))

    if st.session_state["program"]:
        st.divider()
        st.markdown("## Latest Program Output")
        render_program(st.session_state["program"])


# ============================================================
# 2) COURSE TAB
# ============================================================
with tab_course:
    st.subheader("Create a Course")

    program = st.session_state.get("program")

    st.markdown("### A) Generate Course from Latest Program (Linked)")
    if not program:
        st.warning("No program generated yet. Go to the Program tab first.")
    else:
        # Prefill using program output (since you now return name + level)
        prefill_title = program.get("program_name", "Course Title")
        prefill_level = program.get("complexity_level", "beginner")

        colA, colB = st.columns([2, 1])
        with colA:
            course_title_prefill = st.text_input("Course title (prefilled)", value=prefill_title, key="course_title_prefill")
        with colB:
            course_level_prefill = st.selectbox(
                "Complexity level (prefilled)",
                ["beginner", "intermediate", "advanced"],
                index=["beginner", "intermediate", "advanced"].index(prefill_level) if prefill_level in ["beginner", "intermediate", "advanced"] else 0,
                key="course_level_prefill",
            )

        if st.button("Generate course from this program", type="primary"):
            try:
                # Best API design: orchestrator endpoint that maps program → course
                # We'll send the entire program object; orchestrator handles mapping.
                with st.spinner("Generating course from program..."):
                    r = post_json("/course-from-program", program)

                if r.status_code != 200:
                    show_error(r)
                    st.stop()

                data = r.json()
                st.session_state["course"] = data

                # reset downstream when course changes
                st.session_state["modules"] = None
                st.session_state["lessons"] = None

                render_course(data)

            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to the API. Is Orchestrator running on {API_BASE}?")
            except requests.exceptions.Timeout:
                st.error("Request timed out. Try increasing timeout or using a smaller model.")
            except Exception as e:
                st.error("Unexpected error")
                st.code(str(e))

    st.divider()

    st.markdown("### B) Generate Course (Structured Input)")
    col1, col2 = st.columns([2, 1])
    with col1:
        course_title = st.text_input("Course title", value="Foundations of Data Science", key="course_title_direct")
    with col2:
        course_level = st.selectbox("Complexity level", ["beginner", "intermediate", "advanced"], index=0, key="course_level_direct")

    if st.button("Generate course (structured)"):
        payload = {"course_title": course_title.strip(), "complexity_level": course_level}
        try:
            with st.spinner("Generating course..."):
                r = post_json("/course", payload)

            if r.status_code != 200:
                show_error(r)
                st.stop()

            data = r.json()
            st.session_state["course"] = data
            st.session_state["modules"] = None
            st.session_state["lessons"] = None

            render_course(data)

        except requests.exceptions.ConnectionError:
            st.error(f"Could not connect to the API. Is Orchestrator running on {API_BASE}?")
        except requests.exceptions.Timeout:
            st.error("Request timed out. Try increasing timeout or using a smaller model.")
        except Exception as e:
            st.error("Unexpected error")
            st.code(str(e))

    st.divider()

    st.markdown("### C) Generate Course (From Text)")
    text = st.text_area(
        "Describe the course you want",
        value="I want a course that teaches me how to write academic research articles",
        height=120,
        key="course_text",
    )

    if st.button("Generate course (from text)"):
        try:
            with st.spinner("Generating course from text..."):
                r = post_json("/course-from-text", {"text": text})

            if r.status_code != 200:
                show_error(r)
                st.stop()

            data = r.json()
            st.session_state["course"] = data
            st.session_state["modules"] = None
            st.session_state["lessons"] = None

            render_course(data)

        except requests.exceptions.ConnectionError:
            st.error(f"Could not connect to the API. Is Orchestrator running on {API_BASE}?")
        except requests.exceptions.Timeout:
            st.error("Request timed out. Try increasing timeout or using a smaller model.")
        except Exception as e:
            st.error("Unexpected error")
            st.code(str(e))

    if st.session_state["course"]:
        st.divider()
        st.markdown("## Latest Course Output")
        render_course(st.session_state["course"])


# ============================================================
# 3) MODULES TAB (placeholder for next agent)
# ============================================================
with tab_modules:
    st.subheader("Modules (next agent)")
    st.info("When you build the Module agent, we’ll add endpoints like /modules-from-course.")

    if st.session_state["course"]:
        st.markdown("### Latest Course Context (will feed Module agent)")
        st.json(st.session_state["course"])
    else:
        st.warning("Generate a course first.")


# ============================================================
# 4) LESSONS TAB (placeholder for next agent)
# ============================================================
with tab_lessons:
    st.subheader("Lessons (next agent)")
    st.info("When you build the Lesson agent, we’ll add endpoints like /lessons-from-module.")

    if st.session_state["modules"]:
        st.markdown("### Latest Module Context (will feed Lesson agent)")
        st.json(st.session_state["modules"])
    else:
        st.warning("Generate modules first (Module agent not added yet).")
