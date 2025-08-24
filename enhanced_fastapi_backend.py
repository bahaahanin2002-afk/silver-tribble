"""
Enhanced FastAPI app: Rate limiting + WhatsApp + OTP audit logging
----------------------------------------------------------------
New Features:
- Rate limiting (5 requests per minute per IP for OTP endpoints)
- WhatsApp channel option for OTP delivery
- OTP attempts logging for audit and anti-fraud
- Enhanced security and monitoring
"""

from __future__ import annotations
import base64
import hmac
import hashlib
import os
import time
from typing import Optional, Generator
from datetime import datetime, timedelta
from collections import defaultdict
import threading

import jwt
import requests
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, ForeignKey, func, select, Text, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from twilio.rest import Client as TwilioClient

# -----------------------------
# Rate Limiting (Simple in-memory)
# -----------------------------
class RateLimiter:
    def __init__(self, max_requests: int = 5, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str) -> bool:
        now = time.time()
        with self.lock:
            # Clean old requests
            self.requests[key] = [req_time for req_time in self.requests[key] 
                                if now - req_time < self.window_seconds]
            
            # Check if under limit
            if len(self.requests[key]) >= self.max_requests:
                return False
            
            # Add current request
            self.requests[key].append(now)
            return True

# Global rate limiter for OTP endpoints
otp_rate_limiter = RateLimiter(max_requests=5, window_minutes=1)

# -----------------------------
# Settings
# -----------------------------
class Settings(BaseSettings):
    SECRET_KEY: str = "change-this-jwt-secret"
    JWT_ALG: str = "HS256"
    JWT_TTL_SECONDS: int = 3600
    ENCRYPTION_KEY_BASE64: str
    DATABASE_URL: str = "sqlite:///./app.db"
    BINANCE_BASE: str = "https://api.binance.com"

    # Twilio Verify (real OTP)
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_VERIFY_SID: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()


# -----------------------------
# Database Models (Enhanced)
# -----------------------------
Base = declarative_base()
engine = create_engine(settings.DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(32), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, server_default=func.now(), onupdate=func.now())

    binance = relationship("BinanceCredentials", back_populates="user", uselist=False)
    otp_attempts = relationship("OTPAttempt", back_populates="user")

class OTPAttempt(Base):
    __tablename__ = "otp_attempts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable for failed attempts
    phone = Column(String(32), nullable=False)
    channel = Column(String(16), nullable=False)  # 'sms' or 'whatsapp'
    action = Column(String(16), nullable=False)  # 'send' or 'verify'
    success = Column(Boolean, nullable=False, default=False)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="otp_attempts")

class BinanceCredentials(Base):
    __tablename__ = "binance_credentials"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    api_key_enc = Column(Text, nullable=False)
    api_secret_enc = Column(Text, nullable=False)
    permissions = Column(String(64), default="trade-only")
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="binance")

Base.metadata.create_all(engine)


# -----------------------------
# Enhanced Request Models
# -----------------------------
class PhoneSendRequest(BaseModel):
    phone: str = Field(example="+9647XXXXXXXX")
    channel: str = Field(default="sms", example="sms")  # 'sms' or 'whatsapp'

class PhoneVerifyRequest(BaseModel):
    phone: str = Field(example="+9647XXXXXXXX")
    code: str = Field(example="123456")


# -----------------------------
# Helper Functions
# -----------------------------
def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def log_otp_attempt(
    db: Session, 
    phone: str, 
    channel: str, 
    action: str, 
    success: bool, 
    request: Request,
    user_id: Optional[int] = None,
    error_message: Optional[str] = None
):
    """Log OTP attempt for audit and fraud prevention"""
    attempt = OTPAttempt(
        user_id=user_id,
        phone=phone,
        channel=channel,
        action=action,
        success=success,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        error_message=error_message
    )
    db.add(attempt)
    db.commit()

def check_fraud_patterns(db: Session, phone: str, ip_address: str) -> bool:
    """Basic fraud detection - check for suspicious patterns"""
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    
    # Check failed attempts in last hour
    failed_attempts = db.execute(
        select(func.count(OTPAttempt.id))
        .where(OTPAttempt.phone == phone)
        .where(OTPAttempt.success == False)
        .where(OTPAttempt.created_at >= hour_ago)
    ).scalar()
    
    if failed_attempts >= 10:  # More than 10 failed attempts in 1 hour
        return True
    
    # Check IP-based attempts
    ip_attempts = db.execute(
        select(func.count(OTPAttempt.id))
        .where(OTPAttempt.ip_address == ip_address)
        .where(OTPAttempt.created_at >= hour_ago)
    ).scalar()
    
    if ip_attempts >= 20:  # More than 20 attempts from same IP in 1 hour
        return True
    
    return False


app = FastAPI(title="Enhanced Secure Binance Auth API", version="1.2.0")

@app.post("/auth/phone/send", status_code=204)
def auth_phone_send(req: PhoneSendRequest, request: Request, db: Session = Depends(get_db)):
    """Send OTP via Twilio Verify (SMS or WhatsApp) with rate limiting."""
    
    # Rate limiting check
    client_ip = get_client_ip(request)
    if not otp_rate_limiter.is_allowed(f"otp_send:{client_ip}"):
        log_otp_attempt(db, req.phone, req.channel, "send", False, request, 
                       error_message="Rate limit exceeded")
        raise HTTPException(status_code=429, detail="تم تجاوز الحد المسموح. حاول مرة أخرى لاحقاً")
    
    # Fraud detection
    if check_fraud_patterns(db, req.phone, client_ip):
        log_otp_attempt(db, req.phone, req.channel, "send", False, request,
                       error_message="Suspicious activity detected")
        raise HTTPException(status_code=429, detail="نشاط مشبوه. تم حظر الطلب مؤقتاً")
    
    # Validate channel
    if req.channel not in ["sms", "whatsapp"]:
        log_otp_attempt(db, req.phone, req.channel, "send", False, request,
                       error_message="Invalid channel")
        raise HTTPException(status_code=400, detail="قناة غير صحيحة. استخدم 'sms' أو 'whatsapp'")
    
    try:
        client = _twilio()
        client.verify.v2.services(settings.TWILIO_VERIFY_SID).verifications.create(
            to=req.phone,
            channel=req.channel,  # 'sms' or 'whatsapp'
        )
        
        # Log successful send
        log_otp_attempt(db, req.phone, req.channel, "send", True, request)
        return
        
    except Exception as e:
        # Log failed send
        log_otp_attempt(db, req.phone, req.channel, "send", False, request,
                       error_message=str(e))
        raise HTTPException(status_code=500, detail="فشل في إرسال رمز التحقق")

@app.post("/auth/phone/verify", response_model=TokenResponse)
def auth_phone_verify(req: PhoneVerifyRequest, request: Request, db: Session = Depends(get_db)):
    """Verify OTP with enhanced logging and fraud detection."""
    
    client_ip = get_client_ip(request)
    
    # Rate limiting check
    if not otp_rate_limiter.is_allowed(f"otp_verify:{client_ip}"):
        log_otp_attempt(db, req.phone, "unknown", "verify", False, request,
                       error_message="Rate limit exceeded")
        raise HTTPException(status_code=429, detail="تم تجاوز الحد المسموح. حاول مرة أخرى لاحقاً")
    
    try:
        client = _twilio()
        check = client.verify.v2.services(settings.TWILIO_VERIFY_SID).verification_checks.create(
            to=req.phone,
            code=req.code,
        )
        
        if check.status != "approved":
            # Log failed verification
            log_otp_attempt(db, req.phone, check.channel or "unknown", "verify", False, request,
                           error_message="Invalid OTP code")
            raise HTTPException(status_code=401, detail="رمز التحقق غير صحيح")

        # get-or-create user by phone
        user = db.execute(select(User).where(User.phone == req.phone)).scalar_one_or_none()
        if not user:
            user = User(phone=req.phone)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Log successful verification
        log_otp_attempt(db, req.phone, check.channel or "unknown", "verify", True, request, user.id)
        
        token = create_jwt(user.id)
        return TokenResponse(access_token=token)
        
    except HTTPException:
        raise
    except Exception as e:
        # Log unexpected error
        log_otp_attempt(db, req.phone, "unknown", "verify", False, request,
                       error_message=str(e))
        raise HTTPException(status_code=500, detail="خطأ في التحقق من الرمز")

@app.get("/admin/otp-attempts")
def get_otp_attempts(
    phone: Optional[str] = None,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get OTP attempt history for audit purposes (admin only)."""
    # Note: In production, add proper admin role checking
    
    query = select(OTPAttempt).order_by(OTPAttempt.created_at.desc()).limit(limit)
    
    if phone:
        query = query.where(OTPAttempt.phone == phone)
    
    attempts = db.execute(query).scalars().all()
    
    return [{
        "id": attempt.id,
        "phone": attempt.phone,
        "channel": attempt.channel,
        "action": attempt.action,
        "success": attempt.success,
        "ip_address": attempt.ip_address,
        "created_at": attempt.created_at.isoformat(),
        "error_message": attempt.error_message
    } for attempt in attempts]

# ... existing code for Binance integration ...
