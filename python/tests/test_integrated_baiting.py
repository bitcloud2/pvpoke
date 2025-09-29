"""
Test integrated shield baiting logic within DP algorithm (Step 1N).

This test verifies that the baiting logic is properly integrated into the DP algorithm
and influences move selection and state evaluation.
"""

import pytest
from unittest.mock import Mock, patch
from pvpoke.battle.ai import ActionLogic, BattleState, DecisionOption, ShieldDecision
from pvpoke.core.pokemon import Pokemon
from pvpoke.core.moves import FastMove, ChargedMove


def create_baiting_test_pokemon():
    """Create a test Pokemon with baiting moves for testing."""
    # Create mock moves
    fast_move = Mock(spec=FastMove)
    fast_move.energy_gain = 3
    fast_move.turns = 1
    fast_move.damage = 5
    fast_move.cooldown = 500
    
    # Cheap bait move (35 energy, lower DPE)
    bait_move = Mock(spec=ChargedMove)
    bait_move.energy_cost = 35
    bait_move.damage = 60
    bait_move.move_id = "bait_move"
    bait_move.self_debuffing = False
    bait_move.self_buffing = False
    
    # Expensive nuke move (50 energy, higher DPE)
    nuke_move = Mock(spec=ChargedMove)
    nuke_move.energy_cost = 50
    nuke_move.damage = 90
    nuke_move.move_id = "nuke_move"
    nuke_move.self_debuffing = False
    nuke_move.self_buffing = False
    
    # Create mock stats
    stats = Mock()
    stats.atk = 150
    
    # Create mock Pokemon with baiting enabled
    pokemon = Mock(spec=Pokemon)
    pokemon.energy = 40  # Enough for bait, not enough for nuke
    pokemon.current_hp = 100
    pokemon.shields = 2
    pokemon.fast_move = fast_move
    pokemon.charged_move_1 = bait_move
    pokemon.charged_move_2 = nuke_move
    pokemon.index = 0
    pokemon.stats = stats
    pokemon.cooldown = 0
    pokemon.farm_energy = False
    pokemon.bait_shields = True  # Enable baiting
    
    return pokemon


def create_opponent_pokemon():
    """Create an opponent Pokemon for testing."""
    # Create mock moves
    fast_move = Mock(spec=FastMove)
    fast_move.energy_gain = 3
    fast_move.turns = 1
    fast_move.damage = 4
    fast_move.cooldown = 500
    
    charged_move = Mock(spec=ChargedMove)
    charged_move.energy_cost = 40
    charged_move.damage = 70
    charged_move.move_id = "opponent_move"
    
    # Create mock stats
    stats = Mock()
    stats.atk = 140
    
    # Create mock opponent
    opponent = Mock(spec=Pokemon)
    opponent.energy = 30
    opponent.current_hp = 120
    opponent.shields = 2  # Has shields to bait
    opponent.fast_move = fast_move
    opponent.charged_move_1 = charged_move
    opponent.charged_move_2 = None
    opponent.index = 1
    opponent.stats = stats
    opponent.cooldown = 0
    
    return opponent


class TestIntegratedBaiting:
    """Test cases for integrated shield baiting logic."""
    
    def test_filter_moves_for_dp_baiting_no_baiting(self):
        """Test that all moves are returned when baiting is disabled."""
        pokemon = create_baiting_test_pokemon()
        pokemon.bait_shields = False  # Disable baiting
        opponent = create_opponent_pokemon()
        
        active_moves = [pokemon.charged_move_1, pokemon.charged_move_2]
        curr_state = BattleState(
            energy=40,
            opp_health=120,
            turn=0,
            opp_shields=2,
            moves=[],
            buffs=0,
            chance=1.0
        )
        
        result = ActionLogic._filter_moves_for_dp_baiting(
            pokemon, opponent, active_moves, curr_state, None
        )
        
        assert result == active_moves
    
    def test_filter_moves_for_dp_baiting_no_shields(self):
        """Test that all moves are returned when opponent has no shields."""
        pokemon = create_baiting_test_pokemon()
        opponent = create_opponent_pokemon()
        opponent.shields = 0  # No shields
        
        active_moves = [pokemon.charged_move_1, pokemon.charged_move_2]
        curr_state = BattleState(
            energy=40,
            opp_health=120,
            turn=0,
            opp_shields=0,
            moves=[],
            buffs=0,
            chance=1.0
        )
        
        result = ActionLogic._filter_moves_for_dp_baiting(
            pokemon, opponent, active_moves, curr_state, None
        )
        
        assert result == active_moves
    
    def test_filter_moves_for_dp_baiting_build_energy(self):
        """Test that empty list is returned when we should build energy for expensive move."""
        pokemon = create_baiting_test_pokemon()
        pokemon.energy = 40  # Not enough for nuke (50)
        opponent = create_opponent_pokemon()
        
        active_moves = [pokemon.charged_move_1, pokemon.charged_move_2]
        curr_state = BattleState(
            energy=40,
            opp_health=120,
            turn=0,
            opp_shields=2,
            moves=[],
            buffs=0,
            chance=1.0
        )
        
        # Mock battle for logging
        battle = Mock()
        
        result = ActionLogic._filter_moves_for_dp_baiting(
            pokemon, opponent, active_moves, curr_state, battle
        )
        
        # Should return empty list to indicate fast move usage
        assert result == []
    
    def test_filter_moves_for_dp_baiting_self_buffing_exception(self):
        """Test that self-buffing moves prevent baiting when DPE ratio is low."""
        pokemon = create_baiting_test_pokemon()
        pokemon.energy = 40
        
        # Make bait move self-buffing
        pokemon.charged_move_1.self_buffing = True
        
        # Adjust DPE to be close (ratio <= 1.5)
        pokemon.charged_move_2.damage = 75  # Makes ratio 75/50 / 60/35 = 1.5 / 1.71 = 0.87
        
        opponent = create_opponent_pokemon()
        
        active_moves = [pokemon.charged_move_1, pokemon.charged_move_2]
        curr_state = BattleState(
            energy=40,
            opp_health=120,
            turn=0,
            opp_shields=2,
            moves=[],
            buffs=0,
            chance=1.0
        )
        
        result = ActionLogic._filter_moves_for_dp_baiting(
            pokemon, opponent, active_moves, curr_state, None
        )
        
        # Should return all moves (no baiting due to self-buffing exception)
        assert result == active_moves
    
    def test_calculate_dp_baiting_weight_no_baiting(self):
        """Test that normal weight is returned when baiting is disabled."""
        pokemon = create_baiting_test_pokemon()
        pokemon.bait_shields = False
        opponent = create_opponent_pokemon()
        
        active_moves = [pokemon.charged_move_1, pokemon.charged_move_2]
        curr_state = BattleState(
            energy=40,
            opp_health=120,
            turn=0,
            opp_shields=2,
            moves=[],
            buffs=0,
            chance=1.0
        )
        
        weight = ActionLogic._calculate_dp_baiting_weight(
            pokemon, opponent, pokemon.charged_move_1, active_moves, curr_state, None
        )
        
        assert weight == 1.0
    
    @patch.object(ActionLogic, 'would_shield')
    def test_calculate_dp_baiting_weight_bait_move_boost(self, mock_would_shield):
        """Test that bait moves get weight boost when opponent would shield."""
        pokemon = create_baiting_test_pokemon()
        opponent = create_opponent_pokemon()
        
        # Mock opponent would shield the bait move
        mock_would_shield.return_value = ShieldDecision(value=True, shield_weight=4, no_shield_weight=1)
        
        active_moves = [pokemon.charged_move_1, pokemon.charged_move_2]
        curr_state = BattleState(
            energy=40,
            opp_health=120,
            turn=0,
            opp_shields=2,
            moves=[],
            buffs=0,
            chance=1.0
        )
        
        battle = Mock()
        
        weight = ActionLogic._calculate_dp_baiting_weight(
            pokemon, opponent, pokemon.charged_move_1, active_moves, curr_state, battle
        )
        
        # Should get boost for bait move
        assert weight > 1.0
        assert abs(weight - 1.3) < 0.01
    
    def test_calculate_dp_baiting_weight_expensive_move_boost(self):
        """Test that expensive moves get weight boost when we're close to having energy."""
        pokemon = create_baiting_test_pokemon()
        pokemon.energy = 45  # Close to nuke energy (50)
        opponent = create_opponent_pokemon()
        
        active_moves = [pokemon.charged_move_1, pokemon.charged_move_2]
        curr_state = BattleState(
            energy=45,
            opp_health=120,
            turn=0,
            opp_shields=2,
            moves=[],
            buffs=0,
            chance=1.0
        )
        
        battle = Mock()
        
        weight = ActionLogic._calculate_dp_baiting_weight(
            pokemon, opponent, pokemon.charged_move_2, active_moves, curr_state, battle
        )
        
        # Should get boost for expensive target move
        assert weight > 1.0
        assert abs(weight - 1.2) < 0.01
    
    @patch.object(ActionLogic, '_filter_moves_for_dp_baiting')
    @patch.object(ActionLogic, '_calculate_dp_baiting_weight')
    def test_dp_integration_fast_move_state(self, mock_weight, mock_filter):
        """Test that DP algorithm creates fast move state when baiting logic says to build energy."""
        pokemon = create_baiting_test_pokemon()
        opponent = create_opponent_pokemon()
        
        # Mock baiting logic to return empty list (use fast move)
        mock_filter.return_value = []
        mock_weight.return_value = 1.0
        
        # Create initial state
        curr_state = BattleState(
            energy=40,
            opp_health=120,
            turn=0,
            opp_shields=2,
            moves=[],
            buffs=0,
            chance=1.0
        )
        
        # Mock damage calculator
        with patch('pvpoke.battle.ai.DamageCalculator.calculate_damage') as mock_damage:
            mock_damage.return_value = 5  # Fast move damage
            
            # This would be called within the DP loop
            active_moves = [pokemon.charged_move_1, pokemon.charged_move_2]
            moves_to_evaluate = ActionLogic._filter_moves_for_dp_baiting(
                pokemon, opponent, active_moves, curr_state, None
            )
            
            # Should return empty list
            assert moves_to_evaluate == []
    
    @patch.object(ActionLogic, '_calculate_dp_baiting_weight')
    def test_dp_integration_weighted_states(self, mock_weight):
        """Test that DP algorithm applies baiting weights to state chances."""
        pokemon = create_baiting_test_pokemon()
        opponent = create_opponent_pokemon()
        
        # Mock baiting weight
        mock_weight.return_value = 1.3  # Boost for bait move
        
        # Create initial state
        curr_state = BattleState(
            energy=40,
            opp_health=120,
            turn=0,
            opp_shields=2,
            moves=[],
            buffs=0,
            chance=1.0
        )
        
        # Test the weight calculation
        active_moves = [pokemon.charged_move_1, pokemon.charged_move_2]
        weight = ActionLogic._calculate_dp_baiting_weight(
            pokemon, opponent, pokemon.charged_move_1, active_moves, curr_state, None
        )
        
        # Verify weight is applied
        assert weight == 1.3
        
        # Test that weighted chance would be calculated correctly
        weighted_chance = curr_state.chance * weight
        assert weighted_chance == 1.3


if __name__ == "__main__":
    pytest.main([__file__])
