import os
import re
import streamlit as st
import google.generativeai as genai
from PIL import Image
from urllib.parse import quote_plus
from dotenv import load_dotenv

# PDF support
from pdf2image import convert_from_bytes

# -------------------------------------------------
# 1. SETUP
# -------------------------------------------------
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ Missing GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=api_key)
MODEL_NAME = "gemini-1.5-flash"   # ✅ stable on cloud

# -------------------------------------------------
# 2. SESSION STATE
# -------------------------------------------------
def activate_tool(tool):
    st.session_state.active_tool = tool

# -------------------------------------------------
# 3. SAFE INPUT CLASSIFIER (FIXED)
# -------------------------------------------------
def classify_input(image=None, text=None):
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = """
    Classify the input into ONE category only.
    Respond with ONLY one word from:
    Prescription, LabReport, Food, Symptoms, Unknown
    """

    content = [prompt]
    if image:
        content.append(image)
    if text:
        content.append(text)

    try:
        res = model.generate_content(content)
        raw = (res.text or "").lower()

        if "prescription" in raw or "medicine" in raw:
            return "Prescription"
        if "lab" in raw or "report" in raw:
            return "LabReport"
        if "food" in raw or "meal" in raw or "calorie" in raw:
            return "Food"
        if "symptom" in raw or "fever" in raw or "pain" in raw or "cough" in raw:
            return "Symptoms"

        return "Unknown"

    except Exception:
        return "Unknown"

# -------------------------------------------------
# 4. AI RESPONSE
# -------------------------------------------------
def get_ai_response(prompt, image=None):
    model = genai.GenerativeModel(MODEL_NAME)
    content = [prompt, image] if image else [prompt]

    try:
        return model.generate_content(content).text
    except:
        return "⚠️ AI service unavailable."

# -------------------------------------------------
# 5. MEDICINE LINK PATCH
# -------------------------------------------------
def patch_medicine_links(text):
    pattern = re.compile(r"\*\*Brand Medicine:\*\* (.*?)\n", re.IGNORECASE)

    def replace(match):
        name = match.group(1).strip()
        link = f"https://www.1mg.com/search/all?name={quote_plus(name)}"
        return f"**Brand Medicine:** [{name}]({link}) 🔗\n"

    return pattern.sub(replace, text)

# -------------------------------------------------
# 6. UI STYLE
# -------------------------------------------------
def apply_ui():
    st.markdown("""
    <style>
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 22px;
    }
    .feature-body {
        background: var(--secondary-background-color);
        border-radius: 18px;
        padding: 28px;
        margin-top: 25px;
        border: 1px solid rgba(120,120,120,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# 7. MAIN APP
# -------------------------------------------------
def main():
    apply_ui()

    if "active_tool" not in st.session_state:
        st.session_state.active_tool = None

    # SIDEBAR
    with st.sidebar:
        st.markdown("### 👨‍⚕️ Threpsi AI")
        st.caption("AI-Routed Health Assistant")
        st.info("Uploads are auto-classified for safety.")

    # HEADER
    st.markdown("# 🏥 Health Command Center")
    st.divider()

    # DASHBOARD
    if st.session_state.active_tool is None:
        st.markdown("## 🧭 Choose a Tool")

        st.button("💊 Generic Medicine Intelligence", on_click=activate_tool, args=("rx",))
        st.button("📋 Lab Report Pro", on_click=activate_tool, args=("lab",))
        st.button("🍎 Nutritional AI", on_click=activate_tool, args=("food",))
        st.button("🌡️ Symptom Checker", on_click=activate_tool, args=("sym",))

    if st.session_state.active_tool:
        st.button("← Back", on_click=activate_tool, args=(None,))

    # -------------------------------------------------
    # PRESCRIPTION (IMAGE + PDF)
    # -------------------------------------------------
    if st.session_state.active_tool == "rx":
        st.markdown("<div class='feature-body'>", unsafe_allow_html=True)
        st.header("💊 Generic Medicine Intelligence")

        file = st.file_uploader(
            "Upload prescription (image or PDF)",
            type=["jpg", "png", "jpeg", "pdf"]
        )

        if file:
            if file.name.endswith(".pdf"):
                images = convert_from_bytes(file.read())
                img = images[0]
            else:
                img = Image.open(file)

            st.image(img, width=300)

            if st.button("Analyze Prescription"):
                if classify_input(image=img) != "Prescription":
                    st.error("❌ This does not look like a prescription.")
                else:
                    with st.spinner("Analyzing..."):
                        res = get_ai_response(
                            """
                            Analyze the prescription.

                            For EACH medicine:
                            - If BRAND → give GENERIC
                            - If already GENERIC → say "Already generic"

                            Return a TABLE with:
                            Medicine Written | Type | Generic Name | Explanation
                            """,
                            img
                        )
                        st.markdown(patch_medicine_links(res))

        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------
    # SYMPTOMS (FIXED)
    # -------------------------------------------------
    if st.session_state.active_tool == "sym":
        st.markdown("<div class='feature-body'>", unsafe_allow_html=True)
        st.header("🌡️ Symptom Checker")

        symptoms = st.text_area("Describe symptoms")

        if st.button("Analyze Symptoms"):
            if classify_input(text=symptoms) != "Symptoms":
                st.error("❌ Please describe symptoms only.")
            else:
                with st.spinner("Analyzing symptoms..."):
                    st.markdown(get_ai_response(
                        f"""
                        User symptoms:
                        {symptoms}

                        Provide:
                        - Possible conditions
                        - Severity level
                        - When to see a doctor
                        - Home care advice
                        """
                    ))

        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
if __name__ == "__main__":
    main()
