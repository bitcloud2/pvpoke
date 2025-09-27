"""Tests for Battle simulation engine."""

import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core import Pokemon, Stats, IVs
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.battle import Battle, BattlePhase, BattleResult


class TestBattle(unittest.TestCase):
    """Test Battle class functionality."""
    
    def setUp(self):
        """Set up test Pokemon and moves for battles."""
        # Create test Pokemon
        self.pokemon1 = Pokemon(
            species_id="azumarill",
            species_name="Azumarill",
            dex=184,
            base_stats=Stats(atk=112.2, defense=152.3, hp=225),
            types=["water", "fairy"]
        )
        
        self.pokemon2 = Pokemon(
            species_id="medicham",
            species_name="Medicham", 
            dex=308,
            base_stats=Stats(atk=121, defense=152, hp=155),
            types=["fighting", "psychic"]
        )
        
        # Set up moves
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
        
        self.ice_beam = ChargedMove(
            move_id="ICE_BEAM",
            name="Ice Beam",
            move_type="ice",
            power=90,
            energy_cost=55
        )
        
        self.power_up_punch = ChargedMove(
            move_id="POWER_UP_PUNCH",
            name="Power-Up Punch",
            move_type="fighting",
            power=20,
            energy_cost=35,
            buffs=[1.25, 1.0],
            buff_target="self",
            buff_chance=1.0
        )
        
        # Assign moves to Pokemon
        self.pokemon1.fast_move = self.bubble
        self.pokemon1.charged_move_1 = self.ice_beam
        
        self.pokemon2.fast_move = self.counter
        self.pokemon2.charged_move_1 = self.power_up_punch
        
        # Set IVs and level for consistent testing
        self.pokemon1.ivs = IVs(0, 15, 15)
        self.pokemon1.level = 40
        self.pokemon1.cp = self.pokemon1.calculate_cp()
        self.pokemon1.reset()
        
        self.pokemon2.ivs = IVs(0, 15, 15)
        self.pokemon2.level = 40
        self.pokemon2.cp = self.pokemon2.calculate_cp()
        self.pokemon2.reset()
        
        # Create battle instance
        self.battle = Battle(self.pokemon1, self.pokemon2)
    
    def test_battle_initialization(self):
        """Test Battle initializes correctly."""
        self.assertEqual(self.battle.pokemon[0], self.pokemon1)
        self.assertEqual(self.battle.pokemon[1], self.pokemon2)
        self.assertEqual(self.battle.cp_limit, 1500)
        self.assertEqual(self.battle.time_limit, 240000)
        self.assertEqual(self.battle.turn_duration, 500)
        self.assertEqual(self.battle.phase, BattlePhase.NEUTRAL)
    
    def test_set_pokemon(self):
        """Test setting Pokemon in battle."""
        new_pokemon = Pokemon(
            species_id="snorlax",
            species_name="Snorlax",
            dex=143,
            base_stats=Stats(atk=190, defense=169, hp=330),
            types=["normal", None]
        )
        
        self.battle.set_pokemon(new_pokemon, 0)
        self.assertEqual(self.battle.pokemon[0], new_pokemon)
        
        # Test invalid index
        with self.assertRaises(ValueError):
            self.battle.set_pokemon(new_pokemon, 2)
    
    def test_battle_reset(self):
        """Test battle reset functionality."""
        # Modify battle state
        self.battle.current_time = 5000
        self.battle.current_turn = 10
        self.battle.cooldowns = [2, 3]
        self.battle.timeline = [{"test": "event"}]
        
        # Reset
        self.battle.reset()
        
        # Check reset state
        self.assertEqual(self.battle.current_time, 0)
        self.assertEqual(self.battle.current_turn, 0)
        self.assertEqual(self.battle.phase, BattlePhase.NEUTRAL)
        self.assertEqual(self.battle.timeline, [])
        self.assertEqual(self.battle.cooldowns, [0, 0])
        self.assertEqual(self.battle.queued_moves, [None, None])
    
    def test_simulate_requires_both_pokemon(self):
        """Test that simulate requires both Pokemon to be set."""
        battle = Battle()
        with self.assertRaises(ValueError):
            battle.simulate()
        
        battle.set_pokemon(self.pokemon1, 0)
        with self.assertRaises(ValueError):
            battle.simulate()
    
    def test_basic_simulation(self):
        """Test basic battle simulation runs without errors."""
        result = self.battle.simulate()
        
        self.assertIsInstance(result, BattleResult)
        self.assertIn(result.winner, [0, 1])
        self.assertGreaterEqual(result.pokemon1_hp, 0)
        self.assertGreaterEqual(result.pokemon2_hp, 0)
        self.assertGreater(result.turns, 0)
        self.assertLessEqual(result.time_remaining, 240)
    
    def test_simulation_with_timeline(self):
        """Test battle simulation with timeline logging."""
        result = self.battle.simulate(log_timeline=True)
        
        self.assertIsInstance(result.timeline, list)
        if len(result.timeline) > 0:
            # Check timeline event structure
            event = result.timeline[0]
            self.assertIn("turn", event)
            self.assertIn("time", event)
            self.assertIn("attacker", event)
            self.assertIn("action", event)
    
    def test_decide_action_fast_move(self):
        """Test action decision for fast moves."""
        # Pokemon with no energy should use fast move
        self.pokemon1.energy = 0
        action = self.battle.decide_action(0)
        
        self.assertEqual(action["type"], "fast")
        self.assertEqual(action["move"], self.bubble)
        self.assertEqual(action["target"], 1)
    
    def test_decide_action_charged_move(self):
        """Test action decision for charged moves."""
        # Pokemon with enough energy should use charged move
        self.pokemon1.energy = 60
        action = self.battle.decide_action(0)
        
        self.assertEqual(action["type"], "charged")
        self.assertEqual(action["move"], self.ice_beam)
        self.assertEqual(action["target"], 1)
    
    def test_execute_fast_move_action(self):
        """Test executing a fast move action."""
        initial_hp = self.pokemon2.current_hp
        initial_energy = self.pokemon1.energy
        
        action = {
            "type": "fast",
            "move": self.bubble,
            "target": 1
        }
        
        self.battle.execute_action(0, action, log_timeline=False)
        
        # Check damage dealt
        self.assertLess(self.pokemon2.current_hp, initial_hp)
        # Check energy gained
        self.assertGreater(self.pokemon1.energy, initial_energy)
        # Check cooldown set
        self.assertEqual(self.battle.cooldowns[0], self.bubble.turns - 1)
    
    def test_execute_charged_move_action(self):
        """Test executing a charged move action."""
        self.pokemon1.energy = 60
        initial_hp = self.pokemon2.current_hp
        
        action = {
            "type": "charged",
            "move": self.ice_beam,
            "target": 1
        }
        
        self.battle.execute_action(0, action, log_timeline=False)
        
        # Check damage dealt
        self.assertLess(self.pokemon2.current_hp, initial_hp)
        # Check energy consumed
        self.assertEqual(self.pokemon1.energy, 60 - self.ice_beam.energy_cost)
    
    def test_shield_usage(self):
        """Test shield mechanics in charged moves."""
        self.pokemon1.energy = 60
        self.pokemon2.shields = 1
        initial_hp = self.pokemon2.current_hp
        
        action = {
            "type": "charged",
            "move": self.ice_beam,
            "target": 1
        }
        
        self.battle.execute_action(0, action, log_timeline=False)
        
        # Check shield was used
        self.assertEqual(self.pokemon2.shields, 0)
        # Check minimal damage (1 HP)
        self.assertEqual(self.pokemon2.current_hp, initial_hp - 1)
    
    def test_buff_application(self):
        """Test buff/debuff application from moves."""
        self.pokemon2.energy = 40
        initial_buffs = self.pokemon2.stat_buffs.copy()
        
        action = {
            "type": "charged",
            "move": self.power_up_punch,
            "target": 0
        }
        
        # Apply buff with 100% chance
        self.battle.execute_action(1, action, log_timeline=False)
        
        # Check attack buff was applied
        self.assertEqual(self.pokemon2.stat_buffs[0], initial_buffs[0] + 1)
    
    def test_get_buff_stages(self):
        """Test buff stage calculation."""
        # Test various multipliers
        self.assertEqual(self.battle.get_buff_stages(2.0), 2)
        self.assertEqual(self.battle.get_buff_stages(1.5), 1)
        self.assertEqual(self.battle.get_buff_stages(1.0), 0)
        self.assertEqual(self.battle.get_buff_stages(0.75), -1)
        self.assertEqual(self.battle.get_buff_stages(0.5), -2)
    
    def test_process_turn(self):
        """Test processing a single turn."""
        # Set up Pokemon states
        self.pokemon1.energy = 10
        self.pokemon2.energy = 10
        self.battle.cooldowns = [0, 0]
        
        initial_hp1 = self.pokemon1.current_hp
        initial_hp2 = self.pokemon2.current_hp
        
        self.battle.process_turn(log_timeline=False)
        
        # At least one Pokemon should have taken damage
        hp_changed = (self.pokemon1.current_hp < initial_hp1 or 
                     self.pokemon2.current_hp < initial_hp2)
        self.assertTrue(hp_changed)
    
    def test_cooldown_reduction(self):
        """Test cooldown reduction during turns."""
        self.battle.cooldowns = [3, 2]
        
        # Mock decide_action to prevent actual actions
        with patch.object(self.battle, 'decide_action', return_value=None):
            self.battle.process_turn(log_timeline=False)
        
        # Cooldowns should be reduced
        self.assertEqual(self.battle.cooldowns[0], 2)
        self.assertEqual(self.battle.cooldowns[1], 1)
    
    def test_battle_ends_on_faint(self):
        """Test battle ends when a Pokemon faints."""
        # Set one Pokemon to low HP
        self.pokemon2.current_hp = 1
        
        # Give attacker enough energy for charged move
        self.pokemon1.energy = 60
        
        result = self.battle.simulate()
        
        # Battle should end with one Pokemon at 0 HP
        self.assertTrue(result.pokemon1_hp == 0 or result.pokemon2_hp == 0)
    
    def test_battle_timeout(self):
        """Test battle ends at time limit."""
        # Make both Pokemon very tanky to ensure timeout
        self.pokemon1.base_stats.defense = 500
        self.pokemon2.base_stats.defense = 500
        self.pokemon1.reset()
        self.pokemon2.reset()
        
        # Use weak moves
        weak_move = FastMove(
            move_id="SPLASH",
            name="Splash",
            move_type="water",
            power=1,
            energy_gain=3,
            turns=2
        )
        self.pokemon1.fast_move = weak_move
        self.pokemon2.fast_move = weak_move
        
        result = self.battle.simulate()
        
        # Battle should reach time limit
        self.assertAlmostEqual(result.time_remaining, 0, delta=10)
    
    def test_battle_rating_calculation(self):
        """Test battle rating is calculated correctly."""
        result = self.battle.simulate()
        
        # Ratings should sum to 1000
        self.assertEqual(result.rating1 + result.rating2, 1000)
        
        # Winner should have higher rating
        if result.winner == 0:
            self.assertGreater(result.rating1, result.rating2)
        else:
            self.assertGreater(result.rating2, result.rating1)
    
    def test_timeline_event_structure(self):
        """Test timeline events have correct structure."""
        result = self.battle.simulate(log_timeline=True)
        
        if len(result.timeline) > 0:
            for event in result.timeline:
                # Check required fields
                self.assertIn("turn", event)
                self.assertIn("time", event)
                self.assertIn("attacker", event)
                self.assertIn("action", event)
                
                # Check attacker index
                self.assertIn(event["attacker"], [0, 1])
                
                # Check action type
                self.assertIn(event["action"], ["fast", "charged"])
                
                # Check action-specific fields
                if event["action"] == "fast":
                    self.assertIn("damage", event)
                    self.assertIn("energy", event)
                elif event["action"] == "charged":
                    self.assertIn("damage", event)
                    self.assertIn("shielded", event)
    
    def test_should_apply_buff_probability(self):
        """Test buff application probability."""
        # Test always applies (100% chance)
        self.assertTrue(self.battle.should_apply_buff(1.0))
        
        # Test never applies (0% chance)
        self.assertFalse(self.battle.should_apply_buff(0.0))
        
        # Test probabilistic (50% chance) - just check it returns bool
        result = self.battle.should_apply_buff(0.5)
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
