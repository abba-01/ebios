#!/usr/bin/env python3
"""
basic_usage.py

Basic usage examples for eBIOS - demonstrating all layers working together.

This script shows:
1. NUCore operations (Layer 1)
2. NULedger audit logging (Layer 3)
3. NUGuard monitoring (Layer 4)
4. NUPolicy configuration (Layer 5)
"""

import sys
sys.path.insert(0, '/got/ebios')

from src.nucore import add, multiply, compose, catch, flip
from src.nucore.validators import coverage_ratio, validate
from src.nuledger import Ledger, MemoryBackend
from src.nuguard import Monitor, MonitorConfig, CoverageRule, InvariantRule
from src.nupolicy import PolicyManager
from src.nupolicy.integration import create_monitor_from_policy


def example_1_basic_operations():
    """Example 1: Basic NUCore operations"""
    print("=" * 70)
    print("EXAMPLE 1: Basic NUCore Operations")
    print("=" * 70)

    # Addition with uncertainty propagation
    print("\n1. Addition: (10.0 ± 0.5) + (20.0 ± 1.0)")
    n1, u1 = add(10.0, 0.5, 20.0, 1.0)
    print(f"   Result: {n1:.2f} ± {u1:.3f}")
    print(f"   Coverage: {coverage_ratio(n1, u1):.4f}")

    # Multiplication with conservative cross-term
    print("\n2. Multiplication: (10.0 ± 0.5) × (20.0 ± 1.0)")
    n2, u2 = multiply(10.0, 0.5, 20.0, 1.0)
    print(f"   Result: {n2:.2f} ± {u2:.3f}")
    print(f"   Coverage: {coverage_ratio(n2, u2):.4f}")

    # Composition - uncertainty reduction
    print("\n3. Composition: (10.0 ± 5.0) ⊙ (10.0 ± 3.0)")
    n3, u3 = compose(10.0, 5.0, 10.0, 3.0)
    print(f"   Result: {n3:.2f} ± {u3:.3f} (reduced from 5.0 and 3.0)")
    print(f"   Coverage: {coverage_ratio(n3, u3):.4f}")

    # Catch - error handling
    print("\n4. Catch: catch(10.0 ± 0.5)")
    n4, u4 = catch(10.0, 0.5)
    print(f"   Result: {n4:.2f} ± {u4:.3f} (passthrough, valid input)")

    # Flip - negation
    print("\n5. Flip: flip(10.0 ± 0.5)")
    n5, u5 = flip(10.0, 0.5)
    print(f"   Result: {n5:.2f} ± {u5:.3f}")

    print("\n✅ All operations completed successfully\n")


def example_2_ledger_logging():
    """Example 2: Ledger audit trail"""
    print("=" * 70)
    print("EXAMPLE 2: Ledger Audit Trail")
    print("=" * 70)

    # Create ledger
    ledger = Ledger(backend=MemoryBackend())
    print(f"\n📋 Created ledger (backend: Memory)")

    # Log some operations
    operations = [
        ("add", [(10.0, 0.5), (20.0, 1.0)], add(10.0, 0.5, 20.0, 1.0)),
        ("multiply", [(5.0, 0.1), (10.0, 0.2)], multiply(5.0, 0.1, 10.0, 0.2)),
        ("compose", [(10.0, 5.0), (10.0, 3.0)], compose(10.0, 5.0, 10.0, 3.0)),
    ]

    print("\n🔍 Logging operations to ledger...")
    for op_name, inputs, (n_out, u_out) in operations:
        entry = ledger.append(
            operation=op_name,
            inputs=inputs,
            output=(n_out, u_out),
            coverage=coverage_ratio(n_out, u_out),
            invariant_passed=validate(n_out, u_out)
        )
        print(f"   ✓ {op_name}: {entry.op_id[:8]}... (coverage: {entry.coverage:.4f})")

    # Verify integrity
    print(f"\n🔒 Ledger integrity check...")
    is_valid = ledger.verify_integrity()
    print(f"   {'✅' if is_valid else '❌'} Integrity: {'VALID' if is_valid else 'INVALID'}")
    print(f"   📊 Total entries: {len(ledger)}")
    print(f"   🌳 Merkle root: {ledger.get_root()[:16]}...")

    print("\n✅ Ledger operations completed\n")


def example_3_monitoring():
    """Example 3: Runtime monitoring"""
    print("=" * 70)
    print("EXAMPLE 3: Runtime Monitoring with NUGuard")
    print("=" * 70)

    # Create monitor with custom rules
    config = MonitorConfig(
        rules=[
            InvariantRule(),  # Detect u < 0, NaN, infinite nominal
            CoverageRule(threshold=0.05, level=EventLevel.WARNING)  # 5% coverage threshold
        ],
        auto_log=False,
        halt_on_critical=False
    )

    from src.nuguard import EventLevel
    monitor = Monitor(config)

    print("\n📡 Monitor configured:")
    print(f"   Rules: {len(config.rules)}")
    for rule in config.rules:
        print(f"     - {rule.name()}")

    # Test with good operations
    print("\n🧪 Testing operations...")

    # Good operation
    print("\n1. Good operation: (10.0 ± 0.5) + (20.0 ± 1.0)")
    n1, u1 = add(10.0, 0.5, 20.0, 1.0)
    event1 = monitor.check("add", [(10.0, 0.5), (20.0, 1.0)], (n1, u1))
    print(f"   {'✅' if event1 is None else '⚠️'} {event1.message if event1 else 'PASSED'}")

    # Operation with high coverage
    print("\n2. High coverage: (10.0 ± 5.0) + (20.0 ± 10.0)")
    n2, u2 = add(10.0, 5.0, 20.0, 10.0)
    event2 = monitor.check("add", [(10.0, 5.0), (20.0, 10.0)], (n2, u2))
    print(f"   {'✅' if event2 is None else '⚠️'} {event2.message if event2 else 'PASSED'}")

    # Stats
    stats = monitor.stats()
    print(f"\n📊 Monitor statistics:")
    print(f"   Total events: {stats['total_events']}")
    print(f"   Violations: {stats['violations']}")

    print("\n✅ Monitoring completed\n")


def example_4_policy_driven():
    """Example 4: Policy-driven monitoring"""
    print("=" * 70)
    print("EXAMPLE 4: Policy-Driven Monitoring")
    print("=" * 70)

    # Load example policy
    manager = PolicyManager(policy_dir='/got/ebios/governance/policies')

    print("\n📋 Available policies:")
    policies = manager.list_policies()
    for i, policy_name in enumerate(policies, 1):
        print(f"   {i}. {policy_name}")

    # Load conservative policy
    print("\n🔐 Loading 'conservative' policy...")
    policy = manager.load_policy("conservative")

    print(f"   Name: {policy.config.name}")
    print(f"   Version: {policy.config.version}")
    print(f"   Description: {policy.config.description}")
    print(f"   Rules: {len(policy.config.rules)}")
    for rule in policy.config.rules:
        print(f"     - {rule['type']}")

    # Create monitor from policy
    ledger = Ledger(backend=MemoryBackend())
    monitor = create_monitor_from_policy(policy, ledger=ledger, validate=False)

    print(f"\n🤖 Monitor created from policy")
    print(f"   Auto-log: {monitor.config.auto_log}")
    print(f"   Halt on critical: {monitor.config.halt_on_critical}")

    # Run operation with monitoring
    print("\n🧪 Executing operation with policy monitoring...")
    n, u = add(10.0, 0.5, 20.0, 1.0)
    event = monitor.check("add", [(10.0, 0.5), (20.0, 1.0)], (n, u))

    print(f"   Result: {n:.2f} ± {u:.3f}")
    print(f"   Event: {event.message if event else 'No violations'}")
    print(f"   Ledger entries: {len(ledger)}")

    print("\n✅ Policy-driven monitoring completed\n")


def example_5_end_to_end():
    """Example 5: Complete end-to-end workflow"""
    print("=" * 70)
    print("EXAMPLE 5: Complete End-to-End Workflow")
    print("=" * 70)

    print("\n🏗️  Setting up eBIOS stack...")

    # 1. Create ledger
    ledger = Ledger(backend=MemoryBackend())
    print("   ✓ Ledger initialized")

    # 2. Load policy
    manager = PolicyManager(policy_dir='/got/ebios/governance/policies')
    policy = manager.load_policy("conservative")
    print(f"   ✓ Policy loaded: {policy.config.name} v{policy.config.version}")

    # 3. Create monitor from policy
    monitor = create_monitor_from_policy(policy, ledger=ledger, validate=False)
    print(f"   ✓ Monitor configured with {len(monitor.config.rules)} rules")

    # 4. Execute operations with full stack
    print("\n🚀 Executing operations through full stack...\n")

    test_operations = [
        ("Sensor A + Sensor B", (10.0, 0.5), (20.0, 1.0)),
        ("Velocity × Time", (50.0, 2.0), (10.0, 0.5)),
        ("GPS ⊙ IMU", (100.0, 10.0), (100.0, 5.0)),
    ]

    for i, (desc, (n1, u1), (n2, u2)) in enumerate(test_operations, 1):
        print(f"{i}. {desc}")
        print(f"   Input 1: {n1:.2f} ± {u1:.2f}")
        print(f"   Input 2: {n2:.2f} ± {u2:.2f}")

        # Execute operation
        if i == 1:
            n_out, u_out = add(n1, u1, n2, u2)
            op_name = "add"
        elif i == 2:
            n_out, u_out = multiply(n1, u1, n2, u2)
            op_name = "multiply"
        else:
            n_out, u_out = compose(n1, u1, n2, u2)
            op_name = "compose"

        # Monitor
        event = monitor.check(op_name, [(n1, u1), (n2, u2)], (n_out, u_out))

        print(f"   Output: {n_out:.2f} ± {u_out:.2f}")
        print(f"   Coverage: {coverage_ratio(n_out, u_out):.4f}")
        print(f"   Monitor: {'✅ PASS' if event is None else f'⚠️ {event.level.value.upper()}'}")
        print()

    # 5. Verify audit trail
    print("🔍 Final audit trail:")
    print(f"   Total operations logged: {len(ledger)}")
    print(f"   Ledger integrity: {'✅ VALID' if ledger.verify_integrity() else '❌ INVALID'}")
    print(f"   Merkle root: {ledger.get_root()[:32]}...")

    # 6. Monitor statistics
    stats = monitor.stats()
    print(f"\n📊 Monitor statistics:")
    print(f"   Total events: {stats['total_events']}")
    print(f"   Violations: {stats['violations']}")

    print("\n✅ End-to-end workflow completed successfully!\n")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("eBIOS v0.1.0 - Complete Usage Examples")
    print("=" * 70)
    print("\nDemonstrating all layers working together:")
    print("  • Layer 1: NUCore (N/U Algebra)")
    print("  • Layer 3: NULedger (Audit Trail)")
    print("  • Layer 4: NUGuard (Monitoring)")
    print("  • Layer 5: NUPolicy (Governance)")
    print("=" * 70 + "\n")

    try:
        example_1_basic_operations()
        input("Press Enter to continue to Example 2...")

        example_2_ledger_logging()
        input("Press Enter to continue to Example 3...")

        example_3_monitoring()
        input("Press Enter to continue to Example 4...")

        example_4_policy_driven()
        input("Press Enter to continue to Example 5...")

        example_5_end_to_end()

        print("=" * 70)
        print("🎉 All examples completed successfully!")
        print("=" * 70)
        print("\nNext steps:")
        print("  • Try modifying the examples")
        print("  • Create your own policies in governance/policies/")
        print("  • Start the HTTP API: python src/nugovern/server.py")
        print("  • Read the docs: docs/README.md")
        print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
