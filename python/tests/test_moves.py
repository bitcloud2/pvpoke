"""Tests for move classes and type effectiveness."""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core.moves import (
    Move, FastMove, ChargedMove, MoveType, TypeEffectiveness
)


class TestFastMove(unittest.TestCase):
    """Test FastMove class functionality."""
    
    def setUp(self):
        """Set up test fast moves."""
        self.bubble = FastMove(
            move_id="BUBBLE",
            name="Bubble",
            move_type="water",
            power=7,
            energy_gain=11,
            turns=3
        )
        
        self.counter = FastMove(
            move_id="COUNTER",
            name="Counter",
            move_type="fighting",
            power=8,
            energy_gain=7,
            turns=2
        )
    
    def test_fast_move_creation(self):
        """Test fast move initialization."""
        self.assertEqual(self.bubble.move_id, "BUBBLE")
        self.assertEqual(self.bubble.name, "Bubble")
        self.assertEqual(self.bubble.move_type, "water")
        self.assertEqual(self.bubble.power, 7)
        self.assertEqual(self.bubble.energy_gain, 11)
        self.assertEqual(self.bubble.turns, 3)
    
    def test_cooldown_calculation(self):
        """Test cooldown is calculated correctly."""
        self.assertEqual(self.bubble.cooldown, 1500)  # 3 turns * 500ms
        self.assertEqual(self.counter.cooldown, 1000)  # 2 turns * 500ms
    
    def test_dps_calculation(self):
        """Test damage per second calculation."""
        # Bubble: 7 damage / 1.5 seconds = 4.67 DPS
        self.assertAlmostEqual(self.bubble.dps, 4.67, places=2)
        # Counter: 8 damage / 1.0 seconds = 8.0 DPS
        self.assertAlmostEqual(self.counter.dps, 8.0, places=2)
    
    def test_eps_calculation(self):
        """Test energy per second calculation."""
        # Bubble: 11 energy / 1.5 seconds = 7.33 EPS
        self.assertAlmostEqual(self.bubble.eps, 7.33, places=2)
        # Counter: 7 energy / 1.0 seconds = 7.0 EPS
        self.assertAlmostEqual(self.counter.eps, 7.0, places=2)
    
    def test_zero_cooldown_edge_case(self):
        """Test edge case with zero cooldown."""
        move = FastMove(
            move_id="TEST",
            name="Test",
            move_type="normal",
            power=10,
            energy_gain=5,
            turns=0
        )
        self.assertEqual(move.cooldown, 0)
        self.assertEqual(move.dps, 0)
        self.assertEqual(move.eps, 0)


class TestChargedMove(unittest.TestCase):
    """Test ChargedMove class functionality."""
    
    def setUp(self):
        """Set up test charged moves."""
        self.ice_beam = ChargedMove(
            move_id="ICE_BEAM",
            name="Ice Beam",
            move_type="ice",
            power=90,
            energy_cost=55
        )
        
        self.wild_charge = ChargedMove(
            move_id="WILD_CHARGE",
            name="Wild Charge",
            move_type="electric",
            power=100,
            energy_cost=45,
            buffs=[1.0, 0.75],  # -2 defense to self
            buff_target="self",
            buff_chance=1.0
        )
        
        self.icy_wind = ChargedMove(
            move_id="ICY_WIND",
            name="Icy Wind",
            move_type="ice",
            power=60,
            energy_cost=45,
            buffs=[0.75, 1.0],  # -1 attack to opponent
            buff_target="opponent",
            buff_chance=1.0
        )
    
    def test_charged_move_creation(self):
        """Test charged move initialization."""
        self.assertEqual(self.ice_beam.move_id, "ICE_BEAM")
        self.assertEqual(self.ice_beam.name, "Ice Beam")
        self.assertEqual(self.ice_beam.move_type, "ice")
        self.assertEqual(self.ice_beam.power, 90)
        self.assertEqual(self.ice_beam.energy_cost, 55)
        self.assertEqual(self.ice_beam.buffs, [1.0, 1.0])
    
    def test_dpe_calculation(self):
        """Test damage per energy calculation."""
        # Ice Beam: 90 damage / 55 energy = 1.636 DPE
        self.assertAlmostEqual(self.ice_beam.dpe, 1.636, places=3)
        # Wild Charge: 100 damage / 45 energy = 2.222 DPE
        self.assertAlmostEqual(self.wild_charge.dpe, 2.222, places=3)
    
    def test_self_debuffing_detection(self):
        """Test detection of self-debuffing moves."""
        self.assertFalse(self.ice_beam.is_self_debuffing)
        self.assertTrue(self.wild_charge.is_self_debuffing)
        self.assertFalse(self.icy_wind.is_self_debuffing)
    
    def test_opponent_debuffing_detection(self):
        """Test detection of opponent-debuffing moves."""
        self.assertFalse(self.ice_beam.is_opponent_debuffing)
        self.assertFalse(self.wild_charge.is_opponent_debuffing)
        self.assertTrue(self.icy_wind.is_opponent_debuffing)
    
    def test_buffing_detection(self):
        """Test detection of buffing moves."""
        self.assertFalse(self.ice_beam.is_buffing)
        self.assertFalse(self.wild_charge.is_buffing)  # Debuff, not buff
        self.assertFalse(self.icy_wind.is_buffing)  # Opponent debuff
        
        # Create a buffing move
        power_up_punch = ChargedMove(
            move_id="POWER_UP_PUNCH",
            name="Power-Up Punch",
            move_type="fighting",
            power=20,
            energy_cost=35,
            buffs=[1.25, 1.0],  # +1 attack to self
            buff_target="self",
            buff_chance=1.0
        )
        self.assertTrue(power_up_punch.is_buffing)
    
    def test_zero_energy_edge_case(self):
        """Test edge case with zero energy cost."""
        move = ChargedMove(
            move_id="TEST",
            name="Test",
            move_type="normal",
            power=100,
            energy_cost=0
        )
        self.assertEqual(move.dpe, 0)


class TestTypeEffectiveness(unittest.TestCase):
    """Test type effectiveness calculations."""
    
    def test_super_effective(self):
        """Test super effective matchups."""
        # Water vs Fire
        effectiveness = TypeEffectiveness.get_effectiveness("water", ["fire"])
        self.assertEqual(effectiveness, 1.6)
        
        # Fighting vs Normal
        effectiveness = TypeEffectiveness.get_effectiveness("fighting", ["normal"])
        self.assertEqual(effectiveness, 1.6)
        
        # Electric vs Water/Flying (double super effective)
        effectiveness = TypeEffectiveness.get_effectiveness("electric", ["water", "flying"])
        self.assertAlmostEqual(effectiveness, 2.56, places=2)  # 1.6 * 1.6
    
    def test_not_very_effective(self):
        """Test not very effective matchups."""
        # Water vs Grass
        effectiveness = TypeEffectiveness.get_effectiveness("water", ["grass"])
        self.assertEqual(effectiveness, 0.625)
        
        # Fire vs Water
        effectiveness = TypeEffectiveness.get_effectiveness("fire", ["water"])
        self.assertEqual(effectiveness, 0.625)
    
    def test_double_resistance(self):
        """Test double resistance matchups."""
        # Fighting vs Ghost
        effectiveness = TypeEffectiveness.get_effectiveness("fighting", ["ghost"])
        self.assertEqual(effectiveness, 0.390625)
        
        # Normal vs Ghost
        effectiveness = TypeEffectiveness.get_effectiveness("normal", ["ghost"])
        self.assertEqual(effectiveness, 0.390625)
        
        # Poison vs Steel
        effectiveness = TypeEffectiveness.get_effectiveness("poison", ["steel"])
        self.assertEqual(effectiveness, 0.390625)
    
    def test_dual_type_effectiveness(self):
        """Test effectiveness against dual-type Pokemon."""
        # Water vs Rock/Ground (double weak)
        effectiveness = TypeEffectiveness.get_effectiveness("water", ["rock", "ground"])
        self.assertAlmostEqual(effectiveness, 2.56, places=2)  # 1.6 * 1.6
        
        # Grass vs Water/Ground (one weak, one resist)
        effectiveness = TypeEffectiveness.get_effectiveness("grass", ["water", "flying"])
        self.assertEqual(effectiveness, 1.0)  # 1.6 * 0.625
        
        # Fighting vs Poison/Flying (double resist)
        effectiveness = TypeEffectiveness.get_effectiveness("fighting", ["poison", "flying"])
        self.assertEqual(effectiveness, 0.390625)  # 0.625 * 0.625
    
    def test_neutral_effectiveness(self):
        """Test neutral effectiveness."""
        # Normal vs Fighting
        effectiveness = TypeEffectiveness.get_effectiveness("normal", ["fighting"])
        self.assertEqual(effectiveness, 1.0)
        
        # Water vs Normal
        effectiveness = TypeEffectiveness.get_effectiveness("water", ["normal"])
        self.assertEqual(effectiveness, 1.0)
    
    def test_none_type_handling(self):
        """Test handling of None/empty types."""
        # Single type with None second type
        effectiveness = TypeEffectiveness.get_effectiveness("water", ["fire", None])
        self.assertEqual(effectiveness, 1.6)
        
        # Empty type should be treated as neutral
        effectiveness = TypeEffectiveness.get_effectiveness("water", [""])
        self.assertEqual(effectiveness, 1.0)
    
    def test_get_all_effectiveness(self):
        """Test getting effectiveness of all types against a defender."""
        # Test against Water/Flying (Gyarados-like)
        all_effectiveness = TypeEffectiveness.get_all_effectiveness(["water", "flying"])
        
        # Electric should be double super effective
        self.assertAlmostEqual(all_effectiveness["electric"], 2.56, places=2)
        
        # Rock should be super effective
        self.assertEqual(all_effectiveness["rock"], 1.6)
        
        # Fighting should be resisted
        self.assertEqual(all_effectiveness["fighting"], 0.625)
        
        # Ground should be immune (0.390625 in GO)
        self.assertEqual(all_effectiveness["ground"], 0.390625)
        
        # Water should be resisted
        self.assertEqual(all_effectiveness["water"], 0.625)
    
    def test_all_types_present(self):
        """Test that all types are present in the type chart."""
        expected_types = [
            "normal", "fighting", "flying", "poison", "ground",
            "rock", "bug", "ghost", "steel", "fire", "water",
            "grass", "electric", "psychic", "ice", "dragon",
            "dark", "fairy"
        ]
        
        for attack_type in expected_types:
            # Should not raise KeyError
            effectiveness = TypeEffectiveness.get_effectiveness(attack_type, ["normal"])
            self.assertIsInstance(effectiveness, float)
            self.assertGreaterEqual(effectiveness, 0.390625)
            self.assertLessEqual(effectiveness, 1.6)


if __name__ == "__main__":
    unittest.main()
