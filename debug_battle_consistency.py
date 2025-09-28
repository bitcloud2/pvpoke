#!/usr/bin/env python3
"""
Debug script to understand what's causing non-deterministic battle behavior.
"""

import sys
from pathlib import Path

# Add python directory to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from pvpoke.core import GameMaster
from pvpoke.battle import Battle


def debug_battle_consistency():
    """Debug battle consistency with detailed logging."""
    
    print("🔍 DEBUG: Battle Consistency Analysis")
    print("=" * 60)
    
    gm = GameMaster()
    
    # Set up the same matchup as in the validation
    azumarill = gm.get_pokemon("azumarill")
    stunfisk = gm.get_pokemon("stunfisk_galarian")
    
    if not azumarill or not stunfisk:
        print("❌ Could not load Pokemon")
        return False
    
    # Configure Pokemon exactly like in validation
    azumarill.optimize_for_league(1500)
    stunfisk.optimize_for_league(1500)
    
    azumarill.fast_move = gm.get_fast_move("BUBBLE")
    azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
    
    stunfisk.fast_move = gm.get_fast_move("MUD_SHOT")
    stunfisk.charged_move_1 = gm.get_charged_move("ROCK_SLIDE")
    
    print(f"Testing: {azumarill.species_name} vs {stunfisk.species_name}")
    print(f"Azumarill: CP={azumarill.cp}, HP={azumarill.hp}")
    print(f"Stunfisk: CP={stunfisk.cp}, HP={stunfisk.hp}")
    print()
    
    # Run multiple battles with detailed logging
    results = []
    for i in range(3):  # Just 3 battles for detailed analysis
        print(f"🔄 BATTLE {i+1}")
        print("-" * 40)
        
        # Log initial state
        print(f"Initial state:")
        print(f"  Azumarill: HP={azumarill.current_hp}, Energy={azumarill.energy}, Buffs={azumarill.stat_buffs}")
        print(f"  Stunfisk: HP={stunfisk.current_hp}, Energy={stunfisk.energy}, Buffs={stunfisk.stat_buffs}")
        
        # Check move buff meters
        if hasattr(azumarill.charged_move_1, 'buff_apply_meter'):
            print(f"  Azumarill Ice Beam buff_apply_meter: {azumarill.charged_move_1.buff_apply_meter}")
        if hasattr(stunfisk.charged_move_1, 'buff_apply_meter'):
            print(f"  Stunfisk Rock Slide buff_apply_meter: {stunfisk.charged_move_1.buff_apply_meter}")
        
        battle = Battle(azumarill, stunfisk)
        
        # Add detailed logging to battle
        battle.debug_mode = True
        
        result = battle.simulate(log_timeline=True)
        results.append(result)
        
        print(f"Result: Winner={result.winner}, Rating={result.rating1}, Turns={result.turns}")
        print(f"Final HP: Azumarill={result.pokemon1_hp}, Stunfisk={result.pokemon2_hp}")
        
        # Log final move buff meters
        if hasattr(azumarill.charged_move_1, 'buff_apply_meter'):
            print(f"Final Azumarill Ice Beam buff_apply_meter: {azumarill.charged_move_1.buff_apply_meter}")
        if hasattr(stunfisk.charged_move_1, 'buff_apply_meter'):
            print(f"Final Stunfisk Rock Slide buff_apply_meter: {stunfisk.charged_move_1.buff_apply_meter}")
        
        # Show first few timeline events
        if result.timeline:
            print("First 5 timeline events:")
            for j, event in enumerate(result.timeline[:5]):
                print(f"  {j+1}. Turn {event['turn']}: {event}")
        
        print()
    
    # Analyze results
    print("📊 ANALYSIS")
    print("=" * 40)
    
    winners = [r.winner for r in results]
    ratings = [r.rating1 for r in results]
    turns = [r.turns for r in results]
    
    print(f"Winners: {winners}")
    print(f"Ratings: {ratings}")
    print(f"Turns: {turns}")
    
    # Check for differences
    if len(set(winners)) > 1:
        print("❌ INCONSISTENT WINNERS")
    if len(set(ratings)) > 1:
        print(f"❌ INCONSISTENT RATINGS - Range: {max(ratings) - min(ratings)}")
    if len(set(turns)) > 1:
        print(f"❌ INCONSISTENT TURNS - Range: {max(turns) - min(turns)}")
    
    return len(set(winners)) == 1 and len(set(ratings)) == 1 and len(set(turns)) == 1


if __name__ == "__main__":
    debug_battle_consistency()
