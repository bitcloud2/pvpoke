#!/usr/bin/env python3
"""
Simple battle example demonstrating basic PvPoke Python usage.
"""

import sys
from pathlib import Path

# Add parent directory to path to import pvpoke
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core import GameMaster, Pokemon
from pvpoke.battle import Battle, DamageCalculator


def main():
    """Run a simple battle between two Pokemon."""
    
    print("PvPoke Python - Simple Battle Example")
    print("=" * 50)
    
    # Initialize GameMaster
    print("\nLoading game data...")
    gm = GameMaster()
    
    # Get two Pokemon for battle
    # Let's use Azumarill vs Galarian Stunfisk (common Great League matchup)
    azumarill = gm.get_pokemon("azumarill")
    stunfisk = gm.get_pokemon("stunfisk_galarian")
    
    if not azumarill or not stunfisk:
        print("Error: Could not load Pokemon data")
        return
    
    # Set up Pokemon for Great League
    print("\nSetting up Pokemon for Great League (1500 CP)...")
    
    # Optimize IVs for Great League
    azumarill.optimize_for_league(1500)
    stunfisk.optimize_for_league(1500)
    
    # Set moves (using common movesets)
    azumarill.fast_move = gm.get_fast_move("BUBBLE")
    azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
    azumarill.charged_move_2 = gm.get_charged_move("PLAY_ROUGH")
    
    stunfisk.fast_move = gm.get_fast_move("MUD_SHOT")
    stunfisk.charged_move_1 = gm.get_charged_move("ROCK_SLIDE")
    stunfisk.charged_move_2 = gm.get_charged_move("EARTHQUAKE")
    
    # Display Pokemon info
    print(f"\n{azumarill.species_name}")
    print(f"  CP: {azumarill.cp}")
    print(f"  Level: {azumarill.level}")
    print(f"  IVs: {azumarill.ivs.atk}/{azumarill.ivs.defense}/{azumarill.ivs.hp}")
    stats = azumarill.calculate_stats()
    print(f"  Stats: {stats.atk:.1f} ATK / {stats.defense:.1f} DEF / {stats.hp} HP")
    print(f"  Moves: {azumarill.fast_move.name}, {azumarill.charged_move_1.name}, {azumarill.charged_move_2.name}")
    
    print(f"\n{stunfisk.species_name}")
    print(f"  CP: {stunfisk.cp}")
    print(f"  Level: {stunfisk.level}")
    print(f"  IVs: {stunfisk.ivs.atk}/{stunfisk.ivs.defense}/{stunfisk.ivs.hp}")
    stats = stunfisk.calculate_stats()
    print(f"  Stats: {stats.atk:.1f} ATK / {stats.defense:.1f} DEF / {stats.hp} HP")
    print(f"  Moves: {stunfisk.fast_move.name}, {stunfisk.charged_move_1.name}, {stunfisk.charged_move_2.name}")
    
    # Create battle
    print("\n" + "=" * 50)
    print("Starting battle simulation...")
    print("=" * 50)
    
    battle = Battle(azumarill, stunfisk)
    
    # Run simulation
    result = battle.simulate(log_timeline=True)
    
    # Display results
    print(f"\nBattle Result:")
    print(f"  Winner: {azumarill.species_name if result.winner == 0 else stunfisk.species_name}")
    print(f"  Duration: {result.turns} turns ({result.turns * 0.5} seconds)")
    print(f"\nFinal HP:")
    print(f"  {azumarill.species_name}: {result.pokemon1_hp}/{azumarill.hp} HP")
    print(f"  {stunfisk.species_name}: {result.pokemon2_hp}/{stunfisk.hp} HP")
    print(f"\nBattle Ratings:")
    print(f"  {azumarill.species_name}: {result.rating1}")
    print(f"  {stunfisk.species_name}: {result.rating2}")
    
    # Show sample timeline events
    if result.timeline:
        print(f"\nSample Timeline (first 10 actions):")
        for event in result.timeline[:10]:
            attacker_name = azumarill.species_name if event["attacker"] == 0 else stunfisk.species_name
            print(f"  Turn {event['turn']}: {attacker_name} uses {event['move']} "
                  f"(damage: {event.get('damage', 0)})")


if __name__ == "__main__":
    main()
