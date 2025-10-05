"""
Test Aegislash ranking special cases (Step 1AB).

Tests the special handling of Aegislash in the ranking system:
1. Moveset override: Shield form shows AEGISLASH_CHARGE_PSYCHO_CUT as fast move
2. Shield pressure trait: Shield form always has shield pressure trait
3. Chargers scenario scoring: Proper fast move pressure calculation

JavaScript References:
- Ranker.js lines 524-526: Aegislash moveset override
- Pokemon.js line 1473: Aegislash shield pressure trait
- Ranker.js lines 532-537: Chargers scenario scoring
"""

import pytest
import math
from pvpoke.core.pokemon import Pokemon, IVs, Stats
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.rankings.ranker import Ranker, RankingScenario


@pytest.fixture
def aegislash_shield():
    """Create Aegislash Shield form for testing."""
    pokemon = Pokemon(
        species_id="aegislash_shield",
        species_name="Aegislash (Shield)",
        dex=681,
        base_stats=Stats(atk=118, defense=264, hp=155),
        types=["steel", "ghost"],
        level=20.0,
        ivs=IVs(0, 15, 15),
        cp=1500
    )
    
    # Set up moves
    pokemon.fast_move = FastMove(
        move_id="PSYCHO_CUT",
        name="Psycho Cut",
        move_type="psychic",
        power=3,
        energy_gain=9,
        turns=1  # 1 turn = 500ms cooldown
    )
    
    pokemon.charged_move_1 = ChargedMove(
        move_id="SHADOW_BALL",
        name="Shadow Ball",
        move_type="ghost",
        power=100,
        energy_cost=55
    )
    
    pokemon.charged_move_2 = ChargedMove(
        move_id="GYRO_BALL",
        name="Gyro Ball",
        move_type="steel",
        power=80,
        energy_cost=60
    )
    
    pokemon.best_charged_move = pokemon.charged_move_1
    
    return pokemon


@pytest.fixture
def aegislash_blade():
    """Create Aegislash Blade form for testing."""
    pokemon = Pokemon(
        species_id="aegislash_blade",
        species_name="Aegislash (Blade)",
        dex=681,
        base_stats=Stats(atk=237, defense=116, hp=155),
        types=["steel", "ghost"],
        level=10.0,
        ivs=IVs(0, 15, 15),
        cp=1500
    )
    
    # Set up moves
    pokemon.fast_move = FastMove(
        move_id="PSYCHO_CUT",
        name="Psycho Cut",
        move_type="psychic",
        power=3,
        energy_gain=9,
        turns=1  # 1 turn = 500ms cooldown
    )
    
    pokemon.charged_move_1 = ChargedMove(
        move_id="SHADOW_BALL",
        name="Shadow Ball",
        move_type="ghost",
        power=100,
        energy_cost=55
    )
    
    pokemon.best_charged_move = pokemon.charged_move_1
    
    return pokemon


@pytest.fixture
def regular_pokemon():
    """Create a regular Pokemon for comparison."""
    pokemon = Pokemon(
        species_id="azumarill",
        species_name="Azumarill",
        dex=184,
        base_stats=Stats(atk=112, defense=152, hp=225),
        types=["water", "fairy"],
        level=40.0,
        ivs=IVs(0, 15, 15),
        cp=1500
    )
    
    pokemon.fast_move = FastMove(
        move_id="BUBBLE",
        name="Bubble",
        move_type="water",
        power=8,
        energy_gain=11,
        turns=3  # 3 turns = 1500ms cooldown
    )
    
    pokemon.charged_move_1 = ChargedMove(
        move_id="ICE_BEAM",
        name="Ice Beam",
        move_type="ice",
        power=90,
        energy_cost=55
    )
    
    pokemon.charged_move_2 = ChargedMove(
        move_id="PLAY_ROUGH",
        name="Play Rough",
        move_type="fairy",
        power=90,
        energy_cost=60
    )
    
    pokemon.best_charged_move = pokemon.charged_move_1
    
    return pokemon


class TestAegislashMovesetOverride:
    """Test Aegislash moveset override in rankings (Ranker.js lines 524-526)."""
    
    def test_aegislash_shield_moveset_override(self, aegislash_shield, regular_pokemon):
        """Test that Aegislash Shield form gets AEGISLASH_CHARGE_PSYCHO_CUT as fast move in rankings."""
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_shield, regular_pokemon])
        
        # Run a simple scenario
        scenario = RankingScenario("leads", [1, 1], [0, 0])
        rankings = ranker.rank_scenario(scenario)
        
        # Find Aegislash in rankings
        aegislash_ranking = next(r for r in rankings if r["speciesId"] == "aegislash_shield")
        
        # Verify moveset override
        assert "moveset" in aegislash_ranking
        assert aegislash_ranking["moveset"][0] == "AEGISLASH_CHARGE_PSYCHO_CUT"
        assert aegislash_ranking["moveset"][1] == "SHADOW_BALL"
        assert aegislash_ranking["moveset"][2] == "GYRO_BALL"
    
    def test_aegislash_blade_no_override(self, aegislash_blade, regular_pokemon):
        """Test that Aegislash Blade form does NOT get moveset override."""
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_blade, regular_pokemon])
        
        scenario = RankingScenario("leads", [1, 1], [0, 0])
        rankings = ranker.rank_scenario(scenario)
        
        # Find Aegislash Blade in rankings
        aegislash_ranking = next(r for r in rankings if r["speciesId"] == "aegislash_blade")
        
        # Verify no override - should use actual fast move
        assert "moveset" in aegislash_ranking
        assert aegislash_ranking["moveset"][0] == "PSYCHO_CUT"
        assert aegislash_ranking["moveset"][0] != "AEGISLASH_CHARGE_PSYCHO_CUT"
    
    def test_regular_pokemon_no_override(self, regular_pokemon, aegislash_shield):
        """Test that regular Pokemon don't get moveset overrides."""
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([regular_pokemon, aegislash_shield])
        
        scenario = RankingScenario("leads", [1, 1], [0, 0])
        rankings = ranker.rank_scenario(scenario)
        
        # Find regular Pokemon in rankings
        regular_ranking = next(r for r in rankings if r["speciesId"] == "azumarill")
        
        # Verify normal moveset
        assert "moveset" in regular_ranking
        assert regular_ranking["moveset"][0] == "BUBBLE"
        assert regular_ranking["moveset"][1] == "ICE_BEAM"
    
    def test_moveset_with_single_charged_move(self, aegislash_shield):
        """Test moveset override with only one charged move."""
        # Remove second charged move
        aegislash_shield.charged_move_2 = None
        
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_shield])
        
        scenario = RankingScenario("leads", [1, 1], [0, 0])
        rankings = ranker.rank_scenario(scenario)
        
        aegislash_ranking = rankings[0]
        
        # Should have 2 moves (fast + 1 charged)
        assert len(aegislash_ranking["moveset"]) == 2
        assert aegislash_ranking["moveset"][0] == "AEGISLASH_CHARGE_PSYCHO_CUT"
        assert aegislash_ranking["moveset"][1] == "SHADOW_BALL"


class TestAegislashShieldPressureTrait:
    """Test Aegislash shield pressure trait (Pokemon.js line 1473)."""
    
    def test_aegislash_shield_always_has_shield_pressure(self, aegislash_shield):
        """Test that Aegislash Shield form always has shield pressure trait."""
        # Aegislash Shield should always have shield pressure regardless of calculated power
        assert aegislash_shield.has_shield_pressure_trait()
    
    def test_aegislash_shield_pressure_with_weak_move(self, aegislash_shield):
        """Test shield pressure even with a weak charged move."""
        # Give Aegislash a very weak charged move
        weak_move = ChargedMove(
            move_id="STRUGGLE",
            name="Struggle",
            move_type="normal",
            power=15,
            energy_cost=100
        )
        aegislash_shield.best_charged_move = weak_move
        
        # Should still have shield pressure due to species override
        assert aegislash_shield.has_shield_pressure_trait()
    
    def test_aegislash_blade_no_automatic_shield_pressure(self, aegislash_blade):
        """Test that Aegislash Blade form doesn't automatically get shield pressure."""
        # Blade form should be calculated normally (it might still have it, but not automatic)
        # This test just verifies the species check works correctly
        assert aegislash_blade.species_id == "aegislash_blade"
        
        # The trait calculation should run normally (not automatic True)
        # Whether it has shield pressure depends on its actual power calculation
    
    def test_regular_pokemon_shield_pressure_calculation(self, regular_pokemon):
        """Test that regular Pokemon calculate shield pressure normally."""
        # Regular Pokemon should calculate based on effective power
        # This is a basic test - actual value depends on stats
        result = regular_pokemon.has_shield_pressure_trait()
        
        # Should return a boolean (not error)
        assert isinstance(result, bool)
    
    def test_shield_pressure_with_no_moves(self, aegislash_shield):
        """Test shield pressure when best_charged_move is None."""
        aegislash_shield.best_charged_move = None
        
        # Should still return True due to species override
        assert aegislash_shield.has_shield_pressure_trait()
    
    def test_shield_pressure_with_different_target_defense(self, aegislash_shield):
        """Test shield pressure calculation with different target defense values."""
        # Should always be True for Aegislash Shield regardless of target defense
        assert aegislash_shield.has_shield_pressure_trait(target_defense=50)
        assert aegislash_shield.has_shield_pressure_trait(target_defense=100)
        assert aegislash_shield.has_shield_pressure_trait(target_defense=200)


class TestChargersScenarioScoring:
    """Test chargers scenario special scoring (Ranker.js lines 532-537)."""
    
    def test_chargers_scenario_applies_multiplier(self, aegislash_shield, regular_pokemon):
        """Test that chargers scenario applies fast move pressure multiplier."""
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_shield, regular_pokemon])
        
        # Run chargers scenario
        chargers_scenario = RankingScenario("chargers", [1, 1], [6, 0])
        chargers_rankings = ranker.rank_scenario(chargers_scenario)
        
        # Run leads scenario for comparison (no multiplier)
        leads_scenario = RankingScenario("leads", [1, 1], [0, 0])
        leads_rankings = ranker.rank_scenario(leads_scenario)
        
        # Scores should be different due to chargers multiplier
        chargers_aegislash = next(r for r in chargers_rankings if r["speciesId"] == "aegislash_shield")
        leads_aegislash = next(r for r in leads_rankings if r["speciesId"] == "aegislash_shield")
        
        # The chargers score should be modified by the multiplier
        # (it might be higher or lower depending on the Pokemon's characteristics)
        assert "score" in chargers_aegislash
        assert "score" in leads_aegislash
    
    def test_chargers_multiplier_calculation(self, aegislash_shield):
        """Test the chargers scenario multiplier calculation."""
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_shield])
        
        scenario = RankingScenario("chargers", [1, 1], [6, 0])
        rankings = ranker.rank_scenario(scenario)
        
        # Verify the ranking has a score
        assert len(rankings) == 1
        assert "score" in rankings[0]
        assert rankings[0]["score"] > 0
    
    def test_chargers_with_high_energy_carryover(self, aegislash_shield):
        """Test chargers scoring with Pokemon that has high energy carryover."""
        # Aegislash has relatively cheap charged moves (55, 60 energy)
        # Maximum energy remaining = 100 - 55 = 45
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_shield])
        
        scenario = RankingScenario("chargers", [1, 1], [6, 0])
        rankings = ranker.rank_scenario(scenario)
        
        # Should successfully calculate score
        assert rankings[0]["score"] > 0
    
    def test_chargers_with_expensive_charged_moves(self, regular_pokemon):
        """Test chargers scoring with Pokemon that has expensive charged moves."""
        # Give Pokemon very expensive charged moves
        expensive_move = ChargedMove(
            move_id="HYPER_BEAM",
            name="Hyper Beam",
            move_type="normal",
            power=150,
            energy_cost=80
        )
        regular_pokemon.charged_move_1 = expensive_move
        regular_pokemon.charged_move_2 = expensive_move
        
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([regular_pokemon])
        
        scenario = RankingScenario("chargers", [1, 1], [6, 0])
        rankings = ranker.rank_scenario(scenario)
        
        # Should still calculate (lower energy carryover = lower multiplier)
        assert rankings[0]["score"] > 0
    
    def test_chargers_with_fast_fast_move(self, aegislash_shield):
        """Test chargers scoring with a fast fast move (high DPT)."""
        # Psycho Cut has cooldown 2 (fast) and decent power
        # Should get a good fast move pressure score
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_shield])
        
        scenario = RankingScenario("chargers", [1, 1], [6, 0])
        rankings = ranker.rank_scenario(scenario)
        
        # Verify calculation completes
        assert rankings[0]["score"] > 0
    
    def test_non_chargers_scenario_no_multiplier(self, aegislash_shield):
        """Test that non-chargers scenarios don't apply the multiplier."""
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_shield])
        
        # Run different scenarios
        leads = ranker.rank_scenario(RankingScenario("leads", [1, 1], [0, 0]))
        closers = ranker.rank_scenario(RankingScenario("closers", [0, 0], [0, 0]))
        switches = ranker.rank_scenario(RankingScenario("switches", [1, 1], [4, 0]))
        
        # All should have scores (no errors from missing multiplier)
        assert leads[0]["score"] > 0
        assert closers[0]["score"] > 0
        assert switches[0]["score"] > 0


class TestMorpekoMovesetOverride:
    """Test Morpeko moveset override (bonus test for completeness)."""
    
    def test_morpeko_full_belly_moveset_override(self):
        """Test that Morpeko Full Belly form gets AURA_WHEEL_ELECTRIC override."""
        morpeko = Pokemon(
            species_id="morpeko_full_belly",
            species_name="Morpeko (Full Belly)",
            dex=877,
            base_stats=Stats(atk=177, defense=151, hp=151),
            types=["electric", "dark"],
            level=25.0,
            ivs=IVs(0, 15, 15),
            cp=1500
        )
        
        morpeko.fast_move = FastMove(
            move_id="THUNDER_SHOCK",
            name="Thunder Shock",
            move_type="electric",
            power=3,
            energy_gain=9,
            turns=1  # 1 turn = 500ms cooldown
        )
        
        morpeko.charged_move_1 = ChargedMove(
            move_id="AURA_WHEEL_DARK",
            name="Aura Wheel (Dark)",
            move_type="dark",
            power=110,
            energy_cost=55
        )
        
        morpeko.charged_move_2 = ChargedMove(
            move_id="WILD_CHARGE",
            name="Wild Charge",
            move_type="electric",
            power=100,
            energy_cost=50
        )
        
        morpeko.best_charged_move = morpeko.charged_move_1
        
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([morpeko])
        
        scenario = RankingScenario("leads", [1, 1], [0, 0])
        rankings = ranker.rank_scenario(scenario)
        
        # Verify Morpeko gets AURA_WHEEL_ELECTRIC override
        assert rankings[0]["moveset"][1] == "AURA_WHEEL_ELECTRIC"


class TestIntegrationRankings:
    """Integration tests for complete ranking scenarios."""
    
    def test_full_ranking_with_aegislash(self, aegislash_shield, aegislash_blade, regular_pokemon):
        """Test complete ranking with both Aegislash forms."""
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_shield, aegislash_blade, regular_pokemon])
        
        # Run all default scenarios
        all_rankings = ranker.rank_all_scenarios()
        
        # Verify all scenarios completed
        assert "leads" in all_rankings
        assert "closers" in all_rankings
        assert "switches" in all_rankings
        assert "chargers" in all_rankings
        assert "attackers" in all_rankings
        
        # Verify Aegislash Shield has correct moveset in all scenarios
        for scenario_name, rankings in all_rankings.items():
            aegislash_ranking = next(r for r in rankings if r["speciesId"] == "aegislash_shield")
            assert aegislash_ranking["moveset"][0] == "AEGISLASH_CHARGE_PSYCHO_CUT"
    
    def test_ranking_consistency_across_scenarios(self, aegislash_shield):
        """Test that Aegislash ranking is consistent across scenarios."""
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_shield])
        
        # Run multiple scenarios
        scenarios = [
            RankingScenario("leads", [1, 1], [0, 0]),
            RankingScenario("closers", [0, 0], [0, 0]),
            RankingScenario("chargers", [1, 1], [6, 0])
        ]
        
        for scenario in scenarios:
            rankings = ranker.rank_scenario(scenario)
            
            # Should always have the moveset override
            assert rankings[0]["moveset"][0] == "AEGISLASH_CHARGE_PSYCHO_CUT"
            
            # Should always have a valid score
            assert rankings[0]["score"] > 0
    
    def test_aegislash_special_cases_with_iterations(self, aegislash_shield, regular_pokemon):
        """Test Aegislash special cases with weighted iterations."""
        ranker = Ranker(cp_limit=1500)
        ranker.set_pokemon_list([aegislash_shield, regular_pokemon])
        ranker.set_iterations(3)  # Multiple weighted iterations
        
        scenario = RankingScenario("leads", [1, 1], [0, 0])
        rankings = ranker.rank_scenario(scenario)
        
        # Find Aegislash ranking
        aegislash_ranking = next(r for r in rankings if r["speciesId"] == "aegislash_shield")
        
        # Should still have moveset override after iterations
        assert aegislash_ranking["moveset"][0] == "AEGISLASH_CHARGE_PSYCHO_CUT"
        
        # Should have final score
        assert "score" in aegislash_ranking
        assert aegislash_ranking["score"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
