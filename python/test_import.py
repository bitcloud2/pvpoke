#!/usr/bin/env python3
"""
Quick test script to verify the Python package is working.
"""

import sys
from pathlib import Path

# Add python directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing PvPoke Python imports...")
    print("-" * 40)
    
    try:
        # Test core imports
        print("✓ Importing core modules...")
        from pvpoke.core import Pokemon, Stats, IVs, GameMaster
        from pvpoke.core.moves import FastMove, ChargedMove, TypeEffectiveness
        
        # Test battle imports
        print("✓ Importing battle modules...")
        from pvpoke.battle import Battle, DamageCalculator, BattleAI
        
        # Test utils imports
        print("✓ Importing utility modules...")
        from pvpoke.utils import DataLoader, CPCalculator
        
        # Test rankings imports
        print("✓ Importing ranking modules...")
        from pvpoke.rankings import Ranker, TeamRanker
        
        print("\n✅ All imports successful!")
        
        # Try loading GameMaster
        print("\nTesting GameMaster data loading...")
        print("-" * 40)
        gm = GameMaster()
        
        # Test getting a Pokemon
        azumarill = gm.get_pokemon("azumarill")
        if azumarill:
            print(f"✓ Loaded Pokemon: {azumarill.species_name}")
            print(f"  Base stats: ATK={azumarill.base_stats.atk}, "
                  f"DEF={azumarill.base_stats.defense}, HP={azumarill.base_stats.hp}")
        
        # Test getting moves
        bubble = gm.get_fast_move("BUBBLE")
        if bubble:
            print(f"✓ Loaded Fast Move: {bubble.name} (Power: {bubble.power}, Energy: {bubble.energy_gain})")
        
        ice_beam = gm.get_charged_move("ICE_BEAM")
        if ice_beam:
            print(f"✓ Loaded Charged Move: {ice_beam.name} (Power: {ice_beam.power}, Cost: {ice_beam.energy_cost})")
        
        print("\n✅ Data loading successful!")
        
        # Test DataLoader
        print("\nTesting DataLoader...")
        print("-" * 40)
        loader = DataLoader()
        
        # Try loading rankings
        rankings = loader.get_great_league_meta(top_n=5)
        if rankings:
            print(f"✓ Loaded {len(rankings)} Great League rankings")
            print("\nTop 5 Great League Pokemon:")
            for i, entry in enumerate(rankings, 1):
                print(f"  {i}. {entry.get('speciesName', 'Unknown')}")
        
        print("\n" + "=" * 40)
        print("🎉 All tests passed successfully!")
        print("=" * 40)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
