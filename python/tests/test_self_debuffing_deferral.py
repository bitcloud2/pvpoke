"""Tests for self-debuffing move deferral logic (Step 1O)."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pvpoke.battle.ai import ActionLogic, ShieldDecision
from pvpoke.core.pokemon import Pokemon
from pvpoke.core.moves import ChargedMove, FastMove


class TestSelfDebuffingMoveDeferral:
    """Test self-debuffing move deferral logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock Pokemon with self-debuffing move (Superpower)
        self.poke = Mock(spec=Pokemon)
        self.poke.shields = 0
        self.poke.energy = 50
        self.poke.current_hp = 100
        self.poke.stats = Mock()
        self.poke.stats.hp = 150
        
        # Create self-debuffing move (Superpower)
        self.superpower = Mock(spec=ChargedMove)
        self.superpower.move_id = "SUPERPOWER"
        self.superpower.energy_cost = 40
        self.superpower.self_debuffing = True
        self.superpower.self_buffing = False
        
        # Create self-buffing move (Power-Up Punch)
        self.power_up_punch = Mock(spec=ChargedMove)
        self.power_up_punch.move_id = "POWER_UP_PUNCH"
        self.power_up_punch.energy_cost = 35
        self.power_up_punch.self_debuffing = False
        self.power_up_punch.self_buffing = True
        
        # Create normal move (Body Slam)
        self.body_slam = Mock(spec=ChargedMove)
        self.body_slam.move_id = "BODY_SLAM"
        self.body_slam.energy_cost = 35
        self.body_slam.self_debuffing = False
        self.body_slam.self_buffing = False
        
        # Set up Pokemon moves
        self.poke.charged_move_1 = self.superpower
        self.poke.charged_move_2 = self.body_slam
        
        # Create opponent Pokemon
        self.opponent = Mock(spec=Pokemon)
        self.opponent.shields = 1
        self.opponent.energy = 60
        self.opponent.current_hp = 120
        
        # Create opponent's lethal move (Hydro Cannon)
        self.hydro_cannon = Mock(spec=ChargedMove)
        self.hydro_cannon.move_id = "HYDRO_CANNON"
        self.hydro_cannon.energy_cost = 40
        self.opponent.best_charged_move = self.hydro_cannon
        self.opponent.charged_move_1 = self.hydro_cannon
        
    def test_should_defer_non_debuffing_move_returns_false(self):
        """Test that non-debuffing moves are not deferred."""
        battle = Mock()
        result = ActionLogic.should_defer_self_debuffing_move(
            battle, self.poke, self.opponent, self.body_slam
        )
        assert result is False
    
    def test_should_defer_when_opponent_has_lethal_move_ready(self):
        """Test deferring self-debuffing move when opponent has lethal move ready."""
        # Set up conditions for deferral
        self.poke.shields = 0
        self.poke.energy = 50  # Low energy
        self.opponent.energy = 40  # Has energy for lethal move
        
        # Mock shield decision - opponent won't shield
        with patch.object(ActionLogic, 'would_shield') as mock_shield:
            mock_shield.return_value = ShieldDecision(value=False, shield_weight=0, no_shield_weight=10)
            
            # Mock get_active_charged_moves to return non-buffing move
            with patch.object(ActionLogic, 'get_active_charged_moves') as mock_moves:
                mock_moves.return_value = [self.superpower, self.body_slam]
                
                result = ActionLogic.should_defer_self_debuffing_move(
                    Mock(), self.poke, self.opponent, self.superpower
                )
                assert result is True
    
    def test_should_not_defer_when_pokemon_has_shields(self):
        """Test that moves are not deferred when Pokemon has shields."""
        self.poke.shields = 1  # Has shields
        self.poke.energy = 50
        self.opponent.energy = 40
        
        result = ActionLogic.should_defer_self_debuffing_move(
            Mock(), self.poke, self.opponent, self.superpower
        )
        assert result is False
    
    def test_should_not_defer_when_pokemon_has_high_energy(self):
        """Test that moves are not deferred when Pokemon has high energy."""
        self.poke.shields = 0
        self.poke.energy = 100  # High energy
        self.opponent.energy = 40
        
        result = ActionLogic.should_defer_self_debuffing_move(
            Mock(), self.poke, self.opponent, self.superpower
        )
        assert result is False
    
    def test_should_not_defer_when_opponent_lacks_energy(self):
        """Test that moves are not deferred when opponent lacks energy for lethal move."""
        self.poke.shields = 0
        self.poke.energy = 50
        self.opponent.energy = 30  # Not enough energy for lethal move
        
        result = ActionLogic.should_defer_self_debuffing_move(
            Mock(), self.poke, self.opponent, self.superpower
        )
        assert result is False
    
    def test_should_not_defer_when_opponent_would_shield(self):
        """Test that moves are not deferred when opponent would shield their own move."""
        self.poke.shields = 0
        self.poke.energy = 50
        self.opponent.energy = 40
        
        # Mock shield decision - opponent would shield
        with patch.object(ActionLogic, 'would_shield') as mock_shield:
            mock_shield.return_value = ShieldDecision(value=True, shield_weight=10, no_shield_weight=0)
            
            result = ActionLogic.should_defer_self_debuffing_move(
                Mock(), self.poke, self.opponent, self.superpower
            )
            assert result is False
    
    def test_should_not_defer_with_self_buffing_exception(self):
        """Test that self-debuffing moves are not deferred when first move is self-buffing."""
        self.poke.shields = 0
        self.poke.energy = 50
        self.opponent.energy = 40
        
        # Mock shield decision - opponent won't shield
        with patch.object(ActionLogic, 'would_shield') as mock_shield:
            mock_shield.return_value = ShieldDecision(value=False, shield_weight=0, no_shield_weight=10)
            
            # Mock get_active_charged_moves to return self-buffing move first
            with patch.object(ActionLogic, 'get_active_charged_moves') as mock_moves:
                mock_moves.return_value = [self.power_up_punch, self.superpower]
                
                result = ActionLogic.should_defer_self_debuffing_move(
                    Mock(), self.poke, self.opponent, self.superpower
                )
                assert result is False
    
    def test_should_not_defer_when_opponent_has_no_best_move(self):
        """Test that moves are not deferred when opponent has no best charged move."""
        self.poke.shields = 0
        self.poke.energy = 50
        self.opponent.energy = 40
        self.opponent.best_charged_move = None
        
        result = ActionLogic.should_defer_self_debuffing_move(
            Mock(), self.poke, self.opponent, self.superpower
        )
        assert result is False


class TestSurvivabilityAssessment:
    """Test survivability assessment methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.poke = Mock(spec=Pokemon)
        self.poke.shields = 0
        self.poke.current_hp = 100
        
        self.opponent = Mock(spec=Pokemon)
        self.hydro_cannon = Mock(spec=ChargedMove)
        self.hydro_cannon.move_id = "HYDRO_CANNON"
        self.opponent.best_charged_move = self.hydro_cannon
    
    def test_assess_survivability_with_no_opponent_move(self):
        """Test survivability when opponent has no best charged move."""
        self.opponent.best_charged_move = None
        
        result = ActionLogic.assess_survivability_against_opponent_move(
            self.poke, self.opponent
        )
        assert result is True
    
    def test_assess_survivability_pokemon_survives(self):
        """Test survivability when Pokemon can survive opponent's move."""
        # Mock damage calculation to return survivable damage
        with patch('pvpoke.battle.ai.DamageCalculator.calculate_damage') as mock_damage:
            mock_damage.return_value = 80  # Less than current HP
            
            result = ActionLogic.assess_survivability_against_opponent_move(
                self.poke, self.opponent
            )
            assert result is True
    
    def test_assess_survivability_pokemon_faints(self):
        """Test survivability when Pokemon would faint from opponent's move."""
        # Mock damage calculation to return lethal damage
        with patch('pvpoke.battle.ai.DamageCalculator.calculate_damage') as mock_damage:
            mock_damage.return_value = 120  # More than current HP
            
            result = ActionLogic.assess_survivability_against_opponent_move(
                self.poke, self.opponent
            )
            assert result is False
    
    def test_assess_survivability_with_shields(self):
        """Test survivability when Pokemon has shields."""
        self.poke.shields = 1
        
        # Mock damage calculation to return high damage
        with patch('pvpoke.battle.ai.DamageCalculator.calculate_damage') as mock_damage:
            mock_damage.return_value = 120  # Would be lethal without shield
            
            result = ActionLogic.assess_survivability_against_opponent_move(
                self.poke, self.opponent
            )
            assert result is True  # Shield reduces damage to 1


class TestSelfBuffingException:
    """Test self-buffing move exception logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.poke = Mock(spec=Pokemon)
        self.poke.energy = 50
        
        # Create self-buffing move
        self.power_up_punch = Mock(spec=ChargedMove)
        self.power_up_punch.move_id = "POWER_UP_PUNCH"
        self.power_up_punch.energy_cost = 35
        self.power_up_punch.self_buffing = True
        
        # Create normal move
        self.body_slam = Mock(spec=ChargedMove)
        self.body_slam.move_id = "BODY_SLAM"
        self.body_slam.energy_cost = 35
        self.body_slam.self_buffing = False
    
    def test_has_self_buffing_exception_with_no_moves(self):
        """Test self-buffing exception when Pokemon has no moves."""
        with patch.object(ActionLogic, 'get_active_charged_moves') as mock_moves:
            mock_moves.return_value = []
            
            result = ActionLogic.has_self_buffing_exception(self.poke)
            assert result is False
    
    def test_has_self_buffing_exception_with_buffing_move(self):
        """Test self-buffing exception when Pokemon has self-buffing move."""
        with patch.object(ActionLogic, 'get_active_charged_moves') as mock_moves:
            mock_moves.return_value = [self.power_up_punch, self.body_slam]
            
            result = ActionLogic.has_self_buffing_exception(self.poke)
            assert result is True
    
    def test_has_self_buffing_exception_without_buffing_move(self):
        """Test self-buffing exception when Pokemon has no self-buffing moves."""
        with patch.object(ActionLogic, 'get_active_charged_moves') as mock_moves:
            mock_moves.return_value = [self.body_slam]
            
            result = ActionLogic.has_self_buffing_exception(self.poke)
            assert result is False
    
    def test_has_self_buffing_exception_insufficient_energy(self):
        """Test self-buffing exception when Pokemon lacks energy for buffing move."""
        self.poke.energy = 30  # Not enough energy
        
        with patch.object(ActionLogic, 'get_active_charged_moves') as mock_moves:
            mock_moves.return_value = [self.power_up_punch, self.body_slam]
            
            result = ActionLogic.has_self_buffing_exception(self.poke)
            assert result is False


class TestDeferralIntegration:
    """Test integration of deferral logic with main decision flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock battle
        self.battle = Mock()
        self.battle.current_turn = 10
        self.battle.log_decision = Mock()
        
        # Create Pokemon with self-debuffing move
        self.poke = Mock(spec=Pokemon)
        self.poke.index = 0
        self.poke.shields = 0
        self.poke.energy = 50
        self.poke.current_hp = 100
        self.poke.stats = Mock()
        self.poke.stats.atk = 150
        
        # Create fast move
        self.fast_move = Mock(spec=FastMove)
        self.fast_move.energy_gain = 3
        self.fast_move.turns = 1
        self.poke.fast_move = self.fast_move
        
        # Create self-debuffing move
        self.superpower = Mock(spec=ChargedMove)
        self.superpower.move_id = "SUPERPOWER"
        self.superpower.energy_cost = 40
        self.superpower.self_debuffing = True
        self.poke.charged_move_1 = self.superpower
        self.poke.charged_move_2 = None
        
        # Create opponent
        self.opponent = Mock(spec=Pokemon)
        self.opponent.shields = 1
        self.opponent.energy = 60
        self.opponent.current_hp = 120
        self.opponent.stats = Mock()
        self.opponent.stats.atk = 140
        
        # Create opponent's lethal move
        self.hydro_cannon = Mock(spec=ChargedMove)
        self.hydro_cannon.move_id = "HYDRO_CANNON"
        self.hydro_cannon.energy_cost = 40
        self.opponent.best_charged_move = self.hydro_cannon
        self.opponent.charged_move_1 = self.hydro_cannon
        self.opponent.charged_move_2 = None
        
        # Create opponent's fast move
        self.opponent_fast = Mock(spec=FastMove)
        self.opponent_fast.energy_gain = 3
        self.opponent_fast.turns = 1
        self.opponent.fast_move = self.opponent_fast
    
    def test_decide_action_defers_self_debuffing_move(self):
        """Test that decide_action properly defers self-debuffing moves."""
        # Set up conditions for deferral
        self.poke.shields = 0
        self.poke.energy = 50
        self.opponent.energy = 40
        
        # Mock various dependencies
        with patch('pvpoke.battle.ai.DamageCalculator.calculate_damage') as mock_damage:
            mock_damage.return_value = 50  # Moderate damage
            
            with patch.object(ActionLogic, 'would_shield') as mock_shield:
                mock_shield.return_value = ShieldDecision(value=False, shield_weight=0, no_shield_weight=10)
                
                with patch.object(ActionLogic, 'get_active_charged_moves') as mock_moves:
                    mock_moves.return_value = [self.superpower]
                    
                    with patch.object(ActionLogic, '_apply_shield_baiting_logic') as mock_baiting:
                        mock_baiting.return_value = self.superpower
                        
                        # Mock the DP algorithm to return a state with the self-debuffing move
                        with patch.object(ActionLogic, 'can_ko_opponent_advanced') as mock_lethal:
                            mock_lethal.return_value = (False, None)
                            
                            with patch.object(ActionLogic, 'optimize_move_timing') as mock_timing:
                                mock_timing.return_value = False
                                
                                # This should trigger deferral and return None (fast move)
                                result = ActionLogic.decide_action(self.battle, self.poke, self.opponent)
                                
                                # Should return None to use fast move instead of charged move
                                assert result is None
                                
                                # Should log the deferral decision
                                self.battle.log_decision.assert_called()
                                log_calls = [call.args for call in self.battle.log_decision.call_args_list]
                                deferral_logged = any("deferring" in str(call) for call in log_calls)
                                assert deferral_logged
    
    def test_decide_action_does_not_defer_when_conditions_not_met(self):
        """Test that decide_action does not defer when deferral conditions are not met."""
        # Set up conditions where deferral should not happen
        self.poke.shields = 1  # Has shields
        self.poke.energy = 50
        self.opponent.energy = 40
        
        # Mock various dependencies
        with patch('pvpoke.battle.ai.DamageCalculator.calculate_damage') as mock_damage:
            mock_damage.return_value = 50
            
            with patch.object(ActionLogic, '_apply_shield_baiting_logic') as mock_baiting:
                mock_baiting.return_value = self.superpower
                
                with patch.object(ActionLogic, 'can_ko_opponent_advanced') as mock_lethal:
                    mock_lethal.return_value = (False, None)
                    
                    with patch.object(ActionLogic, 'optimize_move_timing') as mock_timing:
                        mock_timing.return_value = False
                        
                        # This should NOT trigger deferral
                        result = ActionLogic.decide_action(self.battle, self.poke, self.opponent)
                        
                        # Should return a TimelineAction for the charged move
                        assert result is not None
                        assert result.action_type == "charged"
                        assert result.value == 0  # First charged move


if __name__ == "__main__":
    pytest.main([__file__])
