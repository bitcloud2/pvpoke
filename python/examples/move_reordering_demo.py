#!/usr/bin/env python3
"""
Move Reordering Logic Demo

This script demonstrates the Move Reordering Logic (Step 1L) implementation
that was just completed. It shows how the AI reorders moves based on:

1. Damage when not baiting or shields are down
2. Energy efficiency when shields are up  
3. Avoiding self-debuffing moves during baiting
4. Preferring efficient moves of same/similar energy costs

Usage:
    cd /Users/jeff.roach/Documents/pvpoke/python
    pixi run python examples/move_reordering_demo.py
"""

from unittest.mock import Mock
from pvpoke.battle.ai import ActionLogic
from pvpoke.core.pokemon import Pokemon
from pvpoke.core.moves import ChargedMove


def create_demo_pokemon():
    """Create a demo Pokemon with multiple charged moves."""
    poke = Mock(spec=Pokemon)
    poke.species_id = "machamp"
    poke.current_hp = 120
    poke.stats = Mock()
    poke.stats.hp = 150
    poke.energy = 80
    poke.bait_shields = True
    return poke


def create_demo_opponent(shields=2):
    """Create a demo opponent Pokemon."""
    opponent = Mock(spec=Pokemon)
    opponent.species_id = "alakazam"
    opponent.current_hp = 100
    opponent.shields = shields
    return opponent


def create_demo_moves():
    """Create demo charged moves with different properties."""
    # Low energy, efficient move
    surf = Mock(spec=ChargedMove)
    surf.move_id = "surf"
    surf.energy_cost = 35
    surf.self_debuffing = False
    
    # High energy, powerful move
    hydro_pump = Mock(spec=ChargedMove)
    hydro_pump.move_id = "hydro_pump"
    hydro_pump.energy_cost = 65
    hydro_pump.self_debuffing = False
    
    # Self-debuffing move
    superpower = Mock(spec=ChargedMove)
    superpower.move_id = "superpower"
    superpower.energy_cost = 55
    superpower.self_debuffing = True
    
    return surf, hydro_pump, superpower


def mock_damage_calculator():
    """Mock the damage calculator for consistent results."""
    def calculate_damage(attacker, defender, move):
        damage_values = {
            "surf": 65,
            "hydro_pump": 130,
            "superpower": 85
        }
        return damage_values.get(move.move_id, 50)
    
    # Patch the DamageCalculator
    import pvpoke.battle.damage_calculator
    pvpoke.battle.damage_calculator.DamageCalculator.calculate_damage = calculate_damage


def demo_scenario_1():
    """Demo 1: Damage sorting when shields are down."""
    print("=== DEMO 1: Damage Sorting (Shields Down) ===")
    
    poke = create_demo_pokemon()
    opponent = create_demo_opponent(shields=0)  # No shields
    surf, hydro_pump, superpower = create_demo_moves()
    
    # DP algorithm chose moves in energy order
    optimal_moves = [surf, hydro_pump]  # Low energy first
    active_moves = [surf, hydro_pump, superpower]
    
    print(f"Original DP order: {[m.move_id for m in optimal_moves]}")
    print(f"Opponent shields: {opponent.shields}")
    print(f"Pokemon bait_shields: {poke.bait_shields}")
    
    result = ActionLogic.apply_move_reordering_logic(
        poke, opponent, optimal_moves, active_moves,
        needs_boost=False, debuffing_move=False
    )
    
    print(f"Reordered moves: {[m.move_id for m in result]}")
    print("Expected: Hydro Pump first (higher damage)")
    print()


def demo_scenario_2():
    """Demo 2: Energy efficiency preference when shields are up."""
    print("=== DEMO 2: Energy Efficiency (Shields Up) ===")
    
    poke = create_demo_pokemon()
    opponent = create_demo_opponent(shields=2)  # Has shields
    surf, hydro_pump, superpower = create_demo_moves()
    
    # DP algorithm chose high energy move
    optimal_moves = [hydro_pump]
    active_moves = [surf, hydro_pump, superpower]
    
    print(f"Original DP choice: {optimal_moves[0].move_id}")
    print(f"Opponent shields: {opponent.shields}")
    print(f"Surf energy: {surf.energy_cost}, Hydro Pump energy: {hydro_pump.energy_cost}")
    
    result = ActionLogic.apply_move_reordering_logic(
        poke, opponent, optimal_moves, active_moves,
        needs_boost=False, debuffing_move=False
    )
    
    print(f"Reordered choice: {result[0].move_id}")
    print("Expected: Surf (lower energy, more efficient when shields up)")
    print()


def demo_scenario_3():
    """Demo 3: Self-debuffing move avoidance."""
    print("=== DEMO 3: Self-Debuffing Avoidance ===")
    
    poke = create_demo_pokemon()
    poke.current_hp = 120  # High HP
    opponent = create_demo_opponent(shields=0)  # No shields
    opponent.current_hp = 100
    
    surf, hydro_pump, superpower = create_demo_moves()
    
    # DP algorithm chose debuffing move
    optimal_moves = [superpower]
    active_moves = [surf, hydro_pump, superpower]
    
    print(f"Original DP choice: {optimal_moves[0].move_id} (self-debuffing)")
    print(f"Pokemon HP: {poke.current_hp}/{poke.stats.hp} ({poke.current_hp/poke.stats.hp:.1%})")
    print(f"Opponent HP: {opponent.current_hp}")
    print(f"Superpower damage: 85 (85% of opponent HP)")
    
    result = ActionLogic.apply_move_reordering_logic(
        poke, opponent, optimal_moves, active_moves,
        needs_boost=False, debuffing_move=True
    )
    
    print(f"Reordered choice: {result[0].move_id}")
    print("Expected: Surf (non-debuffing alternative when both sides have high HP)")
    print()


def demo_scenario_4():
    """Demo 4: Same energy efficiency preference."""
    print("=== DEMO 4: Same Energy Efficiency ===")
    
    poke = create_demo_pokemon()
    opponent = create_demo_opponent(shields=1)
    
    # Create two moves with same energy cost
    ice_beam = Mock(spec=ChargedMove)
    ice_beam.move_id = "ice_beam"
    ice_beam.energy_cost = 55
    ice_beam.self_debuffing = False
    
    thunderbolt = Mock(spec=ChargedMove)
    thunderbolt.move_id = "thunderbolt"
    thunderbolt.energy_cost = 55
    thunderbolt.self_debuffing = False
    
    # Mock DPE calculation to make ice_beam more efficient
    original_dpe = ActionLogic.calculate_move_dpe
    def mock_dpe(poke, opponent, move):
        if move.move_id == "ice_beam":
            return 2.2
        elif move.move_id == "thunderbolt":
            return 1.8
        return original_dpe(poke, opponent, move)
    
    ActionLogic.calculate_move_dpe = mock_dpe
    
    # DP chose less efficient move
    optimal_moves = [thunderbolt]
    active_moves = [ice_beam, thunderbolt]
    
    print(f"Original DP choice: {optimal_moves[0].move_id}")
    print(f"Both moves cost: {ice_beam.energy_cost} energy")
    print("Ice Beam DPE: 2.2, Thunderbolt DPE: 1.8")
    
    result = ActionLogic.apply_move_reordering_logic(
        poke, opponent, optimal_moves, active_moves,
        needs_boost=False, debuffing_move=False
    )
    
    print(f"Reordered choice: {result[0].move_id}")
    print("Expected: Ice Beam (more efficient move of same energy)")
    
    # Restore original function
    ActionLogic.calculate_move_dpe = original_dpe
    print()


def main():
    """Run all move reordering demos."""
    print("Move Reordering Logic (Step 1L) - Demonstration")
    print("=" * 50)
    print()
    
    # Mock the damage calculator for consistent results
    mock_damage_calculator()
    
    # Run demo scenarios
    demo_scenario_1()
    demo_scenario_2()
    demo_scenario_3()
    demo_scenario_4()
    
    print("Move reordering logic successfully demonstrated!")
    print("\nKey Features Implemented:")
    print("✅ Damage-based sorting when shields are down")
    print("✅ Energy efficiency preference when shields are up")
    print("✅ Self-debuffing move avoidance in appropriate conditions")
    print("✅ Same/similar energy cost efficiency optimization")


if __name__ == "__main__":
    main()
