#!/usr/bin/env python3
"""
Test script for Tax Service Integration
This script provides programmatic testing of the integration
"""

import asyncio
import httpx
import json
import sys
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class TestConfig:
    """Test configuration"""
    base_url: str = "http://localhost:8000/api/v1"
    auth_token: Optional[str] = None
    expense_id: int = 1
    invoice_id: int = 1


class TaxIntegrationTester:
    """Test class for tax integration"""

    def __init__(self, config: TestConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.auth_token}" if config.auth_token else ""
            },
            timeout=30.0
        )

    async def close(self):
        """Clean up HTTP client"""
        await self.client.aclose()

    async def make_request(self, method: str, endpoint: str, data: Optional[dict] = None):
        """Make HTTP request"""
        url = f"{self.config.base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = await self.client.get(url)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
            return None

    async def test_integration_status(self):
        """Test integration status endpoint"""
        print("\n🔑 Testing integration status...")
        result = await self.make_request("GET", "/tax-integration/status")
        if result:
            print("✅ Status check successful")
            print(json.dumps(result, indent=2))
        return result

    async def test_connection(self):
        """Test connection to tax service"""
        print("\n🔗 Testing connection to tax service...")
        result = await self.make_request("POST", "/tax-integration/test-connection")
        if result:
            print("✅ Connection test successful")
            print(json.dumps(result, indent=2))
        return result

    async def test_send_expense(self):
        """Test sending expense to tax service"""
        print(f"\n💰 Testing expense send (ID: {self.config.expense_id})...")
        data = {
            "item_id": self.config.expense_id,
            "item_type": "expense"
        }
        result = await self.make_request("POST", "/tax-integration/send", data)
        if result:
            print("✅ Expense send successful")
            print(json.dumps(result, indent=2))
        return result

    async def test_send_invoice(self):
        """Test sending invoice to tax service"""
        print(f"\n📄 Testing invoice send (ID: {self.config.invoice_id})...")
        data = {
            "item_id": self.config.invoice_id,
            "item_type": "invoice"
        }
        result = await self.make_request("POST", "/tax-integration/send", data)
        if result:
            print("✅ Invoice send successful")
            print(json.dumps(result, indent=2))
        return result

    async def test_preview_expense(self):
        """Test expense preview"""
        print(f"\n🔍 Testing expense preview (ID: {self.config.expense_id})...")
        result = await self.make_request("GET", f"/tax-integration/expenses/{self.config.expense_id}/tax-transaction")
        if result:
            print("✅ Expense preview successful")
            print(json.dumps(result, indent=2))
        return result

    async def test_preview_invoice(self):
        """Test invoice preview"""
        print(f"\n🔍 Testing invoice preview (ID: {self.config.invoice_id})...")
        result = await self.make_request("GET", f"/tax-integration/invoices/{self.config.invoice_id}/tax-transaction")
        if result:
            print("✅ Invoice preview successful")
            print(json.dumps(result, indent=2))
        return result

    async def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Running Tax Service Integration Tests")
        print("=" * 50)

        if not self.config.auth_token:
            print("⚠️  Warning: No auth token provided. Some tests may fail.")
            print("   Set AUTH_TOKEN environment variable or pass --token")

        # Run tests
        await self.test_integration_status()
        await self.test_connection()
        await self.test_preview_expense()
        await self.test_preview_invoice()
        await self.test_send_expense()
        await self.test_send_invoice()

        print("\n🎉 All tests completed!")


async def main():
    """Main test function"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Tax Service Integration")
    parser.add_argument("--url", default="http://localhost:8000/api/v1", help="API base URL")
    parser.add_argument("--token", help="JWT auth token")
    parser.add_argument("--expense-id", type=int, default=1, help="Expense ID to test")
    parser.add_argument("--invoice-id", type=int, default=1, help="Invoice ID to test")

    args = parser.parse_args()

    # Get token from environment if not provided
    token = args.token or os.getenv("AUTH_TOKEN")

    config = TestConfig(
        base_url=args.url,
        auth_token=token,
        expense_id=args.expense_id,
        invoice_id=args.invoice_id
    )

    tester = TaxIntegrationTester(config)

    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    import os
    asyncio.run(main())
