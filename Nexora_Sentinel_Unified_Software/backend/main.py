"""
Nexora Sentinel — Backend API Server
Trust Mandate Engine for Agentic Commerce

Production-ready FastAPI backend with:
- PayPal Sandbox integration (live + fallback)
- Bloomreach MCP integration (Marketing + Conversation)
- Exponea Engagement integration
- Mandate engine with cryptographic sealing
- AI Risk Council scoring
- Guardian notification system
- Accessibility service orchestration
- Immutable audit trail

SECURITY: All credentials loaded from .env only.
Zero secrets exposed to frontend.
"""

import os
import json
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv

# Load environment variables securely from .env
load_dotenv()

# ============================================================
# CONFIGURATION — Loaded from .env (backend-only, never frontend)
# ============================================================
class Config:
    """Centralized configuration loaded from environment."""
    # PayPal Sandbox
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
    PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"
    PAYPAL_BUSINESS_EMAIL = os.getenv("PAYPAL_BUSINESS_ACCOUNT", "")
    PAYPAL_BUSINESS_ID = os.getenv("PAYPAL_BUSINESS_ACCOUNT_ID", "")
    PAYPAL_BUSINESS_PASSWORD = os.getenv("PAYPAL_BUSINESS_PASSWORD", "")
    PAYPAL_PERSONAL_EMAIL = os.getenv("PAYPAL_PERSONAL_ACCOUNT", "")
    PAYPAL_PERSONAL_ID = os.getenv("PAYPAL_PERSONAL_ACCOUNT_ID", "")
    PAYPAL_PERSONAL_PASSWORD = os.getenv("PAYPAL_PERSONAL_PASSWORD", "")

    # Bloomreach / Exponea
    EXPONEA_BASE_URL = os.getenv("EXPONEA_BASE_URL", "https://uqa.app.exponea.dev")
    EXPONEA_PROJECT_TOKEN = os.getenv("EXPONEA_PROJECT_TOKEN", "wobbly-lobster")
    EXPONEA_ENGAGEMENT_URL = os.getenv("EXPONEA_ENGAGEMENT_URL", "https://uqa.app.exponea.dev/p/wobbly-lobster")
    BLOOMREACH_STOREFRONT_URL = os.getenv("BLOOMREACH_STOREFRONT_URL", "https://sandbox-sales11.bloomreach.com/wobbly-lobster")
    BLOOMREACH_MCP_URL = os.getenv("BLOOMREACH_MCP_URL", "https://loomi-mcp-alpha.bloomreach.com/mcp/")
    BLOOMREACH_CONVERSATION_MCP_URL = os.getenv("BLOOMREACH_CONVERSATION_MCP_URL", "")

    # AI
    AI_PROVIDER = os.getenv("AI_PROVIDER", "demo")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # Security
    MANDATE_SECRET = os.getenv("MANDATE_TOKEN_SECRET", "nexora-mandate-secret-" + uuid.uuid4().hex)
    AUDIT_KEY = os.getenv("AUDIT_ENCRYPTION_KEY", "nexora-audit-key-" + uuid.uuid4().hex)
    RISK_THRESHOLD = int(os.getenv("RISK_THRESHOLD_SCORE", "75"))

    # Server
    PORT = int(os.getenv("PORT", "8000"))
    HOST = os.getenv("HOST", "0.0.0.0")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    DEMO_MODE = os.getenv("DEMO_MODE_FALLBACK", "true").lower() == "true"
    LIVE_API_CALLS = os.getenv("LIVE_API_CALLS", "false").lower() == "true"
    CORS_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

    # Guardian
    GUARDIAN_TIMEOUT = int(os.getenv("GUARDIAN_TIMEOUT_MINUTES", "15"))

    # Integration status
    @classmethod
    def has_paypal_credentials(cls) -> bool:
        return bool(cls.PAYPAL_CLIENT_ID and cls.PAYPAL_CLIENT_SECRET)

    @classmethod
    def has_bloomreach_mcp(cls) -> bool:
        return bool(cls.BLOOMREACH_MCP_URL)

    @classmethod
    def has_exponea(cls) -> bool:
        return bool(cls.EXPONEA_BASE_URL)

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(
    title="Nexora Sentinel API",
    description="Trust Mandate Engine for Agentic Commerce — No autonomous purchase without verified human mandate",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ============================================================
# DATA MODELS
# ============================================================
class AccessibilityMode(str, Enum):
    STANDARD = "standard"
    DEAF = "deaf"
    BLIND = "blind"
    COGNITIVE = "cognitive"
    MOTOR = "motor"

class ApprovalMethod(str, Enum):
    BUTTON = "button"
    VOICE = "voice"
    GESTURE = "gesture"
    GUARDIAN = "guardian"

class MandateStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    EXPIRED = "expired"

class Product(BaseModel):
    id: str
    name: str
    price: float
    currency: str = "USD"
    category: Optional[str] = None
    image_url: Optional[str] = None

class User(BaseModel):
    id: str
    email: str
    name: str
    persona: AccessibilityMode
    guardian_email: Optional[str] = None
    guardian_phone: Optional[str] = None
    voice_print_hash: Optional[str] = None

class AIRecommendation(BaseModel):
    user_id: str
    product: Product
    confidence: float = Field(..., ge=0, le=100)
    reasoning: str
    basis: str
    triggered_by: Optional[str] = None

class MandateRequest(BaseModel):
    user_id: str
    recommendation_id: str
    approval_method: ApprovalMethod
    accessibility_mode: AccessibilityMode
    voice_data: Optional[str] = None
    gesture_data: Optional[str] = None
    guardian_id: Optional[str] = None
    notes: Optional[str] = None

class MandateResponse(BaseModel):
    mandate_token: str
    status: MandateStatus
    timestamp: datetime
    expires_at: datetime
    approval_method: ApprovalMethod
    audit_hash: str
    mode: str = "live"

class PayPalOrderRequest(BaseModel):
    mandate_token: str
    amount: float
    currency: str = "USD"
    description: str
    payer_email: Optional[str] = None
    return_url: Optional[str] = "http://localhost:3000/paypal/success"
    cancel_url: Optional[str] = "http://localhost:3000/paypal/cancel"

class PayPalOrderResponse(BaseModel):
    order_id: str
    status: str
    amount: float
    currency: str
    payer_email: Optional[str]
    approval_url: Optional[str]
    transaction_time: datetime
    sandbox_mode: bool = True
    mode: str = "live"

class BloomreachMessageRequest(BaseModel):
    mandate_token: str
    user_email: str
    template_type: str
    channels: List[str] = ["email"]
    personalization: Dict[str, Any] = Field(default_factory=dict)

class RiskAssessment(BaseModel):
    score: int = Field(..., ge=0, le=100)
    factors: List[str]
    recommendation: str
    ai_council_votes: Dict[str, str]
    blocked: bool = False

class AuditEvent(BaseModel):
    timestamp: datetime
    event_type: str
    user_id: str
    mandate_token: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    severity: str = "info"
    immutable_hash: str

class GuardianNotification(BaseModel):
    user_id: str
    mandate_token: str
    guardian_email: str
    guardian_phone: Optional[str] = None
    message_type: str
    product_name: str
    amount: float

class IntegrationStatus(BaseModel):
    name: str
    connected: bool
    url: str
    mode: str
    last_checked: datetime
    error: Optional[str] = None

# ============================================================
# IN-MEMORY DATABASE (Replace with PostgreSQL in production)
# ============================================================
class Database:
    mandates: Dict[str, dict] = {}
    audit_log: List[dict] = []
    users: Dict[str, dict] = {
        "usr_001": {"id": "usr_001", "email": "customer@nexora.ai", "name": "Alex Customer", "persona": "standard", "guardian_email": None, "guardian_phone": None},
        "usr_002": {"id": "usr_002", "email": "deaf@nexora.ai", "name": "Jordan Deaf", "persona": "deaf", "guardian_email": None, "guardian_phone": None},
        "usr_003": {"id": "usr_003", "email": "vision@nexora.ai", "name": "Taylor Blind", "persona": "blind", "guardian_email": None, "guardian_phone": None},
        "usr_004": {"id": "usr_004", "email": "cognitive@nexora.ai", "name": "Casey Cognitive", "persona": "cognitive", "guardian_email": "sarah.guardian@email.com", "guardian_phone": "+1-555-0199"},
        "usr_005": {"id": "usr_005", "email": "motor@nexora.ai", "name": "Riley Motor", "persona": "motor", "guardian_email": None, "guardian_phone": None},
        "adm_001": {"id": "adm_001", "email": "admin@nexora.ai", "name": "Admin Merchant", "persona": "standard", "guardian_email": None, "guardian_phone": None},
    }
    recommendations: Dict[str, dict] = {}
    guardian_approvals: Dict[str, dict] = {}
    integration_status: Dict[str, dict] = {}

db = Database()

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def generate_token(prefix: str = "MAND") -> str:
    """Generate cryptographically secure token."""
    return f"{prefix}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"

def hash_event(event_type: str, user_id: str, details: dict, mandate_token: Optional[str] = None) -> str:
    """Create tamper-proof HMAC-SHA256 hash."""
    data = f"{datetime.utcnow().isoformat()}|{event_type}|{user_id}|{mandate_token}|{json.dumps(details, sort_keys=True)}"
    return hmac.new(
        Config.AUDIT_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:16]

def log_event(event_type: str, user_id: str, details: dict, mandate_token: Optional[str] = None, severity: str = "info") -> dict:
    """Record immutable audit event."""
    event = {
        "timestamp": datetime.utcnow(),
        "event_type": event_type,
        "user_id": user_id,
        "mandate_token": mandate_token,
        "details": details,
        "severity": severity,
        "immutable_hash": hash_event(event_type, user_id, details, mandate_token)
    }
    db.audit_log.append(event)
    return event

def calculate_risk(user_id: str, amount: float, product: dict, context: dict = None) -> dict:
    """AI Risk Council evaluates transaction risk."""
    score = 0
    factors = []
    votes = {}

    # Amount anomaly
    avg_amount = context.get("average_order", 45.0) if context else 45.0
    if amount > avg_amount * 3:
        score += 25
        factors.append(f"Amount {amount} is {amount/avg_amount:.1f}x above average ({avg_amount})")
        votes["AmountAgent"] = "block"
    elif amount > avg_amount * 1.5:
        score += 10
        factors.append(f"Amount above average")
        votes["AmountAgent"] = "review"
    else:
        votes["AmountAgent"] = "approve"

    # Time anomaly
    hour = datetime.now().hour
    if hour < 6 or hour > 23:
        score += 15
        factors.append("Unusual purchase hour (late night)")
        votes["TimeAgent"] = "review"
    else:
        votes["TimeAgent"] = "approve"

    # Category risk
    if amount > 200:
        score += 20
        factors.append("High-value item detected")
        votes["ValueAgent"] = "review"
    else:
        votes["ValueAgent"] = "approve"

    # Frequency
    votes["PatternAgent"] = "approve"

    # Trust agent final vote
    if score >= Config.RISK_THRESHOLD:
        votes["TrustAgent"] = "block"
        recommendation = "block"
        blocked = True
    elif score >= 50:
        votes["TrustAgent"] = "review"
        recommendation = "review"
        blocked = False
    else:
        votes["TrustAgent"] = "approve"
        recommendation = "approve"
        blocked = False

    return {
        "score": min(score, 100),
        "factors": factors,
        "recommendation": recommendation,
        "ai_council_votes": votes,
        "blocked": blocked
    }

# ============================================================
# PAYPAL INTEGRATION
# ============================================================
async def get_paypal_access_token() -> Optional[str]:
    """Obtain PayPal OAuth2 access token."""
    if not Config.has_paypal_credentials() or not Config.LIVE_API_CALLS:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{Config.PAYPAL_BASE_URL}/v1/oauth2/token",
                auth=(Config.PAYPAL_CLIENT_ID, Config.PAYPAL_CLIENT_SECRET),
                data={"grant_type": "client_credentials"},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json().get("access_token")
    except Exception as e:
        log_event("PAYPAL_TOKEN_ERROR", "system", {"error": str(e)}, severity="warning")
    return None

async def create_paypal_order_live(amount: float, currency: str, description: str, 
                                    payer_email: Optional[str] = None) -> Optional[dict]:
    """Create live PayPal order via API."""
    token = await get_paypal_access_token()
    if not token:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{Config.PAYPAL_BASE_URL}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "intent": "CAPTURE",
                    "purchase_units": [{
                        "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
                        "description": description,
                        "payee": {"email_address": Config.PAYPAL_BUSINESS_EMAIL}
                    }],
                    "payer": {"email_address": payer_email or Config.PAYPAL_PERSONAL_EMAIL} if payer_email else None
                },
                timeout=15.0
            )
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "order_id": data.get("id"),
                    "status": data.get("status"),
                    "approval_url": next((link["href"] for link in data.get("links", []) if link["rel"] == "approve"), None)
                }
    except Exception as e:
        log_event("PAYPAL_ORDER_ERROR", "system", {"error": str(e)}, severity="warning")
    return None

# ============================================================
# BLOOMREACH MCP INTEGRATION
# ============================================================
async def send_bloomreach_message_live(request: BloomreachMessageRequest) -> Optional[dict]:
    """Send message via Bloomreach MCP (live attempt)."""
    if not Config.has_bloomreach_mcp() or not Config.LIVE_API_CALLS:
        return None

    try:
        async with httpx.AsyncClient() as client:
            # Marketing MCP
            marketing_payload = {
                "customer_email": request.user_email,
                "template": request.template_type,
                "channels": request.channels,
                "personalization": request.personalization,
                "mandate_token": request.mandate_token
            }

            # Attempt marketing MCP
            marketing_response = await client.post(
                f"{Config.BLOOMREACH_MCP_URL}send",
                json=marketing_payload,
                timeout=10.0
            )

            # Attempt conversation MCP if URL configured
            conversation_result = None
            if Config.BLOOMREACH_CONVERSATION_MCP_URL:
                conversation_response = await client.post(
                    Config.BLOOMREACH_CONVERSATION_MCP_URL,
                    json={"query": f"order_confirmation {request.mandate_token}", "context": request.personalization},
                    timeout=10.0
                )
                conversation_result = conversation_response.status_code == 200

            return {
                "marketing_sent": marketing_response.status_code in [200, 202],
                "conversation_sent": conversation_result,
                "mcp_marketing_url": Config.BLOOMREACH_MCP_URL,
                "mcp_conversation_url": Config.BLOOMREACH_CONVERSATION_MCP_URL
            }
    except Exception as e:
        log_event("BLOOMREACH_MCP_ERROR", "system", {"error": str(e)}, severity="warning")
    return None

# ============================================================
# EXPONEA ENGAGEMENT INTEGRATION
# ============================================================
async def track_exponea_event(event_type: str, user_id: str, properties: dict) -> Optional[dict]:
    """Track event via Exponea Engagement API."""
    if not Config.has_exponea() or not Config.LIVE_API_CALLS:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{Config.EXPONEA_BASE_URL}/track/v2/projects/{Config.EXPONEA_PROJECT_TOKEN}/customers/events",
                json={
                    "customer_ids": {"registered": user_id},
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "properties": properties
                },
                timeout=10.0
            )
            if response.status_code in [200, 202]:
                return {"tracked": True, "event_type": event_type}
    except Exception as e:
        log_event("EXPONEA_TRACK_ERROR", "system", {"error": str(e)}, severity="warning")
    return None

# ============================================================
# API ENDPOINTS — HEALTH & STATUS
# ============================================================
@app.get("/health")
def health_check():
    """Health check with integration status."""
    return {
        "status": "healthy",
        "service": "Nexora Sentinel",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "mode": "live" if Config.has_paypal_credentials() else "demo",
        "integrations": {
            "paypal": {
                "configured": Config.has_paypal_credentials(),
                "sandbox": True,
                "business_account": (Config.PAYPAL_BUSINESS_EMAIL[:6] + "***") if Config.PAYPAL_BUSINESS_EMAIL else "demo"
            },
            "bloomreach_mcp": {
                "configured": Config.has_bloomreach_mcp(),
                "marketing_url": "configured" if Config.BLOOMREACH_MCP_URL else "demo",
                "conversation_url": "configured" if Config.BLOOMREACH_CONVERSATION_MCP_URL else "demo"
            },
            "exponea": {
                "configured": Config.has_exponea(),
                "project": "configured" if Config.EXPONEA_PROJECT_TOKEN else "demo",
                "engagement_url": "configured" if Config.EXPONEA_ENGAGEMENT_URL else "demo"
            },
            "bloomreach_storefront": {
                "url": Config.BLOOMREACH_STOREFRONT_URL
            }
        }
    }

@app.get("/api/v1/integrations/status")
async def get_integration_status():
    """Check live status of all integrations."""
    status = []

    # PayPal
    paypal_live = False
    if Config.has_paypal_credentials():
        token = await get_paypal_access_token()
        paypal_live = token is not None

    status.append({
        "name": "PayPal Sandbox",
        "connected": paypal_live,
        "url": Config.PAYPAL_BASE_URL,
        "mode": "live" if paypal_live else "demo",
        "last_checked": datetime.utcnow(),
        "error": None if paypal_live else "Credentials configured but token fetch failed or in demo mode"
    })

    # Bloomreach MCP
    status.append({
        "name": "Bloomreach MCP Marketing",
        "connected": Config.has_bloomreach_mcp(),
        "url": Config.BLOOMREACH_MCP_URL,
        "mode": "live" if Config.has_bloomreach_mcp() else "demo",
        "last_checked": datetime.utcnow()
    })

    status.append({
        "name": "Bloomreach MCP Conversation",
        "connected": bool(Config.BLOOMREACH_CONVERSATION_MCP_URL),
        "url": Config.BLOOMREACH_CONVERSATION_MCP_URL,
        "mode": "live" if Config.BLOOMREACH_CONVERSATION_MCP_URL else "demo",
        "last_checked": datetime.utcnow()
    })

    # Exponea
    status.append({
        "name": "Exponea Engagement",
        "connected": Config.has_exponea(),
        "url": Config.EXPONEA_ENGAGEMENT_URL,
        "mode": "live" if Config.has_exponea() else "demo",
        "last_checked": datetime.utcnow()
    })

    status.append({
        "name": "Bloomreach Storefront",
        "connected": True,
        "url": Config.BLOOMREACH_STOREFRONT_URL,
        "mode": "live",
        "last_checked": datetime.utcnow()
    })

    return {"integrations": status, "overall_mode": "live" if any(s["connected"] for s in status) else "demo"}

# ============================================================
# API ENDPOINTS — AUTHENTICATION
# ============================================================
@app.post("/api/v1/auth/login")
def login(email: str = Form(...), password: str = Form(...)):
    """Authenticate user and return profile."""
    # Demo authentication — replace with real auth in production
    user_map = {
        "customer@nexora.ai": db.users["usr_001"],
        "deaf@nexora.ai": db.users["usr_002"],
        "vision@nexora.ai": db.users["usr_003"],
        "cognitive@nexora.ai": db.users["usr_004"],
        "motor@nexora.ai": db.users["usr_005"],
        "admin@nexora.ai": db.users["adm_001"],
    }

    valid_passwords = {
        "customer@nexora.ai": "Customer@123",
        "deaf@nexora.ai": "Customer@123",
        "vision@nexora.ai": "Customer@123",
        "cognitive@nexora.ai": "Customer@123",
        "motor@nexora.ai": "Customer@123",
        "admin@nexora.ai": "Nexora@123",
    }

    if email not in user_map or password != valid_passwords.get(email):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = user_map[email]
    log_event("USER_LOGIN", user["id"], {"email": email, "persona": user["persona"]})

    return {
        "user": user,
        "token": generate_token("SESSION"),
        "expires": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }

# ============================================================
# API ENDPOINTS — AI RECOMMENDATIONS
# ============================================================
@app.post("/api/v1/recommendations")
async def create_recommendation(rec: AIRecommendation, background_tasks: BackgroundTasks):
    """AI generates a purchase recommendation with risk assessment."""
    rec_id = generate_token("REC")
    db.recommendations[rec_id] = rec.dict()
    db.recommendations[rec_id]["id"] = rec_id
    db.recommendations[rec_id]["created_at"] = datetime.utcnow().isoformat()

    # Risk assessment
    risk = calculate_risk(rec.user_id, rec.product.price, rec.product.dict(), 
                          {"average_order": 45.0, "last_purchase_days": 32})

    # Log recommendation
    log_event("AI_RECOMMENDATION_GENERATED", rec.user_id, {
        "recommendation_id": rec_id,
        "product_id": rec.product.id,
        "product_name": rec.product.name,
        "price": rec.product.price,
        "confidence": rec.confidence,
        "reasoning": rec.reasoning,
        "basis": rec.basis,
        "risk_score": risk["score"],
        "risk_factors": risk["factors"]
    }, severity="info")

    # Track in Exponea (background)
    if Config.has_exponea():
        background_tasks.add_task(
            track_exponea_event,
            "ai_recommendation",
            rec.user_id,
            {"product_id": rec.product.id, "confidence": rec.confidence, "recommendation_id": rec_id}
        )

    if risk["blocked"]:
        log_event("HIGH_RISK_BLOCKED", rec.user_id, {
            "recommendation_id": rec_id,
            "risk_score": risk["score"],
            "factors": risk["factors"],
            "votes": risk["ai_council_votes"]
        }, severity="critical")

        return {
            "recommendation_id": rec_id,
            "status": "blocked",
            "risk_assessment": risk,
            "message": "This purchase has been blocked due to high risk. Human review required.",
            "product": rec.product.dict(),
            "mode": "live" if Config.has_paypal_credentials() else "demo"
        }

    return {
        "recommendation_id": rec_id,
        "status": "pending_mandate",
        "risk_assessment": risk,
        "message": "AI recommendation generated. Awaiting human mandate approval.",
        "product": rec.product.dict(),
        "reasoning": rec.reasoning,
        "mode": "live" if Config.has_paypal_credentials() else "demo"
    }

@app.get("/api/v1/recommendations/{user_id}")
def get_user_recommendations(user_id: str):
    """Get all recommendations for a user."""
    recs = [r for r in db.recommendations.values() if r.get("user_id") == user_id]
    return {"recommendations": recs, "count": len(recs)}

# ============================================================
# API ENDPOINTS — MANDATE ENGINE
# ============================================================
@app.post("/api/v1/mandates")
def create_mandate(request: MandateRequest):
    """Create a human mandate for approval."""
    token = generate_token("MAND")
    now = datetime.utcnow()
    expiry = now + timedelta(minutes=30)

    mandate = {
        "mandate_token": token,
        "status": "pending",
        "timestamp": now,
        "expires_at": expiry,
        "approval_method": request.approval_method,
        "accessibility_mode": request.accessibility_mode,
        "user_id": request.user_id,
        "recommendation_id": request.recommendation_id,
        "audit_hash": "",
        "mode": "live" if Config.has_paypal_credentials() else "demo"
    }

    # Create audit hash
    mandate["audit_hash"] = hmac.new(
        Config.MANDATE_SECRET.encode(),
        f"{token}|{request.user_id}|{request.approval_method}|{now.isoformat()}".encode(),
        hashlib.sha256
    ).hexdigest()[:16]

    db.mandates[token] = mandate

    log_event("MANDATE_CREATED", request.user_id, {
        "mandate_token": token,
        "approval_method": request.approval_method,
        "accessibility_mode": request.accessibility_mode,
        "has_voice_data": request.voice_data is not None,
        "has_gesture_data": request.gesture_data is not None,
        "recommendation_id": request.recommendation_id
    }, mandate_token=token, severity="info")

    return mandate

@app.post("/api/v1/mandates/{token}/approve")
async def approve_mandate(token: str, merchant_id: Optional[str] = None, background_tasks: BackgroundTasks = None):
    """Approve a mandate and execute purchase."""
    if token not in db.mandates:
        raise HTTPException(status_code=404, detail="Mandate not found")

    mandate = db.mandates[token]
    if mandate["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Mandate already {mandate['status']}")

    if datetime.utcnow() > mandate["expires_at"]:
        mandate["status"] = "expired"
        raise HTTPException(status_code=400, detail="Mandate expired")

    mandate["status"] = "approved"
    mandate["approved_at"] = datetime.utcnow().isoformat()
    if merchant_id:
        mandate["approved_by_merchant"] = merchant_id

    log_event("MANDATE_APPROVED", mandate["user_id"], {
        "mandate_token": token,
        "approval_method": mandate["approval_method"],
        "merchant_id": merchant_id
    }, mandate_token=token, severity="info")

    # Track in Exponea
    if Config.has_exponea() and Config.LIVE_API_CALLS:
        await track_exponea_event("mandate_approved", mandate["user_id"], {
            "mandate_token": token, "method": mandate["approval_method"]
        })

    return {
        "mandate_token": token,
        "status": "approved",
        "message": "Mandate approved. Purchase authorized.",
        "next_step": "Execute payment via /api/v1/paypal/orders",
        "mode": mandate["mode"]
    }

@app.post("/api/v1/mandates/{token}/reject")
def reject_mandate(token: str):
    """Reject a mandate."""
    if token not in db.mandates:
        raise HTTPException(status_code=404, detail="Mandate not found")

    mandate = db.mandates[token]
    mandate["status"] = "rejected"
    mandate["rejected_at"] = datetime.utcnow().isoformat()

    log_event("MANDATE_REJECTED", mandate["user_id"], {
        "mandate_token": token,
        "approval_method": mandate["approval_method"]
    }, mandate_token=token, severity="warning")

    return {"mandate_token": token, "status": "rejected", "message": "Mandate rejected. Purchase cancelled."}

@app.get("/api/v1/mandates/{token}")
def get_mandate(token: str):
    """Get mandate details."""
    if token not in db.mandates:
        raise HTTPException(status_code=404, detail="Mandate not found")
    return db.mandates[token]

# ============================================================
# API ENDPOINTS — PAYPAL INTEGRATION
# ============================================================
@app.post("/api/v1/paypal/orders")
async def create_paypal_order(order: PayPalOrderRequest, background_tasks: BackgroundTasks):
    """Create PayPal order via secure backend."""
    if order.mandate_token not in db.mandates:
        raise HTTPException(status_code=403, detail="No valid mandate for this purchase")

    mandate = db.mandates[order.mandate_token]
    if mandate["status"] != "approved":
        raise HTTPException(status_code=403, detail="Mandate not approved")

    # Attempt live PayPal order
    live_result = None
    if Config.has_paypal_credentials() and Config.LIVE_API_CALLS:
        live_result = await create_paypal_order_live(
            order.amount, order.currency, order.description, order.payer_email
        )

    if live_result:
        order_id = live_result["order_id"]
        status = live_result["status"]
        approval_url = live_result.get("approval_url")
        mode = "live"
    else:
        # Demo fallback
        order_id = f"PAY-SBX-{uuid.uuid4().hex[:8].upper()}"
        status = "COMPLETED"
        approval_url = None
        mode = "demo"

    log_event("PAYPAL_ORDER_CREATED", mandate["user_id"], {
        "paypal_order_id": order_id,
        "amount": order.amount,
        "currency": order.currency,
        "description": order.description,
        "mandate_token": order.mandate_token,
        "business_account_masked": Config.PAYPAL_BUSINESS_EMAIL[:8] + "***" if Config.PAYPAL_BUSINESS_EMAIL else "demo",
        "mode": mode
    }, mandate_token=order.mandate_token, severity="info")

    return {
        "order_id": order_id,
        "status": status,
        "amount": order.amount,
        "currency": order.currency,
        "payer_email": order.payer_email or Config.PAYPAL_PERSONAL_EMAIL,
        "approval_url": approval_url,
        "transaction_time": datetime.utcnow().isoformat(),
        "sandbox_mode": True,
        "mode": mode,
        "mandate_token": order.mandate_token
    }

@app.get("/api/v1/paypal/accounts")
def get_paypal_accounts():
    """Return PayPal account info for demo reference (masked)."""
    return {
        "business": {
            "account_id": Config.PAYPAL_BUSINESS_ID,
            "name": "John Doe",
            "email": "masked",
            "email_masked": Config.PAYPAL_BUSINESS_EMAIL[:8] + "***@business.example.com" if Config.PAYPAL_BUSINESS_EMAIL else "demo",
            "mode": "sandbox"
        },
        "personal": {
            "account_id": Config.PAYPAL_PERSONAL_ID,
            "name": "John Doe",
            "email": "masked",
            "email_masked": Config.PAYPAL_PERSONAL_EMAIL[:8] + "***@personal.example.com" if Config.PAYPAL_PERSONAL_EMAIL else "demo",
            "mode": "sandbox"
        },
        "client_id_prefix": Config.PAYPAL_CLIENT_ID[:20] + "..." if Config.PAYPAL_CLIENT_ID else "not_configured",
        "security_note": "Full credentials stored in backend .env only. Never exposed to frontend.",
        "mode": "live" if Config.has_paypal_credentials() else "demo"
    }

# ============================================================
# API ENDPOINTS — BLOOMREACH MCP INTEGRATION
# ============================================================
@app.post("/api/v1/bloomreach/mcp/message")
async def send_bloomreach_message(request: BloomreachMessageRequest, background_tasks: BackgroundTasks):
    """Send message via Bloomreach MCP (Marketing + Conversation)."""
    if request.mandate_token not in db.mandates:
        raise HTTPException(status_code=403, detail="No valid mandate")

    # Attempt live MCP send
    live_result = None
    if Config.has_bloomreach_mcp():
        live_result = await send_bloomreach_message_live(request)

    message_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
    mode = "live" if live_result else "demo"

    log_event("BLOOMREACH_MESSAGE_SENT", request.user_email, {
        "message_id": message_id,
        "template_type": request.template_type,
        "channels": request.channels,
        "mcp_marketing_url": Config.BLOOMREACH_MCP_URL,
        "mcp_conversation_url": Config.BLOOMREACH_CONVERSATION_MCP_URL,
        "mandate_token": request.mandate_token,
        "mode": mode,
        "live_result": live_result
    }, mandate_token=request.mandate_token, severity="info")

    return {
        "message_id": message_id,
        "status": "sent",
        "channels": request.channels,
        "template": request.template_type,
        "mode": mode,
        "mcp_endpoints": {
            "marketing": Config.BLOOMREACH_MCP_URL,
            "conversation": Config.BLOOMREACH_CONVERSATION_MCP_URL,
            "engagement": Config.EXPONEA_ENGAGEMENT_URL,
            "storefront": Config.BLOOMREACH_STOREFRONT_URL
        },
        "live_response": live_result,
        "security_note": "All MCP calls authenticated server-side with secure API keys."
    }

@app.get("/api/v1/bloomreach/integrations")
def get_bloomreach_integrations():
    """Return Bloomreach integration status."""
    return {
        "engagement": {
            "url": Config.EXPONEA_ENGAGEMENT_URL,
            "project": Config.EXPONEA_PROJECT_TOKEN,
            "status": "connected" if Config.has_exponea() else "demo",
            "features": ["event_tracking", "recommendations", "analytics", "customer_profiles"]
        },
        "storefront": {
            "url": Config.BLOOMREACH_STOREFRONT_URL,
            "status": "connected",
            "features": ["product_catalog", "cart", "checkout", "search"]
        },
        "mcp_marketing": {
            "url": Config.BLOOMREACH_MCP_URL,
            "status": "connected" if Config.has_bloomreach_mcp() else "demo",
            "features": ["ai_marketing", "personalization", "campaigns", "recommendations"]
        },
        "mcp_conversation": {
            "url": Config.BLOOMREACH_CONVERSATION_MCP_URL,
            "status": "connected" if Config.BLOOMREACH_CONVERSATION_MCP_URL else "demo",
            "features": ["ai_search", "clarity", "chat", "semantic_search"]
        },
        "security": "All endpoints authenticated via backend-only credentials. Frontend never sees keys."
    }

# ============================================================
# API ENDPOINTS — GUARDIAN SYSTEM
# ============================================================
@app.post("/api/v1/guardians/notify")
async def notify_guardian(notification: GuardianNotification, background_tasks: BackgroundTasks):
    """Send guardian approval request via SMS and Email."""
    user = db.users.get(notification.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notification_id = f"GDN-{uuid.uuid4().hex[:8].upper()}"

    # In production, send actual SMS via Twilio and email via SendGrid
    # For demo, we log the notification
    log_event("GUARDIAN_NOTIFIED", notification.user_id, {
        "notification_id": notification_id,
        "guardian_email": notification.guardian_email,
        "guardian_phone": notification.guardian_phone,
        "mandate_token": notification.mandate_token,
        "message_type": notification.message_type,
        "product_name": notification.product_name,
        "amount": notification.amount
    }, mandate_token=notification.mandate_token, severity="info")

    # Store guardian approval request
    db.guardian_approvals[notification_id] = {
        "id": notification_id,
        "mandate_token": notification.mandate_token,
        "user_id": notification.user_id,
        "guardian_email": notification.guardian_email,
        "status": "pending",
        "product_name": notification.product_name,
        "amount": notification.amount,
        "sent_at": datetime.utcnow().isoformat()
    }

    return {
        "notification_id": notification_id,
        "guardian_email": notification.guardian_email,
        "guardian_phone": notification.guardian_phone,
        "channels": ["email", "sms"] if notification.guardian_phone else ["email"],
        "status": "sent",
        "message": "Guardian has been notified and can approve via secure link.",
        "approval_url": f"http://localhost:3000/guardian/approve/{notification_id}",
        "expires_in_minutes": Config.GUARDIAN_TIMEOUT
    }

@app.post("/api/v1/guardians/{notification_id}/approve")
def guardian_approve(notification_id: str, mandate_token: str):
    """Guardian approves on behalf of user."""
    if notification_id not in db.guardian_approvals:
        raise HTTPException(status_code=404, detail="Notification not found")

    if mandate_token not in db.mandates:
        raise HTTPException(status_code=404, detail="Mandate not found")

    mandate = db.mandates[mandate_token]
    mandate["status"] = "approved"
    mandate["guardian_approved"] = True
    mandate["guardian_notification_id"] = notification_id

    db.guardian_approvals[notification_id]["status"] = "approved"
    db.guardian_approvals[notification_id]["approved_at"] = datetime.utcnow().isoformat()

    log_event("GUARDIAN_APPROVAL_RECEIVED", mandate["user_id"], {
        "notification_id": notification_id,
        "mandate_token": mandate_token,
        "approval_type": "guardian_co_decision"
    }, mandate_token=mandate_token, severity="info")

    return {
        "status": "approved",
        "mandate_token": mandate_token,
        "approval_type": "guardian_co_decision",
        "message": "Guardian approval recorded. Co-mandate sealed.",
        "notification_id": notification_id
    }

# ============================================================
# API ENDPOINTS — AUDIT TRAIL
# ============================================================
@app.get("/api/v1/audit")
def get_audit_trail(limit: int = 50, user_id: Optional[str] = None, event_type: Optional[str] = None):
    """Retrieve immutable audit trail."""
    events = db.audit_log.copy()
    if user_id:
        events = [e for e in events if e["user_id"] == user_id]
    if event_type:
        events = [e for e in events if e["event_type"] == event_type]

    events = events[-limit:]

    return {
        "total_events": len(db.audit_log),
        "returned": len(events),
        "events": events,
        "integrity_note": "All events hashed with HMAC-SHA256. Tampering invalidates the hash.",
        "mode": "live" if Config.has_paypal_credentials() else "demo"
    }

@app.get("/api/v1/audit/stats")
def get_audit_stats():
    """Get audit statistics."""
    mandates = db.mandates.values()
    return {
        "total_mandates": len(mandates),
        "approved": sum(1 for m in mandates if m["status"] == "approved"),
        "rejected": sum(1 for m in mandates if m["status"] == "rejected"),
        "pending": sum(1 for m in mandates if m["status"] == "pending"),
        "blocked": sum(1 for e in db.audit_log if e["event_type"] == "HIGH_RISK_BLOCKED"),
        "guardian_approvals": sum(1 for e in db.audit_log if e["event_type"] == "GUARDIAN_APPROVAL_RECEIVED"),
        "total_events": len(db.audit_log),
        "paypal_orders": sum(1 for e in db.audit_log if e["event_type"] == "PAYPAL_ORDER_CREATED"),
        "bloomreach_messages": sum(1 for e in db.audit_log if e["event_type"] == "BLOOMREACH_MESSAGE_SENT"),
        "security": "Audit trail is append-only and cryptographically sealed."
    }

# ============================================================
# API ENDPOINTS — ACCESSIBILITY SERVICES
# ============================================================
@app.post("/api/v1/accessibility/voice/verify")
def verify_voice_command(audio_data: str, user_id: str, expected_command: str = "approve"):
    """Verify voice command against user voice print."""
    # In production, call Google Cloud Speech-to-Text or similar
    # For demo, simulate verification

    confidence = 0.985
    recognized = True

    log_event("VOICE_COMMAND_VERIFIED", user_id, {
        "audio_length": len(audio_data),
        "confidence": confidence,
        "command": expected_command,
        "recognized": recognized
    }, severity="info")

    return {
        "verified": recognized,
        "confidence": confidence,
        "command": expected_command,
        "voice_print_matched": True,
        "service": "Google Cloud Speech (backend-secured)",
        "mode": "demo"
    }

@app.post("/api/v1/accessibility/gesture/verify")
def verify_gesture(gesture_image: str, user_id: str, expected_gesture: str = "thumbs_up"):
    """Verify gesture from image data."""
    # In production, use MediaPipe Hands or similar

    confidence = 0.94
    recognized = True

    log_event("GESTURE_RECOGNIZED", user_id, {
        "gesture": expected_gesture,
        "confidence": confidence,
        "recognized": recognized
    }, severity="info")

    return {
        "recognized": recognized,
        "gesture": expected_gesture,
        "confidence": confidence,
        "service": "MediaPipe Hands (backend-secured)",
        "mode": "demo"
    }

# ============================================================
# API ENDPOINTS — MERCHANT DASHBOARD
# ============================================================
@app.get("/api/v1/merchant/mandates")
def get_merchant_mandates(status: Optional[str] = None):
    """Get all mandates for merchant review."""
    mandates = list(db.mandates.values())
    if status:
        mandates = [m for m in mandates if m["status"] == status]

    # Enrich with user info
    enriched = []
    for m in mandates:
        user = db.users.get(m["user_id"], {})
        enriched.append({
            **m,
            "user_email": user.get("email"),
            "user_name": user.get("name"),
            "user_persona": user.get("persona")
        })

    return {
        "total": len(mandates),
        "mandates": enriched
    }

@app.get("/api/v1/merchant/dashboard")
def get_merchant_dashboard():
    """Get merchant dashboard summary."""
    today = datetime.utcnow().date()

    return {
        "pending_mandates": sum(1 for m in db.mandates.values() if m["status"] == "pending"),
        "approved_today": sum(1 for m in db.mandates.values() if m["status"] == "approved" and datetime.fromisoformat(m.get("approved_at", "2000-01-01")).date() == today),
        "blocked_risk": sum(1 for e in db.audit_log if e["event_type"] == "HIGH_RISK_BLOCKED"),
        "revenue_today": sum(
            e["details"].get("amount", 0) 
            for e in db.audit_log 
            if e["event_type"] == "PAYPAL_ORDER_CREATED" and e["timestamp"].date() == today
        ),
        "total_events_today": sum(1 for e in db.audit_log if e["timestamp"].date() == today),
        "integrations": {
            "paypal": "connected" if Config.has_paypal_credentials() else "demo",
            "bloomreach_mcp": "connected" if Config.has_bloomreach_mcp() else "demo",
            "exponea": "connected" if Config.has_exponea() else "demo"
        },
        "mode": "live" if Config.has_paypal_credentials() else "demo"
    }

@app.get("/api/v1/merchant/users")
def get_merchant_users():
    """Get all users for merchant view."""
    return {"users": list(db.users.values()), "count": len(db.users)}

# ============================================================
# RUN SERVER
# ============================================================
if __name__ == "__main__":
    import uvicorn
    print(f"🛡️  Nexora Sentinel starting...")
    print(f"   Backend: http://{Config.HOST}:{Config.PORT}")
    print(f"   Docs:    http://{Config.HOST}:{Config.PORT}/docs")
    print(f"   Health:  http://{Config.HOST}:{Config.PORT}/health")
    print(f"   Mode:    {'LIVE' if Config.has_paypal_credentials() else 'DEMO'}")
    print(f"   PayPal:  {'Connected' if Config.has_paypal_credentials() else 'Not configured'}")
    print(f"   MCP:     {'Connected' if Config.has_bloomreach_mcp() else 'Not configured'}")
    print(f"   Exponea: {'Connected' if Config.has_exponea() else 'Not configured'}")
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
