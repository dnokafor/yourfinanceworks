# Plugin Settings Migration: localStorage → Database

## Overview
Migrated plugin settings from browser localStorage to persistent database storage. This ensures plugin configurations survive browser cache clears and work consistently across devices.

## Changes Made

### 1. Database Model
**File:** `api/core/models/models.py`

Added `TenantPluginSettings` model:
```python
class TenantPluginSettings(Base):
    __tablename__ = "tenant_plugin_settings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True)
    enabled_plugins = Column(JSON, default=list, nullable=False)  # ["investments", ...]
    created_at = Column(DateTime(timezone=True), default=now)
    updated_at = Column(DateTime(timezone=True), default=now)
```

### 2. Database Migration
**File:** `api/alembic/versions/006_add_tenant_plugin_settings.py`

Creates the `tenant_plugin_settings` table with:
- One-to-one relationship with tenants
- JSON array to store enabled plugin IDs
- Timestamps for audit trail

### 3. API Endpoints
**File:** `api/plugins/router.py`

New endpoints for plugin management:

- `GET /api/plugins/settings` - Get enabled plugins for tenant
- `POST /api/plugins/settings` - Update all enabled plugins
- `POST /api/plugins/settings/{plugin_id}/enable` - Enable specific plugin
- `POST /api/plugins/settings/{plugin_id}/disable` - Disable specific plugin

All endpoints require admin role and return:
```json
{
  "tenant_id": 1,
  "enabled_plugins": ["investments"],
  "updated_at": "2024-02-06T10:00:00Z"
}
```

### 4. Frontend Changes
**File:** `ui/src/contexts/PluginContext.tsx`

Updated `PluginProvider`:
- Replaced `PluginStorage.load()` with API call to `/api/plugins/settings`
- Updated `togglePlugin()` to use API endpoints instead of localStorage
- Maintains optimistic UI updates with fallback on API errors
- Preserves all error handling and event dispatching

### 5. API Registration
**File:** `api/main.py`

- Imported plugin router: `from plugins.router import router as plugins_router`
- Registered router: `app.include_router(plugins_router)`

## Migration Steps

### For Existing Deployments

1. **Run migration:**
   ```bash
   alembic upgrade head
   ```

2. **Initialize plugin settings for existing tenants:**
   ```python
   # Run this script to create default settings for all tenants
   from api.core.models.models import Tenant, TenantPluginSettings
   from api.core.database import SessionLocal

   db = SessionLocal()
   tenants = db.query(Tenant).all()

   for tenant in tenants:
       existing = db.query(TenantPluginSettings).filter_by(tenant_id=tenant.id).first()
       if not existing:
           settings = TenantPluginSettings(tenant_id=tenant.id, enabled_plugins=[])
           db.add(settings)

   db.commit()
   ```

3. **Clear browser localStorage** (optional, for clean state):
   - Users can clear browser data or the app will automatically use API on next load

## Benefits

✅ **Persistent across devices** - Settings follow user, not browser
✅ **Survives cache clears** - No data loss on browser cleanup
✅ **Multi-device support** - Same settings on desktop, mobile, different browsers
✅ **Admin control** - Server-side management of plugin states
✅ **Tenant isolation** - Each organization has independent plugin configs
✅ **Audit trail** - Updated_at timestamp tracks changes

## Backward Compatibility

- localStorage fallback removed (no longer needed)
- PluginStorage class still exists but is no longer used
- Can be removed in future cleanup if desired

## Testing

### Manual Testing
1. Enable/disable plugins in Settings → Plugins tab
2. Refresh page - plugins should remain in same state
3. Open in different browser - plugins should be enabled
4. Clear browser cache - plugins should still be enabled

### API Testing
```bash
# Get current settings
curl -X GET http://localhost:8000/api/plugins/settings \
  -H "Authorization: Bearer {token}"

# Enable investments plugin
curl -X POST http://localhost:8000/api/plugins/settings/investments/enable \
  -H "Authorization: Bearer {token}"

# Disable investments plugin
curl -X POST http://localhost:8000/api/plugins/settings/investments/disable \
  -H "Authorization: Bearer {token}"
```

## Rollback Plan

If issues occur:
1. Revert code changes
2. Run: `alembic downgrade -1`
3. Clear browser localStorage manually if needed

## Future Enhancements

- Add plugin licensing validation in API
- Add audit logging for plugin changes
- Add bulk plugin management for admins
- Add plugin dependency resolution
