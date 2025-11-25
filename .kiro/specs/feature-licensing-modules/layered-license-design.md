# Layered License Design

## Overview

This document describes a **tiered licensing system** that allows customers to purchase different license tiers (Starter, Professional, Enterprise) with progressively more features. This replaces the current binary "feature enabled/disabled" model with a more flexible tier-based approach.

## Current State vs. Proposed State

### Current State
- Binary feature licensing: each feature is either enabled or disabled
- License keys contain a list of individual features
- No concept of "plans" or "tiers"
- Customers must purchase each feature individually

### Proposed State
- **Tiered licensing**: Starter → Professional → Enterprise → Ultimate
- Each tier includes all features from lower tiers (cumulative)
- License keys specify a tier level
- Customers purchase a tier, not individual features
- Optional add-ons for specialized features

## License Tier Structure

### Tier 1: Starter (Free Trial / Entry Level)
**Target**: Small businesses, freelancers, basic usage

**Included Features**:
- Core invoice management
- Core expense management
- Basic client management
- Basic reporting
- Cloud storage (limited)
- Mobile app access

**Limitations**:
- Up to 100 invoices/month
- Up to 50 expenses/month
- 1 user
- 1GB storage

### Tier 2: Professional
**Target**: Growing businesses, teams

**Includes**: All Starter features, plus:
- AI Invoice Processing (`ai_invoice`)
- AI Expense Processing (`ai_expense`)
- Batch File Processing (`batch_processing`)
- Advanced Reporting (`reporting`)
- Advanced Search (`advanced_search`)
- Inventory Management (`inventory`)

**Limitations**:
- Up to 1,000 invoices/month
- Up to 500 expenses/month
- Up to 5 users
- 10GB storage

### Tier 3: Enterprise
**Target**: Large organizations, complex workflows

**Includes**: All Professional features, plus:
- AI Bank Statement Processing (`ai_bank_statement`)
- Approval Workflows (`approvals`)
- SSO Authentication (`sso`)
- Slack Integration (`slack_integration`)
- Tax Service Integration (`tax_integration`)
- Priority support

**Limitations**:
- Unlimited invoices
- Unlimited expenses
- Up to 50 users
- 100GB storage

### Tier 4: Ultimate (Optional)
**Target**: Enterprise with custom needs

**Includes**: All Enterprise features, plus:
- AI Chat Assistant (`ai_chat`)
- Custom integrations
- Dedicated support
- SLA guarantees
- White-label options

**Limitations**:
- Unlimited everything
- Unlimited users
- Unlimited storage

## Add-On Modules (Optional)

Some features can be purchased as add-ons to any tier:

- **AI Chat Assistant** - Add to Professional or Enterprise
- **Custom Integration** - Add to any tier
- **Additional Storage** - Add to any tier
- **Additional Users** - Add to any tier

## Data Model Changes

### License Payload Structure

**Current Structure**:
```json
{
  "customer_email": "customer@example.com",
  "customer_name": "John Doe",
  "organization_name": "Acme Corp",
  "features": ["ai_invoice", "ai_expense", "batch_processing"],
  "exp": 1735689600
}
```

**New Structure**:
```json
{
  "customer_email": "customer@example.com",
  "customer_name": "John Doe",
  "organization_name": "Acme Corp",
  "license_tier": "professional",
  "add_ons": ["ai_chat"],
  "limits": {
    "max_invoices_per_month": 1000,
    "max_expenses_per_month": 500,
    "max_users": 5,
    "max_storage_gb": 10
  },
  "exp": 1735689600,
  "iat": 1704153600
}
```

### Database Schema Updates

```sql
-- Add tier information to installation_info table
ALTER TABLE installation_info ADD COLUMN license_tier VARCHAR(50);
ALTER TABLE installation_info ADD COLUMN license_add_ons JSON;
ALTER TABLE installation_info ADD COLUMN license_limits JSON;

-- Create tier definitions table
CREATE TABLE license_tiers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL,
    included_features JSON NOT NULL,
    default_limits JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create usage tracking table for limits
CREATE TABLE usage_tracking (
    id SERIAL PRIMARY KEY,
    installation_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value INTEGER NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(installation_id, metric_name, period_start)
);
```

## Implementation Architecture

### 1. Tier Configuration Service

```python
# api/services/tier_config_service.py

class TierConfigService:
    """Service for managing license tier definitions and feature mappings"""
    
    TIERS = {
        'starter': {
            'name': 'Starter',
            'display_name': 'Starter Plan',
            'description': 'Perfect for freelancers and small businesses',
            'sort_order': 1,
            'features': [],  # Core features only
            'limits': {
                'max_invoices_per_month': 100,
                'max_expenses_per_month': 50,
                'max_users': 1,
                'max_storage_gb': 1
            }
        },
        'professional': {
            'name': 'Professional',
            'display_name': 'Professional Plan',
            'description': 'For growing businesses and teams',
            'sort_order': 2,
            'features': [
                'ai_invoice',
                'ai_expense',
                'batch_processing',
                'reporting',
                'advanced_search',
                'inventory'
            ],
            'limits': {
                'max_invoices_per_month': 1000,
                'max_expenses_per_month': 500,
                'max_users': 5,
                'max_storage_gb': 10
            }
        },
        'enterprise': {
            'name': 'Enterprise',
            'display_name': 'Enterprise Plan',
            'description': 'For large organizations with complex needs',
            'sort_order': 3,
            'features': [
                'ai_invoice',
                'ai_expense',
                'ai_bank_statement',
                'batch_processing',
                'reporting',
                'advanced_search',
                'inventory',
                'approvals',
                'sso',
                'slack_integration',
                'tax_integration'
            ],
            'limits': {
                'max_invoices_per_month': -1,  # -1 = unlimited
                'max_expenses_per_month': -1,
                'max_users': 50,
                'max_storage_gb': 100
            }
        },
        'ultimate': {
            'name': 'Ultimate',
            'display_name': 'Ultimate Plan',
            'description': 'Everything included with premium support',
            'sort_order': 4,
            'features': [
                'ai_invoice',
                'ai_expense',
                'ai_bank_statement',
                'ai_chat',
                'batch_processing',
                'reporting',
                'advanced_search',
                'inventory',
                'approvals',
                'sso',
                'slack_integration',
                'tax_integration'
            ],
            'limits': {
                'max_invoices_per_month': -1,
                'max_expenses_per_month': -1,
                'max_users': -1,
                'max_storage_gb': -1
            }
        }
    }
    
    @classmethod
    def get_tier_features(cls, tier_id: str) -> List[str]:
        """Get all features included in a tier"""
        if tier_id not in cls.TIERS:
            return []
        return cls.TIERS[tier_id]['features']
    
    @classmethod
    def get_tier_limits(cls, tier_id: str) -> Dict[str, int]:
        """Get usage limits for a tier"""
        if tier_id not in cls.TIERS:
            return {}
        return cls.TIERS[tier_id]['limits']
    
    @classmethod
    def is_feature_in_tier(cls, feature_id: str, tier_id: str) -> bool:
        """Check if a feature is included in a specific tier"""
        features = cls.get_tier_features(tier_id)
        return feature_id in features
    
    @classmethod
    def get_tier_for_feature(cls, feature_id: str) -> Optional[str]:
        """Get the minimum tier that includes a feature"""
        for tier_id in ['starter', 'professional', 'enterprise', 'ultimate']:
            if cls.is_feature_in_tier(feature_id, tier_id):
                return tier_id
        return None
    
    @classmethod
    def compare_tiers(cls, tier1: str, tier2: str) -> int:
        """
        Compare two tiers.
        Returns: -1 if tier1 < tier2, 0 if equal, 1 if tier1 > tier2
        """
        if tier1 not in cls.TIERS or tier2 not in cls.TIERS:
            return 0
        
        order1 = cls.TIERS[tier1]['sort_order']
        order2 = cls.TIERS[tier2]['sort_order']
        
        if order1 < order2:
            return -1
        elif order1 > order2:
            return 1
        else:
            return 0
```

### 2. Enhanced License Service

```python
# api/services/license_service.py (additions)

class LicenseService:
    
    def get_enabled_features(self) -> List[str]:
        """
        Get list of licensed features based on tier + add-ons.
        """
        installation = self._get_or_create_installation()
        
        # If in trial or grace period, return professional tier features
        if self.is_trial_active() or self.is_in_grace_period():
            return TierConfigService.get_tier_features('professional')
        
        # If licensed, return tier features + add-ons
        if installation.license_status == "active":
            # Check if license is expired
            if installation.license_expires_at:
                expires_at = installation.license_expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > expires_at:
                    installation.license_status = "expired"
                    self.db.commit()
                    return []
            
            # Get features from tier
            tier = installation.license_tier or 'starter'
            features = TierConfigService.get_tier_features(tier)
            
            # Add features from add-ons
            if installation.license_add_ons:
                features.extend(installation.license_add_ons)
            
            return list(set(features))  # Remove duplicates
        
        # No active license or trial - return starter features
        return TierConfigService.get_tier_features('starter')
    
    def get_license_tier(self) -> str:
        """Get the current license tier"""
        installation = self._get_or_create_installation()
        
        if self.is_trial_active() or self.is_in_grace_period():
            return 'professional'  # Trial gets professional features
        
        if installation.license_status == "active":
            return installation.license_tier or 'starter'
        
        return 'starter'
    
    def get_license_limits(self) -> Dict[str, int]:
        """Get usage limits for current license"""
        installation = self._get_or_create_installation()
        
        tier = self.get_license_tier()
        limits = TierConfigService.get_tier_limits(tier)
        
        # Override with custom limits from license if present
        if installation.license_limits:
            limits.update(installation.license_limits)
        
        return limits
    
    def check_usage_limit(self, metric_name: str, current_value: int) -> Dict[str, Any]:
        """
        Check if current usage is within limits.
        
        Returns:
            {
                "within_limit": bool,
                "current_value": int,
                "limit": int,
                "percentage_used": float
            }
        """
        limits = self.get_license_limits()
        limit = limits.get(metric_name, -1)
        
        # -1 means unlimited
        if limit == -1:
            return {
                "within_limit": True,
                "current_value": current_value,
                "limit": -1,
                "percentage_used": 0.0
            }
        
        within_limit = current_value < limit
        percentage = (current_value / limit * 100) if limit > 0 else 0
        
        return {
            "within_limit": within_limit,
            "current_value": current_value,
            "limit": limit,
            "percentage_used": round(percentage, 2)
        }
```

### 3. Usage Tracking Service

```python
# api/services/usage_tracking_service.py

class UsageTrackingService:
    """Service for tracking usage metrics against license limits"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_current_period(self) -> tuple[datetime, datetime]:
        """Get current billing period (month)"""
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get last day of month
        if now.month == 12:
            period_end = period_start.replace(year=now.year + 1, month=1)
        else:
            period_end = period_start.replace(month=now.month + 1)
        
        return period_start, period_end
    
    def get_usage(self, installation_id: str, metric_name: str) -> int:
        """Get current usage for a metric in the current period"""
        period_start, period_end = self.get_current_period()
        
        usage = self.db.query(UsageTracking).filter(
            UsageTracking.installation_id == installation_id,
            UsageTracking.metric_name == metric_name,
            UsageTracking.period_start == period_start.date()
        ).first()
        
        return usage.metric_value if usage else 0
    
    def increment_usage(self, installation_id: str, metric_name: str, amount: int = 1):
        """Increment usage counter for a metric"""
        period_start, period_end = self.get_current_period()
        
        usage = self.db.query(UsageTracking).filter(
            UsageTracking.installation_id == installation_id,
            UsageTracking.metric_name == metric_name,
            UsageTracking.period_start == period_start.date()
        ).first()
        
        if usage:
            usage.metric_value += amount
        else:
            usage = UsageTracking(
                installation_id=installation_id,
                metric_name=metric_name,
                metric_value=amount,
                period_start=period_start.date(),
                period_end=period_end.date()
            )
            self.db.add(usage)
        
        self.db.commit()
    
    def check_limit(
        self,
        installation_id: str,
        metric_name: str,
        license_service: LicenseService
    ) -> Dict[str, Any]:
        """Check if usage is within limits"""
        current_usage = self.get_usage(installation_id, metric_name)
        return license_service.check_usage_limit(metric_name, current_usage)
```

### 4. Enhanced Feature Gate with Limits

```python
# api/utils/feature_gate.py (additions)

def require_usage_limit(metric_name: str, error_message: Optional[str] = None):
    """
    Decorator to check usage limits before allowing operation.
    
    Usage:
        @router.post("/invoices")
        @require_usage_limit("max_invoices_per_month")
        async def create_invoice(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            db: Optional[Session] = kwargs.get('db')
            close_db = False
            
            if db is None:
                for arg in args:
                    if isinstance(arg, Session):
                        db = arg
                        break
            
            if db is None:
                db = next(get_db())
                close_db = True
            
            try:
                license_service = LicenseService(db)
                usage_service = UsageTrackingService(db)
                
                installation = license_service._get_or_create_installation()
                limit_check = usage_service.check_limit(
                    installation.installation_id,
                    metric_name,
                    license_service
                )
                
                if not limit_check["within_limit"]:
                    tier = license_service.get_license_tier()
                    message = error_message or (
                        f"You have reached your {metric_name} limit "
                        f"({limit_check['current_value']}/{limit_check['limit']}). "
                        f"Please upgrade your plan to continue."
                    )
                    
                    raise HTTPException(
                        status_code=402,
                        detail={
                            "error": "USAGE_LIMIT_EXCEEDED",
                            "message": message,
                            "metric": metric_name,
                            "current_usage": limit_check["current_value"],
                            "limit": limit_check["limit"],
                            "current_tier": tier,
                            "upgrade_required": True
                        }
                    )
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Increment usage after successful operation
                usage_service.increment_usage(
                    installation.installation_id,
                    metric_name
                )
                
                return result
                
            finally:
                if close_db:
                    db.close()
        
        return async_wrapper
    
    return decorator
```

### 5. API Endpoints for Tier Information

```python
# api/routers/license.py (additions)

@router.get("/tiers")
async def get_available_tiers():
    """Get all available license tiers"""
    tiers = []
    for tier_id, tier_data in TierConfigService.TIERS.items():
        tiers.append({
            "id": tier_id,
            "name": tier_data['name'],
            "display_name": tier_data['display_name'],
            "description": tier_data['description'],
            "features": tier_data['features'],
            "limits": tier_data['limits']
        })
    
    # Sort by sort_order
    tiers.sort(key=lambda x: TierConfigService.TIERS[x['id']]['sort_order'])
    
    return {"tiers": tiers}


@router.get("/current-tier")
async def get_current_tier(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current license tier and usage information"""
    license_service = LicenseService(db)
    usage_service = UsageTrackingService(db)
    
    installation = license_service._get_or_create_installation()
    tier = license_service.get_license_tier()
    limits = license_service.get_license_limits()
    
    # Get current usage for all metrics
    usage = {}
    for metric_name in limits.keys():
        current_usage = usage_service.get_usage(
            installation.installation_id,
            metric_name
        )
        limit_check = license_service.check_usage_limit(metric_name, current_usage)
        usage[metric_name] = limit_check
    
    return {
        "tier": tier,
        "tier_info": TierConfigService.TIERS.get(tier),
        "limits": limits,
        "usage": usage,
        "add_ons": installation.license_add_ons or []
    }


@router.get("/upgrade-options")
async def get_upgrade_options(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available upgrade options from current tier"""
    license_service = LicenseService(db)
    current_tier = license_service.get_license_tier()
    
    # Get higher tiers
    available_tiers = []
    for tier_id, tier_data in TierConfigService.TIERS.items():
        if TierConfigService.compare_tiers(tier_id, current_tier) > 0:
            available_tiers.append({
                "id": tier_id,
                "name": tier_data['display_name'],
                "description": tier_data['description'],
                "features": tier_data['features'],
                "limits": tier_data['limits']
            })
    
    available_tiers.sort(key=lambda x: TierConfigService.TIERS[x['id']]['sort_order'])
    
    return {
        "current_tier": current_tier,
        "upgrade_options": available_tiers
    }
```

## Frontend Integration

### Tier Display Component

```typescript
// ui/src/components/TierBadge.tsx
interface TierBadgeProps {
  tier: 'starter' | 'professional' | 'enterprise' | 'ultimate';
}

export const TierBadge: React.FC<TierBadgeProps> = ({ tier }) => {
  const tierColors = {
    starter: 'bg-gray-100 text-gray-800',
    professional: 'bg-blue-100 text-blue-800',
    enterprise: 'bg-purple-100 text-purple-800',
    ultimate: 'bg-gold-100 text-gold-800'
  };
  
  const tierLabels = {
    starter: 'Starter',
    professional: 'Professional',
    enterprise: 'Enterprise',
    ultimate: 'Ultimate'
  };
  
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${tierColors[tier]}`}>
      {tierLabels[tier]}
    </span>
  );
};
```

### Usage Meter Component

```typescript
// ui/src/components/UsageMeter.tsx
interface UsageMeterProps {
  label: string;
  current: number;
  limit: number;
  unit?: string;
}

export const UsageMeter: React.FC<UsageMeterProps> = ({
  label,
  current,
  limit,
  unit = ''
}) => {
  const percentage = limit === -1 ? 0 : (current / limit) * 100;
  const isUnlimited = limit === -1;
  const isNearLimit = percentage > 80;
  const isOverLimit = percentage >= 100;
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className={isOverLimit ? 'text-red-600' : isNearLimit ? 'text-yellow-600' : ''}>
          {isUnlimited ? (
            `${current} ${unit} (Unlimited)`
          ) : (
            `${current} / ${limit} ${unit}`
          )}
        </span>
      </div>
      {!isUnlimited && (
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              isOverLimit ? 'bg-red-500' : isNearLimit ? 'bg-yellow-500' : 'bg-blue-500'
            }`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
};
```

### Tier Comparison Page

```typescript
// ui/src/pages/TierComparison.tsx
export const TierComparison = () => {
  const [tiers, setTiers] = useState([]);
  const [currentTier, setCurrentTier] = useState(null);
  
  useEffect(() => {
    // Fetch available tiers
    api.get('/license/tiers').then(res => setTiers(res.data.tiers));
    api.get('/license/current-tier').then(res => setCurrentTier(res.data.tier));
  }, []);
  
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Choose Your Plan</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {tiers.map(tier => (
          <div
            key={tier.id}
            className={`border rounded-lg p-6 ${
              tier.id === currentTier ? 'border-blue-500 ring-2 ring-blue-200' : ''
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">{tier.display_name}</h2>
              {tier.id === currentTier && (
                <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  Current
                </span>
              )}
            </div>
            
            <p className="text-gray-600 mb-6">{tier.description}</p>
            
            <div className="space-y-4 mb-6">
              <h3 className="font-semibold">Features:</h3>
              <ul className="space-y-2">
                {tier.features.map(feature => (
                  <li key={feature} className="flex items-center text-sm">
                    <Check className="w-4 h-4 text-green-500 mr-2" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="space-y-2 mb-6">
              <h3 className="font-semibold">Limits:</h3>
              {Object.entries(tier.limits).map(([key, value]) => (
                <div key={key} className="text-sm text-gray-600">
                  {key}: {value === -1 ? 'Unlimited' : value}
                </div>
              ))}
            </div>
            
            {tier.id !== currentTier && (
              <button className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600">
                Upgrade to {tier.display_name}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

## Migration Strategy

### Phase 1: Add Tier Support (Week 1)
1. Create `TierConfigService` with tier definitions
2. Add tier columns to database
3. Update `LicenseService` to support tiers
4. Maintain backward compatibility with feature-list licenses

### Phase 2: Usage Tracking (Week 2)
1. Create `UsageTrackingService`
2. Add usage tracking tables
3. Implement `@require_usage_limit` decorator
4. Add usage tracking to invoice/expense creation

### Phase 3: License Generation Updates (Week 3)
1. Update license generator to create tier-based licenses
2. Add tier selection to license purchase flow
3. Update Stripe integration with tier pricing

### Phase 4: Frontend Updates (Week 4)
1. Create tier display components
2. Add usage meters to dashboard
3. Create tier comparison page
4. Add upgrade prompts

### Phase 5: Migration & Testing (Week 5)
1. Migrate existing licenses to tier system
2. Test all tier transitions
3. Test usage limits
4. Documentation updates

## Pricing Strategy Example

| Tier | Monthly Price | Annual Price | Target |
|------|--------------|--------------|--------|
| Starter | Free | Free | Trial/Hobby |
| Professional | $49/mo | $490/yr (2 months free) | Small Business |
| Enterprise | $199/mo | $1,990/yr (2 months free) | Large Business |
| Ultimate | $499/mo | $4,990/yr (2 months free) | Enterprise |

**Add-Ons**:
- AI Chat Assistant: +$29/mo
- Additional 10GB Storage: +$10/mo
- Additional 5 Users: +$25/mo

## Benefits of Layered Licensing

1. **Simpler for Customers**: Choose a tier instead of individual features
2. **Upsell Opportunities**: Clear upgrade path from Starter → Ultimate
3. **Predictable Revenue**: Tier-based pricing is easier to forecast
4. **Feature Bundling**: Group related features logically
5. **Usage Limits**: Enforce fair usage policies
6. **Flexibility**: Add-ons allow customization within tiers

## Summary

This layered license design provides:
- **4 clear tiers** with progressive feature sets
- **Usage limits** to enforce fair usage
- **Add-on modules** for customization
- **Backward compatibility** with existing feature-based licenses
- **Clear upgrade paths** for customers
- **Usage tracking** for limit enforcement

The system maintains the flexibility of the current design while adding the structure and simplicity of tiered pricing.
