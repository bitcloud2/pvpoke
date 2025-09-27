"""Tests for damage calculation system."""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core import Pokemon, Stats, IVs
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.battle.damage_calculator import DamageCalculator


class TestDamageCalculator(unittest.TestCase):
    """Test DamageCalculator functionality."""
    
    def setUp(self):
        """Set up test Pokemon and moves."""
        # Create water/fairy Pokemon (Azumarill-like)
        self.attacker = Pokemon(
            species_id="azumarill",
            species_name="Azumarill",
            dex=184,
            base_stats=Stats(atk=112.2, defense=152.3, hp=225),
            types=["water", "fairy"]
        )
        
        # Create fire Pokemon (vulnerable to water)
        self.defender = Pokemon(
            species_id="charizard",
            species_name="Charizard",
            dex=6,
            base_stats=Stats(atk=223, defense=173, hp=186),
            types=["fire", "flying"]
        )
        
        # Set IVs and level
        self.attacker.ivs = IVs(0, 15, 15)
        self.attacker.level = 40
        self.attacker.reset()
        
        self.defender.ivs = IVs(0, 15, 15)
        self.defender.level = 40
        self.defender.reset()
        
        # Create test moves
        self.water_fast = FastMove(
            move_id="BUBBLE",
            name="Bubble",
            move_type="water",
            power=7,
            energy_gain=11,
            turns=3
        )
        
        self.water_charged = ChargedMove(
            move_id="HYDRO_PUMP",
            name="Hydro Pump",
            move_type="water",
            power=130,
            energy_cost=75
        )
        
        self.normal_fast = FastMove(
            move_id="TACKLE",
            name="Tackle",
            move_type="normal",
            power=5,
            energy_gain=5,
            turns=1
        )
        
        self.ice_charged = ChargedMove(
            move_id="ICE_BEAM",
            name="Ice Beam",
            move_type="ice",
            power=90,
            energy_cost=55
        )
    
    def test_calculate_fast_move_damage_basic(self):
        """Test basic fast move damage calculation."""
        damage, energy = DamageCalculator.calculate_fast_move_damage(
            self.attacker, self.defender, self.water_fast
        )
        
        # Should deal damage
        self.assertGreater(damage, 0)
        # Should gain energy
        self.assertEqual(energy, self.water_fast.energy_gain)
    
    def test_calculate_fast_move_damage_super_effective(self):
        """Test super effective fast move damage."""
        # Water vs Fire should be super effective (1.6x)
        damage_se, _ = DamageCalculator.calculate_fast_move_damage(
            self.attacker, self.defender, self.water_fast
        )
        
        # Normal vs Fire should be neutral
        damage_neutral, _ = DamageCalculator.calculate_fast_move_damage(
            self.attacker, self.defender, self.normal_fast
        )
        
        # Super effective should deal more damage (accounting for base power difference)
        # Normalize by power: water_fast has 7 power, normal_fast has 5 power
        normalized_se = damage_se / self.water_fast.power
        normalized_neutral = damage_neutral / self.normal_fast.power
        
        self.assertGreater(normalized_se, normalized_neutral)
    
    def test_calculate_charged_move_damage_basic(self):
        """Test basic charged move damage calculation."""
        damage = DamageCalculator.calculate_charged_move_damage(
            self.attacker, self.defender, self.water_charged, shields=0
        )
        
        # Should deal damage
        self.assertGreater(damage, 0)
        # Should be integer
        self.assertIsInstance(damage, int)
    
    def test_calculate_charged_move_damage_with_stab(self):
        """Test STAB bonus for charged moves."""
        # Water move from water Pokemon should get STAB
        damage_stab = DamageCalculator.calculate_charged_move_damage(
            self.attacker, self.defender, self.water_charged, shields=0
        )
        
        # Ice move from water/fairy Pokemon should not get STAB
        damage_no_stab = DamageCalculator.calculate_charged_move_damage(
            self.attacker, self.defender, self.ice_charged, shields=0
        )
        
        # Normalize by power
        normalized_stab = damage_stab / self.water_charged.power
        normalized_no_stab = damage_no_stab / self.ice_charged.power
        
        # STAB should result in more damage per power
        self.assertGreater(normalized_stab, normalized_no_stab)
    
    def test_minimum_damage(self):
        """Test minimum damage is always 1."""
        # Create very weak attacker
        weak_attacker = Pokemon(
            species_id="weak",
            species_name="Weak",
            dex=999,
            base_stats=Stats(atk=10, defense=10, hp=10),
            types=["normal", None]
        )
        weak_attacker.ivs = IVs(0, 0, 0)
        weak_attacker.level = 1
        weak_attacker.reset()
        
        # Create very strong defender
        strong_defender = Pokemon(
            species_id="strong",
            species_name="Strong",
            dex=999,
            base_stats=Stats(atk=300, defense=300, hp=300),
            types=["steel", "rock"]
        )
        strong_defender.ivs = IVs(15, 15, 15)
        strong_defender.level = 50
        strong_defender.reset()
        
        # Even with terrible matchup, damage should be at least 1
        damage, _ = DamageCalculator.calculate_fast_move_damage(
            weak_attacker, strong_defender, self.normal_fast
        )
        self.assertGreaterEqual(damage, 1)
    
    def test_stat_buffs_affect_damage(self):
        """Test that stat buffs affect damage calculation."""
        # Base damage
        base_damage, _ = DamageCalculator.calculate_fast_move_damage(
            self.attacker, self.defender, self.water_fast
        )
        
        # Apply attack buff to attacker
        self.attacker.stat_buffs = [1, 0]  # +1 attack stage
        buffed_damage, _ = DamageCalculator.calculate_fast_move_damage(
            self.attacker, self.defender, self.water_fast
        )
        
        # Buffed attack should deal more damage
        self.assertGreater(buffed_damage, base_damage)
        
        # Reset and apply defense buff to defender
        self.attacker.stat_buffs = [0, 0]
        self.defender.stat_buffs = [0, 1]  # +1 defense stage
        defended_damage, _ = DamageCalculator.calculate_fast_move_damage(
            self.attacker, self.defender, self.water_fast
        )
        
        # Buffed defense should reduce damage
        self.assertLess(defended_damage, base_damage)
    
    def test_shadow_bonus(self):
        """Test shadow Pokemon damage bonus."""
        # Normal damage
        normal_damage, _ = DamageCalculator.calculate_fast_move_damage(
            self.attacker, self.defender, self.water_fast
        )
        
        # Shadow attacker
        self.attacker.shadow_type = "shadow"
        shadow_damage, _ = DamageCalculator.calculate_fast_move_damage(
            self.attacker, self.defender, self.water_fast
        )
        
        # Shadow should deal more damage
        self.assertGreater(shadow_damage, normal_damage)
        
        # Reset attacker, make defender shadow
        self.attacker.shadow_type = "normal"
        self.defender.shadow_type = "shadow"
        vs_shadow_damage, _ = DamageCalculator.calculate_fast_move_damage(
            self.attacker, self.defender, self.water_fast
        )
        
        # Shadow defender should take more damage
        self.assertGreater(vs_shadow_damage, normal_damage)
    
    def test_get_duel_rating(self):
        """Test duel rating calculation."""
        # Equal HP remaining
        rating = DamageCalculator.get_duel_rating(
            self.attacker, self.defender,
            remaining_hp1=100, remaining_hp2=100
        )
        self.assertEqual(rating, 500)  # Should be even
        
        # Attacker has more HP
        rating = DamageCalculator.get_duel_rating(
            self.attacker, self.defender,
            remaining_hp1=150, remaining_hp2=50
        )
        self.assertGreater(rating, 500)
        
        # Defender has more HP
        rating = DamageCalculator.get_duel_rating(
            self.attacker, self.defender,
            remaining_hp1=50, remaining_hp2=150
        )
        self.assertLess(rating, 500)
        
        # One Pokemon fainted
        rating = DamageCalculator.get_duel_rating(
            self.attacker, self.defender,
            remaining_hp1=100, remaining_hp2=0
        )
        self.assertGreater(rating, 900)  # Should be close to max
    
    def test_get_type_effectiveness(self):
        """Test type effectiveness calculation helper."""
        # Super effective
        effectiveness = DamageCalculator.get_type_effectiveness(
            "water", ["fire", "flying"]
        )
        self.assertEqual(effectiveness, 1.6)
        
        # Not very effective
        effectiveness = DamageCalculator.get_type_effectiveness(
            "water", ["water", "grass"]
        )
        self.assertLess(effectiveness, 1.0)
        
        # Neutral
        effectiveness = DamageCalculator.get_type_effectiveness(
            "normal", ["fighting", None]
        )
        self.assertEqual(effectiveness, 1.0)
        
        # Double super effective
        effectiveness = DamageCalculator.get_type_effectiveness(
            "rock", ["fire", "flying"]
        )
        self.assertAlmostEqual(effectiveness, 2.56, places=2)
    
    def test_calculate_damage_with_multipliers(self):
        """Test damage calculation with various multipliers."""
        # Test with different multiplier combinations
        base_stats = self.attacker.calculate_stats()
        
        # High attack multiplier
        damage = DamageCalculator.calculate_damage(
            attack=base_stats.atk * 2,
            defense=self.defender.calculate_stats().defense,
            power=10,
            effectiveness=1.0,
            stab=1.0
        )
        self.assertGreater(damage, 0)
        
        # Low defense (should increase damage)
        damage_low_def = DamageCalculator.calculate_damage(
            attack=base_stats.atk,
            defense=self.defender.calculate_stats().defense * 0.5,
            power=10,
            effectiveness=1.0,
            stab=1.0
        )
        self.assertGreater(damage_low_def, damage / 2)
        
        # STAB bonus
        damage_stab = DamageCalculator.calculate_damage(
            attack=base_stats.atk,
            defense=self.defender.calculate_stats().defense,
            power=10,
            effectiveness=1.0,
            stab=1.2
        )
        damage_no_stab = DamageCalculator.calculate_damage(
            attack=base_stats.atk,
            defense=self.defender.calculate_stats().defense,
            power=10,
            effectiveness=1.0,
            stab=1.0
        )
        self.assertGreater(damage_stab, damage_no_stab)
    
    def test_pvp_multiplier(self):
        """Test PvP multiplier is applied correctly."""
        # The PvP multiplier should be consistent
        # In PvP, there's a specific multiplier (usually around 1.3)
        
        attack = 100
        defense = 100
        power = 50
        
        damage = DamageCalculator.calculate_damage(
            attack=attack,
            defense=defense,
            power=power,
            effectiveness=1.0,
            stab=1.0
        )
        
        # Check damage is within expected range for PvP
        # Formula: floor(0.5 * Power * Attack / Defense * Multiplier) + 1
        # With PvP multiplier ~1.3
        expected_min = int(0.5 * power * attack / defense * 1.2) + 1
        expected_max = int(0.5 * power * attack / defense * 1.4) + 1
        
        self.assertGreaterEqual(damage, expected_min)
        self.assertLessEqual(damage, expected_max)
    
    def test_energy_gain_not_affected_by_effectiveness(self):
        """Test that energy gain is not affected by type effectiveness."""
        # Super effective
        _, energy_se = DamageCalculator.calculate_fast_move_damage(
            self.attacker, self.defender, self.water_fast
        )
        
        # Change defender to resist water
        grass_defender = Pokemon(
            species_id="grass",
            species_name="Grass",
            dex=999,
            base_stats=Stats(atk=100, defense=100, hp=100),
            types=["grass", None]
        )
        grass_defender.ivs = IVs(10, 10, 10)
        grass_defender.level = 40
        grass_defender.reset()
        
        # Not very effective
        _, energy_nve = DamageCalculator.calculate_fast_move_damage(
            self.attacker, grass_defender, self.water_fast
        )
        
        # Energy gain should be the same regardless of effectiveness
        self.assertEqual(energy_se, energy_nve)
        self.assertEqual(energy_se, self.water_fast.energy_gain)


if __name__ == "__main__":
    unittest.main()
