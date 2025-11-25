# Complete License Key Generation Guide

## Overview

This guide shows you exactly how to generate, sign, and manage license keys for your customers. We'll use JWT (JSON Web Tokens) with RSA signatures - the same approach used by GitLab, Sentry, and Metabase.

## Step 1: Generate RSA Key Pair (One-Time Setup)

### Using OpenSSL (Recommended)

```bash
# Generate private key (KEEP THIS SECRET!)
openssl genrsa -out private_key.pem 4096

# Generate public key (embed in your app)
openssl rsa -in private_key.pem -pubout -out public_key.pem

# View the keys
cat private_key.pem
cat public_key.pem
```

### Using Python

```python
# generate_keys.py
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Generate private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096,
    backend=default_backend()
)

# Save private key (KEEP SECRET!)
with open('private_key.pem', 'wb') as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Generate and save public key
public_key = private_key.public_key()
with open('public_key.pem', 'wb') as f:
    f.write(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

print("✅ Keys generated successfully!")
print("⚠️  IMPORTANT: Keep private_key.pem SECRET!")
print("📦 Embed public_key.pem in your application")
```

**Run it:**
```bash
python generate_keys.py
```

**Result:**
```
private_key.pem  # KEEP SECRET - use for signing licenses
public_key.pem   # PUBLIC - embed in your app for verification
```


## Step 2: License Generation System (Your Side)

Create a separate service/script for generating licenses. This should NOT be in the customer's installation.

### Complete License Generator

```python
# license_generator.py
import jwt
import datetime
import uuid
from pathlib import Path

class LicenseGenerator:
    """
    Generate signed license keys for customers.
    Run this on YOUR server, not customer's installation.
    """
    
    def __init__(self, private_key_path='private_key.pem'):
        """Load your private key"""
        with open(private_key_path, 'rb') as f:
            self.private_key = f.read()
    
    def generate_license(
        self,
        customer_email: str,
        customer_name: str,
        features: list,
        duration_days: int = 365,
        max_users: int = None,
        metadata: dict = None
    ) -> str:
        """
        Generate a signed license key.
        
        Args:
            customer_email: Customer's email address
            customer_name: Customer's company/name
            features: List of feature IDs (e.g., ['ai_invoice', 'ai_expense'])
            duration_days: License duration in days (365 = 1 year)
            max_users: Maximum number of users (None = unlimited)
            metadata: Additional custom data
        
        Returns:
            JWT license key string
        """
        now = datetime.datetime.utcnow()
        expires_at = now + datetime.timedelta(days=duration_days)
        
        # License payload
        payload = {
            # Standard JWT claims
            'iss': 'YourCompany',  # Issuer
            'sub': customer_email,  # Subject (customer)
            'iat': int(now.timestamp()),  # Issued at
            'exp': int(expires_at.timestamp()),  # Expires at
            'jti': str(uuid.uuid4()),  # Unique license ID
            
            # Custom claims
            'customer_name': customer_name,
            'customer_email': customer_email,
            'features': features,
            'max_users': max_users,
            'license_type': 'commercial',
            'version': '1.0',
            
            # Optional metadata
            **(metadata or {})
        }
        
        # Sign with private key
        license_key = jwt.encode(
            payload,
            self.private_key,
            algorithm='RS256'
        )
        
        return license_key
    
    def generate_trial_license(
        self,
        customer_email: str,
        trial_days: int = 30
    ) -> str:
        """Generate a trial license with all features"""
        return self.generate_license(
            customer_email=customer_email,
            customer_name='Trial User',
            features=['all'],  # All features for trial
            duration_days=trial_days,
            metadata={'license_type': 'trial'}
        )
    
    def decode_license(self, license_key: str) -> dict:
        """
        Decode a license (for testing/debugging).
        Note: This doesn't verify signature, just decodes.
        """
        return jwt.decode(license_key, options={"verify_signature": False})


# Example usage
if __name__ == '__main__':
    generator = LicenseGenerator('private_key.pem')
    
    # Generate a license
    license_key = generator.generate_license(
        customer_email='customer@example.com',
        customer_name='Acme Corporation',
        features=['ai_invoice', 'ai_expense', 'batch_processing'],
        duration_days=365,  # 1 year
        max_users=10
    )
    
    print("=" * 80)
    print("LICENSE KEY GENERATED")
    print("=" * 80)
    print(f"\nCustomer: Acme Corporation")
    print(f"Email: customer@example.com")
    print(f"Features: AI Invoice, AI Expense, Batch Processing")
    print(f"Duration: 365 days")
    print(f"Max Users: 10")
    print(f"\nLicense Key:")
    print("-" * 80)
    print(license_key)
    print("-" * 80)
    
    # Decode to verify
    decoded = generator.decode_license(license_key)
    print(f"\nExpires: {datetime.datetime.fromtimestamp(decoded['exp'])}")
    print(f"License ID: {decoded['jti']}")
```

**Run it:**
```bash
python license_generator.py
```

**Output:**
```
================================================================================
LICENSE KEY GENERATED
================================================================================

Customer: Acme Corporation
Email: customer@example.com
Features: AI Invoice, AI Expense, Batch Processing
Duration: 365 days
Max Users: 10

License Key:
--------------------------------------------------------------------------------
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZb3VyQ29tcGFueSIsInN1YiI6ImN1c3RvbWVyQGV4YW1wbGUuY29tIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjE3MzE1MzYwMDAsImp0aSI6IjEyMzQ1Njc4LTkwYWItY2RlZi0xMjM0LTU2Nzg5MGFiY2RlZiIsImN1c3RvbWVyX25hbWUiOiJBY21lIENvcnBvcmF0aW9uIiwiY3VzdG9tZXJfZW1haWwiOiJjdXN0b21lckBleGFtcGxlLmNvbSIsImZlYXR1cmVzIjpbImFpX2ludm9pY2UiLCJhaV9leHBlbnNlIiwiYmF0Y2hfcHJvY2Vzc2luZyJdLCJtYXhfdXNlcnMiOjEwLCJsaWNlbnNlX3R5cGUiOiJjb21tZXJjaWFsIiwidmVyc2lvbiI6IjEuMCJ9.signature...
--------------------------------------------------------------------------------

Expires: 2024-11-16 12:00:00
License ID: 12345678-90ab-cdef-1234-567890abcdef
```


## Step 3: CLI Tool for Easy License Generation

Create a user-friendly CLI tool for generating licenses:

```python
# generate_license_cli.py
import argparse
import sys
from license_generator import LicenseGenerator
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(
        description='Generate license keys for customers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate 1-year license with specific features
  python generate_license_cli.py \\
    --email customer@example.com \\
    --name "Acme Corp" \\
    --features ai_invoice ai_expense \\
    --duration 365

  # Generate trial license
  python generate_license_cli.py \\
    --email trial@example.com \\
    --trial

  # Generate license with user limit
  python generate_license_cli.py \\
    --email customer@example.com \\
    --name "Small Business" \\
    --features ai_invoice \\
    --duration 365 \\
    --max-users 5
        '''
    )
    
    parser.add_argument('--email', required=True, help='Customer email')
    parser.add_argument('--name', help='Customer name/company')
    parser.add_argument('--features', nargs='+', help='Feature IDs (space-separated)')
    parser.add_argument('--duration', type=int, default=365, help='Duration in days (default: 365)')
    parser.add_argument('--max-users', type=int, help='Maximum number of users')
    parser.add_argument('--trial', action='store_true', help='Generate trial license')
    parser.add_argument('--private-key', default='private_key.pem', help='Path to private key')
    parser.add_argument('--output', help='Save license to file')
    
    args = parser.parse_args()
    
    # Initialize generator
    try:
        generator = LicenseGenerator(args.private_key)
    except FileNotFoundError:
        print(f"❌ Error: Private key not found at {args.private_key}")
        print("   Run 'python generate_keys.py' first to create keys")
        sys.exit(1)
    
    # Generate license
    if args.trial:
        license_key = generator.generate_trial_license(args.email)
        print(f"\n✅ Trial license generated for {args.email}")
    else:
        if not args.features:
            print("❌ Error: --features required (unless using --trial)")
            sys.exit(1)
        
        license_key = generator.generate_license(
            customer_email=args.email,
            customer_name=args.name or args.email,
            features=args.features,
            duration_days=args.duration,
            max_users=args.max_users
        )
        print(f"\n✅ License generated for {args.name or args.email}")
    
    # Decode to show details
    decoded = generator.decode_license(license_key)
    expires = datetime.fromtimestamp(decoded['exp'])
    
    print("\n" + "=" * 80)
    print("LICENSE DETAILS")
    print("=" * 80)
    print(f"Customer: {decoded.get('customer_name', 'N/A')}")
    print(f"Email: {decoded['customer_email']}")
    print(f"Features: {', '.join(decoded['features'])}")
    print(f"Expires: {expires.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Max Users: {decoded.get('max_users', 'Unlimited')}")
    print(f"License ID: {decoded['jti']}")
    
    print("\n" + "=" * 80)
    print("LICENSE KEY")
    print("=" * 80)
    print(license_key)
    print("=" * 80)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(license_key)
        print(f"\n💾 License saved to {args.output}")
    
    print("\n📧 Send this license key to the customer")
    print("   They can enter it in Settings → License Management")

if __name__ == '__main__':
    main()
```

**Usage Examples:**

```bash
# Generate license for a customer
python generate_license_cli.py \
  --email customer@acme.com \
  --name "Acme Corporation" \
  --features ai_invoice ai_expense batch_processing \
  --duration 365 \
  --max-users 10

# Generate trial license
python generate_license_cli.py \
  --email trial@startup.com \
  --trial

# Generate and save to file
python generate_license_cli.py \
  --email customer@example.com \
  --name "Example Inc" \
  --features ai_invoice \
  --duration 365 \
  --output license_example_inc.txt
```


## Step 4: Web-Based License Generator (Optional)

For a more user-friendly approach, create a simple web interface:

```python
# license_web_generator.py
from flask import Flask, render_template, request, jsonify
from license_generator import LicenseGenerator
from datetime import datetime

app = Flask(__name__)
generator = LicenseGenerator('private_key.pem')

AVAILABLE_FEATURES = {
    'ai_invoice': 'AI Invoice Processing',
    'ai_expense': 'AI Expense Processing',
    'ai_bank_statement': 'AI Bank Statement Processing',
    'ai_chat': 'AI Chat Assistant',
    'tax_integration': 'Tax Service Integration',
    'slack_integration': 'Slack Integration',
    'batch_processing': 'Batch File Processing',
    'inventory': 'Inventory Management',
    'approvals': 'Approval Workflows',
    'reporting': 'Advanced Reporting',
}

@app.route('/')
def index():
    return render_template('generator.html', features=AVAILABLE_FEATURES)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    
    try:
        license_key = generator.generate_license(
            customer_email=data['email'],
            customer_name=data['name'],
            features=data['features'],
            duration_days=int(data['duration']),
            max_users=int(data['max_users']) if data.get('max_users') else None
        )
        
        decoded = generator.decode_license(license_key)
        
        return jsonify({
            'success': True,
            'license_key': license_key,
            'details': {
                'customer': decoded['customer_name'],
                'email': decoded['customer_email'],
                'features': decoded['features'],
                'expires': datetime.fromtimestamp(decoded['exp']).isoformat(),
                'license_id': decoded['jti']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**HTML Template (templates/generator.html):**

```html
<!DOCTYPE html>
<html>
<head>
    <title>License Generator</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 8px; box-sizing: border-box; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        .result { margin-top: 20px; padding: 15px; background: #f8f9fa; border: 1px solid #dee2e6; }
        .license-key { font-family: monospace; word-break: break-all; background: white; padding: 10px; border: 1px solid #ccc; }
        .feature-checkbox { margin-right: 10px; }
    </style>
</head>
<body>
    <h1>🔑 License Key Generator</h1>
    
    <form id="licenseForm">
        <div class="form-group">
            <label>Customer Email *</label>
            <input type="email" id="email" required>
        </div>
        
        <div class="form-group">
            <label>Customer Name *</label>
            <input type="text" id="name" required>
        </div>
        
        <div class="form-group">
            <label>Features *</label>
            {% for id, name in features.items() %}
            <div>
                <input type="checkbox" class="feature-checkbox" value="{{ id }}" id="feature_{{ id }}">
                <label for="feature_{{ id }}" style="display: inline; font-weight: normal;">{{ name }}</label>
            </div>
            {% endfor %}
        </div>
        
        <div class="form-group">
            <label>Duration (days) *</label>
            <select id="duration">
                <option value="30">30 days (Trial)</option>
                <option value="90">90 days (Quarterly)</option>
                <option value="365" selected>365 days (Annual)</option>
                <option value="730">730 days (2 Years)</option>
                <option value="1095">1095 days (3 Years)</option>
            </select>
        </div>
        
        <div class="form-group">
            <label>Max Users (leave empty for unlimited)</label>
            <input type="number" id="max_users" min="1">
        </div>
        
        <button type="submit">Generate License</button>
    </form>
    
    <div id="result" class="result" style="display: none;">
        <h2>✅ License Generated</h2>
        <p><strong>Customer:</strong> <span id="result_customer"></span></p>
        <p><strong>Email:</strong> <span id="result_email"></span></p>
        <p><strong>Features:</strong> <span id="result_features"></span></p>
        <p><strong>Expires:</strong> <span id="result_expires"></span></p>
        <p><strong>License ID:</strong> <span id="result_id"></span></p>
        
        <h3>License Key:</h3>
        <div class="license-key" id="license_key"></div>
        
        <button onclick="copyLicense()">📋 Copy to Clipboard</button>
    </div>
    
    <script>
        document.getElementById('licenseForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const features = Array.from(document.querySelectorAll('.feature-checkbox:checked'))
                .map(cb => cb.value);
            
            if (features.length === 0) {
                alert('Please select at least one feature');
                return;
            }
            
            const data = {
                email: document.getElementById('email').value,
                name: document.getElementById('name').value,
                features: features,
                duration: document.getElementById('duration').value,
                max_users: document.getElementById('max_users').value
            };
            
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('result_customer').textContent = result.details.customer;
                document.getElementById('result_email').textContent = result.details.email;
                document.getElementById('result_features').textContent = result.details.features.join(', ');
                document.getElementById('result_expires').textContent = new Date(result.details.expires).toLocaleString();
                document.getElementById('result_id').textContent = result.details.license_id;
                document.getElementById('license_key').textContent = result.license_key;
                document.getElementById('result').style.display = 'block';
            } else {
                alert('Error: ' + result.error);
            }
        });
        
        function copyLicense() {
            const licenseKey = document.getElementById('license_key').textContent;
            navigator.clipboard.writeText(licenseKey);
            alert('License key copied to clipboard!');
        }
    </script>
</body>
</html>
```

**Run it:**
```bash
pip install flask
python license_web_generator.py
```

Then open: http://localhost:5000


## Step 5: Automated License Generation with Stripe

Integrate with Stripe to automatically generate licenses when customers pay:

```python
# stripe_webhook_handler.py
from flask import Flask, request, jsonify
import stripe
from license_generator import LicenseGenerator
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
stripe.api_key = 'sk_live_...'  # Your Stripe secret key
webhook_secret = 'whsec_...'  # Your Stripe webhook secret

generator = LicenseGenerator('private_key.pem')

# Feature pricing mapping
FEATURE_PRICES = {
    'price_ai_invoice_monthly': ['ai_invoice'],
    'price_ai_expense_monthly': ['ai_expense'],
    'price_bundle_monthly': ['ai_invoice', 'ai_expense', 'batch_processing', 'tax_integration'],
}

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Handle successful payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Extract customer info
        customer_email = session['customer_details']['email']
        customer_name = session['customer_details']['name']
        
        # Get purchased items
        line_items = stripe.checkout.Session.list_line_items(session['id'])
        
        # Determine features from purchased items
        features = []
        for item in line_items['data']:
            price_id = item['price']['id']
            if price_id in FEATURE_PRICES:
                features.extend(FEATURE_PRICES[price_id])
        
        # Determine duration (monthly = 30 days, yearly = 365 days)
        duration_days = 365 if 'yearly' in session.get('metadata', {}).get('plan', '') else 30
        
        # Generate license
        license_key = generator.generate_license(
            customer_email=customer_email,
            customer_name=customer_name,
            features=list(set(features)),  # Remove duplicates
            duration_days=duration_days,
            metadata={
                'stripe_session_id': session['id'],
                'stripe_customer_id': session.get('customer'),
                'amount_paid': session['amount_total'] / 100,  # Convert cents to dollars
                'currency': session['currency']
            }
        )
        
        # Save to database
        save_license_to_database(customer_email, license_key, features)
        
        # Send email to customer
        send_license_email(customer_email, customer_name, license_key, features)
        
        print(f"✅ License generated and sent to {customer_email}")
        
        return jsonify({'success': True}), 200
    
    return jsonify({'success': True}), 200


def save_license_to_database(email, license_key, features):
    """Save license to your database for record-keeping"""
    # Implementation depends on your database
    pass


def send_license_email(email, name, license_key, features):
    """Send license key to customer via email"""
    
    # Email configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "licenses@yourcompany.com"
    sender_password = "your-app-password"
    
    # Create email
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Invoice App License Key"
    message["From"] = sender_email
    message["To"] = email
    
    # Email body
    text = f"""
    Hi {name},
    
    Thank you for purchasing Invoice App!
    
    Your license key is:
    {license_key}
    
    Features included:
    {', '.join(features)}
    
    To activate:
    1. Open Invoice App
    2. Go to Settings → License Management
    3. Enter your license key
    4. Click "Activate"
    
    Need help? Reply to this email or visit https://yourcompany.com/support
    
    Best regards,
    The Invoice App Team
    """
    
    html = f"""
    <html>
      <body>
        <h2>Thank you for purchasing Invoice App!</h2>
        <p>Hi {name},</p>
        <p>Your license key is:</p>
        <div style="background: #f5f5f5; padding: 15px; font-family: monospace; word-break: break-all;">
          {license_key}
        </div>
        <h3>Features included:</h3>
        <ul>
          {''.join(f'<li>{feature}</li>' for feature in features)}
        </ul>
        <h3>To activate:</h3>
        <ol>
          <li>Open Invoice App</li>
          <li>Go to Settings → License Management</li>
          <li>Enter your license key</li>
          <li>Click "Activate"</li>
        </ol>
        <p>Need help? Reply to this email or visit <a href="https://yourcompany.com/support">our support page</a></p>
        <p>Best regards,<br>The Invoice App Team</p>
      </body>
    </html>
    """
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)
    
    # Send email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        print(f"📧 Email sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


if __name__ == '__main__':
    app.run(port=5001)
```

**Setup Stripe Webhook:**
1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://yourdomain.com/webhook/stripe`
3. Select events: `checkout.session.completed`
4. Copy webhook secret to `webhook_secret` variable


## Step 6: License Management Dashboard

Create a simple dashboard to manage all licenses:

```python
# license_dashboard.py
from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime
from license_generator import LicenseGenerator

app = Flask(__name__)
generator = LicenseGenerator('private_key.pem')

# Initialize database
def init_db():
    conn = sqlite3.connect('licenses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_email TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            license_key TEXT NOT NULL,
            features TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'active',
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def dashboard():
    conn = sqlite3.connect('licenses.db')
    c = conn.cursor()
    c.execute('SELECT * FROM licenses ORDER BY created_at DESC')
    licenses = c.fetchall()
    conn.close()
    
    # Decode each license to get details
    license_data = []
    for lic in licenses:
        try:
            decoded = generator.decode_license(lic[3])  # license_key column
            license_data.append({
                'id': lic[0],
                'customer_email': lic[1],
                'customer_name': lic[2],
                'features': lic[4],
                'created_at': lic[5],
                'expires_at': datetime.fromtimestamp(decoded['exp']).strftime('%Y-%m-%d'),
                'status': 'expired' if decoded['exp'] < datetime.now().timestamp() else 'active',
                'license_id': decoded['jti']
            })
        except:
            pass
    
    return render_template('dashboard.html', licenses=license_data)

@app.route('/api/licenses')
def get_licenses():
    conn = sqlite3.connect('licenses.db')
    c = conn.cursor()
    c.execute('SELECT * FROM licenses ORDER BY created_at DESC')
    licenses = c.fetchall()
    conn.close()
    
    return jsonify([{
        'id': lic[0],
        'customer_email': lic[1],
        'customer_name': lic[2],
        'features': lic[4],
        'created_at': lic[5],
        'status': lic[7]
    } for lic in licenses])

if __name__ == '__main__':
    app.run(debug=True, port=5002)
```


## Step 7: Security Best Practices

### 1. Protect Your Private Key

```bash
# Set restrictive permissions
chmod 600 private_key.pem

# Store in secure location
# - Use environment variables
# - Use secret management (AWS Secrets Manager, HashiCorp Vault)
# - Never commit to git

# Add to .gitignore
echo "private_key.pem" >> .gitignore
echo "*.pem" >> .gitignore
```

### 2. Rotate Keys Periodically

```python
# key_rotation.py
from license_generator import LicenseGenerator
from datetime import datetime

def rotate_keys():
    """
    Generate new key pair and re-sign all active licenses.
    Do this annually or if private key is compromised.
    """
    # Generate new keys
    print("Generating new key pair...")
    # ... key generation code ...
    
    # Re-sign all active licenses
    old_generator = LicenseGenerator('private_key_old.pem')
    new_generator = LicenseGenerator('private_key_new.pem')
    
    # Get all licenses from database
    licenses = get_all_licenses_from_db()
    
    for license_data in licenses:
        # Decode old license
        old_decoded = old_generator.decode_license(license_data['license_key'])
        
        # Generate new license with same data
        new_license = new_generator.generate_license(
            customer_email=old_decoded['customer_email'],
            customer_name=old_decoded['customer_name'],
            features=old_decoded['features'],
            duration_days=calculate_remaining_days(old_decoded['exp']),
            max_users=old_decoded.get('max_users')
        )
        
        # Update database
        update_license_in_db(license_data['id'], new_license)
        
        # Email customer with new license
        send_license_update_email(old_decoded['customer_email'], new_license)
    
    print(f"✅ Rotated {len(licenses)} licenses")
```

### 3. License Validation Rate Limiting

```python
# In customer's installation
from functools import lru_cache
import time

@lru_cache(maxsize=1)
def get_license_validation_cache():
    return {'last_check': 0, 'result': None}

def verify_license_with_cache(license_key):
    """Verify license with caching to prevent excessive checks"""
    cache = get_license_validation_cache()
    
    # Only check once per hour
    if time.time() - cache['last_check'] < 3600:
        return cache['result']
    
    # Perform verification
    result = verify_license(license_key)
    
    # Update cache
    cache['last_check'] = time.time()
    cache['result'] = result
    
    return result
```

### 4. Revocation List (Optional)

```python
# revocation_check.py
import requests

def is_license_revoked(license_id):
    """
    Check if license has been revoked.
    Optional: requires internet connection.
    """
    try:
        response = requests.get(
            f'https://licenses.yourcompany.com/api/revoked/{license_id}',
            timeout=5
        )
        return response.status_code == 200 and response.json().get('revoked', False)
    except:
        # If check fails, assume not revoked (offline-friendly)
        return False
```


## Complete Workflow Summary

### Your Side (License Server):

```
1. Customer purchases → Stripe payment
2. Stripe webhook → Your server
3. Generate license → Sign with private key
4. Save to database → Record keeping
5. Email customer → Send license key
```

### Customer Side (Self-Hosted):

```
1. Receive email → Get license key
2. Open app → Go to Settings
3. Enter license → Paste key
4. Verify signature → Using public key (embedded in app)
5. Features unlock → Immediately available
```

## Quick Start Checklist

- [ ] **Step 1:** Generate RSA key pair
  ```bash
  python generate_keys.py
  ```

- [ ] **Step 2:** Embed public key in your app
  ```python
  # In your app's license_service.py
  PUBLIC_KEY = """
  -----BEGIN PUBLIC KEY-----
  [paste public_key.pem content here]
  -----END PUBLIC KEY-----
  """
  ```

- [ ] **Step 3:** Secure private key
  ```bash
  chmod 600 private_key.pem
  # Store securely, never commit to git
  ```

- [ ] **Step 4:** Test license generation
  ```bash
  python generate_license_cli.py \
    --email test@example.com \
    --name "Test Customer" \
    --features ai_invoice \
    --duration 365
  ```

- [ ] **Step 5:** Test license verification
  ```python
  # In your app
  from services.license_service import verify_license
  result = verify_license(license_key)
  print(result)  # Should show valid=True
  ```

- [ ] **Step 6:** Set up Stripe webhook (optional)
  - Create webhook endpoint
  - Configure automatic license generation
  - Test with Stripe test mode

- [ ] **Step 7:** Create customer documentation
  - How to enter license key
  - What to do if license expires
  - How to contact support

## Example License Keys

### Trial License (30 days, all features):
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZb3VyQ29tcGFueSIsInN1YiI6InRyaWFsQGV4YW1wbGUuY29tIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjE3MDI1OTIwMDAsImp0aSI6ImFiYzEyMy0uLi4iLCJjdXN0b21lcl9uYW1lIjoiVHJpYWwgVXNlciIsImN1c3RvbWVyX2VtYWlsIjoidHJpYWxAZXhhbXBsZS5jb20iLCJmZWF0dXJlcyI6WyJhbGwiXSwibGljZW5zZV90eXBlIjoidHJpYWwifQ.signature...
```

### Commercial License (1 year, specific features):
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZb3VyQ29tcGFueSIsInN1YiI6ImN1c3RvbWVyQGV4YW1wbGUuY29tIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjE3MzE1MzYwMDAsImp0aSI6ImRlZjQ1Ni0uLi4iLCJjdXN0b21lcl9uYW1lIjoiQWNtZSBDb3JwIiwiY3VzdG9tZXJfZW1haWwiOiJjdXN0b21lckBleGFtcGxlLmNvbSIsImZlYXR1cmVzIjpbImFpX2ludm9pY2UiLCJhaV9leHBlbnNlIl0sIm1heF91c2VycyI6MTAsImxpY2Vuc2VfdHlwZSI6ImNvbW1lcmNpYWwifQ.signature...
```

## Troubleshooting

### "Invalid signature" error
- Check that public key in app matches private key used for signing
- Ensure license key wasn't modified or truncated
- Verify JWT library versions match

### "License expired" error
- Check system clock on customer's server
- Verify expiration date in license
- Generate new license with extended duration

### "Feature not available" error
- Verify feature ID matches exactly
- Check license includes the requested feature
- Ensure license is activated in the app

## Support Resources

- **Documentation:** https://yourcompany.com/docs/licensing
- **Support Email:** licenses@yourcompany.com
- **License Portal:** https://licenses.yourcompany.com

## Conclusion

You now have a complete system for generating and managing license keys:

1. ✅ Cryptographically secure (RSA signatures)
2. ✅ Easy to generate (CLI + Web tools)
3. ✅ Automated with payments (Stripe integration)
4. ✅ Customer-friendly (simple copy/paste)
5. ✅ Offline-capable (no constant internet required)
6. ✅ Scalable (can handle thousands of licenses)

This is the same approach used by GitLab, Sentry, and other successful self-hosted products generating millions in revenue.
