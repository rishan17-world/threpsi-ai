import os
import re
import streamlit as st
import google.generativeai as genai
from PIL import Image
from urllib.parse import quote_plus
from dotenv import load_dotenv


# 1. SETUP (LOCAL + STREAMLIT CLOUD)

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("Missing GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=api_key)
MODEL_NAME = "models/gemini-1.5-flash"

# 2. SESSION STATE

def activate_tool(tool):
    st.session_state.active_tool = tool

# 3. CLASSIFIER (SAFE, NON-BLOCKING)

def classify_input(image=None, text=None):
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = """
    Classify the input into ONE category only:
    Prescription, LabReport, Food, Symptoms, Unknown
    """

    content = [prompt]
    if image:
        content.append(image)
    if text:
        content.append(text)

    try:
        res = model.generate_content(content)
        raw = res.text or ""
        label = raw.strip().split()[0].lower()

        if "prescription" in label:
            return "Prescription"
        if "lab" in label:
            return "LabReport"
        if "food" in label:
            return "Food"
        if "symptom" in label:
            return "Symptoms"

        return "Unknown"

    except Exception:
        return "Unknown"

# 4. AI RESPONSE

def get_ai_response(prompt, image=None):
    model = genai.GenerativeModel(MODEL_NAME)
    content = [prompt, image] if image else [prompt]

    for _ in range(2):  # retry once
        try:
            res = model.generate_content(content)
            return res.text
        except Exception as e:
            last_error = e

    st.error(f"Gemini Error: {last_error}")
    return "⚠️ AI service temporarily unavailable."

def patch_medicine_links(text):
    pattern = re.compile(r"\*\*Brand Medicine:\*\* (.*?)\n", re.IGNORECASE)
    def replace(match):
        name = match.group(1).strip()
        link = f"https://www.1mg.com/search/all?name={quote_plus(name)}"
        return f"**Brand Medicine:** [{name}]({link}) 🔗\n"
    return pattern.sub(replace, text)

# 5. UI STYLE

def apply_ui():
    st.markdown("""
    <style>
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 22px;
        margin-top: 25px;
    }
    .feature-body {
        background: var(--secondary-background-color);
        border-radius: 20px;
        padding: 28px;
        margin-top: 30px;
        border: 1px solid rgba(120,120,120,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# 6. MAIN APP

def main():
    apply_ui()

    if "active_tool" not in st.session_state:
        st.session_state.active_tool = None

    # SIDEBAR
    with st.sidebar:
        st.markdown("### 👨‍⚕️ Threpsi AI")
        st.caption("AI-Routed Health Assistant")
        st.divider()
        st.info("Classification is advisory — analysis always runs.")
        st.divider()

    # HEADER
    st.markdown("# 🏥 Health Command Center")
    st.write("AI understands your input and guides you safely.")
    st.divider()

    # DASHBOARD
    if st.session_state.active_tool is None:
        st.markdown("## 🧭 Choose a Tool")

        st.markdown("<div class='feature-grid'>", unsafe_allow_html=True)

        st.button("💊 Generic Medicine Intelligence", on_click=activate_tool, args=("rx",))
        st.button("📋 Lab Report Pro", on_click=activate_tool, args=("lab",))
        st.button("🍎 Nutritional AI", on_click=activate_tool, args=("food",))
        st.button("🌡️ Symptom Checker", on_click=activate_tool, args=("sym",))

        st.markdown("</div>", unsafe_allow_html=True)

    # BACK
    if st.session_state.active_tool:
        st.button("← Back", on_click=activate_tool, args=(None,))

    # PRESCRIPTION (NO BLOCKING)
    
    if st.session_state.active_tool == "rx":
        st.markdown("<div class='feature-body'>", unsafe_allow_html=True)
        st.header("💊 Generic Medicine Intelligence")

        file = st.file_uploader(
            "Upload prescription (image or PDF)",
            type=["jpg", "png", "jpeg"]
        )

        if file:
            img = Image.open(file)
            st.image(img, width=300)

            if st.button("Analyze Prescription"):
                doc_type = classify_input(image=img)

                if doc_type not in ["Prescription", "Unknown"]:
                    st.warning(
                        f"⚠️ Detected **{doc_type}**, but continuing — prescriptions vary."
                    )

                with st.spinner("Analyzing prescription..."):
                    res = get_ai_response(
                        """
                        Analyze this doctor's prescription carefully.

                        For EACH medicine:
                        - If BRAND → suggest GENERIC
                        - If ALREADY GENERIC → say "Already generic"

                        Output as a table:
                        Medicine Written | Type | Generic Name | Explanation

                        Be precise. Do not hallucinate.
                        """,
                        img
                    )
                    st.markdown(patch_medicine_links(res))

        st.caption("⚠️ Informational only. Consult a licensed doctor.")
        st.markdown("</div>", unsafe_allow_html=True)

    # LAB REPORT
    
    if st.session_state.active_tool == "lab":
        st.markdown("<div class='feature-body'>", unsafe_allow_html=True)
        st.header("📋 Lab Report Pro")

        file = st.file_uploader("Upload lab report image", type=["jpg","png","jpeg"])
        if file:
            img = Image.open(file)
            st.image(img, width=350)

            if st.button("Analyze Lab Report"):
                with st.spinner("Analyzing lab report..."):
                    st.markdown(get_ai_response(
                        "Analyze this lab report and highlight abnormal values.",
                        img
                    ))
        st.markdown("</div>", unsafe_allow_html=True)

    # 🍎 FOOD
    
    if st.session_state.active_tool == "food":
        st.markdown("<div class='feature-body'>", unsafe_allow_html=True)
        st.header("🍎 Nutritional AI")

        file = st.file_uploader("Upload food image", type=["jpg","png","jpeg"])
        if file:
            img = Image.open(file)
            st.image(img, width=350)

            if st.button("Estimate Calories"):
                with st.spinner("Estimating calories..."):
                    st.markdown(get_ai_response(
                        "Estimate calories and macros for the food shown.",
                        img
                    ))
        st.markdown("</div>", unsafe_allow_html=True)

    
    # SYMPTOMS (FIXED)
    
    if st.session_state.active_tool == "sym":
        st.markdown("<div class='feature-body'>", unsafe_allow_html=True)
        st.header("🌡️ Symptom Checker")

        symptoms = st.text_area("Describe your symptoms")

        if st.button("Analyze Symptoms"):
            if not symptoms.strip():
                st.error("Please describe symptoms.")
            else:
                with st.spinner("Analyzing symptoms..."):
                    st.markdown(get_ai_response(
                        f"Provide possible causes and advice for: {symptoms}"
                    ))
        st.markdown("</div>", unsafe_allow_html=True)


# ENTRY

if __name__ == "__main__":
    main()


