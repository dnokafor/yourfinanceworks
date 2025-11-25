#!/usr/bin/env python3
"""
Script to generate RSA key pair for license signing.

This script generates:
- private_key.pem: Used by license server to sign licenses (keep secure!)
- public_key.pem: Embedded in application to verify licenses
"""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os

def generate_rsa_keypair(key_size=2048):
    """Generate RSA key pair for license signing"""
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem


def main():
    """Generate and save RSA key pair"""
    
    # Create keys directory if it doesn't exist
    keys_dir = os.path.join(os.path.dirname(__file__), '..', 'keys')
    os.makedirs(keys_dir, exist_ok=True)
    
    private_key_path = os.path.join(keys_dir, 'private_key.pem')
    public_key_path = os.path.join(keys_dir, 'public_key.pem')
    
    # Check if keys already exist
    if os.path.exists(private_key_path) or os.path.exists(public_key_path):
        response = input("Keys already exist. Overwrite? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted. Existing keys preserved.")
            return
    
    print("Generating RSA key pair (2048-bit)...")
    private_pem, public_pem = generate_rsa_keypair()
    
    # Save private key
    with open(private_key_path, 'wb') as f:
        f.write(private_pem)
    
    # Save public key
    with open(public_key_path, 'wb') as f:
        f.write(public_pem)
    
    # Secure private key (chmod 600)
    os.chmod(private_key_path, 0o600)
    
    print(f"✓ Private key saved to: {private_key_path}")
    print(f"✓ Public key saved to: {public_key_path}")
    print(f"✓ Private key permissions set to 600 (owner read/write only)")
    print("\nIMPORTANT:")
    print("- Keep private_key.pem SECURE and NEVER commit it to version control")
    print("- The private key is used to sign licenses (keep on license server only)")
    print("- The public key will be embedded in the application to verify licenses")
    print("- Add 'keys/private_key.pem' to .gitignore")


if __name__ == '__main__':
    main()
