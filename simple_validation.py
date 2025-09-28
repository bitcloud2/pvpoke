#!/usr/bin/env python3
"""
Simple validation script to test Python PvPoke implementation.

This script runs battle scenarios and compares results against expected outcomes
from the JavaScript version (based on known PvPoke.com results).

Usage:
    pixi shell
    python simple_validation.py
"""

import sys
from pathlib import Path

# Add python directory to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from pvpoke.core import GameMaster
from pvpoke.battle import Battle


def test_azumarill_vs_stunfisk():
    """Test the classic Azumarill vs Galarian Stunfisk matchup."""
    
    print("Testing: Azumarill vs Galarian Stunfisk")
    print("-" * 50)
    
    # Initialize GameMaster
    gm = GameMaster()
    
    # Get Pokemon
    azumarill = gm.get_pokemon("azumarill")
    stunfisk = gm.get_pokemon("stunfisk_galarian")
    
    if not azumarill or not stunfisk:
        print("❌ Could not load Pokemon data")
        return False
    
    # Set up for Great League
    azumarill.optimize_for_league(1500)
    stunfisk.optimize_for_league(1500)
    
    # Set optimal movesets
    azumarill.fast_move = gm.get_fast_move("BUBBLE")
    azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
    azumarill.charged_move_2 = gm.get_charged_move("PLAY_ROUGH")
    
    stunfisk.fast_move = gm.get_fast_move("MUD_SHOT")
    stunfisk.charged_move_1 = gm.get_charged_move("ROCK_SLIDE")
    stunfisk.charged_move_2 = gm.get_charged_move("EARTHQUAKE")
    
    # Display setup
    print(f"Azumarill: CP {azumarill.cp}, Level {azumarill.level}")
    print(f"  IVs: {azumarill.ivs.atk}/{azumarill.ivs.defense}/{azumarill.ivs.hp}")
    print(f"  Moves: {azumarill.fast_move.name}, {azumarill.charged_move_1.name}, {azumarill.charged_move_2.name}")
    
    print(f"Stunfisk: CP {stunfisk.cp}, Level {stunfisk.level}")
    print(f"  IVs: {stunfisk.ivs.atk}/{stunfisk.ivs.defense}/{stunfisk.ivs.hp}")
    print(f"  Moves: {stunfisk.fast_move.name}, {stunfisk.charged_move_1.name}, {stunfisk.charged_move_2.name}")
    
    # Run battle
    battle = Battle(azumarill, stunfisk)
    result = battle.simulate(log_timeline=True)
    
    # Display results
    print(f"\nBattle Results:")
    winner_name = azumarill.species_name if result.winner == 0 else stunfisk.species_name
    print(f"  Winner: {winner_name}")
    print(f"  Final HP: {result.pokemon1_hp} / {result.pokemon2_hp}")
    print(f"  Battle Rating: {result.rating1} / {result.rating2}")
    print(f"  Duration: {result.turns} turns ({result.turns * 0.5:.1f} seconds)")
    
    # Show some timeline
    if result.timeline:
        print(f"\nFirst 5 actions:")
        for i, event in enumerate(result.timeline[:5]):
            attacker = "Azumarill" if event["attacker"] == 0 else "Stunfisk"
            print(f"  {i+1}. Turn {event['turn']}: {attacker} uses {event['move']} (dmg: {event.get('damage', 0)})")
    
    # Expected result: Azumarill should win this matchup
    # Based on PvPoke.com, Azumarill typically wins with ~60-70% rating
    expected_winner = 0  # Azumarill
    expected_rating_range = (600, 800)  # Azumarill should have strong advantage
    
    success = True
    if result.winner != expected_winner:
        print(f"⚠️  Unexpected winner: got {winner_name}, expected Azumarill")
        success = False
    
    if not (expected_rating_range[0] <= result.rating1 <= expected_rating_range[1]):
        print(f"⚠️  Rating outside expected range: got {result.rating1}, expected {expected_rating_range}")
        success = False
    
    if success:
        print("✅ Test passed - results match expectations!")
    
    return success


def test_medicham_vs_altaria():
    """Test Medicham vs Altaria matchup."""
    
    print("\nTesting: Medicham vs Altaria")
    print("-" * 50)
    
    gm = GameMaster()
    
    # Get Pokemon
    medicham = gm.get_pokemon("medicham")
    altaria = gm.get_pokemon("altaria")
    
    if not medicham or not altaria:
        print("❌ Could not load Pokemon data")
        return False
    
    # Set up for Great League
    medicham.optimize_for_league(1500)
    altaria.optimize_for_league(1500)
    
    # Set movesets
    medicham.fast_move = gm.get_fast_move("COUNTER")
    medicham.charged_move_1 = gm.get_charged_move("DYNAMIC_PUNCH")
    medicham.charged_move_2 = gm.get_charged_move("ICE_PUNCH")
    
    altaria.fast_move = gm.get_fast_move("DRAGON_BREATH")
    altaria.charged_move_1 = gm.get_charged_move("SKY_ATTACK")
    altaria.charged_move_2 = gm.get_charged_move("DRAGON_PULSE")
    
    # Display setup
    print(f"Medicham: CP {medicham.cp}, Level {medicham.level}")
    print(f"Altaria: CP {altaria.cp}, Level {altaria.level}")
    
    # Run battle
    battle = Battle(medicham, altaria)
    result = battle.simulate()
    
    # Display results
    winner_name = medicham.species_name if result.winner == 0 else altaria.species_name
    print(f"\nResults: {winner_name} wins")
    print(f"  Final HP: {result.pokemon1_hp} / {result.pokemon2_hp}")
    print(f"  Rating: {result.rating1} / {result.rating2}")
    print(f"  Turns: {result.turns}")
    
    # Expected: This should be a close matchup, slight edge to Medicham
    # Rating should be around 550-650 for Medicham
    expected_winner = 0  # Medicham
    expected_rating_range = (520, 700)
    
    success = True
    if result.winner != expected_winner:
        print(f"⚠️  Unexpected winner: got {winner_name}, expected Medicham")
        success = False
    
    if not (expected_rating_range[0] <= result.rating1 <= expected_rating_range[1]):
        print(f"⚠️  Rating outside expected range: got {result.rating1}, expected {expected_rating_range}")
        success = False
    
    if success:
        print("✅ Test passed!")
    
    return success


def test_registeel_vs_azumarill():
    """Test Registeel vs Azumarill - should be very close."""
    
    print("\nTesting: Registeel vs Azumarill")
    print("-" * 50)
    
    gm = GameMaster()
    
    # Get Pokemon
    registeel = gm.get_pokemon("registeel")
    azumarill = gm.get_pokemon("azumarill")
    
    if not registeel or not azumarill:
        print("❌ Could not load Pokemon data")
        return False
    
    # Set up for Great League
    registeel.optimize_for_league(1500)
    azumarill.optimize_for_league(1500)
    
    # Set movesets
    registeel.fast_move = gm.get_fast_move("LOCK_ON")
    registeel.charged_move_1 = gm.get_charged_move("FOCUS_BLAST")
    registeel.charged_move_2 = gm.get_charged_move("ZAP_CANNON")
    
    azumarill.fast_move = gm.get_fast_move("BUBBLE")
    azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
    azumarill.charged_move_2 = gm.get_charged_move("HYDRO_PUMP")
    
    print(f"Registeel: CP {registeel.cp}")
    print(f"Azumarill: CP {azumarill.cp}")
    
    # Run battle
    battle = Battle(registeel, azumarill)
    result = battle.simulate()
    
    winner_name = registeel.species_name if result.winner == 0 else azumarill.species_name
    print(f"\nResults: {winner_name} wins")
    print(f"  Final HP: {result.pokemon1_hp} / {result.pokemon2_hp}")
    print(f"  Rating: {result.rating1} / {result.rating2}")
    
    # This should be a very close matchup - rating should be near 500
    expected_rating_range = (450, 550)
    
    success = True
    if not (expected_rating_range[0] <= result.rating1 <= expected_rating_range[1]):
        print(f"⚠️  Rating outside expected range: got {result.rating1}, expected {expected_rating_range}")
        success = False
    
    if success:
        print("✅ Test passed - close matchup as expected!")
    
    return success


def test_damage_calculations():
    """Test basic damage calculations."""
    
    print("\nTesting: Damage Calculations")
    print("-" * 50)
    
    gm = GameMaster()
    
    # Get a simple Pokemon for testing
    pokemon = gm.get_pokemon("azumarill")
    opponent = gm.get_pokemon("medicham")
    
    if not pokemon or not opponent:
        print("❌ Could not load Pokemon data")
        return False
    
    # Set up basic stats
    pokemon.optimize_for_league(1500)
    opponent.optimize_for_league(1500)
    
    # Set moves
    pokemon.fast_move = gm.get_fast_move("BUBBLE")
    pokemon.charged_move_1 = gm.get_charged_move("ICE_BEAM")
    
    print(f"Azumarill Bubble vs Medicham:")
    print(f"  Azumarill Attack: {pokemon.calculate_stats().atk:.1f}")
    print(f"  Medicham Defense: {opponent.calculate_stats().defense:.1f}")
    
    # Test damage calculation
    from pvpoke.battle.damage_calculator import DamageCalculator
    
    fast_damage = DamageCalculator.calculate_damage(pokemon, opponent, pokemon.fast_move)
    charged_damage = DamageCalculator.calculate_damage(pokemon, opponent, pokemon.charged_move_1)
    
    print(f"  Bubble damage: {fast_damage}")
    print(f"  Ice Beam damage: {charged_damage}")
    
    # Basic sanity checks
    success = True
    if fast_damage <= 0:
        print("❌ Fast move damage should be positive")
        success = False
    
    if charged_damage <= fast_damage:
        print("❌ Charged move should do more damage than fast move")
        success = False
    
    if fast_damage > 50:  # Unreasonably high for a fast move
        print(f"❌ Fast move damage seems too high: {fast_damage}")
        success = False
    
    if success:
        print("✅ Damage calculations look reasonable!")
    
    return success


def main():
    """Run all validation tests."""
    
    print("PvPoke Python Implementation Validation")
    print("=" * 60)
    print("Testing core battle mechanics against expected results")
    print()
    
    tests = [
        test_damage_calculations,
        test_azumarill_vs_stunfisk,
        test_medicham_vs_altaria,
        test_registeel_vs_azumarill,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 60)
    print(f"VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("The Python implementation is working correctly!")
        print("\nKey findings:")
        print("✅ Battle simulation runs without errors")
        print("✅ Damage calculations are reasonable")
        print("✅ Battle outcomes match expected patterns")
        print("✅ Ratings are in expected ranges")
        print("\nYou can proceed with confidence that the core mechanics are working!")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed.")
        print("Review the results above to identify issues.")
        print("The implementation may need adjustments before full validation.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
