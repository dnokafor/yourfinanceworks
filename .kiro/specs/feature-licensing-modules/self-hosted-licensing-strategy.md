# Self-Hosted Feature Licensing Strategy

## The Challenge

You have a self-hosted application where:
- ✅ Users have full code access (open source or source-available)
- ✅ Users want control over their infrastructure
- ✅ Users should try features easily before paying
- ❌ Traditional license keys can be bypassed (code is visible)
- ❌ Cloud-only licensing removes user control

## Best Practices for Self-Hosted Feature Licensing

### Strategy: "Honor System + Value-Based Licensing"

This approach is used successfully by companies like:
- **GitLab** (self-hosted with paid features)
- **Sentry** (self-hosted with license keys)
- **Metabase** (self-hosted with premium features)
- **Mattermost** (self-hosted with enterprise features)

## Recommended Approach: Hybrid Licensing Model

### 1. **Trial-First Experience** (Best for User Experience)

```
User Journey:
1. Install → All features enabled (30-day trial)
2. Use features → Discover what they need
3. Trial expires → Choose features to purchase
4. Enter license key → Features re-enabled
5. License expires → Grace period → Disable
```

**Benefits:**
- Users can try everything
- Low friction to start
- Users only pay for what they value
- Builds trust


### 2. **License Key System** (Technical Implementation)

#### A. License Key Generation (Your Side)

```python
# Your licensing server (separate from user's installation)
import jwt
import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class LicenseGenerator:
    """Generate signed license keys"""
    
    def __init__(self, private_key_path: str):
        with open(private_key_path, 'rb') as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None
            )
    
    def generate_license(
        self,
        customer_email: str,
        features: list[str],
        expires_at: datetime.datetime,
        max_users: int = None
    ) -> str:
        """
        Generate a signed license key
        
        Returns: JWT token that can be verified with public key
        """
        payload = {
            'customer_email': customer_email,
            'features': features,
            'expires_at': expires_at.isoformat(),
            'max_users': max_users,
            'issued_at': datetime.datetime.utcnow().isoformat(),
            'license_version': '1.0'
        }
        
        # Sign with your private key
        license_key = jwt.encode(
            payload,
            self.private_key,
            algorithm='RS256'
        )
        
        return license_key

# Example usage
generator = LicenseGenerator('private_key.pem')
license_key = generator.generate_license(
    customer_email='customer@example.com',
    features=['ai_invoice', 'ai_expense', 'batch_processing'],
    expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=365),
    max_users=10
)

print(f"License Key: {license_key}")
```

#### B. License Verification (User's Installation)

```python
# api/services/license_service.py
import jwt
import datetime
import requests
from typing import Optional, Dict, List
from cryptography.hazmat.primitives import serialization

class LicenseService:
    """Verify and manage licenses in user's installation"""
    
    # Your public key (embedded in the application)
    PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----
    """
    
    # Optional: License server for online validation
    LICENSE_SERVER = "https://licenses.yourcompany.com/api/validate"
    
    def __init__(self, db: Session):
        self.db = db
        self.public_key = serialization.load_pem_public_key(
            self.PUBLIC_KEY.encode()
        )
    
    def verify_license(self, license_key: str) -> Dict:
        """
        Verify license key signature and expiration
        
        Returns license details if valid, raises exception if invalid
        """
        try:
            # Decode and verify signature
            payload = jwt.decode(
                license_key,
                self.public_key,
                algorithms=['RS256']
            )
            
            # Check expiration
            expires_at = datetime.datetime.fromisoformat(payload['expires_at'])
            if expires_at < datetime.datetime.utcnow():
                return {
                    'valid': False,
                    'error': 'LICENSE_EXPIRED',
                    'expires_at': expires_at
                }
            
            # Optional: Online validation (requires internet)
            if self._should_validate_online():
                online_valid = self._validate_online(license_key)
                if not online_valid:
                    return {
                        'valid': False,
                        'error': 'LICENSE_REVOKED'
                    }
            
            return {
                'valid': True,
                'customer_email': payload['customer_email'],
                'features': payload['features'],
                'expires_at': expires_at,
                'max_users': payload.get('max_users'),
                'issued_at': payload['issued_at']
            }
            
        except jwt.InvalidSignatureError:
            return {'valid': False, 'error': 'INVALID_SIGNATURE'}
        except jwt.DecodeError:
            return {'valid': False, 'error': 'INVALID_FORMAT'}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _should_validate_online(self) -> bool:
        """Check if online validation should be attempted"""
        # Only validate online once per day to avoid constant calls
        last_check = self._get_last_online_check()
        if not last_check:
            return True
        
        return (datetime.datetime.utcnow() - last_check).days >= 1
    
    def _validate_online(self, license_key: str) -> bool:
        """Optional: Validate license with your server"""
        try:
            response = requests.post(
                self.LICENSE_SERVER,
                json={'license_key': license_key},
                timeout=5
            )
            return response.status_code == 200 and response.json().get('valid')
        except:
            # If server unreachable, trust local validation
            return True
    
    def get_enabled_features(self, license_key: Optional[str] = None) -> List[str]:
        """Get list of enabled features based on license"""
        
        # Check for trial mode
        if self._is_trial_active():
            return self._get_all_features()
        
        # No license = core features only
        if not license_key:
            return self._get_core_features()
        
        # Verify license
        license_info = self.verify_license(license_key)
        if license_info['valid']:
            return license_info['features']
        
        # Invalid license = core features only
        return self._get_core_features()
```


### 3. **Trial Management**

```python
# api/services/trial_service.py
import datetime
from sqlalchemy.orm import Session
from models.models_per_tenant import InstallationInfo

class TrialService:
    """Manage trial periods for self-hosted installations"""
    
    TRIAL_DAYS = 30
    GRACE_PERIOD_DAYS = 7
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_installation_info(self) -> InstallationInfo:
        """Get or create installation info"""
        info = self.db.query(InstallationInfo).first()
        
        if not info:
            # First time installation
            info = InstallationInfo(
                installation_id=self._generate_installation_id(),
                first_started_at=datetime.datetime.utcnow(),
                trial_started_at=datetime.datetime.utcnow(),
                trial_ends_at=datetime.datetime.utcnow() + datetime.timedelta(days=self.TRIAL_DAYS)
            )
            self.db.add(info)
            self.db.commit()
        
        return info
    
    def is_trial_active(self) -> bool:
        """Check if trial period is still active"""
        info = self.get_installation_info()
        
        if info.license_key:
            # Has license, not in trial
            return False
        
        now = datetime.datetime.utcnow()
        return now < info.trial_ends_at
    
    def get_trial_status(self) -> Dict:
        """Get detailed trial status"""
        info = self.get_installation_info()
        now = datetime.datetime.utcnow()
        
        if info.license_key:
            return {
                'status': 'licensed',
                'has_license': True
            }
        
        days_remaining = (info.trial_ends_at - now).days
        
        if days_remaining > 0:
            return {
                'status': 'trial',
                'days_remaining': days_remaining,
                'trial_ends_at': info.trial_ends_at.isoformat(),
                'in_grace_period': False
            }
        
        # Trial expired, check grace period
        grace_ends_at = info.trial_ends_at + datetime.timedelta(days=self.GRACE_PERIOD_DAYS)
        grace_days_remaining = (grace_ends_at - now).days
        
        if grace_days_remaining > 0:
            return {
                'status': 'grace_period',
                'days_remaining': grace_days_remaining,
                'grace_ends_at': grace_ends_at.isoformat(),
                'in_grace_period': True
            }
        
        return {
            'status': 'expired',
            'days_remaining': 0,
            'trial_expired': True
        }
    
    def activate_license(self, license_key: str) -> Dict:
        """Activate a license key"""
        from services.license_service import LicenseService
        
        license_service = LicenseService(self.db)
        license_info = license_service.verify_license(license_key)
        
        if not license_info['valid']:
            return {
                'success': False,
                'error': license_info['error']
            }
        
        # Save license
        info = self.get_installation_info()
        info.license_key = license_key
        info.license_activated_at = datetime.datetime.utcnow()
        info.license_expires_at = license_info['expires_at']
        self.db.commit()
        
        return {
            'success': True,
            'features': license_info['features'],
            'expires_at': license_info['expires_at']
        }
```


### 4. **User-Friendly UI for License Management**

```typescript
// ui/src/pages/LicenseManagement.tsx
import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

export const LicenseManagement = () => {
  const [trialStatus, setTrialStatus] = useState(null);
  const [licenseKey, setLicenseKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchTrialStatus();
  }, []);

  const fetchTrialStatus = async () => {
    const response = await api.get('/license/status');
    setTrialStatus(response.data);
  };

  const activateLicense = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/license/activate', { license_key: licenseKey });
      
      if (response.data.success) {
        alert('License activated successfully!');
        fetchTrialStatus();
        window.location.reload(); // Refresh to load new features
      } else {
        setError(response.data.error);
      }
    } catch (err) {
      setError('Failed to activate license');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = () => {
    if (!trialStatus) return null;
    
    switch (trialStatus.status) {
      case 'licensed':
        return <Badge variant="success">Licensed</Badge>;
      case 'trial':
        return <Badge variant="info">Trial ({trialStatus.days_remaining} days left)</Badge>;
      case 'grace_period':
        return <Badge variant="warning">Grace Period ({trialStatus.days_remaining} days left)</Badge>;
      case 'expired':
        return <Badge variant="destructive">Expired</Badge>;
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">License Management</h1>
      
      {/* Current Status */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Current Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">License Status</p>
              {getStatusBadge()}
            </div>
            
            {trialStatus?.status === 'trial' && (
              <Alert className="max-w-md">
                <AlertDescription>
                  Your trial expires in {trialStatus.days_remaining} days. 
                  Purchase a license to continue using premium features.
                </AlertDescription>
              </Alert>
            )}
            
            {trialStatus?.status === 'grace_period' && (
              <Alert variant="warning" className="max-w-md">
                <AlertDescription>
                  Your trial has expired. You have {trialStatus.days_remaining} days 
                  of grace period remaining. Premium features will be disabled after that.
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>
      
      {/* Activate License */}
      {trialStatus?.status !== 'licensed' && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Activate License</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  License Key
                </label>
                <Input
                  type="text"
                  placeholder="Enter your license key"
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  className="font-mono"
                />
              </div>
              
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              
              <Button 
                onClick={activateLicense} 
                disabled={!licenseKey || loading}
              >
                {loading ? 'Activating...' : 'Activate License'}
              </Button>
              
              <p className="text-sm text-gray-600">
                Don't have a license? 
                <a href="https://yourcompany.com/pricing" className="text-blue-600 ml-1">
                  Purchase one here
                </a>
              </p>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Licensed Features */}
      {trialStatus?.features && (
        <Card>
          <CardHeader>
            <CardTitle>Enabled Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {trialStatus.features.map((feature) => (
                <div key={feature.id} className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span>{feature.name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
```


### 5. **Payment & License Generation Flow**

```
User Side (Self-Hosted)          Your Side (License Server)
─────────────────────            ──────────────────────────

1. User tries feature
   during trial ──────────────►  (No interaction)

2. User likes feature,
   clicks "Purchase" ──────────► Website/Stripe checkout

3. User completes payment ─────► Payment webhook received
                                  ↓
                                  Generate license key
                                  ↓
                                  Email license to customer
                                  ↓
4. User receives email ◄─────────  Send email with:
   with license key                - License key
                                   - Installation instructions
                                   - Support info

5. User enters license
   in Settings UI ──────────────► (Optional) Validate online
                                   ↓
6. License verified locally        Return: valid/invalid
   ↓
7. Features enabled! ◄─────────── (No further interaction needed)
```

#### Payment Integration Example (Stripe)

```python
# Your license server
from flask import Flask, request
import stripe
from license_generator import LicenseGenerator

app = Flask(__name__)
stripe.api_key = 'sk_live_...'

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe payment webhook"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Extract purchase details
        customer_email = session['customer_email']
        features = session['metadata']['features'].split(',')
        plan_duration = int(session['metadata']['duration_days'])
        
        # Generate license
        generator = LicenseGenerator('private_key.pem')
        license_key = generator.generate_license(
            customer_email=customer_email,
            features=features,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=plan_duration)
        )
        
        # Store in database
        save_license_to_db(customer_email, license_key, features)
        
        # Send email
        send_license_email(customer_email, license_key, features)
        
        return 'Success', 200
    
    return 'Unhandled event', 200
```


## Addressing Your Concerns

### "Users have all the code - can't they just bypass licensing?"

**Yes, technically they can.** But here's why it works anyway:

#### 1. **Honor System Works for B2B**
- Most businesses won't risk legal issues
- Companies have budgets for software
- Bypassing licenses damages reputation
- Support and updates require valid license

#### 2. **Make Bypassing Harder Than Paying**
```python
# Don't do this (easy to bypass):
if license_key == "ABC123":
    enable_feature()

# Do this (requires effort to bypass):
# - Cryptographic signature verification
# - Multiple validation points
# - Obfuscated validation logic
# - Online validation checks
```

#### 3. **Value-Based Pricing**
- If features are valuable, users will pay
- If they bypass, they weren't going to pay anyway
- Focus on making features so good they want to support you

#### 4. **Enforcement Through Updates**
- New versions require valid license
- Security patches require valid license
- Support requires valid license

### "How to make it easy for users to pay?"

#### Option 1: Self-Service Portal (Recommended)

```
User clicks "Upgrade" in app
    ↓
Opens: https://yourcompany.com/purchase
    ↓
Selects features + duration
    ↓
Pays with Stripe/PayPal
    ↓
Receives license key immediately
    ↓
Enters key in app
    ↓
Features enabled!
```

**Implementation:**
```typescript
// In your app
<Button onClick={() => {
  window.open('https://yourcompany.com/purchase?email=' + userEmail, '_blank')
}}>
  Purchase License
</Button>
```

#### Option 2: In-App Purchase Flow

```typescript
// ui/src/pages/FeatureUpgrade.tsx
export const FeatureUpgrade = ({ feature }) => {
  const handlePurchase = async () => {
    // Create Stripe checkout session
    const response = await api.post('/license/create-checkout', {
      features: [feature.id],
      duration: 365 // days
    });
    
    // Redirect to Stripe
    window.location.href = response.data.checkout_url;
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{feature.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <p>{feature.description}</p>
        <p className="text-2xl font-bold">${feature.price}/year</p>
        <Button onClick={handlePurchase}>
          Purchase Now
        </Button>
      </CardContent>
    </Card>
  );
};
```


## Recommended Licensing Models

### Model 1: Feature-Based (Your Use Case)

```
Core Features: FREE
├── Invoices
├── Expenses  
├── Clients
└── Basic Reports

Premium Features: PAID
├── AI Invoice Processing - $29/month
├── AI Expense Processing - $29/month
├── Batch Processing - $19/month
├── Tax Integration - $15/month
├── Inventory Management - $25/month
└── Advanced Analytics - $35/month

Bundle: All Premium - $99/month (save 40%)
```

**License Key Format:**
```
features: ["ai_invoice", "ai_expense", "batch_processing"]
expires: 2025-12-31
```

### Model 2: Tier-Based

```
Starter: FREE
├── Core features only

Professional: $49/month
├── All AI features
├── Batch processing
├── Basic integrations

Enterprise: $149/month
├── Everything in Professional
├── Inventory management
├── Advanced analytics
├── Priority support
```

### Model 3: Usage-Based

```
Pay per AI processing:
├── $0.10 per invoice processed
├── $0.05 per expense processed
├── $0.15 per bank statement

Prepaid credits:
├── $50 = 500 credits
├── $200 = 2,500 credits (25% bonus)
├── $500 = 7,500 credits (50% bonus)
```

**License Key Format:**
```
credits: 500
features: ["ai_invoice", "ai_expense"]
expires: 2025-12-31
```


## Complete User Experience Flow

### First-Time Installation

```
Day 1: User installs your app
├── All features enabled (30-day trial)
├── Banner: "Trial: 30 days remaining"
└── User explores all features

Day 15: User loves AI Invoice feature
├── Banner: "Trial: 15 days remaining"
├── User clicks "Purchase AI Invoice"
├── Redirected to payment page
├── Pays $29/month
├── Receives license key via email
├── Enters key in Settings
└── AI Invoice feature permanently enabled

Day 30: Trial expires
├── Features without license disabled
├── Banner: "Trial expired. Purchase features you need."
├── Grace period: 7 days to enter license
└── After grace: Premium features fully disabled

Day 37: Grace period ends
├── Only core features available
├── Prominent "Upgrade" buttons on disabled features
└── User can purchase anytime
```

### Renewal Experience

```
30 days before expiration:
├── Email: "License expires in 30 days"
└── In-app banner: "Renew now"

7 days before expiration:
├── Email: "License expires in 7 days"
└── In-app warning banner

Expiration day:
├── Features disabled
├── Grace period: 7 days
└── Email: "License expired - renew now"

After grace period:
├── Features fully disabled
└── User can renew anytime
```


## Technical Architecture

### Database Schema

```sql
-- Installation tracking
CREATE TABLE installation_info (
    id SERIAL PRIMARY KEY,
    installation_id VARCHAR(100) UNIQUE NOT NULL,
    first_started_at TIMESTAMP NOT NULL,
    trial_started_at TIMESTAMP NOT NULL,
    trial_ends_at TIMESTAMP NOT NULL,
    license_key TEXT,
    license_activated_at TIMESTAMP,
    license_expires_at TIMESTAMP,
    last_online_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- License validation cache
CREATE TABLE license_validations (
    id SERIAL PRIMARY KEY,
    license_key TEXT NOT NULL,
    validated_at TIMESTAMP NOT NULL,
    is_valid BOOLEAN NOT NULL,
    features JSON,
    expires_at TIMESTAMP,
    error_message TEXT
);

-- Feature usage tracking (for analytics)
CREATE TABLE feature_usage (
    id SERIAL PRIMARY KEY,
    feature_id VARCHAR(50) NOT NULL,
    used_at TIMESTAMP NOT NULL,
    user_id INTEGER,
    metadata JSON
);
```

### API Endpoints

```python
# api/routers/license.py
from fastapi import APIRouter, Depends
from services.license_service import LicenseService
from services.trial_service import TrialService

router = APIRouter(prefix="/license", tags=["license"])

@router.get("/status")
async def get_license_status(db: Session = Depends(get_db)):
    """Get current license/trial status"""
    trial_service = TrialService(db)
    return trial_service.get_trial_status()

@router.post("/activate")
async def activate_license(
    request: LicenseActivateRequest,
    db: Session = Depends(get_db)
):
    """Activate a license key"""
    trial_service = TrialService(db)
    return trial_service.activate_license(request.license_key)

@router.post("/validate")
async def validate_license(
    request: LicenseValidateRequest,
    db: Session = Depends(get_db)
):
    """Validate a license key"""
    license_service = LicenseService(db)
    return license_service.verify_license(request.license_key)

@router.get("/features")
async def get_available_features():
    """Get list of all licensable features"""
    return {
        "features": [
            {
                "id": "ai_invoice",
                "name": "AI Invoice Processing",
                "description": "Automatically extract data from invoices using AI",
                "price_monthly": 29,
                "price_yearly": 290
            },
            # ... more features
        ]
    }

@router.post("/create-checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    current_user = Depends(get_current_user)
):
    """Create Stripe checkout session for license purchase"""
    import stripe
    
    session = stripe.checkout.Session.create(
        customer_email=current_user.email,
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'License: {", ".join(request.features)}',
                },
                'unit_amount': calculate_price(request.features, request.duration),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='https://yourapp.com/license/success',
        cancel_url='https://yourapp.com/license/cancel',
        metadata={
            'features': ','.join(request.features),
            'duration_days': request.duration
        }
    )
    
    return {'checkout_url': session.url}
```


## Best Practices Summary

### ✅ DO

1. **Make trial generous** - 30 days, all features
2. **Make payment easy** - One-click purchase, instant activation
3. **Be transparent** - Clear pricing, no hidden fees
4. **Provide value** - Features worth paying for
5. **Offer support** - Help with license issues
6. **Allow offline** - Don't require constant internet
7. **Grace periods** - 7 days after expiration
8. **Email reminders** - Before expiration
9. **Flexible licensing** - Per-feature or bundles
10. **Honor system** - Trust your users

### ❌ DON'T

1. **Don't be aggressive** - No constant popups
2. **Don't break core features** - Keep basic functionality free
3. **Don't require internet** - For basic validation
4. **Don't make it complex** - Simple license key entry
5. **Don't hide pricing** - Be upfront about costs
6. **Don't punish trials** - Full features during trial
7. **Don't make it hard to pay** - Streamline purchase
8. **Don't over-validate** - Once per day online check is enough
9. **Don't be unclear** - Explain what each feature does
10. **Don't forget support** - Help users with issues

## Implementation Priority

### Phase 1: Basic Licensing (Week 1-2)
- [ ] Create license generation system
- [ ] Implement license verification
- [ ] Add trial tracking
- [ ] Create license activation UI
- [ ] Test license flow

### Phase 2: Payment Integration (Week 3)
- [ ] Set up Stripe account
- [ ] Create pricing page
- [ ] Implement webhook handler
- [ ] Test payment flow
- [ ] Set up email notifications

### Phase 3: Feature Gating (Week 4-5)
- [ ] Add feature gates to code
- [ ] Update UI to show licensed features
- [ ] Add upgrade prompts
- [ ] Test feature enable/disable
- [ ] Add usage analytics

### Phase 4: Polish (Week 6)
- [ ] Add expiration warnings
- [ ] Improve error messages
- [ ] Add license management UI
- [ ] Create documentation
- [ ] Beta test with users

## Conclusion

**Recommended Approach for Your Use Case:**

1. **30-day trial** with all features enabled
2. **Feature-based licensing** - users pay for what they use
3. **Self-service purchase** - Stripe checkout
4. **License key activation** - Simple copy/paste
5. **Offline-first** - Works without internet
6. **Honor system** - Trust users, make bypassing harder than paying
7. **Grace periods** - 7 days after expiration
8. **Transparent pricing** - Clear value proposition

This gives users **maximum control** (self-hosted) while providing you with **sustainable revenue** (paid features). The key is making features so valuable that users want to pay, and making payment so easy that they don't hesitate.

**Example Companies Using This Model Successfully:**
- GitLab (self-hosted + paid features)
- Sentry (self-hosted + paid features)
- Metabase (self-hosted + paid features)
- Mattermost (self-hosted + paid features)
- Discourse (self-hosted + paid features)

They all have open-source code, yet generate millions in revenue because they provide value and make it easy to pay.
