"""
Tests for Aegislash Move Initialization Logic (Step 1Y).

This module tests the special move initialization logic for Aegislash Shield form,
which marks all charged moves as self-debuffing with [0,0] buffs to ensure proper
AI decision making.

JavaScript Reference: Pokemon.js lines 745-751
"""

import pytest
from pvpoke.core.pokemon import Pokemon, Stats, IVs
from pvpoke.core.moves import ChargedMove


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
    
    # Set form-specific properties
    aegislash.active_form_id = "aegislash_shield"
    
    return aegislash


@pytest.fixture
def aegislash_blade():
    """Create an Aegislash in Blade form."""
    aegislash = Pokemon(
        species_id="aegislash_blade",
        species_name="Aegislash (Blade)",
        dex=681,
        base_stats=Stats(atk=266, defense=114, hp=155),
        types=["steel", "ghost"],
        level=40.0,
        ivs=IVs(0, 15, 15)
    )
    
    # Set form-specific properties
    aegislash.active_form_id = "aegislash_blade"
    
    return aegislash


@pytest.fixture
def regular_pokemon():
    """Create a regular Pokemon (not Aegislash)."""
    pokemon = Pokemon(
        species_id="azumarill",
        species_name="Azumarill",
        dex=184,
        base_stats=Stats(atk=112, defense=152, hp=225),
        types=["water", "fairy"],
        level=40.0,
        ivs=IVs(0, 15, 15)
    )
    
    return pokemon


class TestAegislashMoveInitialization:
    """Test Aegislash Shield form move initialization."""
    
    def test_shield_form_single_charged_move_marked_as_self_debuffing(self, aegislash_shield):
        """Test that a single charged move is marked as self-debuffing."""
        # Set up a charged move with normal buffs
        aegislash_shield.charged_move_1 = ChargedMove(
            move_id="SHADOW_BALL",
            name="Shadow Ball",
            move_type="ghost",
            power=100,
            energy_cost=55,
            buffs=[1.0, 1.0],  # No buffs initially
            buff_target="opponent"
        )
        
        # Initialize Aegislash moves
        aegislash_shield.initialize_aegislash_moves()
        
        # Verify the move is marked as self-debuffing
        assert aegislash_shield.charged_move_1.buffs == [0.0, 0.0]
        assert aegislash_shield.charged_move_1.buff_target == "self"
        assert aegislash_shield.charged_move_1.self_debuffing is True
    
    def test_shield_form_two_charged_moves_both_marked_as_self_debuffing(self, aegislash_shield):
        """Test that both charged moves are marked as self-debuffing."""
        # Set up two charged moves
        aegislash_shield.charged_move_1 = ChargedMove(
            move_id="SHADOW_BALL",
            name="Shadow Ball",
            move_type="ghost",
            power=100,
            energy_cost=55,
            buffs=[1.0, 1.0],
            buff_target="opponent"
        )
        
        aegislash_shield.charged_move_2 = ChargedMove(
            move_id="GYRO_BALL",
            name="Gyro Ball",
            move_type="steel",
            power=80,
            energy_cost=60,
            buffs=[1.0, 1.0],
            buff_target="opponent"
        )
        
        # Initialize Aegislash moves
        aegislash_shield.initialize_aegislash_moves()
        
        # Verify both moves are marked as self-debuffing
        assert aegislash_shield.charged_move_1.buffs == [0.0, 0.0]
        assert aegislash_shield.charged_move_1.buff_target == "self"
        assert aegislash_shield.charged_move_1.self_debuffing is True
        
        assert aegislash_shield.charged_move_2.buffs == [0.0, 0.0]
        assert aegislash_shield.charged_move_2.buff_target == "self"
        assert aegislash_shield.charged_move_2.self_debuffing is True
    
    def test_shield_form_overwrites_existing_buffs(self, aegislash_shield):
        """Test that initialization overwrites existing buff values."""
        # Set up a move with actual buffs
        aegislash_shield.charged_move_1 = ChargedMove(
            move_id="FLASH_CANNON",
            name="Flash Cannon",
            move_type="steel",
            power=110,
            energy_cost=70,
            buffs=[1.0, 0.8571],  # Defense debuff
            buff_target="opponent",
            buff_chance=0.1
        )
        
        # Initialize Aegislash moves
        aegislash_shield.initialize_aegislash_moves()
        
        # Verify the buffs are overwritten
        assert aegislash_shield.charged_move_1.buffs == [0.0, 0.0]
        assert aegislash_shield.charged_move_1.buff_target == "self"
        assert aegislash_shield.charged_move_1.self_debuffing is True
    
    def test_shield_form_with_no_charged_moves(self, aegislash_shield):
        """Test that initialization doesn't crash with no charged moves."""
        # No charged moves set
        aegislash_shield.charged_move_1 = None
        aegislash_shield.charged_move_2 = None
        
        # Should not raise an error
        aegislash_shield.initialize_aegislash_moves()
    
    def test_shield_form_with_only_one_charged_move_slot(self, aegislash_shield):
        """Test initialization with only one charged move slot filled."""
        aegislash_shield.charged_move_1 = ChargedMove(
            move_id="SHADOW_BALL",
            name="Shadow Ball",
            move_type="ghost",
            power=100,
            energy_cost=55,
            buffs=[1.0, 1.0],
            buff_target="opponent"
        )
        aegislash_shield.charged_move_2 = None
        
        # Initialize Aegislash moves
        aegislash_shield.initialize_aegislash_moves()
        
        # Verify only the first move is modified
        assert aegislash_shield.charged_move_1.buffs == [0.0, 0.0]
        assert aegislash_shield.charged_move_1.buff_target == "self"
        assert aegislash_shield.charged_move_1.self_debuffing is True
    
    def test_blade_form_does_not_modify_moves(self, aegislash_blade):
        """Test that Blade form does not modify charged moves."""
        # Set up charged moves
        aegislash_blade.charged_move_1 = ChargedMove(
            move_id="SHADOW_BALL",
            name="Shadow Ball",
            move_type="ghost",
            power=100,
            energy_cost=55,
            buffs=[1.0, 1.0],
            buff_target="opponent"
        )
        
        original_buffs = aegislash_blade.charged_move_1.buffs.copy()
        original_target = aegislash_blade.charged_move_1.buff_target
        
        # Initialize moves (should do nothing for Blade form)
        aegislash_blade.initialize_aegislash_moves()
        
        # Verify moves are unchanged
        assert aegislash_blade.charged_move_1.buffs == original_buffs
        assert aegislash_blade.charged_move_1.buff_target == original_target
        assert aegislash_blade.charged_move_1.self_debuffing is False
    
    def test_regular_pokemon_does_not_modify_moves(self, regular_pokemon):
        """Test that regular Pokemon do not have their moves modified."""
        # Set up charged moves
        regular_pokemon.charged_move_1 = ChargedMove(
            move_id="ICE_BEAM",
            name="Ice Beam",
            move_type="ice",
            power=90,
            energy_cost=55,
            buffs=[1.0, 1.0],
            buff_target="opponent"
        )
        
        original_buffs = regular_pokemon.charged_move_1.buffs.copy()
        original_target = regular_pokemon.charged_move_1.buff_target
        
        # Initialize moves (should do nothing for regular Pokemon)
        regular_pokemon.initialize_aegislash_moves()
        
        # Verify moves are unchanged
        assert regular_pokemon.charged_move_1.buffs == original_buffs
        assert regular_pokemon.charged_move_1.buff_target == original_target
        assert regular_pokemon.charged_move_1.self_debuffing is False
    
    def test_self_debuffing_property_works_correctly(self, aegislash_shield):
        """Test that the self_debuffing property correctly identifies debuffing moves."""
        # Set up a charged move
        aegislash_shield.charged_move_1 = ChargedMove(
            move_id="SHADOW_BALL",
            name="Shadow Ball",
            move_type="ghost",
            power=100,
            energy_cost=55,
            buffs=[1.0, 1.0],
            buff_target="opponent"
        )
        
        # Before initialization, should not be self-debuffing
        assert aegislash_shield.charged_move_1.self_debuffing is False
        
        # Initialize Aegislash moves
        aegislash_shield.initialize_aegislash_moves()
        
        # After initialization, should be self-debuffing
        assert aegislash_shield.charged_move_1.self_debuffing is True
    
    def test_buff_values_are_zero_not_less_than_one(self, aegislash_shield):
        """Test that buff values are exactly [0.0, 0.0], not [<1, <1]."""
        # Set up charged moves
        aegislash_shield.charged_move_1 = ChargedMove(
            move_id="SHADOW_BALL",
            name="Shadow Ball",
            move_type="ghost",
            power=100,
            energy_cost=55,
            buffs=[1.0, 1.0],
            buff_target="opponent"
        )
        
        # Initialize Aegislash moves
        aegislash_shield.initialize_aegislash_moves()
        
        # Verify exact values
        assert aegislash_shield.charged_move_1.buffs[0] == 0.0
        assert aegislash_shield.charged_move_1.buffs[1] == 0.0
    
    def test_multiple_initializations_are_idempotent(self, aegislash_shield):
        """Test that calling initialize multiple times produces the same result."""
        # Set up charged moves
        aegislash_shield.charged_move_1 = ChargedMove(
            move_id="SHADOW_BALL",
            name="Shadow Ball",
            move_type="ghost",
            power=100,
            energy_cost=55,
            buffs=[1.0, 1.0],
            buff_target="opponent"
        )
        
        # Initialize multiple times
        aegislash_shield.initialize_aegislash_moves()
        first_buffs = aegislash_shield.charged_move_1.buffs.copy()
        first_target = aegislash_shield.charged_move_1.buff_target
        
        aegislash_shield.initialize_aegislash_moves()
        second_buffs = aegislash_shield.charged_move_1.buffs.copy()
        second_target = aegislash_shield.charged_move_1.buff_target
        
        # Verify results are the same
        assert first_buffs == second_buffs == [0.0, 0.0]
        assert first_target == second_target == "self"
    
    def test_shield_form_with_self_buffing_move(self, aegislash_shield):
        """Test that even self-buffing moves are converted to self-debuffing."""
        # Set up a self-buffing move (hypothetically)
        aegislash_shield.charged_move_1 = ChargedMove(
            move_id="ANCIENT_POWER",
            name="Ancient Power",
            move_type="rock",
            power=70,
            energy_cost=45,
            buffs=[1.25, 1.25],  # Self-buff
            buff_target="self",
            buff_chance=0.1
        )
        
        # Before initialization, should be self-buffing
        assert aegislash_shield.charged_move_1.self_buffing is True
        assert aegislash_shield.charged_move_1.self_debuffing is False
        
        # Initialize Aegislash moves
        aegislash_shield.initialize_aegislash_moves()
        
        # After initialization, should be self-debuffing, not buffing
        assert aegislash_shield.charged_move_1.buffs == [0.0, 0.0]
        assert aegislash_shield.charged_move_1.buff_target == "self"
        assert aegislash_shield.charged_move_1.self_debuffing is True
        assert aegislash_shield.charged_move_1.self_buffing is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
