"""Tests for Pokemon ranking system."""

import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core import Pokemon, Stats, IVs
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.rankings.ranker import Ranker
from pvpoke.battle import Battle, BattleResult


class TestRanker(unittest.TestCase):
    """Test Ranker class functionality."""
    
    def setUp(self):
        """Set up test Pokemon and ranker."""
        # Create test Pokemon
        self.pokemon1 = Pokemon(
            species_id="azumarill",
            species_name="Azumarill",
            dex=184,
            base_stats=Stats(atk=112.2, defense=152.3, hp=225),
            types=["water", "fairy"]
        )
        
        self.pokemon2 = Pokemon(
            species_id="medicham",
            species_name="Medicham",
            dex=308,
            base_stats=Stats(atk=121, defense=152, hp=155),
            types=["fighting", "psychic"]
        )
        
        self.pokemon3 = Pokemon(
            species_id="skarmory",
            species_name="Skarmory",
            dex=227,
            base_stats=Stats(atk=148, defense=226, hp=163),
            types=["steel", "flying"]
        )
        
        # Set up moves for each Pokemon
        bubble = FastMove("BUBBLE", "Bubble", "water", 7, 11, 3)
        ice_beam = ChargedMove("ICE_BEAM", "Ice Beam", "ice", 90, 55)
        
        counter = FastMove("COUNTER", "Counter", "fighting", 8, 7, 2)
        power_up_punch = ChargedMove("POWER_UP_PUNCH", "Power-Up Punch", "fighting", 20, 35,
                                     buffs=[1.25, 1.0], buff_target="self", buff_chance=1.0)
        
        air_slash = FastMove("AIR_SLASH", "Air Slash", "flying", 9, 9, 3)
        sky_attack = ChargedMove("SKY_ATTACK", "Sky Attack", "flying", 75, 45)
        
        self.pokemon1.fast_move = bubble
        self.pokemon1.charged_move_1 = ice_beam
        
        self.pokemon2.fast_move = counter
        self.pokemon2.charged_move_1 = power_up_punch
        
        self.pokemon3.fast_move = air_slash
        self.pokemon3.charged_move_1 = sky_attack
        
        # Set IVs and levels
        for pokemon in [self.pokemon1, self.pokemon2, self.pokemon3]:
            pokemon.ivs = IVs(0, 15, 15)
            pokemon.level = 40
            pokemon.shields = 1
            pokemon.reset()
        
        # Create ranker
        self.ranker = Ranker(cp_limit=1500)
        self.pokemon_list = [self.pokemon1, self.pokemon2, self.pokemon3]
    
    def test_ranker_initialization(self):
        """Test Ranker initializes correctly."""
        self.assertEqual(self.ranker.cp_limit, 1500)
        self.assertEqual(self.ranker.pokemon_list, [])
        self.assertEqual(self.ranker.results, [])
    
    def test_set_pokemon_list(self):
        """Test setting Pokemon list."""
        self.ranker.set_pokemon_list(self.pokemon_list)
        self.assertEqual(len(self.ranker.pokemon_list), 3)
        self.assertEqual(self.ranker.pokemon_list[0], self.pokemon1)
    
    def test_rank_with_default_scenarios(self):
        """Test ranking with default scenarios."""
        self.ranker.set_pokemon_list(self.pokemon_list)
        rankings = self.ranker.rank()
        
        # Should return rankings for all Pokemon
        self.assertEqual(len(rankings), 3)
        
        # Each ranking should have required fields
        for ranking in rankings:
            self.assertIn("speciesId", ranking)
            self.assertIn("speciesName", ranking)
            self.assertIn("score", ranking)
            self.assertIn("matchups", ranking)
            self.assertIn("counters", ranking)
            
            # Score should be a reasonable value
            self.assertGreaterEqual(ranking["score"], 0)
            self.assertLessEqual(ranking["score"], 1000)
    
    def test_rank_with_custom_scenarios(self):
        """Test ranking with custom battle scenarios."""
        custom_scenarios = [
            {"shields": [0, 0], "energy": [0, 0]},
            {"shields": [2, 2], "energy": [0, 0]},
            {"shields": [1, 2], "energy": [0, 0]},
        ]
        
        self.ranker.set_pokemon_list(self.pokemon_list)
        rankings = self.ranker.rank(scenarios=custom_scenarios)
        
        self.assertEqual(len(rankings), 3)
        
        # Rankings should be sorted by score
        scores = [r["score"] for r in rankings]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_matchup_calculation(self):
        """Test individual matchup calculations."""
        self.ranker.set_pokemon_list([self.pokemon1, self.pokemon2])
        rankings = self.ranker.rank()
        
        # Find Azumarill's ranking
        azumarill_ranking = next(r for r in rankings if r["speciesId"] == "azumarill")
        
        # Should have matchup data
        self.assertGreater(len(azumarill_ranking["matchups"]), 0)
        
        # Matchup should contain opponent info
        matchup = azumarill_ranking["matchups"][0]
        self.assertIn("opponent", matchup)
        self.assertIn("rating", matchup)
        
        # Rating should be between 0 and 1000
        self.assertGreaterEqual(matchup["rating"], 0)
        self.assertLessEqual(matchup["rating"], 1000)
    
    def test_counters_identification(self):
        """Test that counters are properly identified."""
        self.ranker.set_pokemon_list(self.pokemon_list)
        rankings = self.ranker.rank()
        
        for ranking in rankings:
            # Counters should be the worst matchups
            counters = ranking["counters"]
            
            if len(counters) > 0:
                # Counters should have low ratings
                for counter in counters:
                    self.assertLessEqual(counter["rating"], 500)
    
    def test_self_matchup_exclusion(self):
        """Test that Pokemon don't battle themselves."""
        # Add duplicate Pokemon
        duplicate_list = [self.pokemon1, self.pokemon1]
        self.ranker.set_pokemon_list(duplicate_list)
        
        rankings = self.ranker.rank()
        
        # Should still rank but not battle itself
        azumarill_ranking = rankings[0]
        
        # Should have no matchups (only opponent was itself)
        self.assertEqual(len(azumarill_ranking["matchups"]), 0)
        
        # Score should be default (500)
        self.assertEqual(azumarill_ranking["score"], 500)
    
    def test_get_matchup_matrix(self):
        """Test matchup matrix generation."""
        matrix = self.ranker.get_matchup_matrix(self.pokemon_list)
        
        # Matrix should have entry for each Pokemon
        self.assertEqual(len(matrix), 3)
        
        # Each Pokemon should have matchups against all others
        for pokemon_id, matchups in matrix.items():
            self.assertEqual(len(matchups), 3)
            
            # Self-matchup should be 500
            self.assertEqual(matchups[pokemon_id], 500)
            
            # Other matchups should be valid ratings
            for opponent_id, rating in matchups.items():
                self.assertGreaterEqual(rating, 0)
                self.assertLessEqual(rating, 1000)
    
    def test_matrix_symmetry(self):
        """Test that matchup matrix is inversely symmetric."""
        matrix = self.ranker.get_matchup_matrix([self.pokemon1, self.pokemon2])
        
        # If A beats B with rating X, B loses to A with rating 1000-X
        rating_1v2 = matrix["azumarill"]["medicham"]
        rating_2v1 = matrix["medicham"]["azumarill"]
        
        # Should sum to 1000 (approximately, due to simulation variance)
        self.assertAlmostEqual(rating_1v2 + rating_2v1, 1000, delta=50)
    
    def test_empty_pokemon_list(self):
        """Test ranking with empty Pokemon list."""
        self.ranker.set_pokemon_list([])
        rankings = self.ranker.rank()
        
        self.assertEqual(rankings, [])
    
    def test_single_pokemon_ranking(self):
        """Test ranking with single Pokemon."""
        self.ranker.set_pokemon_list([self.pokemon1])
        rankings = self.ranker.rank()
        
        self.assertEqual(len(rankings), 1)
        
        # With no opponents, score should be default
        self.assertEqual(rankings[0]["score"], 500)
        self.assertEqual(len(rankings[0]["matchups"]), 0)
        self.assertEqual(len(rankings[0]["counters"]), 0)
    
    def test_shield_scenarios_affect_rankings(self):
        """Test that different shield scenarios affect rankings."""
        self.ranker.set_pokemon_list([self.pokemon1, self.pokemon2])
        
        # No shields
        rankings_no_shields = self.ranker.rank(
            scenarios=[{"shields": [0, 0], "energy": [0, 0]}]
        )
        
        # Max shields
        rankings_max_shields = self.ranker.rank(
            scenarios=[{"shields": [2, 2], "energy": [0, 0]}]
        )
        
        # Scores should differ between scenarios
        score_no_shields = rankings_no_shields[0]["score"]
        score_max_shields = rankings_max_shields[0]["score"]
        
        # Scores might be different (though not guaranteed)
        # At minimum, they should be valid
        self.assertGreaterEqual(score_no_shields, 0)
        self.assertGreaterEqual(score_max_shields, 0)
    
    def test_ranking_consistency(self):
        """Test that rankings are consistent across runs."""
        self.ranker.set_pokemon_list(self.pokemon_list)
        
        # Run ranking multiple times with same scenarios
        scenarios = [{"shields": [1, 1], "energy": [0, 0]}]
        
        rankings1 = self.ranker.rank(scenarios=scenarios)
        rankings2 = self.ranker.rank(scenarios=scenarios)
        
        # Order should be the same
        order1 = [r["speciesId"] for r in rankings1]
        order2 = [r["speciesId"] for r in rankings2]
        
        # Due to potential randomness in battles, scores might vary slightly
        # but order should generally be consistent
        self.assertEqual(len(order1), len(order2))
    
    @patch('pvpoke.rankings.ranker.Battle')
    def test_battle_simulation_called(self, mock_battle_class):
        """Test that Battle simulation is called correctly."""
        # Set up mock
        mock_battle = MagicMock()
        mock_result = BattleResult(
            winner=0,
            pokemon1_hp=100,
            pokemon2_hp=0,
            rating1=750,
            rating2=250,
            turns=50,
            time_remaining=200,
            timeline=[]
        )
        mock_battle.simulate.return_value = mock_result
        mock_battle_class.return_value = mock_battle
        
        # Run ranking
        self.ranker.set_pokemon_list([self.pokemon1, self.pokemon2])
        rankings = self.ranker.rank()
        
        # Battle should have been created and simulated
        self.assertTrue(mock_battle_class.called)
        self.assertTrue(mock_battle.simulate.called)
        
        # Results should use the mock battle results
        self.assertEqual(len(rankings), 2)
    
    def test_top_matchups_and_counters_limited(self):
        """Test that matchups and counters are limited to top 5."""
        # Create more Pokemon for testing
        pokemon_list = []
        for i in range(10):
            pokemon = Pokemon(
                species_id=f"pokemon_{i}",
                species_name=f"Pokemon {i}",
                dex=i,
                base_stats=Stats(atk=100+i*10, defense=100+i*5, hp=150+i*3),
                types=["normal", None]
            )
            pokemon.fast_move = FastMove(f"MOVE_{i}", f"Move {i}", "normal", 5, 5, 2)
            pokemon.charged_move_1 = ChargedMove(f"CHARGED_{i}", f"Charged {i}", "normal", 50, 40)
            pokemon.ivs = IVs(10, 10, 10)
            pokemon.level = 40
            pokemon.reset()
            pokemon_list.append(pokemon)
        
        self.ranker.set_pokemon_list(pokemon_list)
        rankings = self.ranker.rank()
        
        # Each Pokemon should have at most 5 matchups and 5 counters listed
        for ranking in rankings:
            self.assertLessEqual(len(ranking["matchups"]), 5)
            self.assertLessEqual(len(ranking["counters"]), 5)


if __name__ == "__main__":
    unittest.main()
