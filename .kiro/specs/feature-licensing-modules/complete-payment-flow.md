# Complete Payment to Activation Flow

## Overview

This document shows the complete process from when a customer pays to when features are activated in their self-hosted installation.

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER'S JOURNEY                                   │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: Customer Uses App (Trial)
┌──────────────────────────┐
│  Customer's Server       │
│  (Self-Hosted)           │
│                          │
│  ┌────────────────────┐  │
│  │ Invoice App        │  │
│  │ - All features ON  │  │
│  │ - 30-day trial     │  │
│  │ - Banner: "Trial"  │  │
│  └────────────────────┘  │
└──────────────────────────┘
         │
         │ Customer loves AI Invoice feature
         ↓

Step 2: Customer Clicks "Purchase"
┌──────────────────────────┐
│  Customer's Browser      │
│                          │
│  ┌────────────────────┐  │
│  │ [Purchase AI       │  │
│  │  Invoice - $29/mo] │  │
│  │                    │  │
│  │ Click! ────────────┼──┼──→ Opens: yourcompany.com/pricing
│  └────────────────────┘  │
└──────────────────────────┘


Step 3: Customer Pays via Stripe
┌──────────────────────────────────────────────────────────────┐
│  Your Website (yourcompany.com)                              │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Pricing Page                                        │    │
│  │                                                      │    │
│  │ AI Invoice Processing - $29/month                   │    │
│  │ [Select Features: ☑ AI Invoice ☐ AI Expense]       │    │
│  │                                                      │    │
│  │ Email: customer@acme.com                            │    │
│  │                                                      │    │
│  │ [Pay with Stripe] ←─── Customer clicks             │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
         │
         │ Redirects to Stripe Checkout
         ↓
┌──────────────────────────┐
│  Stripe Checkout         │
│                          │
│  💳 Enter card details   │
│  [Pay $29.00]            │
│                          │
│  Customer completes ─────┼──→ Payment successful!
└──────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         YOUR BACKEND (Automated)                             │
└─────────────────────────────────────────────────────────────────────────────┘

Step 4: Stripe Webhook Triggers
┌──────────────────────────────────────────────────────────────┐
│  Stripe                                                       │
│                                                               │
│  Payment successful! ─────────────────────────────────────►  │
│                                                               │
│  Sends webhook to:                                           │
│  POST https://yourcompany.com/webhook/stripe                 │
│  {                                                            │
│    "type": "checkout.session.completed",                     │
│    "data": {                                                 │
│      "customer_email": "customer@acme.com",                  │
│      "customer_name": "Acme Corp",                           │
│      "amount": 2900,  // $29.00                              │
│      "metadata": {                                           │
│        "features": "ai_invoice",                             │
│        "duration": "monthly"                                 │
│      }                                                        │
│    }                                                          │
│  }                                                            │
└──────────────────────────────────────────────────────────────┘
         │
         ↓

Step 5: Your Server Generates License
┌──────────────────────────────────────────────────────────────┐
│  Your License Server                                          │
│                                                               │
│  1. Receive webhook                                          │
│  2. Extract customer info                                    │
│  3. Generate license key:                                    │
│                                                               │
│     license_key = jwt.encode({                               │
│       'customer_email': 'customer@acme.com',                 │
│       'customer_name': 'Acme Corp',                          │
│       'features': ['ai_invoice'],                            │
│       'expires_at': '2025-12-16',  // 1 year                 │
│       'max_users': 10                                        │
│     }, private_key, algorithm='RS256')                       │
│                                                               │
│  4. Save to database                                         │
│  5. Send email to customer                                   │
└──────────────────────────────────────────────────────────────┘
         │
         ↓

Step 6: Customer Receives Email
┌──────────────────────────────────────────────────────────────┐
│  Customer's Email Inbox                                       │
│                                                               │
│  From: licenses@yourcompany.com                              │
│  Subject: Your Invoice App License Key                       │
│                                                               │
│  Hi Acme Corp,                                               │
│                                                               │
│  Thank you for purchasing Invoice App!                       │
│                                                               │
│  Your license key is:                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZb3... │ │
│  │ (long JWT string)                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  Features: AI Invoice Processing                             │
│  Expires: 2025-12-16                                         │
│                                                               │
│  To activate:                                                │
│  1. Open Invoice App                                         │
│  2. Go to Settings → License                                 │
│  3. Paste your license key                                   │
│  4. Click "Activate"                                         │
└──────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                    CUSTOMER ACTIVATES LICENSE                                │
└─────────────────────────────────────────────────────────────────────────────┘

Step 7: Customer Enters License Key
┌──────────────────────────────────────────────────────────────┐
│  Customer's Self-Hosted App                                   │
│                                                               │
│  Settings → License Management                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ License Key:                                           │ │
│  │ ┌────────────────────────────────────────────────────┐ │ │
│  │ │ eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOi... │ │ │
│  │ └────────────────────────────────────────────────────┘ │ │
│  │                                                         │ │
│  │ [Activate License] ←─── Customer clicks                │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
         │
         ↓

Step 8: License Verification (Local - No Internet Required!)
┌──────────────────────────────────────────────────────────────┐
│  Customer's Server (Self-Hosted)                             │
│                                                               │
│  LicenseService.verify_license(license_key)                  │
│                                                               │
│  1. Decode JWT token                                         │
│  2. Verify signature using PUBLIC KEY (embedded in app)      │
│     ✓ Signature valid (proves it came from you)             │
│                                                               │
│  3. Check expiration                                         │
│     ✓ Expires: 2025-12-16 (still valid)                     │
│                                                               │
│  4. Extract features                                         │
│     ✓ Features: ['ai_invoice']                              │
│                                                               │
│  5. Save to local database                                   │
│     ✓ License activated!                                     │
│                                                               │
│  Result: {                                                    │
│    'valid': True,                                            │
│    'features': ['ai_invoice'],                               │
│    'expires_at': '2025-12-16',                               │
│    'customer_name': 'Acme Corp'                              │
│  }                                                            │
└──────────────────────────────────────────────────────────────┘
         │
         ↓

Step 9: Features Unlocked!
┌──────────────────────────────────────────────────────────────┐
│  Customer's App                                               │
│                                                               │
│  ✅ License Activated Successfully!                          │
│                                                               │
│  Enabled Features:                                           │
│  ✓ AI Invoice Processing                                     │
│                                                               │
│  Expires: 2025-12-16 (365 days remaining)                    │
│                                                               │
│  [Continue Using App]                                        │
└──────────────────────────────────────────────────────────────┘
         │
         ↓

Step 10: Customer Uses Premium Feature
┌──────────────────────────────────────────────────────────────┐
│  Customer's App                                               │
│                                                               │
│  Invoices Page                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Upload Invoice: invoice.pdf                            │ │
│  │                                                         │ │
│  │ [🤖 AI Process Invoice] ←─── Now visible & clickable!  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  When clicked:                                               │
│  1. Check: has_feature('ai_invoice') → True ✓               │
│  2. Execute AI processing                                    │
│  3. Extract invoice data automatically                       │
│  4. Success!                                                 │
└──────────────────────────────────────────────────────────────┘
```


## Detailed Step-by-Step Breakdown

### Phase 1: Customer Side (Before Payment)

**What Happens:**
1. Customer installs your app on their server
2. App automatically starts 30-day trial
3. All features are enabled
4. Customer tries AI Invoice feature and loves it
5. Customer clicks "Purchase" button in the app

**Code in Customer's App:**
```typescript
// ui/src/pages/Settings.tsx
<Button onClick={() => {
  window.open('https://yourcompany.com/pricing?email=' + userEmail, '_blank')
}}>
  Purchase AI Invoice Processing
</Button>
```

---

### Phase 2: Payment (Your Website)

**What Happens:**
1. Customer lands on your pricing page
2. Selects features they want
3. Enters email (pre-filled from app)
4. Clicks "Pay with Stripe"
5. Stripe checkout opens
6. Customer enters card details
7. Payment processes
8. Stripe shows success message

**Code on Your Website:**
```javascript
// yourcompany.com/pricing
<script src="https://js.stripe.com/v3/"></script>
<script>
const stripe = Stripe('pk_live_...');

async function purchaseLicense() {
  const response = await fetch('/api/create-checkout', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      email: 'customer@acme.com',
      features: ['ai_invoice'],
      plan: 'monthly'
    })
  });
  
  const session = await response.json();
  
  // Redirect to Stripe Checkout
  await stripe.redirectToCheckout({
    sessionId: session.id
  });
}
</script>
```

---

### Phase 3: Webhook Processing (Your Server - Automated)

**What Happens:**
1. Stripe sends webhook to your server
2. Your server receives payment confirmation
3. Extracts customer info and purchased features
4. Generates signed license key (JWT)
5. Saves license to your database
6. Sends email to customer with license key

**Code on Your Server:**
```python
# yourcompany.com/webhook/stripe
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    event = stripe.Webhook.construct_event(
        request.data,
        request.headers['Stripe-Signature'],
        webhook_secret
    )
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Generate license
        license_key = generator.generate_license(
            customer_email=session['customer_email'],
            customer_name=session['customer_details']['name'],
            features=['ai_invoice'],
            duration_days=30  # Monthly
        )
        
        # Save to database
        save_license(customer_email, license_key)
        
        # Email customer
        send_email(
            to=customer_email,
            subject='Your Invoice App License',
            body=f'Your license key: {license_key}'
        )
    
    return {'success': True}
```

**Time:** This happens within seconds of payment

---

### Phase 4: Customer Receives Email

**What Happens:**
1. Customer receives email (usually within 1 minute)
2. Email contains license key (long JWT string)
3. Email has instructions for activation
4. Customer copies license key

**Email Content:**
```
Subject: Your Invoice App License Key

Hi Acme Corp,

Thank you for purchasing Invoice App!

Your license key is:
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZb3VyQ29tcGFueSIsInN1YiI6ImN1c3RvbWVyQGFjbWUuY29tIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjE3MzE1MzYwMDAsImp0aSI6IjEyMzQ1Njc4LTkwYWItY2RlZi0xMjM0LTU2Nzg5MGFiY2RlZiIsImN1c3RvbWVyX25hbWUiOiJBY21lIENvcnAiLCJjdXN0b21lcl9lbWFpbCI6ImN1c3RvbWVyQGFjbWUuY29tIiwiZmVhdHVyZXMiOlsiYWlfaW52b2ljZSJdLCJtYXhfdXNlcnMiOjEwLCJsaWNlbnNlX3R5cGUiOiJjb21tZXJjaWFsIn0.signature...

Features: AI Invoice Processing
Expires: 2025-12-16

To activate:
1. Open Invoice App
2. Go to Settings → License
3. Paste your license key
4. Click "Activate"

Need help? Reply to this email.
```

---

### Phase 5: License Activation (Customer's Server)

**What Happens:**
1. Customer opens their self-hosted app
2. Goes to Settings → License Management
3. Pastes license key
4. Clicks "Activate"
5. App verifies license locally (no internet needed!)
6. License is saved to local database
7. Features are immediately enabled

**Code in Customer's App:**
```python
# api/routers/license.py (in customer's installation)
@router.post("/license/activate")
async def activate_license(
    request: LicenseActivateRequest,
    db: Session = Depends(get_db)
):
    license_service = LicenseService(db)
    
    # Verify license (happens locally!)
    result = license_service.verify_license(request.license_key)
    
    if not result['valid']:
        raise HTTPException(403, detail=result['error'])
    
    # Save to database
    license_service.activate_license(request.license_key)
    
    return {
        'success': True,
        'features': result['features'],
        'expires_at': result['expires_at']
    }
```

**Verification Process (Local - No Internet!):**
```python
# This happens on customer's server
def verify_license(license_key):
    # 1. Decode JWT
    payload = jwt.decode(
        license_key,
        PUBLIC_KEY,  # Embedded in app
        algorithms=['RS256']
    )
    
    # 2. Check signature (proves it came from you)
    # JWT library does this automatically
    # If signature invalid, jwt.decode() raises exception
    
    # 3. Check expiration
    if payload['exp'] < time.time():
        return {'valid': False, 'error': 'EXPIRED'}
    
    # 4. Extract features
    return {
        'valid': True,
        'features': payload['features'],
        'expires_at': datetime.fromtimestamp(payload['exp'])
    }
```

---

### Phase 6: Feature Usage (Customer's Server)

**What Happens:**
1. Customer navigates to Invoices page
2. AI Process button is now visible
3. Customer clicks button
4. App checks license: `has_feature('ai_invoice')` → True
5. AI processing executes
6. Invoice data extracted automatically

**Code in Customer's App:**
```python
# api/routers/invoices.py (in customer's installation)
from utils.feature_gate import require_feature

@router.post("/invoices/{id}/ai-process")
@require_feature("ai_invoice")  # ← Checks license
async def ai_process_invoice(id: int):
    # This only runs if license has 'ai_invoice' feature
    result = await ai_service.process_invoice(id)
    return result
```

**Feature Check:**
```python
# utils/feature_gate.py
def require_feature(feature_id):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            license_service = LicenseService(db)
            
            # Check if feature is enabled
            if not license_service.has_feature(feature_id):
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=f"Feature '{feature_id}' requires a license"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```


## Key Points About the Process

### 1. **No Payment Verification in Customer's App**

The customer's app does NOT verify payment. It only verifies the license key's cryptographic signature.

```
❌ Customer's app does NOT:
   - Contact your payment server
   - Check if payment was made
   - Validate credit card
   - Check Stripe

✅ Customer's app ONLY:
   - Verifies JWT signature (proves license came from you)
   - Checks expiration date
   - Extracts features list
```

### 2. **License Key IS the Proof of Payment**

The license key itself is proof that payment was made because:

1. **Only you can create valid license keys** (you have the private key)
2. **Customer can't forge license keys** (they only have public key)
3. **Signature proves authenticity** (cryptographically secure)

```
License Key = Cryptographically Signed Receipt
├── Signed by: Your private key (only you have this)
├── Verified by: Public key (embedded in app)
└── Contains: Features, expiration, customer info
```

### 3. **Offline-First Design**

Customer's app works completely offline after license activation:

```
Internet Required:
├── Payment (Stripe checkout) ✓
├── Receiving email ✓
└── Initial license activation (optional online check)

Internet NOT Required:
├── License verification ✗
├── Feature checks ✗
├── Using licensed features ✗
└── App continues working ✗
```

### 4. **Security Through Cryptography**

```
Your Private Key (SECRET)
    ↓
    Signs license key
    ↓
License Key (JWT)
    ↓
    Sent to customer
    ↓
Customer's App
    ↓
    Verifies with Public Key (EMBEDDED)
    ↓
    ✓ Valid = Features enabled
    ✗ Invalid = Features disabled
```

**Why This Works:**
- Private key can SIGN (create licenses)
- Public key can only VERIFY (check signatures)
- Customer can't create valid licenses without private key
- Even if they see the public key, they can't forge licenses


## Timeline Summary

```
Time: 0 seconds
├── Customer clicks "Purchase" in app
│
Time: +5 seconds
├── Customer lands on your pricing page
│
Time: +30 seconds
├── Customer enters payment info in Stripe
│
Time: +35 seconds
├── Payment processes
├── Stripe sends webhook to your server
│
Time: +36 seconds
├── Your server generates license key
├── Your server saves to database
├── Your server sends email
│
Time: +40 seconds
├── Customer receives email with license key
│
Time: +60 seconds
├── Customer copies license key
├── Customer pastes in app
├── Customer clicks "Activate"
│
Time: +61 seconds
├── App verifies license (locally, instant)
├── License saved to local database
├── Features enabled
│
Time: +62 seconds
├── Customer uses AI Invoice feature
└── ✅ Complete!
```

**Total Time: ~1 minute from payment to using feature**

## Comparison: Payment Verification vs License Verification

### Traditional SaaS (Cloud-Based)
```
Customer uses feature
    ↓
App checks: "Did customer pay?" (API call to payment server)
    ↓
Payment server checks Stripe subscription
    ↓
Returns: Yes/No
    ↓
Feature enabled/disabled
```

**Problems:**
- Requires internet for every check
- Slow (API calls)
- Single point of failure (your server down = app broken)
- Customer has no control

### Your Approach (Self-Hosted with License Keys)
```
Customer uses feature
    ↓
App checks: "Is license key valid?" (local verification)
    ↓
Verify JWT signature with public key (instant, offline)
    ↓
Check expiration date (instant, offline)
    ↓
Feature enabled/disabled
```

**Benefits:**
- Works offline
- Instant (no API calls)
- No single point of failure
- Customer has full control
- Privacy-friendly (no tracking)

## What Customer Sees

### Before Payment (Trial)
```
┌─────────────────────────────────────┐
│ Invoice App                         │
├─────────────────────────────────────┤
│ ⚠️ Trial: 15 days remaining         │
│                                     │
│ Invoices                            │
│ ┌─────────────────────────────────┐ │
│ │ invoice.pdf                     │ │
│ │ [🤖 AI Process] ← Works!        │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Purchase License]                  │
└─────────────────────────────────────┘
```

### After Trial Expires (No License)
```
┌─────────────────────────────────────┐
│ Invoice App                         │
├─────────────────────────────────────┤
│ ❌ Trial expired                    │
│                                     │
│ Invoices                            │
│ ┌─────────────────────────────────┐ │
│ │ invoice.pdf                     │ │
│ │ [🤖 AI Process] ← Disabled      │ │
│ │                                 │ │
│ │ 🔒 This feature requires a      │ │
│ │    license. [Purchase]          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### After License Activated
```
┌─────────────────────────────────────┐
│ Invoice App                         │
├─────────────────────────────────────┤
│ ✅ Licensed to: Acme Corp           │
│ Expires: 2025-12-16 (365 days)      │
│                                     │
│ Invoices                            │
│ ┌─────────────────────────────────┐ │
│ │ invoice.pdf                     │ │
│ │ [🤖 AI Process] ← Works!        │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## FAQ

### Q: Does the customer's app contact your server to verify payment?
**A: No.** The app only verifies the license key's cryptographic signature locally. No internet required.

### Q: How do you know the customer actually paid?
**A: The license key proves it.** Only you can create valid license keys (you have the private key). If the signature is valid, payment was made.

### Q: Can customers bypass this by modifying the code?
**A: Technically yes, but:**
- It's illegal (license agreement)
- Most businesses won't risk it
- They lose support and updates
- Cryptographic signatures make it harder than just paying

### Q: What if customer's license expires?
**A: Features automatically disable.** The app checks expiration date on every feature use. When expired, features stop working until they renew.

### Q: Can customers use the app offline?
**A: Yes!** Once license is activated, everything works offline. License verification is local.

### Q: What if your server goes down?
**A: Customer's app keeps working.** Their app doesn't depend on your server for license verification.

### Q: How do you revoke a license?
**A: You can't instantly revoke** (offline-first design). But:
- License expires naturally
- You can refuse to issue renewal
- You can add optional online revocation check

## Summary

The process is:

1. **Customer pays** → Stripe processes payment
2. **Your server generates license** → Signed JWT token
3. **Customer receives email** → Contains license key
4. **Customer activates license** → Pastes key in app
5. **App verifies locally** → Checks signature + expiration
6. **Features unlock** → Immediately available

**Key Insight:** The license key IS the proof of payment. It's cryptographically signed, so customers can't forge it. Your app verifies the signature locally without needing to contact your servers.

This is the same approach used by GitLab, Sentry, Metabase, and other successful self-hosted products.
