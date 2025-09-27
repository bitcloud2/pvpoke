"""Tests for team ranking system."""

import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core import Pokemon, Stats, IVs
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.rankings.team_ranker import TeamRanker


class TestTeamRanker(unittest.TestCase):
    """Test TeamRanker class functionality."""
    
    def setUp(self):
        """Set up test teams and Pokemon."""
        # Create test Pokemon
        self.azumarill = Pokemon(
            species_id="azumarill",
            species_name="Azumarill",
            dex=184,
            base_stats=Stats(atk=112.2, defense=152.3, hp=225),
            types=["water", "fairy"]
        )
        
        self.medicham = Pokemon(
            species_id="medicham",
            species_name="Medicham",
            dex=308,
            base_stats=Stats(atk=121, defense=152, hp=155),
            types=["fighting", "psychic"]
        )
        
        self.skarmory = Pokemon(
            species_id="skarmory",
            species_name="Skarmory",
            dex=227,
            base_stats=Stats(atk=148, defense=226, hp=163),
            types=["steel", "flying"]
        )
        
        self.altaria = Pokemon(
            species_id="altaria",
            species_name="Altaria",
            dex=334,
            base_stats=Stats(atk=141, defense=201, hp=181),
            types=["dragon", "flying"]
        )
        
        self.bastiodon = Pokemon(
            species_id="bastiodon",
            species_name="Bastiodon",
            dex=411,
            base_stats=Stats(atk=94, defense=286, hp=155),
            types=["rock", "steel"]
        )
        
        self.sableye = Pokemon(
            species_id="sableye",
            species_name="Sableye",
            dex=302,
            base_stats=Stats(atk=141, defense=136, hp=137),
            types=["dark", "ghost"]
        )
        
        # Set up basic moves for all Pokemon
        for pokemon in [self.azumarill, self.medicham, self.skarmory, 
                       self.altaria, self.bastiodon, self.sableye]:
            pokemon.fast_move = FastMove("QUICK_ATTACK", "Quick Attack", "normal", 5, 7, 2)
            pokemon.charged_move_1 = ChargedMove("BODY_SLAM", "Body Slam", "normal", 60, 35)
            pokemon.ivs = IVs(0, 15, 15)
            pokemon.level = 40
            pokemon.reset()
        
        # Create test teams
        self.team1 = [self.azumarill, self.medicham, self.skarmory]
        self.team2 = [self.altaria, self.bastiodon, self.sableye]
        
        # Create team ranker
        self.team_ranker = TeamRanker(cp_limit=1500)
    
    def test_team_ranker_initialization(self):
        """Test TeamRanker initializes correctly."""
        self.assertEqual(self.team_ranker.cp_limit, 1500)
        self.assertEqual(self.team_ranker.teams, [])
        self.assertEqual(self.team_ranker.opponent_pool, [])
    
    def test_set_teams(self):
        """Test setting teams for ranking."""
        teams = [self.team1, self.team2]
        self.team_ranker.set_teams(teams)
        
        self.assertEqual(len(self.team_ranker.teams), 2)
        self.assertEqual(len(self.team_ranker.teams[0]), 3)
        self.assertEqual(self.team_ranker.teams[0][0], self.azumarill)
    
    def test_set_opponent_pool(self):
        """Test setting opponent pool."""
        opponent_pool = [self.azumarill, self.medicham, self.skarmory, 
                        self.altaria, self.bastiodon, self.sableye]
        self.team_ranker.set_opponent_pool(opponent_pool)
        
        self.assertEqual(len(self.team_ranker.opponent_pool), 6)
    
    def test_rank_teams_basic(self):
        """Test basic team ranking functionality."""
        self.team_ranker.set_teams([self.team1, self.team2])
        self.team_ranker.set_opponent_pool([self.azumarill, self.medicham])
        
        rankings = self.team_ranker.rank_teams()
        
        # Should return rankings for both teams
        self.assertEqual(len(rankings), 2)
        
        # Each ranking should have required fields
        for ranking in rankings:
            self.assertIn("team", ranking)
            self.assertIn("score", ranking)
            self.assertIn("coverage", ranking)
            self.assertIn("weaknesses", ranking)
            
            # Team should be list of species IDs
            self.assertIsInstance(ranking["team"], list)
            self.assertEqual(len(ranking["team"]), 3)
            
            # Score should be valid
            self.assertGreaterEqual(ranking["score"], 0)
    
    def test_calculate_team_coverage(self):
        """Test team coverage calculation."""
        coverage = self.team_ranker.calculate_team_coverage(
            self.team1, 
            [self.altaria, self.bastiodon, self.sableye]
        )
        
        # Coverage should be a percentage
        self.assertGreaterEqual(coverage, 0)
        self.assertLessEqual(coverage, 100)
        
        # Team with diverse types should have decent coverage
        self.assertGreater(coverage, 30)
    
    def test_identify_team_weaknesses(self):
        """Test identification of team weaknesses."""
        weaknesses = self.team_ranker.identify_team_weaknesses(
            self.team1,
            [self.altaria, self.bastiodon, self.sableye]
        )
        
        # Should return list of problematic opponents
        self.assertIsInstance(weaknesses, list)
        
        # Each weakness should have opponent info and threat score
        for weakness in weaknesses:
            self.assertIn("opponent", weakness)
            self.assertIn("threat_score", weakness)
            
            # Threat score should be valid
            self.assertGreaterEqual(weakness["threat_score"], 0)
    
    def test_calculate_team_synergy(self):
        """Test team synergy calculation."""
        synergy = self.team_ranker.calculate_team_synergy(self.team1)
        
        # Synergy should be a score
        self.assertIsInstance(synergy, (int, float))
        self.assertGreaterEqual(synergy, 0)
        
        # Team with good type coverage should have positive synergy
        self.assertGreater(synergy, 0)
    
    def test_rank_teams_with_weights(self):
        """Test team ranking with custom weights."""
        self.team_ranker.set_teams([self.team1, self.team2])
        self.team_ranker.set_opponent_pool([self.azumarill, self.medicham])
        
        # Custom weights emphasizing coverage
        weights = {
            "battle_performance": 0.3,
            "coverage": 0.5,
            "synergy": 0.2
        }
        
        rankings = self.team_ranker.rank_teams(weights=weights)
        
        # Rankings should still work with custom weights
        self.assertEqual(len(rankings), 2)
        
        # Scores should reflect weighted calculation
        for ranking in rankings:
            self.assertGreaterEqual(ranking["score"], 0)
    
    def test_empty_teams_list(self):
        """Test ranking with no teams."""
        self.team_ranker.set_teams([])
        rankings = self.team_ranker.rank_teams()
        
        self.assertEqual(rankings, [])
    
    def test_empty_opponent_pool(self):
        """Test ranking with no opponent pool."""
        self.team_ranker.set_teams([self.team1])
        self.team_ranker.set_opponent_pool([])
        
        rankings = self.team_ranker.rank_teams()
        
        # Should still return rankings but with limited data
        self.assertEqual(len(rankings), 1)
        
        # Coverage and weaknesses should reflect no opponents
        self.assertEqual(rankings[0]["coverage"], 0)
        self.assertEqual(rankings[0]["weaknesses"], [])
    
    def test_team_vs_team_matchup(self):
        """Test direct team vs team matchup calculation."""
        score = self.team_ranker.calculate_team_matchup(self.team1, self.team2)
        
        # Score should be between 0 and 1000
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1000)
        
        # Reverse matchup should be inverse
        reverse_score = self.team_ranker.calculate_team_matchup(self.team2, self.team1)
        
        # Scores should roughly sum to 1000
        self.assertAlmostEqual(score + reverse_score, 1000, delta=100)
    
    def test_find_best_lead(self):
        """Test finding best lead Pokemon for a team."""
        best_lead = self.team_ranker.find_best_lead(
            self.team1,
            [self.altaria, self.bastiodon, self.sableye]
        )
        
        # Should return one of the team members
        self.assertIn(best_lead, self.team1)
    
    def test_suggest_team_improvements(self):
        """Test team improvement suggestions."""
        suggestions = self.team_ranker.suggest_improvements(
            self.team1,
            [self.azumarill, self.medicham, self.skarmory, 
             self.altaria, self.bastiodon, self.sableye]
        )
        
        # Should return list of suggestions
        self.assertIsInstance(suggestions, list)
        
        # Each suggestion should have replacement info
        for suggestion in suggestions[:3]:  # Check first few suggestions
            self.assertIn("replace", suggestion)
            self.assertIn("with", suggestion)
            self.assertIn("improvement", suggestion)
            
            # Improvement should be positive
            self.assertGreater(suggestion["improvement"], 0)
    
    def test_team_type_balance(self):
        """Test evaluation of team type balance."""
        # Team with good type diversity
        balance1 = self.team_ranker.evaluate_type_balance(self.team1)
        
        # Create team with poor type diversity (all same type)
        water_team = []
        for i in range(3):
            pokemon = Pokemon(
                species_id=f"water_{i}",
                species_name=f"Water {i}",
                dex=i,
                base_stats=Stats(atk=100, defense=100, hp=100),
                types=["water", None]
            )
            water_team.append(pokemon)
        
        balance2 = self.team_ranker.evaluate_type_balance(water_team)
        
        # Diverse team should have better balance
        self.assertGreater(balance1, balance2)
    
    def test_team_role_composition(self):
        """Test evaluation of team role composition."""
        roles = self.team_ranker.evaluate_team_roles(self.team1)
        
        # Should identify roles for each Pokemon
        self.assertIn("lead", roles)
        self.assertIn("safe_switch", roles)
        self.assertIn("closer", roles)
        
        # Each role should be assigned to a team member
        self.assertIn(roles["lead"], self.team1)
        self.assertIn(roles["safe_switch"], self.team1)
        self.assertIn(roles["closer"], self.team1)
    
    def test_team_with_duplicates(self):
        """Test handling team with duplicate Pokemon."""
        duplicate_team = [self.azumarill, self.azumarill, self.medicham]
        
        self.team_ranker.set_teams([duplicate_team])
        self.team_ranker.set_opponent_pool([self.skarmory])
        
        # Should handle duplicates gracefully
        rankings = self.team_ranker.rank_teams()
        
        self.assertEqual(len(rankings), 1)
        
        # Team should be recognized as having duplicates
        self.assertIn("azumarill", rankings[0]["team"])
    
    def test_large_opponent_pool_performance(self):
        """Test performance with large opponent pool."""
        # Create large opponent pool
        large_pool = []
        for i in range(50):
            pokemon = Pokemon(
                species_id=f"pokemon_{i}",
                species_name=f"Pokemon {i}",
                dex=i,
                base_stats=Stats(atk=100+i, defense=100+i, hp=150+i),
                types=["normal", None]
            )
            pokemon.fast_move = FastMove(f"MOVE_{i}", f"Move {i}", "normal", 5, 5, 2)
            pokemon.charged_move_1 = ChargedMove(f"CHARGED_{i}", f"Charged {i}", "normal", 50, 40)
            pokemon.ivs = IVs(10, 10, 10)
            pokemon.level = 40
            pokemon.reset()
            large_pool.append(pokemon)
        
        self.team_ranker.set_teams([self.team1])
        self.team_ranker.set_opponent_pool(large_pool)
        
        # Should complete ranking without issues
        rankings = self.team_ranker.rank_teams()
        
        self.assertEqual(len(rankings), 1)
        self.assertGreaterEqual(rankings[0]["score"], 0)
    
    def test_team_ranking_order(self):
        """Test that teams are ranked in correct order."""
        # Create teams with obvious strength differences
        strong_team = [self.azumarill, self.medicham, self.skarmory]
        weak_team = []
        
        for i in range(3):
            pokemon = Pokemon(
                species_id=f"weak_{i}",
                species_name=f"Weak {i}",
                dex=900+i,
                base_stats=Stats(atk=50, defense=50, hp=50),
                types=["normal", None]
            )
            pokemon.fast_move = FastMove("TACKLE", "Tackle", "normal", 3, 3, 2)
            pokemon.charged_move_1 = ChargedMove("STRUGGLE", "Struggle", "normal", 35, 100)
            pokemon.ivs = IVs(0, 0, 0)
            pokemon.level = 20
            pokemon.reset()
            weak_team.append(pokemon)
        
        self.team_ranker.set_teams([weak_team, strong_team])
        self.team_ranker.set_opponent_pool([self.altaria, self.bastiodon])
        
        rankings = self.team_ranker.rank_teams()
        
        # Rankings should be sorted by score
        scores = [r["score"] for r in rankings]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        # Strong team should rank higher
        strong_idx = next(i for i, r in enumerate(rankings) 
                         if "azumarill" in r["team"])
        weak_idx = next(i for i, r in enumerate(rankings) 
                       if "weak_0" in r["team"])
        
        self.assertLess(strong_idx, weak_idx)


if __name__ == "__main__":
    unittest.main()
