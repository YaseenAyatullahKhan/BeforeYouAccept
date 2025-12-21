import streamlit as st
from utils import fetch_analysis_column, generate_pdf
import time
from utils import get_base64_bin_file

# --- 1. PAGE CONFIG & DESIGN ---
st.set_page_config(
    page_title="BeforeYouAccept",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Purple Gradient and Design
try:
    bin_str = get_base64_bin_file('assets/background.jpg')
    bg_img_style = f"""
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
    """
except FileNotFoundError:
    # Fallback to the purple gradient if image isn't found
    bg_img_style = """
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #1e0030 0%, #4b0082 50%, #1e0030 100%);
        }
    """

st.markdown(f"""
    <style>
    {bg_img_style}
    
    /* FIX THE EMPTY BAR: Make header transparent and zero height */
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
        height: 0px;
    }}
    
    /* REMOVE PADDING: Bring content to the very top */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 0rem;
    }}

    /* Your existing button and glassmorphism styles */
    .stApp {{ color: white; }}
    div[data-testid="stHorizontalBlock"] button {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid #9d5bef !important;
        color: white !important;
        border-radius: 10px;
    }}
    .glass-box {{
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE INITIALIZATION ---
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "results" not in st.session_state:
    st.session_state.results = {}
if "risk_header" not in st.session_state:
    st.session_state.risk_header = ""

# --- 3. PAGE LOGIC: LANDING PAGE ---
if st.session_state.page == "landing":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Assuming logo.png is in assets/ folder
        try:
            st.image("assets/logo.png", width=200)
        except:
            st.title("🧐 BeforeYouAccept")
            
        st.markdown("<h1 class='hero-text'>Know Those T&Cs Right 🧐</h1>", unsafe_allow_html=True)
        
        # Space for your background hero image placeholder
        st.image("assets/background.jpg", use_container_width=True)
        
        if st.button("Get T&C Alerts", use_container_width=True, type="primary"):
            st.session_state.page = "execution"
            st.rerun()

# --- 4. PAGE LOGIC: EXECUTION PAGE ---
else:
    st.title("T&C Risk Analyzer")
    
    # --- INPUT SECTION ---
    with st.container():
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        
        # Multi-option Input
        input_type = st.radio("Choose Input Method:", ["Paste Text", "Upload PDF"], horizontal=True)
        
        tnc_input = ""
        if input_type == "Paste Text":
            tnc_input = st.text_area("Paste the T&C text here:", height=250, placeholder="Scroll to the bottom, Ctrl+A, Ctrl+C...")
        else:
            uploaded_file = st.file_uploader("Upload T&C Document (PDF)", type="pdf")
            if uploaded_file:
                # Basic text extraction from PDF can be added here or in utils.py
                # For this prototype, we'll assume text paste for full accuracy
                st.warning("PDF Text Extraction requires 'PyPDF2' - using pasted text for now.")
        
        analyze_btn = st.button("Analyze Malaysian Compliance 🚀", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- EXECUTION & RESULTS ---
    if analyze_btn and tnc_input:
        with st.status("Analyzing against PUA 2024 & CPA 1999...", expanded=True) as status:
            # 1. Get Risk Score first (Low Token Cost)
            st.write("Calculating Risk Score...")
            st.session_state.risk_header = fetch_analysis_column(tnc_input, "risk_scoring")
            
            # 2. Reset other results to force "Load on Demand"
            st.session_state.results = {}
            st.session_state.current_text = tnc_input # Save text for tab calls
            
            status.update(label="Analysis Complete!", state="complete", expanded=False)
        
        # Auto-scroll anchor
        st.markdown("<div id='results-top'></div>", unsafe_allow_html=True)
        st.components.v1.html("""<script>window.parent.document.getElementById('results-top').scrollIntoView({behavior: 'smooth'});</script>""", height=0)

    # --- TAB SECTION (LOAD ON DEMAND) ---
    if st.session_state.risk_header:
        st.divider()
        st.subheader(st.session_state.risk_header)
        
        # Using Columns as fake "Tabs" for Load-On-Demand control
        t1, t2, t3 = st.columns(3)
        
        # Column 1: Summary
        if t1.button("📜 Summary", use_container_width=True):
            with st.spinner("Summarizing..."):
                st.session_state.results["analysis_summary"] = fetch_analysis_column(st.session_state.current_text, "analysis_summary")
        
        # Column 2: Critical Alerts
        if t2.button("⚠️ Critical Alerts", use_container_width=True):
            with st.spinner("Finding Violations..."):
                st.session_state.results["critical_alerts"] = fetch_analysis_column(st.session_state.current_text, "critical_alerts")
        
        # Column 3: Implications
        if t3.button("🔮 Implications", use_container_width=True):
            with st.spinner("Forecasting Risks..."):
                st.session_state.results["long_term_implications"] = fetch_analysis_column(st.session_state.current_text, "long_term_implications")

        # Display Area
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        # Show whichever result was last fetched
        for key in ["analysis_summary", "critical_alerts", "long_term_implications"]:
            if key in st.session_state.results:
                label = key.replace("_", " ").title()
                st.write(f"### {label}")
                st.write(st.session_state.results[key])
                st.divider()
        st.markdown("</div>", unsafe_allow_html=True)

        # --- EXPORT SECTION ---
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.results:
            pdf_data = generate_pdf(st.session_state.results)
            st.download_button(
                label="📥 Export Full Report to PDF",
                data=pdf_data,
                file_name="TnC_Legal_Report_Malaysia.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    # Back to Landing Button
    if st.button("← Back to Home", type="tertiary"):
        st.session_state.page = "landing"
        st.rerun()
