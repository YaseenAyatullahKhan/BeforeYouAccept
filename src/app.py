import streamlit as st
from utils import fetch_full_analysis, generate_pdf, get_base64_bin_file
import time

# --- 1. PAGE CONFIG & DESIGN ---
st.set_page_config(
    page_title="BeforeYouAccept",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Background and Removing the "Empty Bar"
try:
    img_base64 = get_base64_bin_file("assets/background.jpg")
    bg_style = f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
    """
except FileNotFoundError:
    bg_style = "<style> .stApp { background: #1e0030; } "

st.markdown(bg_style + """
    <style>
    /* HIDE STREAMLIT HEADER & REDUCE TOP GAP */
    header[data-testid="stHeader"] {
        background: rgba(0,0,0,0);
        height: 0px;
    }
    
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }

    /* REMOVE THE GAP BELOW THE TITLE */
    h1 {
        margin-top: -10px !important;
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }

    .stApp { color: white; }
    
    .glass-box {
        height: 1500
        width: 100%
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 10px;
    }

    /* Style for the tabs */
    div[data-testid="stHorizontalBlock"] button {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(157, 91, 239, 0.5) !important;
    }

    /* Remove standard Streamlit padding at the top */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 90%; /* Allows the content to expand significantly */
    }

    .info-section, .glass-box {
        height: 1500
        width: 90%
        background: rgba(255, 255, 255, 0.05);
        padding: 3rem; /* Increased padding for a more spacious feel */
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 2rem;
        width: 100%; /* Ensure it fills the wide container */
        color: #ffffff; /* Fixes your black text issue */
    }

    /* Keep the disclaimer text readable but distinct */
    .disclaimer-text {
        font-size: 0.95rem;
        color: #e0e0e0;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE INITIALIZATION ---
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "results" not in st.session_state:
    st.session_state.results = {} # Will hold all JamAI data
if "risk_header" not in st.session_state:
    st.session_state.risk_header = ""
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "analysis_summary"

# --- 3. PAGE LOGIC: LANDING PAGE ---
if st.session_state.page == "landing":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("assets/logo.png", width=250)
        except:
            st.title("🧐 BeforeYouAccept")
        
        st.markdown("<h1 style='text-align: center;'>Know Those T&Cs Right 🧐</h1>", unsafe_allow_html=True)
        
        if st.button("Get T&C Alerts", use_container_width=True, type="primary"):
            st.session_state.page = "execution"
            st.rerun()
        st.markdown("---") # Visual separator
    
        # --- ABOUT SECTION ---
        st.markdown("""
        <div class='info-section'>
            <h2>🛡️ About BYA</h2>
            <p>
                BeforeYouAccept is an AI-powered legal audit tool designed to protect consumers in Malaysia. 
                By leveraging the <b>Malaysian Consumer Protection Act 1999</b> and the 
                <b>Personal Data Protection Act 2010</b>, we scan complex Terms & Conditions 
                to find hidden risks so you don't have to.
                <br><br>
                Made by Yaseen Ayatullah Khan | 2025
            </p>
        </div>
        """, unsafe_allow_html=True)
    
        # --- DISCLAIMER SECTION ---
        st.markdown("""
        <div class='info-section'>
            <h2>⚖️ Legal Disclaimer</h2>
            <div class='disclaimer-text'>
                This tool is powered by Artificial Intelligence and is for <b>informational purposes only</b>. 
                It does not constitute professional legal advice. While we strive for accuracy based 
                on Malaysian Law, the AI may occasionally misinterpret clauses. 
                <br><br>
                Always consult with a qualified legal professional for serious contractual matters. 
                By using this tool, you acknowledge that "Before You Accept" is not liable for any 
                decisions made based on this analysis.
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 4. PAGE LOGIC: EXECUTION PAGE ---
else:
    st.title("T&C Risk Analyzer")
    
    # --- INPUT SECTION ---
    with st.container():
        st.markdown("<div>", unsafe_allow_html=True)
        input_type = st.radio("Choose Input Method:", ["Paste Text", "Upload PDF"], horizontal=True)
        
        tnc_input = ""
        if input_type == "Paste Text":
            tnc_input = st.text_area("Paste the T&C text here:", height=200, placeholder="Ctrl+A, Ctrl+C...")
        else:
            uploaded_file = st.file_uploader("Upload PDF", type="pdf")
            st.info("PDF extraction active in backend.")

        analyze_btn = st.button("Analyze Malaysian Compliance 🚀", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- EXECUTION ---
    if analyze_btn and tnc_input:
        with st.status("Performing Single-Pass Legal Audit...", expanded=True) as status:
            # ONE SINGLE CALL: Fetches all columns into a dictionary
            full_data = fetch_full_analysis(tnc_input)
            
            if full_data:
                st.session_state.results = full_data
                # Risk score is part of the dictionary
                st.session_state.risk_header = full_data.get("risk_scoring", "⚠️ Score Unavailable")
                status.update(label="Analysis Complete!", state="complete", expanded=False)
            else:
                st.error("JamAI failed to analyze the document.")

    # --- RESULTS SECTION ---
    if st.session_state.risk_header:
        # Clean the header if it contains the JamAI internal error message
        display_header = st.session_state.risk_header
        if "KeyError" in display_header or "Output column" in display_header:
            display_header = "⚠️ Analysis Column Mismatch - Check JamAI Column IDs"
    
        st.markdown(f"<h2 style='text-align: center; color: #9d5bef;'>{display_header}</h2>", unsafe_allow_html=True)
        
        # Fake Tabs using columns
        t1, t2, t3 = st.columns(3)
        if t1.button("📜 Summary", use_container_width=True):
            st.session_state.active_tab = "analysis_summary"
        if t2.button("⚠️ Critical Alerts", use_container_width=True):
            st.session_state.active_tab = "critical_alerts"
        if t3.button("🔮 Implications", use_container_width=True):
            st.session_state.active_tab = "long_term_implications"

        # Content Display Area
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        active = st.session_state.active_tab
        display_text = st.session_state.results.get(active, "Click a tab to view details.")
        
        # Formatting for Critical Alerts
        if active == "critical_alerts":
            display_text = display_text.replace("- ", "⚠️ ").replace("* ", "⚠️ ")
            
        st.write(f"### {active.replace('_', ' ').title()}")
        st.write(display_text)
        st.markdown("</div>", unsafe_allow_html=True)

        # --- EXPORT ---
        st.markdown("<br>", unsafe_allow_html=True)
        pdf_data = generate_pdf(st.session_state.results)
        st.download_button(
            label="📥 Export Full Report to PDF",
            data=pdf_data,
            file_name="BYA_Legal_Audit.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    if st.button("← Back to Home", type="tertiary"):
        st.session_state.page = "landing"
        st.rerun()
