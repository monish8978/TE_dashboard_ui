from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from fastapi import FastAPI, Request, Query
from pymongo import MongoClient
from datetime import datetime, timedelta
from fastapi.responses import FileResponse
import ast
import requests
import json
import pdfkit
import base64
import os
import time
import asyncio
import re


app = FastAPI()

# =====================================================
# CONFIG
# =====================================================
SESSION_TIMEOUT = timedelta(minutes=15)
MAX_ATTEMPTS = 3

# =====================================================
# OTP API CONFIG
# =====================================================
OTP_GENERATE_URL = "https://api.wonderhfl.com/OmniFinServices/restServices/userService/otp/generate"
OTP_VALIDATE_URL = "https://api.wonderhfl.com/OmniFinServices/restServices/userService/otp/validate"

COMMON_CREDENTIALS = {
    "userId": "APPUSER",
    "userPassword": "a18b22ba81f1a4cb6b1884ccff5e04d4",
    "source": "MOBILE",
    "sourceId": "e3712a79edeabcad",
    "initiatedBy": "admin",
    "deviceName": "RMX3581",
    "deviceVersion": "30",
    "sourceVersion": "6.0.0.5",
    "latitude": "28.6077002",
    "longitude": "77.3617263",
    "address": ""
}


CRITICAL_ISSUES_WHATSAPP_BUTTONS = [
    "FCL / SOA / LOD Request",
    "EMI / Pre-EMI Related",
    "Refund",
    "CLSS refund related",
    "Loan Application",
    "Cibil related",
    "Fake signature",
    "Misconduct by WHFL",
    "Miscommunication"
]

WHATSAPP_DOC_BUTTONS = [
    "Bounce Memo",
    "Copy of Insurance Policy",
    "Copy of Documents",
    "List of Documents",
    "Statement of Account",
    "Repayment Schedule",
    "Tax Certificate",
    "Welcome Letter",
    "Property Dispatch & NOC",
    "Property Paper Retrieval"
]

WHATSAPP_BUTTONS_PAYMENT_EMI = [
    "EMI Related",
    "Insurance Refund",
    "Part Payment",
    "Prepayment Related",
    "Levy of Prepay Charges",
    "Cheque Related"
]

WHATSAPP_BUTTONS_LOAN_SERVICE = [
    "Loan A/c Related",
    "Loan Application Related",
    "Loan Document Related",
    "Loan Cancellation",
    "Processing Fees Related",
    "Top-up",
    "Rate of Interest Related",
    "Disbursement Related",
    "Subsidy Related"
]

WHATSAPP_BUTTONS_LEGAL_RECOVERY_OPTIONS = [
    "Legal / Recovery Related",
    "Foreclosure",
    "Foreclosure Request"
]


CRITICAL_ISSUE_MAPPING = {
    "FCL / SOA / LOD Request": "FCL/SOA/LOD Request (out of TAT)",
    "EMI/ Pre-EMI Related": "EMI/ Pre-EMI Related (payment updation)",
    "Refund": "Refund (advance payment or excess payment)",
    "CLSS refund related": "CLSS refund related",
    "Loan Application": "Loan Application related",
    "Cibil related": "Cibil related",
    "Fake signature": "Fake signature",
    "Misconduct by WHFL": "Misconduct by WHFL employee",
    "Miscommunication": "Miscommunication about ROI and Tenor"
}


NON_CRITICAL_ISSUE_MAPPING = {
    "Bounce MEMO": "Bounce Memo Related",
    "Copy of Insurance policy": "Insurance Policy Copy Request",
    "Copy of documents": "Documents Copy Request",
    "Foreclosure request": "Foreclosure Request (Loan Closure Request)",
    "Tax certificate": "Tax Certificate Request",
    "List of Documents": "List of Documents Request",
    "Original property dispatch and NOC": "Original Property Dispatch & NOC Related",
    "Repayment schedule": "Repayment Schedule Request",
    "Statement of Account": "Statement of Account (SOA) Request",
    "Temporary retrieval of property paper": "Temporary Retrieval of Property Papers",
    "Welcome letter": "Welcome Letter Request",
    "Loan A/c related": "Loan Account Related Query",
    "Disbursal Related": "Disbursement Related Query",
    "Subsidy Related": "Subsidy Related Query",
    "EMI Related": "EMI Related Query",
    "Address Change": "Address Change Request",
    "Foreclosure": "Foreclosure Related Query",
    "Insurance Refund": "Insurance Refund Related",
    "Part Payment": "Part Payment Related",
    "Top up": "Top-Up Loan Related",
    "Rate of Interest Related": "Rate of Interest (ROI) Related",
    "Prepayment Related": "Prepayment Related Query",
    "Legal/Recovery related": "Legal / Recovery Related",
    "Disbursement related": "Disbursement Related",
    "Loan Document related": "Loan Document Related",
    "Presentation of cheque related": "Cheque Presentation Related",
    "Insurance Related": "Insurance Related Query",
    "Levy of prepay charges": "Levy of Prepayment Charges",
    "Loan Cancellation": "Loan Cancellation Request",
    "Loan Application related": "Loan Application Related",
    "Processing fees related": "Processing Fees Related"
}



# =====================================================
# TWILIO CONFIG
# =====================================================
TWILIO_ACCOUNT_SID = "AC34df793595c05125c2acadb0f34c11a7"
TWILIO_AUTH_TOKEN = "1400334a5628419a650de4119c9dfde1"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"

# Templates
TEMPLATE_GREETING = "greeting_message"
TEMPLATE_FIRST_MAIN_MENU = "template_first_main_menu"
TEMPLATE_NEW_PROSPECT_MENU = "template_new_prospect_menu"
TEMPLATE_NEW_PROSPECT_LOAN_TYPE = "template_new_prospect_loan_type"
TEMPLATE_EMP_TYPE = "template_emp_type"
EXISTING_LOAN_NUMBER = "existing_loan_number"
TEMPLATE_EXISTING_MENU = "HXea30645cd1df86fbac076e7c9ad35248"
TEMPLATE_BRANCH_LOCATOR_LINK = "template_branch_locator_link"
TEMPLATE_ASSISTANCE_CONFIRMATION = "template_assistance_confirmation"
typeofsupporttxt = "HX1fe135ceee6af33168656af217069a20"
criticalsupportissuesmenu = "criticalsupportissuesmenu"
documentsstatements = "documentsstatements"
paymentsemimenu = "paymentsemimenu"
loanaccountservicesmenu = "loanaccountservicesmenu"
legalrecoverymenu = "legalrecoverymenu"
changeandresendmenu = "changeandresendmenu"
chatwithsupportagent = "returntomenu"
docmenutemplatelistmenu = "docmenutemplatelistmenu "
returntomenu = "returntomenu"

# =====================================================
# DATABASE
# =====================================================
client = MongoClient("mongodb+srv://mongodb:mongodb@cluster0.1nfoz.mongodb.net/?retryWrites=true&w=majority")
db = client["whatsapp_bot"]
users = db["chat_state"]



# ==============================
# 🔐 META CONFIG
# ==============================
META_ACCESS_TOKEN = "37a67b134b41144da7cf67f1b3b30cb9"
PHONE_NUMBER_ID = "102447942486079"
VERIFY_TOKEN = "EAAqPVXyiYlYBQjJrnMkyOnBOYIVYK6gCYkim4rNZBsu6txriZCPuORYZC8IMPbzsmXZCF3kMbVZB231gz2fqeyMPumnTAPMDE1TTk8ZANeZCug96PdXUoZB1zwkB3H2GKyc5l2QMT21cPwSYytjrD0ejF3vent62u15fLXpzjFanoN0ZBM5ZAmyMIrVFZBP7lxlPBsNvgZDZD"
META_API_VERSION = "v22.0"


PDF_STORAGE_PATH = "/Czentrix/apps/wonder_homes_loan_bot/documents"
os.makedirs(PDF_STORAGE_PATH, exist_ok=True)


def normalize(text):
    return text.lower().strip().replace("  ", " ")

def check_critical_issue(msg):
    msg_norm = normalize(msg)
    # print(msg_norm,"llllllllllllllllllllllpppppppppppppppppppp")
    for wa_text, internal_issue in CRITICAL_ISSUE_MAPPING.items():
        # print(wa_text,"=============================",internal_issue)
        if normalize(wa_text) == msg_norm:
            return internal_issue   # matched

    return None


def check_non_critical_issue(msg):
    msg_norm = normalize(msg)

    for wa_text, internal_issue in NON_CRITICAL_ISSUE_MAPPING.items():
        if normalize(wa_text) == msg_norm:
            return internal_issue   # matched

    return None

async def send_second_message_after_delay(wa):
    await asyncio.sleep(10)
    send_text_template(wa, TEMPLATE_ASSISTANCE_CONFIRMATION)


def download_interest_certificate(loan_number, from_date, to_date):
    url = "https://uat-api.wonderhfl.com/OmniFinServices/restServices/customerServiceController/fetchInterestCertificate"

    headers = {
        "Content-Type": "application/json",
        "Cookie": "JSESSIONID=GtwdUoEThWz70a32S7_Uk_T6sEVstpqm5p8KHaJl.win-dop26btmo11; JSESSIONID=y_PLqxAGkBLdf5-EA3yRjb9gENJU8_d-boL8pRsn.win-dop26btmo11"
    }

    payload = {
        "userCredentials": {
            "userId": "appuser",
            "userPassword": "a18b22ba81f1a4cb6b1884ccff5e04d4"
        },
        "loanNumber": loan_number,
        "fromDate": from_date,
        "toDate": to_date
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code != 200:
        return {"error": "API Failed", "details": response.text}

    data = response.json()

    if data.get("operationStatus") != "1":
        return {"error": data.get("operationMessage")}

    base64_pdf = data["interestCertificateStream"]

    # Decode Base64 → PDF
    pdf_bytes = base64.b64decode(base64_pdf)

    # Folder
    os.makedirs(PDF_STORAGE_PATH, exist_ok=True)

    filename = f"Interest_Certificate_{loan_number}.pdf"
    filepath = os.path.join(PDF_STORAGE_PATH, filename)

    with open(filepath, "wb") as f:
        f.write(pdf_bytes)

    return {
        "status": "success",
        "message": "Interest Certificate Generated",
        "file": filepath
    }



def download_welcome_letter(loan_number):
    url = "https://uat-api.wonderhfl.com/OmniFinServices/restServices/customerServiceController/fetchWelcomeLetterReport"

    headers = {
        "Content-Type": "application/json",
        "Cookie": "JSESSIONID=GtwdUoEThWz70a32S7_Uk_T6sEVstpqm5p8KHaJl.win-dop26btmo11"
    }

    payload = {
        "userCredentials": {
            "userId": "appuser",
            "userPassword": "a18b22ba81f1a4cb6b1884ccff5e04d4"
        },
        "loanNumber": loan_number
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code != 200:
        return {"error": "API Failed", "details": response.text}

    data = response.json()

    if data.get("operationStatus") != "1":
        return {"error": data.get("operationMessage")}

    base64_pdf = data["welcomeLetterReportStream"]

    # Decode Base64 → PDF
    pdf_bytes = base64.b64decode(base64_pdf)

    # Folder
    os.makedirs(PDF_STORAGE_PATH, exist_ok=True)

    filename = f"welcome_letter_{loan_number}.pdf"
    filepath = os.path.join(PDF_STORAGE_PATH, filename)

    with open(filepath, "wb") as f:
        f.write(pdf_bytes)

    return {
        "status": "success",
        "message": "Welcome Letter Generated",
        "file": filepath
    }



def send_whatsapp_cta_template(
        mobile_no: str,
        template_name: str,
        message_body: list,
        license_id: str,
        language_code: str = "en",
        api_type: str = "aisensy"
):
    """
    Send WhatsApp CTA Template Message
    """

    url = "https://usomniservice.c-zentrix.com/whatsappApi_v2/OUT/outgoing.php"

    payload = {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhc3Npc3RhbnRJZCI6IjY1MTExNjY5YTAxYzhjMGJkNWZlNmE3MiIsImNsaWVudElkIjoiNjUxMTE2NjlhMDFjOGMwYmQ1ZmU2YTY4Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vdXNvbW5pc2VydmljZS5jLXplbnRyaXguY29tL3doYXRzYXBwQXBpX3YyL0lOL2FpU2Vuc3lJbmNvbWluZy5waHA_bGljZW5zZUlkPTI4MWVjYWE1OWU1OTQ1MTkxMWM1ZGVmMDViYzk4ZjM5JmRlcHQ9MjIzJnR5cGU9Y2hhdCZ2ZW5kb3I9YWlzZW5zeSZ0YWc9U2FsZXMiLCJpYXQiOjE3NDYwMTg3MTN9.2btlReQSS77WfBeJ5OJoo9D0CLS3PWtcVHQQXMzcgNk",
        "mobile_no": mobile_no,
        "api_type": api_type,
        "type": "template",
        "template_name": template_name,
        "languageCode": language_code,
        "messageBody": message_body,
        "licenseId": license_id
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )

        return {
            "status_code": response.status_code,
            "response": response.json()
        }

    except Exception as e:
        return {
            "status": False,
            "error": str(e)
        }



def fetch_repayment_schedule(loan_number):
    url = "https://uat-api.wonderhfl.com/OmniFinServices/restServices/customerServiceController/repaymentSchedule"

    headers = {
        "Content-Type": "application/json",
        "Cookie": "JSESSIONID=GtwdUoEThWz70a32S7_Uk_T6sEVstpqm5p8KHaJl.win-dop26btmo11; JSESSIONID=bILhxzVwJTNPo2v5kMgnJ4PAkaq5YMdoP132L4mW.win-dop26btmo11"
    }

    payload = {
        "userCredentials": {
            "userId": "appuser",
            "userPassword": "a18b22ba81f1a4cb6b1884ccff5e04d4"
        },
        "loanNumber": loan_number
    }

    r = requests.post(url, headers=headers, json=payload, timeout=20)

    if r.status_code != 200:
        return None

    return r.json()

def extract_main_fields(api_data):
    rows = api_data.get("crRepayschDtlList", [])

    clean_rows = []
    for r in rows:
        clean_rows.append({
            "date": r["instlDate"],
            "emi": float(r["instlAmount"]),
            "principal": float(r["prinComp"]),
            "interest": float(r["intComp"]),
            "balance": float(r["prinOs"])
        })

    return clean_rows

def extract_loan_details(api_data):

    # 🔹 Step 1: Convert string to dict
    if isinstance(api_data, str):
        api_data = ast.literal_eval(api_data)

    rows = api_data.get("customerLoanDetails", [])

    clean_rows = []
    for r in rows:
        clean_rows.append({
            "customerName": r["customerName"],
            "loanAmount": float(r["loanAmount"]),
            "emi": float(r["emiAndPreEmi"]),
            "loanNumber": r["loanNumber"],
            "nextPaymentDueDate": r["nextPaymentDueDate"],
            "branchName": r["branchName"],
            "branchPhoneNo": r["branchPhoneNo"]
        })

    return clean_rows


def create_emi_pdf(loan_no, emi_rows, file_path):
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(f"Loan Repayment Schedule<br/>Loan No: {loan_no}", styles["Title"])
    elements.append(title)

    data = [
        ["Date", "EMI (₹)", "Principal (₹)", "Interest (₹)", "Balance (₹)"]
    ]

    for r in emi_rows:
        data.append([
            r["date"],
            f"{r['emi']:,.0f}",
            f"{r['principal']:,.0f}",
            f"{r['interest']:,.0f}",
            f"{r['balance']:,.0f}"
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), "#DDDDDD"),
        ("GRID", (0,0), (-1,-1), 1, "#000000"),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ]))

    elements.append(table)

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    doc.build(elements)


def create_loan_details_pdf(loan_rows, file_path):
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph("Customer Loan Details Report", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 0.3 * inch))

    data = [[
        "Customer Name",
        "Loan Amount (₹)",
        "EMI (₹)",
        "Loan Number",
        "Next Due Date",
        "Branch Name",
        "Branch Phone"
    ]]

    for loan in loan_rows:
        data.append([
            loan.get("customerName", ""),
            f"{loan.get('loanAmount', 0):,.0f}",
            f"{loan.get('emi', 0):,.0f}",   # ✅ FIXED
            loan.get("loanNumber", ""),
            loan.get("nextPaymentDueDate", ""),
            loan.get("branchName", ""),
            loan.get("branchPhoneNo", "")
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    doc.build(elements)




def build_emi_message(api_data, loan_no):
    rows = api_data.get("crRepayschDtlList", [])

    if not rows:
        return "❌ EMI schedule not found for this loan number."

    msg = f"📄 *EMI Repayment Schedule*\n\nLoan No: {loan_no}\n\n"

    for i, r in enumerate(rows[:6], 1):
        date = datetime.strptime(r["instlDate"], "%Y-%m-%d").strftime("%d-%b-%Y")

        msg += (
            f"{i}️⃣ {date}\n"
            f"EMI: ₹{int(float(r['instlAmount'])):,}\n"
            f"Principal: ₹{int(float(r['prinComp'])):,}\n"
            f"Interest: ₹{int(float(r['intComp'])):,}\n"
            f"Balance: ₹{int(float(r['prinOs'])):,}\n\n"
        )

    msg += "📌 For complete schedule, type *PDF*"

    return msg.strip()

# ==============================
# 📤 Send Text
# ==============================
def send_text(to, message):
    url = f"https://graph.facebook.com/{META_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {VERIFY_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=payload)
    response = response.json()


    return response


def send_text_template(to, template):
    url = f"https://graph.facebook.com/{META_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {VERIFY_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": f"{to}",
        "type": "template",
        "template": {
        "name": f"{template}",
        "language": { "code": "en" }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    response = response.json()

    return response


def send_text_template_with_variables(to, template, user_name):
    url = f"https://graph.facebook.com/{META_API_VERSION}/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {VERIFY_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": str(to),
        "type": "template",
        "template": {
            "name": template,
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": user_name
                        }
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    return data


def send_text_template_flow(to, flow_id):
    url = f"https://graph.facebook.com/{META_API_VERSION}/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {VERIFY_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "body": {
            "text": "Please provide your details below to start your loan application process."
            },
            "action": {
            "name": "flow",
            "parameters": {
                "flow_message_version": "3",
                "flow_id": flow_id,
                "flow_cta": "Apply Now"
            }
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    return data

def send_whatsapp_flow_message(phone_number: str, flow_token: str):
    """
    Send WhatsApp template message with Flow button

    Args:
        phone_number (str): Recipient phone number with country code (e.g., 917533941271)
        flow_token (str): Flow token for the WhatsApp flow
    """

    url = "https://partnersV1.pinbot.ai/v3/742406742288776/messages"

    headers = {
        "apikey": "6e90b3a8-7f1e-11f0-98fc-02c8a5e042bd",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "apply_loan_application",
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "button",
                    "sub_type": "flow",
                    "index": "0",
                    "parameters": [
                        {
                            "type": "action",
                            "action": {
                                "flow_token": flow_token
                            }
                        }
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return {
            "status_code": response.status_code,
            "response": response.json()
        }
    except Exception as e:
        return {
            "error": str(e)
        }

def send_text_template_with_header_variables(to, template, header_name, body_name):
    url = f"https://graph.facebook.com/{META_API_VERSION}/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {VERIFY_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": str(to),
        "type": "template",
        "template": {
            "name": template,
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "text",
                            "text": header_name
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": body_name
                        }
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()



def send_cibil_pdf_whatsapp(to, pdf_url,filename):
    url = "https://omniqa.c-zentrix.com/whatsappApi_v2/OUT/outgoing.php"
    payload = {
        "token": "6e90b3a8-7f1e-11f0-98fc-02c8a5e042bd",
        "auth_token": "6e90b3a8-7f1e-11f0-98fc-02c8a5e042bd",
        "accountId": "6e90b3a8-7f1e-11f0-98fc-02c8a5e042bd",
        "mobile_no": "917753803306",
        "type": "image",
        "tag": "BotTvt",
        "licenseId": "a21c1b4e8c44ced0d7aa67ffb203db34",
        "api_type": "pinnacle",
        "media_url": pdf_url,
        "messageBody": filename,
        "mime_type": "application/pdf"
    }
    # url = "https://usomniservice.c-zentrix.com/whatsappApi_v2/OUT/outgoing.php"

    # payload = {
    #     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhc3Npc3RhbnRJZCI6IjY1MTExNjY5YTAxYzhjMGJkNWZlNmE3MiIsImNsaWVudElkIjoiNjUxMTE2NjlhMDFjOGMwYmQ1ZmU2YTY4Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vdXNvbW5pc2VydmljZS5jLXplbnRyaXguY29tL3doYXRzYXBwQXBpX3YyL0lOL2FpU2Vuc3lJbmNvbWluZy5waHA_bGljZW5zZUlkPTI4MWVjYWE1OWU1OTQ1MTkxMWM1ZGVmMDViYzk4ZjM5JmRlcHQ9MjIzJnR5cGU9Y2hhdCZ2ZW5kb3I9YWlzZW5zeSZ0YWc9U2FsZXMiLCJpYXQiOjE3NDYwMTg3MTN9.2btlReQSS77WfBeJ5OJoo9D0CLS3PWtcVHQQXMzcgNk",
    #     "mobile_no": to,
    #     "type": "document",
    #     "tag": "OTVT",
    #     "licenseId": "8e2a733c2796c6367e838fff6191b74d",
    #     "api_type": "aisensy",
    #     "media_url": pdf_url,
    #     "messageBody": filename,
    #     "mime_type": "application/pdf"
    # }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return response.json()
    except Exception as e:
        print("Error:", str(e))
        return None

# =====================================================
# TWILIO HELPER
# =====================================================
def send_twilio_template(to, TEMPLATE, variables=None):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    payload = {
        "To": f"whatsapp:{to}",
        "From": TWILIO_WHATSAPP_FROM,
        "Body": "Hi",
        "ContentSid": TEMPLATE,
    }
    if variables:
        payload["ContentVariables"] = json.dumps(variables)
    res = requests.post(url, data=payload, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=10)
    return res.json()

# =====================================================
# HELPERS
# =====================================================
def get_user(wa):
    return users.find_one({"wa": wa})

def reset_flow(wa, clear_mobile=False):
    """
    Resets the flow.
    If clear_mobile is True, it wipes everything.
    Otherwise, it preserves the 'mobile' number if it exists.
    """
    user = get_user(wa)
    existing_mobile = user.get("mobile") if user else None

    # Delete old state
    users.delete_one({"wa": wa})

    # New state
    new_state = {
        "wa": wa,
        "step": "LANG",
        "attempt": 0,
        "createdAt": datetime.utcnow(),
        "lastInteractionAt": datetime.utcnow()
    }

    # Preserve mobile if we don't want to clear it
    if not clear_mobile and existing_mobile:
        new_state["mobile"] = existing_mobile

    users.insert_one(new_state)

def save_user(wa, data):
    users.update_one(
        {"wa": wa},
        {"$set": {**data, "lastInteractionAt": datetime.utcnow()}},
        upsert=True
    )

def attempt_failed(user, wa):
    attempt = user.get("attempt", 0) + 1
    if attempt >= MAX_ATTEMPTS:
        reset_flow(wa) # Keep mobile, just reset steps
        return True
    save_user(wa, {"attempt": attempt})
    return False

def is_session_expired(user):
    last = user.get("lastInteractionAt")
    return not last or datetime.utcnow() - last > SESSION_TIMEOUT

# =====================================================
# OTP FUNCTIONS
# =====================================================
def generate_otp(mobile):
    payload = {
        "mobileNumber": mobile,
        "workingUserId": "admin",
        "userCredentials": COMMON_CREDENTIALS,
        "businessDate": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    res = requests.post(OTP_GENERATE_URL, json=payload, timeout=10).json()
    return res

def validate_otp(sms_record_id, otp):
    payload = {
        "smsRecordId": sms_record_id,
        "smsOTP": otp,
        "userCredentials": COMMON_CREDENTIALS
    }
    return requests.post(OTP_VALIDATE_URL, json=payload, timeout=10).json()


def get_loan_oauth_token():
    url = "https://uat-api.wonderhfl.com/gateway-service/authServices/oauth/token"

    headers = {
        "Accept": "application/json",
        "Authorization": "Basic bW9iaWxlOm1vYmlsZQ==",
        "clinetName": "mobile",
        "Cookie": "Path=/gateway-service"
    }

    data = {
        "username": "ADMIN",
        "password": "0cc175b9c0f1b6a831c399e269772661",
        "grant_type": "password",
        "client_id": "mobile"
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()

    token_data = response.json()
    return token_data["access_token"]


def get_loan_details(phone_no):
    access_token = get_loan_oauth_token()

    url = "https://uat-api.wonderhfl.com/gateway-service/omnifin-los-lms-api/dsaDealerWSServices/getLoanDetails"

    headers = {
        "Authorization": f"bearer {access_token}",
        "Content-Type": "application/json",
        "Cookie": "Path=/gateway-service; Path=/gateway-service"
    }

    payload = {
        "phoneNo": phone_no
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    loan_data = response.json()

    # MongoDB upsert
    collection = db[phone_no]
    collection.replace_one(
        {"phoneNo": phone_no},   # filter
        loan_data,               # new document
        upsert=True
    )

    return loan_data


# =====================================================
# BUSINESS LOGIC (DUMMY)
# =====================================================
def validate_loan_with_crm(mobile, loan_last_5):
    loan_collection = db[mobile]
    pipeline = [
        {"$unwind": "$customerLoanDetails"},

        {
            "$addFields": {
                "lastFiveDigits": {
                    "$substr": [
                        "$customerLoanDetails.loanNumber",
                        {"$subtract": [
                            {"$strLenCP": "$customerLoanDetails.loanNumber"}, 5
                        ]},
                        5
                    ]
                }
            }
        },

        {
            "$match": {
                "lastFiveDigits": loan_last_5
                # "mobile": mobile
            }
        },

        {
            "$group": {
                "_id": "$lastFiveDigits",
                "loanData": {"$first": "$customerLoanDetails"}
            }
        }
    ]

    result = list(loan_collection.aggregate(pipeline))

    if result:
        loan = result[0]["loanData"]
        return {
            "status": "MATCH",
            "customer_name": loan["customerName"],
            "branch": loan["branchName"],
            "loan_number": loan["loanNumber"]
        }

    return {"status": "NOT_MATCH"}


def get_all_loan(mobile):
    loan_collection = db[mobile]
    data = loan_collection.find_one(
        {},
        {"_id": 0}
    )
    return data

def format_loans_for_whatsapp(data):
    loans = data.get("customerLoanDetails", [])

    if not loans:
        return "❌ No loan details found."

    seen = set()
    message = "📄 *Your Loan Details*\n\n"

    for loan in loans:
        loan_key = (loan["customerName"], loan["loanNumber"])
        if loan_key in seen:
            continue
        seen.add(loan_key)

        message += (
            "━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Customer Name*: {loan['customerName']}\n"
            f"💳 *Loan No*: {loan['loanNumber']}\n"
            f"💰 *Loan Amount*: ₹{int(loan['loanAmount'])}\n"
            f"📆 *Next Due Date*: {loan['nextPaymentDueDate']}\n"
            f"💵 *EMI*: ₹{int(loan['emiAndPreEmi'])}\n"
            f"🏢 *Branch*: {loan['branchName']}\n"
            f"📞 *Branch Phone*: {loan['branchPhoneNo']}\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
        )

    customerName = loan['customerName']

    return message.strip(),customerName


def verify_pan(pan: str):
    url = "https://hub.perfios.com/api/kyc/v2/pan"

    headers = {
        "Content-Type": "application/json",
        "x-auth-key": "yehitufubQfhvUw"
    }

    payload = {
        "consent": "Y",
        "pan": pan,
        "clientData": {
            "caseId": "123456"
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises error for 4xx/5xx

        return response.json()  # API response as dict

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def generate_transunion_token():
    url = "https://www.test.transuniondecisioncentre.co.in/DC/TUcl/TU.DE.Pont/Token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {
        "grant_type": "password",
        "username": "HF6411GO01_UAT001",
        "password": "Wonder#20252026"
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()

        token_data = response.json()
        return token_data.get("access_token")   # ✅ Only access_token return

    except requests.exceptions.RequestException as e:
        print("Token Error:", str(e))
        return None


user_data = {"RequestInfo":{"SolutionSetName":"Go_WONDERHOME_AGSS","ExecuteLatestVersion":"true"},"Fields":{"Applicants":{"Applicant":{"ApplicantType":"Main","ApplicantFirstName":"YASH","ApplicantMiddleName":"","ApplicantLastName":"BANSAL","DateOfBirth":"24042000","Gender":"M","Identifiers":{"Identifier":[{"IdNumber":"DVWPB4941P","IdType":"01"},{"IdNumber":"315260054706","IdType":"06"}]},"Telephones":{"Telephone":[{"TelephoneExtension":"","TelephoneNumber":"8646456566","TelephoneType":"01"}]},"Addresses":{"Address":{"AddressType":"02","AddressLine1":"S\/O VIVEK BANSAL 23 HANUMAN ROAD CHAUBEY","AddressLine2":"KA BAGH NEAR CHHOTE HANUMAN FIROZABAD","AddressLine3":"FIROZABAD UTTAR PRADESH 283203","AddressLine4":"","AddressLine5":"","City":"Firozabad","PinCode":"283203","ResidenceType":"02","StateCode":"09"}},"Services":{"Service":{"Id":"CORE","Operations":{"Operation":[{"Name":"ConsumerCIR","Params":{"Param":[{"Name":"CibilBureauFlag","Value":"false"},{"Name":"Amount","Value":"1000000"},{"Name":"Purpose","Value":"40"},{"Name":"ScoreType","Value":"08"},{"Name":"MemberCode","Value":"HF64117777_MUATC2CNPE"},{"Name":"Password","Value":"niu@gtlsEra7tsfxjnz"},{"Name":"FormattedReport","Value":"true"},{"Name":"GSTStateCode","Value":"09"}]}},{"Name":"IDV","Params":{"Param":[{"Name":"IDVerificationFlag","Value":"false"},{"Name":"ConsumerConsentForUIDAIAuthentication","Value":"N"},{"Name":"GSTStateCode","Value":"09"}]}},{"Name":"FIWaiver","Params":{"Param":[{"Name":"FIWaiver","Value":"false"}]}}]}}}}},"ApplicationData":{"GSTStateCode":"09","Services":{"Service":{"Id":"CORE","Skip":"N","Consent":"true"}}}}}


def submit_cibil_application(access_token: str):
    url = "https://www.test.transuniondecisioncentre.co.in/DC/TUCL/TU.DE.Pont/Applications"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.post(url, headers=headers, json=user_data)
        response.raise_for_status()
        result = response.json()

        ApplicantLastName = user_data["Fields"]["Applicants"]["Applicant"]["ApplicantLastName"]
        PanNumber = user_data["Fields"]["Applicants"]["Applicant"]["Identifiers"]["Identifier"][0]["IdNumber"]

        # Document ID extract
        document_id = None
        try:
            services = result['Fields']['Applicants']['Applicant']['Services']['Service']

            # Service can be list or dict
            if isinstance(services, list):
                for service in services:
                    operations = service.get('Operations', {}).get('Operation', [])
                    for operation in operations:
                        document = operation.get('Data', {}).get('Response', {}).get('RawResponse', {}).get('Document')
                        if document and 'Id' in document:
                            document_id = document['Id']
                            break
                    if document_id:
                        break
            elif isinstance(services, dict):
                operations = services.get('Operations', {}).get('Operation', [])
                for operation in operations:
                    document = operation.get('Data', {}).get('Response', {}).get('RawResponse', {}).get('Document')
                    if document and 'Id' in document:
                        document_id = document['Id']
                        break

        except KeyError:
            document_id = None

        # Return original response + extracted document id
        return document_id,ApplicantLastName,PanNumber

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_value(soup, label):
    cell = soup.find("td", string=lambda x: x and label.lower() in x.lower())
    if not cell:
        return None
    return cell.find_next_sibling("td").get_text(strip=True)


def delete_pdf_file(filename):
    """
    Deletes a file from /Czentrix/apps/wonder_homes_loan_bot/documents
    """

    try:
        # Security: remove any path traversal
        safe_filename = os.path.basename(filename)

        file_path = os.path.join(PDF_STORAGE_PATH, safe_filename)

        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": "File not found",
                "file": safe_filename
            }

        os.remove(file_path)

        return {
            "status": "success",
            "message": "File deleted successfully",
            "file": safe_filename
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to delete file",
            "details": str(e)
        }

def fetch_transunion_report_pdf(document_id, access_token,output_pdf_file):
    TU_URL = f"https://www.test.transuniondecisioncentre.co.in/DC/TUcl/TU.DE.Pont/documents/{document_id}"

    HEADERS = {
        "Authorization": f"Bearer {access_token}"
    }

    # Create folder if not exists
    os.makedirs(PDF_STORAGE_PATH, exist_ok=True)

    output_pdf = os.path.join(PDF_STORAGE_PATH, f"{output_pdf_file}")

    r = requests.get(TU_URL, headers=HEADERS, timeout=60)
    r.raise_for_status()

    html_content = r.text

    # ---------- Fix UTF-16 / XML encoding ----------
    if html_content.startswith("<?xml"):
        html_content = html_content.encode("utf-8", "ignore").decode("utf-8")

    # ---------- Save temp HTML ----------
    temp_html = f"/tmp/tu_{document_id}.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    # ---------- wkhtmltopdf options ----------
    options = {
        'page-size': 'A4',
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'encoding': 'UTF-8',
        'enable-local-file-access': None,
        'disable-smart-shrinking': ''
    }

    # ---------- Convert to PDF ----------
    pdfkit.from_file(temp_html, output_pdf, options=options)

    os.remove(temp_html)

    return output_pdf

@app.get("/download/cibil")
def download_cibil_report(file: str = Query(...)):
    # security: no folder traversal
    safe_file = os.path.basename(file)

    file_path = os.path.join(PDF_STORAGE_PATH, safe_file)

    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": "Documents not found"
        }

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_file
    )

# =====================================================
# MAIN API
# =====================================================
@app.post("/chat/process")
async def chat_process(req: Request):
    body = await req.json()
    wa_no = body.get("wa_numer")
    msg = body.get("message", "").strip()
    extraParms = body.get("extraParms")
    csid_data = json.loads(extraParms)
    wa = csid_data.get("csid")
    cmd = msg.upper()

    # -------- GLOBAL COMMANDS --------
    if cmd == "RESTART":
        reset_flow(wa, clear_mobile=True) # Full reset including mobile
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "I am Citra, your Virtual Assistant.I am here to help you. Hope you are doing well.Please select one of the options below to start"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "English",
                    "title": "English",
                    "value": "English"
                    },
                    {
                    "id": "Hindi",
                    "title": "Hindi",
                    "value": "Hindi"
                    }
                ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    user = get_user(wa)

    if user and is_session_expired(user):
        reset_flow(wa) # Preserve mobile, reset steps
        user = get_user(wa)

    if not user:
        reset_flow(wa, clear_mobile=True)
        # send_text_template(wa, TEMPLATE_GREETING)
        # return {"reply": "Welcome 👋 Template sent", "flag": True}
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "I am Citra, your Virtual Assistant.I am here to help you. Hope you are doing well.Please select one of the options below to start"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "English",
                    "title": "English",
                    "value": "English"
                    },
                    {
                    "id": "Hindi",
                    "title": "Hindi",
                    "value": "Hindi"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    step = user["step"]
    try:
        tmp_step = user["tmp_step"]
    except:
        tmp_step = ""
    print(user,"uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu")
    print(msg,"mmmmmmmmmmmmmmmmmmmmm")
    print(step,"ssssssssssssssssssss")
    print(tmp_step,"tttttttttttttttttmmmmmmmmmmppppppppp")

    existing_mobile = user.get("mobile") if user else None


    if step == "LANG" and msg.lower() in ["hii", "hi", "hey", "hello","Root","root","start","Start"]:
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "I am Citra, your Virtual Assistant.I am here to help you. Hope you are doing well.Please select one of the options below to start"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "English",
                    "title": "English",
                    "value": "English"
                    },
                    {
                    "id": "Hindi",
                    "title": "Hindi",
                    "value": "Hindi"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload


    # Jab mobile number NA ho
    if not existing_mobile and msg.lower() in ["hii", "hi", "hey", "hello","Root","root","start","Start"] and msg:
        reset_flow(wa)  # No mobile to preserve

        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "I am Citra, your Virtual Assistant.I am here to help you. Hope you are doing well.Please select one of the options below to start"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "English",
                    "title": "English",
                    "value": "English"
                    },
                    {
                    "id": "Hindi",
                    "title": "Hindi",
                    "value": "Hindi"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    existing_smsRecordId = user.get("smsRecordId") if user else None
    if existing_mobile and msg.lower() in ["hii", "hi", "hey", "hello","Root","root","start","Start"] and msg:
        save_user(wa, {"step": "MAIN_MENU", "attempt": 0})
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        # # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        # return {"reply": "existing user", "flag": True}
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "How may i help you today?"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "Apply For New Loan",
                    "title": "Apply For New Loan",
                    "value": "Apply For New Loan"
                    },
                    {
                    "id": "Existing Customer",
                    "title": "Existing Customer",
                    "value": "Existing Customer"
                    },
                    {
                    "id": "Branch Locator",
                    "title": "Branch Locator",
                    "value": "Branch Locator"
                    },
                    {
                    "id": "Customer Support",
                    "title": "Customer Support",
                    "value": "Customer Support"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload


    if msg in CRITICAL_ISSUES_WHATSAPP_BUTTONS and step != "DOC_MENU":
        critical_issue = check_critical_issue(msg)
        if critical_issue:
            save_user(wa, {"step": "SUPPPORT_ISSUE"})
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Thank you for reaching out.\n\nWe have received your request and it has been marked as a critical issue.\n\nOur Support Team will connect with you shortly to assist you further."
                    },
                    {
                        "type": "Button",
                        "id": "serviceType",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Contact Us",
                                "title": "Contact Us",
                                "value": "Contact Us"
                            },
                            {
                                "id": "Back To Menu",
                                "title": "Back To Menu",
                                "value": "Back To Menu"
                            },
                            {
                                "id": "Main Menu",
                                "title": "Main Menu",
                                "value": "Main Menu"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "id": "crmSubmitForm",
                        "value": "Submit",
                        "actionId": "7777.70007"
                    }
                ]
            }
            return payload

    if step != "DOC_MENU":
        if (
            msg in WHATSAPP_DOC_BUTTONS or
            msg in WHATSAPP_BUTTONS_PAYMENT_EMI or
            msg in WHATSAPP_BUTTONS_LOAN_SERVICE or
            msg in WHATSAPP_BUTTONS_LEGAL_RECOVERY_OPTIONS
        ):
            non_critical_issue = check_non_critical_issue(msg)
            if non_critical_issue:
                save_user(wa, {"step": "SUPPPORT_ISSUE"})
                payload = {
                    "type": "adaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "Thank you for reaching out. For assistance with this request, please contact our customer support team at 1800 102 1002 or email us at hello@wonderhfl.com. Our team will be happy to help you."
                        },
                        {
                            "type": "Button",
                            "id": "serviceType",
                            "style": "expanded",
                            "choices": [
                                {
                                    "id": "Contact Us",
                                    "title": "Contact Us",
                                    "value": "Contact Us"
                                },
                                {
                                    "id": "Back To Menu",
                                    "title": "Back To Menu",
                                    "value": "Back To Menu"
                                },
                                {
                                    "id": "Main Menu",
                                    "title": "Main Menu",
                                    "value": "Main Menu"
                                }
                            ]
                        }
                    ],
                    "actions": [
                        {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "id": "crmSubmitForm",
                        "value": "Submit",
                        "actionId": "7777.70007"
                        }
                    ]
                }
                return payload

    if msg == "Main Menu":
        save_user(wa, {"step": "MAIN_MENU", "attempt": 0})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "How may i help you today?"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Apply For New Loan",
                            "title": "Apply For New Loan",
                            "value": "Apply For New Loan"
                        },
                        {
                            "id": "Existing Customer",
                            "title": "Existing Customer",
                            "value": "Existing Customer"
                        },
                        {
                            "id": "Branch Locator",
                            "title": "Branch Locator",
                            "value": "Branch Locator"
                        },
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload
        # return {"reply": "Main Menu", "flag": True}


    if msg == "Calculators" and step == "NEW_LOAN_MENU":
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Thank you for connecting with Wonder Home Finance!\n\nIf you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                },
                {
                    "type": "TextBlock",
                    "text": "Tap the Visit Website button below to view the branch nearest to your location."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Visit website",
                            "title": "Visit website",
                            "value": "Visit website"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload


    if msg == "Track Loan Status" and step == "NEW_LOAN_MENU":
        # send_text_template(wa, TEMPLATE_BRANCH_LOCATOR_LINK)
        # send_text_template(wa, returntomenu)
        reset_flow(wa)
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "Thank you for connecting with Wonder Home Finance!\n\nIf you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                },
                {
                "type": "TextBlock",
                "text": "Tap the Visit Website button below to view the branch nearest to your location."
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "Visit website",
                    "title": "Visit website",
                    "value": "Visit website"
                    },
                    {
                    "id": "Back To Menu",
                    "title": "Back To Menu",
                    "value": "Back To Menu"
                    },
                    {
                    "id": "Main Menu",
                    "title": "Main Menu",
                    "value": "Main Menu"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload


    if step in ["Balance_Transfer","Home_Construction_Loan","Home_Extension_Loan","Home_Loan_General","Home_Renovation_Loan"] and msg == "Back To Menu":
        save_user(wa, {"step": "CUSTOMER_SUPPORT"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Welcome to Wonder Home Finance Support.\n\nPlease select the loan category you would like assistance with. Our team is here to help you with complete information related to your home loan queries."
                },
                {
                    "type": "Button",
                    "id": "faqCategory",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Balance Transfer",
                            "title": "Balance Transfer",
                            "value": "Balance Transfer"
                        },
                        {
                            "id": "Home Construction Loan",
                            "title": "Home Construction Loan",
                            "value": "Home Construction Loan"
                        },
                        {
                            "id": "Home Extension Loan",
                            "title": "Home Extension Loan",
                            "value": "Home Extension Loan"
                        },
                        {
                            "id": "Home Loan General",
                            "title": "Home Loan General",
                            "value": "Home Loan General"
                        },
                        {
                            "id": "Home Renovation Loan",
                            "title": "Home Renovation Loan",
                            "value": "Home Renovation Loan"
                        },
                        {
                            "id": "Contact Us",
                            "title": "Contact Us",
                            "value": "Contact Us"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        # return payload
        return payload


    if msg == "Back To Menu" and step == "EC_MENU" and tmp_step == "MY_LOAN":
        save_user(wa, {"step": "EC_MENU", "tmp_step": "MY_LOAN"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "How may I help you today?"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Apply for Loan",
                            "title": "Apply for Loan",
                            "value": "Apply for Loan"
                        },
                        {
                            "id": "My Loans",
                            "title": "My Loans",
                            "value": "My Loans"
                        },
                        {
                            "id": "Branch Locator",
                            "title": "Branch Locator",
                            "value": "Branch Locator"
                        },
                        {
                            "id": "Documents",
                            "title": "Documents",
                            "value": "Documents"
                        },
                        {
                            "id": "Install WHFL App",
                            "title": "Install WHFL App",
                            "value": "Install WHFL App"
                        },
                        {
                            "id": "Pay EMI Now",
                            "title": "Pay EMI Now",
                            "value": "Pay EMI Now"
                        },
                        {
                            "id": "Contact Us",
                            "title": "Contact Us",
                            "value": "Contact Us"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload


    if msg == "Back To Menu" and step == "LANG":
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        save_user(wa, {"step": "MAIN_MENU", "attempt": 0})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "How may i help you today?"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "Apply For New Loan",
                    "title": "Apply For New Loan",
                    "value": "Apply For New Loan"
                    },
                    {
                    "id": "Existing Customer",
                    "title": "Existing Customer",
                    "value": "Existing Customer"
                    },
                    {
                    "id": "Branch Locator",
                    "title": "Branch Locator",
                    "value": "Branch Locator"
                    },
                    {
                    "id": "Customer Support",
                    "title": "Customer Support",
                    "value": "Customer Support"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload
        # return {"reply": "Back To Menu", "flag": True}

    if msg == "Back To Menu" and step == "MAIN_MENU":
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        save_user(wa, {"step": "MAIN_MENU", "attempt": 0})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "How may i help you today?"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "Apply For New Loan",
                    "title": "Apply For New Loan",
                    "value": "Apply For New Loan"
                    },
                    {
                    "id": "Existing Customer",
                    "title": "Existing Customer",
                    "value": "Existing Customer"
                    },
                    {
                    "id": "Branch Locator",
                    "title": "Branch Locator",
                    "value": "Branch Locator"
                    },
                    {
                    "id": "Customer Support",
                    "title": "Customer Support",
                    "value": "Customer Support"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload
        # return {"reply": "Back To Menu", "flag": True}

    if step == "NP_PAN" and msg == "Back To Menu":
        save_user(wa, {"step": "MAIN_MENU"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                    {
                        "type": "TextBlock",
                        "text": "Welcome to WHFL! What can I assist you?"
                    },
                    {
                        "type": "Button",
                        "id": "serviceType",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Apply for a Loan",
                                "title": "Apply for a Loan",
                                "value": "Apply for a Loan"
                            },
                            {
                                "id": "Calculators",
                                "title": "Calculators",
                                "value": "Calculators"
                            },
                            {
                                "id": "Back To Menu",
                                "title": "Back To Menu",
                                "value": "Back To Menu"
                            },
                            {
                                "id": "Main Menu",
                                "title": "Main Menu",
                                "value": "Main Menu"
                            }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload



    if step == "NEW_LOAN_MENU" and msg == "Back To Menu":
        save_user(wa, {"step": "MAIN_MENU"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                    {
                        "type": "TextBlock",
                        "text": "Welcome to WHFL! What can I assist you?"
                    },
                    {
                        "type": "Button",
                        "id": "serviceType",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Apply for a Loan",
                                "title": "Apply for a Loan",
                                "value": "Apply for a Loan"
                            },
                            {
                                "id": "Calculators",
                                "title": "Calculators",
                                "value": "Calculators"
                            },
                            {
                                "id": "Back To Menu",
                                "title": "Back To Menu",
                                "value": "Back To Menu"
                            },
                            {
                                "id": "Main Menu",
                                "title": "Main Menu",
                                "value": "Main Menu"
                            }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if msg == "Back To Menu" and step == "MAIN_MENU":
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        save_user(wa, {"step": "MAIN_MENU", "attempt": 0})
        # return {"reply": "Back To Menu", "flag": True}
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "How may i help you today?"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "Apply For New Loan",
                    "title": "Apply For New Loan",
                    "value": "Apply For New Loan"
                    },
                    {
                    "id": "Existing Customer",
                    "title": "Existing Customer",
                    "value": "Existing Customer"
                    },
                    {
                    "id": "Branch Locator",
                    "title": "Branch Locator",
                    "value": "Branch Locator"
                    },
                    {
                    "id": "Customer Support",
                    "title": "Customer Support",
                    "value": "Customer Support"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if msg == "Back To Menu" and step == "EC_MENU":
        save_user(wa, {"step": "MAIN_MENU"})
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        # return {"reply": "Back To Menu", "flag": True}
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "How may i help you today?"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Apply For New Loan",
                            "title": "Apply For New Loan",
                            "value": "Apply For New Loan"
                        },
                        {
                            "id": "Existing Customer",
                            "title": "Existing Customer",
                            "value": "Existing Customer"
                        },
                        {
                            "id": "Branch Locator",
                            "title": "Branch Locator",
                            "value": "Branch Locator"
                        },
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload



    if msg == "Back To Menu" and step == "Contact_Us":
        save_user(wa, {"step": "EC_MENU"})
        # send_text_template(wa, EXISTING_LOAN_NUMBER)
        # return {"reply": "Back To Menu", "flag": True}
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "How may I help you today?"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Apply for Loan",
                            "title": "Apply for Loan",
                            "value": "Apply for Loan"
                        },
                        {
                            "id": "My Loans",
                            "title": "My Loans",
                            "value": "My Loans"
                        },
                        {
                            "id": "Branch Locator",
                            "title": "Branch Locator",
                            "value": "Branch Locator"
                        },
                        {
                            "id": "Documents",
                            "title": "Documents",
                            "value": "Documents"
                        },
                        {
                            "id": "Install WHFL App",
                            "title": "Install WHFL App",
                            "value": "Install WHFL App"
                        },
                        {
                            "id": "Pay EMI Now",
                            "title": "Pay EMI Now",
                            "value": "Pay EMI Now"
                        },
                        {
                            "id": "Contact Us",
                            "title": "Contact Us",
                            "value": "Contact Us"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if msg == "Back To Menu" and step == "DOC_MENU" and tmp_step == "DOC_TYPE" :
        save_user(wa, {"step": "DOC_MENU", "tmp_step": ""})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Please choose the type of document you would like to download from the list below."
                },
                {
                    "type": "Button",
                    "id": "Documents",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Interest Certificate",
                            "title": "Interest Certificate",
                            "value": "Interest Certificate"
                        },
                        {
                            "id": "Repayment Schedule",
                            "title": "Repayment Schedule",
                            "value": "Repayment Schedule"
                        },
                        {
                            "id": "Welcome Letter",
                            "title": "Welcome Letter",
                            "value": "Welcome Letter"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if msg == "Back To Menu" and step == "DOC_MENU":
        save_user(wa, {"step": "EC_MENU"})
        # send_text_template(wa, EXISTING_LOAN_NUMBER)
        # return {"reply": "Back To Menu", "flag": True}
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "How may I help you today?"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Apply for Loan",
                            "title": "Apply for Loan",
                            "value": "Apply for Loan"
                        },
                        {
                            "id": "My Loans",
                            "title": "My Loans",
                            "value": "My Loans"
                        },
                        {
                            "id": "Branch Locator",
                            "title": "Branch Locator",
                            "value": "Branch Locator"
                        },
                        {
                            "id": "Documents",
                            "title": "Documents",
                            "value": "Documents"
                        },
                        {
                            "id": "Install WHFL App",
                            "title": "Install WHFL App",
                            "value": "Install WHFL App"
                        },
                        {
                            "id": "Pay EMI Now",
                            "title": "Pay EMI Now",
                            "value": "Pay EMI Now"
                        },
                        {
                            "id": "Contact Us",
                            "title": "Contact Us",
                            "value": "Contact Us"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if msg == "Customer Support" and step != "Back To Menu":
        save_user(wa, {"step": "CUSTOMER_SUPPORT"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Welcome to Wonder Home Finance Support.\n\nPlease select the loan category you would like assistance with. Our team is here to help you with complete information related to your home loan queries."
                },
                {
                    "type": "Button",
                    "id": "faqCategory",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Balance Transfer",
                            "title": "Balance Transfer",
                            "value": "Balance Transfer"
                        },
                        {
                            "id": "Home Construction Loan",
                            "title": "Home Construction Loan",
                            "value": "Home Construction Loan"
                        },
                        {
                            "id": "Home Extension Loan",
                            "title": "Home Extension Loan",
                            "value": "Home Extension Loan"
                        },
                        {
                            "id": "Home Loan General",
                            "title": "Home Loan General",
                            "value": "Home Loan General"
                        },
                        {
                            "id": "Home Renovation Loan",
                            "title": "Home Renovation Loan",
                            "value": "Home Renovation Loan"
                        },
                        {
                            "id": "Contact Us",
                            "title": "Contact Us",
                            "value": "Contact Us"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload


    if step == "LANG" and  msg == "No":
        reset_flow(wa)
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Thank you for connecting with Wonder Home Finance!\n\nIf you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload


    # =====================================================
    # LANGUAGE / START
    # =====================================================
    existing_smsRecordId = user.get("smsRecordId") if user else None
    if not existing_smsRecordId:
        if step == "LANG":
            if msg in ["English", "Hindi"]:
                save_user(wa, {"step": "ASK_MOBILE", "attempt": 0})
                payload = {
                    "type": "adaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "Please enter your valid 10-digit mobile number to continue with the verification process."
                        }
                    ],
                    "actions": [
                    ]
                }
                return payload

            payload = {
                    "type": "adaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "Please enter your valid 10-digit mobile number to continue with the verification process."
                        }
                    ],
                    "actions": [
                    ]
            }
            return payload
            # return {"reply": "Select language", "flag": True}

        if msg == "Change Number" and step == "OTP_FAILED_MENU":
            save_user(wa, {"step": "ASK_MOBILE", "attempt": 0})
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Please enter your valid 10-digit mobile number to continue with the verification process."
                    }
                ],
                "actions": [
                ]
            }

            return payload

    # =====================================================
    # MOBILE COLLECTION
    # =====================================================
    if step == "ASK_MOBILE":
        if msg.isdigit() and len(msg) == 10:
            otp_res = generate_otp(msg)
            if otp_res.get("operationStatus") == "1":
                save_user(wa, {"mobile": msg, "smsRecordId": otp_res.get("smsRecordId"), "step": "OTP", "attempt": 0})
                payload = {
                    "type": "adaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "Your One-Time Password (OTP) has been sent successfully.\n\nPlease enter the valid OTP to proceed."
                        }
                    ],
                    "actions": [
                    ]
                }
                return payload


        if attempt_failed(user, wa):
            # send_text_template(wa, TEMPLATE_PHONE_NUMBER)
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Please enter your valid 10-digit mobile number to continue with the verification process."
                    }
                ],
                "actions": [
                ]
            }

            return payload
        return {"reply": "Enter valid mobile text template"}

    elif step == "OTP_FAILED_MENU" and msg == "RESEND OTP":
        # if step == "OTP_FAILED_MENU" and msg == "RESEND OTP":
        stored_mobile = user.get("mobile") # MongoDB se saved number nikala
        if stored_mobile:
            otp_res = generate_otp(stored_mobile) # Saved number par OTP bheja
            if otp_res.get("operationStatus") == "1":
                save_user(wa, {
                    "smsRecordId": otp_res.get("smsRecordId"),
                    "step": "OTP",
                    "attempt": 0
                })
                payload = {
                    "type": "adaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "Your One-Time Password (OTP) has been resent successfully.\n\nPlease enter the valid OTP to proceed."
                        }
                    ],
                    "actions": [
                    ]
                }
                return payload

        if attempt_failed(user, wa):
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Please enter your valid 10-digit mobile number to continue with the verification process."
                    }
                ],
                "actions": [
                ]
            }

            return payload
        return {"reply": "Enter valid mobile text template"}

    # =====================================================
    # OTP VERIFICATION
    # =====================================================
    if step == "OTP":
        res = validate_otp(user["smsRecordId"], msg)
        if res.get("operationStatus") == "1":
            save_user(wa, {"step": "MAIN_MENU", "attempt": 0})
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "How may i help you today?"
                    },
                    {
                        "type": "Button",
                        "id": "serviceType",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Apply For New Loan",
                                "title": "Apply For New Loan",
                                "value": "Apply For New Loan"
                            },
                            {
                                "id": "Existing Customer",
                                "title": "Existing Customer",
                                "value": "Existing Customer"
                            },
                            {
                                "id": "Branch Locator",
                                "title": "Branch Locator",
                                "value": "Branch Locator"
                            },
                            {
                                "id": "Customer Support",
                                "title": "Customer Support",
                                "value": "Customer Support"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "id": "crmSubmitForm",
                        "value": "Submit",
                        "actionId": "7777.70007"
                    }
                ]
            }
            return payload

        if attempt_failed(user, wa):
            save_user(wa, {"step": "OTP_FAILED_MENU", "attempt": 0})
            # send_text_template(wa, changeandresendmenu)
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "You have entered an incorrect OTP three times. You can request a new OTP to try again, or update your mobile number if you wish to use a different one."
                    },
                    {
                        "type": "Button",
                        "id": "serviceType",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Change Number",
                                "title": "Change Number",
                                "value": "Change Number"
                            },
                            {
                                "id": "RESEND OTP",
                                "title": "RESEND OTP",
                                "value": "RESEND OTP"
                            }
                        ]
                    }
                ],
                "actions": [
                ]
            }

            return payload


        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Invalid OTP entered. For secure verification, please re-enter the correct OTP."
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }

        return payload

    if step == "EC_MENU" and msg == "Apply for Loan":
        save_user(wa, {"name": msg, "step": "NP_LOAN_TYPE"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "Welcome to WHFL! What can I assist you?"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                        "id": "Apply for a Loan",
                        "title": "Apply for a Loan",
                        "value": "Apply for a Loan"
                    },
                    {
                        "id": "Calculators",
                        "title": "Calculators",
                        "value": "Calculators"
                    },
                    {
                        "id": "Back To Menu",
                        "title": "Back To Menu",
                        "value": "Back To Menu"
                    },
                    {
                        "id": "Main Menu",
                        "title": "Main Menu",
                        "value": "Main Menu"
                    }
                ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    # =====================================================
    # MAIN MENU
    # =====================================================

    if step == "MAIN_MENU":
        if msg == "Apply For New Loan":
            save_user(wa, {"step": "NEW_LOAN_MENU"})
            # send_text_template(wa, TEMPLATE_NEW_PROSPECT_MENU)
            # return {"reply": "New prospect menu", "flag": True}
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Welcome to WHFL! What can I assist you?"
                    },
                    {
                        "type": "Button",
                        "id": "serviceType",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Apply for a Loan",
                                "title": "Apply for a Loan",
                                "value": "Apply for a Loan"
                            },
                            {
                                "id": "Calculators",
                                "title": "Calculators",
                                "value": "Calculators"
                            },
                            {
                                "id": "Back To Menu",
                                "title": "Back To Menu",
                                "value": "Back To Menu"
                            }
                            ,
                            {
                                "id": "Main Menu",
                                "title": "Main Menu",
                                "value": "Main Menu"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "id": "crmSubmitForm",
                        "value": "Submit",
                        "actionId": "7777.70007"
                    }
                ]
            }
            return payload


        if msg == "Existing Customer":
            filename = "existing-loan-details-8076893187.pdf"
            file_path = f"{PDF_STORAGE_PATH}/{filename}"
            # loan_data = get_loan_details("8076893187")
            # loan_rows = extract_loan_details(loan_data)

            # create_loan_details_pdf(loan_rows, file_path)

            pdf_url = f"https://api-retriever-bitnet.c-zentrix.com/download/cibil?file={filename}"
            print(pdf_url,"pdf_url")
            tmp_data = send_cibil_pdf_whatsapp("917533941271", pdf_url,filename)
            print(tmp_data,"++++++++++++++++++++++++++++")

            if loan_data["operationStatus"] != "1":
                res = get_all_loan("8076893187")
                reply_text,customerName = format_loans_for_whatsapp(res)
                save_user(wa, {"step": "EC_LOAN"})
                payload = {
                    "type": "adaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"Hi {customerName}, please find below the summary of your active home loan account with us.\n\n{reply_text} \n\nEnter the last 5 digits of your loan account number for more details."
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.Submit",
                            "title": "Submit",
                            "id": "crmSubmitForm",
                            "value": "Submit",
                            "actionId": "7777.70007"
                        }
                    ]
                }
                return payload
            else:
                payload = {
                    "type": "adaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"Based on the information provided, there is currently no existing loan associated with your profile in our records. If you require any further assistance or clarification, please feel free to reach out."
                        },
                        {
                            "type": "Button",
                            "id": "serviceType",
                            "style": "expanded",
                            "choices": [
                                {
                                    "id": "Main Menu",
                                    "title": "Main Menu",
                                    "value": "Main Menu"
                                },
                                {
                                    "id": "Back To Menu",
                                    "title": "Back To Menu",
                                    "value": "Back To Menu"
                                }
                            ]
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.Submit",
                            "title": "Submit",
                            "id": "crmSubmitForm",
                            "value": "Submit",
                            "actionId": "7777.70007"
                        }
                    ]
                }
                return payload

        if msg == "Branch Locator":
            reset_flow(wa)
            data = send_whatsapp_cta_template(
                mobile_no="917533941271",
                template_name="branch_locator_v3",
                message_body=["Monish"],
                license_id="8e2a733c2796c6367e838fff6191b74d"
            )
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Thank you for connecting with Wonder Home Finance!\n\nIf you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                    },
                    {
                        "type": "Button",
                        "id": "serviceType",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Customer Support",
                                "title": "Customer Support",
                                "value": "Customer Support"
                            },
                            {
                                "id": "Back To Menu",
                                "title": "Back To Menu",
                                "value": "Back To Menu"
                            },
                            {
                                "id": "Main Menu",
                                "title": "Main Menu",
                                "value": "Main Menu"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "id": "crmSubmitForm",
                        "value": "Submit",
                        "actionId": "7777.70007"
                    }
                ]
            }
            return payload


    if step == "CUSTOMER_ASS" and msg == "Critical cases":
        save_user(wa, {"step": "CRITCAL_CASE"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Welcome to Wonder Home Finance Customer Support.\n\nPlease select the service request that best matches your concern. Our support team will assist you accordingly."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "FCL/SOA/LOD Request",
                            "title": "FCL / SOA / LOD Request",
                            "value": "FCL/SOA/LOD Request"
                        },
                        {
                            "id": "EMI/ Pre-EMI Related",
                            "title": "EMI / Pre-EMI Related",
                            "value": "EMI/ Pre-EMI Related"
                        },
                        {
                            "id": "Refund",
                            "title": "Refund",
                            "value": "Refund"
                        },
                        {
                            "id": "CLSS refund related",
                            "title": "CLSS Refund Related",
                            "value": "CLSS refund related"
                        },
                        {
                            "id": "Loan Application",
                            "title": "Loan Application",
                            "value": "Loan Application"
                        },
                        {
                            "id": "Cibil related",
                            "title": "CIBIL Related",
                            "value": "Cibil related"
                        },
                        {
                            "id": "Fake signature",
                            "title": "Fake Signature",
                            "value": "Fake signature"
                        },
                        {
                            "id": "More Option",
                            "title": "More Option",
                            "value": "More Option"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if step == "CUSTOMER_ASS" and msg == "Non-critical cases":
        save_user(wa, {"step": "NON_CRITCAL_CASE"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Please select the document or service request you would like to proceed with."
                },
                {
                    "type": "Button",
                    "id": "documentRequest",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Bounce Memo",
                            "title": "Bounce Memo",
                            "value": "Bounce Memo"
                        },
                        {
                            "id": "Copy of Insurance Policy",
                            "title": "Copy of Insurance Policy",
                            "value": "Copy of Insurance Policy"
                        },
                        {
                            "id": "Copy of Documents",
                            "title": "Copy of Documents",
                            "value": "Copy of Documents"
                        },
                        {
                            "id": "List of Documents",
                            "title": "List of Documents",
                            "value": "List of Documents"
                        },
                        {
                            "id": "Statement of Account",
                            "title": "Statement of Account",
                            "value": "Statement of Account"
                        },
                        {
                            "id": "Repayment Schedule",
                            "title": "Repayment Schedule",
                            "value": "Repayment Schedule"
                        },
                        {
                            "id": "More Option",
                            "title": "More Option",
                            "value": "More Option"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70008"
                }
            ]
        }

        return payload
    # =====================================================
    # CUSTOMER SUPPORT LOGIC
    # =====================================================
    if step in ["Balance_Transfer","Home_Construction_Loan","Home_Extension_Loan","Home_Loan_General","Home_Renovation_Loan"] and  msg == "Yes":
        save_user(wa, {"step": "CUSTOMER_ASS"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Thank you for connecting with Wonder Home Finance!\n\nIf you need any further assistance, feel free to reach out. Wishing you a wonderful day!\n\nPlease select a loan option below to proceed."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Critical cases",
                            "title": "Critical cases",
                            "value": "Critical cases"
                        },
                        {
                            "id": "Non-critical cases",
                            "title": "Non-critical cases",
                            "value": "Non-critical cases"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if step in ["Balance_Transfer","Home_Construction_Loan","Home_Extension_Loan","Home_Loan_General","Home_Renovation_Loan"] and msg == "No":
        reset_flow(wa)
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Thank you for connecting with Wonder Home Finance!\n\nIf you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if msg in ["Balance Transfer","Home Construction Loan","Home Extension Loan","Home Loan General","Home Renovation Loan"] and step == "CUSTOMER_SUPPORT":
        if msg == "Balance Transfer":
            save_user(wa, {"step": "Balance_Transfer"})
            FAQ_1 = "**Q. What is Home Loan Balance Transfer?**\n\n" \
            "Ans. Home Loan Balance Transfer is a facility that allows you to transfer your existing home loan from your current bank to Wonder Home Finance. This helps you enjoy lower EMIs and savings.\n\n" \
            "**Q. Can I transfer my home loan from any lender?**\n\n" \
            "Ans. Yes. You can transfer your home loan or loan against property from any lender, subject to eligibility.\n\n" \
            "**Q. Can I opt for a top-up loan during the balance transfer?**\n\n" \
            "Ans. Yes. You can avail a top-up loan to access additional funds."
        elif msg == "Home Construction Loan":
            save_user(wa, {"step": "Home_Construction_Loan"})
            FAQ_1 = "**Q. What is Home Loan Balance Transfer?**\n\n" \
            "Ans. Home Loan Balance Transfer is a facility that allows you to transfer your existing home loan from your current bank to Wonder Home Finance. This helps you enjoy lower EMIs and savings.\n\n" \
            "**Q. Can I transfer my home loan from any lender?**\n\n" \
            "Ans. Yes. You can transfer your home loan or loan against property from any lender, subject to eligibility.\n\n" \
            "**Q. Can I opt for a top-up loan during the balance transfer?**\n\n" \
            "Ans. Yes. You can avail a top-up loan to access additional funds."
        elif msg == "Home Extension Loan":
            save_user(wa, {"step": "Home_Extension_Loan"})
            FAQ_1 = "**Q. What is Home Loan Balance Transfer?**\n\n" \
            "Ans. Home Loan Balance Transfer is a facility that allows you to transfer your existing home loan from your current bank to Wonder Home Finance. This helps you enjoy lower EMIs and savings.\n\n" \
            "**Q. Can I transfer my home loan from any lender?**\n\n" \
            "Ans. Yes. You can transfer your home loan or loan against property from any lender, subject to eligibility.\n\n" \
            "**Q. Can I opt for a top-up loan during the balance transfer?**\n\n" \
            "Ans. Yes. You can avail a top-up loan to access additional funds."
        elif msg == "Home Loan General":
            save_user(wa, {"step": "Home_Loan_General"})
            FAQ_1 = "**Q. What is Home Loan Balance Transfer?**\n\n" \
            "Ans. Home Loan Balance Transfer is a facility that allows you to transfer your existing home loan from your current bank to Wonder Home Finance. This helps you enjoy lower EMIs and savings.\n\n" \
            "**Q. Can I transfer my home loan from any lender?**\n\n" \
            "Ans. Yes. You can transfer your home loan or loan against property from any lender, subject to eligibility.\n\n" \
            "**Q. Can I opt for a top-up loan during the balance transfer?**\n\n" \
            "Ans. Yes. You can avail a top-up loan to access additional funds."
        elif msg == "Home Renovation Loan":
            save_user(wa, {"step": "Home_Renovation_Loan"})
            FAQ_1 = "**Q. What is Home Loan Balance Transfer?**\n\n" \
            "Ans. Home Loan Balance Transfer is a facility that allows you to transfer your existing home loan from your current bank to Wonder Home Finance. This helps you enjoy lower EMIs and savings.\n\n" \
            "**Q. Can I transfer my home loan from any lender?**\n\n" \
            "Ans. Yes. You can transfer your home loan or loan against property from any lender, subject to eligibility.\n\n" \
            "**Q. Can I opt for a top-up loan during the balance transfer?**\n\n" \
            "Ans. Yes. You can avail a top-up loan to access additional funds."

        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"{FAQ_1}\n\nWe hope your query has been addressed.\n\nIf you need any further assistance, please select *Yes*.\n\nThank you for choosing Wonder Home Finance."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Yes",
                            "title": "Yes",
                            "value": "Yes"
                        },
                        {
                            "id": "No",
                            "title": "No",
                            "value": "No"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if msg == "Main_Menu" and step == "NP_LOAN_TYPE":
        save_user(wa, {"step": "MAIN_MENU"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "How may i help you today?"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Apply For New Loan",
                            "title": "Apply For New Loan",
                            "value": "Apply For New Loan"
                        },
                        {
                            "id": "Existing Customer",
                            "title": "Existing Customer",
                            "value": "Existing Customer"
                        },
                        {
                            "id": "Branch Locator",
                            "title": "Branch Locator",
                            "value": "Branch Locator"
                        },
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    # =====================================================
    # NEW LOAN FLOW
    # =====================================================
    if step == "NEW_LOAN_MENU" or msg != "Back To Menu":
        if msg == "Apply for a Loan":
            save_user(wa, {"step": "NP_NAME"})
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                    "type": "TextBlock",
                    "text": "Please enter your full name."
                    }
                ],
                "actions": [
                ]
            }
            return payload
            # return {"reply": "Please enter your full name", "flag": False}

        if msg == "BACK TO MENU":
            save_user(wa, {"step": "MAIN_MENU"})
            # # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
            # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
            # return {"reply": "Back to main menu", "flag": True}
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "How may i help you today?"
                    },
                    {
                        "type": "Button",
                        "id": "serviceType",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Apply For New Loan",
                                "title": "Apply For New Loan",
                                "value": "Apply For New Loan"
                            },
                            {
                                "id": "Existing Customer",
                                "title": "Existing Customer",
                                "value": "Existing Customer"
                            },
                            {
                                "id": "Branch Locator",
                                "title": "Branch Locator",
                                "value": "Branch Locator"
                            },
                            {
                                "id": "Customer Support",
                                "title": "Customer Support",
                                "value": "Customer Support"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "id": "crmSubmitForm",
                        "value": "Submit",
                        "actionId": "7777.70007"
                    }
                ]
            }
            return payload

    if step == "NP_NAME":
        save_user(wa, {"name": msg, "step": "NP_PAN"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"Hi {msg} Please select a loan option below to proceed."
                },
                {
                    "type": "Button",
                    "id": "loanType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Home Purchase Loan",
                            "title": "Home Purchase Loan",
                            "value": "Home Purchase Loan"
                        },
                        {
                            "id": "Home Construction Loan",
                            "title": "Home Construction Loan",
                            "value": "Home Construction Loan"
                        },
                        {
                            "id": "Construction Loan",
                            "title": "Construction Loan",
                            "value": "Construction Loan"
                        },
                        {
                            "id": "Home Renovation Loan",
                            "title": "Home Renovation Loan",
                            "value": "Home Renovation Loan"
                        },
                        {
                            "id": "Home Extension Loan",
                            "title": "Home Extension Loan",
                            "value": "Home Extension Loan"
                        },
                        {
                            "id": "Loan Against Property",
                            "title": "Loan Against Property",
                            "value": "Loan Against Property"
                        },
                        {
                            "id": "Balance Transfer",
                            "title": "Balance Transfer",
                            "value": "Balance Transfer"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload
        # send_text_template_with_variables(wa, TEMPLATE_NEW_PROSPECT_LOAN_TYPE, msg)
        # return {"reply": "TEMPLATE_NEW_PROSPECT_LOAN_TYPE", "flag": True}


    if step == "NP_PAN":
        save_user(wa, {"name": msg, "step": "NP_FLOW"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "flow",
                    "id": "loanApplication",
                    "style": "expanded",
                    "flow": {
                        "name": "apply_loan_application",
                        "language": {
                        "code": "en"
                        },
                        "components": [
                        {
                            "type": "button",
                            "sub_type": "flow",
                            "index": "0",
                            "parameters": [
                            {
                                "type": "action",
                                "action": {
                                "flow_token": "123"
                                }
                            }
                            ]
                        }
                        ]
                    }
                }
            ],
            "actions": []
            }
        return payload

    if step == "NP_FLOW":
        if isinstance(msg, str):
            msg = json.loads(msg)

        pan = msg.get("screen_0_Enter_Pan_No_1")

        response = verify_pan(pan)
        status_code = response.get("status-code")
        if status_code == "101":
            user_data = get_user(wa)
            access_token = generate_transunion_token()
            document_id,ApplicantLastName,PanNumber = submit_cibil_application(access_token)
            cibil_report = "cibil_report_" + ApplicantLastName + "_" + PanNumber +".pdf"
            fetch_transunion_report_pdf(document_id,access_token,cibil_report)
            pdf_url = f"https://api-retriever-bitnet.c-zentrix.com/download/cibil?file={cibil_report}"
            tmp_data = send_cibil_pdf_whatsapp("917533941271", pdf_url,cibil_report)

            lead_payload = {
                "name": user_data.get("name"),
                "mobile": user_data.get("mobile"),
                "loan_type": user_data.get("loan_type"),
                "amount": user_data.get("amount"),
                "tenure": user_data.get("tenure"),
                "pincode": user_data.get("pincode"),
                "pan": msg
            }

            # reset_flow(wa)
            # send_text_template(wa, returntomenu)
            save_user(wa, {"step": "MAIN_MENU"})
            # delete_pdf_file(cibil_report)
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": f"Dear {ApplicantLastName},\n\n"
                                f"Thank you for applying for a home loan with Wonder Homes.\n\n"
                                f"Your application has been successfully received.\n"
                                f"Our verification team is reviewing your details and you will be contacted shortly.\n\n"
                                f"You will receive your CIBIL report and eligibility update on WhatsApp.\n\n"
                                f"Regards,\n"
                                f"Regards Wonder Home Finance Team."
                    },
                    {
                        "type": "Button",
                        "id": "postApplicationOptions",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Customer Support",
                                "title": "Customer Support",
                                "value": "Customer Support"
                            },
                            {
                                "id": "Back to Main Menu",
                                "title": "Back to Main Menu",
                                "value": "Back to Main Menu"
                            },
                            {
                                "id": "Main Menu",
                                "title": "Main Menu",
                                "value": "Main Menu"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "id": "crmSubmitForm",
                        "value": "Submit",
                        "actionId": "7777.70007"
                    }
                ]
            }
            return payload
        else:
            result = send_whatsapp_flow_message(
                phone_number="917533941271",
                flow_token="123"
            )
            save_user(wa, {"name": msg, "step": "NP_FLOW"})
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "We are unable to verify the PAN number provided.\n\nPlease check your PAN details and enter a valid PAN to continue with your application."
                    }
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "id": "crmSubmitForm",
                        "value": "Submit",
                        "actionId": "7777.70007"
                    }
                ]
            }
            return payload

    if step == "MAIN_MENU" and msg == "Customer Support":
        save_user(wa, {"step": "CUSTOMER_SUPPORT"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Welcome to Wonder Home Finance Support.\n\nPlease select the loan category you would like assistance with. Our team is here to help you with complete information related to your home loan queries."
                },
                {
                    "type": "Button",
                    "id": "faqCategory",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Balance Transfer",
                            "title": "Balance Transfer",
                            "value": "Balance Transfer"
                        },
                        {
                            "id": "Home Construction Loan",
                            "title": "Home Construction Loan",
                            "value": "Home Construction Loan"
                        },
                        {
                            "id": "Home Extension Loan",
                            "title": "Home Extension Loan",
                            "value": "Home Extension Loan"
                        },
                        {
                            "id": "Home Loan General",
                            "title": "Home Loan General",
                            "value": "Home Loan General"
                        },
                        {
                            "id": "Home Renovation Loan",
                            "title": "Home Renovation Loan",
                            "value": "Home Renovation Loan"
                        },
                        {
                            "id": "Contact Us",
                            "title": "Contact Us",
                            "value": "Contact Us"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        # return payload
        return payload

    # if msg == "MAIN_MENU" and step == "Back to Menu":
    if step == "MAIN_MENU" and msg == "Main Menu":
        save_user(wa, {"step": "MAIN_MENU", "attempt": 0})
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        # return {"reply": "finish step", "flag": True}
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "How may i help you today?"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Apply For New Loan",
                            "title": "Apply For New Loan",
                            "value": "Apply For New Loan"
                        },
                        {
                            "id": "Existing Customer",
                            "title": "Existing Customer",
                            "value": "Existing Customer"
                        },
                        {
                            "id": "Branch Locator",
                            "title": "Branch Locator",
                            "value": "Branch Locator"
                        },
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if step == "EC_MENU" and msg == "Customer Support":
        save_user(wa, {"step": "CUSTOMER_SUPPORT"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Welcome to Wonder Home Finance Support.\n\nPlease select the loan category you would like assistance with. Our team is here to help you with complete information related to your home loan queries."
                },
                {
                    "type": "Button",
                    "id": "faqCategory",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Balance Transfer",
                            "title": "Balance Transfer",
                            "value": "Balance Transfer"
                        },
                        {
                            "id": "Home Construction Loan",
                            "title": "Home Construction Loan",
                            "value": "Home Construction Loan"
                        },
                        {
                            "id": "Home Extension Loan",
                            "title": "Home Extension Loan",
                            "value": "Home Extension Loan"
                        },
                        {
                            "id": "Home Loan General",
                            "title": "Home Loan General",
                            "value": "Home Loan General"
                        },
                        {
                            "id": "Home Renovation Loan",
                            "title": "Home Renovation Loan",
                            "value": "Home Renovation Loan"
                        },
                        {
                            "id": "Contact Us",
                            "title": "Contact Us",
                            "value": "Contact Us"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        # return payload
        return payload


    # if msg == "MAIN_MENU" and step == "Back to Menu":
    if step == "EC_MENU" and msg == "Main Menu":
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        save_user(wa, {"step": "MAIN_MENU", "attempt": 0})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "How may i help you today?"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "Apply For New Loan",
                    "title": "Apply For New Loan",
                    "value": "Apply For New Loan"
                    },
                    {
                    "id": "Existing Customer",
                    "title": "Existing Customer",
                    "value": "Existing Customer"
                    },
                    {
                    "id": "Branch Locator",
                    "title": "Branch Locator",
                    "value": "Branch Locator"
                    },
                    {
                    "id": "Customer Support",
                    "title": "Customer Support",
                    "value": "Customer Support"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if step == "EC_MENU" and msg == "My Loans":
        filename = "existing-loan-details-8076893187.pdf"
        file_path = f"{PDF_STORAGE_PATH}/{filename}"
        loan_data = get_loan_details("8076893187")
        loan_rows = extract_loan_details(loan_data)

        create_loan_details_pdf(loan_rows, file_path)

        pdf_url = f"https://api-retriever-bitnet.c-zentrix.com/download/cibil?file={filename}"
        # print(pdf_url,"pdf_url")
        tmp_data = send_cibil_pdf_whatsapp("917533941271", pdf_url,filename)
        res = get_all_loan("8076893187")
        reply_text,customerName = format_loans_for_whatsapp(res)
        save_user(wa, {"tmp_step": "MY_LOAN"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"{reply_text}"
                },
                {
                    "type": "Button",
                    "id": "interestcertificate",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if step == "EC_MENU" and msg == "Branch Locator":
        save_user(wa, {"step": "MAIN_MENU"})
        data = send_whatsapp_cta_template(
            mobile_no="917533941271",
            template_name="branch_locator_v3",
            message_body=["Monish"],
            license_id="8e2a733c2796c6367e838fff6191b74d"
        )
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Thank you for connecting with Wonder Home Finance!\n\nIf you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if step == "CUSTOMER_ASS" and msg == "Back To Menu":
        save_user(wa, {"step": "CUSTOMER_SUPPORT"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Welcome to Wonder Home Finance Support.\n\nPlease select the loan category you would like assistance with. Our team is here to help you with complete information related to your home loan queries."
                },
                {
                    "type": "Button",
                    "id": "faqCategory",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Balance Transfer",
                            "title": "Balance Transfer",
                            "value": "Balance Transfer"
                        },
                        {
                            "id": "Home Construction Loan",
                            "title": "Home Construction Loan",
                            "value": "Home Construction Loan"
                        },
                        {
                            "id": "Home Extension Loan",
                            "title": "Home Extension Loan",
                            "value": "Home Extension Loan"
                        },
                        {
                            "id": "Home Loan General",
                            "title": "Home Loan General",
                            "value": "Home Loan General"
                        },
                        {
                            "id": "Home Renovation Loan",
                            "title": "Home Renovation Loan",
                            "value": "Home Renovation Loan"
                        },
                        {
                            "id": "Contact Us",
                            "title": "Contact Us",
                            "value": "Contact Us"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        # return payload
        return payload

    if step == "CRITCAL_CASE" and msg == "Back To Menu":
        save_user(wa, {"step": "CUSTOMER_ASS"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Thank you for connecting with Wonder Home Finance!\n\nIf you need any further assistance, feel free to reach out. Wishing you a wonderful day!\n\nPlease select a loan option below to proceed."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Critical cases",
                            "title": "Critical cases",
                            "value": "Critical cases"
                        },
                        {
                            "id": "Non-critical cases",
                            "title": "Non-critical cases",
                            "value": "Non-critical cases"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if step == "SUPPPORT_ISSUE" and msg == "Back To Menu":
        save_user(wa, {"step": "CUSTOMER_ASS"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Welcome to Wonder Home Finance Customer Support.\n\nPlease select the service request that best matches your concern. Our support team will assist you accordingly."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "FCL/SOA/LOD Request",
                            "title": "FCL / SOA / LOD Request",
                            "value": "FCL/SOA/LOD Request"
                        },
                        {
                            "id": "EMI/ Pre-EMI Related",
                            "title": "EMI / Pre-EMI Related",
                            "value": "EMI/ Pre-EMI Related"
                        },
                        {
                            "id": "Refund",
                            "title": "Refund",
                            "value": "Refund"
                        },
                        {
                            "id": "CLSS refund related",
                            "title": "CLSS Refund Related",
                            "value": "CLSS refund related"
                        },
                        {
                            "id": "Loan Application",
                            "title": "Loan Application",
                            "value": "Loan Application"
                        },
                        {
                            "id": "Cibil related",
                            "title": "CIBIL Related",
                            "value": "Cibil related"
                        },
                        {
                            "id": "Fake signature",
                            "title": "Fake Signature",
                            "value": "Fake signature"
                        },
                        {
                            "id": "More Option",
                            "title": "More Option",
                            "value": "More Option"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload



    if step == "SUPPPORT_ISSUE" and msg == "Contact Us":
        save_user(wa, {"step": "Contact_Us"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📞 Call us at 1800-102-1002\n📧 Email us at hello@wonderhfl.com\n\nOur team will be happy to help you."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload


    if step == "CUSTOMER_SUPPORT" and msg == "Contact Us":
        save_user(wa, {"step": "Contact_Us"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📞 Call us at 1800-102-1002\n📧 Email us at hello@wonderhfl.com\n\nOur team will be happy to help you."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload


    if step == "EC_MENU" and msg == "Contact Us":
        save_user(wa, {"step": "Contact_Us"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📞 Call us at 1800-102-1002\n📧 Email us at hello@wonderhfl.com\n\nOur team will be happy to help you."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if msg == "Documents" and step == "EC_MENU":
        # send_text_template(wa, docmenutemplatelistmenu)
        save_user(wa, {"step": "DOC_MENU"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Please choose the type of document you would like to download from the list below."
                },
                {
                    "type": "Button",
                    "id": "Documents",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Interest Certificate",
                            "title": "Interest Certificate",
                            "value": "Interest Certificate"
                        },
                        {
                            "id": "Repayment Schedule",
                            "title": "Repayment Schedule",
                            "value": "Repayment Schedule"
                        },
                        {
                            "id": "Welcome Letter",
                            "title": "Welcome Letter",
                            "value": "Welcome Letter"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload


    if msg == "Pay EMI Now" and step == "EC_MENU":
        # send_text_template(wa, docmenutemplatelistmenu)
        # send_text_template(wa, returntomenu)
        save_user(wa, {"step": "EC_LOAN"})
        # reset_flow(wa)
        # return {
        #     "reply": "Pay EMI Now",
        #     "flag": False
        # }
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Kindly choose one of the options below to continue with your EMI payment."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Pay EMI Now",
                            "title": "Pay EMI Now",
                            "value": "Pay EMI Now"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }

        return payload


    if msg == "Install WHFL App" and step == "EC_MENU":

        # send_text_template(wa, TEMPLATE_BRANCH_LOCATOR_LINK)
        # send_text_template(wa, docmenutemplatelistmenu)
        # send_text_template(wa, returntomenu)
        save_user(wa, {"step": "EC_LOAN"})
        # return {
        #     "reply": "Install WHFL App",
        #     "flag": True
        # }
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Thank you for connecting with Wonder Home Finance!\n\nIf you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                },
                {
                    "type": "TextBlock",
                    "text": "Tap the button below to install the WHFL Customer App."
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Install WHFL App",
                            "title": "Install WHFL App",
                            "value": "Install WHFL App"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }

        return payload


    if msg == "Back To Menu" and step == "DOC_MENU":
        save_user(wa, {"step": "MAIN_MENU", "attempt": 0})
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)
        # return {
        #     "reply": "Back To Menu",
        #     "flag": True
        # }
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "How may i help you today?"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "Apply For New Loan",
                    "title": "Apply For New Loan",
                    "value": "Apply For New Loan"
                    },
                    {
                    "id": "Existing Customer",
                    "title": "Existing Customer",
                    "value": "Existing Customer"
                    },
                    {
                    "id": "Branch Locator",
                    "title": "Branch Locator",
                    "value": "Branch Locator"
                    },
                    {
                    "id": "Customer Support",
                    "title": "Customer Support",
                    "value": "Customer Support"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if msg == "Back To Menu" and step == "EC_LOAN":
        save_user(wa, {"step": "EC_MENU", "attempt": 0})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "How may i help you today?"
                },
                {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Apply For New Loan",
                            "title": "Apply For New Loan",
                            "value": "Apply For New Loan"
                        },
                        {
                            "id": "Existing Customer",
                            "title": "Existing Customer",
                            "value": "Existing Customer"
                        },
                        {
                            "id": "Branch Locator",
                            "title": "Branch Locator",
                            "value": "Branch Locator"
                        },
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "id": "crmSubmitForm",
                    "value": "Submit",
                    "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if msg == "Back To Menu" and step == "EC_LOAN":
        save_user(wa, {"step": "EC_MENU", "attempt": 0})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                "type": "TextBlock",
                "text": "How may i help you today?"
                },
                {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                    "id": "Apply For New Loan",
                    "title": "Apply For New Loan",
                    "value": "Apply For New Loan"
                    },
                    {
                    "id": "Existing Customer",
                    "title": "Existing Customer",
                    "value": "Existing Customer"
                    },
                    {
                    "id": "Branch Locator",
                    "title": "Branch Locator",
                    "value": "Branch Locator"
                    },
                    {
                    "id": "Customer Support",
                    "title": "Customer Support",
                    "value": "Customer Support"
                    }
                ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    # =====================================================
    # EXISTING CUSTOMER FLOW
    # =====================================================
    if step == "EC_LOAN":
        res = validate_loan_with_crm("8076893187", msg)
        if res["status"] == "MATCH":
            save_user(wa, {"step": "EC_MENU"})
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "I How may I help you today?"
                    },
                    {
                        "type": "Button",
                        "id": "serviceType",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Apply for Loan",
                                "title": "Apply for Loan",
                                "value": "Apply for Loan"
                            },
                            {
                                "id": "My Loans",
                                "title": "My Loans",
                                "value": "My Loans"
                            },
                            {
                                "id": "Branch Locator",
                                "title": "Branch Locator",
                                "value": "Branch Locator"
                            },
                            {
                                "id": "Documents",
                                "title": "Documents",
                                "value": "Documents"
                            },
                            {
                                "id": "Install WHFL App",
                                "title": "Install WHFL App",
                                "value": "Install WHFL App"
                            },
                            {
                                "id": "Pay EMI Now",
                                "title": "Pay EMI Now",
                                "value": "Pay EMI Now"
                            },
                            {
                                "id": "Contact Us",
                                "title": "Contact Us",
                                "value": "Contact Us"
                            },
                            {
                                "id": "Back To Menu",
                                "title": "Back To Menu",
                                "value": "Back To Menu"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "id": "crmSubmitForm",
                        "value": "Submit",
                        "actionId": "7777.70007"
                    }
                ]
            }
           
            return payload
        else:
            # send_text_template(wa, EXISTING_LOAN_NUMBER_NOT_VALID)
            # return {"reply": "We are unable to verify the loan number with the registered mobile number.Kindly update your mobile number at the nearest branch or raise a request through the WHFL Mobile App for assistance.", "flag": False}
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "We are unable to verify the loan number with the registered mobile number. Kindly update your mobile number at the nearest branch or raise a request through the WHFL Mobile App for assistance."
                    },
                    {
                        "type": "Button",
                        "id": "serviceType",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Main Menu",
                                "title": "Main Menu",
                                "value": "Main Menu"
                            },
                            {
                                "id": "Back To Menu",
                                "title": "Back To Menu",
                                "value": "Back To Menu"
                            }
                        ]
                    }
                ],
                "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
            }

            return payload

    if step == "DOC_MENU" and msg == "Mini SOA":
        pdf_url = f"https://api-retriever-bitnet.c-zentrix.com/download/cibil?file=cibil_report_BANSAL_DVWPB4941P.pdf"
        tmp_data = send_cibil_pdf_whatsapp("917533941271", pdf_url,"Interest_Certificate_LN29003HP22-23010778.pdf")
        # send_text_template(wa, returntomenu)
        save_user(wa, {"step": "DOC_MENU"})
        # return {"reply": "Mini SOA", "flag": True}
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Thank you for connecting with Wonder Home Finance! If you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                },
                {
                    "type": "Button",
                    "id": "interestcertificate",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if step == "DOC_MENU" and msg == "Interest Certificate":
        data = download_interest_certificate("LN29003HP22-23010778", "01-04-2024", "31-03-2025")

        pdf_url = f"https://api-retriever-bitnet.c-zentrix.com/download/cibil?file=Interest_Certificate_LN29003HP22-23010778.pdf"
        tmp_data = send_cibil_pdf_whatsapp("917533941271", pdf_url,"Interest_Certificate_LN29003HP22-23010778.pdf")
        # delete_pdf_file("Interest_Certificate_LN29003HP22-23010778.pdf")

        save_user(wa, {"step": "DOC_MENU", "tmp_step": "DOC_TYPE"})
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Thank you for connecting with Wonder Home Finance! If you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                },
                {
                    "type": "Button",
                    "id": "interestcertificate",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload

    if step == "DOC_MENU" and msg == "Repayment Schedule":
        repayment_data = fetch_repayment_schedule("LN29003HP22-23010778")
        status = repayment_data["operationStatus"]
        if status == "1":
            emi_rows  = extract_main_fields(repayment_data)
            file_path = f"{PDF_STORAGE_PATH}/EMI_Schedule_LN29003HP22-23010778.pdf"
            create_emi_pdf("LN29003HP22-23010778", emi_rows, file_path)
            pdf_url = f"https://api-retriever-bitnet.c-zentrix.com/download/cibil?file=EMI_Schedule_LN29003HP22-23010778.pdf"
            tmp_data = send_cibil_pdf_whatsapp("917533941271", pdf_url,"EMI_Schedule_LN29003HP22-23010778.pdf")
            # print(tmp_data,"rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
            # delete_pdf_file("welcome_letter_LN29003HP22-23010778.pdf")
            # send_text_template(wa, returntomenu)
            save_user(wa, {"step": "DOC_MENU", "tmp_step": "DOC_TYPE"})
            # return {"reply": "Repayment Schedule", "flag": True}
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Thank you for connecting with Wonder Home Finance! If you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                    },
                    {
                        "type": "Button",
                        "id": "interestcertificate",
                        "style": "expanded",
                        "choices": [
                            {
                                "id": "Customer Support",
                                "title": "Customer Support",
                                "value": "Customer Support"
                            },
                            {
                                "id": "Back To Menu",
                                "title": "Back To Menu",
                                "value": "Back To Menu"
                            },
                            {
                                "id": "Main Menu",
                                "title": "Main Menu",
                                "value": "Main Menu"
                            }
                        ]
                    }
                ],
                "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
            }
            return payload
        else:
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "We are unable to fetch your Repayment Schedule at the moment due to a system authentication issue. Please try again after some time or contact customer support for assistance."
                    }
                ],
                "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
            }
            return payload

    if step == "DOC_MENU" and msg == "Welcome Letter":
        download_welcome_letter("LN29003HP22-23010778")
        pdf_url = f"https://api-retriever-bitnet.c-zentrix.com/download/cibil?file=welcome_letter_LN29003HP22-23010778.pdf"
        tmp_data = send_cibil_pdf_whatsapp("917533941271", pdf_url,"welcome_letter_LN29003HP22-23010778.pdf")
        # print(tmp_data,"wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww")
        # delete_pdf_file("welcome_letter_LN29003HP22-23010778.pdf")
        # send_text_template(wa, returntomenu)
        save_user(wa, {"step": "DOC_MENU", "tmp_step": "DOC_TYPE"})
        # return {"reply": "welcome_letter", "flag": True}
        payload = {
            "type": "adaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Thank you for connecting with Wonder Home Finance! If you need any further assistance, feel free to reach out. Wishing you a wonderful day!"
                },
                {
                    "type": "Button",
                    "id": "interestcertificate",
                    "style": "expanded",
                    "choices": [
                        {
                            "id": "Customer Support",
                            "title": "Customer Support",
                            "value": "Customer Support"
                        },
                        {
                            "id": "Back To Menu",
                            "title": "Back To Menu",
                            "value": "Back To Menu"
                        },
                        {
                            "id": "Main Menu",
                            "title": "Main Menu",
                            "value": "Main Menu"
                        }
                    ]
                }
            ],
            "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
        }
        return payload


    if existing_mobile:
        if msg == "English" or msg == "english":
            # send_text_template(wa, TEMPLATE_FIRST_MAIN_MENU)

            save_user(wa, {"step": "MAIN_MENU", "attempt": 0})
            payload = {
                "type": "adaptiveCard",
                "body": [
                    {
                    "type": "TextBlock",
                    "text": "How may i help you today?"
                    },
                    {
                    "type": "Button",
                    "id": "serviceType",
                    "style": "expanded",
                    "choices": [
                        {
                        "id": "Apply For New Loan",
                        "title": "Apply For New Loan",
                        "value": "Apply For New Loan"
                        },
                        {
                        "id": "Existing Customer",
                        "title": "Existing Customer",
                        "value": "Existing Customer"
                        },
                        {
                        "id": "Branch Locator",
                        "title": "Branch Locator",
                        "value": "Branch Locator"
                        },
                        {
                        "id": "Customer Support",
                        "title": "Customer Support",
                        "value": "Customer Support"
                        }
                    ]
                    }
                ],
                "actions": [
                {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
                }
            ]
            }
            return payload
            # reset_flow(wa)  # No mobile to preserve
            # return {"reply": "Main Menu", "flag": True}


    save_user(wa, {"step": "MAIN_MENU"})
    payload = {
        "type": "adaptiveCard",
        "body": [
            {
                "type": "TextBlock",
                "text": "How may i help you today?"
            },
            {
                "type": "Button",
                "id": "serviceType",
                "style": "expanded",
                "choices": [
                    {
                        "id": "Apply For New Loan",
                        "title": "Apply For New Loan",
                        "value": "Apply For New Loan"
                    },
                    {
                        "id": "Existing Customer",
                        "title": "Existing Customer",
                        "value": "Existing Customer"
                    },
                    {
                        "id": "Branch Locator",
                        "title": "Branch Locator",
                        "value": "Branch Locator"
                    },
                    {
                        "id": "Customer Support",
                        "title": "Customer Support",
                        "value": "Customer Support"
                    }
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Submit",
                "id": "crmSubmitForm",
                "value": "Submit",
                "actionId": "7777.70007"
            }
        ]
    }
    return payload

    # return {
    #     "reply": (
            # "⚠️ *Session Error*\n\n"
            # "Your current session is no longer active or has gone out of flow.\n"
            # "To continue, please restart the conversation.\n\n"
            # "👉 You can type *RESTART* or simply send *Hi*, *Hello*, or *Hey* to begin again.\n\n"
            # "We’re here to assist you. Thank you for your patience 😊"
    #     ),
    #     "flag": False
    # }

@app.post("/api/exist-number")
async def exist_number(req: Request):
    body = await req.json()
    number = body.get("mobile")

    if not number:
        return {"success": False, "message": "Mobile number is required"}

    number = str(number)

    # Remove country code 91
    if number.startswith("91") and len(number) == 12:
        number = number[2:]

    existing_user = users.find_one({"mobile": number})

    if existing_user:
        return {
            "exists": True,
            "data": {
                "wa": existing_user.get("wa"),
                "step": existing_user.get("step"),   # ✅ step yaha se aa raha hai
                "mobile": existing_user.get("mobile"),
                "name": existing_user.get("name")
            }
        }

    return {"exists": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9010)


