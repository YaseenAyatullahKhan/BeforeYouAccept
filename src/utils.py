import streamlit as st
from jamaibase import JamAI, types as t
from fpdf import FPDF
import time
import base64

def get_base64_image(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def get_base64_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Initialize JamAI Client
def get_jamai_client():
    # Streamlit Cloud will fetch this from "Secrets" (Advanced Settings)
    api_key = st.secrets["JAMAI_API_KEY"]
    project_id = st.secrets.get("JAMAI_PROJECT_ID", "proj_aab63d006950e027eebfe137")
    return JamAI(token=api_key, project_id=project_id)

def fetch_analysis_column(tnc_text, column_name):
    """
    Calls JamAI for a specific column only. 
    This is the core 'Token Saver' logic.
    """
    jamai = get_jamai_client()
    try:
        # Add a row to the 'Analyzer' Action Table
        response = jamai.table.add_table_rows(
            table_type=t.TableType.ACTION,
            request=t.RowAddRequest(
                table_id="Analyzer",
                data=[{"tnc_text": tnc_text}],
                stream=False
            )
        )
        
        # Extract the specific column requested
        if response.rows:
            # Note: JamAI returns all columns in the row. 
            # Filter for the one the user clicked.
            row_data = response.rows[0].columns
            result = next((col.value for col in row_data if col.name == column_name), "No data found.")
            
            # Special formatting for Critical Alerts
            if column_name == "critical_alerts":
                result = result.replace("- ", "⚠️ ").replace("* ", "⚠️ ")
                
            return result
    except Exception as e:
        return f"Error connecting to JamAI: {str(e)}"
    return "Error: Could not retrieve analysis."

def generate_pdf(results_dict):
    """
    Generates a professional Deep Purple themed PDF report.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(75, 0, 130) # Deep Purple (Indigo)
    pdf.cell(200, 20, "BeforeYouAccept: Risk Report", ln=True, align='C')
    pdf.ln(10)
    
    # Date
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(200, 10, f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='R')
    pdf.ln(10)
    
    # Content Sections
    sections = {
        "Summary": "analysis_summary",
        "Critical Alerts": "critical_alerts",
        "Long Term Implications": "long_term_implications"
    }
    
    for title, key in sections.items():
        # Header
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(106, 13, 173) # Purple
        pdf.cell(200, 10, title, ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Purple underline
        pdf.ln(5)
        
        # Body
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        content = results_dict.get(key, "No analysis performed for this section.")
        
        # Clean up emojis for PDF compatibility (PDF fonts often don't support ⚠️)
        clean_content = content.replace("⚠️", "!!") 
        
        pdf.multi_cell(0, 10, clean_content)
        pdf.ln(10)
        
    return pdf.output(dest='S').encode('latin-1')
