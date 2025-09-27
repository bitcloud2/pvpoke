"""Tests for Pokemon class."""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core import Pokemon, Stats, IVs


class TestPokemon(unittest.TestCase):
    """Test Pokemon class functionality."""
    
    def setUp(self):
        """Set up test Pokemon."""
        # Create a test Pokemon (Azumarill-like stats)
        self.base_stats = Stats(atk=112.2, defense=152.3, hp=225)
        self.pokemon = Pokemon(
            species_id="test_pokemon",
            species_name="Test Pokemon",
            dex=999,
            base_stats=self.base_stats,
            types=["water", "fairy"]
        )
    
    def test_iv_validation(self):
        """Test IV validation."""
        valid_ivs = IVs(10, 10, 10)
        valid_ivs.validate()  # Should not raise
        
        with self.assertRaises(ValueError):
            invalid_ivs = IVs(16, 10, 10)  # Attack IV too high
            invalid_ivs.validate()
        
        with self.assertRaises(ValueError):
            invalid_ivs = IVs(-1, 10, 10)  # Negative IV
            invalid_ivs.validate()
    
    def test_cp_calculation(self):
        """Test CP calculation."""
        self.pokemon.ivs = IVs(0, 15, 15)
        self.pokemon.level = 40
        
        cp = self.pokemon.calculate_cp()
        
        # CP should be a positive integer
        self.assertIsInstance(cp, int)
        self.assertGreater(cp, 0)
        
        # Test minimum CP
        self.pokemon.level = 1
        cp = self.pokemon.calculate_cp()
        self.assertGreaterEqual(cp, 10)  # Minimum CP is 10
    
    def test_stat_calculation(self):
        """Test stat calculation."""
        self.pokemon.ivs = IVs(0, 15, 15)
        self.pokemon.level = 40
        
        stats = self.pokemon.calculate_stats()
        
        # Stats should be calculated correctly
        self.assertIsInstance(stats.atk, float)
        self.assertIsInstance(stats.defense, float)
        self.assertIsInstance(stats.hp, int)
        
        self.assertGreater(stats.atk, 0)
        self.assertGreater(stats.defense, 0)
        self.assertGreater(stats.hp, 0)
    
    def test_shadow_bonuses(self):
        """Test shadow Pokemon bonuses/penalties."""
        self.pokemon.ivs = IVs(10, 10, 10)
        self.pokemon.level = 40
        
        # Normal stats
        normal_stats = self.pokemon.calculate_stats()
        
        # Shadow stats
        self.pokemon.shadow_type = "shadow"
        shadow_stats = self.pokemon.calculate_stats()
        
        # Shadow should have higher attack, lower defense
        self.assertGreater(shadow_stats.atk, normal_stats.atk)
        self.assertLess(shadow_stats.defense, normal_stats.defense)
        self.assertEqual(shadow_stats.hp, normal_stats.hp)  # HP unchanged
    
    def test_optimize_for_league(self):
        """Test IV optimization for Great League."""
        self.pokemon.optimize_for_league(1500)
        
        # Should have valid CP under limit
        self.assertLessEqual(self.pokemon.cp, 1500)
        self.assertGreater(self.pokemon.cp, 0)
        
        # Should have valid IVs
        self.assertIn(self.pokemon.ivs.atk, range(16))
        self.assertIn(self.pokemon.ivs.defense, range(16))
        self.assertIn(self.pokemon.ivs.hp, range(16))
        
        # Should have valid level
        self.assertGreaterEqual(self.pokemon.level, 1)
        self.assertLessEqual(self.pokemon.level, 50)
    
    def test_stat_buffs(self):
        """Test stat buff mechanics."""
        self.pokemon.ivs = IVs(10, 10, 10)
        self.pokemon.level = 40
        
        # Base effective stat
        base_atk = self.pokemon.get_effective_stat(0)
        base_def = self.pokemon.get_effective_stat(1)
        
        # Apply buff
        self.pokemon.stat_buffs = [1, 0]  # +1 attack stage
        buffed_atk = self.pokemon.get_effective_stat(0)
        
        # Attack should be increased
        self.assertGreater(buffed_atk, base_atk)
        self.assertAlmostEqual(buffed_atk, base_atk * 1.25, places=2)
        
        # Apply debuff
        self.pokemon.stat_buffs = [0, -2]  # -2 defense stages
        debuffed_def = self.pokemon.get_effective_stat(1)
        
        # Defense should be decreased
        self.assertLess(debuffed_def, base_def)
    
    def test_reset(self):
        """Test Pokemon reset."""
        self.pokemon.ivs = IVs(10, 10, 10)
        self.pokemon.level = 40
        self.pokemon.optimize_for_league(1500)
        
        # Modify state
        self.pokemon.current_hp = 50
        self.pokemon.energy = 75
        self.pokemon.stat_buffs = [1, -1]
        
        # Reset
        self.pokemon.reset()
        
        # Should reset to initial state
        stats = self.pokemon.calculate_stats()
        self.assertEqual(self.pokemon.current_hp, stats.hp)
        self.assertEqual(self.pokemon.energy, 0)
        self.assertEqual(self.pokemon.stat_buffs, [0, 0])


if __name__ == "__main__":
    unittest.main()
