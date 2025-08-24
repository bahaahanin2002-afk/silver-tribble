# FastAPI Backend Setup Instructions

## Prerequisites
- Python 3.8+
- pip package manager

## Installation Steps

1. **Install required packages:**
\`\`\`bash
pip install fastapi uvicorn twilio cryptography python-jose[cryptography] passlib[bcrypt] python-multipart requests sqlalchemy psycopg2-binary
\`\`\`

2. **Set up environment variables:**
Create a `.env` file with:
\`\`\`
DATABASE_URL=postgresql://username:password@localhost/trading_db
JWT_SECRET=your-super-secret-jwt-key-here
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_VERIFY_SERVICE_SID=your-twilio-verify-service-sid
ENCRYPTION_KEY=your-32-byte-base64-encryption-key
\`\`\`

3. **Run the FastAPI server:**
\`\`\`bash
python scripts/secure_fastapi_backend.py
\`\`\`

The server will run on http://localhost:8000

## Next.js Integration
The Next.js API routes are already configured to proxy requests to the FastAPI backend.
Make sure both servers are running:
- FastAPI backend: http://localhost:8000
- Next.js frontend: http://localhost:3000
