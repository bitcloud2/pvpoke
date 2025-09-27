#!/usr/bin/env python3
"""
Great League rankings example - shows top Pokemon and their stats.
"""

import sys
from pathlib import Path

# Add parent directory to path to import pvpoke
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core import GameMaster
from pvpoke.utils import DataLoader, CPCalculator


def main():
    """Display Great League rankings and analyze top Pokemon."""
    
    print("PvPoke Python - Great League Rankings")
    print("=" * 50)
    
    # Initialize data loader
    loader = DataLoader()
    gm = GameMaster()
    
    # Load Great League rankings
    print("\nLoading Great League rankings...")
    rankings = loader.get_great_league_meta(top_n=30)
    
    if not rankings:
        print("Error: Could not load rankings data")
        print("Make sure the rankings data exists in src/data/rankings/")
        return
    
    print(f"Found {len(rankings)} top Pokemon")
    
    # Display top 10
    print("\nTop 10 Great League Pokemon:")
    print("-" * 50)
    print(f"{'Rank':<6} {'Pokemon':<25} {'Score':<8} {'Type'}")
    print("-" * 50)
    
    for i, entry in enumerate(rankings[:10], 1):
        pokemon = gm.get_pokemon(entry['speciesId'])
        if pokemon:
            type_str = "/".join([t for t in pokemon.types if t])
            print(f"{i:<6} {entry['speciesName']:<25} {entry.get('score', 0):<8.1f} {type_str}")
    
    print("\n" + "=" * 50)
    print("Detailed Analysis of Top 3:")
    print("=" * 50)
    
    # Analyze top 3 in detail
    for i, entry in enumerate(rankings[:3], 1):
        pokemon = gm.get_pokemon(entry['speciesId'])
        if not pokemon:
            continue
        
        print(f"\n#{i}: {entry['speciesName']}")
        print("-" * 30)
        
        # Optimize for Great League
        pokemon.optimize_for_league(1500)
        
        # Display stats
        stats = pokemon.calculate_stats()
        print(f"  Optimal CP: {pokemon.cp}")
        print(f"  Optimal Level: {pokemon.level}")
        print(f"  Optimal IVs: {pokemon.ivs.atk}/{pokemon.ivs.defense}/{pokemon.ivs.hp}")
        print(f"  Stats: {stats.atk:.1f} ATK / {stats.defense:.1f} DEF / {stats.hp} HP")
        print(f"  Stat Product: {int(stats.atk * stats.defense * stats.hp)}")
        
        # Show recommended moves from rankings
        if 'moveset' in entry:
            print(f"  Recommended Moveset:")
            for move_id in entry['moveset']:
                move = gm.get_fast_move(move_id) or gm.get_charged_move(move_id)
                if move:
                    print(f"    - {move.name}")
        
        # Show key matchups
        if 'counters' in entry and entry['counters']:
            print(f"  Loses to:")
            for counter in entry['counters'][:3]:
                print(f"    - {counter['opponent']} ({counter['rating']} rating)")
        
        if 'matchups' in entry and entry['matchups']:
            print(f"  Beats:")
            for matchup in entry['matchups'][:3]:
                print(f"    - {matchup['opponent']} ({matchup['rating']} rating)")
    
    # Show type distribution
    print("\n" + "=" * 50)
    print("Type Distribution in Top 30:")
    print("=" * 50)
    
    type_counts = {}
    for entry in rankings[:30]:
        pokemon = gm.get_pokemon(entry['speciesId'])
        if pokemon:
            for ptype in pokemon.types:
                if ptype:
                    type_counts[ptype] = type_counts.get(ptype, 0) + 1
    
    # Sort by count
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    
    for ptype, count in sorted_types[:10]:
        bar = "█" * count
        print(f"  {ptype:<10} {bar} {count}")
    
    # IV spread recommendations
    print("\n" + "=" * 50)
    print("IV Optimization Example - Azumarill:")
    print("=" * 50)
    
    azumarill = gm.get_pokemon("azumarill")
    if azumarill:
        recommendations = CPCalculator.recommend_great_league_ivs(azumarill.base_stats)
        
        print(f"Top 5 IV spreads for {azumarill.species_name}:")
        print(f"{'Rank':<6} {'IVs':<12} {'Level':<8} {'CP':<6} {'%'}")
        print("-" * 40)
        
        for rec in recommendations[:5]:
            print(f"{rec['rank']:<6} {rec['ivs']:<12} {rec['level']:<8} "
                  f"{rec['cp']:<6} {rec['percentage']}")


if __name__ == "__main__":
    main()
