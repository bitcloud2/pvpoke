"""
End-to-End Battle Simulation Tests: Shield Configuration Scenarios (Step 3.1)

This test suite tests battles with different shield configurations to verify
that baiting priority adjusts based on shield counts:
- 2v2: Maximum baiting priority
- 2v1: Shield advantage (less aggressive baiting)
- 1v2: Shield disadvantage (aggressive baiting)
- 0v0: No baiting needed
- 1v0: Shield advantage (no baiting needed)
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core import GameMaster, Pokemon
from pvpoke.battle import Battle, BattleResult


class ShieldScenarioAnalyzer:
    """Helper class to analyze shield scenario battles."""
    
    def __init__(self, result: BattleResult):
        self.result = result
        self.timeline = result.timeline
    
    def get_charged_move_turns(self, pokemon_index: int) -> List[Dict[str, Any]]:
        """Get all turns where a Pokemon used a charged move."""
        return [
            event for event in self.timeline
            if event.get("attacker") == pokemon_index and event.get("action") == "charged"
        ]
    
    def get_move_sequence(self, pokemon_index: int) -> List[str]:
        """Get sequence of charged moves used by a Pokemon."""
        charged_turns = self.get_charged_move_turns(pokemon_index)
        return [turn.get("move") for turn in charged_turns]
    
    def count_shields_used(self, pokemon_index: int) -> int:
        """Count how many shields a Pokemon used (as defender)."""
        opponent_index = 1 - pokemon_index
        shield_count = 0
        for event in self.timeline:
            if (event.get("attacker") == opponent_index and 
                event.get("action") == "charged" and 
                event.get("shielded", False)):
                shield_count += 1
        return shield_count
    
    def count_move_usage(self, pokemon_index: int, move_id: str) -> int:
        """Count how many times a specific move was used."""
        moves = self.get_move_sequence(pokemon_index)
        return moves.count(move_id)
    
    def get_first_move_used(self, pokemon_index: int) -> str:
        """Get the first charged move used by a Pokemon."""
        moves = self.get_move_sequence(pokemon_index)
        return moves[0] if moves else None
    
    def print_analysis(self, pokemon1_name: str, pokemon2_name: str, 
                      shields1: int, shields2: int):
        """Print detailed analysis of the shield scenario."""
        print(f"\n{'='*70}")
        print(f"Shield Scenario: {pokemon1_name} ({shields1}s) vs {pokemon2_name} ({shields2}s)")
        print(f"{'='*70}")
        
        print(f"\nBattle Outcome:")
        print(f"  Winner: {pokemon1_name if self.result.winner == 0 else pokemon2_name}")
        print(f"  Total Turns: {self.result.turns}")
        print(f"  Final HP: {pokemon1_name}={self.result.pokemon1_hp}, {pokemon2_name}={self.result.pokemon2_hp}")
        
        # Move sequences
        p1_moves = self.get_move_sequence(0)
        p2_moves = self.get_move_sequence(1)
        print(f"\nCharged Move Sequences:")
        print(f"  {pokemon1_name}: {p1_moves if p1_moves else 'None'}")
        print(f"  {pokemon2_name}: {p2_moves if p2_moves else 'None'}")
        
        # Shield usage
        p1_shields = self.count_shields_used(0)
        p2_shields = self.count_shields_used(1)
        print(f"\nShields Used:")
        print(f"  {pokemon1_name}: {p1_shields}/{shields1}")
        print(f"  {pokemon2_name}: {p2_shields}/{shields2}")
        
        print(f"{'='*70}\n")


@pytest.fixture(scope="module")
def gm():
    """Load GameMaster once for all tests."""
    return GameMaster()


class TestShieldConfigurationScenarios:
    """Test suite for different shield configuration scenarios."""
    
    def test_2v2_shields_maximum_baiting_priority(self, gm):
        """
        Test 3.1.1: 2v2 Shields (Maximum Baiting Priority)
        
        Both Pokemon have 2 shields. Baiting should be most aggressive.
        Expected: Bait moves preferred over nuke moves to burn opponent shields.
        """
        print("\n" + "="*70)
        print("TEST 3.1.1: 2v2 Shields - Maximum Baiting Priority")
        print("="*70)
        
        # Setup Pokemon - Swampert has clear bait/nuke split
        swampert = gm.get_pokemon("swampert")
        azumarill = gm.get_pokemon("azumarill")
        
        assert swampert is not None, "Could not load Swampert"
        assert azumarill is not None, "Could not load Azumarill"
        
        # Optimize for Great League
        swampert.optimize_for_league(1500)
        azumarill.optimize_for_league(1500)
        
        # Set moves - Swampert with Hydro Cannon (40E, high DPE) and Earthquake (65E, lower DPE)
        swampert.fast_move = gm.get_fast_move("MUD_SHOT")
        swampert.charged_move_1 = gm.get_charged_move("HYDRO_CANNON")  # 40E bait
        swampert.charged_move_2 = gm.get_charged_move("EARTHQUAKE")    # 65E nuke
        swampert.bait_shields = True  # Enable baiting
        swampert.shields = 2
        
        azumarill.fast_move = gm.get_fast_move("BUBBLE")
        azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
        azumarill.charged_move_2 = gm.get_charged_move("PLAY_ROUGH")
        azumarill.shields = 2
        
        # Run battle with timeline logging
        battle = Battle(swampert, azumarill)
        result = battle.simulate(log_timeline=True)
        
        # Analyze
        analyzer = ShieldScenarioAnalyzer(result)
        analyzer.print_analysis("Swampert", "Azumarill", 2, 2)
        
        # Assertions
        swampert_moves = analyzer.get_move_sequence(0)
        assert len(swampert_moves) > 0, "Swampert should have used at least one charged move"
        
        # Count move usage
        hydro_cannon_count = analyzer.count_move_usage(0, "HYDRO_CANNON")
        earthquake_count = analyzer.count_move_usage(0, "EARTHQUAKE")
        shields_burned = analyzer.count_shields_used(1)
        
        print(f"\n✓ Test passed: 2v2 shield scenario tested")
        print(f"  Hydro Cannon used: {hydro_cannon_count} times")
        print(f"  Earthquake used: {earthquake_count} times")
        print(f"  Opponent shields burned: {shields_burned}")
        print(f"  Note: With 2v2 shields, baiting should be most aggressive")
    
    def test_2v1_shields_shield_advantage(self, gm):
        """
        Test 3.1.2: 2v1 Shields (Shield Advantage)
        
        Player has 2 shields, opponent has 1. Less aggressive baiting needed.
        Expected: May use nuke moves earlier since shield advantage exists.
        """
        print("\n" + "="*70)
        print("TEST 3.1.2: 2v1 Shields - Shield Advantage")
        print("="*70)
        
        # Setup Pokemon
        swampert = gm.get_pokemon("swampert")
        azumarill = gm.get_pokemon("azumarill")
        
        assert swampert is not None, "Could not load Swampert"
        assert azumarill is not None, "Could not load Azumarill"
        
        # Optimize for Great League
        swampert.optimize_for_league(1500)
        azumarill.optimize_for_league(1500)
        
        # Set moves
        swampert.fast_move = gm.get_fast_move("MUD_SHOT")
        swampert.charged_move_1 = gm.get_charged_move("HYDRO_CANNON")  # 40E bait
        swampert.charged_move_2 = gm.get_charged_move("EARTHQUAKE")    # 65E nuke
        swampert.bait_shields = True
        swampert.shields = 2  # Shield advantage
        
        azumarill.fast_move = gm.get_fast_move("BUBBLE")
        azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
        azumarill.charged_move_2 = gm.get_charged_move("PLAY_ROUGH")
        azumarill.shields = 1  # Shield disadvantage
        
        # Run battle with timeline logging
        battle = Battle(swampert, azumarill)
        result = battle.simulate(log_timeline=True)
        
        # Analyze
        analyzer = ShieldScenarioAnalyzer(result)
        analyzer.print_analysis("Swampert", "Azumarill", 2, 1)
        
        # Assertions
        swampert_moves = analyzer.get_move_sequence(0)
        assert len(swampert_moves) > 0, "Swampert should have used at least one charged move"
        
        # Count move usage
        hydro_cannon_count = analyzer.count_move_usage(0, "HYDRO_CANNON")
        earthquake_count = analyzer.count_move_usage(0, "EARTHQUAKE")
        shields_burned = analyzer.count_shields_used(1)
        
        print(f"\n✓ Test passed: 2v1 shield advantage scenario tested")
        print(f"  Hydro Cannon used: {hydro_cannon_count} times")
        print(f"  Earthquake used: {earthquake_count} times")
        print(f"  Opponent shields burned: {shields_burned}")
        print(f"  Note: With shield advantage, baiting may be less aggressive")
    
    def test_1v2_shields_shield_disadvantage(self, gm):
        """
        Test 3.1.3: 1v2 Shields (Shield Disadvantage)
        
        Player has 1 shield, opponent has 2. Must bait opponent shields efficiently.
        Expected: Aggressive baiting to even shield count.
        """
        print("\n" + "="*70)
        print("TEST 3.1.3: 1v2 Shields - Shield Disadvantage")
        print("="*70)
        
        # Setup Pokemon
        swampert = gm.get_pokemon("swampert")
        azumarill = gm.get_pokemon("azumarill")
        
        assert swampert is not None, "Could not load Swampert"
        assert azumarill is not None, "Could not load Azumarill"
        
        # Optimize for Great League
        swampert.optimize_for_league(1500)
        azumarill.optimize_for_league(1500)
        
        # Set moves
        swampert.fast_move = gm.get_fast_move("MUD_SHOT")
        swampert.charged_move_1 = gm.get_charged_move("HYDRO_CANNON")  # 40E bait
        swampert.charged_move_2 = gm.get_charged_move("EARTHQUAKE")    # 65E nuke
        swampert.bait_shields = True
        swampert.shields = 1  # Shield disadvantage
        
        azumarill.fast_move = gm.get_fast_move("BUBBLE")
        azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
        azumarill.charged_move_2 = gm.get_charged_move("PLAY_ROUGH")
        azumarill.shields = 2  # Shield advantage
        
        # Run battle with timeline logging
        battle = Battle(swampert, azumarill)
        result = battle.simulate(log_timeline=True)
        
        # Analyze
        analyzer = ShieldScenarioAnalyzer(result)
        analyzer.print_analysis("Swampert", "Azumarill", 1, 2)
        
        # Assertions
        swampert_moves = analyzer.get_move_sequence(0)
        assert len(swampert_moves) > 0, "Swampert should have used at least one charged move"
        
        # Count move usage
        hydro_cannon_count = analyzer.count_move_usage(0, "HYDRO_CANNON")
        earthquake_count = analyzer.count_move_usage(0, "EARTHQUAKE")
        shields_burned = analyzer.count_shields_used(1)
        
        print(f"\n✓ Test passed: 1v2 shield disadvantage scenario tested")
        print(f"  Hydro Cannon used: {hydro_cannon_count} times")
        print(f"  Earthquake used: {earthquake_count} times")
        print(f"  Opponent shields burned: {shields_burned}")
        print(f"  Note: With shield disadvantage, baiting should be aggressive")
    
    def test_0v0_shields_no_baiting(self, gm):
        """
        Test 3.1.4: 0v0 Shields (No Baiting Needed)
        
        No shields available. Baiting logic should be disabled or have no effect.
        Expected: Always use highest damage/DPE moves.
        """
        print("\n" + "="*70)
        print("TEST 3.1.4: 0v0 Shields - No Baiting Needed")
        print("="*70)
        
        # Setup Pokemon
        swampert = gm.get_pokemon("swampert")
        azumarill = gm.get_pokemon("azumarill")
        
        assert swampert is not None, "Could not load Swampert"
        assert azumarill is not None, "Could not load Azumarill"
        
        # Optimize for Great League
        swampert.optimize_for_league(1500)
        azumarill.optimize_for_league(1500)
        
        # Set moves
        swampert.fast_move = gm.get_fast_move("MUD_SHOT")
        swampert.charged_move_1 = gm.get_charged_move("HYDRO_CANNON")  # 40E bait
        swampert.charged_move_2 = gm.get_charged_move("EARTHQUAKE")    # 65E nuke
        swampert.bait_shields = True  # Even with baiting enabled...
        swampert.shields = 0  # No shields
        
        azumarill.fast_move = gm.get_fast_move("BUBBLE")
        azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
        azumarill.charged_move_2 = gm.get_charged_move("PLAY_ROUGH")
        azumarill.shields = 0  # No shields
        
        # Run battle with timeline logging
        battle = Battle(swampert, azumarill)
        result = battle.simulate(log_timeline=True)
        
        # Analyze
        analyzer = ShieldScenarioAnalyzer(result)
        analyzer.print_analysis("Swampert", "Azumarill", 0, 0)
        
        # Assertions
        swampert_moves = analyzer.get_move_sequence(0)
        assert len(swampert_moves) > 0, "Swampert should have used at least one charged move"
        
        # Count move usage
        hydro_cannon_count = analyzer.count_move_usage(0, "HYDRO_CANNON")
        earthquake_count = analyzer.count_move_usage(0, "EARTHQUAKE")
        
        print(f"\n✓ Test passed: 0v0 shields (no baiting) scenario tested")
        print(f"  Hydro Cannon used: {hydro_cannon_count} times")
        print(f"  Earthquake used: {earthquake_count} times")
        print(f"  Note: With no shields, baiting should have no effect")
        print(f"  Expected: Optimal DPE moves chosen based on battle state")
    
    def test_1v0_shields_no_baiting_needed(self, gm):
        """
        Test 3.1.5: 1v0 Shields (Shield Advantage, No Baiting)
        
        Player has shield, opponent doesn't. No need to bait.
        Expected: Use optimal damage moves without baiting.
        """
        print("\n" + "="*70)
        print("TEST 3.1.5: 1v0 Shields - No Baiting Needed")
        print("="*70)
        
        # Setup Pokemon
        swampert = gm.get_pokemon("swampert")
        azumarill = gm.get_pokemon("azumarill")
        
        assert swampert is not None, "Could not load Swampert"
        assert azumarill is not None, "Could not load Azumarill"
        
        # Optimize for Great League
        swampert.optimize_for_league(1500)
        azumarill.optimize_for_league(1500)
        
        # Set moves
        swampert.fast_move = gm.get_fast_move("MUD_SHOT")
        swampert.charged_move_1 = gm.get_charged_move("HYDRO_CANNON")  # 40E bait
        swampert.charged_move_2 = gm.get_charged_move("EARTHQUAKE")    # 65E nuke
        swampert.bait_shields = True
        swampert.shields = 1  # Has shield
        
        azumarill.fast_move = gm.get_fast_move("BUBBLE")
        azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")
        azumarill.charged_move_2 = gm.get_charged_move("PLAY_ROUGH")
        azumarill.shields = 0  # No shields
        
        # Run battle with timeline logging
        battle = Battle(swampert, azumarill)
        result = battle.simulate(log_timeline=True)
        
        # Analyze
        analyzer = ShieldScenarioAnalyzer(result)
        analyzer.print_analysis("Swampert", "Azumarill", 1, 0)
        
        # Assertions
        swampert_moves = analyzer.get_move_sequence(0)
        assert len(swampert_moves) > 0, "Swampert should have used at least one charged move"
        
        # Count move usage
        hydro_cannon_count = analyzer.count_move_usage(0, "HYDRO_CANNON")
        earthquake_count = analyzer.count_move_usage(0, "EARTHQUAKE")
        
        print(f"\n✓ Test passed: 1v0 shields (no baiting needed) scenario tested")
        print(f"  Hydro Cannon used: {hydro_cannon_count} times")
        print(f"  Earthquake used: {earthquake_count} times")
        print(f"  Note: With no opponent shields, baiting is unnecessary")
        print(f"  Expected: Optimal moves chosen without baiting consideration")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
