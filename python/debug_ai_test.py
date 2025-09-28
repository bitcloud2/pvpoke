#!/usr/bin/env python3
"""Debug script to test AI decision making."""

from unittest.mock import Mock, patch
from pvpoke.battle.ai import ActionLogic
from pvpoke.core.pokemon import Pokemon
from pvpoke.core.moves import FastMove, ChargedMove


def create_simple_test():
    """Create a simple test scenario."""
    # Create mock moves
    fast_move = Mock(spec=FastMove)
    fast_move.energy_gain = 3
    fast_move.turns = 1
    fast_move.damage = 5
    fast_move.cooldown = 500
    
    charged_move_1 = Mock(spec=ChargedMove)
    charged_move_1.energy_cost = 35
    charged_move_1.move_id = "test_move_1"
    
    # Create mock stats
    stats = Mock()
    stats.atk = 150
    
    # Create mock Pokemon
    pokemon = Mock(spec=Pokemon)
    pokemon.energy = 50  # Enough for charged move
    pokemon.current_hp = 100
    pokemon.shields = 2
    pokemon.fast_move = fast_move
    pokemon.charged_move_1 = charged_move_1
    pokemon.charged_move_2 = None  # Only one charged move
    pokemon.index = 0
    pokemon.stats = stats
    
    # Set attributes that should be False/None
    del pokemon.farm_energy  # Remove the mock attribute
    del pokemon.bait_shields  # Remove the mock attribute
    
    # Create opponent
    opp_fast_move = Mock(spec=FastMove)
    opp_fast_move.energy_gain = 4
    opp_fast_move.turns = 2
    opp_fast_move.damage = 8
    opp_fast_move.cooldown = 1000
    
    opp_stats = Mock()
    opp_stats.atk = 140
    
    opponent = Mock(spec=Pokemon)
    opponent.current_hp = 30  # Low health
    opponent.shields = 0  # No shields
    opponent.fast_move = opp_fast_move
    opponent.stats = opp_stats
    opponent.energy = 20
    opponent.charged_move_1 = None
    opponent.charged_move_2 = None
    
    # Remove mock attributes that should not exist or be 0
    del opponent.cooldown  # This should not exist or be 0
    
    # Create battle
    battle = Mock()
    battle.current_turn = 5
    battle.log_decision = Mock()
    
    return pokemon, opponent, battle


def main():
    """Run the debug test."""
    pokemon, opponent, battle = create_simple_test()
    
    print(f"Pokemon energy: {pokemon.energy}")
    print(f"Charged move cost: {pokemon.charged_move_1.energy_cost}")
    print(f"Opponent HP: {opponent.current_hp}")
    print(f"Opponent shields: {opponent.shields}")
    
    with patch('pvpoke.battle.ai.DamageCalculator') as mock_calc:
        def damage_side_effect(attacker, defender, move):
            if move == pokemon.charged_move_1:
                print(f"Charged move damage: 40")
                return 40
            else:
                print(f"Fast move damage: 5")
                return 5
        
        mock_calc.calculate_damage.side_effect = damage_side_effect
        
        print(f"Fast move damage check: {opponent.current_hp} > {pokemon.fast_move.damage}")
        print(f"Farm energy: {getattr(pokemon, 'farm_energy', False)}")
        print(f"Bait shields: {getattr(pokemon, 'bait_shields', False)}")
        
        result = ActionLogic.decide_action(battle, pokemon, opponent)
        
        print(f"Result: {result}")
        if result:
            print(f"Action type: {result.action_type}")
            print(f"Move index: {result.value}")
        
        # Check what the battle log captured
        if battle.log_decision.called:
            print("Log calls:")
            for call in battle.log_decision.call_args_list:
                print(f"  {call}")


if __name__ == "__main__":
    main()
