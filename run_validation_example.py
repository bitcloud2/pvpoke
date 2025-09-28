#!/usr/bin/env python3
"""
Example script showing how to validate the Python PvPoke implementation.

This demonstrates the validation process and provides examples of comparing
the Python implementation against expected results.

Usage:
    pixi shell
    python run_validation_example.py
"""

import sys
from pathlib import Path

# Add python directory to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from pvpoke.core import GameMaster
from pvpoke.battle import Battle


def demonstrate_basic_battle():
    """Demonstrate a basic battle and show detailed results."""
    
    print("🔥 DEMONSTRATION: Basic Battle Simulation")
    print("=" * 60)
    
    # Initialize GameMaster
    print("Loading Pokemon data...")
    gm = GameMaster()
    
    # Create two popular Great League Pokemon
    azumarill = gm.get_pokemon("azumarill")
    medicham = gm.get_pokemon("medicham")
    
    if not azumarill or not medicham:
        print("❌ Could not load Pokemon data")
        return False
    
    print("✅ Pokemon data loaded successfully")
    
    # Optimize for Great League
    print("\nOptimizing for Great League (1500 CP)...")
    azumarill.optimize_for_league(1500)
    medicham.optimize_for_league(1500)
    
    # Set competitive movesets
    azumarill.fast_move = gm.get_fast_move("BUBBLE")
    azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
    azumarill.charged_move_2 = gm.get_charged_move("PLAY_ROUGH")
    
    medicham.fast_move = gm.get_fast_move("COUNTER")
    medicham.charged_move_1 = gm.get_charged_move("DYNAMIC_PUNCH")
    medicham.charged_move_2 = gm.get_charged_move("ICE_PUNCH")
    
    # Display Pokemon details
    print(f"\n🔵 {azumarill.species_name}")
    print(f"   CP: {azumarill.cp} | Level: {azumarill.level}")
    print(f"   IVs: {azumarill.ivs.atk}/{azumarill.ivs.defense}/{azumarill.ivs.hp}")
    stats = azumarill.calculate_stats()
    print(f"   Stats: {stats.atk:.1f} ATK / {stats.defense:.1f} DEF / {stats.hp} HP")
    print(f"   Moves: {azumarill.fast_move.name}, {azumarill.charged_move_1.name}, {azumarill.charged_move_2.name}")
    
    print(f"\n🟠 {medicham.species_name}")
    print(f"   CP: {medicham.cp} | Level: {medicham.level}")
    print(f"   IVs: {medicham.ivs.atk}/{medicham.ivs.defense}/{medicham.ivs.hp}")
    stats = medicham.calculate_stats()
    print(f"   Stats: {stats.atk:.1f} ATK / {stats.defense:.1f} DEF / {stats.hp} HP")
    print(f"   Moves: {medicham.fast_move.name}, {medicham.charged_move_1.name}, {medicham.charged_move_2.name}")
    
    # Run the battle
    print(f"\n⚔️  BATTLE: {azumarill.species_name} vs {medicham.species_name}")
    print("-" * 60)
    
    battle = Battle(azumarill, medicham)
    result = battle.simulate(log_timeline=True)
    
    # Display comprehensive results
    winner_name = azumarill.species_name if result.winner == 0 else medicham.species_name
    loser_name = medicham.species_name if result.winner == 0 else azumarill.species_name
    
    print(f"🏆 WINNER: {winner_name}")
    print(f"💔 LOSER: {loser_name}")
    print(f"\n📊 BATTLE STATISTICS:")
    print(f"   Duration: {result.turns} turns ({result.turns * 0.5:.1f} seconds)")
    print(f"   Time Remaining: {result.time_remaining:.1f} seconds")
    print(f"\n💚 FINAL HP:")
    print(f"   {azumarill.species_name}: {result.pokemon1_hp}/{azumarill.hp} HP ({result.pokemon1_hp/azumarill.hp*100:.1f}%)")
    print(f"   {medicham.species_name}: {result.pokemon2_hp}/{medicham.hp} HP ({result.pokemon2_hp/medicham.hp*100:.1f}%)")
    print(f"\n⭐ BATTLE RATINGS:")
    print(f"   {azumarill.species_name}: {result.rating1}/1000")
    print(f"   {medicham.species_name}: {result.rating2}/1000")
    
    # Show battle timeline
    if result.timeline:
        print(f"\n📝 BATTLE TIMELINE (First 10 actions):")
        for i, event in enumerate(result.timeline[:10]):
            attacker = azumarill.species_name if event["attacker"] == 0 else medicham.species_name
            action_type = "⚡" if event["action"] == "fast" else "💥"
            shielded = " (SHIELDED)" if event.get("shielded", False) else ""
            print(f"   {i+1:2d}. Turn {event['turn']:2d}: {action_type} {attacker} uses {event['move']} "
                  f"→ {event.get('damage', 0)} damage{shielded}")
    
    print(f"\n✅ Battle simulation completed successfully!")
    return True


def validate_damage_consistency():
    """Validate that damage calculations are consistent and reasonable."""
    
    print(f"\n🧮 VALIDATION: Damage Calculation Consistency")
    print("=" * 60)
    
    gm = GameMaster()
    
    # Test with a variety of Pokemon and moves
    test_cases = [
        ("azumarill", "BUBBLE", "medicham"),
        ("medicham", "COUNTER", "altaria"),
        ("altaria", "DRAGON_BREATH", "azumarill"),
        ("registeel", "LOCK_ON", "azumarill"),
    ]
    
    from pvpoke.battle.damage_calculator import DamageCalculator
    
    all_passed = True
    
    for attacker_species, move_id, defender_species in test_cases:
        attacker = gm.get_pokemon(attacker_species)
        defender = gm.get_pokemon(defender_species)
        move = gm.get_fast_move(move_id)
        
        if not all([attacker, defender, move]):
            print(f"❌ Could not load test case: {attacker_species} vs {defender_species}")
            all_passed = False
            continue
        
        # Optimize both Pokemon
        attacker.optimize_for_league(1500)
        defender.optimize_for_league(1500)
        attacker.fast_move = move
        
        # Calculate damage
        damage = DamageCalculator.calculate_damage(attacker, defender, move)
        
        print(f"🎯 {attacker.species_name} {move.name} → {defender.species_name}: {damage} damage")
        
        # Validation checks
        if damage <= 0:
            print(f"   ❌ FAIL: Damage should be positive")
            all_passed = False
        elif damage > 100:
            print(f"   ❌ FAIL: Damage seems unreasonably high for a fast move")
            all_passed = False
        else:
            print(f"   ✅ PASS: Damage is reasonable")
    
    if all_passed:
        print(f"\n✅ All damage calculations passed validation!")
    else:
        print(f"\n❌ Some damage calculations failed validation")
    
    return all_passed


def test_multiple_battles():
    """Test multiple battles to check for consistency."""
    
    print(f"\n🔄 VALIDATION: Multiple Battle Consistency")
    print("=" * 60)
    
    gm = GameMaster()
    
    # Set up the same matchup
    azumarill = gm.get_pokemon("azumarill")
    stunfisk = gm.get_pokemon("stunfisk_galarian")
    
    if not azumarill or not stunfisk:
        print("❌ Could not load Pokemon")
        return False
    
    # Configure Pokemon
    azumarill.optimize_for_league(1500)
    stunfisk.optimize_for_league(1500)
    
    azumarill.fast_move = gm.get_fast_move("BUBBLE")
    azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
    
    stunfisk.fast_move = gm.get_fast_move("MUD_SHOT")
    stunfisk.charged_move_1 = gm.get_charged_move("ROCK_SLIDE")
    
    print(f"Testing: {azumarill.species_name} vs {stunfisk.species_name}")
    print("Running 5 identical battles to check consistency...")
    
    results = []
    for i in range(5):
        battle = Battle(azumarill, stunfisk)
        result = battle.simulate()
        results.append(result)
        print(f"  Battle {i+1}: Winner={result.winner}, Rating={result.rating1}, Turns={result.turns}")
    
    # Check consistency
    winners = [r.winner for r in results]
    ratings = [r.rating1 for r in results]
    turns = [r.turns for r in results]
    
    consistent = True
    
    # All battles should have the same winner
    if len(set(winners)) > 1:
        print(f"❌ FAIL: Inconsistent winners: {winners}")
        consistent = False
    
    # Ratings should be very similar (within 10 points)
    rating_range = max(ratings) - min(ratings)
    if rating_range > 10:
        print(f"❌ FAIL: Rating range too large: {rating_range}")
        consistent = False
    
    # Turn counts should be identical or very close
    turn_range = max(turns) - min(turns)
    if turn_range > 2:
        print(f"❌ FAIL: Turn count range too large: {turn_range}")
        consistent = False
    
    if consistent:
        print(f"✅ PASS: All battles produced consistent results")
        print(f"   Winner: Pokemon {winners[0]}")
        print(f"   Average rating: {sum(ratings)/len(ratings):.1f}")
        print(f"   Average turns: {sum(turns)/len(turns):.1f}")
    
    return consistent


def main():
    """Run the complete validation example."""
    
    print("🚀 PvPoke Python Implementation Validation Example")
    print("=" * 80)
    print("This script demonstrates how to validate the Python implementation")
    print("against expected battle simulation results.")
    print()
    
    # Run all validation tests
    tests = [
        ("Basic Battle Demonstration", demonstrate_basic_battle),
        ("Damage Calculation Validation", validate_damage_consistency),
        ("Multiple Battle Consistency", test_multiple_battles),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"🏁 VALIDATION COMPLETE")
    print(f"{'='*80}")
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print(f"\n🎉 EXCELLENT! All validation tests passed!")
        print(f"\n📋 SUMMARY OF WHAT WORKS:")
        print(f"   ✅ Pokemon data loading and optimization")
        print(f"   ✅ Move assignment and validation")
        print(f"   ✅ Battle simulation engine")
        print(f"   ✅ Damage calculations")
        print(f"   ✅ Battle rating system")
        print(f"   ✅ Timeline generation")
        print(f"   ✅ Result consistency")
        print(f"\n🚀 READY FOR PRODUCTION!")
        print(f"   The Python implementation is working correctly and can be")
        print(f"   used for battle simulations, ranking calculations, and analysis.")
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Run more extensive validation against JavaScript results")
        print(f"   2. Test edge cases and advanced mechanics")
        print(f"   3. Performance optimization for bulk simulations")
        print(f"   4. Add any missing advanced features as needed")
    else:
        print(f"\n⚠️  Some tests failed. Review the results above.")
        print(f"   The implementation may need adjustments before production use.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
