# Wandora V8 — Real Email Authentication

V8 keeps the V7 Google + email/password authentication and removes development OTP display. Verification and password-reset codes are delivered by real email through SMTP.

## Authentication
- Continue with Google
- Email + password signup
- Real 6-digit email verification
- Email + password login
- Resend verification code
- Forgot password + real 6-digit reset code
- Password reset
- Google credentials are handled by Google; Wandora never receives a Google password
- Existing activities, people, messages, trips and profiles preserved

## 1. Google setup
Use a Google OAuth Web application client. Add these Authorized JavaScript origins:
- `http://127.0.0.1:8000`
- `http://localhost:8000`
- `https://wandora-1wme.onrender.com` (production)

The Google Web Client ID is public client configuration. Never put a Google client secret in the frontend.

## 2. Real email setup
V8 requires SMTP. Use a transactional email provider or an SMTP-enabled mailbox. For Gmail, use an App Password rather than your normal Google account password.

Set these environment variables:
```text
WANDORA_EMAIL_MODE=smtp
WANDORA_SMTP_HOST=smtp.example.com
WANDORA_SMTP_PORT=587
WANDORA_SMTP_USERNAME=...
WANDORA_SMTP_PASSWORD=...
WANDORA_FROM_EMAIL=no-reply@example.com
WANDORA_FROM_NAME=Wandora
```

Do not commit SMTP credentials to GitHub.

## 3. Local setup
```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Create a `.env` file in the project root using `.env.example` as the template, then fill in the Google client ID and SMTP settings. V8 loads `.env` automatically.

Start:
```powershell
python -m uvicorn app.main:app --reload --app-dir backend
```

Open `http://127.0.0.1:8000/`.

## 4. Email verification flow
```text
Create account
  -> Wandora sends 6-digit code to email
  -> User enters code
  -> Email verified
  -> Logged in
```
No OTP is shown in the browser or returned by the API.

## 5. Password reset
```text
Forgot password
  -> Enter email
  -> Wandora sends reset code
  -> Enter code + new password
  -> Password changed
```

## 6. Render
Set the following Render environment variables:
- `WANDORA_SECRET_KEY` (generate a strong value)
- `GOOGLE_CLIENT_ID`
- `WANDORA_EMAIL_MODE=smtp`
- `WANDORA_SMTP_HOST`
- `WANDORA_SMTP_PORT=587` (or 465 for SSL SMTP)
- `WANDORA_SMTP_USERNAME`
- `WANDORA_SMTP_PASSWORD`
- `WANDORA_FROM_EMAIL`
- `WANDORA_FROM_NAME=Wandora`

Also add `https://wandora-1wme.onrender.com` to the Google OAuth Authorized JavaScript origins.

## Security
- Passwords are PBKDF2-SHA256 hashed.
- Verification/reset codes are stored hashed and expire after 10 minutes.
- Google ID tokens are verified server-side.
- Google `sub` is used as the stable Google account identifier.
- Google passwords never pass through Wandora.
- SMTP credentials are server-side only.
