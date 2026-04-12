import os
import json
from fpdf import FPDF
import time

class DecisionAuditReport(FPDF):
    def header(self):
        self.set_fill_color(15, 15, 20)
        self.rect(0, 0, 210, 40, 'F')
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 25, ' NEXUS AI : RETURN AUDIT REPORT ', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | NEXUS Neural Matrix Log | {time.strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

def generate_audit_pdf(observation, action, reward, filename="audit_report.pdf"):
    """Generates a professional PDF audit for a specific decision."""
    pdf = DecisionAuditReport()
    pdf.add_page()
    
    # Section: Request Data
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(60, 60, 255)
    pdf.cell(0, 10, "1. TRANSACTION TELEMETRY", 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    
    data = [
        ["Product Price", f"${observation['product_price']:.2f}"],
        ["Customer Profile", observation['customer_type'].capitalize()],
        ["Fraud Risk Score", f"{float(observation['fraud_risk'])*100:.1f}%"],
        ["Return Reason", observation.get('return_reason_label', 'Unknown')],
        ["Days Since Purchase", f"{observation['days_since_purchase']} days"]
    ]
    
    for row in data:
        pdf.cell(50, 8, row[0], 1)
        pdf.cell(100, 8, row[1], 1)
        pdf.ln()
    
    pdf.ln(10)
    
    # Section: AI Reasoning
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(168, 85, 247)
    pdf.cell(0, 10, "2. AI NEURAL REASONING", 0, 1)
    pdf.set_font('Arial', 'I', 11)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 10, f"Final Action: {action['action_label']}\nReasoning: {action['reasoning']}\nConfidence: {float(action.get('confidence', 0.9))*100:.1f}%", border=1)
    
    pdf.ln(10)
    
    # Section: Financial Impact
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(16, 185, 129)
    pdf.cell(0, 10, "3. FINANCIAL AUDIT", 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(50, 8, "Net Reward Value", 1)
    pdf.cell(100, 8, f"{reward['value']:+.2f} USD", 1)
    pdf.ln()
    
    if reward.get('fraud_intercepted'):
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 10, "!!! FRAUD BLOCK DETECTED & INTERCEPTED !!!", 0, 1)

    # Save
    path = os.path.join(os.getcwd(), filename)
    pdf.output(path)
    return path

if __name__ == "__main__":
    # Test generation
    sample_obs = {"product_price": 299.99, "customer_type": "fraudster", "fraud_risk": 0.85, "return_reason_label": "Changed Mind", "days_since_purchase": 5}
    sample_act = {"action_label": "Rejected", "reasoning": "High fraud probability combined with subjective return reason.", "confidence": 0.92}
    sample_rew = {"value": -5.0, "fraud_intercepted": True}
    print(f"Generated test audit: {generate_audit_pdf(sample_obs, sample_act, sample_rew)}")
