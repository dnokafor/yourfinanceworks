#!/bin/bash
# Setup script to ensure keys are properly versioned

echo "Setting up license keys..."

# Check if versioned keys exist
if [ -f "private_key_v2.pem" ] && [ -f "public_key_v2.pem" ]; then
    echo "✓ Versioned keys already exist"
else
    # Check if non-versioned keys exist
    if [ -f "private_key.pem" ] && [ -f "public_key.pem" ]; then
        echo "Creating versioned copies..."
        cp private_key.pem private_key_v2.pem
        cp public_key.pem public_key_v2.pem
        chmod 600 private_key_v2.pem
        chmod 644 public_key_v2.pem
        echo "✓ Created private_key_v2.pem and public_key_v2.pem"
    else
        echo "✗ No keys found. Keys will be auto-generated on startup."
        exit 1
    fi
fi

# Copy to license_server if it exists
if [ -d "../../license_server/keys" ]; then
    echo "Copying keys to license_server..."
    cp private_key_v2.pem ../../license_server/keys/
    cp public_key_v2.pem ../../license_server/keys/
    chmod 600 ../../license_server/keys/private_key_v2.pem
    chmod 644 ../../license_server/keys/public_key_v2.pem
    echo "✓ Keys copied to license_server/keys/"
fi

echo ""
echo "Setup complete! You can now:"
echo "1. Generate licenses with: cd license_server && python generate_license_cli.py --private-key keys/private_key_v2.pem ..."
echo "2. Or use the default: cd license_server && python generate_license_cli.py ..."
