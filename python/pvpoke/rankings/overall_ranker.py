"""Overall ranking calculation system."""

import math
from typing import List, Dict, Optional
from ..core.pokemon import Pokemon


class OverallRanker:
    """
    Calculate overall rankings by combining category rankings.
    Implements the complete PvPoke overall ranking algorithm.
    """
    
    def __init__(self):
        """Initialize the overall ranker."""
        self.categories = ["leads", "closers", "switches", "chargers", "attackers"]
        self.overrides = []  # Editor overrides for specific Pokemon
    
    def set_overrides(self, overrides: List[Dict]):
        """Set editor overrides for Pokemon scores."""
        self.overrides = overrides
    
    def calculate_consistency_score(self, pokemon: Pokemon) -> float:
        """
        Calculate consistency score for a Pokemon.
        
        Args:
            pokemon: Pokemon to calculate consistency for
            
        Returns:
            Consistency score (0-100)
        """
        # This is a simplified version - the original calculates based on
        # move timing, energy requirements, and shield dependency
        
        # Factors that affect consistency:
        # - Fast move duration (shorter = more consistent)
        # - Energy requirements of charged moves
        # - Damage variance
        
        consistency = 75  # Base consistency
        
        # Adjust based on fast move cooldown
        if hasattr(pokemon, 'fast_move') and pokemon.fast_move:
            if pokemon.fast_move.cooldown <= 2:
                consistency += 10  # Very fast moves are more consistent
            elif pokemon.fast_move.cooldown >= 4:
                consistency -= 10  # Slow moves are less consistent
        
        # Adjust based on charged move energy requirements
        if hasattr(pokemon, 'charged_moves') and pokemon.charged_moves:
            avg_energy = sum(move.energy for move in pokemon.charged_moves) / len(pokemon.charged_moves)
            if avg_energy <= 35:
                consistency += 5  # Low energy moves are more consistent
            elif avg_energy >= 60:
                consistency -= 5  # High energy moves are less consistent
        
        return max(0, min(100, consistency))
    
    def combine_category_rankings(self, category_rankings: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Combine rankings from all categories into overall rankings.
        
        Args:
            category_rankings: Dictionary mapping category names to rankings
            
        Returns:
            Overall rankings
        """
        # Build a map of Pokemon to their scores in each category
        pokemon_data = {}
        
        for category, rankings in category_rankings.items():
            if category not in self.categories:
                continue
                
            # Find the maximum score in this category for normalization
            max_score = max(ranking["score"] for ranking in rankings) if rankings else 1
            
            for i, ranking in enumerate(rankings):
                species_id = ranking["speciesId"]
                
                if species_id not in pokemon_data:
                    pokemon_data[species_id] = {
                        "speciesId": species_id,
                        "speciesName": ranking.get("speciesName", species_id),
                        "scores": {},
                        "moveset": ranking.get("moveset", []),
                        "moves": ranking.get("moves", {}),
                        "matchups": ranking.get("matches", [])
                    }
                
                # Normalize score to percentage of #1 Pokemon in this category
                normalized_score = (ranking["score"] / max_score) * 100 if max_score > 0 else 0
                pokemon_data[species_id]["scores"][category] = normalized_score
        
        # Calculate overall scores
        overall_rankings = []
        
        for species_id, data in pokemon_data.items():
            scores = data["scores"]
            
            # Only include Pokemon that have scores in all categories
            if len(scores) < len(self.categories):
                continue
            
            # Get scores in order: leads, closers, switches, chargers, attackers
            category_scores = [scores.get(category, 0) for category in self.categories]
            
            # Calculate consistency score
            # This would normally be calculated from the Pokemon's moveset
            # For now, use a simplified calculation
            consistency_score = sum(category_scores) / len(category_scores) * 0.8  # Simplified
            
            # Sort scores for weighted calculation
            sorted_scores = sorted(category_scores, reverse=True)
            
            # Weighted geometric mean calculation from original algorithm
            # Formula: (score1^12 * score2^6 * max(score3,score4)^4 * score5^2 * consistency^2)^(1/26)
            try:
                overall_score = pow(
                    pow(max(sorted_scores[0], 1), 12) * 
                    pow(max(sorted_scores[1], 1), 6) * 
                    pow(max(sorted_scores[2], sorted_scores[3]), 4) * 
                    pow(max(sorted_scores[4], 1), 2) * 
                    pow(max(consistency_score, 1), 2),
                    1/26
                )
                
                # Apply additional weighting for low-performing Pokemon
                if sorted_scores[4] <= 75 and consistency_score <= 75:
                    overall_score = pow(
                        pow(max(overall_score, 1), 14) * 
                        pow(max(sorted_scores[4], 1), 1) * 
                        pow(max(consistency_score, 1), 1),
                        1/16
                    )
                
            except (ValueError, ZeroDivisionError):
                overall_score = 0
            
            # Apply editor overrides if any
            editor_score = None
            editor_notes = None
            
            for override in self.overrides:
                if override.get("speciesId") == species_id:
                    if "editorScore" in override:
                        editor_score = override["editorScore"]
                        # Weight heavily toward editor score (75% editor, 25% calculated)
                        overall_score = (overall_score * 0.25) + (editor_score * 0.75)
                    
                    if "editorNotes" in override:
                        editor_notes = override["editorNotes"]
                    break
            
            # Round to one decimal place
            overall_score = round(overall_score, 1)
            
            ranking_data = {
                "speciesId": species_id,
                "speciesName": data["speciesName"],
                "score": overall_score,
                "scores": category_scores,
                "moveset": data["moveset"],
                "moves": data["moves"]
            }
            
            # Add editor data if present
            if editor_score is not None:
                ranking_data["editorScore"] = editor_score
            if editor_notes is not None:
                ranking_data["editorNotes"] = editor_notes
            
            # Add top matchups and counters from leads category (as per original)
            if "leads" in category_rankings and category_rankings["leads"]:
                leads_ranking = next(
                    (r for r in category_rankings["leads"] if r["speciesId"] == species_id), 
                    None
                )
                if leads_ranking and "matches" in leads_ranking:
                    # Sort matchups by rating
                    matchups = sorted(leads_ranking["matches"], key=lambda x: x["rating"], reverse=True)
                    ranking_data["matchups"] = matchups[:5]  # Top 5 matchups
                    ranking_data["counters"] = sorted(matchups, key=lambda x: x["rating"])[:5]  # Top 5 counters
            
            overall_rankings.append(ranking_data)
        
        # Sort by overall score
        overall_rankings.sort(key=lambda x: x["score"], reverse=True)
        
        return overall_rankings
    
    def add_pokemon_stats(self, rankings: List[Dict], pokemon_list: List[Pokemon]) -> List[Dict]:
        """
        Add Pokemon stats to the rankings.
        
        Args:
            rankings: List of ranking dictionaries
            pokemon_list: List of Pokemon objects
            
        Returns:
            Rankings with added stats
        """
        # Create a lookup map for Pokemon
        pokemon_map = {p.species_id: p for p in pokemon_list}
        
        for ranking in rankings:
            species_id = ranking["speciesId"]
            if species_id in pokemon_map:
                pokemon = pokemon_map[species_id]
                
                stats = pokemon.calculate_stats()
                ranking["stats"] = {
                    "product": round(stats.atk * stats.defense * stats.hp / 1000),
                    "atk": round(stats.atk, 1),
                    "def": round(stats.defense, 1),
                    "hp": stats.hp
                }
        
        return rankings
    
    def generate_overall_rankings(self, category_rankings: Dict[str, List[Dict]], 
                                pokemon_list: Optional[List[Pokemon]] = None) -> List[Dict]:
        """
        Generate complete overall rankings.
        
        Args:
            category_rankings: Rankings for each category
            pokemon_list: List of Pokemon objects (for stats)
            
        Returns:
            Complete overall rankings
        """
        # Combine category rankings
        overall_rankings = self.combine_category_rankings(category_rankings)
        
        # Add Pokemon stats if available
        if pokemon_list:
            overall_rankings = self.add_pokemon_stats(overall_rankings, pokemon_list)
        
        return overall_rankings
