import os
import re
import streamlit as st
import google.generativeai as genai
from PIL import Image
from urllib.parse import quote_plus
from dotenv import load_dotenv

# 1. SETUP

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("Missing API Key. Please configure it in Streamlit Secrets or a .env file.")
    st.stop()

genai.configure(api_key=api_key)
MODEL_NAME = "gemini-3-flash-preview" 

def activate_tool(tool):
    st.session_state.active_tool = tool

def classify_input(image=None, text=None):
    """
    Determines what the user input is.
    Returns: Prescription | LabReport | Food | Symptoms | Unknown
    """
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = """
    Identify the type of the input.
    Respond with ONLY one word:
    Prescription, LabReport, Food, Symptoms, Unknown
    """

    content = [prompt]
    if image:
        content.append(image)
    if text:
        content.append(text)

    try:
        res = model.generate_content(content)
        return res.text.strip()
    except:
        return "Unknown"


def get_ai_response(prompt, image=None):
    model = genai.GenerativeModel(MODEL_NAME)
    content = [prompt, image] if image else [prompt]
    try:
        response = model.generate_content(content)
        return response.text
    except Exception as e:
        return "⚠️ AI service temporarily unavailable."

def patch_medicine_links(text):
    pattern = re.compile(r"\*\*Brand Medicine:\*\* (.*?)\n", re.IGNORECASE)
    def replace(match):
        name = match.group(1).strip()
        link = f"https://www.1mg.com/search/all?name={quote_plus(name)}"
        return f"**Brand Medicine:** [{name}]({link}) 🔗\n"
    return pattern.sub(replace, text)

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

def main():
    apply_ui()

    if "active_tool" not in st.session_state:
        st.session_state.active_tool = None

    # SIDEBAR
    with st.sidebar:
        st.markdown("### 👨‍⚕️ Threpsi AI")
        st.caption("AI-Routed Health Assistant")
        st.divider()
        st.info("Input is automatically classified for safety.")
        st.divider()

    # HEADER
    st.markdown("# 🏥 Health Command Center")
    st.write("AI automatically understands your input and guides you.")
    st.divider()

    # DASHBOARD
    if st.session_state.active_tool is None:
        st.markdown("## 🧭 Choose a Tool")

        st.markdown("<div class='feature-grid'>", unsafe_allow_html=True)

        st.button("💊 Generic Medicine Intelligence", on_click=activate_tool, args=("rx",))
        st.caption("Upload prescriptions only")

        st.button("📋 Lab Report Pro", on_click=activate_tool, args=("lab",))
        st.caption("Upload lab reports only")

        st.button("🍎 Nutritional AI", on_click=activate_tool, args=("food",))
        st.caption("Upload food images")

        st.button("🌡️ Symptom Checker", on_click=activate_tool, args=("sym",))
        st.caption("Describe symptoms in text")

        st.markdown("</div>", unsafe_allow_html=True)

    # BACK BUTTON
    if st.session_state.active_tool:
        st.button("← Back", on_click=activate_tool, args=(None,))

    
    # 💊 PRESCRIPTION
    if st.session_state.active_tool == "rx":
        st.markdown("<div class='feature-body'>", unsafe_allow_html=True)
        st.header("💊 Generic Medicine Intelligence")

        file = st.file_uploader("Upload prescription image", type=["jpg","png","jpeg"])
        if file:
            img = Image.open(file)
            st.image(img, width=280)

            if st.button("Analyze Prescription"):
                doc_type = classify_input(image=img)

                if doc_type != "Prescription":
                    st.error(f"❌ This appears to be a **{doc_type}**. Please use the correct section.")
                else:
                    with st.spinner("Analyzing prescription..."):
                        res = get_ai_response(                       
                            """
                            Analyze this prescription carefully.
                        
                            Rules:
                            1. If a medicine is a BRAND, suggest its GENERIC name.
                            2. If a medicine is ALREADY GENERIC, clearly state: "Already generic medicine".
                            3. Do NOT invent medicines.
                            4. Add safety note if prescription is old.
                        
                            Output format (MANDATORY):
                            Medicine Name | Type (Brand/Generic) | Generic Name / Status | Use
                        
                            Example:
                            Crocin | Brand | Paracetamol | Fever & pain
                            Paracetamol | Generic | Already generic medicine | Fever & pain
                            """,
                            img
                        )
                        st.markdown(patch_medicine_links(res))
        st.markdown("</div>", unsafe_allow_html=True)

    # 📋 LAB REPORT
    if st.session_state.active_tool == "lab":
        st.markdown("<div class='feature-body'>", unsafe_allow_html=True)
        st.header("📋 Lab Report Pro")

        file = st.file_uploader("Upload lab report image", type=["jpg","png","jpeg"])
        if file:
            img = Image.open(file)
            st.image(img, width=350)

            if st.button("Analyze Lab Report"):
                doc_type = classify_input(image=img)

                if doc_type != "LabReport":
                    st.error(f"❌ This appears to be a **{doc_type}**. Please switch sections.")
                else:
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
                doc_type = classify_input(image=img)

                if doc_type != "Food":
                    st.error("❌ This does not look like food. Please upload a food image.")
                else:
                    with st.spinner("Estimating calories..."):
                        st.markdown(get_ai_response(
                            "Estimate calories and macros for the food items in this image.",
                            img
                        ))
        st.markdown("</div>", unsafe_allow_html=True)

    # 🌡️ SYMPTOMS
    if st.session_state.active_tool == "sym":
        st.markdown("<div class='feature-body'>", unsafe_allow_html=True)
        st.header("🌡️ Symptom Checker")

        symptoms = st.text_area("Describe your symptoms")
        if st.button("Analyze Symptoms"):
            doc_type = classify_input(text=symptoms)

            if doc_type != "Symptoms":
                st.error("❌ Please describe symptoms here, not upload reports.")
            else:
                with st.spinner("Analyzing symptoms..."):
                    st.markdown(get_ai_response(
                        f"Provide possible conditions and advice for: {symptoms}"
                    ))
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()



