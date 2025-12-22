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
    Generates a PDF with Unicode-safe text processing.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Title
    pdf.set_font("Helvetica", 'B', 24)
    pdf.set_text_color(75, 0, 130)
    pdf.cell(200, 20, "BeforeYouAccept: Risk Report", ln=True, align='C')
    pdf.ln(10)
    
    sections = {
        "Risk Score": "risk_scoring",
        "Summary": "analysis_summary",
        "Critical Alerts": "critical_alerts",
        "Long Term Implications": "long_term_implications"
    }
    
    for title, key in sections.items():
        pdf.set_font("Helvetica", 'B', 16)
        pdf.set_text_color(106, 13, 173)
        pdf.cell(200, 10, title, ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font("Helvetica", size=12)
        pdf.set_text_color(0, 0, 0)
        
        # FIX: Sanitize content for PDF (Removes emojis and smart quotes)
        content = results_dict.get(key, "No data.")
        clean_content = content.replace("’", "'").replace("“", '"').replace("”", '"')
        clean_content = clean_content.replace("⚠️", "!!").replace("🔴", "!!").replace("🟡", "!!").replace("🟢", "OK")
        
        pdf.multi_cell(0, 10, clean_content)
        pdf.ln(10)
        
    return pdf.output()
