"""
Tests for Aegislash Form Change Logic (Step 1R).

This module tests the special form change logic for Aegislash Shield form,
which wants to maximize energy before switching to Blade form to minimize
time spent in the vulnerable Blade form.
"""

import pytest
from pvpoke.core.pokemon import Pokemon, Stats, IVs
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.battle.ai import ActionLogic
from pvpoke.battle.damage_calculator import DamageCalculator


class MockBattle:
    """Mock battle object for testing."""
    
    def __init__(self, mode="simulate"):
        self.current_turn = 0
        self.mode = mode
        self.decision_log = []
    
    def get_mode(self):
        return self.mode
    
    def log_decision(self, poke, message):
        self.decision_log.append(f"{poke.species_id}: {message}")


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
    
    # Set up moves
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
    
    aegislash.charged_move_2 = ChargedMove(
        move_id="GYRO_BALL",
        name="Gyro Ball",
        move_type="steel",
        power=80,
        energy_cost=60
    )
    
    # Set form-specific properties
    aegislash.active_form_id = "aegislash_shield"
    aegislash.best_charged_move = aegislash.charged_move_1
    aegislash.energy = 0
    aegislash.current_hp = 100
    aegislash.index = 0
    
    return aegislash


@pytest.fixture
def opponent():
    """Create an opponent Pokemon."""
    opponent = Pokemon(
        species_id="azumarill",
        species_name="Azumarill",
        dex=184,
        base_stats=Stats(atk=112, defense=152, hp=225),
        types=["water", "fairy"],
        level=40.0,
        ivs=IVs(0, 15, 15)
    )
    
    opponent.fast_move = FastMove(
        move_id="BUBBLE",
        name="Bubble",
        move_type="water",
        power=8,
        energy_gain=11,
        turns=2
    )
    
    opponent.charged_move_1 = ChargedMove(
        move_id="ICE_BEAM",
        name="Ice Beam",
        move_type="ice",
        power=90,
        energy_cost=55
    )
    
    opponent.energy = 0
    opponent.current_hp = 150
    opponent.index = 1
    
    return opponent


class TestAegislashEnergyThreshold:
    """Test energy threshold calculation for Aegislash."""
    
    def test_energy_below_threshold_should_build(self, aegislash_shield, opponent):
        """Aegislash should build energy when below threshold."""
        battle = MockBattle(mode="simulate")
        
        # Set energy below threshold: 100 - (9 / 2) = 95.5
        aegislash_shield.energy = 90
        opponent.current_hp = 150  # Move won't KO
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is True
    
    def test_energy_at_threshold_should_not_build(self, aegislash_shield, opponent):
        """Aegislash should not build energy when at or above threshold."""
        battle = MockBattle(mode="simulate")
        
        # Set energy at threshold: 100 - (9 / 2) = 95.5
        aegislash_shield.energy = 96
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is False
    
    def test_energy_above_threshold_should_not_build(self, aegislash_shield, opponent):
        """Aegislash should not build energy when above threshold."""
        battle = MockBattle(mode="simulate")
        
        # Set energy above threshold
        aegislash_shield.energy = 100
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is False


class TestAegislashBattleMode:
    """Test battle mode consideration for Aegislash."""
    
    def test_simulate_mode_move_wont_ko(self, aegislash_shield, opponent):
        """In simulate mode, build energy if move won't KO opponent."""
        battle = MockBattle(mode="simulate")
        
        aegislash_shield.energy = 90
        opponent.current_hp = 150  # High HP, move won't KO
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is True
    
    def test_simulate_mode_move_will_ko(self, aegislash_shield, opponent):
        """In simulate mode, don't build energy if move will KO opponent."""
        battle = MockBattle(mode="simulate")
        
        aegislash_shield.energy = 90
        opponent.current_hp = 1  # Very low HP, move will KO
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is False
    
    def test_emulate_mode_always_builds(self, aegislash_shield, opponent):
        """In emulate mode, always build energy for optimal play."""
        battle = MockBattle(mode="emulate")
        
        aegislash_shield.energy = 90
        opponent.current_hp = 1  # Even with low HP opponent
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is True


class TestAegislashFormCheck:
    """Test form-specific checks for Aegislash."""
    
    def test_non_aegislash_should_not_build(self, opponent):
        """Non-Aegislash Pokemon should not trigger energy building."""
        battle = MockBattle(mode="simulate")
        
        # Create a regular Pokemon
        regular_pokemon = opponent
        regular_pokemon.active_form_id = None
        regular_pokemon.energy = 90
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, regular_pokemon, opponent
        )
        
        assert result is False
    
    def test_aegislash_blade_should_not_build(self, aegislash_shield, opponent):
        """Aegislash in Blade form should not trigger energy building."""
        battle = MockBattle(mode="simulate")
        
        # Change to Blade form
        aegislash_shield.active_form_id = "aegislash_blade"
        aegislash_shield.energy = 90
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is False
    
    def test_aegislash_shield_should_build(self, aegislash_shield, opponent):
        """Aegislash in Shield form should trigger energy building."""
        battle = MockBattle(mode="simulate")
        
        aegislash_shield.active_form_id = "aegislash_shield"
        aegislash_shield.energy = 90
        opponent.current_hp = 150
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is True


class TestAegislashBestChargedMove:
    """Test best charged move consideration for Aegislash."""
    
    def test_no_best_charged_move_should_not_build(self, aegislash_shield, opponent):
        """Without best_charged_move, should not build energy in simulate mode."""
        battle = MockBattle(mode="simulate")
        
        aegislash_shield.energy = 90
        aegislash_shield.best_charged_move = None
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is False
    
    def test_with_best_charged_move_should_build(self, aegislash_shield, opponent):
        """With best_charged_move set, should build energy properly."""
        battle = MockBattle(mode="simulate")
        
        aegislash_shield.energy = 90
        aegislash_shield.best_charged_move = aegislash_shield.charged_move_1
        opponent.current_hp = 150
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is True


class TestAegislashIntegration:
    """Test integration with decide_action method."""
    
    def test_decide_action_builds_energy_below_threshold(self, aegislash_shield, opponent):
        """decide_action should return None (fast move) when building energy."""
        battle = MockBattle(mode="simulate")
        
        aegislash_shield.active_form_id = "aegislash_shield"
        aegislash_shield.energy = 90  # Below threshold
        aegislash_shield.best_charged_move = aegislash_shield.charged_move_1
        opponent.current_hp = 150
        
        # Give enough energy for a charged move
        aegislash_shield.energy = 60
        
        action = ActionLogic.decide_action(battle, aegislash_shield, opponent)
        
        # Should return None to use fast move (build energy)
        assert action is None
        # Check decision log
        assert any("wants to gain as much energy as possible before changing form" in msg 
                  for msg in battle.decision_log)
    
    def test_decide_action_uses_charged_move_above_threshold(self, aegislash_shield, opponent):
        """decide_action should use charged move when above threshold."""
        battle = MockBattle(mode="simulate")
        
        aegislash_shield.active_form_id = "aegislash_shield"
        aegislash_shield.energy = 100  # At max energy (above threshold)
        aegislash_shield.best_charged_move = aegislash_shield.charged_move_1
        opponent.current_hp = 150
        
        action = ActionLogic.decide_action(battle, aegislash_shield, opponent)
        
        # Should return a charged move action
        assert action is not None
        assert action.action_type == "charged"
    
    def test_decide_action_emulate_mode_always_builds(self, aegislash_shield, opponent):
        """In emulate mode, should always build energy below threshold."""
        battle = MockBattle(mode="emulate")
        
        aegislash_shield.active_form_id = "aegislash_shield"
        aegislash_shield.energy = 60  # Below threshold, enough for charged move
        aegislash_shield.best_charged_move = aegislash_shield.charged_move_1
        opponent.current_hp = 1  # Even with low HP opponent
        
        action = ActionLogic.decide_action(battle, aegislash_shield, opponent)
        
        # Should return None to use fast move (build energy)
        assert action is None
        assert any("wants to gain as much energy as possible before changing form" in msg 
                  for msg in battle.decision_log)


class TestAegislashEdgeCases:
    """Test edge cases for Aegislash form change logic."""
    
    def test_exact_threshold_energy(self, aegislash_shield, opponent):
        """Test behavior at exact energy threshold."""
        battle = MockBattle(mode="simulate")
        
        # Calculate exact threshold: 100 - (9 / 2) = 95.5
        # At 95.5, should not build (not less than threshold)
        aegislash_shield.energy = 95.5
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is False
    
    def test_just_below_threshold_energy(self, aegislash_shield, opponent):
        """Test behavior just below energy threshold."""
        battle = MockBattle(mode="simulate")
        
        # Just below threshold: 95.4
        aegislash_shield.energy = 95.4
        opponent.current_hp = 150
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is True
    
    def test_zero_energy(self, aegislash_shield, opponent):
        """Test behavior with zero energy."""
        battle = MockBattle(mode="simulate")
        
        aegislash_shield.energy = 0
        opponent.current_hp = 150
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is True
    
    def test_different_fast_move_energy_gain(self, aegislash_shield, opponent):
        """Test threshold calculation with different fast move energy gain."""
        battle = MockBattle(mode="simulate")
        
        # Change fast move energy gain
        aegislash_shield.fast_move.energy_gain = 12
        # New threshold: 100 - (12 / 2) = 94
        
        aegislash_shield.energy = 93  # Below new threshold
        opponent.current_hp = 150
        
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is True
        
        # Test at new threshold
        aegislash_shield.energy = 94
        result = ActionLogic.should_build_energy_for_aegislash(
            battle, aegislash_shield, opponent
        )
        
        assert result is False


class TestAegislashDecisionLogging:
    """Test decision logging for Aegislash."""
    
    def test_logs_energy_building_decision(self, aegislash_shield, opponent):
        """Should log decision when building energy."""
        battle = MockBattle(mode="simulate")
        
        aegislash_shield.energy = 90
        opponent.current_hp = 150
        
        ActionLogic.should_build_energy_for_aegislash(battle, aegislash_shield, opponent)
        
        # The logging happens in decide_action, not in the helper method
        # So we test it through decide_action
        aegislash_shield.energy = 60  # Enough for charged move
        action = ActionLogic.decide_action(battle, aegislash_shield, opponent)
        
        assert action is None
        assert len(battle.decision_log) > 0
        assert any("wants to gain as much energy as possible before changing form" in msg 
                  for msg in battle.decision_log)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
