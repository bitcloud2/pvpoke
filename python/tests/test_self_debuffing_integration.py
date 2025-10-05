"""Integration test for self-debuffing move deferral logic."""

import pytest
from unittest.mock import Mock, patch
from pvpoke.battle.ai import ActionLogic
from pvpoke.core.pokemon import Pokemon
from pvpoke.core.moves import ChargedMove, FastMove


class TestSelfDebuffingIntegration:
    """Test self-debuffing move deferral in realistic scenarios."""
    
    def setup_method(self):
        """Set up realistic test scenario."""
        # Create Machamp with Superpower (self-debuffing)
        self.machamp = Mock(spec=Pokemon)
        self.machamp.index = 0
        self.machamp.species_id = "machamp"
        self.machamp.shields = 0
        self.machamp.energy = 50
        self.machamp.current_hp = 100
        self.machamp.stats = Mock()
        self.machamp.stats.atk = 234
        self.machamp.stats.hp = 180
        
        # Create Machamp's fast move (Counter)
        self.counter = Mock(spec=FastMove)
        self.counter.move_id = "COUNTER"
        self.counter.energy_gain = 3
        self.counter.turns = 1
        self.counter.damage = 12
        self.machamp.fast_move = self.counter
        
        # Create Superpower (self-debuffing move)
        self.superpower = Mock(spec=ChargedMove)
        self.superpower.move_id = "SUPERPOWER"
        self.superpower.energy_cost = 40
        self.superpower.self_debuffing = True
        self.superpower.self_buffing = False
        
        # Create Dynamic Punch (normal move)
        self.dynamic_punch = Mock(spec=ChargedMove)
        self.dynamic_punch.move_id = "DYNAMIC_PUNCH"
        self.dynamic_punch.energy_cost = 50
        self.dynamic_punch.self_debuffing = False
        self.dynamic_punch.self_buffing = False
        
        self.machamp.charged_move_1 = self.superpower
        self.machamp.charged_move_2 = self.dynamic_punch
        
        # Create Swampert opponent with Hydro Cannon
        self.swampert = Mock(spec=Pokemon)
        self.swampert.index = 1
        self.swampert.species_id = "swampert"
        self.swampert.shields = 1
        self.swampert.energy = 40  # Has energy for Hydro Cannon
        self.swampert.current_hp = 120
        self.swampert.stats = Mock()
        self.swampert.stats.atk = 208
        
        # Create Swampert's fast move (Mud Shot)
        self.mud_shot = Mock(spec=FastMove)
        self.mud_shot.move_id = "MUD_SHOT"
        self.mud_shot.energy_gain = 3
        self.mud_shot.turns = 1
        self.mud_shot.damage = 5
        self.swampert.fast_move = self.mud_shot
        
        # Create Hydro Cannon (lethal move)
        self.hydro_cannon = Mock(spec=ChargedMove)
        self.hydro_cannon.move_id = "HYDRO_CANNON"
        self.hydro_cannon.energy_cost = 40
        self.hydro_cannon.move_type = "charged"
        self.swampert.best_charged_move = self.hydro_cannon
        self.swampert.charged_move_1 = self.hydro_cannon
        self.swampert.charged_move_2 = None
        
        # Create mock battle
        self.battle = Mock()
        self.battle.current_turn = 10
        self.battle.log_decision = Mock()
    
    def test_deferral_logic_integration(self):
        """Test that deferral logic properly integrates with the decision flow."""
        # Mock the would_shield method to avoid complex damage calculations
        with patch.object(ActionLogic, 'would_shield') as mock_shield:
            from pvpoke.battle.ai import ShieldDecision
            mock_shield.return_value = ShieldDecision(value=False, shield_weight=0, no_shield_weight=10)
            
            # Test the individual deferral method first
            result = ActionLogic.should_defer_self_debuffing_move(
                self.battle, self.machamp, self.swampert, self.superpower
            )
            
            # Should defer because:
            # - Machamp has no shields (0)
            # - Machamp has low energy (50 < 100)
            # - Swampert has energy for lethal move (40 >= 40)
            # - Superpower is self-debuffing
            # - Opponent won't shield (mocked)
            assert result is True
            
            # Test when conditions are not met (Pokemon has shields)
            self.machamp.shields = 1
            result = ActionLogic.should_defer_self_debuffing_move(
                self.battle, self.machamp, self.swampert, self.superpower
            )
            
            # Should not defer when Pokemon has shields
            assert result is False
    
    def test_survivability_assessment_integration(self):
        """Test survivability assessment with realistic Pokemon."""
        # Test when opponent has no best charged move
        self.swampert.best_charged_move = None
        
        result = ActionLogic.assess_survivability_against_opponent_move(
            self.machamp, self.swampert
        )
        
        # Should survive when opponent has no lethal move
        assert result is True
        
        # Test with shields (damage calculation would be mocked in full integration)
        self.swampert.best_charged_move = self.hydro_cannon
        self.machamp.shields = 1  # Has shield
        
        # Mock the damage calculation to avoid complex setup
        with patch('pvpoke.battle.ai.DamageCalculator.calculate_damage') as mock_damage:
            mock_damage.return_value = 100  # High damage
            
            result = ActionLogic.assess_survivability_against_opponent_move(
                self.machamp, self.swampert
            )
            
            # Should survive due to shield (damage reduced to 1)
            assert result is True
    
    def test_self_buffing_exception_integration(self):
        """Test self-buffing exception with realistic moves."""
        # Create Power-Up Punch (self-buffing)
        power_up_punch = Mock(spec=ChargedMove)
        power_up_punch.move_id = "POWER_UP_PUNCH"
        power_up_punch.energy_cost = 35
        power_up_punch.self_buffing = True
        
        # Replace one of Machamp's moves
        self.machamp.charged_move_1 = power_up_punch
        
        # Test with sufficient energy
        self.machamp.energy = 40
        
        result = ActionLogic.has_self_buffing_exception(self.machamp)
        
        # Should have exception due to self-buffing move
        assert result is True
        
        # Test with insufficient energy
        self.machamp.energy = 30
        
        result = ActionLogic.has_self_buffing_exception(self.machamp)
        
        # Should not have exception due to insufficient energy
        assert result is False
    
    def test_get_active_charged_moves_integration(self):
        """Test that get_active_charged_moves works with our setup."""
        active_moves = ActionLogic.get_active_charged_moves(self.machamp)
        
        # Should return both moves
        assert len(active_moves) == 2
        assert self.superpower in active_moves
        assert self.dynamic_punch in active_moves
        
        # Test with only one move
        self.machamp.charged_move_2 = None
        active_moves = ActionLogic.get_active_charged_moves(self.machamp)
        
        assert len(active_moves) == 1
        assert self.superpower in active_moves


if __name__ == "__main__":
    pytest.main([__file__])
