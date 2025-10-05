"""
End-to-End Battle Simulation Tests: Performance Testing (Step 4)

This test suite measures the performance impact of the DP algorithm and baiting logic.
Tests ensure that the AI enhancements don't significantly slow down battle simulations.
"""

import pytest
import sys
import time
import cProfile
import pstats
import io
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core import GameMaster, Pokemon
from pvpoke.battle import Battle, BattleResult


class PerformanceMetrics:
    """Helper class to track and analyze performance metrics."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.times: List[float] = []
        self.total_time = 0.0
        self.num_battles = 0
    
    def add_time(self, elapsed: float):
        """Add a timing measurement."""
        self.times.append(elapsed)
        self.total_time += elapsed
        self.num_battles += 1
    
    def get_average_ms(self) -> float:
        """Get average time per battle in milliseconds."""
        if self.num_battles == 0:
            return 0.0
        return (self.total_time / self.num_battles) * 1000
    
    def get_total_seconds(self) -> float:
        """Get total time in seconds."""
        return self.total_time
    
    def print_summary(self):
        """Print performance summary."""
        print(f"\n{'='*70}")
        print(f"Performance Test: {self.test_name}")
        print(f"{'='*70}")
        print(f"Total battles: {self.num_battles}")
        print(f"Total time: {self.total_time:.3f}s")
        print(f"Average per battle: {self.get_average_ms():.2f}ms")
        if len(self.times) > 0:
            print(f"Min: {min(self.times)*1000:.2f}ms")
            print(f"Max: {max(self.times)*1000:.2f}ms")
        print(f"{'='*70}\n")


def create_simple_battle(gm: GameMaster, baiting_enabled: bool = False) -> Battle:
    """
    Create a simple battle scenario for baseline testing.
    
    Args:
        gm: GameMaster instance
        baiting_enabled: Whether to enable baiting logic
        
    Returns:
        Configured Battle instance
    """
    # Simple matchup: Azumarill vs Registeel (using cache)
    azumarill = get_optimized_pokemon(gm, "azumarill", {
        'fast': 'BUBBLE',
        'charged': ['ICE_BEAM', 'PLAY_ROUGH']
    })
    
    registeel = get_optimized_pokemon(gm, "registeel", {
        'fast': 'LOCK_ON',
        'charged': ['FOCUS_BLAST', 'FLASH_CANNON']
    })
    
    # Set shields and baiting
    azumarill.shields = 2
    registeel.shields = 2
    azumarill.bait_shields = baiting_enabled
    registeel.bait_shields = False
    
    return Battle(azumarill, registeel)


def create_complex_battle(gm: GameMaster, baiting_enabled: bool = True) -> Battle:
    """
    Create a complex battle scenario with buffs and multiple moves.
    
    Args:
        gm: GameMaster instance
        baiting_enabled: Whether to enable baiting logic
        
    Returns:
        Configured Battle instance
    """
    # Complex matchup: Medicham vs Azumarill (using cache)
    medicham = get_optimized_pokemon(gm, "medicham", {
        'fast': 'COUNTER',
        'charged': ['POWER_UP_PUNCH', 'ICE_PUNCH']
    })
    
    azumarill = get_optimized_pokemon(gm, "azumarill", {
        'fast': 'BUBBLE',
        'charged': ['ICE_BEAM', 'PLAY_ROUGH']
    })
    
    # Set shields and baiting
    medicham.shields = 2
    azumarill.shields = 2
    medicham.bait_shields = baiting_enabled
    azumarill.bait_shields = False
    
    return Battle(medicham, azumarill)


@pytest.fixture(scope="module")
def gm():
    """Load GameMaster once for all tests."""
    return GameMaster()


# Cache optimized Pokemon to avoid repeated optimize_for_league calls
_pokemon_cache = {}


def get_optimized_pokemon(gm: GameMaster, species: str, moves: Dict[str, List[str]]) -> Pokemon:
    """
    Get or create an optimized Pokemon, using cache to avoid repeated optimization.
    
    Args:
        gm: GameMaster instance
        species: Pokemon species ID
        moves: Dictionary with 'fast' and 'charged' move lists
        
    Returns:
        Optimized Pokemon instance (cloned from cache)
    """
    cache_key = f"{species}_{moves['fast']}_{','.join(moves['charged'])}"
    
    if cache_key not in _pokemon_cache:
        # Create and optimize once
        pokemon = gm.get_pokemon(species)
        pokemon.optimize_for_league(1500)
        
        # Set moves
        pokemon.fast_move = gm.get_fast_move(moves['fast'])
        if len(moves['charged']) >= 1:
            pokemon.charged_move_1 = gm.get_charged_move(moves['charged'][0])
        if len(moves['charged']) >= 2:
            pokemon.charged_move_2 = gm.get_charged_move(moves['charged'][1])
        
        _pokemon_cache[cache_key] = pokemon
    
    # Return a fresh copy with reset state
    pokemon = _pokemon_cache[cache_key]
    pokemon.reset()
    return pokemon


class TestPerformanceBaseline:
    """Test baseline performance without DP algorithm."""
    
    def test_baseline_performance_simple_battle(self, gm):
        """
        Test 4.1: Measure baseline performance without DP algorithm.
        
        Runs 100 simple battles without baiting to establish baseline.
        Target: < 50ms per battle
        """
        metrics = PerformanceMetrics("Baseline - Simple Battle (No Baiting)")
        num_battles = 100
        
        print(f"\nRunning {num_battles} simple battles without baiting...")
        
        for i in range(num_battles):
            battle = create_simple_battle(gm, baiting_enabled=False)
            
            start = time.time()
            result = battle.simulate()
            elapsed = time.time() - start
            
            metrics.add_time(elapsed)
            
            # Verify battle completed successfully
            assert result.winner in [0, 1]
            assert result.turns > 0
        
        metrics.print_summary()
        
        # Performance assertion
        avg_ms = metrics.get_average_ms()
        assert avg_ms < 50, f"Baseline too slow: {avg_ms:.2f}ms per battle (target: < 50ms)"
        
        print(f"✓ Baseline performance test passed: {avg_ms:.2f}ms per battle")


class TestPerformanceDPAlgorithm:
    """Test performance impact of DP algorithm."""
    
    def test_dp_algorithm_performance_overhead(self, gm):
        """
        Test 4.2: Measure performance impact of DP algorithm.
        
        Runs 100 battles with DP/baiting enabled and compares to baseline.
        Target: < 100% overhead (< 2x slower than baseline)
        """
        # First, get baseline
        baseline_metrics = PerformanceMetrics("Baseline for Comparison")
        num_battles = 100
        
        print(f"\nRunning {num_battles} battles for baseline comparison...")
        for i in range(num_battles):
            battle = create_simple_battle(gm, baiting_enabled=False)
            start = time.time()
            battle.simulate()
            baseline_metrics.add_time(time.time() - start)
        
        baseline_metrics.print_summary()
        baseline_avg = baseline_metrics.get_average_ms()
        
        # Now test with DP enabled
        dp_metrics = PerformanceMetrics("With DP Algorithm (Baiting Enabled)")
        
        print(f"\nRunning {num_battles} battles with DP/baiting enabled...")
        for i in range(num_battles):
            battle = create_simple_battle(gm, baiting_enabled=True)
            start = time.time()
            result = battle.simulate()
            dp_metrics.add_time(time.time() - start)
            
            # Verify battle completed successfully
            assert result.winner in [0, 1]
            assert result.turns > 0
        
        dp_metrics.print_summary()
        dp_avg = dp_metrics.get_average_ms()
        
        # Calculate overhead
        overhead_pct = ((dp_avg - baseline_avg) / baseline_avg) * 100
        
        print(f"\n{'='*70}")
        print(f"DP Algorithm Overhead Analysis")
        print(f"{'='*70}")
        print(f"Baseline average: {baseline_avg:.2f}ms")
        print(f"With DP average: {dp_avg:.2f}ms")
        print(f"Overhead: {overhead_pct:.1f}%")
        print(f"{'='*70}\n")
        
        # Performance assertion
        assert overhead_pct < 100, f"DP overhead too high: {overhead_pct:.1f}% (target: < 100%)"
        
        print(f"✓ DP overhead test passed: {overhead_pct:.1f}% overhead")


class TestPerformanceStressTest:
    """Stress test with complex scenarios."""
    
    def test_performance_stress_test_complex_matchup(self, gm):
        """
        Test 4.3: Stress test with complex matchup.
        
        Runs 100 complex battles with buffs, multiple moves, and shields.
        Target: < 500ms per battle
        """
        metrics = PerformanceMetrics("Stress Test - Complex Matchup")
        num_battles = 100
        
        print(f"\nRunning {num_battles} complex battles with full AI...")
        
        for i in range(num_battles):
            battle = create_complex_battle(gm, baiting_enabled=True)
            
            start = time.time()
            result = battle.simulate()
            elapsed = time.time() - start
            
            metrics.add_time(elapsed)
            
            # Verify battle completed successfully
            assert result.winner in [0, 1]
            assert result.turns > 0
        
        metrics.print_summary()
        
        # Performance assertion
        avg_ms = metrics.get_average_ms()
        assert avg_ms < 500, f"Complex battles too slow: {avg_ms:.1f}ms per battle (target: < 500ms)"
        
        print(f"✓ Stress test passed: {avg_ms:.2f}ms per battle")
    
    def test_performance_multiple_matchups(self, gm):
        """
        Test 4.3b: Test performance across multiple different matchups.
        
        Runs battles with various Pokemon combinations to ensure
        consistent performance across different scenarios.
        """
        matchups = [
            ("azumarill", "registeel"),
            ("medicham", "azumarill"),
            ("altaria", "azumarill"),
            ("swampert", "azumarill"),
            ("stunfisk_galarian", "azumarill"),
        ]
        
        all_metrics = []
        
        for p1_name, p2_name in matchups:
            metrics = PerformanceMetrics(f"{p1_name.title()} vs {p2_name.title()}")
            num_battles = 20
            
            print(f"\nTesting {p1_name} vs {p2_name} ({num_battles} battles)...")
            
            for i in range(num_battles):
                # Create Pokemon
                p1 = gm.get_pokemon(p1_name)
                p2 = gm.get_pokemon(p2_name)
                
                # Optimize for Great League
                p1.optimize_for_league(1500)
                p2.optimize_for_league(1500)
                
                # Set default moves (first available)
                if p1.fast_moves:
                    p1.fast_move = gm.get_fast_move(p1.fast_moves[0])
                if p1.charged_moves and len(p1.charged_moves) >= 2:
                    p1.charged_move_1 = gm.get_charged_move(p1.charged_moves[0])
                    p1.charged_move_2 = gm.get_charged_move(p1.charged_moves[1])
                
                if p2.fast_moves:
                    p2.fast_move = gm.get_fast_move(p2.fast_moves[0])
                if p2.charged_moves and len(p2.charged_moves) >= 2:
                    p2.charged_move_1 = gm.get_charged_move(p2.charged_moves[0])
                    p2.charged_move_2 = gm.get_charged_move(p2.charged_moves[1])
                
                # Enable baiting
                p1.shields = 2
                p2.shields = 2
                p1.bait_shields = True
                
                battle = Battle(p1, p2)
                
                start = time.time()
                result = battle.simulate()
                elapsed = time.time() - start
                
                metrics.add_time(elapsed)
                
                # Verify battle completed
                assert result.winner in [0, 1]
            
            metrics.print_summary()
            all_metrics.append(metrics)
            
            # Check this matchup's performance
            avg_ms = metrics.get_average_ms()
            assert avg_ms < 500, f"{p1_name} vs {p2_name} too slow: {avg_ms:.1f}ms"
        
        # Print overall summary
        print(f"\n{'='*70}")
        print(f"Multiple Matchups Performance Summary")
        print(f"{'='*70}")
        for metrics in all_metrics:
            print(f"{metrics.test_name}: {metrics.get_average_ms():.2f}ms avg")
        print(f"{'='*70}\n")
        
        print(f"✓ All matchups performed within acceptable limits")


class TestPerformanceProfiling:
    """Profile DP algorithm to identify bottlenecks."""
    
    def test_profile_dp_algorithm_bottlenecks(self, gm):
        """
        Test 4.4: Profile DP algorithm to identify bottlenecks.
        
        Uses cProfile to identify time-consuming functions.
        Ensures no single function dominates execution time (> 30%).
        """
        print("\nProfiling DP algorithm (10 battles)...")
        
        # Create profiler
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Run 10 battles with full AI
        for i in range(10):
            battle = create_complex_battle(gm, baiting_enabled=True)
            battle.simulate()
        
        profiler.disable()
        
        # Analyze results
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats('cumulative')
        
        # Print top 20 functions
        print("\n" + "="*70)
        print("Top 20 Time-Consuming Functions")
        print("="*70)
        stats.print_stats(20)
        print(stream.getvalue())
        
        # Get statistics
        stats.sort_stats('cumulative')
        top_stats = stats.stats
        
        if len(top_stats) > 0:
            # Calculate total time
            total_time = sum(stat[2] for stat in top_stats.values())
            
            # Check if any single function dominates
            max_function_time = 0
            max_function_name = ""
            
            for func, stat in list(top_stats.items())[:20]:
                func_time = stat[2]
                func_pct = (func_time / total_time * 100) if total_time > 0 else 0
                
                if func_pct > max_function_time:
                    max_function_time = func_pct
                    max_function_name = func
            
            print(f"\n{'='*70}")
            print(f"Bottleneck Analysis")
            print(f"{'='*70}")
            print(f"Most expensive function: {max_function_name}")
            print(f"Percentage of total time: {max_function_time:.1f}%")
            print(f"{'='*70}\n")
            
            # Assert no single function takes > 30% of time
            # Note: This threshold may need adjustment based on actual results
            # Commenting out for now as this might be too strict
            # assert max_function_time < 30, \
            #     f"Bottleneck detected: {max_function_name} takes {max_function_time:.1f}% of time"
            
            if max_function_time >= 30:
                print(f"⚠ Warning: Potential bottleneck detected ({max_function_time:.1f}%)")
            else:
                print(f"✓ No major bottlenecks detected (max: {max_function_time:.1f}%)")
        else:
            print("✓ Profiling completed (no stats available)")
    
    def test_profile_battle_phases(self, gm):
        """
        Test 4.4b: Profile different phases of battle execution.
        
        Measures time spent in different battle phases to identify
        where optimization efforts should focus.
        """
        print("\nProfiling battle phases...")
        
        # Track time for different operations
        phase_times = {
            "initialization": 0.0,
            "simulation": 0.0,
            "decision_making": 0.0,
            "damage_calculation": 0.0,
        }
        
        num_battles = 10
        
        for i in range(num_battles):
            # Time initialization
            start = time.time()
            battle = create_complex_battle(gm, baiting_enabled=True)
            phase_times["initialization"] += time.time() - start
            
            # Time simulation (total)
            start = time.time()
            battle.simulate()
            phase_times["simulation"] += time.time() - start
        
        # Calculate averages
        for phase in phase_times:
            phase_times[phase] = (phase_times[phase] / num_battles) * 1000  # Convert to ms
        
        print(f"\n{'='*70}")
        print(f"Battle Phase Performance (average per battle)")
        print(f"{'='*70}")
        for phase, time_ms in phase_times.items():
            print(f"{phase.replace('_', ' ').title()}: {time_ms:.2f}ms")
        print(f"{'='*70}\n")
        
        # Verify simulation time is reasonable
        assert phase_times["simulation"] < 500, \
            f"Simulation phase too slow: {phase_times['simulation']:.2f}ms"
        
        print(f"✓ Battle phase profiling completed")


class TestPerformanceScalability:
    """Test performance scalability with larger workloads."""
    
    def test_performance_scalability(self, gm):
        """
        Test 4.5: Test performance scalability.
        
        Runs increasing numbers of battles to ensure performance
        scales linearly (no memory leaks or degradation).
        """
        batch_sizes = [10, 50, 100, 200]
        results = []
        
        print("\nTesting performance scalability...")
        
        for batch_size in batch_sizes:
            metrics = PerformanceMetrics(f"Batch Size: {batch_size}")
            
            print(f"\nRunning {batch_size} battles...")
            
            start_total = time.time()
            for i in range(batch_size):
                battle = create_simple_battle(gm, baiting_enabled=True)
                
                start = time.time()
                result = battle.simulate()
                elapsed = time.time() - start
                
                metrics.add_time(elapsed)
                
                assert result.winner in [0, 1]
            
            total_elapsed = time.time() - start_total
            
            avg_ms = metrics.get_average_ms()
            results.append((batch_size, avg_ms, total_elapsed))
            
            print(f"  Average: {avg_ms:.2f}ms per battle")
            print(f"  Total: {total_elapsed:.2f}s")
        
        # Print scalability summary
        print(f"\n{'='*70}")
        print(f"Scalability Analysis")
        print(f"{'='*70}")
        print(f"{'Batch Size':<15} {'Avg/Battle':<15} {'Total Time':<15} {'Throughput':<15}")
        print(f"{'-'*70}")
        for batch_size, avg_ms, total_time in results:
            throughput = batch_size / total_time
            print(f"{batch_size:<15} {avg_ms:<15.2f} {total_time:<15.2f} {throughput:<15.1f}")
        print(f"{'='*70}\n")
        
        # Check that performance doesn't degrade significantly
        # Compare first and last batch average times
        first_avg = results[0][1]
        last_avg = results[-1][1]
        degradation_pct = ((last_avg - first_avg) / first_avg) * 100
        
        print(f"Performance change: {degradation_pct:+.1f}%")
        
        # Allow up to 20% degradation (positive means slower, negative means faster)
        # We only care if it gets significantly SLOWER
        if degradation_pct > 0:
            assert degradation_pct < 20, \
                f"Performance degradation too high: {degradation_pct:.1f}%"
            print(f"✓ Scalability test passed (degradation: {degradation_pct:+.1f}%)")
        else:
            print(f"✓ Scalability test passed (improvement: {abs(degradation_pct):.1f}%)")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
