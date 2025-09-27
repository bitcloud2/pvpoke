"""Pokemon ranking calculation system."""

from typing import List, Dict, Optional
from ..core.pokemon import Pokemon
from ..battle.battle import Battle


class Ranker:
    """
    Calculate rankings for Pokemon in a given league.
    This is a simplified version - full implementation will port the JavaScript ranking logic.
    """
    
    def __init__(self, cp_limit: int = 1500):
        """
        Initialize ranker for a specific league.
        
        Args:
            cp_limit: CP limit for the league
        """
        self.cp_limit = cp_limit
        self.pokemon_list = []
        self.results = []
    
    def set_pokemon_list(self, pokemon_list: List[Pokemon]):
        """Set the list of Pokemon to rank."""
        self.pokemon_list = pokemon_list
    
    def rank(self, scenarios: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Run ranking calculations.
        
        Args:
            scenarios: Battle scenarios to test (shields, energy advantages, etc.)
            
        Returns:
            List of ranking results
        """
        if not scenarios:
            # Default scenarios: even shields
            scenarios = [
                {"shields": [0, 0], "energy": [0, 0]},
                {"shields": [1, 1], "energy": [0, 0]},
                {"shields": [2, 2], "energy": [0, 0]}
            ]
        
        rankings = []
        
        for pokemon in self.pokemon_list:
            total_score = 0
            matchups = []
            
            # Battle against all other Pokemon
            for opponent in self.pokemon_list:
                if pokemon.species_id == opponent.species_id:
                    continue
                
                scenario_scores = []
                
                for scenario in scenarios:
                    # Set shields
                    pokemon.shields = scenario["shields"][0]
                    opponent.shields = scenario["shields"][1]
                    
                    # Run battle
                    battle = Battle(pokemon, opponent)
                    result = battle.simulate()
                    
                    scenario_scores.append(result.rating1)
                
                # Average across scenarios
                avg_score = sum(scenario_scores) / len(scenario_scores)
                total_score += avg_score
                
                matchups.append({
                    "opponent": opponent.species_id,
                    "rating": int(avg_score)
                })
            
            # Calculate overall score
            if len(matchups) > 0:
                overall_score = total_score / len(matchups)
            else:
                overall_score = 500
            
            rankings.append({
                "speciesId": pokemon.species_id,
                "speciesName": pokemon.species_name,
                "score": overall_score,
                "matchups": sorted(matchups, key=lambda x: x["rating"], reverse=True)[:5],
                "counters": sorted(matchups, key=lambda x: x["rating"])[:5]
            })
        
        # Sort by score
        rankings.sort(key=lambda x: x["score"], reverse=True)
        
        return rankings
    
    def get_matchup_matrix(self, pokemon_list: List[Pokemon]) -> Dict:
        """
        Generate a matchup matrix for the given Pokemon.
        
        Args:
            pokemon_list: List of Pokemon to compare
            
        Returns:
            Matrix of matchup scores
        """
        matrix = {}
        
        for attacker in pokemon_list:
            matrix[attacker.species_id] = {}
            
            for defender in pokemon_list:
                if attacker.species_id == defender.species_id:
                    matrix[attacker.species_id][defender.species_id] = 500
                    continue
                
                # Run battle
                battle = Battle(attacker, defender)
                result = battle.simulate()
                
                matrix[attacker.species_id][defender.species_id] = result.rating1
        
        return matrix
