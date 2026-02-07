# Plugin Settings - Quick Start Guide

## What Changed?
Plugin settings now persist in the database instead of browser localStorage. This means:
- ✅ Settings survive browser cache clears
- ✅ Settings work across different devices
- ✅ Settings are managed server-side

## For Users

### Enabling/Disabling Plugins
1. Go to **Settings** → **Plugins**
2. Toggle the switch for "Investment Management" or other plugins
3. Changes are saved to the database automatically
4. Refresh the page - plugin should still be enabled

### Troubleshooting
- **Plugin disappeared after clearing cache?** - It's now saved in the database, just re-enable it in Settings
- **Plugin not showing in sidebar?** - Make sure you're an admin and the plugin is enabled in Settings

## For Developers

### Running the Migration

```bash
# 1. Run the database migration
cd api
alembic upgrade head

# 2. Initialize plugin settings for existing tenants
python scripts/initialize_plugin_settings.py

# 3. Restart the API server
```

### Testing the API

```bash
# Get current plugin settings
curl -X GET http://localhost:8000/api/plugins/settings \
  -H "Authorization: Bearer YOUR_TOKEN"

# Enable investments plugin
curl -X POST http://localhost:8000/api/plugins/settings/investments/enable \
  -H "Authorization: Bearer YOUR_TOKEN"

# Disable investments plugin
curl -X POST http://localhost:8000/api/plugins/settings/investments/disable \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Adding a New Plugin

1. **Add to valid plugins list** in `api/plugins/router.py`:
   ```python
   valid_plugins = {"investments", "reports", "your_new_plugin"}
   ```

2. **Add to plugin configs** in `ui/src/components/layout/AppSidebar.tsx`:
   ```typescript
   const pluginConfigs = [
     {
       id: 'your_new_plugin',
       path: '/your-plugin',
       label: 'Your Plugin',
       icon: <YourIcon className="w-5 h-5" />,
       priority: 2
     }
   ];
   ```

3. **Register in PluginDiscovery** in `ui/src/contexts/PluginContext.tsx`:
   ```typescript
   private static async getBuiltInPlugins(): Promise<PluginMetadata[]> {
     return [
       // ... existing plugins
       {
         id: 'your_new_plugin',
         name: 'Your Plugin',
         description: 'Plugin description',
         // ... other metadata
       }
     ];
   }
   ```

## File Structure

```
api/
├── plugins/
│   └── router.py                    # Plugin API endpoints
├── core/models/
│   └── models.py                    # TenantPluginSettings model
├── alembic/versions/
│   └── 006_add_tenant_plugin_settings.py  # Database migration
└── scripts/
    └── initialize_plugin_settings.py      # Setup script

ui/src/
├── contexts/
│   └── PluginContext.tsx            # Updated to use API
└── components/layout/
    └── AppSidebar.tsx               # Plugin menu rendering
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/plugins/settings` | Get enabled plugins | User |
| POST | `/api/plugins/settings` | Update all plugins | Admin |
| POST | `/api/plugins/settings/{id}/enable` | Enable plugin | Admin |
| POST | `/api/plugins/settings/{id}/disable` | Disable plugin | Admin |

## Database Schema

```sql
CREATE TABLE tenant_plugin_settings (
  id INTEGER PRIMARY KEY,
  tenant_id INTEGER UNIQUE NOT NULL REFERENCES tenants(id),
  enabled_plugins JSON DEFAULT '[]',
  created_at TIMESTAMP WITH TIMEZONE,
  updated_at TIMESTAMP WITH TIMEZONE
);
```

## Rollback

If you need to revert:

```bash
# Revert database migration
alembic downgrade -1

# Revert code changes
git checkout HEAD~1
```

## Support

For issues or questions:
1. Check the full migration guide: `PLUGIN_SETTINGS_MIGRATION.md`
2. Review API endpoint documentation in `api/plugins/router.py`
3. Check browser console for error messages
