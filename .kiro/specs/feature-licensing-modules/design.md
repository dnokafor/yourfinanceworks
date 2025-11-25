# Feature Modularization Design Document

## Overview

This document describes how to hide/enable code for different feature modules at multiple levels:
1. **Backend API Level** - Control which endpoints are accessible
2. **Service Level** - Control which services execute
3. **Frontend UI Level** - Control which UI elements are visible
4. **Database Level** - Control which features are stored per tenant
5. **Build Level** - Optionally exclude code from builds

## Architecture

### High-Level Flow

```
User Request → Feature Check → Execute/Block
     ↓              ↓
  Frontend      Backend API
     ↓              ↓
  UI Hidden    Endpoint Gated
```

### Component Layers

```
┌─────────────────────────────────────────┐
│         Frontend (React/Vue)            │
│  - Feature Context Provider             │
│  - Conditional Rendering                │
│  - Route Guards                         │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Backend API (FastAPI)           │
│  - Feature Gate Decorator               │
│  - Router Registration Control          │
│  - Middleware Checks                    │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Service Layer                   │
│  - Feature Config Service               │
│  - Conditional Service Execution        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Database                        │
│  - Feature Flags Table                  │
│  - Tenant Feature Mapping               │
└─────────────────────────────────────────┘
```

## Data Models

### Feature Configuration Table

```sql
CREATE TABLE feature_modules (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),  -- 'ai', 'integration', 'advanced'
    is_core BOOLEAN DEFAULT FALSE,
    dependencies JSON,  -- ['feature_id1', 'feature_id2']
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tenant Feature Mapping Table

```sql
CREATE TABLE tenant_features (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    feature_id VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    enabled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    metadata JSON,
    FOREIGN KEY (feature_id) REFERENCES feature_modules(id),
    UNIQUE(tenant_id, feature_id)
);
```


## Implementation Details

### 1. Backend API Level - Feature Gates

#### A. Feature Configuration Service

```python
# api/services/feature_config_service.py
import os
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from functools import lru_cache

class FeatureConfigService:
    """Centralized service for feature availability checks"""
    
    # Feature definitions
    FEATURES = {
        'ai_invoice': {
            'name': 'AI Invoice Processing',
            'category': 'ai',
            'env_var': 'FEATURE_AI_INVOICE_ENABLED',
            'default': True
        },
        'ai_expense': {
            'name': 'AI Expense Processing',
            'category': 'ai',
            'env_var': 'FEATURE_AI_EXPENSE_ENABLED',
            'default': True
        },
        'tax_integration': {
            'name': 'Tax Service Integration',
            'category': 'integration',
            'env_var': 'FEATURE_TAX_INTEGRATION_ENABLED',
            'default': False
        },
        'slack_integration': {
            'name': 'Slack Integration',
            'category': 'integration',
            'env_var': 'FEATURE_SLACK_INTEGRATION_ENABLED',
            'default': False
        },
        'batch_processing': {
            'name': 'Batch File Processing',
            'category': 'advanced',
            'env_var': 'FEATURE_BATCH_PROCESSING_ENABLED',
            'default': True
        },
        # Add more features...
    }
    
    @classmethod
    @lru_cache(maxsize=128)
    def is_enabled(cls, feature_id: str, tenant_id: Optional[str] = None) -> bool:
        """
        Check if a feature is enabled.
        Priority: Database > Environment Variable > Default
        """
        if feature_id not in cls.FEATURES:
            return False
        
        feature = cls.FEATURES[feature_id]
        
        # Check database if tenant_id provided
        if tenant_id:
            db_enabled = cls._check_database(feature_id, tenant_id)
            if db_enabled is not None:
                return db_enabled
        
        # Check environment variable
        env_var = feature.get('env_var')
        if env_var:
            env_value = os.getenv(env_var)
            if env_value is not None:
                return env_value.lower() in ('true', '1', 'yes')
        
        # Return default
        return feature.get('default', False)
    
    @classmethod
    def _check_database(cls, feature_id: str, tenant_id: str) -> Optional[bool]:
        """Check feature status in database"""
        # Implementation will query tenant_features table
        pass
    
    @classmethod
    def get_enabled_features(cls, tenant_id: Optional[str] = None) -> Dict[str, bool]:
        """Get all features and their enabled status"""
        return {
            feature_id: cls.is_enabled(feature_id, tenant_id)
            for feature_id in cls.FEATURES.keys()
        }
```


#### B. Feature Gate Decorator

```python
# api/utils/feature_gate.py
from functools import wraps
from fastapi import HTTPException
from services.feature_config_service import FeatureConfigService
from models.database import get_tenant_context

def require_feature(feature_id: str, error_message: str = None):
    """
    Decorator to gate API endpoints behind feature checks.
    
    Usage:
        @router.post("/ai/chat")
        @require_feature("ai_chat")
        async def chat_endpoint(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get tenant from context
            tenant_id = get_tenant_context()
            
            # Check if feature is enabled
            if not FeatureConfigService.is_enabled(feature_id, tenant_id):
                message = error_message or f"Feature '{feature_id}' is not enabled"
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "FEATURE_NOT_ENABLED",
                        "message": message,
                        "feature_id": feature_id,
                        "upgrade_required": True
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def feature_enabled(feature_id: str, tenant_id: Optional[str] = None) -> bool:
    """
    Helper function to check feature status in code.
    
    Usage:
        if feature_enabled("ai_invoice"):
            # Execute AI processing
        else:
            # Use fallback method
    """
    return FeatureConfigService.is_enabled(feature_id, tenant_id)
```


#### C. Usage in Routers

```python
# api/routers/ai.py
from fastapi import APIRouter, Depends
from utils.feature_gate import require_feature, feature_enabled
from routers.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

# Method 1: Decorator-based gating (recommended)
@router.post("/chat")
@require_feature("ai_chat")
async def chat_with_ai(
    request: ChatRequest,
    current_user = Depends(get_current_user)
):
    # This endpoint only executes if ai_chat is enabled
    return await process_chat(request)


# Method 2: Conditional execution in code
@router.post("/process-invoice")
async def process_invoice(
    file: UploadFile,
    current_user = Depends(get_current_user)
):
    if feature_enabled("ai_invoice"):
        # Use AI processing
        result = await ai_process_invoice(file)
    else:
        # Use basic processing
        result = await basic_process_invoice(file)
    
    return result


# Method 3: Early return with error
@router.get("/invoice-ocr-status")
async def get_ocr_status(current_user = Depends(get_current_user)):
    if not feature_enabled("ai_invoice"):
        raise HTTPException(
            status_code=403,
            detail="AI Invoice Processing is not enabled"
        )
    
    return {"status": "enabled", "provider": "openai"}
```


#### D. Conditional Router Registration

```python
# api/main.py
from fastapi import FastAPI
from services.feature_config_service import FeatureConfigService

app = FastAPI()

# Core routers (always included)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(clients.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")

# Conditional routers (only if feature enabled)
if FeatureConfigService.is_enabled("ai_chat"):
    app.include_router(ai.router, prefix="/api/v1")

if FeatureConfigService.is_enabled("tax_integration"):
    app.include_router(tax_integration.router, prefix="/api/v1")

if FeatureConfigService.is_enabled("slack_integration"):
    app.include_router(slack_simplified.router, prefix="/api/v1")

if FeatureConfigService.is_enabled("batch_processing"):
    app.include_router(batch_processing.router, prefix="/api/v1")

if FeatureConfigService.is_enabled("inventory"):
    app.include_router(inventory.router, prefix="/api/v1")

# Alternative: Dynamic registration
FEATURE_ROUTERS = {
    "ai_chat": (ai.router, "/api/v1"),
    "tax_integration": (tax_integration.router, "/api/v1"),
    "slack_integration": (slack_simplified.router, "/api/v1"),
    "batch_processing": (batch_processing.router, "/api/v1"),
    "inventory": (inventory.router, "/api/v1"),
}

for feature_id, (router, prefix) in FEATURE_ROUTERS.items():
    if FeatureConfigService.is_enabled(feature_id):
        app.include_router(router, prefix=prefix)
```


### 2. Service Level - Conditional Execution

```python
# api/services/invoice_service.py
from utils.feature_gate import feature_enabled

class InvoiceService:
    
    async def process_invoice(self, file_path: str, db: Session):
        """Process invoice with optional AI enhancement"""
        
        # Basic extraction (always available)
        basic_data = self._extract_basic_data(file_path)
        
        # AI enhancement (only if enabled)
        if feature_enabled("ai_invoice"):
            try:
                from services.invoice_ai_service import InvoiceAIService
                ai_service = InvoiceAIService(db)
                ai_data = await ai_service.extract_invoice_data(file_path)
                
                # Merge AI data with basic data
                return {**basic_data, **ai_data, "ai_enhanced": True}
            except Exception as e:
                logger.warning(f"AI processing failed, using basic data: {e}")
                return {**basic_data, "ai_enhanced": False}
        
        return {**basic_data, "ai_enhanced": False}
    
    
    def save_to_tax_service(self, invoice_data: dict):
        """Optionally sync to tax service"""
        
        if not feature_enabled("tax_integration"):
            logger.debug("Tax integration disabled, skipping sync")
            return None
        
        from services.tax_integration_service import TaxIntegrationService
        tax_service = TaxIntegrationService()
        return tax_service.send_invoice(invoice_data)
```


### 3. Frontend UI Level - Conditional Rendering

#### A. Feature Context Provider (React)

```typescript
// ui/src/contexts/FeatureContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface FeatureFlags {
  ai_invoice: boolean;
  ai_expense: boolean;
  ai_chat: boolean;
  tax_integration: boolean;
  slack_integration: boolean;
  batch_processing: boolean;
  inventory: boolean;
  approvals: boolean;
  reporting: boolean;
  [key: string]: boolean;
}

interface FeatureContextType {
  features: FeatureFlags;
  isFeatureEnabled: (featureId: string) => boolean;
  loading: boolean;
}

const FeatureContext = createContext<FeatureContextType | undefined>(undefined);

export const FeatureProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [features, setFeatures] = useState<FeatureFlags>({} as FeatureFlags);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch enabled features from backend
    const fetchFeatures = async () => {
      try {
        const response = await api.get('/features/enabled');
        setFeatures(response.data);
      } catch (error) {
        console.error('Failed to fetch feature flags:', error);
        // Set all to false on error
        setFeatures({
          ai_invoice: false,
          ai_expense: false,
          ai_chat: false,
          tax_integration: false,
          slack_integration: false,
          batch_processing: false,
          inventory: false,
          approvals: false,
          reporting: false,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchFeatures();
  }, []);

  const isFeatureEnabled = (featureId: string): boolean => {
    return features[featureId] === true;
  };

  return (
    <FeatureContext.Provider value={{ features, isFeatureEnabled, loading }}>
      {children}
    </FeatureContext.Provider>
  );
};

export const useFeatures = () => {
  const context = useContext(FeatureContext);
  if (!context) {
    throw new Error('useFeatures must be used within FeatureProvider');
  }
  return context;
};
```


#### B. Feature Gate Component

```typescript
// ui/src/components/FeatureGate.tsx
import React from 'react';
import { useFeatures } from '@/contexts/FeatureContext';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Lock } from 'lucide-react';

interface FeatureGateProps {
  feature: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgradePrompt?: boolean;
}

export const FeatureGate: React.FC<FeatureGateProps> = ({
  feature,
  children,
  fallback,
  showUpgradePrompt = false
}) => {
  const { isFeatureEnabled, loading } = useFeatures();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isFeatureEnabled(feature)) {
    if (showUpgradePrompt) {
      return (
        <Alert>
          <Lock className="h-4 w-4" />
          <AlertDescription>
            This feature requires an upgrade. Contact your administrator.
          </AlertDescription>
        </Alert>
      );
    }
    return fallback ? <>{fallback}</> : null;
  }

  return <>{children}</>;
};
```


#### C. Usage in Components

```typescript
// ui/src/pages/Invoices.tsx
import { FeatureGate } from '@/components/FeatureGate';
import { useFeatures } from '@/contexts/FeatureContext';

export const InvoicesPage = () => {
  const { isFeatureEnabled } = useFeatures();

  return (
    <div>
      <h1>Invoices</h1>
      
      {/* Method 1: Using FeatureGate component */}
      <FeatureGate feature="ai_invoice">
        <button onClick={handleAIProcess}>
          AI Process Invoice
        </button>
      </FeatureGate>
      
      {/* Method 2: Using hook directly */}
      {isFeatureEnabled('batch_processing') && (
        <button onClick={handleBatchUpload}>
          Batch Upload
        </button>
      )}
      
      {/* Method 3: With upgrade prompt */}
      <FeatureGate
        feature="inventory" 
        showUpgradePrompt={true}
      >
        <InventorySection />
      </FeatureGate>
      
      {/* Method 4: With fallback */}
      <FeatureGate
        feature="ai_expense"
        fallback={<BasicExpenseForm />}
      >
        <AIEnhancedExpenseForm />
      </FeatureGate>
    </div>
  );
};
```


#### D. Navigation Menu Filtering

```typescript
// ui/src/components/Navigation.tsx
import { useFeatures } from '@/contexts/FeatureContext';

export const Navigation = () => {
  const { isFeatureEnabled } = useFeatures();

  const menuItems = [
    { path: '/invoices', label: 'Invoices', feature: null }, // Always visible
    { path: '/expenses', label: 'Expenses', feature: null },
    { path: '/clients', label: 'Clients', feature: null },
    { path: '/inventory', label: 'Inventory', feature: 'inventory' },
    { path: '/reports', label: 'Reports', feature: 'reporting' },
    { path: '/batch', label: 'Batch Processing', feature: 'batch_processing' },
    { path: '/ai-chat', label: 'AI Assistant', feature: 'ai_chat' },
  ];

  // Filter menu items based on feature availability
  const visibleItems = menuItems.filter(item => 
    !item.feature || isFeatureEnabled(item.feature)
  );

  return (
    <nav>
      {visibleItems.map(item => (
        <a key={item.path} href={item.path}>
          {item.label}
        </a>
      ))}
    </nav>
  );
};
```


### 4. API Endpoint for Feature Status

```python
# api/routers/features.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.database import get_db, get_tenant_context
from services.feature_config_service import FeatureConfigService
from routers.auth import get_current_user

router = APIRouter(prefix="/features", tags=["features"])

@router.get("/enabled")
async def get_enabled_features(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all enabled features for the current tenant.
    Used by frontend to determine UI visibility.
    """
    tenant_id = get_tenant_context()
    features = FeatureConfigService.get_enabled_features(tenant_id)
    
    return {
        "features": features,
        "tenant_id": tenant_id
    }


@router.get("/check/{feature_id}")
async def check_feature(
    feature_id: str,
    current_user = Depends(get_current_user)
):
    """Check if a specific feature is enabled"""
    tenant_id = get_tenant_context()
    enabled = FeatureConfigService.is_enabled(feature_id, tenant_id)
    
    return {
        "feature_id": feature_id,
        "enabled": enabled,
        "tenant_id": tenant_id
    }


@router.get("/available")
async def get_available_features():
    """Get list of all available features (public endpoint)"""
    return {
        "features": [
            {
                "id": feature_id,
                "name": feature_data['name'],
                "category": feature_data['category']
            }
            for feature_id, feature_data in FeatureConfigService.FEATURES.items()
        ]
    }
```


### 5. Environment Variable Configuration

```bash
# .env.features
# AI Features
FEATURE_AI_INVOICE_ENABLED=true
FEATURE_AI_EXPENSE_ENABLED=true
FEATURE_AI_BANK_STATEMENT_ENABLED=true
FEATURE_AI_CHAT_ENABLED=false

# Integration Features
FEATURE_TAX_INTEGRATION_ENABLED=false
FEATURE_SLACK_INTEGRATION_ENABLED=false
FEATURE_CLOUD_STORAGE_ENABLED=true
FEATURE_SSO_ENABLED=false

# Advanced Features
FEATURE_BATCH_PROCESSING_ENABLED=true
FEATURE_REPORTING_ENABLED=true
FEATURE_APPROVAL_WORKFLOWS_ENABLED=false
FEATURE_INVENTORY_ENABLED=false
FEATURE_ADVANCED_SEARCH_ENABLED=true
```

### 6. Database-Backed Feature Management (Optional)

```python
# api/routers/admin/features.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db
from models.models_per_tenant import TenantFeature
from routers.auth import get_current_user
from utils.rbac import require_admin

router = APIRouter(prefix="/admin/features", tags=["admin"])

@router.post("/enable/{tenant_id}/{feature_id}")
@require_admin
async def enable_feature(
    tenant_id: str,
    feature_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable a feature for a specific tenant"""
    
    # Check if feature exists
    if feature_id not in FeatureConfigService.FEATURES:
        raise HTTPException(404, "Feature not found")
    
    # Create or update tenant feature
    tenant_feature = db.query(TenantFeature).filter(
        TenantFeature.tenant_id == tenant_id,
        TenantFeature.feature_id == feature_id
    ).first()
    
    if tenant_feature:
        tenant_feature.enabled = True
    else:
        tenant_feature = TenantFeature(
            tenant_id=tenant_id,
            feature_id=feature_id,
            enabled=True
        )
        db.add(tenant_feature)
    
    db.commit()
    
    # Clear cache
    FeatureConfigService.is_enabled.cache_clear()
    
    return {"message": f"Feature {feature_id} enabled for tenant {tenant_id}"}


@router.post("/disable/{tenant_id}/{feature_id}")
@require_admin
async def disable_feature(
    tenant_id: str,
    feature_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable a feature for a specific tenant"""
    
    tenant_feature = db.query(TenantFeature).filter(
        TenantFeature.tenant_id == tenant_id,
        TenantFeature.feature_id == feature_id
    ).first()
    
    if tenant_feature:
        tenant_feature.enabled = False
        db.commit()
    
    # Clear cache
    FeatureConfigService.is_enabled.cache_clear()
    
    return {"message": f"Feature {feature_id} disabled for tenant {tenant_id}"}
```


## Complete Implementation Example

### Example: Modularizing AI Invoice Processing

#### 1. Backend Router

```python
# api/routers/invoices.py
from utils.feature_gate import require_feature, feature_enabled

@router.post("/{invoice_id}/ai-process")
@require_feature("ai_invoice")  # Gate the entire endpoint
async def ai_process_invoice(
    invoice_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI-powered invoice processing (requires ai_invoice feature)"""
    from services.invoice_ai_service import InvoiceAIService
    
    ai_service = InvoiceAIService(db)
    result = await ai_service.extract_invoice_data(invoice_id)
    
    return result


@router.post("/{invoice_id}/process")
async def process_invoice(
    invoice_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process invoice with optional AI enhancement"""
    
    if feature_enabled("ai_invoice"):
        # Use AI processing
        from services.invoice_ai_service import InvoiceAIService
        ai_service = InvoiceAIService(db)
        result = await ai_service.extract_invoice_data(invoice_id)
    else:
        # Use basic processing
        result = await basic_invoice_processing(invoice_id, db)
    
    return result
```

#### 2. Frontend Component

```typescript
// ui/src/pages/InvoiceDetail.tsx
import { FeatureGate } from '@/components/FeatureGate';
import { useFeatures } from '@/contexts/FeatureContext';

export const InvoiceDetail = ({ invoiceId }) => {
  const { isFeatureEnabled } = useFeatures();

  const handleProcess = async () => {
    if (isFeatureEnabled('ai_invoice')) {
      // Call AI endpoint
      await api.post(`/invoices/${invoiceId}/ai-process`);
    } else {
      // Call basic endpoint
      await api.post(`/invoices/${invoiceId}/process`);
    }
  };

  return (
    <div>
      <h1>Invoice #{invoiceId}</h1>
      
      {/* Show AI button only if feature enabled */}
      <FeatureGate feature="ai_invoice">
        <button onClick={handleProcess} className="btn-primary">
          🤖 AI Process Invoice
        </button>
      </FeatureGate>
      
      {/* Show upgrade prompt if not enabled */}
      <FeatureGate 
        feature="ai_invoice" 
        showUpgradePrompt={true}
        fallback={
          <button onClick={handleProcess} className="btn-secondary">
            Process Invoice (Basic)
          </button>
        }
      />
    </div>
  );
};
```

#### 3. Configuration

```bash
# .env
FEATURE_AI_INVOICE_ENABLED=true
```


## Advanced: Build-Time Code Exclusion (Optional)

For truly removing code from builds, you can use build-time flags:

### Python (Backend)

```python
# api/config/features.py
import os

# Build-time feature flags
BUILD_WITH_AI = os.getenv('BUILD_WITH_AI', 'true').lower() == 'true'
BUILD_WITH_TAX = os.getenv('BUILD_WITH_TAX', 'true').lower() == 'true'
BUILD_WITH_SLACK = os.getenv('BUILD_WITH_SLACK', 'true').lower() == 'true'

# Conditional imports
if BUILD_WITH_AI:
    from routers import ai
    from services import invoice_ai_service

if BUILD_WITH_TAX:
    from routers import tax_integration

if BUILD_WITH_SLACK:
    from routers import slack_simplified
```

### TypeScript (Frontend)

```typescript
// ui/vite.config.ts
import { defineConfig } from 'vite';

export default defineConfig({
  define: {
    'import.meta.env.VITE_FEATURE_AI': JSON.stringify(
      process.env.VITE_FEATURE_AI || 'true'
    ),
    'import.meta.env.VITE_FEATURE_INVENTORY': JSON.stringify(
      process.env.VITE_FEATURE_INVENTORY || 'true'
    ),
  },
});

// Usage in code
if (import.meta.env.VITE_FEATURE_AI === 'true') {
  // This code will be tree-shaken out if feature is disabled at build time
  import('./components/AIChat').then(module => {
    // ...
  });
}
```

## Testing Strategy

### 1. Feature Flag Tests

```python
# tests/test_feature_gates.py
import pytest
from utils.feature_gate import require_feature, feature_enabled

def test_feature_enabled_with_env_var(monkeypatch):
    monkeypatch.setenv('FEATURE_AI_INVOICE_ENABLED', 'true')
    assert feature_enabled('ai_invoice') == True
    
    monkeypatch.setenv('FEATURE_AI_INVOICE_ENABLED', 'false')
    assert feature_enabled('ai_invoice') == False


def test_feature_gate_decorator_blocks_disabled_feature():
    @require_feature('ai_invoice')
    async def protected_endpoint():
        return {"success": True}
    
    # Should raise HTTPException when feature disabled
    with pytest.raises(HTTPException) as exc:
        await protected_endpoint()
    
    assert exc.value.status_code == 403
```

### 2. Integration Tests

```python
# tests/test_invoice_features.py
def test_invoice_processing_with_ai_enabled(client, monkeypatch):
    monkeypatch.setenv('FEATURE_AI_INVOICE_ENABLED', 'true')
    
    response = client.post('/invoices/1/ai-process')
    assert response.status_code == 200


def test_invoice_processing_with_ai_disabled(client, monkeypatch):
    monkeypatch.setenv('FEATURE_AI_INVOICE_ENABLED', 'false')
    
    response = client.post('/invoices/1/ai-process')
    assert response.status_code == 403
    assert 'FEATURE_NOT_ENABLED' in response.json()['detail']['error']
```


## Migration Strategy

### Phase 1: Add Feature Configuration (Week 1)
1. Create `FeatureConfigService`
2. Add environment variables for all features
3. Create feature flags endpoint
4. No code changes to existing features yet

### Phase 2: Backend Gating (Week 2)
1. Create `@require_feature` decorator
2. Add feature gates to AI endpoints
3. Add feature gates to integration endpoints
4. Test with feature flags on/off

### Phase 3: Frontend Integration (Week 3)
1. Create `FeatureContext` and `FeatureProvider`
2. Create `FeatureGate` component
3. Update navigation menus
4. Update component visibility

### Phase 4: Database-Backed Features (Week 4)
1. Create database tables
2. Add admin endpoints for feature management
3. Migrate from env vars to database
4. Add tenant-specific feature control

### Phase 5: Polish & Documentation (Week 5)
1. Add upgrade prompts in UI
2. Create feature documentation
3. Add monitoring and analytics
4. Create customer-facing feature list

## Deployment Checklist

- [ ] Create database migrations for feature tables
- [ ] Add environment variables to production
- [ ] Deploy backend with feature gates
- [ ] Deploy frontend with feature context
- [ ] Test all features in enabled/disabled states
- [ ] Document feature IDs for sales team
- [ ] Create admin UI for feature management
- [ ] Set up monitoring for feature usage
- [ ] Create customer documentation

## Summary

This design provides **5 levels of code hiding/enabling**:

1. **API Level**: Endpoints blocked with `@require_feature` decorator
2. **Service Level**: Conditional execution with `feature_enabled()` checks
3. **UI Level**: Components hidden with `<FeatureGate>` or `useFeatures()` hook
4. **Router Level**: Entire routers conditionally registered in `main.py`
5. **Build Level**: Code excluded from builds (optional, advanced)

The system is:
- **Flexible**: Works with env vars, database, or both
- **Performant**: Uses caching to avoid repeated checks
- **User-Friendly**: Clear error messages and upgrade prompts
- **Developer-Friendly**: Simple decorators and hooks
- **Scalable**: Easy to add new features

You can start with just environment variables and gradually move to database-backed feature management as needed.
