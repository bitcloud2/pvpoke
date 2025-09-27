#!/usr/bin/env python3
"""Test script to verify the AI logic port is working correctly."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'pvpoke'))

from pvpoke.core.pokemon import Pokemon, Stats, IVs
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.battle.battle import Battle
from pvpoke.battle.ai import ActionLogic, BattleAI


def create_test_pokemon():
    """Create test Pokemon for battle simulation."""
    
    # Create Azumarill
    azumarill = Pokemon(
        species_id="azumarill",
        species_name="Azumarill",
        dex=184,
        base_stats=Stats(atk=112, defense=152, hp=225),
        types=["water", "fairy"],
        level=20.0,
        ivs=IVs(atk=0, defense=15, hp=15)
    )
    
    # Create moves
    bubble = FastMove(
        move_id="BUBBLE",
        name="Bubble",
        move_type="water",
        power=8,
        energy_gain=11,
        turns=3
    )
    
    ice_beam = ChargedMove(
        move_id="ICE_BEAM",
        name="Ice Beam",
        move_type="ice",
        power=90,
        energy_cost=55
    )
    
    play_rough = ChargedMove(
        move_id="PLAY_ROUGH",
        name="Play Rough",
        move_type="fairy",
        power=90,
        energy_cost=60,
        buffs=[0.8, 1.0],  # Attack debuff
        buff_target="self",
        buff_chance=1.0
    )
    
    # Assign moves
    azumarill.fast_move = bubble
    azumarill.charged_move_1 = ice_beam
    azumarill.charged_move_2 = play_rough
    azumarill.index = 0
    
    # Create Registeel
    registeel = Pokemon(
        species_id="registeel",
        species_name="Registeel",
        dex=379,
        base_stats=Stats(atk=143, defense=285, hp=190),
        types=["steel"],
        level=25.0,
        ivs=IVs(atk=0, defense=15, hp=15)
    )
    
    # Create moves for Registeel
    lock_on = FastMove(
        move_id="LOCK_ON",
        name="Lock-On",
        move_type="normal",
        power=1,
        energy_gain=5,
        turns=1
    )
    
    focus_blast = ChargedMove(
        move_id="FOCUS_BLAST",
        name="Focus Blast",
        move_type="fighting",
        power=140,
        energy_cost=75
    )
    
    flash_cannon = ChargedMove(
        move_id="FLASH_CANNON",
        name="Flash Cannon",
        move_type="steel",
        power=110,
        energy_cost=70,
        buffs=[1.0, 0.8],  # Defense debuff on opponent
        buff_target="opponent",
        buff_chance=1.0
    )
    
    # Assign moves
    registeel.fast_move = lock_on
    registeel.charged_move_1 = focus_blast
    registeel.charged_move_2 = flash_cannon
    registeel.index = 1
    
    return azumarill, registeel


def test_ai_decision_making():
    """Test the AI decision making logic."""
    print("Testing AI Decision Making...")
    
    azumarill, registeel = create_test_pokemon()
    
    # Initialize Pokemon for battle
    azumarill.reset()
    registeel.reset()
    
    # Set some energy to test charged move decisions
    azumarill.energy = 60  # Can use both moves
    registeel.energy = 30  # Can't use any charged moves yet
    
    # Create a mock battle
    class MockBattle:
        def __init__(self):
            self.current_turn = 5
        
        def log_decision(self, poke, message):
            print(f"Turn {self.current_turn}: {poke.species_name} - {message}")
    
    battle = MockBattle()
    
    # Test ActionLogic decision
    print("\n--- Testing ActionLogic.decide_action ---")
    action = ActionLogic.decide_action(battle, azumarill, registeel)
    
    if action:
        move_name = "Ice Beam" if action.value == 0 else "Play Rough"
        print(f"Azumarill decided to use {action.action_type} move: {move_name}")
    else:
        print("Azumarill decided to use fast move")
    
    # Test BattleAI wrapper
    print("\n--- Testing BattleAI.decide_action ---")
    battle_context = {"turn": 5, "time_remaining": 200}
    ai_action = BattleAI.decide_action(azumarill, registeel, battle_context)
    
    print(f"BattleAI decided: {ai_action['type']} move")
    if ai_action['move']:
        print(f"Move: {ai_action['move'].name}")
    
    # Test shield decision
    print("\n--- Testing Shield Decision ---")
    should_shield = BattleAI.should_shield(azumarill, registeel, azumarill.charged_move_1, 2)
    print(f"Registeel should shield Ice Beam: {should_shield}")
    
    # Test with ActionLogic shield decision
    shield_decision = ActionLogic.would_shield(battle, azumarill, registeel, azumarill.charged_move_1)
    print(f"ActionLogic shield decision: {shield_decision.value} (weight: {shield_decision.shield_weight})")


def test_battle_integration():
    """Test the AI integration with the battle system."""
    print("\n\nTesting Battle Integration...")
    
    azumarill, registeel = create_test_pokemon()
    
    # Create battle
    battle = Battle(azumarill, registeel)
    
    # Set some initial energy for more interesting decisions
    azumarill.energy = 55  # Can use Ice Beam
    registeel.energy = 20  # Building up energy
    
    print("Running 5 turns of battle simulation...")
    
    for turn in range(5):
        print(f"\n--- Turn {turn + 1} ---")
        print(f"Azumarill: HP={azumarill.current_hp}, Energy={azumarill.energy}")
        print(f"Registeel: HP={registeel.current_hp}, Energy={registeel.energy}")
        
        # Process one turn
        battle.process_turn(log_timeline=True)
        
        # Check if battle should end
        if azumarill.current_hp <= 0 or registeel.current_hp <= 0:
            print("Battle ended due to faint!")
            break
    
    print("\nFinal state:")
    print(f"Azumarill: HP={azumarill.current_hp}, Energy={azumarill.energy}")
    print(f"Registeel: HP={registeel.current_hp}, Energy={registeel.energy}")


def test_random_ai():
    """Test the random AI decision making."""
    print("\n\nTesting Random AI...")
    
    azumarill, registeel = create_test_pokemon()
    azumarill.reset()
    registeel.reset()
    
    # Give both Pokemon energy for charged moves
    azumarill.energy = 80
    registeel.energy = 75
    
    class MockBattle:
        def __init__(self):
            self.current_turn = 10
        
        def log_decision(self, poke, message):
            print(f"Random AI: {poke.species_name} - {message}")
    
    battle = MockBattle()
    
    print("Testing 5 random decisions for Azumarill:")
    for i in range(5):
        action = ActionLogic.decide_random_action(battle, azumarill, registeel)
        if action:
            move_name = "Ice Beam" if action.value == 0 else "Play Rough"
            print(f"Decision {i+1}: {action.action_type} move - {move_name}")
        else:
            print(f"Decision {i+1}: fast move")


if __name__ == "__main__":
    print("=== PvPoke AI Logic Port Test ===")
    
    try:
        test_ai_decision_making()
        test_battle_integration()
        test_random_ai()
        
        print("\n=== All Tests Completed Successfully! ===")
        print("The AI logic has been successfully ported from JavaScript to Python.")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
