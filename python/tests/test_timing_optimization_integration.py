"""
Test Move Timing Optimization Integration (Step 2C).

This test verifies that the battle context methods and timing optimization
integration work correctly with the ActionLogic system.
"""

import pytest
from unittest.mock import Mock, patch
from pvpoke.battle.ai import ActionLogic, TimelineAction
from pvpoke.battle.battle import Battle
from pvpoke.core.pokemon import Pokemon
from pvpoke.core.moves import FastMove, ChargedMove


def create_test_pokemon(energy=50, hp=100, cooldown=0, optimize_timing=True):
    """Create a test Pokemon with configurable properties."""
    # Create mock moves
    fast_move = Mock(spec=FastMove)
    fast_move.energy_gain = 3
    fast_move.turns = 1
    fast_move.damage = 5
    fast_move.cooldown = 500
    
    charged_move_1 = Mock(spec=ChargedMove)
    charged_move_1.energy_cost = 35
    charged_move_1.move_id = "test_move_1"
    charged_move_1.self_debuffing = False
    
    charged_move_2 = Mock(spec=ChargedMove)
    charged_move_2.energy_cost = 50
    charged_move_2.move_id = "test_move_2"
    charged_move_2.self_debuffing = False
    
    # Create mock stats
    stats = Mock()
    stats.atk = 150
    
    # Create mock Pokemon
    pokemon = Mock(spec=Pokemon)
    pokemon.energy = energy
    pokemon.current_hp = hp
    pokemon.shields = 2
    pokemon.fast_move = fast_move
    pokemon.charged_move_1 = charged_move_1
    pokemon.charged_move_2 = charged_move_2
    pokemon.index = 0
    pokemon.stats = stats
    pokemon.cooldown = cooldown
    pokemon.farm_energy = False
    pokemon.optimize_move_timing = optimize_timing
    pokemon.species_id = "test_pokemon"
    
    return pokemon


def create_opponent_pokemon(cooldown=0, hp=100):
    """Create an opponent Pokemon with configurable properties."""
    # Create mock moves
    fast_move = Mock(spec=FastMove)
    fast_move.energy_gain = 4
    fast_move.turns = 2
    fast_move.damage = 8
    fast_move.cooldown = 1000
    
    charged_move_1 = Mock(spec=ChargedMove)
    charged_move_1.energy_cost = 40
    charged_move_1.move_id = "opp_move_1"
    
    # Create mock stats
    stats = Mock()
    stats.atk = 140
    
    # Create mock Pokemon
    pokemon = Mock(spec=Pokemon)
    pokemon.energy = 20
    pokemon.current_hp = hp
    pokemon.shields = 1
    pokemon.fast_move = fast_move
    pokemon.charged_move_1 = charged_move_1
    pokemon.charged_move_2 = None
    pokemon.index = 1
    pokemon.stats = stats
    pokemon.cooldown = cooldown
    pokemon.species_id = "opponent_pokemon"
    
    return pokemon


class TestBattleContextMethods:
    """Test the battle context methods added in Step 2C."""
    
    def test_get_queued_actions_empty(self):
        """Test get_queued_actions returns empty list initially."""
        battle = Battle()
        actions = battle.get_queued_actions()
        assert actions == []
        assert isinstance(actions, list)
    
    def test_get_queued_actions_with_actions(self):
        """Test get_queued_actions returns queued actions."""
        battle = Battle()
        
        # Add some mock actions
        action1 = Mock()
        action1.actor = 0
        action1.type = "fast"
        
        action2 = Mock()
        action2.actor = 1
        action2.type = "charged"
        
        battle.queued_actions = [action1, action2]
        
        actions = battle.get_queued_actions()
        assert len(actions) == 2
        assert actions[0] == action1
        assert actions[1] == action2
    
    def test_log_decision_debug_off(self):
        """Test log_decision does nothing when debug is off."""
        battle = Battle()
        battle.debug_mode = False
        pokemon = create_test_pokemon()
        
        # Should not raise any exceptions
        battle.log_decision(pokemon, "test message")
    
    def test_log_decision_debug_on(self, capsys):
        """Test log_decision prints when debug is on."""
        battle = Battle()
        battle.debug_mode = True
        battle.current_turn = 5
        pokemon = create_test_pokemon()
        
        battle.log_decision(pokemon, "test message")
        
        captured = capsys.readouterr()
        assert "Turn 5: test_pokemon test message" in captured.out
    
    def test_get_mode(self):
        """Test get_mode returns simulate."""
        battle = Battle()
        assert battle.get_mode() == "simulate"


class TestTimingOptimizationIntegration:
    """Test the timing optimization integration with ActionLogic."""
    
    @patch('pvpoke.battle.ai.DamageCalculator.calculate_damage')
    def test_optimize_move_timing_disabled(self, mock_damage):
        """Test timing optimization when disabled on Pokemon."""
        mock_damage.return_value = 10
        
        battle = Battle()
        poke = create_test_pokemon(optimize_timing=False)
        opponent = create_opponent_pokemon()
        
        result = ActionLogic.optimize_move_timing(battle, poke, opponent, 10)
        assert result is False
    
    @patch('pvpoke.battle.ai.DamageCalculator.calculate_damage')
    def test_optimize_move_timing_same_cooldown(self, mock_damage):
        """Test timing optimization disabled for same cooldown moves."""
        mock_damage.return_value = 10
        
        battle = Battle()
        poke = create_test_pokemon()
        opponent = create_opponent_pokemon()
        
        # Set same cooldowns
        poke.fast_move.cooldown = 500
        opponent.fast_move.cooldown = 500
        
        result = ActionLogic.optimize_move_timing(battle, poke, opponent, 10)
        assert result is False
    
    @patch('pvpoke.battle.ai.DamageCalculator.calculate_damage')
    def test_optimize_move_timing_target_cooldown_calculation(self, mock_damage):
        """Test target cooldown calculation logic."""
        mock_damage.return_value = 10
        
        battle = Battle()
        poke = create_test_pokemon()
        opponent = create_opponent_pokemon()
        
        # Test default 500ms target
        poke.fast_move.cooldown = 500
        opponent.fast_move.cooldown = 1000
        target = ActionLogic.calculate_target_cooldown(poke, opponent)
        assert target == 500
        
        # Test 4+ turn moves use 1000ms target
        poke.fast_move.cooldown = 2000
        target = ActionLogic.calculate_target_cooldown(poke, opponent)
        assert target == 1000
        
        # Test 3-turn vs 5-turn matchup
        poke.fast_move.cooldown = 1500
        opponent.fast_move.cooldown = 2500
        target = ActionLogic.calculate_target_cooldown(poke, opponent)
        assert target == 1000
        
        # Test 2-turn vs 4-turn matchup
        poke.fast_move.cooldown = 1000
        opponent.fast_move.cooldown = 2000
        target = ActionLogic.calculate_target_cooldown(poke, opponent)
        assert target == 1000
    
    @patch('pvpoke.battle.ai.DamageCalculator.calculate_damage')
    def test_optimize_move_timing_survival_check(self, mock_damage):
        """Test survival condition checks."""
        mock_damage.return_value = 10
        
        battle = Battle()
        poke = create_test_pokemon(hp=5)  # Low HP
        opponent = create_opponent_pokemon()
        opponent.fast_move.damage = 10  # Would KO
        
        result = ActionLogic.check_survival_conditions(battle, poke, opponent)
        assert result is False
    
    @patch('pvpoke.battle.ai.DamageCalculator.calculate_damage')
    def test_optimize_move_timing_energy_check(self, mock_damage):
        """Test energy overflow prevention."""
        mock_damage.return_value = 10
        
        battle = Battle()
        poke = create_test_pokemon(energy=95)  # High energy
        opponent = create_opponent_pokemon()
        
        # Mock queued actions that would cause overflow
        mock_action = Mock()
        mock_action.actor = 0
        mock_action.type = "fast"
        battle.queued_actions = [mock_action, mock_action]  # 2 queued fast moves
        
        result = ActionLogic.check_energy_conditions(battle, poke)
        assert result is False  # Would exceed 100 energy
    
    @patch('pvpoke.battle.ai.DamageCalculator.calculate_damage')
    def test_optimize_move_timing_strategic_check(self, mock_damage):
        """Test strategic condition checks."""
        mock_damage.return_value = 50  # Lethal damage
        
        battle = Battle()
        poke = create_test_pokemon()
        opponent = create_opponent_pokemon(hp=40)  # Low HP opponent
        opponent.shields = 0  # No shields
        
        result = ActionLogic.check_strategic_conditions(battle, poke, opponent, 10)
        assert result is False  # Should not optimize when we can KO
    
    @patch('pvpoke.battle.ai.DamageCalculator.calculate_damage')
    def test_optimize_move_timing_full_integration(self, mock_damage):
        """Test full timing optimization integration."""
        mock_damage.return_value = 10
        
        battle = Battle()
        battle.debug_mode = True
        poke = create_test_pokemon()
        opponent = create_opponent_pokemon(cooldown=600)  # High cooldown
        
        # Should optimize timing
        result = ActionLogic.optimize_move_timing(battle, poke, opponent, 10)
        assert result is True
    
    @patch('pvpoke.battle.ai.DamageCalculator.calculate_damage')
    def test_decide_action_with_timing_optimization(self, mock_damage):
        """Test decide_action integrates timing optimization."""
        mock_damage.return_value = 10
        
        battle = Battle()
        battle.current_turn = 1
        poke = create_test_pokemon()
        opponent = create_opponent_pokemon(cooldown=600)  # High cooldown
        
        # Mock the timing optimization to return True
        with patch.object(ActionLogic, 'optimize_move_timing', return_value=True):
            action = ActionLogic.decide_action(battle, poke, opponent)
            # Should return None (fast move) due to timing optimization
            assert action is None
    
    @patch('pvpoke.battle.ai.DamageCalculator.calculate_damage')
    def test_decide_action_without_timing_optimization(self, mock_damage):
        """Test decide_action proceeds normally when timing optimization disabled."""
        mock_damage.return_value = 10
        
        battle = Battle()
        battle.current_turn = 1
        poke = create_test_pokemon(optimize_timing=False)
        opponent = create_opponent_pokemon()
        
        # Mock the timing optimization to return False
        with patch.object(ActionLogic, 'optimize_move_timing', return_value=False):
            action = ActionLogic.decide_action(battle, poke, opponent)
            # Should proceed with normal decision logic
            # (May return None for fast move or TimelineAction for charged move)
            # The exact result depends on the DP algorithm


class TestTimingOptimizationDisabling:
    """Test timing optimization disabling rules."""
    
    def test_should_disable_same_duration(self):
        """Test disabling for same duration moves."""
        poke = create_test_pokemon()
        opponent = create_opponent_pokemon()
        
        poke.fast_move.cooldown = 500
        opponent.fast_move.cooldown = 500
        
        result = ActionLogic.should_disable_timing_optimization(poke, opponent)
        assert result is True
    
    def test_should_disable_evenly_divisible(self):
        """Test disabling for evenly divisible longer moves."""
        poke = create_test_pokemon()
        opponent = create_opponent_pokemon()
        
        # 4-turn vs 2-turn (evenly divisible)
        poke.fast_move.cooldown = 2000
        opponent.fast_move.cooldown = 1000
        
        result = ActionLogic.should_disable_timing_optimization(poke, opponent)
        assert result is True
        
        # 3-turn vs 1-turn (evenly divisible)
        poke.fast_move.cooldown = 1500
        opponent.fast_move.cooldown = 500
        
        result = ActionLogic.should_disable_timing_optimization(poke, opponent)
        assert result is True
    
    def test_should_not_disable_non_divisible(self):
        """Test not disabling for non-evenly divisible moves."""
        poke = create_test_pokemon()
        opponent = create_opponent_pokemon()
        
        # 3-turn vs 2-turn (not evenly divisible)
        poke.fast_move.cooldown = 1500
        opponent.fast_move.cooldown = 1000
        
        result = ActionLogic.should_disable_timing_optimization(poke, opponent)
        assert result is False


class TestBattleIntegration:
    """Test integration with the Battle class."""
    
    def test_battle_has_required_methods(self):
        """Test Battle class has all required methods for timing optimization."""
        battle = Battle()
        
        # Check required methods exist
        assert hasattr(battle, 'get_queued_actions')
        assert hasattr(battle, 'log_decision')
        assert hasattr(battle, 'get_mode')
        assert hasattr(battle, 'queued_actions')
        
        # Check methods are callable
        assert callable(battle.get_queued_actions)
        assert callable(battle.log_decision)
        assert callable(battle.get_mode)
    
    def test_battle_queued_actions_initialization(self):
        """Test Battle initializes queued_actions properly."""
        battle = Battle()
        assert hasattr(battle, 'queued_actions')
        assert isinstance(battle.queued_actions, list)
        assert len(battle.queued_actions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
