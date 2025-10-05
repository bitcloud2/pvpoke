"""
Tests for Aegislash Form Change Move Replacement (Step 1Z).

This module tests the move replacement logic when Aegislash changes forms,
ensuring that fast moves are properly swapped between AEGISLASH_CHARGE_* variants
and regular moves.

JavaScript Reference (Pokemon.js lines 2375-2383):
case "aegislash_blade":
    self.replaceMove("fast", "AEGISLASH_CHARGE_AIR_SLASH", "AIR_SLASH");
    self.replaceMove("fast", "AEGISLASH_CHARGE_PSYCHO_CUT", "PSYCHO_CUT");
    break;

case "aegislash_shield":
    self.replaceMove("fast", "AIR_SLASH", "AEGISLASH_CHARGE_AIR_SLASH");
    self.replaceMove("fast", "PSYCHO_CUT", "AEGISLASH_CHARGE_PSYCHO_CUT");
    break;
"""

import pytest
from pvpoke.core.pokemon import Pokemon, Stats, IVs
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.core.gamemaster import GameMaster


@pytest.fixture
def gamemaster():
    """Load GameMaster for move lookups."""
    return GameMaster()


@pytest.fixture
def aegislash_shield_psycho_cut(gamemaster):
    """Create an Aegislash Shield form with AEGISLASH_CHARGE_PSYCHO_CUT."""
    aegislash = Pokemon(
        species_id="aegislash_shield",
        species_name="Aegislash (Shield)",
        dex=681,
        base_stats=Stats(atk=118, defense=264, hp=155),
        types=["steel", "ghost"],
        level=40.0,
        ivs=IVs(0, 15, 15)
    )
    
    # Set up with AEGISLASH_CHARGE_PSYCHO_CUT
    aegislash.fast_move = gamemaster.get_fast_move("AEGISLASH_CHARGE_PSYCHO_CUT")
    aegislash.charged_move_1 = gamemaster.get_charged_move("SHADOW_BALL")
    aegislash.charged_move_2 = gamemaster.get_charged_move("GYRO_BALL")
    
    aegislash.active_form_id = "aegislash_shield"
    aegislash.energy = 0
    aegislash.current_hp = 100
    
    return aegislash


@pytest.fixture
def aegislash_shield_air_slash(gamemaster):
    """Create an Aegislash Shield form with AEGISLASH_CHARGE_AIR_SLASH."""
    aegislash = Pokemon(
        species_id="aegislash_shield",
        species_name="Aegislash (Shield)",
        dex=681,
        base_stats=Stats(atk=118, defense=264, hp=155),
        types=["steel", "ghost"],
        level=40.0,
        ivs=IVs(0, 15, 15)
    )
    
    # Set up with AEGISLASH_CHARGE_AIR_SLASH
    aegislash.fast_move = gamemaster.get_fast_move("AEGISLASH_CHARGE_AIR_SLASH")
    aegislash.charged_move_1 = gamemaster.get_charged_move("SHADOW_BALL")
    aegislash.charged_move_2 = gamemaster.get_charged_move("GYRO_BALL")
    
    aegislash.active_form_id = "aegislash_shield"
    aegislash.energy = 0
    aegislash.current_hp = 100
    
    return aegislash


@pytest.fixture
def aegislash_blade_psycho_cut(gamemaster):
    """Create an Aegislash Blade form with PSYCHO_CUT."""
    aegislash = Pokemon(
        species_id="aegislash_blade",
        species_name="Aegislash (Blade)",
        dex=681,
        base_stats=Stats(atk=237, defense=158, hp=155),
        types=["steel", "ghost"],
        level=20.0,
        ivs=IVs(0, 15, 15)
    )
    
    # Set up with regular PSYCHO_CUT
    aegislash.fast_move = gamemaster.get_fast_move("PSYCHO_CUT")
    aegislash.charged_move_1 = gamemaster.get_charged_move("SHADOW_BALL")
    aegislash.charged_move_2 = gamemaster.get_charged_move("GYRO_BALL")
    
    aegislash.active_form_id = "aegislash_blade"
    aegislash.energy = 0
    aegislash.current_hp = 100
    
    return aegislash


@pytest.fixture
def aegislash_blade_air_slash(gamemaster):
    """Create an Aegislash Blade form with AIR_SLASH."""
    aegislash = Pokemon(
        species_id="aegislash_blade",
        species_name="Aegislash (Blade)",
        dex=681,
        base_stats=Stats(atk=237, defense=158, hp=155),
        types=["steel", "ghost"],
        level=20.0,
        ivs=IVs(0, 15, 15)
    )
    
    # Set up with regular AIR_SLASH
    aegislash.fast_move = gamemaster.get_fast_move("AIR_SLASH")
    aegislash.charged_move_1 = gamemaster.get_charged_move("SHADOW_BALL")
    aegislash.charged_move_2 = gamemaster.get_charged_move("GYRO_BALL")
    
    aegislash.active_form_id = "aegislash_blade"
    aegislash.energy = 0
    aegislash.current_hp = 100
    
    return aegislash


class TestReplaceMove:
    """Test the replace_move method."""
    
    def test_replace_fast_move_psycho_cut_to_charge(self, aegislash_blade_psycho_cut, gamemaster):
        """Test replacing PSYCHO_CUT with AEGISLASH_CHARGE_PSYCHO_CUT."""
        # Verify initial state
        assert aegislash_blade_psycho_cut.fast_move.move_id == "PSYCHO_CUT"
        
        # Replace the move
        aegislash_blade_psycho_cut.replace_move("fast", "PSYCHO_CUT", "AEGISLASH_CHARGE_PSYCHO_CUT")
        
        # Verify move was replaced
        assert aegislash_blade_psycho_cut.fast_move.move_id == "AEGISLASH_CHARGE_PSYCHO_CUT"
        assert aegislash_blade_psycho_cut.fast_move.name == "Psycho Cut"
    
    def test_replace_fast_move_air_slash_to_charge(self, aegislash_blade_air_slash, gamemaster):
        """Test replacing AIR_SLASH with AEGISLASH_CHARGE_AIR_SLASH."""
        # Verify initial state
        assert aegislash_blade_air_slash.fast_move.move_id == "AIR_SLASH"
        
        # Replace the move
        aegislash_blade_air_slash.replace_move("fast", "AIR_SLASH", "AEGISLASH_CHARGE_AIR_SLASH")
        
        # Verify move was replaced
        assert aegislash_blade_air_slash.fast_move.move_id == "AEGISLASH_CHARGE_AIR_SLASH"
        assert aegislash_blade_air_slash.fast_move.name == "Air Slash"
    
    def test_replace_fast_move_charge_to_psycho_cut(self, aegislash_shield_psycho_cut, gamemaster):
        """Test replacing AEGISLASH_CHARGE_PSYCHO_CUT with PSYCHO_CUT."""
        # Verify initial state
        assert aegislash_shield_psycho_cut.fast_move.move_id == "AEGISLASH_CHARGE_PSYCHO_CUT"
        
        # Replace the move
        aegislash_shield_psycho_cut.replace_move("fast", "AEGISLASH_CHARGE_PSYCHO_CUT", "PSYCHO_CUT")
        
        # Verify move was replaced
        assert aegislash_shield_psycho_cut.fast_move.move_id == "PSYCHO_CUT"
        assert aegislash_shield_psycho_cut.fast_move.name == "Psycho Cut"
    
    def test_replace_fast_move_charge_to_air_slash(self, aegislash_shield_air_slash, gamemaster):
        """Test replacing AEGISLASH_CHARGE_AIR_SLASH with AIR_SLASH."""
        # Verify initial state
        assert aegislash_shield_air_slash.fast_move.move_id == "AEGISLASH_CHARGE_AIR_SLASH"
        
        # Replace the move
        aegislash_shield_air_slash.replace_move("fast", "AEGISLASH_CHARGE_AIR_SLASH", "AIR_SLASH")
        
        # Verify move was replaced
        assert aegislash_shield_air_slash.fast_move.move_id == "AIR_SLASH"
        assert aegislash_shield_air_slash.fast_move.name == "Air Slash"
    
    def test_replace_move_no_match(self, aegislash_shield_psycho_cut, gamemaster):
        """Test that replace_move does nothing if move doesn't match."""
        # Try to replace a move that doesn't exist
        original_move_id = aegislash_shield_psycho_cut.fast_move.move_id
        aegislash_shield_psycho_cut.replace_move("fast", "COUNTER", "PSYCHO_CUT")
        
        # Verify move was NOT replaced
        assert aegislash_shield_psycho_cut.fast_move.move_id == original_move_id
    
    def test_replace_charged_move_first_slot(self, aegislash_shield_psycho_cut, gamemaster):
        """Test replacing a charged move in the first slot."""
        # Verify initial state
        assert aegislash_shield_psycho_cut.charged_move_1.move_id == "SHADOW_BALL"
        
        # Replace the move
        aegislash_shield_psycho_cut.replace_move("charged", "SHADOW_BALL", "FLASH_CANNON")
        
        # Verify move was replaced
        assert aegislash_shield_psycho_cut.charged_move_1.move_id == "FLASH_CANNON"
    
    def test_replace_charged_move_second_slot(self, aegislash_shield_psycho_cut, gamemaster):
        """Test replacing a charged move in the second slot."""
        # Verify initial state
        assert aegislash_shield_psycho_cut.charged_move_2.move_id == "GYRO_BALL"
        
        # Replace the move
        aegislash_shield_psycho_cut.replace_move("charged", "GYRO_BALL", "FLASH_CANNON")
        
        # Verify move was replaced
        assert aegislash_shield_psycho_cut.charged_move_2.move_id == "FLASH_CANNON"


class TestChangeForm:
    """Test the change_form method."""
    
    def test_change_form_shield_to_blade_psycho_cut(self, aegislash_shield_psycho_cut):
        """Test changing from Shield to Blade form with PSYCHO_CUT."""
        # Verify initial state
        assert aegislash_shield_psycho_cut.active_form_id == "aegislash_shield"
        assert aegislash_shield_psycho_cut.fast_move.move_id == "AEGISLASH_CHARGE_PSYCHO_CUT"
        
        # Change to Blade form
        aegislash_shield_psycho_cut.change_form("aegislash_blade", battle_cp=1500)
        
        # Verify form changed
        assert aegislash_shield_psycho_cut.active_form_id == "aegislash_blade"
        
        # Verify move was replaced
        assert aegislash_shield_psycho_cut.fast_move.move_id == "PSYCHO_CUT"
        assert aegislash_shield_psycho_cut.fast_move.name == "Psycho Cut"
    
    def test_change_form_shield_to_blade_air_slash(self, aegislash_shield_air_slash):
        """Test changing from Shield to Blade form with AIR_SLASH."""
        # Verify initial state
        assert aegislash_shield_air_slash.active_form_id == "aegislash_shield"
        assert aegislash_shield_air_slash.fast_move.move_id == "AEGISLASH_CHARGE_AIR_SLASH"
        
        # Change to Blade form
        aegislash_shield_air_slash.change_form("aegislash_blade", battle_cp=1500)
        
        # Verify form changed
        assert aegislash_shield_air_slash.active_form_id == "aegislash_blade"
        
        # Verify move was replaced
        assert aegislash_shield_air_slash.fast_move.move_id == "AIR_SLASH"
        assert aegislash_shield_air_slash.fast_move.name == "Air Slash"
    
    def test_change_form_blade_to_shield_psycho_cut(self, aegislash_blade_psycho_cut):
        """Test changing from Blade to Shield form with PSYCHO_CUT."""
        # Verify initial state
        assert aegislash_blade_psycho_cut.active_form_id == "aegislash_blade"
        assert aegislash_blade_psycho_cut.fast_move.move_id == "PSYCHO_CUT"
        
        # Change to Shield form
        aegislash_blade_psycho_cut.change_form("aegislash_shield", battle_cp=1500)
        
        # Verify form changed
        assert aegislash_blade_psycho_cut.active_form_id == "aegislash_shield"
        
        # Verify move was replaced
        assert aegislash_blade_psycho_cut.fast_move.move_id == "AEGISLASH_CHARGE_PSYCHO_CUT"
        assert aegislash_blade_psycho_cut.fast_move.name == "Psycho Cut"
    
    def test_change_form_blade_to_shield_air_slash(self, aegislash_blade_air_slash):
        """Test changing from Blade to Shield form with AIR_SLASH."""
        # Verify initial state
        assert aegislash_blade_air_slash.active_form_id == "aegislash_blade"
        assert aegislash_blade_air_slash.fast_move.move_id == "AIR_SLASH"
        
        # Change to Shield form
        aegislash_blade_air_slash.change_form("aegislash_shield", battle_cp=1500)
        
        # Verify form changed
        assert aegislash_blade_air_slash.active_form_id == "aegislash_shield"
        
        # Verify move was replaced
        assert aegislash_blade_air_slash.fast_move.move_id == "AEGISLASH_CHARGE_AIR_SLASH"
        assert aegislash_blade_air_slash.fast_move.name == "Air Slash"
    
    def test_change_form_charged_moves_preserved(self, aegislash_shield_psycho_cut):
        """Test that charged moves are preserved during form change."""
        # Store original charged moves
        original_move_1 = aegislash_shield_psycho_cut.charged_move_1.move_id
        original_move_2 = aegislash_shield_psycho_cut.charged_move_2.move_id
        
        # Change to Blade form
        aegislash_shield_psycho_cut.change_form("aegislash_blade", battle_cp=1500)
        
        # Verify charged moves are unchanged
        assert aegislash_shield_psycho_cut.charged_move_1.move_id == original_move_1
        assert aegislash_shield_psycho_cut.charged_move_2.move_id == original_move_2
    
    def test_change_form_stats_updated(self, aegislash_shield_psycho_cut):
        """Test that stats are updated during form change."""
        # Store original stats
        original_atk = aegislash_shield_psycho_cut.base_stats.atk
        original_def = aegislash_shield_psycho_cut.base_stats.defense
        
        # Change to Blade form
        aegislash_shield_psycho_cut.change_form("aegislash_blade", battle_cp=1500)
        
        # Verify stats changed (Blade has higher attack, lower defense)
        # Note: Stats will be different due to form-specific base stats
        assert aegislash_shield_psycho_cut.base_stats.atk != original_atk
        assert aegislash_shield_psycho_cut.base_stats.defense != original_def
    
    def test_change_form_shield_reinitializes_moves(self, aegislash_blade_psycho_cut):
        """Test that changing to Shield form reinitializes moves with self-debuffing."""
        # Change to Shield form
        aegislash_blade_psycho_cut.change_form("aegislash_shield", battle_cp=1500)
        
        # Verify charged moves are marked as self-debuffing
        assert aegislash_blade_psycho_cut.charged_move_1.buffs == [0.0, 0.0]
        assert aegislash_blade_psycho_cut.charged_move_1.buff_target == "self"
        
        assert aegislash_blade_psycho_cut.charged_move_2.buffs == [0.0, 0.0]
        assert aegislash_blade_psycho_cut.charged_move_2.buff_target == "self"
    
    def test_change_form_multiple_times(self, aegislash_shield_psycho_cut):
        """Test changing forms multiple times."""
        # Verify initial state
        assert aegislash_shield_psycho_cut.active_form_id == "aegislash_shield"
        assert aegislash_shield_psycho_cut.fast_move.move_id == "AEGISLASH_CHARGE_PSYCHO_CUT"
        
        # Change to Blade
        aegislash_shield_psycho_cut.change_form("aegislash_blade", battle_cp=1500)
        assert aegislash_shield_psycho_cut.active_form_id == "aegislash_blade"
        assert aegislash_shield_psycho_cut.fast_move.move_id == "PSYCHO_CUT"
        
        # Change back to Shield
        aegislash_shield_psycho_cut.change_form("aegislash_shield", battle_cp=1500)
        assert aegislash_shield_psycho_cut.active_form_id == "aegislash_shield"
        assert aegislash_shield_psycho_cut.fast_move.move_id == "AEGISLASH_CHARGE_PSYCHO_CUT"
        
        # Change to Blade again
        aegislash_shield_psycho_cut.change_form("aegislash_blade", battle_cp=1500)
        assert aegislash_shield_psycho_cut.active_form_id == "aegislash_blade"
        assert aegislash_shield_psycho_cut.fast_move.move_id == "PSYCHO_CUT"


class TestFormChangeIntegration:
    """Test form change integration with battle scenarios."""
    
    def test_form_change_preserves_energy(self, aegislash_shield_psycho_cut):
        """Test that energy is preserved during form change."""
        # Set energy
        aegislash_shield_psycho_cut.energy = 75
        
        # Change form
        aegislash_shield_psycho_cut.change_form("aegislash_blade", battle_cp=1500)
        
        # Verify energy preserved
        assert aegislash_shield_psycho_cut.energy == 75
    
    def test_form_change_preserves_hp(self, aegislash_shield_psycho_cut):
        """Test that HP is preserved during form change."""
        # Set HP
        aegislash_shield_psycho_cut.current_hp = 50
        
        # Change form
        aegislash_shield_psycho_cut.change_form("aegislash_blade", battle_cp=1500)
        
        # Verify HP preserved
        assert aegislash_shield_psycho_cut.current_hp == 50
    
    def test_form_change_preserves_shields(self, aegislash_shield_psycho_cut):
        """Test that shields are preserved during form change."""
        # Set shields
        aegislash_shield_psycho_cut.shields = 1
        
        # Change form
        aegislash_shield_psycho_cut.change_form("aegislash_blade", battle_cp=1500)
        
        # Verify shields preserved
        assert aegislash_shield_psycho_cut.shields == 1
    
    def test_form_change_different_cp_limits(self, aegislash_shield_psycho_cut):
        """Test form change with different CP limits."""
        # Test Great League (1500)
        aegislash_shield_psycho_cut.change_form("aegislash_blade", battle_cp=1500)
        assert aegislash_shield_psycho_cut.active_form_id == "aegislash_blade"
        
        # Reset to Shield
        aegislash_shield_psycho_cut.change_form("aegislash_shield", battle_cp=1500)
        
        # Test Ultra League (2500)
        aegislash_shield_psycho_cut.change_form("aegislash_blade", battle_cp=2500)
        assert aegislash_shield_psycho_cut.active_form_id == "aegislash_blade"
