"""
test_performance.py

Performance benchmarks for eBIOS layers

Verifies spec claims (CI-adjusted for shared runners):
- NUCore operations: <2.5μs per operation (local: 0.1-0.2μs)
- NULedger: >1000 ops/sec throughput
- Merkle verification: <500ms for 10K entries (local: <50ms)
- O(1) complexity guarantees

Note: CI specs are 2-5x more lenient than local hardware to account for
shared runner variability. Real-time capability maintained.
"""

import pytest
import time
import statistics
from src.nucore import add, multiply, compose, catch, flip
from src.nuledger import Ledger, MemoryBackend, SQLiteBackend
import tempfile


class TestNUCorePerformance:
    """
    Benchmark NUCore operation latencies

    Spec (CI): All operations must complete in <2.5μs (O(1) constant time)
    Spec (Local): <0.5μs typical on modern hardware
    """

    def benchmark_operation(self, op_func, *args, iterations=10000):
        """Run operation many times and measure statistics"""
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            result = op_func(*args)
            end = time.perf_counter()
            times.append((end - start) * 1e6)  # Convert to microseconds

        return {
            'mean_us': statistics.mean(times),
            'median_us': statistics.median(times),
            'min_us': min(times),
            'max_us': max(times),
            'stdev_us': statistics.stdev(times) if len(times) > 1 else 0,
            'iterations': iterations
        }

    def test_add_performance(self):
        """Benchmark addition operation"""
        stats = self.benchmark_operation(add, 10.0, 0.5, 20.0, 1.0)

        print(f"\n  Add operation: {stats['mean_us']:.3f}μs avg, {stats['median_us']:.3f}μs median")

        # Spec: <2.5μs average (CI-adjusted)
        assert stats['mean_us'] < 2.5, f"Add too slow: {stats['mean_us']:.3f}μs (spec: <2.5μs)"

    def test_multiply_performance(self):
        """Benchmark multiplication operation"""
        stats = self.benchmark_operation(multiply, 5.0, 0.1, 3.0, 0.2)

        print(f"\n  Multiply operation: {stats['mean_us']:.3f}μs avg, {stats['median_us']:.3f}μs median")

        assert stats['mean_us'] < 2.5, f"Multiply too slow: {stats['mean_us']:.3f}μs (spec: <2.5μs)"

    def test_compose_performance(self):
        """Benchmark composition (sensor fusion) operation"""
        stats = self.benchmark_operation(compose, 100.0, 5.0, 102.0, 2.0)

        print(f"\n  Compose operation: {stats['mean_us']:.3f}μs avg, {stats['median_us']:.3f}μs median")

        assert stats['mean_us'] < 2.5, f"Compose too slow: {stats['mean_us']:.3f}μs (spec: <2.5μs)"

    def test_catch_performance(self):
        """Benchmark catch operation"""
        stats = self.benchmark_operation(catch, 10.0, 5.0, 0.0)

        print(f"\n  Catch operation: {stats['mean_us']:.3f}μs avg, {stats['median_us']:.3f}μs median")

        assert stats['mean_us'] < 2.5, f"Catch too slow: {stats['mean_us']:.3f}μs (spec: <2.5μs)"

    def test_flip_performance(self):
        """Benchmark flip operation"""
        stats = self.benchmark_operation(flip, 42.0, 3.14)

        print(f"\n  Flip operation: {stats['mean_us']:.3f}μs avg, {stats['median_us']:.3f}μs median")

        assert stats['mean_us'] < 2.5, f"Flip too slow: {stats['mean_us']:.3f}μs (spec: <2.5μs)"

    def test_operation_consistency(self):
        """Verify operations have consistent timing (O(1) not O(n))"""
        # Small values
        stats_small = self.benchmark_operation(add, 1.0, 0.1, 2.0, 0.1, iterations=5000)

        # Large values (should be same time - O(1))
        stats_large = self.benchmark_operation(add, 1e100, 1e99, 2e100, 1e99, iterations=5000)

        # Ratio should be close to 1.0 (within 2x for O(1))
        ratio = stats_large['mean_us'] / stats_small['mean_us']

        print(f"\n  Small values: {stats_small['mean_us']:.3f}μs")
        print(f"  Large values: {stats_large['mean_us']:.3f}μs")
        print(f"  Ratio: {ratio:.2f}x")

        assert ratio < 2.0, f"Not O(1): large/small ratio = {ratio:.2f}x (should be ~1.0)"


class TestNULedgerPerformance:
    """
    Benchmark NULedger throughput

    Spec: >1000 operations/second for append operations
    """

    def test_memory_backend_throughput(self):
        """Benchmark append throughput with memory backend"""
        ledger = Ledger(backend=MemoryBackend())

        num_ops = 10000
        start = time.perf_counter()

        for i in range(num_ops):
            ledger.append(
                operation="test",
                inputs=[(10.0, 0.5)],
                output=(10.0, 0.5),
                coverage=0.05,
                invariant_passed=True
            )

        end = time.perf_counter()
        elapsed = end - start
        throughput = num_ops / elapsed

        print(f"\n  Memory backend: {throughput:.0f} ops/sec ({elapsed:.3f}s for {num_ops} ops)")

        # Spec: >1000 ops/sec
        assert throughput > 1000, f"Throughput too low: {throughput:.0f} ops/sec (spec: >1000)"

    def test_sqlite_backend_throughput(self):
        """Benchmark append throughput with SQLite backend"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/bench.db"
            ledger = Ledger(backend=SQLiteBackend(db_path))

            num_ops = 1000  # Fewer for SQLite (disk I/O)
            start = time.perf_counter()

            for i in range(num_ops):
                ledger.append(
                    operation="test",
                    inputs=[(10.0, 0.5)],
                    output=(10.0, 0.5),
                    coverage=0.05,
                    invariant_passed=True
                )

            end = time.perf_counter()
            elapsed = end - start
            throughput = num_ops / elapsed

            print(f"\n  SQLite backend: {throughput:.0f} ops/sec ({elapsed:.3f}s for {num_ops} ops)")

            # SQLite is slower but should still be usable (>100 ops/sec)
            assert throughput > 100, f"SQLite too slow: {throughput:.0f} ops/sec"

    def test_merkle_verification_performance(self):
        """Benchmark Merkle tree verification time"""
        ledger = Ledger(backend=MemoryBackend())

        # Build ledger with 10K entries
        for i in range(10000):
            ledger.append("test", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)

        # Time verification
        start = time.perf_counter()
        result = ledger.verify_integrity()
        end = time.perf_counter()

        elapsed_ms = (end - start) * 1000

        print(f"\n  Merkle verification (10K entries): {elapsed_ms:.2f}ms")

        assert result is True
        # CI-adjusted spec: <500ms for 10K entries (local: <50ms typical)
        assert elapsed_ms < 500, f"Verification too slow: {elapsed_ms:.2f}ms (spec: <500ms)"

    def test_ledger_scaling(self):
        """Verify ledger append time doesn't degrade with size"""
        ledger = Ledger(backend=MemoryBackend())

        # Measure append time at different ledger sizes
        sizes = [100, 1000, 10000]
        times = []

        for target_size in sizes:
            # Grow ledger to target size
            while len(ledger) < target_size:
                ledger.append("test", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)

            # Measure next 100 appends
            start = time.perf_counter()
            for _ in range(100):
                ledger.append("test", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)
            end = time.perf_counter()

            avg_time_us = ((end - start) / 100) * 1e6
            times.append(avg_time_us)

            print(f"\n  Ledger size {target_size}: {avg_time_us:.2f}μs per append")

        # Check that time doesn't grow significantly (should be O(log n) for Merkle)
        # Allow up to 3x slowdown from smallest to largest
        ratio = times[-1] / times[0]
        assert ratio < 3.0, f"Append time degraded {ratio:.2f}x (should be ~constant)"


class TestIntegrationPerformance:
    """
    Benchmark realistic end-to-end scenarios
    """

    def test_sensor_fusion_pipeline_latency(self):
        """Benchmark complete sensor fusion with logging pipeline"""
        ledger = Ledger(backend=MemoryBackend())

        iterations = 1000
        times = []

        for i in range(iterations):
            # Simulate sensor fusion scenario
            start = time.perf_counter()

            # Step 1: Radar measurement
            radar_n, radar_u = 1000.0, 50.0

            # Step 2: Visual measurement
            visual_n, visual_u = 1020.0, 10.0

            # Step 3: Fuse measurements
            fused_n, fused_u = compose(radar_n, radar_u, visual_n, visual_u)

            # Step 4: Log to ledger
            ledger.append(
                operation="sensor_fusion",
                inputs=[(radar_n, radar_u), (visual_n, visual_u)],
                output=(fused_n, fused_u),
                coverage=fused_u / abs(fused_n) if fused_n != 0 else float('inf'),
                invariant_passed=True
            )

            end = time.perf_counter()
            times.append((end - start) * 1e6)  # microseconds

        mean_us = statistics.mean(times)
        median_us = statistics.median(times)

        print(f"\n  End-to-end fusion pipeline: {mean_us:.2f}μs avg, {median_us:.2f}μs median")

        # CI-adjusted: <150μs (local: <50μs typical)
        # Still suitable for real-time systems (6.6kHz update rate)
        assert mean_us < 150, f"Pipeline too slow: {mean_us:.2f}μs (spec: <150μs)"

    def test_multi_step_calculation_throughput(self):
        """Benchmark multi-step calculation chain"""
        ledger = Ledger(backend=MemoryBackend())

        num_chains = 1000
        ops_per_chain = 5

        start = time.perf_counter()

        for chain_id in range(num_chains):
            # Chain of 5 operations
            n, u = 10.0, 1.0
            parent_id = None

            for step in range(ops_per_chain):
                # Perform operation
                n, u = multiply(n, u, 1.1, 0.1)

                # Log
                entry = ledger.append(
                    operation=f"step_{step}",
                    inputs=[(n, u)],
                    output=(n, u),
                    coverage=u/abs(n) if n != 0 else float('inf'),
                    invariant_passed=True,
                    parent_id=parent_id
                )
                parent_id = entry.op_id

        end = time.perf_counter()
        elapsed = end - start

        total_ops = num_chains * ops_per_chain
        throughput = total_ops / elapsed

        print(f"\n  Multi-step chains: {throughput:.0f} ops/sec ({total_ops} ops in {elapsed:.3f}s)")

        # Should maintain >1000 ops/sec even with chaining
        assert throughput > 1000, f"Chained throughput too low: {throughput:.0f} ops/sec"


class TestMemoryUsage:
    """
    Verify memory usage is reasonable
    """

    def test_ledger_memory_footprint(self):
        """Check memory footprint of ledger entries"""
        import sys

        ledger = Ledger(backend=MemoryBackend())

        # Add 10K entries
        num_entries = 10000
        for i in range(num_entries):
            ledger.append("test", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)

        # Estimate memory (rough)
        # Each entry has: timestamp, op_id (UUID), operation str, inputs, output, signature
        # Approximate: ~500 bytes per entry conservatively

        entries = ledger.backend.get_all()
        expected_mb = (num_entries * 500) / (1024 * 1024)

        print(f"\n  {num_entries} entries: ~{expected_mb:.2f}MB estimated")

        # Just verify we can handle 10K entries (should be fine)
        assert len(entries) == num_entries


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_performance.py -v -s
    pytest.main([__file__, "-v", "-s"])
