# License Activation Limits - TODO

## Problem Statement

**Current Issue**: The license system allows the same license key to be used by unlimited installations. A customer could share their license key with others, or activate it on multiple servers without restriction.

**Impact**: 
- Revenue loss from license sharing
- No control over license distribution
- Cannot enforce per-installation licensing model
- No way to track active installations

## Recommended Solution: Activation Limits with Tracking

Implement a license activation tracking system that:
1. Tracks each activation in a central database
2. Enforces configurable activation limits (e.g., 1-3 activations per license)
3. Allows customers to deactivate old installations
4. Provides grace period for reactivation

## Implementation Plan

### Phase 1: License Server Database & API

#### 1.1 Create License Database Schema

**File**: `license_server/database/schema.sql` or `license_server/models.py`

```python
# Tables needed:
- licenses
  - id (primary key)
  - license_key_hash (SHA-256 of license key)
  - customer_email
  - customer_name
  - features (JSON)
  - max_activations (default: 1)
  - created_at
  - expires_at
  - status (active, suspended, expired)

- license_activations
  - id (primary key)
  - license_id (foreign key)
  - installation_id (UUID from customer installation)
  - activated_at
  - last_seen_at
  - status (active, deactivated)
  - ip_address
  - hostname
  - metadata (JSON - OS, version, etc.)

- activation_logs
  - id (primary key)
  - license_id (foreign key)
  - installation_id
  - action (activate, deactivate, validate, reject)
  - result (success, failed, limit_reached)
  - timestamp
  - ip_address
  - error_message
```

**Tasks**:
- [ ] Create database schema
- [ ] Set up database connection (SQLite for simple, PostgreSQL for production)
- [ ] Create SQLAlchemy models
- [ ] Create database migration scripts
- [ ] Add database initialization script

**Estimated Time**: 2-3 hours

---

#### 1.2 Modify License Generator to Track Licenses

**File**: `license_server/license_generator.py`

**Changes**:
- [ ] Add database integration to `LicenseGenerator`
- [ ] Store license metadata in database when generating
- [ ] Add `max_activations` parameter to `generate_license()`
- [ ] Store license key hash (not full key) for lookup
- [ ] Add method to update license metadata

**Example**:
```python
def generate_license(
    self,
    customer_email: str,
    customer_name: str,
    features: List[str],
    duration_days: int,
    max_activations: int = 1,  # NEW
    **kwargs
) -> str:
    # Generate license JWT as before
    license_key = ...
    
    # Store in database
    self._store_license_metadata(
        license_key=license_key,
        customer_email=customer_email,
        max_activations=max_activations,
        ...
    )
    
    return license_key
```

**Tasks**:
- [ ] Add database session to LicenseGenerator
- [ ] Implement `_store_license_metadata()` method
- [ ] Update CLI tool to support `--max-activations` flag
- [ ] Add license lookup methods
- [ ] Update examples and documentation

**Estimated Time**: 2-3 hours

---

#### 1.3 Create License Activation API

**File**: `license_server/api/activation_api.py` (new FastAPI app)

**Endpoints**:

```python
POST /api/v1/licenses/activate
- Request: { license_key, installation_id, metadata }
- Response: { success, message, activation_id }
- Logic:
  1. Verify license signature
  2. Check if license exists in database
  3. Check if license is expired
  4. Count current active activations
  5. If under limit, create activation record
  6. If over limit, reject with error

POST /api/v1/licenses/deactivate
- Request: { license_key, installation_id }
- Response: { success, message }
- Logic:
  1. Verify license signature
  2. Find activation record
  3. Mark as deactivated
  4. Allow reactivation on new installation

POST /api/v1/licenses/validate
- Request: { license_key, installation_id }
- Response: { valid, features, expires_at }
- Logic:
  1. Verify license signature
  2. Check activation exists and is active
  3. Update last_seen_at timestamp
  4. Return license details

GET /api/v1/licenses/{license_key_hash}/activations
- Response: { activations: [...] }
- Logic: List all activations for a license (admin only)
```

**Tasks**:
- [ ] Create FastAPI application
- [ ] Implement activation endpoint
- [ ] Implement deactivation endpoint
- [ ] Implement validation endpoint
- [ ] Add authentication (API key for admin endpoints)
- [ ] Add rate limiting
- [ ] Add logging and monitoring
- [ ] Create API documentation
- [ ] Write API tests

**Estimated Time**: 4-6 hours

---

### Phase 2: Customer-Side Integration

#### 2.1 Modify Customer License Service

**File**: `api/services/license_service.py`

**Changes**:

```python
class LicenseService:
    def activate_license(
        self,
        license_key: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Verify license signature (offline)
        verification = self.verify_license(license_key)
        if not verification["valid"]:
            return {"success": False, "error": verification["error"]}
        
        # 2. Get or create installation ID
        installation = self._get_or_create_installation()
        
        # 3. Call license server activation API (NEW)
        activation_result = self._call_activation_api(
            license_key=license_key,
            installation_id=installation.installation_id,
            metadata={
                "hostname": socket.gethostname(),
                "os": platform.system(),
                "version": APP_VERSION
            }
        )
        
        if not activation_result["success"]:
            return {
                "success": False,
                "error": activation_result["message"]
            }
        
        # 4. Store license locally (as before)
        # ...
        
        return {"success": True, ...}
    
    def _call_activation_api(self, license_key, installation_id, metadata):
        """Call license server activation API"""
        try:
            response = requests.post(
                f"{LICENSE_SERVER_URL}/api/v1/licenses/activate",
                json={
                    "license_key": license_key,
                    "installation_id": installation_id,
                    "metadata": metadata
                },
                timeout=10
            )
            return response.json()
        except requests.RequestException as e:
            # Handle offline scenario
            return {
                "success": False,
                "message": f"Cannot reach license server: {e}"
            }
```

**Tasks**:
- [ ] Add license server URL configuration
- [ ] Implement `_call_activation_api()` method
- [ ] Implement `_call_deactivation_api()` method
- [ ] Add offline fallback logic
- [ ] Handle network errors gracefully
- [ ] Add retry logic with exponential backoff
- [ ] Update error messages for users
- [ ] Add periodic validation (optional)

**Estimated Time**: 3-4 hours

---

#### 2.2 Update License Management UI

**File**: `ui/src/pages/LicenseManagement.tsx`

**Changes**:
- [ ] Show activation status (e.g., "Activation 1 of 3")
- [ ] Add "Deactivate License" button
- [ ] Show installation ID
- [ ] Handle activation limit errors with clear messaging
- [ ] Add help text about activation limits
- [ ] Show "Contact support to reset" message if needed

**Example Error Messages**:
```
"Activation limit reached (3/3 activations used). 
Please deactivate an old installation or contact support."

"This license is already activated on another installation. 
Installation ID: abc-123-def. 
Activated on: 2025-01-15"
```

**Tasks**:
- [ ] Update UI to show activation info
- [ ] Add deactivation button and confirmation dialog
- [ ] Improve error messaging
- [ ] Add loading states
- [ ] Update help documentation

**Estimated Time**: 2-3 hours

---

### Phase 3: License Server Admin Tools

#### 3.1 Create Admin Dashboard

**File**: `license_server/admin/dashboard.py` (Streamlit or simple web UI)

**Features**:
- [ ] View all licenses
- [ ] View activations per license
- [ ] Manually deactivate installations
- [ ] Reset activation limits
- [ ] View activation logs
- [ ] Search by customer email
- [ ] Export reports

**Tasks**:
- [ ] Create admin web interface
- [ ] Add authentication
- [ ] Implement license management views
- [ ] Add activation management
- [ ] Create reports and analytics
- [ ] Add audit log viewer

**Estimated Time**: 4-6 hours

---

#### 3.2 Create CLI Admin Tools

**File**: `license_server/admin_cli.py`

**Commands**:
```bash
# List activations for a license
python admin_cli.py list-activations --email customer@example.com

# Deactivate a specific installation
python admin_cli.py deactivate --license-hash abc123 --installation-id xyz789

# Reset activation limit
python admin_cli.py reset-activations --email customer@example.com

# View activation logs
python admin_cli.py logs --email customer@example.com --days 30
```

**Tasks**:
- [ ] Create CLI tool with argparse
- [ ] Implement list-activations command
- [ ] Implement deactivate command
- [ ] Implement reset-activations command
- [ ] Implement logs command
- [ ] Add confirmation prompts
- [ ] Add output formatting (table, JSON)

**Estimated Time**: 2-3 hours

---

### Phase 4: Configuration & Deployment

#### 4.1 Configuration

**File**: `license_server/config.py`

```python
# License server configuration
LICENSE_SERVER_URL = os.getenv("LICENSE_SERVER_URL", "https://licenses.yourcompany.com")
DATABASE_URL = os.getenv("LICENSE_DB_URL", "sqlite:///licenses.db")
API_KEY = os.getenv("LICENSE_API_KEY", "")  # For admin endpoints
MAX_ACTIVATIONS_DEFAULT = int(os.getenv("MAX_ACTIVATIONS_DEFAULT", "1"))
ACTIVATION_GRACE_PERIOD_DAYS = int(os.getenv("ACTIVATION_GRACE_PERIOD_DAYS", "7"))
```

**Tasks**:
- [ ] Create configuration file
- [ ] Add environment variable support
- [ ] Document all configuration options
- [ ] Create example .env file
- [ ] Add configuration validation

**Estimated Time**: 1 hour

---

#### 4.2 Deployment Guide

**File**: `license_server/DEPLOYMENT.md`

**Content**:
- [ ] Server requirements
- [ ] Database setup instructions
- [ ] API deployment (Docker, systemd, etc.)
- [ ] SSL/TLS configuration
- [ ] Monitoring and logging setup
- [ ] Backup procedures
- [ ] Security hardening checklist

**Estimated Time**: 2 hours

---

### Phase 5: Testing & Documentation

#### 5.1 Testing

**Files**: 
- `license_server/tests/test_activation_api.py`
- `license_server/tests/test_activation_limits.py`
- `api/tests/test_license_activation.py`

**Test Cases**:
- [ ] Successful activation within limit
- [ ] Rejection when limit exceeded
- [ ] Deactivation and reactivation
- [ ] Expired license rejection
- [ ] Invalid license rejection
- [ ] Network failure handling
- [ ] Concurrent activation attempts
- [ ] Installation ID uniqueness

**Estimated Time**: 3-4 hours

---

#### 5.2 Documentation

**Files to Update**:
- [ ] `license_server/README.md` - Add activation limits section
- [ ] `license_server/QUICK_START.md` - Update with new features
- [ ] `api/docs/LICENSE_MANAGEMENT_API.md` - Document new behavior
- [ ] Create `license_server/ACTIVATION_LIMITS.md` - Detailed guide
- [ ] Update customer-facing documentation

**Estimated Time**: 2-3 hours

---

## Alternative Approaches

### Option A: Simpler Offline-Only Approach

**Pros**: No license server API needed, works offline
**Cons**: Cannot enforce limits across installations, easier to bypass

**Implementation**:
1. Bind license to installation ID during first activation
2. Store binding in JWT metadata
3. Reject if installation ID doesn't match

**Estimated Time**: 4-6 hours total

---

### Option B: Hardware Fingerprinting

**Pros**: Harder to share, no server needed
**Cons**: Breaks on hardware changes, customer frustration

**Implementation**:
1. Generate hardware fingerprint (CPU, MAC, disk serial)
2. Include in license activation
3. Verify on each startup

**Estimated Time**: 6-8 hours total

---

### Option C: Periodic Phone-Home (Most Secure)

**Pros**: Can detect sharing, revoke licenses remotely
**Cons**: Requires internet, privacy concerns, complex

**Implementation**:
1. Require validation every 24-48 hours
2. Track last validation timestamp
3. Disable features if validation fails

**Estimated Time**: 8-12 hours total

---

## Recommended Timeline

### Minimal Implementation (Option A - Offline Only)
- **Time**: 1-2 days
- **Effort**: Low
- **Security**: Medium

### Full Implementation (Recommended)
- **Phase 1**: 8-12 hours (License server)
- **Phase 2**: 5-7 hours (Customer integration)
- **Phase 3**: 6-9 hours (Admin tools)
- **Phase 4**: 3 hours (Config & deployment)
- **Phase 5**: 5-7 hours (Testing & docs)
- **Total**: 27-38 hours (3-5 days)

### Enterprise Implementation (Option C)
- **Time**: 5-7 days
- **Effort**: High
- **Security**: High

---

## Decision Points

Before starting implementation, decide:

1. **Activation Limit**: How many activations per license?
   - [ ] 1 (single installation)
   - [ ] 3 (development, staging, production)
   - [ ] 5 (small team)
   - [ ] Configurable per license

2. **Deactivation Policy**: Can customers deactivate?
   - [ ] Self-service deactivation (recommended)
   - [ ] Contact support only
   - [ ] Automatic after X days inactive

3. **Offline Support**: What happens without internet?
   - [ ] Require online activation, then work offline
   - [ ] Grace period (7-30 days) before requiring revalidation
   - [ ] Fully offline after initial activation

4. **License Server Hosting**:
   - [ ] Self-hosted (VPS, AWS EC2)
   - [ ] Serverless (AWS Lambda + API Gateway)
   - [ ] Managed service (custom solution)

5. **Database Choice**:
   - [ ] SQLite (simple, single server)
   - [ ] PostgreSQL (production, scalable)
   - [ ] MySQL/MariaDB (alternative)

---

## Priority Recommendation

**Start with**: Full Implementation (Recommended approach)

**Reasoning**:
- Balances security and user experience
- Allows legitimate server migrations
- Provides admin control
- Scalable for growth
- Industry standard approach

**Quick Win**: Implement Phase 1 & 2 first (core functionality), then add admin tools later.

---

## Notes

- Keep license verification offline (JWT signature check) for performance
- Only call license server during activation/deactivation
- Cache activation status locally
- Provide clear error messages to users
- Document the process for customers
- Consider grace periods for network issues
- Log all activation attempts for security

---

## Questions to Answer

1. What's your target activation limit per license?
2. Do you want self-service deactivation?
3. Should there be a grace period for reactivation?
4. Where will you host the license server?
5. What database do you prefer?
6. Do you need periodic validation or one-time activation?

---

## Next Steps

1. Review this document and make decisions on the decision points
2. Choose implementation approach (Recommended: Full Implementation)
3. Set up license server infrastructure
4. Implement Phase 1 (database + API)
5. Test activation API
6. Implement Phase 2 (customer integration)
7. Test end-to-end flow
8. Add admin tools (Phase 3)
9. Document and deploy

---

**Created**: 2025-11-17  
**Status**: Planning  
**Priority**: High (Security Issue)  
**Estimated Effort**: 3-5 days for full implementation
