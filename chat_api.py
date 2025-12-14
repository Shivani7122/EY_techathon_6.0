from fastapi import FastAPI
from pydantic import BaseModel
from fpdf import FPDF
from typing import Optional

import uuid
import os

app = FastAPI(title="Tata Capital Agentic AI Chatbot")

# -----------------------------
# DUMMY CUSTOMER DATA (10 users)
# -----------------------------
CUSTOMERS = {
    "cust1": {"name": "Rahul", "salary": 50000, "credit_score": 760, "limit": 300000},
    "cust2": {"name": "Anita", "salary": 40000, "credit_score": 720, "limit": 200000},
    "cust3": {"name": "Aman", "salary": 35000, "credit_score": 680, "limit": 150000},
}

SESSIONS = {}

# -----------------------------
# REQUEST / RESPONSE
# -----------------------------
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    pdf_url: Optional[str] = None


# -----------------------------
# SANCTION LETTER AGENT
# -----------------------------
def generate_sanction_letter(name, amount):
    os.makedirs("sanction_letters", exist_ok=True)
    filename = f"sanction_{uuid.uuid4().hex}.pdf"
    path = f"sanction_letters/{filename}"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Tata Capital Sanction Letter", ln=True)
    pdf.cell(200, 10, txt=f"Customer: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Approved Amount: ₹{amount}", ln=True)
    pdf.cell(200, 10, txt="Status: Approved", ln=True)
    pdf.output(path)

    return path

# -----------------------------
# MASTER AGENT (CHAT CONTROLLER)
# -----------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    session = SESSIONS.get(request.session_id)

    # -----------------------------
    # START CONVERSATION
    # -----------------------------
    if session is None:
        SESSIONS[request.session_id] = {
            "state": "ASK_AMOUNT",
            "customer": CUSTOMERS["cust1"]  # pick dummy user
        }
        return ChatResponse(
            reply="Hi 👋 I’m Tata Capital’s digital loan assistant. How much personal loan are you looking for?"
        )

    state = session["state"]
    customer = session["customer"]

    # -----------------------------
    # SALES AGENT
    # -----------------------------
    if state == "ASK_AMOUNT":
        session["amount"] = int(request.message.replace(",", ""))
        session["state"] = "ASK_TENURE"
        return ChatResponse(
            reply="Great choice 😊 For how many months would you like the loan?"
        )

    if state == "ASK_TENURE":
        session["tenure"] = int(request.message)
        session["state"] = "VERIFICATION"
        return ChatResponse(
            reply="Thanks! Please confirm your mobile number for KYC verification."
        )

    # -----------------------------
    # VERIFICATION AGENT
    # -----------------------------
    if state == "VERIFICATION":
        session["state"] = "UNDERWRITING"
        return ChatResponse(
            reply="KYC verified successfully ✅ Checking your eligibility now…"
        )

    # -----------------------------
    # UNDERWRITING AGENT (CORE LOGIC)
    # -----------------------------
    if state == "UNDERWRITING":
        amount = session["amount"]
        limit = customer["limit"]
        credit = customer["credit_score"]
        salary = customer["salary"]

        if credit < 700:
            session["state"] = "END"
            return ChatResponse(
                reply="Sorry 😔 your loan cannot be approved due to low credit score."
            )

        if amount <= limit:
            session["state"] = "SANCTION"
        elif amount <= 2 * limit:
            session["state"] = "ASK_SALARY"
            return ChatResponse(
                reply="Please upload your salary slip for further processing."
            )
        else:
            session["state"] = "END"
            return ChatResponse(
                reply="Sorry 😔 the requested amount exceeds your eligibility."
            )

    if state == "ASK_SALARY":
        emi = session["amount"] / session["tenure"]
        if emi <= 0.5 * customer["salary"]:
            session["state"] = "SANCTION"
        else:
            session["state"] = "END"
            return ChatResponse(
                reply="Loan rejected ❌ EMI exceeds 50% of your salary."
            )

    # -----------------------------
    # SANCTION LETTER AGENT
    # -----------------------------
    if session["state"] == "SANCTION":
        pdf = generate_sanction_letter(customer["name"], session["amount"])
        session["state"] = "END"
        return ChatResponse(
            reply="Congratulations 🎉 Your loan has been approved. Your sanction letter is ready.",
            pdf_url=pdf
        )

    return ChatResponse(reply="Thank you for chatting with Tata Capital 😊")
