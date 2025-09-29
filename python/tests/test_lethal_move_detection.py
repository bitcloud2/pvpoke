"""Tests for lethal move detection in battle AI."""

import pytest
from unittest.mock import Mock, MagicMock
from pvpoke.battle.ai import ActionLogic, TimelineAction
from pvpoke.core.pokemon import Pokemon
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.battle.damage_calculator import DamageCalculator


class TestLethalMoveDetection:
    """Test lethal move detection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock Pokemon
        self.attacker = Mock(spec=Pokemon)
        self.attacker.index = 0
        self.attacker.energy = 50
        self.attacker.current_hp = 100
        self.attacker.shields = 0
        # Add missing attributes with defaults
        self.attacker.farm_energy = False
        self.attacker.bait_shields = False
        
        # Add mock stats for integration tests
        self.attacker.stats = Mock()
        self.attacker.stats.atk = 150
        
        self.defender = Mock(spec=Pokemon)
        self.defender.index = 1
        self.defender.current_hp = 30
        self.defender.shields = 0
        self.defender.energy = 20
        
        # Add mock stats for integration tests
        self.defender.stats = Mock()
        self.defender.stats.atk = 140
        
        # Create mock moves
        self.fast_move = Mock(spec=FastMove)
        self.fast_move.damage = 5
        self.fast_move.energy_gain = 3
        self.fast_move.cooldown = 500
        self.fast_move.turns = 1
        
        self.charged_move_1 = Mock(spec=ChargedMove)
        self.charged_move_1.move_id = "HYDRO_PUMP"
        self.charged_move_1.energy_cost = 40
        self.charged_move_1.self_debuffing = False
        
        self.charged_move_2 = Mock(spec=ChargedMove)
        self.charged_move_2.move_id = "SURF"
        self.charged_move_2.energy_cost = 35
        self.charged_move_2.self_debuffing = False
        
        # Set up Pokemon moves
        self.attacker.fast_move = self.fast_move
        self.attacker.charged_move_1 = self.charged_move_1
        self.attacker.charged_move_2 = self.charged_move_2
        
        self.defender.fast_move = self.fast_move
        self.defender.charged_move_1 = self.charged_move_1
        self.defender.charged_move_2 = self.charged_move_2
        self.defender.cooldown = 0
        
        # Mock battle
        self.battle = Mock()
        self.battle.current_turn = 10
        
        # Mock damage calculator
        self.original_calculate_damage = DamageCalculator.calculate_damage
        DamageCalculator.calculate_damage = Mock(return_value=35)
    
    def teardown_method(self):
        """Clean up after tests."""
        DamageCalculator.calculate_damage = self.original_calculate_damage
    
    def test_can_ko_opponent_basic_lethal(self):
        """Test basic lethal move detection."""
        # Setup: Defender has 30 HP, move does 35 damage
        DamageCalculator.calculate_damage.return_value = 35
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is True
        assert lethal_move == self.charged_move_1
        assert DamageCalculator.calculate_damage.called
    
    def test_can_ko_opponent_no_lethal(self):
        """Test when no moves can KO opponent."""
        # Setup: Defender has 30 HP, move does 20 damage
        DamageCalculator.calculate_damage.return_value = 20
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is False
        assert lethal_move is None
    
    def test_can_ko_opponent_insufficient_energy(self):
        """Test when Pokemon doesn't have enough energy."""
        # Setup: Not enough energy for any moves
        self.attacker.energy = 30  # Less than both moves' energy cost
        DamageCalculator.calculate_damage.return_value = 35
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is False
        assert lethal_move is None
    
    def test_can_ko_opponent_shields_block(self):
        """Test that shields prevent lethal detection."""
        # Setup: Defender has shields
        self.defender.shields = 1
        DamageCalculator.calculate_damage.return_value = 35
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is False
        assert lethal_move is None
    
    def test_can_ko_opponent_farming_energy(self):
        """Test that farming energy prevents lethal detection."""
        # Setup: Pokemon is farming energy
        self.attacker.farm_energy = True
        DamageCalculator.calculate_damage.return_value = 35
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is False
        assert lethal_move is None
    
    def test_can_ko_opponent_self_debuffing_move(self):
        """Test that self-debuffing moves are excluded."""
        # Setup: Only move available is self-debuffing
        self.charged_move_1.self_debuffing = True
        self.attacker.charged_move_2 = None
        DamageCalculator.calculate_damage.return_value = 35
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is False
        assert lethal_move is None
    
    def test_can_ko_opponent_fast_move_would_ko(self):
        """Test exclusion when fast move would KO anyway."""
        # Setup: Fast move damage >= opponent HP
        self.fast_move.damage = 30  # Same as defender HP
        DamageCalculator.calculate_damage.return_value = 35
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is False
        assert lethal_move is None
    
    def test_can_ko_opponent_bait_shields_logic(self):
        """Test bait shields logic for second move."""
        # Setup: Only second move is lethal, but baiting shields
        self.attacker.bait_shields = True
        self.attacker.energy = 100  # Enough for both moves
        
        # First move can't KO, second move can
        def damage_side_effect(attacker, defender, move):
            if move == self.charged_move_1:
                return 20  # Not lethal
            elif move == self.charged_move_2:
                return 35  # Lethal
            return 0
        
        DamageCalculator.calculate_damage.side_effect = damage_side_effect
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        # Should not use second move when baiting shields
        assert can_ko is False
        assert lethal_move is None
    
    def test_can_ko_opponent_no_bait_shields(self):
        """Test second move can be used when not baiting shields."""
        # Setup: Only second move is lethal, not baiting shields
        self.attacker.bait_shields = False
        self.attacker.energy = 100  # Enough for both moves
        
        # First move can't KO, second move can
        def damage_side_effect(attacker, defender, move):
            if move == self.charged_move_1:
                return 20  # Not lethal
            elif move == self.charged_move_2:
                return 35  # Lethal
            return 0
        
        DamageCalculator.calculate_damage.side_effect = damage_side_effect
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is True
        assert lethal_move == self.charged_move_2
    
    def test_calculate_lethal_damage(self):
        """Test lethal damage calculation."""
        DamageCalculator.calculate_damage.return_value = 42
        
        damage = ActionLogic.calculate_lethal_damage(self.attacker, self.defender, self.charged_move_1)
        
        assert damage == 42
        DamageCalculator.calculate_damage.assert_called_once_with(
            self.attacker, self.defender, self.charged_move_1
        )
    
    def test_select_best_lethal_move_first_priority(self):
        """Test that first move gets priority."""
        lethal_moves = [
            (self.charged_move_2, 35, 1),  # Second move
            (self.charged_move_1, 40, 0),  # First move
        ]
        
        best_move = ActionLogic.select_best_lethal_move(lethal_moves)
        
        # Should select first move (index 0) even though it's listed second
        assert best_move == self.charged_move_1
    
    def test_select_best_lethal_move_single_option(self):
        """Test selection with single lethal move."""
        lethal_moves = [(self.charged_move_2, 35, 1)]
        
        best_move = ActionLogic.select_best_lethal_move(lethal_moves)
        
        assert best_move == self.charged_move_2
    
    def test_integration_lethal_detection_called(self):
        """Test that lethal detection is properly integrated."""
        # Mock the can_ko_opponent method to verify it's called
        original_can_ko = ActionLogic.can_ko_opponent
        ActionLogic.can_ko_opponent = Mock(return_value=(True, self.charged_move_1))
        
        try:
            # Setup minimal conditions to reach lethal detection
            self.attacker.energy = 50  # Enough for moves
            
            action = ActionLogic.decide_action(self.battle, self.attacker, self.defender)
            
            # Verify can_ko_opponent was called
            ActionLogic.can_ko_opponent.assert_called_once_with(self.attacker, self.defender)
            
            # Verify lethal move is used
            assert action is not None
            assert action.action_type == "charged"
            assert action.value == 0  # First move index
            
        finally:
            ActionLogic.can_ko_opponent = original_can_ko
    
    def test_integration_no_lethal_continues(self):
        """Test that non-lethal scenarios continue past lethal detection."""
        # Mock can_ko_opponent to return False (no lethal moves)
        original_can_ko = ActionLogic.can_ko_opponent
        ActionLogic.can_ko_opponent = Mock(return_value=(False, None))
        
        # Mock timing optimization to return True (optimize timing)
        original_optimize = ActionLogic.optimize_move_timing
        ActionLogic.optimize_move_timing = Mock(return_value=True)
        
        try:
            action = ActionLogic.decide_action(self.battle, self.attacker, self.defender)
            
            # Should call lethal detection first
            ActionLogic.can_ko_opponent.assert_called_once()
            
            # Should continue to timing optimization
            ActionLogic.optimize_move_timing.assert_called_once()
            
            # Should return None (fast move) due to timing optimization
            assert action is None
            
        finally:
            ActionLogic.can_ko_opponent = original_can_ko
            ActionLogic.optimize_move_timing = original_optimize
    
    def test_no_charged_moves_available(self):
        """Test behavior when no charged moves are available."""
        self.attacker.charged_move_1 = None
        self.attacker.charged_move_2 = None
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is False
        assert lethal_move is None
    
    def test_one_charged_move_available(self):
        """Test with only one charged move available."""
        self.attacker.charged_move_2 = None
        DamageCalculator.calculate_damage.return_value = 35
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is True
        assert lethal_move == self.charged_move_1
    
    def test_edge_case_exact_damage(self):
        """Test edge case where damage exactly equals opponent HP."""
        self.defender.current_hp = 35
        DamageCalculator.calculate_damage.return_value = 35
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is True
        assert lethal_move == self.charged_move_1
    
    def test_edge_case_one_hp_difference(self):
        """Test edge case where damage is one less than opponent HP."""
        self.defender.current_hp = 36
        DamageCalculator.calculate_damage.return_value = 35
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent(self.attacker, self.defender)
        
        assert can_ko is False
        assert lethal_move is None


if __name__ == "__main__":
    pytest.main([__file__])
