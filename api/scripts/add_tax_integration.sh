#!/bin/bash

# Quick integration script for Tax Service UI components
# This script helps add tax integration to existing pages

echo "🧾 Tax Service UI Integration Helper"
echo "===================================="

TARGET_FILE="$1"

if [ -z "$TARGET_FILE" ]; then
    echo "❌ Usage: $0 <path/to/page.tsx>"
    echo ""
    echo "Examples:"
    echo "  $0 src/pages/Expenses.tsx"
    echo "  $0 src/pages/Invoices.tsx"
    echo ""
    exit 1
fi

if [ ! -f "$TARGET_FILE" ]; then
    echo "❌ File not found: $TARGET_FILE"
    exit 1
fi

echo "📝 Adding tax integration to: $TARGET_FILE"
echo ""

# Backup original file
cp "$TARGET_FILE" "${TARGET_FILE}.backup"
echo "✅ Created backup: ${TARGET_FILE}.backup"

# Add imports
if ! grep -q "tax-integration" "$TARGET_FILE"; then
    # Find the last import line and add our imports after it
    sed -i '/^import.*from.*@/a import { SendToTaxServiceButton, TaxIntegrationStatus, BulkSendToTaxServiceDialog } from "@/components/tax-integration";' "$TARGET_FILE"
    echo "✅ Added tax integration imports"
fi

# Add useState for bulk operations if not present
if ! grep -q "useState.*selectedIds" "$TARGET_FILE"; then
    # Find the first useState line and add our state after it
    sed -i '/const \[.*useState/a const [selectedIds, setSelectedIds] = useState<number[]>([]);\n  const [bulkSendDialogOpen, setBulkSendDialogOpen] = useState(false);' "$TARGET_FILE"
    echo "✅ Added bulk operation state"
fi

# Add success handler function
if ! grep -q "handleTaxServiceSuccess" "$TARGET_FILE"; then
    # Add after the last useState or useEffect
    sed -i '/useState\|useEffect/a \
  const handleTaxServiceSuccess = () => {\n    fetchData(); // Refresh your data\n    setSelectedIds([]); // Clear selections\n  };' "$TARGET_FILE"
    echo "✅ Added success handler"
fi

echo ""
echo "🎉 Basic integration complete!"
echo ""
echo "📋 Manual steps remaining:"
echo ""
echo "1. Add TaxIntegrationStatus component:"
echo '   <TaxIntegrationStatus />'
echo ""
echo "2. Add checkboxes to your table:"
echo '   <Checkbox'
echo '     checked={selectedIds.includes(item.id)}'
echo '     onCheckedChange={(checked) => {'
echo '       setSelectedIds(prev =>'
echo '         checked ? [...prev, item.id] : prev.filter(id => id !== item.id)'
echo '       );'
echo '     }}'
echo '   />'
echo ""
echo "3. Add bulk actions bar:"
echo '   {selectedIds.length > 0 && ('
echo '     <div className="p-4 bg-blue-50 border rounded-md">'
echo '       <Button onClick={() => setBulkSendDialogOpen(true)}>'
echo '         Send {selectedIds.length} to Tax Service'
echo '       </Button>'
echo '     </div>'
echo '   )}'
echo ""
echo "4. Add send buttons to table rows:"
echo '   <SendToTaxServiceButton'
echo '     itemId={item.id}'
echo '     itemType="expense" // or "invoice"'
echo '     onSuccess={handleTaxServiceSuccess}'
echo '     size="sm"'
echo '   />'
echo ""
echo "5. Add bulk send dialog:"
echo '   <BulkSendToTaxServiceDialog'
echo '     open={bulkSendDialogOpen}'
echo '     onOpenChange={setBulkSendDialogOpen}'
echo '     items={items.filter(item => selectedIds.includes(item.id))}'
echo '     itemType="expense" // or "invoice"'
echo '     onSuccess={handleTaxServiceSuccess}'
echo '   />'
echo ""
echo "6. Update fetchData function name in handleTaxServiceSuccess"
echo ""
echo "🔍 Check the integration examples in:"
echo "   - ExpensesWithTaxIntegration.tsx"
echo "   - InvoicesWithTaxIntegration.tsx"
echo "   - TAX_INTEGRATION_UI_GUIDE.md"
echo ""
echo "⚠️  Remember to test thoroughly after integration!"
