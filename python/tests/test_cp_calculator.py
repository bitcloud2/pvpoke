"""Tests for CP calculation utilities."""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.utils.cp_calculator import CPCalculator
from pvpoke.core import Stats, IVs


class TestCPCalculator(unittest.TestCase):
    """Test CPCalculator functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Azumarill stats for testing
        self.azumarill_stats = Stats(atk=112.2, defense=152.3, hp=225)
        
        # Mewtwo stats for testing (high CP Pokemon)
        self.mewtwo_stats = Stats(atk=300, defense=182, hp=214)
        
        # Shuckle stats for testing (extreme defense)
        self.shuckle_stats = Stats(atk=17, defense=396, hp=85)
    
    def test_calculate_cp_basic(self):
        """Test basic CP calculation."""
        ivs = IVs(10, 10, 10)
        level = 20
        
        cp = CPCalculator.calculate_cp(self.azumarill_stats, ivs, level)
        
        # CP should be positive integer
        self.assertIsInstance(cp, int)
        self.assertGreater(cp, 0)
        
        # Azumarill at level 20 with 10/10/10 IVs should be around 800-900 CP
        self.assertGreater(cp, 700)
        self.assertLess(cp, 1000)
    
    def test_calculate_cp_perfect_ivs(self):
        """Test CP calculation with perfect IVs."""
        perfect_ivs = IVs(15, 15, 15)
        level = 40
        
        cp = CPCalculator.calculate_cp(self.azumarill_stats, perfect_ivs, level)
        
        # Perfect Azumarill at level 40 should be around 1500 CP
        self.assertGreater(cp, 1400)
        self.assertLess(cp, 1600)
    
    def test_calculate_cp_zero_ivs(self):
        """Test CP calculation with zero IVs."""
        zero_ivs = IVs(0, 0, 0)
        level = 40
        
        cp = CPCalculator.calculate_cp(self.azumarill_stats, zero_ivs, level)
        
        # Should still have positive CP
        self.assertGreater(cp, 0)
        
        # Should be less than perfect IVs
        perfect_cp = CPCalculator.calculate_cp(
            self.azumarill_stats, IVs(15, 15, 15), level
        )
        self.assertLess(cp, perfect_cp)
    
    def test_calculate_cp_minimum(self):
        """Test minimum CP is 10."""
        # Very low level and stats
        weak_stats = Stats(atk=10, defense=10, hp=10)
        ivs = IVs(0, 0, 0)
        level = 1
        
        cp = CPCalculator.calculate_cp(weak_stats, ivs, level)
        
        # Minimum CP should be 10
        self.assertEqual(cp, 10)
    
    def test_calculate_cp_level_scaling(self):
        """Test CP scales with level."""
        ivs = IVs(10, 10, 10)
        
        cp_level_10 = CPCalculator.calculate_cp(self.azumarill_stats, ivs, 10)
        cp_level_20 = CPCalculator.calculate_cp(self.azumarill_stats, ivs, 20)
        cp_level_30 = CPCalculator.calculate_cp(self.azumarill_stats, ivs, 30)
        cp_level_40 = CPCalculator.calculate_cp(self.azumarill_stats, ivs, 40)
        
        # CP should increase with level
        self.assertLess(cp_level_10, cp_level_20)
        self.assertLess(cp_level_20, cp_level_30)
        self.assertLess(cp_level_30, cp_level_40)
    
    def test_calculate_cp_iv_impact(self):
        """Test impact of different IV combinations."""
        level = 25
        
        # High attack IV
        high_atk = CPCalculator.calculate_cp(
            self.azumarill_stats, IVs(15, 0, 0), level
        )
        
        # High defense IV
        high_def = CPCalculator.calculate_cp(
            self.azumarill_stats, IVs(0, 15, 0), level
        )
        
        # High HP IV
        high_hp = CPCalculator.calculate_cp(
            self.azumarill_stats, IVs(0, 0, 15), level
        )
        
        # Attack has highest impact on CP
        self.assertGreater(high_atk, high_def)
        self.assertGreater(high_atk, high_hp)
    
    def test_optimize_ivs_for_league(self):
        """Test IV optimization for league CP limits."""
        # Optimize for Great League
        best_ivs, level = CPCalculator.optimize_ivs_for_league(
            self.azumarill_stats, 1500
        )
        
        # Should return valid IVs
        self.assertIsInstance(best_ivs, IVs)
        self.assertIn(best_ivs.atk, range(16))
        self.assertIn(best_ivs.defense, range(16))
        self.assertIn(best_ivs.hp, range(16))
        
        # Level should be valid
        self.assertGreaterEqual(level, 1)
        self.assertLessEqual(level, 50)
        
        # CP should be at or just under limit
        cp = CPCalculator.calculate_cp(self.azumarill_stats, best_ivs, level)
        self.assertLessEqual(cp, 1500)
        self.assertGreater(cp, 1400)  # Should be close to limit
    
    def test_optimize_ivs_prefer_bulk(self):
        """Test that IV optimization prefers bulk (def/hp) over attack."""
        best_ivs, _ = CPCalculator.optimize_ivs_for_league(
            self.azumarill_stats, 1500
        )
        
        # For most Pokemon, optimal IVs have low attack, high def/hp
        # This maximizes stat product under CP cap
        self.assertLessEqual(best_ivs.atk, 5)  # Usually low attack
        self.assertGreaterEqual(best_ivs.defense, 10)  # Usually high defense
        self.assertGreaterEqual(best_ivs.hp, 10)  # Usually high HP
    
    def test_optimize_ivs_high_cp_pokemon(self):
        """Test IV optimization for Pokemon that don't reach cap."""
        # Shuckle has very low attack, might not reach 1500 CP
        best_ivs, level = CPCalculator.optimize_ivs_for_league(
            self.shuckle_stats, 1500
        )
        
        # Should max out level
        self.assertEqual(level, 50)
        
        # Should use perfect IVs if can't reach cap
        cp = CPCalculator.calculate_cp(self.shuckle_stats, best_ivs, level)
        if cp < 1500:
            # If can't reach cap, should use 15/15/15
            self.assertEqual(best_ivs.atk, 15)
            self.assertEqual(best_ivs.defense, 15)
            self.assertEqual(best_ivs.hp, 15)
    
    def test_optimize_ivs_master_league(self):
        """Test IV optimization for Master League (no CP cap)."""
        best_ivs, level = CPCalculator.optimize_ivs_for_league(
            self.mewtwo_stats, 10000
        )
        
        # Should use max level
        self.assertEqual(level, 50)
        
        # Should use perfect IVs for max stats
        self.assertEqual(best_ivs.atk, 15)
        self.assertEqual(best_ivs.defense, 15)
        self.assertEqual(best_ivs.hp, 15)
    
    def test_get_cp_multiplier(self):
        """Test CP multiplier calculation for different levels."""
        # Test known multipliers
        mult_1 = CPCalculator.get_cp_multiplier(1)
        mult_10 = CPCalculator.get_cp_multiplier(10)
        mult_20 = CPCalculator.get_cp_multiplier(20)
        mult_30 = CPCalculator.get_cp_multiplier(30)
        mult_40 = CPCalculator.get_cp_multiplier(40)
        mult_50 = CPCalculator.get_cp_multiplier(50)
        
        # Multipliers should increase with level
        self.assertLess(mult_1, mult_10)
        self.assertLess(mult_10, mult_20)
        self.assertLess(mult_20, mult_30)
        self.assertLess(mult_30, mult_40)
        self.assertLess(mult_40, mult_50)
        
        # Check approximate values
        self.assertAlmostEqual(mult_1, 0.094, places=3)
        self.assertAlmostEqual(mult_40, 0.7903, places=3)
    
    def test_get_cp_multiplier_half_levels(self):
        """Test CP multiplier for half levels."""
        # Half levels should work
        mult_20_5 = CPCalculator.get_cp_multiplier(20.5)
        mult_20 = CPCalculator.get_cp_multiplier(20)
        mult_21 = CPCalculator.get_cp_multiplier(21)
        
        # Should be between whole levels
        self.assertGreater(mult_20_5, mult_20)
        self.assertLess(mult_20_5, mult_21)
    
    def test_calculate_stat_product(self):
        """Test stat product calculation."""
        ivs = IVs(0, 15, 15)
        level = 40
        
        stat_product = CPCalculator.calculate_stat_product(
            self.azumarill_stats, ivs, level
        )
        
        # Stat product should be positive
        self.assertGreater(stat_product, 0)
        
        # Compare different IV spreads
        sp_low_atk = stat_product
        sp_high_atk = CPCalculator.calculate_stat_product(
            self.azumarill_stats, IVs(15, 0, 0), level
        )
        
        # Low attack IV should have higher stat product at same level
        self.assertGreater(sp_low_atk, sp_high_atk)
    
    def test_find_breakpoints(self):
        """Test finding damage breakpoints."""
        # Find breakpoints for Azumarill vs another Pokemon
        defender_stats = Stats(atk=150, defense=150, hp=150)
        move_power = 7  # Bubble power
        
        breakpoints = CPCalculator.find_breakpoints(
            attacker_stats=self.azumarill_stats,
            defender_stats=defender_stats,
            move_power=move_power,
            attacker_ivs=IVs(0, 15, 15),
            defender_ivs=IVs(15, 15, 15)
        )
        
        # Should return list of breakpoints
        self.assertIsInstance(breakpoints, list)
        
        # Each breakpoint should have level and damage
        for bp in breakpoints:
            self.assertIn("level", bp)
            self.assertIn("damage", bp)
            self.assertGreaterEqual(bp["level"], 1)
            self.assertLessEqual(bp["level"], 50)
            self.assertGreater(bp["damage"], 0)
    
    def test_calculate_effective_stats(self):
        """Test effective stat calculation."""
        ivs = IVs(10, 10, 10)
        level = 25
        
        stats = CPCalculator.calculate_effective_stats(
            self.azumarill_stats, ivs, level
        )
        
        # Should return Stats object
        self.assertIsInstance(stats, Stats)
        
        # Stats should be positive
        self.assertGreater(stats.atk, 0)
        self.assertGreater(stats.defense, 0)
        self.assertGreater(stats.hp, 0)
        
        # HP should be integer
        self.assertIsInstance(stats.hp, int)
    
    def test_level_from_cp(self):
        """Test calculating level from target CP."""
        ivs = IVs(0, 15, 15)
        target_cp = 1500
        
        level = CPCalculator.get_level_for_cp(
            self.azumarill_stats, ivs, target_cp
        )
        
        # Should return valid level
        self.assertGreaterEqual(level, 1)
        self.assertLessEqual(level, 50)
        
        # CP at that level should be close to target
        actual_cp = CPCalculator.calculate_cp(
            self.azumarill_stats, ivs, level
        )
        self.assertLessEqual(actual_cp, target_cp)
        self.assertGreater(actual_cp, target_cp - 50)  # Within 50 CP
    
    def test_compare_iv_spreads(self):
        """Test comparing different IV spreads."""
        spreads = [
            IVs(0, 15, 15),   # Rank 1 typical
            IVs(15, 15, 15),  # Perfect
            IVs(15, 0, 0),    # High attack
            IVs(0, 0, 15),    # High HP only
        ]
        
        comparisons = CPCalculator.compare_iv_spreads(
            self.azumarill_stats, spreads, 1500
        )
        
        # Should return comparison data for each spread
        self.assertEqual(len(comparisons), 4)
        
        # Each comparison should have relevant metrics
        for comp in comparisons:
            self.assertIn("ivs", comp)
            self.assertIn("level", comp)
            self.assertIn("cp", comp)
            self.assertIn("stat_product", comp)
            self.assertIn("rank", comp)
        
        # Ranks should be 1-4
        ranks = [c["rank"] for c in comparisons]
        self.assertEqual(sorted(ranks), [1, 2, 3, 4])
        
        # Rank 1 should have highest stat product
        rank_1 = next(c for c in comparisons if c["rank"] == 1)
        for comp in comparisons:
            if comp["rank"] != 1:
                self.assertGreaterEqual(
                    rank_1["stat_product"], 
                    comp["stat_product"]
                )


if __name__ == "__main__":
    unittest.main()
