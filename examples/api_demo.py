#!/usr/bin/env python3
"""
api_demo.py

Demonstration of the NUGovern HTTP API (Layer 6).

This script shows how to use eBIOS through the REST API:
1. Start the API server
2. Execute operations remotely
3. Manage policies via HTTP
4. Query the audit ledger
5. Generate attestations

Prerequisites:
    pip install requests

Usage:
    # Terminal 1: Start the API server
    python src/nugovern/server.py

    # Terminal 2: Run this demo
    python examples/api_demo.py
"""

import requests
import json
import time
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def check_health() -> bool:
    """Check if API server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


def example_1_operations():
    """Example 1: Execute operations via API"""
    print("=" * 70)
    print("EXAMPLE 1: Remote Operation Execution")
    print("=" * 70)

    operations = [
        {
            "name": "Addition",
            "request": {
                "operation": "add",
                "inputs": [[10.0, 0.5], [20.0, 1.0]],
                "params": None
            }
        },
        {
            "name": "Multiplication",
            "request": {
                "operation": "multiply",
                "inputs": [[10.0, 0.5], [20.0, 1.0]],
                "params": {"lambda_margin": 1.0}
            }
        },
        {
            "name": "Composition",
            "request": {
                "operation": "compose",
                "inputs": [[10.0, 5.0], [10.0, 3.0]],
                "params": None
            }
        }
    ]

    print("\n🚀 Executing operations via HTTP API...\n")

    for op in operations:
        print(f"📊 {op['name']}")
        response = requests.post(
            f"{BASE_URL}/operations/execute",
            json=op["request"]
        )

        if response.status_code == 200:
            data = response.json()
            n, u = data["result"]
            print(f"   Result: {n:.2f} ± {u:.3f}")
            print(f"   Coverage: {data['coverage']:.4f}")
            print(f"   Invariants: {'✅ PASS' if data['invariant_passed'] else '❌ FAIL'}")
            if data['ledger_id']:
                print(f"   Ledger ID: {data['ledger_id'][:16]}...")
        else:
            print(f"   ❌ Error: {response.status_code}")
        print()

    print("✅ All operations completed\n")


def example_2_policy_management():
    """Example 2: Create and activate policies"""
    print("=" * 70)
    print("EXAMPLE 2: Policy Management via API")
    print("=" * 70)

    # Create a new policy
    print("\n📝 Creating custom policy...")
    policy_request = {
        "name": "APITestPolicy",
        "version": "1.0.0",
        "description": "Policy created via API",
        "rules": [
            {"type": "InvariantRule"},
            {"type": "CoverageRule", "threshold": 0.1, "level": "warning"}
        ],
        "escalation": {
            "halt_on_critical": False,
            "auto_log": True
        },
        "metadata": {
            "author": "API Demo",
            "created_via": "HTTP POST"
        }
    }

    response = requests.post(f"{BASE_URL}/policies", json=policy_request)

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Policy created: {data['name']}")
        print(f"   Version: {data['version']}")
        print(f"   Rules: {data['rules_count']}")
        print(f"   Hash: {data['policy_hash'][:32]}...")
    else:
        print(f"   ❌ Error: {response.status_code}")

    # List all policies
    print("\n📋 Listing all policies...")
    response = requests.get(f"{BASE_URL}/policies")

    if response.status_code == 200:
        policies = response.json()
        for i, policy_name in enumerate(policies, 1):
            print(f"   {i}. {policy_name}")

    # Activate policy
    print("\n🔐 Activating policy...")
    response = requests.put(f"{BASE_URL}/policies/APITestPolicy/activate")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {data['message']}")
    else:
        print(f"   ❌ Error: {response.status_code}")

    print("\n✅ Policy management completed\n")


def example_3_ledger_queries():
    """Example 3: Query audit ledger"""
    print("=" * 70)
    print("EXAMPLE 3: Ledger Queries via API")
    print("=" * 70)

    # Execute some operations first
    print("\n🔄 Executing operations to populate ledger...")
    for i in range(3):
        requests.post(
            f"{BASE_URL}/operations/execute",
            json={
                "operation": "add",
                "inputs": [[float(i), 0.1], [10.0, 0.5]],
                "params": None
            }
        )
    print("   ✅ Operations logged")

    # Query all entries
    print("\n📊 Querying ledger entries...")
    response = requests.get(f"{BASE_URL}/ledger/entries?limit=10&offset=0")

    if response.status_code == 200:
        entries = response.json()
        print(f"   Found {len(entries)} entries")

        for i, entry in enumerate(entries[:3], 1):
            print(f"\n   Entry {i}:")
            print(f"     Op ID: {entry['op_id'][:16]}...")
            print(f"     Operation: {entry['operation']}")
            print(f"     Coverage: {entry['coverage']:.4f}")
            print(f"     Invariants: {'✅' if entry['invariant_passed'] else '❌'}")

    # Verify integrity
    print("\n🔒 Verifying ledger integrity...")
    response = requests.get(f"{BASE_URL}/ledger/verify")

    if response.status_code == 200:
        data = response.json()
        print(f"   Integrity: {'✅ VALID' if data['valid'] else '❌ INVALID'}")
        print(f"   Total entries: {data['entries']}")
        print(f"   Merkle root: {data['root'][:32]}...")

    print("\n✅ Ledger queries completed\n")


def example_4_monitor_stats():
    """Example 4: Monitor statistics"""
    print("=" * 70)
    print("EXAMPLE 4: Monitor Statistics via API")
    print("=" * 70)

    print("\n📊 Fetching monitor statistics...")
    response = requests.get(f"{BASE_URL}/monitor/stats")

    if response.status_code == 200:
        stats = response.json()
        print(f"   Total events: {stats['total_events']}")
        print(f"   Violations: {stats['violations']}")
        print(f"   Rules configured: {len(stats['rules'])}")
        for rule in stats['rules']:
            print(f"     - {rule}")
        print(f"   Auto-log: {'✅' if stats['auto_log'] else '❌'}")
        print(f"   Halt on critical: {'✅' if stats['halt_on_critical'] else '❌'}")

    print("\n🔄 Resetting monitor...")
    response = requests.post(f"{BASE_URL}/monitor/reset")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {data['message']}")

    print("\n✅ Monitor operations completed\n")


def example_5_attestation():
    """Example 5: Generate attestations"""
    print("=" * 70)
    print("EXAMPLE 5: Cryptographic Attestation via API")
    print("=" * 70)

    # Ledger attestation
    print("\n🔐 Generating ledger attestation...")
    response = requests.post(
        f"{BASE_URL}/attestation",
        json={
            "attestation_type": "ledger",
            "target_id": None
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"   Type: {data['attestation_type']}")
        print(f"   Timestamp: {data['timestamp']}")
        print(f"   Hash (Merkle root): {data['hash'][:32]}...")
        print(f"   Verified: {'✅' if data['verified'] else '❌'}")

    # Policy attestation (if exists)
    print("\n🔐 Generating policy attestation...")
    response = requests.post(
        f"{BASE_URL}/attestation",
        json={
            "attestation_type": "policy",
            "target_id": "conservative"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"   Type: {data['attestation_type']}")
        print(f"   Target: {data['target_id']}")
        print(f"   Timestamp: {data['timestamp']}")
        print(f"   Hash: {data['hash'][:32]}...")
        print(f"   Signed: {'✅' if data['signature'] != 'unsigned' else '❌'}")
    elif response.status_code == 404:
        print(f"   ⚠️  Policy 'conservative' not found in API server policy dir")

    print("\n✅ Attestation completed\n")


def main():
    """Run all API examples"""
    print("\n" + "=" * 70)
    print("eBIOS v0.1.0 - HTTP API Demonstration")
    print("=" * 70)
    print("\nNUGovern (Layer 6) - RESTful API for Governance")
    print("=" * 70 + "\n")

    # Check if server is running
    print("🔍 Checking API server status...")
    if not check_health():
        print("❌ API server is not running!")
        print("\nPlease start the server first:")
        print("  python src/nugovern/server.py")
        print("\nThen run this demo again.")
        return

    print("✅ API server is running at", BASE_URL)
    print()

    try:
        example_1_operations()
        input("Press Enter to continue to Example 2...")

        example_2_policy_management()
        input("Press Enter to continue to Example 3...")

        example_3_ledger_queries()
        input("Press Enter to continue to Example 4...")

        example_4_monitor_stats()
        input("Press Enter to continue to Example 5...")

        example_5_attestation()

        print("=" * 70)
        print("🎉 All API examples completed successfully!")
        print("=" * 70)
        print("\nNext steps:")
        print("  • Open Swagger UI: http://localhost:8000/docs")
        print("  • Try ReDoc: http://localhost:8000/redoc")
        print("  • Modify examples to test different scenarios")
        print("  • Read API docs: docs/NUGovern_API.md")
        print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except requests.exceptions.ConnectionError:
        print("\n\n❌ Error: Lost connection to API server")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
