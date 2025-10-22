#!/usr/bin/env python3
"""
cli.py

Command-line interface for NULedger audit queries.

Usage:
    nuledger trace <op_id>          -- Show causal chain for operation
    nuledger verify                 -- Verify ledger integrity
    nuledger stats                  -- Show ledger statistics
    nuledger export <file>          -- Export ledger to JSON
    nuledger root                   -- Show current Merkle root
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from .ledger import Ledger
from .backends import SQLiteBackend, MemoryBackend


def trace_operation(ledger: Ledger, op_id: str) -> None:
    """
    Trace causal chain for operation

    Args:
        ledger: NULedger instance
        op_id: Operation ID to trace
    """
    chain = ledger.trace(op_id)

    if not chain:
        print(f"❌ Operation {op_id} not found in ledger")
        sys.exit(1)

    print(f"Causal Chain for {op_id}")
    print("=" * 70)
    print()

    for i, entry in enumerate(chain):
        print(f"[{i}] {entry.operation.upper()}")
        print(f"    Op ID:      {entry.op_id}")
        print(f"    Timestamp:  {entry.timestamp}")
        print(f"    Parent:     {entry.parent_id or '(root)'}")
        print(f"    Inputs:     {entry.inputs}")
        print(f"    Output:     {entry.output}")
        print(f"    Coverage:   {entry.coverage:.6f}")
        print(f"    Invariants: {'✓ PASS' if entry.invariant_passed else '✗ FAIL'}")
        print(f"    Signature:  {entry.signature[:32]}...")
        print()

    print(f"Chain length: {len(chain)} operations")
    print(f"Merkle root:  {ledger.get_root()[:32]}...")


def verify_ledger(ledger: Ledger) -> None:
    """
    Verify complete ledger integrity

    Args:
        ledger: NULedger instance
    """
    print("Verifying ledger integrity...")
    print()

    is_valid = ledger.verify_integrity()

    if is_valid:
        print("✅ Ledger integrity verified!")
        print()
        print(f"  Entries:     {len(ledger)}")
        print(f"  Merkle root: {ledger.get_root()[:32]}...")
    else:
        print("❌ Ledger integrity check FAILED!")
        print()
        print("Possible causes:")
        print("  - Tampered entries")
        print("  - Invalid signatures")
        print("  - Non-monotonic timestamps")
        sys.exit(1)


def show_stats(ledger: Ledger) -> None:
    """
    Show ledger statistics

    Args:
        ledger: NULedger instance
    """
    entries = ledger.get_all()

    if not entries:
        print("Ledger is empty")
        return

    # Compute statistics
    operation_counts = {}
    total_coverage = 0.0
    failed_invariants = 0

    for entry in entries:
        operation_counts[entry.operation] = operation_counts.get(entry.operation, 0) + 1
        total_coverage += entry.coverage
        if not entry.invariant_passed:
            failed_invariants += 1

    avg_coverage = total_coverage / len(entries)

    # Display
    print("NULedger Statistics")
    print("=" * 70)
    print()
    print(f"Total Entries:        {len(entries)}")
    print(f"Merkle Root:          {ledger.get_root()[:32]}...")
    print(f"Average Coverage:     {avg_coverage:.6f}")
    print(f"Failed Invariants:    {failed_invariants}")
    print()

    print("Operations:")
    for op, count in sorted(operation_counts.items()):
        percentage = (count / len(entries)) * 100
        print(f"  {op:15s}  {count:6d}  ({percentage:5.1f}%)")


def export_ledger(ledger: Ledger, output_file: str) -> None:
    """
    Export ledger to JSON file

    Args:
        ledger: NULedger instance
        output_file: Path to output JSON file
    """
    entries = ledger.get_all()

    data = {
        "merkle_root": ledger.get_root(),
        "entry_count": len(entries),
        "entries": [entry.to_dict() for entry in entries]
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Exported {len(entries)} entries to {output_file}")


def show_root(ledger: Ledger) -> None:
    """
    Show current Merkle root

    Args:
        ledger: NULedger instance
    """
    root = ledger.get_root()
    print(f"Current Merkle root:")
    print(root)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="NULedger: Audit trail query tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nuledger trace abc123-def456          Trace operation causal chain
  nuledger verify                       Verify ledger integrity
  nuledger stats                        Show statistics
  nuledger export audit.json            Export to JSON
  nuledger root                         Show Merkle root

Philosophy:
  "Truth is a data structure, not a declaration."
        """
    )

    parser.add_argument(
        '--db',
        default='nuledger.db',
        help='Path to SQLite database (default: nuledger.db)'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Trace command
    trace_parser = subparsers.add_parser('trace', help='Trace operation causal chain')
    trace_parser.add_argument('op_id', help='Operation ID to trace')

    # Verify command
    subparsers.add_parser('verify', help='Verify ledger integrity')

    # Stats command
    subparsers.add_parser('stats', help='Show ledger statistics')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export ledger to JSON')
    export_parser.add_argument('output', help='Output JSON file')

    # Root command
    subparsers.add_parser('root', help='Show current Merkle root')

    args = parser.parse_args()

    # Load ledger
    if Path(args.db).exists():
        backend = SQLiteBackend(args.db)
    else:
        print(f"❌ Database not found: {args.db}")
        print("Create a ledger first by using NULedger in your application")
        sys.exit(1)

    ledger = Ledger(backend=backend)

    # Execute command
    try:
        if args.command == 'trace':
            trace_operation(ledger, args.op_id)
        elif args.command == 'verify':
            verify_ledger(ledger)
        elif args.command == 'stats':
            show_stats(ledger)
        elif args.command == 'export':
            export_ledger(ledger, args.output)
        elif args.command == 'root':
            show_root(ledger)
        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
