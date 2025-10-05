"""
Tests for Aegislash Energy Gain Override (Step 1W).

This module tests the special energy gain override for Aegislash Shield form,
which always gains 6 energy per fast move regardless of the move's base energy gain.

JavaScript Reference:
- Battle.js lines 1278-1280: Shield form fast move energy gain override
- Battle.js lines 1464-1466: Shield form timeline event energy override
"""

import pytest
from pvpoke.core.pokemon import Pokemon, Stats, IVs
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.battle.damage_calculator import DamageCalculator
from pvpoke.battle.battle import Battle


@pytest.fixture
def aegislash_shield():
    """Create an Aegislash in Shield form."""
    aegislash = Pokemon(
        species_id="aegislash_shield",
        species_name="Aegislash (Shield)",
        dex=681,
        base_stats=Stats(atk=118, defense=264, hp=155),
        types=["steel", "ghost"],
        level=40.0,
        ivs=IVs(0, 15, 15)
    )
    
    # Set up moves - Psycho Cut normally has 9 energy gain
    aegislash.fast_move = FastMove(
        move_id="AEGISLASH_CHARGE_PSYCHO_CUT",
        name="Psycho Cut",
        move_type="psychic",
        power=3,
        energy_gain=9,  # Normal energy gain
        turns=1
    )
    
    aegislash.charged_move_1 = ChargedMove(
        move_id="SHADOW_BALL",
        name="Shadow Ball",
        move_type="ghost",
        power=100,
        energy_cost=55
    )
    
    # Set active form ID
    aegislash.active_form_id = "aegislash_shield"
    
    return aegislash


@pytest.fixture
def aegislash_blade():
    """Create an Aegislash in Blade form."""
    aegislash = Pokemon(
        species_id="aegislash",
        species_name="Aegislash",
        dex=681,
        base_stats=Stats(atk=238, defense=128, hp=155),
        types=["steel", "ghost"],
        level=40.0,
        ivs=IVs(0, 15, 15)
    )
    
    # Set up moves - Normal Psycho Cut with 9 energy gain
    aegislash.fast_move = FastMove(
        move_id="PSYCHO_CUT",
        name="Psycho Cut",
        move_type="psychic",
        power=3,
        energy_gain=9,
        turns=1
    )
    
    aegislash.charged_move_1 = ChargedMove(
        move_id="SHADOW_BALL",
        name="Shadow Ball",
        move_type="ghost",
        power=100,
        energy_cost=55
    )
    
    # Set active form ID (or None for normal form)
    aegislash.active_form_id = "aegislash_blade"
    
    return aegislash


@pytest.fixture
def opponent():
    """Create a standard opponent Pokemon."""
    pokemon = Pokemon(
        species_id="registeel",
        species_name="Registeel",
        dex=379,
        base_stats=Stats(atk=143, defense=285, hp=190),
        types=["steel"],
        level=40.0,
        ivs=IVs(0, 15, 15)
    )
    
    pokemon.fast_move = FastMove(
        move_id="LOCK_ON",
        name="Lock On",
        move_type="normal",
        power=1,
        energy_gain=5,
        turns=1
    )
    
    return pokemon


class TestAegislashEnergyGainOverride:
    """Test Aegislash Shield form energy gain override."""
    
    def test_shield_form_energy_gain_override(self, aegislash_shield, opponent):
        """Test that Shield form gets 6 energy per fast move."""
        # Calculate fast move damage and energy
        damage, energy = DamageCalculator.calculate_fast_move_damage(
            aegislash_shield, opponent, aegislash_shield.fast_move
        )
        
        # Energy should be overridden to 6 (not the move's base 9)
        assert energy == 6, f"Expected energy gain of 6, got {energy}"
    
    def test_blade_form_normal_energy_gain(self, aegislash_blade, opponent):
        """Test that Blade form uses normal energy gain."""
        # Calculate fast move damage and energy
        damage, energy = DamageCalculator.calculate_fast_move_damage(
            aegislash_blade, opponent, aegislash_blade.fast_move
        )
        
        # Energy should be the move's base value (9)
        assert energy == 9, f"Expected energy gain of 9, got {energy}"
    
    def test_shield_form_with_different_fast_move(self, aegislash_shield, opponent):
        """Test that Shield form override works with different fast moves."""
        # Change to a different fast move with different energy gain
        aegislash_shield.fast_move = FastMove(
            move_id="AEGISLASH_CHARGE_SMACK_DOWN",
            name="Smack Down",
            move_type="rock",
            power=12,
            energy_gain=8,  # Different base energy gain
            turns=2
        )
        
        # Calculate fast move damage and energy
        damage, energy = DamageCalculator.calculate_fast_move_damage(
            aegislash_shield, opponent, aegislash_shield.fast_move
        )
        
        # Energy should still be overridden to 6
        assert energy == 6, f"Expected energy gain of 6, got {energy}"
    
    def test_shield_form_energy_gain_in_battle(self, aegislash_shield, opponent):
        """Test that Shield form energy gain works correctly in battle simulation."""
        battle = Battle(aegislash_shield, opponent)
        
        # Set initial energy to 0
        aegislash_shield.energy = 0
        
        # Execute a fast move
        action = {
            "type": "fast",
            "move": aegislash_shield.fast_move,
            "target": 1
        }
        battle.execute_action(0, action, log_timeline=False)
        
        # Energy should be 6 (overridden)
        assert aegislash_shield.energy == 6, f"Expected energy of 6, got {aegislash_shield.energy}"
    
    def test_shield_form_energy_accumulation(self, aegislash_shield, opponent):
        """Test that Shield form energy accumulates correctly over multiple fast moves."""
        battle = Battle(aegislash_shield, opponent)
        
        # Set initial energy to 0
        aegislash_shield.energy = 0
        
        # Execute 5 fast moves
        action = {
            "type": "fast",
            "move": aegislash_shield.fast_move,
            "target": 1
        }
        
        for i in range(5):
            battle.execute_action(0, action, log_timeline=False)
        
        # Energy should be 30 (6 * 5)
        assert aegislash_shield.energy == 30, f"Expected energy of 30, got {aegislash_shield.energy}"
    
    def test_shield_form_energy_cap_at_100(self, aegislash_shield, opponent):
        """Test that Shield form energy caps at 100."""
        battle = Battle(aegislash_shield, opponent)
        
        # Set initial energy to 95
        aegislash_shield.energy = 95
        
        # Execute 2 fast moves (would be 95 + 6 + 6 = 107)
        action = {
            "type": "fast",
            "move": aegislash_shield.fast_move,
            "target": 1
        }
        
        battle.execute_action(0, action, log_timeline=False)
        battle.execute_action(0, action, log_timeline=False)
        
        # Energy should be capped at 100
        assert aegislash_shield.energy == 100, f"Expected energy of 100, got {aegislash_shield.energy}"
    
    def test_shield_form_timeline_energy_logging(self, aegislash_shield, opponent):
        """Test that timeline correctly logs energy gain for Shield form."""
        battle = Battle(aegislash_shield, opponent)
        
        # Set initial energy to 0
        aegislash_shield.energy = 0
        
        # Execute a fast move with timeline logging
        action = {
            "type": "fast",
            "move": aegislash_shield.fast_move,
            "target": 1
        }
        battle.execute_action(0, action, log_timeline=True)
        
        # Check timeline event
        assert len(battle.timeline) == 1
        event = battle.timeline[0]
        assert event["action"] == "fast"
        assert event["energy"] == 6, f"Expected timeline energy of 6, got {event['energy']}"
    
    def test_normal_pokemon_energy_gain_unaffected(self, opponent):
        """Test that normal Pokemon energy gain is not affected by the override."""
        # Create a normal Pokemon
        normal_pokemon = Pokemon(
            species_id="medicham",
            species_name="Medicham",
            dex=308,
            base_stats=Stats(atk=121, defense=152, hp=155),
            types=["fighting", "psychic"],
            level=40.0,
            ivs=IVs(0, 15, 15)
        )
        
        normal_pokemon.fast_move = FastMove(
            move_id="PSYCHO_CUT",
            name="Psycho Cut",
            move_type="psychic",
            power=3,
            energy_gain=9,
            turns=1
        )
        
        # Calculate fast move damage and energy
        damage, energy = DamageCalculator.calculate_fast_move_damage(
            normal_pokemon, opponent, normal_pokemon.fast_move
        )
        
        # Energy should be the move's base value (9)
        assert energy == 9, f"Expected energy gain of 9, got {energy}"


class TestAegislashEnergyGainEdgeCases:
    """Test edge cases for Aegislash energy gain override."""
    
    def test_shield_form_without_active_form_id(self, opponent):
        """Test behavior when active_form_id is not set."""
        aegislash = Pokemon(
            species_id="aegislash_shield",
            species_name="Aegislash (Shield)",
            dex=681,
            base_stats=Stats(atk=118, defense=264, hp=155),
            types=["steel", "ghost"],
            level=40.0,
            ivs=IVs(0, 15, 15)
        )
        
        aegislash.fast_move = FastMove(
            move_id="PSYCHO_CUT",
            name="Psycho Cut",
            move_type="psychic",
            power=3,
            energy_gain=9,
            turns=1
        )
        
        # Don't set active_form_id
        
        # Calculate fast move damage and energy
        damage, energy = DamageCalculator.calculate_fast_move_damage(
            aegislash, opponent, aegislash.fast_move
        )
        
        # Energy should be the move's base value (9) since active_form_id is not set
        assert energy == 9, f"Expected energy gain of 9, got {energy}"
    
    def test_shield_form_with_zero_energy_move(self, aegislash_shield, opponent):
        """Test Shield form with a fast move that has 0 energy gain."""
        # Create a hypothetical fast move with 0 energy gain
        aegislash_shield.fast_move = FastMove(
            move_id="SPLASH",
            name="Splash",
            move_type="normal",
            power=0,
            energy_gain=0,
            turns=1
        )
        
        # Calculate fast move damage and energy
        damage, energy = DamageCalculator.calculate_fast_move_damage(
            aegislash_shield, opponent, aegislash_shield.fast_move
        )
        
        # Energy should still be overridden to 6
        assert energy == 6, f"Expected energy gain of 6, got {energy}"
    
    def test_shield_form_reaches_charged_move_threshold(self, aegislash_shield, opponent):
        """Test that Shield form can reach charged move energy threshold with override."""
        battle = Battle(aegislash_shield, opponent)
        
        # Set initial energy to 0
        aegislash_shield.energy = 0
        
        # Shadow Ball costs 55 energy
        # With 6 energy per fast move, need 10 fast moves (60 energy)
        action = {
            "type": "fast",
            "move": aegislash_shield.fast_move,
            "target": 1
        }
        
        for i in range(10):
            battle.execute_action(0, action, log_timeline=False)
        
        # Energy should be 60
        assert aegislash_shield.energy == 60, f"Expected energy of 60, got {aegislash_shield.energy}"
        
        # Should have enough energy for Shadow Ball (55 cost)
        assert aegislash_shield.energy >= aegislash_shield.charged_move_1.energy_cost


class TestAegislashEnergyGainComparison:
    """Compare Shield form vs Blade form energy gain."""
    
    def test_shield_vs_blade_energy_gain_difference(self, aegislash_shield, aegislash_blade, opponent):
        """Test that Shield form gains less energy than Blade form per fast move."""
        # Calculate Shield form energy
        _, shield_energy = DamageCalculator.calculate_fast_move_damage(
            aegislash_shield, opponent, aegislash_shield.fast_move
        )
        
        # Calculate Blade form energy
        _, blade_energy = DamageCalculator.calculate_fast_move_damage(
            aegislash_blade, opponent, aegislash_blade.fast_move
        )
        
        # Shield form should gain 6 energy
        assert shield_energy == 6
        
        # Blade form should gain 9 energy (normal)
        assert blade_energy == 9
        
        # Blade form gains more energy per fast move
        assert blade_energy > shield_energy
    
    def test_shield_form_takes_longer_to_charge(self, aegislash_shield, aegislash_blade):
        """Test that Shield form takes more fast moves to reach charged move threshold."""
        # Shadow Ball costs 55 energy
        charged_move_cost = 55
        
        # Shield form: 6 energy per fast move
        shield_fast_moves_needed = (charged_move_cost + 5) // 6  # Round up
        
        # Blade form: 9 energy per fast move
        blade_fast_moves_needed = (charged_move_cost + 8) // 9  # Round up
        
        # Shield form needs more fast moves
        assert shield_fast_moves_needed > blade_fast_moves_needed
        
        # Verify: Shield needs 10 fast moves (60 energy), Blade needs 7 fast moves (63 energy)
        assert shield_fast_moves_needed == 10
        assert blade_fast_moves_needed == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
