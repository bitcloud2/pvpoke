"""
Test suite for Move Reordering Logic (Step 1L) in ActionLogic.

Tests the move reordering functionality that determines optimal move order
based on shields, energy costs, DPE ratios, and debuffing effects.
"""

import pytest
from unittest.mock import Mock, patch
from pvpoke.battle.ai import ActionLogic
from pvpoke.core.pokemon import Pokemon
from pvpoke.core.moves import ChargedMove
from pvpoke.battle.damage_calculator import DamageCalculator


class TestMoveReorderingLogic:
    """Test cases for move reordering logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock Pokemon
        self.poke = Mock(spec=Pokemon)
        self.poke.current_hp = 100
        self.poke.stats = Mock()
        self.poke.stats.hp = 150
        self.poke.energy = 80
        self.poke.bait_shields = True
        
        self.opponent = Mock(spec=Pokemon)
        self.opponent.current_hp = 120
        self.opponent.shields = 2
        
        # Create test moves with different properties
        self.low_energy_move = Mock(spec=ChargedMove)
        self.low_energy_move.move_id = "surf"
        self.low_energy_move.energy_cost = 35
        self.low_energy_move.self_debuffing = False
        
        self.high_energy_move = Mock(spec=ChargedMove)
        self.high_energy_move.move_id = "hydro_pump"
        self.high_energy_move.energy_cost = 65
        self.high_energy_move.self_debuffing = False
        
        self.debuffing_move = Mock(spec=ChargedMove)
        self.debuffing_move.move_id = "superpower"
        self.debuffing_move.energy_cost = 55
        self.debuffing_move.self_debuffing = True
        
        self.active_charged_moves = [self.low_energy_move, self.high_energy_move]
        
        # Mock battle for logging
        self.battle = Mock()
    
    @patch.object(DamageCalculator, 'calculate_damage')
    def test_damage_based_sorting_shields_down(self, mock_damage):
        """Test that moves are sorted by damage when shields are down and not baiting."""
        # Setup: Opponent has no shields, Pokemon not baiting
        self.opponent.shields = 0
        self.poke.bait_shields = False
        
        # Mock damage calculations - high energy move does more damage
        mock_damage.side_effect = lambda poke, opp, move: 80 if move == self.high_energy_move else 50
        
        optimal_moves = [self.low_energy_move, self.high_energy_move]
        
        result = ActionLogic.apply_move_reordering_logic(
            self.poke, self.opponent, optimal_moves, self.active_charged_moves,
            needs_boost=False, debuffing_move=False, battle=self.battle
        )
        
        # Should sort by damage (highest first)
        assert result[0] == self.high_energy_move
        assert result[1] == self.low_energy_move
    
    @patch.object(ActionLogic, 'calculate_move_dpe')
    def test_efficient_low_energy_preference_shields_up(self, mock_dpe):
        """Test preference for efficient low energy moves when shields are up."""
        # Setup: Opponent has shields
        self.opponent.shields = 2
        
        # Mock DPE calculations - low energy move is more efficient
        mock_dpe.side_effect = lambda poke, opp, move: 2.5 if move == self.low_energy_move else 2.0
        
        optimal_moves = [self.high_energy_move]  # DP chose high energy move
        
        result = ActionLogic.apply_move_reordering_logic(
            self.poke, self.opponent, optimal_moves, self.active_charged_moves,
            needs_boost=False, debuffing_move=False, battle=self.battle
        )
        
        # Should prefer the more efficient low energy move
        assert result[0] == self.low_energy_move
    
    @patch.object(ActionLogic, 'calculate_move_dpe')
    @patch.object(DamageCalculator, 'calculate_damage')
    def test_non_debuffing_preference_shields_down(self, mock_damage, mock_dpe):
        """Test preference for non-debuffing moves when shields are down and HP is high."""
        # Setup: Opponent has no shields, both Pokemon have high HP
        self.opponent.shields = 0
        self.poke.current_hp = 120  # 80% HP
        self.opponent.current_hp = 100
        
        # Mock damage - debuffing move doesn't do enough damage to KO
        mock_damage.return_value = 60  # 60% of opponent HP
        mock_dpe.return_value = 1.0
        
        optimal_moves = [self.debuffing_move]  # DP chose debuffing move
        
        result = ActionLogic.apply_move_reordering_logic(
            self.poke, self.opponent, optimal_moves, self.active_charged_moves,
            needs_boost=False, debuffing_move=True, battle=self.battle
        )
        
        # Should prefer non-debuffing alternative
        assert result[0] == self.low_energy_move
    
    @patch.object(ActionLogic, 'calculate_move_dpe')
    def test_same_energy_efficiency_preference(self, mock_dpe):
        """Test preference for more efficient move of same energy cost."""
        # Create two moves with same energy cost
        same_energy_move_1 = Mock(spec=ChargedMove)
        same_energy_move_1.move_id = "ice_beam"
        same_energy_move_1.energy_cost = 55
        same_energy_move_1.self_debuffing = False
        
        same_energy_move_2 = Mock(spec=ChargedMove)
        same_energy_move_2.move_id = "thunderbolt"
        same_energy_move_2.energy_cost = 55
        same_energy_move_2.self_debuffing = False
        
        # Mock DPE - first move is more efficient
        mock_dpe.side_effect = lambda poke, opp, move: 2.2 if move == same_energy_move_1 else 1.8
        
        active_moves = [same_energy_move_1, same_energy_move_2]
        optimal_moves = [same_energy_move_2]  # DP chose less efficient move
        
        result = ActionLogic.apply_move_reordering_logic(
            self.poke, self.opponent, optimal_moves, active_moves,
            needs_boost=False, debuffing_move=False, battle=self.battle
        )
        
        # Should switch to more efficient move of same energy
        assert result[0] == same_energy_move_1
    
    @patch.object(ActionLogic, 'calculate_move_dpe')
    def test_similar_energy_debuff_avoidance(self, mock_dpe):
        """Test preference for non-debuffing move of similar energy cost."""
        # Create debuffing move and similar energy non-debuffing move
        debuff_move = Mock(spec=ChargedMove)
        debuff_move.move_id = "superpower"
        debuff_move.energy_cost = 55
        debuff_move.self_debuffing = True
        
        similar_energy_move = Mock(spec=ChargedMove)
        similar_energy_move.move_id = "close_combat"
        similar_energy_move.energy_cost = 50  # Within 10 energy
        similar_energy_move.self_debuffing = False
        
        # Mock DPE - non-debuffing move is more efficient
        mock_dpe.side_effect = lambda poke, opp, move: 2.0 if move == similar_energy_move else 1.8
        
        active_moves = [similar_energy_move, debuff_move]
        optimal_moves = [debuff_move]  # DP chose debuffing move
        
        result = ActionLogic.apply_move_reordering_logic(
            self.poke, self.opponent, optimal_moves, active_moves,
            needs_boost=False, debuffing_move=True, battle=self.battle
        )
        
        # Should switch to non-debuffing move of similar energy
        assert result[0] == similar_energy_move
    
    def test_no_reordering_when_needs_boost(self):
        """Test that no reordering occurs when Pokemon needs stat boosts."""
        optimal_moves = [self.high_energy_move, self.low_energy_move]
        
        result = ActionLogic.apply_move_reordering_logic(
            self.poke, self.opponent, optimal_moves, self.active_charged_moves,
            needs_boost=True, debuffing_move=False, battle=self.battle
        )
        
        # Should return moves in original order
        assert result == optimal_moves
    
    @patch.object(DamageCalculator, 'calculate_damage')
    @patch.object(ActionLogic, 'calculate_move_dpe')
    def test_damage_sorting_with_baiting_disabled(self, mock_dpe, mock_damage):
        """Test damage sorting when baiting is disabled but other rules may still apply."""
        self.poke.bait_shields = False
        self.opponent.shields = 2  # Has shields but baiting disabled
        
        # Mock damage calculations - high energy move does more damage
        mock_damage.side_effect = lambda poke, opp, move: 90 if move == self.high_energy_move else 60
        
        # Mock DPE - high energy move is also more efficient (so no override by Rule 3)
        mock_dpe.side_effect = lambda poke, opp, move: 1.8 if move == self.high_energy_move else 1.5
        
        optimal_moves = [self.low_energy_move, self.high_energy_move]
        
        result = ActionLogic.apply_move_reordering_logic(
            self.poke, self.opponent, optimal_moves, self.active_charged_moves,
            needs_boost=False, debuffing_move=False, battle=self.battle
        )
        
        # Should sort by damage and not be overridden by efficiency rules
        assert result[0] == self.high_energy_move
    
    def test_empty_moves_handling(self):
        """Test handling of empty move lists."""
        result = ActionLogic.apply_move_reordering_logic(
            self.poke, self.opponent, [], self.active_charged_moves,
            needs_boost=False, debuffing_move=False, battle=self.battle
        )
        
        assert result == []
    
    @patch.object(ActionLogic, 'calculate_move_dpe')
    def test_no_alternative_moves_available(self, mock_dpe):
        """Test behavior when no alternative moves are available."""
        mock_dpe.return_value = 1.5
        
        # Only one move available
        single_move = [self.low_energy_move]
        optimal_moves = [self.low_energy_move]
        
        result = ActionLogic.apply_move_reordering_logic(
            self.poke, self.opponent, optimal_moves, single_move,
            needs_boost=False, debuffing_move=False, battle=self.battle
        )
        
        # Should return the single move unchanged
        assert result == optimal_moves


class TestMoveReorderingHelperMethods:
    """Test cases for move reordering helper methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.poke = Mock(spec=Pokemon)
        self.opponent = Mock(spec=Pokemon)
        self.battle = Mock()
        
        self.move_a = Mock(spec=ChargedMove)
        self.move_a.move_id = "move_a"
        
        self.move_b = Mock(spec=ChargedMove)
        self.move_b.move_id = "move_b"
    
    @patch.object(DamageCalculator, 'calculate_damage')
    def test_sort_moves_by_damage(self, mock_damage):
        """Test damage-based move sorting."""
        # Mock damage calculations
        mock_damage.side_effect = lambda poke, opp, move: 100 if move == self.move_a else 80
        
        moves = [self.move_b, self.move_a]  # Lower damage move first
        
        ActionLogic._sort_moves_by_damage(self.poke, self.opponent, moves, self.battle)
        
        # Should be sorted by damage (highest first)
        assert moves[0] == self.move_a
        assert moves[1] == self.move_b
    
    @patch.object(ActionLogic, 'calculate_move_dpe')
    def test_prefer_efficient_low_energy_move(self, mock_dpe):
        """Test preference for efficient low energy moves."""
        # Setup moves with different energy costs and DPE
        low_energy = Mock(spec=ChargedMove)
        low_energy.move_id = "low_energy"
        low_energy.energy_cost = 35
        low_energy.self_debuffing = False
        
        high_energy = Mock(spec=ChargedMove)
        high_energy.move_id = "high_energy"
        high_energy.energy_cost = 65
        
        # Low energy move is more efficient
        mock_dpe.side_effect = lambda poke, opp, move: 2.5 if move == low_energy else 2.0
        
        result = ActionLogic._prefer_efficient_low_energy_move(
            self.poke, self.opponent, high_energy, [low_energy], self.battle
        )
        
        assert result == low_energy
    
    @patch.object(DamageCalculator, 'calculate_damage')
    def test_prefer_non_debuffing_shields_down(self, mock_damage):
        """Test preference for non-debuffing moves when shields are down."""
        # Setup Pokemon with high HP
        self.poke.current_hp = 120
        self.poke.stats = Mock()
        self.poke.stats.hp = 150  # 80% HP
        
        self.opponent.current_hp = 100
        
        # Setup debuffing move that doesn't do enough damage
        debuff_move = Mock(spec=ChargedMove)
        debuff_move.move_id = "superpower"
        debuff_move.energy_cost = 55
        debuff_move.self_debuffing = True
        
        non_debuff_move = Mock(spec=ChargedMove)
        non_debuff_move.move_id = "close_combat"
        non_debuff_move.self_debuffing = False
        
        # Mock damage - not enough to KO
        mock_damage.return_value = 70  # 70% of opponent HP
        
        result = ActionLogic._prefer_non_debuffing_move_shields_down(
            self.poke, self.opponent, debuff_move, [non_debuff_move], self.battle
        )
        
        assert result == non_debuff_move
    
    @patch.object(ActionLogic, 'calculate_move_dpe')
    def test_force_efficient_same_energy(self, mock_dpe):
        """Test forcing more efficient move of same energy cost."""
        # Setup moves with same energy cost
        move_1 = Mock(spec=ChargedMove)
        move_1.move_id = "move_1"
        move_1.energy_cost = 50
        move_1.self_debuffing = False
        
        move_2 = Mock(spec=ChargedMove)
        move_2.move_id = "move_2"
        move_2.energy_cost = 50
        
        # Move 1 is more efficient
        mock_dpe.side_effect = lambda poke, opp, move: 2.2 if move == move_1 else 1.8
        
        result = ActionLogic._force_efficient_same_energy_move(
            self.poke, self.opponent, move_2, [move_1], self.battle
        )
        
        assert result == move_1
    
    @patch.object(ActionLogic, 'calculate_move_dpe')
    def test_force_efficient_similar_energy_debuff_avoidance(self, mock_dpe):
        """Test forcing efficient move of similar energy to avoid debuffs."""
        # Setup debuffing move and similar energy alternative
        debuff_move = Mock(spec=ChargedMove)
        debuff_move.move_id = "superpower"
        debuff_move.energy_cost = 55
        debuff_move.self_debuffing = True
        
        alternative = Mock(spec=ChargedMove)
        alternative.move_id = "close_combat"
        alternative.energy_cost = 50  # Within 10 energy (55 - 10 = 45, 50 > 45)
        alternative.self_debuffing = False
        
        # Alternative is more efficient
        mock_dpe.side_effect = lambda poke, opp, move: 2.0 if move == alternative else 1.8
        
        result = ActionLogic._force_efficient_similar_energy_move(
            self.poke, self.opponent, debuff_move, [alternative], self.battle
        )
        
        assert result == alternative


if __name__ == '__main__':
    pytest.main([__file__])
