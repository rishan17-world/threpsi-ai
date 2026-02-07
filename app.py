import os
import re
import streamlit as st
import google.generativeai as genai
from PIL import Image
from urllib.parse import quote_plus
from dotenv import load_dotenv

# --- 1. SETUP & MODERN MODEL SELECTION ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("Missing GOOGLE_API_KEY. Set it in .env or Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# Using Gemini 3 Flash for maximum speed and handwriting accuracy
MODEL_NAME = "gemini-2.5-flash-lite"
# --- 2. LOGIC FUNCTIONS ---

def activate_tool(tool):
    st.session_state.active_tool = tool

def get_ai_response(prompt, image=None):
    """Core function to get multimodal responses with retry logic."""
    model = genai.GenerativeModel(MODEL_NAME)
    content = [prompt, image] if image else [prompt]
    try:
        res = model.generate_content(content)
        return res.text
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def patch_medicine_links(text):
    """Turns brand names into clickable health links."""
    pattern = re.compile(r"\*\*Brand Medicine:\*\* (.*?)\n", re.IGNORECASE)
    def replace(match):
        name = match.group(1).strip()
        link = f"https://www.1mg.com/search/all?name={quote_plus(name)}"
        return f"**Brand Medicine:** [{name}]({link}) 🔗\n"
    return pattern.sub(replace, text)

# --- 3. UI STYLE ---

def apply_ui():
    st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: 600; }
    .feature-body {
        background: rgba(120, 120, 120, 0.05);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(120,120,120,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. MAIN APP ---

def main():
    st.set_page_config(page_title="Threpsi AI 2026", page_icon="🏥", layout="wide")
    apply_ui()

    if "active_tool" not in st.session_state:
        st.session_state.active_tool = None

    # Sidebar Navigation
    with st.sidebar:
        st.title("👨‍⚕️ Threpsi AI")
        st.info("Medical Assistant powered by Gemini 3 Flash.")
        if st.session_state.active_tool:
            if st.button("⬅️ Home Dashboard"):
                activate_tool(None)
                st.rerun()

    # DASHBOARD
    if st.session_state.active_tool is None:
        st.header("🏥 Health Command Center")
        st.write("Select a module to begin your health analysis.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("💊 Generic Medicine", on_click=activate_tool, args=("rx",))
            st.button("📋 Lab Report Pro", on_click=activate_tool, args=("lab",))
        with col2:
            st.button("🍎 Nutritional AI", on_click=activate_tool, args=("food",))
            st.button("🌡️ Symptom Checker", on_click=activate_tool, args=("sym",))

    # --- MODULE: PRESCRIPTION ---
    elif st.session_state.active_tool == "rx":
        st.header("💊 Medicine Intelligence")
        file = st.file_uploader("Upload prescription photo", type=["jpg","png","jpeg"])
        if file:
            img = Image.open(file)
            st.image(img, width=400, caption="Uploaded Prescription")
            if st.button("Analyze for Generic Alternatives"):
                with st.spinner("Extracting handwritten data..."):
                    prompt = """Analyze this prescription. Create a Markdown table with:
                    | Medicine | Original Type | Generic Name | Why switch? |
                    Use 'Brand Medicine: [Name]' format for the search link to work."""
                    res = get_ai_response(prompt, img)
                    st.markdown(patch_medicine_links(res))
        st.warning("⚠️ For informational use only. Verify with your pharmacist.")

    # --- MODULE: LABS ---
    elif st.session_state.active_tool == "lab":
        st.header("📋 Lab Report Interpretation")
        file = st.file_uploader("Upload lab results", type=["jpg","png","jpeg"])
        if file:
            img = Image.open(file)
            st.image(img, width=400)
            if st.button("Explain Results"):
                with st.spinner("Reading values..."):
                    res = get_ai_response("Explain these lab results. Highlight abnormal values and suggest questions for a doctor.", img)
                    st.markdown(res)

    # --- MODULE: FOOD ---
    elif st.session_state.active_tool == "food":
        st.header("🍎 Nutritional Analysis")
        file = st.file_uploader("Upload meal photo", type=["jpg","png","jpeg"])
        if file:
            img = Image.open(file)
            st.image(img, width=400)
            if st.button("Calculate Macros"):
                with st.spinner("Analyzing plate..."):
                    res = get_ai_response("Estimate calories, protein, carbs, and fats for this meal.", img)
                    st.markdown(res)

    # --- MODULE: SYMPTOMS ---
    elif st.session_state.active_tool == "sym":
        st.header("🌡️ Symptom Checker")
        desc = st.text_area("How are you feeling?")
        if st.button("Check Symptoms"):
            with st.spinner("Analyzing symptoms..."):
                res = get_ai_response(f"Evaluate these symptoms: {desc}. List potential causes and suggest when to seek urgent care.")
                st.markdown(res)

if __name__ == "__main__":
    main()

