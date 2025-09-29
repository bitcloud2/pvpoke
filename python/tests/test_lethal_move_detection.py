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


class TestAdvancedLethalMoveDetection:
    """Test advanced lethal move detection functionality (Step 1H)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock Pokemon
        self.attacker = Mock(spec=Pokemon)
        self.attacker.index = 0
        self.attacker.energy = 50
        self.attacker.current_hp = 100
        self.attacker.shields = 0
        self.attacker.farm_energy = False
        self.attacker.bait_shields = False
        
        # Add stat buffs for buff testing
        self.attacker.stat_buffs = [0, 0]  # [attack_buff, defense_buff]
        
        # Add mock stats for integration tests
        self.attacker.stats = Mock()
        self.attacker.stats.atk = 150
        
        self.defender = Mock(spec=Pokemon)
        self.defender.index = 1
        self.defender.current_hp = 30
        self.defender.shields = 0
        self.defender.energy = 20
        
        # Add stat buffs for buff testing
        self.defender.stat_buffs = [0, 0]  # [attack_buff, defense_buff]
        
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
        
        # Self-debuffing move for testing
        self.debuff_move = Mock(spec=ChargedMove)
        self.debuff_move.move_id = "SUPERPOWER"
        self.debuff_move.energy_cost = 40
        self.debuff_move.self_debuffing = True
        
        # Set up Pokemon moves
        self.attacker.fast_move = self.fast_move
        self.attacker.charged_move_1 = self.charged_move_1
        self.attacker.charged_move_2 = self.charged_move_2
        
        self.defender.fast_move = self.fast_move
        self.defender.charged_move_1 = self.charged_move_1
        self.defender.charged_move_2 = self.charged_move_2
        self.defender.cooldown = 0
        
        # Mock damage calculator
        self.original_calculate_damage = DamageCalculator.calculate_damage
        DamageCalculator.calculate_damage = Mock(return_value=25)  # Default non-lethal
    
    def teardown_method(self):
        """Clean up after tests."""
        DamageCalculator.calculate_damage = self.original_calculate_damage
    
    def test_multi_move_lethal_combination(self):
        """Test multi-move lethal combinations (charged + fast)."""
        # Setup: Charged move does 20 damage, fast move does 15, opponent has 30 HP
        def damage_side_effect(attacker, defender, move):
            if move == self.charged_move_1:
                return 20  # Leaves 10 HP
            elif move == self.fast_move:
                return 15  # Can finish the remaining 10 HP
            return 0
        
        DamageCalculator.calculate_damage.side_effect = damage_side_effect
        
        can_ko, move_sequence = ActionLogic.check_multi_move_lethal(self.attacker, self.defender)
        
        assert can_ko is True
        assert len(move_sequence) == 1
        assert move_sequence[0] == self.charged_move_1
    
    def test_multi_move_lethal_insufficient_damage(self):
        """Test multi-move combinations that can't KO."""
        # Setup: Combined damage is insufficient
        def damage_side_effect(attacker, defender, move):
            if move == self.charged_move_1:
                return 15  # Leaves 15 HP
            elif move == self.fast_move:
                return 10  # Only does 10 damage, can't finish
            return 0
        
        DamageCalculator.calculate_damage.side_effect = damage_side_effect
        
        can_ko, move_sequence = ActionLogic.check_multi_move_lethal(self.attacker, self.defender)
        
        assert can_ko is False
        assert move_sequence == []
    
    def test_multi_move_lethal_with_shields(self):
        """Test that multi-move detection respects shields."""
        self.defender.shields = 1
        DamageCalculator.calculate_damage.return_value = 20
        
        can_ko, move_sequence = ActionLogic.check_multi_move_lethal(self.attacker, self.defender)
        
        assert can_ko is False
        assert move_sequence == []
    
    def test_buffed_lethal_damage_calculation(self):
        """Test buffed damage calculation."""
        # Setup: +2 attack buff, -1 defense debuff
        attack_buff = 2
        defense_buff = -1
        
        # Mock base damage
        DamageCalculator.calculate_damage.return_value = 20
        
        buffed_damage = ActionLogic.calculate_buffed_lethal_damage(
            self.attacker, self.defender, self.charged_move_1, attack_buff, defense_buff
        )
        
        # Expected: 20 * 1.5 (attack +2) / 1.25 (defense -1) = 24
        # Note: defense_buff -1 means opponent has -1 defense, which increases their damage taken
        # Defense multiplier for -1 is 1.25 (they take more damage)
        expected_damage = int(20 * 1.5 / 1.25)
        assert buffed_damage == expected_damage
    
    def test_get_attack_multiplier(self):
        """Test attack multiplier calculation."""
        assert ActionLogic.get_attack_multiplier(-4) == 0.5
        assert ActionLogic.get_attack_multiplier(-2) == 0.667
        assert ActionLogic.get_attack_multiplier(0) == 1.0
        assert ActionLogic.get_attack_multiplier(2) == 1.5
        assert ActionLogic.get_attack_multiplier(4) == 2.0
    
    def test_get_defense_multiplier(self):
        """Test defense multiplier calculation."""
        assert ActionLogic.get_defense_multiplier(-4) == 2.0
        assert ActionLogic.get_defense_multiplier(-2) == 1.5
        assert ActionLogic.get_defense_multiplier(0) == 1.0
        assert ActionLogic.get_defense_multiplier(2) == 0.667
        assert ActionLogic.get_defense_multiplier(4) == 0.5
    
    def test_special_case_opponent_at_1_hp(self):
        """Test special case handling for opponent at 1 HP."""
        self.defender.current_hp = 1
        
        can_ko, lethal_move = ActionLogic.handle_special_lethal_cases(self.attacker, self.defender)
        
        assert can_ko is True
        # Should prefer lowest energy cost move
        assert lethal_move == self.charged_move_2  # 35 energy vs 40 energy
    
    def test_special_case_opponent_at_1_hp_no_energy(self):
        """Test special case when opponent at 1 HP but no energy for charged moves."""
        self.defender.current_hp = 1
        self.attacker.energy = 30  # Not enough for any charged move
        
        can_ko, lethal_move = ActionLogic.handle_special_lethal_cases(self.attacker, self.defender)
        
        assert can_ko is True
        assert lethal_move is None  # Should use fast move
    
    def test_special_case_low_hp_fast_move(self):
        """Test special case for very low HP with fast move."""
        self.defender.current_hp = 4
        DamageCalculator.calculate_damage.return_value = 5  # Fast move can KO
        
        can_ko, lethal_move = ActionLogic.handle_special_lethal_cases(self.attacker, self.defender)
        
        assert can_ko is True
        assert lethal_move is None  # Should use fast move
    
    def test_special_case_self_debuffing_lethal(self):
        """Test special case for self-debuffing moves that are still lethal."""
        self.attacker.charged_move_1 = self.debuff_move
        self.attacker.energy = 50  # Enough for debuff move
        DamageCalculator.calculate_damage.return_value = 35  # Lethal damage
        
        can_ko, lethal_move = ActionLogic.handle_special_lethal_cases(self.attacker, self.defender)
        
        assert can_ko is True
        assert lethal_move == self.debuff_move
    
    def test_buffed_lethal_moves_detection(self):
        """Test detection of moves that become lethal with buffs."""
        # Setup: Move normally does 25 damage, but with +2 attack buff does 37
        self.attacker.stat_buffs = [2, 0]  # +2 attack buff
        self.defender.current_hp = 35
        
        # Mock damage calculations
        def damage_side_effect(attacker, defender, move, attack_buff=0, defense_buff=0):
            base_damage = 25
            if attack_buff == 2:
                return int(base_damage * 1.5)  # 37 damage with +2 attack
            return base_damage
        
        DamageCalculator.calculate_damage.return_value = 25  # Normal damage
        ActionLogic.calculate_buffed_lethal_damage = Mock(return_value=37)  # Buffed damage
        
        can_ko, lethal_move = ActionLogic.check_buffed_lethal_moves(self.attacker, self.defender)
        
        assert can_ko is True
        assert lethal_move == self.charged_move_1
    
    def test_buffed_lethal_moves_no_buffs(self):
        """Test that buffed lethal detection skips when no buffs active."""
        # No buffs active
        self.attacker.stat_buffs = [0, 0]
        self.defender.stat_buffs = [0, 0]
        
        can_ko, lethal_move = ActionLogic.check_buffed_lethal_moves(self.attacker, self.defender)
        
        assert can_ko is False
        assert lethal_move is None
    
    def test_advanced_lethal_priority_ordering(self):
        """Test priority ordering in advanced lethal selection."""
        # Create multiple lethal options
        lethal_moves = [(self.charged_move_2, 35, 1)]  # Basic lethal (index 1)
        multi_moves = [self.charged_move_1]  # Multi-move option
        special_move = self.charged_move_2  # Special case (1 HP scenario)
        
        best_move = ActionLogic.select_best_lethal_move_advanced(
            lethal_moves, multi_moves, special_move
        )
        
        # Special case should win (lowest priority score)
        assert best_move == special_move
    
    def test_advanced_lethal_integration(self):
        """Test full advanced lethal detection integration."""
        # Mock all detection methods
        ActionLogic.can_ko_opponent = Mock(return_value=(False, None))
        ActionLogic.check_multi_move_lethal = Mock(return_value=(True, [self.charged_move_1]))
        ActionLogic.handle_special_lethal_cases = Mock(return_value=(False, None))
        ActionLogic.check_buffed_lethal_moves = Mock(return_value=(False, None))
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent_advanced(self.attacker, self.defender)
        
        assert can_ko is True
        # Should select from multi-move options since that's the only lethal option
        assert lethal_move == self.charged_move_1
    
    def test_advanced_lethal_fast_move_priority(self):
        """Test that fast move gets priority when returned by special cases."""
        ActionLogic.can_ko_opponent = Mock(return_value=(False, None))
        ActionLogic.check_multi_move_lethal = Mock(return_value=(False, []))
        ActionLogic.handle_special_lethal_cases = Mock(return_value=(True, None))  # Fast move
        ActionLogic.check_buffed_lethal_moves = Mock(return_value=(False, None))
        
        can_ko, lethal_move = ActionLogic.can_ko_opponent_advanced(self.attacker, self.defender)
        
        assert can_ko is True
        assert lethal_move is None  # None indicates fast move
    
    def test_move_efficiency_score_calculation(self):
        """Test move efficiency score calculation."""
        # Test basic move (index 0)
        score = ActionLogic.calculate_move_efficiency_score(
            self.charged_move_1, 35, 'basic', 0
        )
        expected = 40 + 0 + 0 - (35/100)  # energy_cost + index_penalty + type_penalty - damage_bonus
        assert abs(score - expected) < 0.1
        
        # Test multi-move (higher penalty)
        score = ActionLogic.calculate_move_efficiency_score(
            self.charged_move_1, 35, 'multi', 0
        )
        expected = 40 + 0 + 200 - (35/100)  # energy_cost + index_penalty + multi_penalty - damage_bonus
        assert abs(score - expected) < 0.1
        
        # Test self-debuffing move (additional penalty)
        score = ActionLogic.calculate_move_efficiency_score(
            self.debuff_move, 35, 'basic', 0
        )
        expected = 40 + 0 + 0 - (35/100) + 50  # energy_cost + penalties - damage_bonus + debuff_penalty
        assert abs(score - expected) < 0.1
    
    def test_advanced_lethal_integration_with_main_ai(self):
        """Test that advanced lethal detection is properly integrated with main AI."""
        # Mock advanced lethal detection
        original_advanced = ActionLogic.can_ko_opponent_advanced
        ActionLogic.can_ko_opponent_advanced = Mock(return_value=(True, self.charged_move_2))
        
        # Mock battle
        battle = Mock()
        battle.current_turn = 10
        
        try:
            action = ActionLogic.decide_action(battle, self.attacker, self.defender)
            
            # Verify advanced lethal detection was called
            ActionLogic.can_ko_opponent_advanced.assert_called_once_with(self.attacker, self.defender)
            
            # Verify correct action is returned
            assert action is not None
            assert action.action_type == "charged"
            assert action.value == 1  # Second move index
            
        finally:
            ActionLogic.can_ko_opponent_advanced = original_advanced
    
    def test_advanced_lethal_fast_move_integration(self):
        """Test that advanced lethal detection properly handles fast move returns."""
        # Mock advanced lethal detection to return fast move
        original_advanced = ActionLogic.can_ko_opponent_advanced
        ActionLogic.can_ko_opponent_advanced = Mock(return_value=(True, None))  # None = fast move
        
        # Mock battle
        battle = Mock()
        battle.current_turn = 10
        
        try:
            action = ActionLogic.decide_action(battle, self.attacker, self.defender)
            
            # Should return None for fast move
            assert action is None
            
        finally:
            ActionLogic.can_ko_opponent_advanced = original_advanced


if __name__ == "__main__":
    pytest.main([__file__])
