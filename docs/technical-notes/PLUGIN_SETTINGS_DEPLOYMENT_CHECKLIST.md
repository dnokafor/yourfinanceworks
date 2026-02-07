# Plugin Settings Deployment Checklist

## Pre-Deployment Verification ✅

- [x] Frontend authentication fixed - `apiRequest` import added to PluginContext
- [x] Backend API router created and registered
- [x] Database model defined
- [x] Database migration created
- [x] Initialization script created
- [x] No TypeScript/Python errors
- [x] All imports correct
- [x] Authentication properly configured

## Deployment Steps

### Step 1: Database Migration
```bash
cd api
alembic upgrade head
```
**Expected Output**: Migration 006 applied successfully

### Step 2: Initialize Plugin Settings
```bash
cd api
python scripts/initialize_plugin_settings.py
```
**Expected Output**:
```
Found X tenants
✓ Tenant 'name' (ID: X) - created default settings
✅ Initialization complete!
```

### Step 3: Rebuild Containers
```bash
docker-compose down
docker-compose up --build
```
**Expected Output**: All services start without errors

### Step 4: Verify API Endpoints
```bash
# Get plugin settings (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://demo.yourfinanceworks.com/api/v1/plugins/settings

# Expected response:
# {
#   "tenant_id": 1,
#   "enabled_plugins": [],
#   "updated_at": "2024-02-06T10:00:00Z"
# }
```

### Step 5: Test UI
1. Log in to application
2. Navigate to Settings → Plugins tab
3. Click "Enable" on Investments plugin
4. Verify plugin appears in sidebar
5. Refresh page - plugin should still be visible
6. Click "Disable" on Investments plugin
7. Verify plugin disappears from sidebar
8. Refresh page - plugin should remain disabled

### Step 6: Test Persistence
1. Restart containers: `docker-compose restart`
2. Log in again
3. Verify plugin state matches what was set before restart

## Rollback Plan

If issues occur:

### Rollback Database
```bash
cd api
alembic downgrade -1
```

### Rollback Code
```bash
git checkout HEAD -- ui/src/contexts/PluginContext.tsx
docker-compose down
docker-compose up --build
```

## Monitoring

After deployment, monitor:
- Browser console for errors
- API logs for 401/403 errors
- Database for plugin_settings table growth
- User reports of plugin persistence

## Success Criteria

✅ Plugins persist after page refresh
✅ Plugins persist after container restart
✅ No 401 Unauthorized errors
✅ Plugin enable/disable works in UI
✅ Settings are per-tenant (different tenants have different settings)
✅ Admin-only access enforced

## Support

If issues occur:
1. Check `PLUGIN_SETTINGS_IMPLEMENTATION_COMPLETE.md` for troubleshooting
2. Review API logs: `docker-compose logs invoice_app_api`
3. Check database: `SELECT * FROM tenant_plugin_settings;`
4. Verify JWT token is valid and stored in localStorage
