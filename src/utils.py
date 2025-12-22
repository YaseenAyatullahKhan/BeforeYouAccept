import streamlit as st
from jamaibase import JamAI, types as t
from fpdf import FPDF
import time
import base64
import re

# Helper for images
def get_base64_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Initialize JamAI Client
def get_jamai_client():
    api_key = st.secrets["JAMAI_API_KEY"]
    project_id = st.secrets["JAMAI_PROJECT_ID"]
    return JamAI(token=api_key, project_id=project_id)

def fetch_full_analysis(tnc_text):
    """
    Fetches all analysis columns in a single JamAI row addition.
    Saves tokens by only adding one row per T&C document.
    """
    jamai = get_jamai_client()
    try:
        response = jamai.table.add_table_rows(
            table_type=t.TableType.ACTION,
            request=t.RowAddRequest(
                table_id="Analyzer", 
                data=[{"tnc_text": tnc_text}],
                stream=False
            )
        )
        
        if response.rows:
            # Return the raw dictionary of column names to text values
            cols = response.rows[0].columns
            return {k: v.text for k, v in cols.items()}
                
    except Exception as e:
        st.error(f"JamAI Error: {str(e)}")
    return None

def generate_pdf(results_dict):
    """
    Generates a report by cleaning all non-standard characters 
    to prevent FPDFUnicodeEncodingException.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Helvetica", 'B', 24)
    pdf.set_text_color(75, 0, 130) # Deep Purple
    pdf.cell(200, 20, "BeforeYouAccept: Risk Report", ln=True, align='C')
    pdf.ln(10)
    
    # Define what sections to include in the PDF
    sections = {
        "Risk Score": "risk_scoring",
        "Summary": "analysis_summary",
        "Critical Alerts": "critical_alerts",
        "Long Term Implications": "long_term_implications"
    }
    
    for title, key in sections.items():
        # Section Header
        pdf.set_font("Helvetica", 'B', 16)
        pdf.set_text_color(106, 13, 173) # Purple
        pdf.cell(200, 10, title, ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Section Body
        pdf.set_font("Helvetica", size=11)
        pdf.set_text_color(0, 0, 0)
        
        # 1. Get content and convert to string
        content = str(results_dict.get(key, "Information not available for this section."))
        
        # 2. THE FIX: Replace characters that FPDF hates
        replacements = {
            "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
            "©": "(c)", "®": "(r)", "™": "TM", "⚠️": "!!", "🔴": "X", 
            "🟡": "!", "🟢": "OK", "🚀": ">", "•": "*"
        }
        for char, replacement in replacements.items():
            content = content.replace(char, replacement)
        
        # 3. FINAL FAILSAFE: Strip any remaining non-Latin-1 characters
        # This prevents the app from crashing even if there's a weird hidden character
        clean_content = content.encode('latin-1', 'ignore').decode('latin-1')
        
        pdf.multi_cell(0, 8, clean_content)
        pdf.ln(10)
        
    return pdf.output()
