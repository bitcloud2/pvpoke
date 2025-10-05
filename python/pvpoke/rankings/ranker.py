"""Pokemon ranking calculation system."""

import math
from typing import List, Dict, Optional, Tuple
from ..core.pokemon import Pokemon
from ..battle.battle import Battle


class RankingScenario:
    """Represents a ranking scenario with specific battle conditions."""
    
    def __init__(self, slug: str, shields: List[int], energy: List[int]):
        self.slug = slug
        self.shields = shields  # [attacker_shields, defender_shields]
        self.energy = energy    # [attacker_energy_advantage, defender_energy_advantage]


class Ranker:
    """
    Calculate rankings for Pokemon in a given league.
    Implements the complete PvPoke ranking algorithm.
    """
    
    # Default ranking scenarios from the original system
    DEFAULT_SCENARIOS = [
        RankingScenario("leads", [1, 1], [0, 0]),
        RankingScenario("closers", [0, 0], [0, 0]),
        RankingScenario("switches", [1, 1], [4, 0]),
        RankingScenario("chargers", [1, 1], [6, 0]),
        RankingScenario("attackers", [0, 1], [0, 0])
    ]
    
    def __init__(self, cp_limit: int = 1500):
        """
        Initialize ranker for a specific league.
        
        Args:
            cp_limit: CP limit for the league
        """
        self.cp_limit = cp_limit
        self.pokemon_list = []
        self.targets = []  # Pokemon to rank against (can be different from pokemon_list)
        self.move_select_mode = "force"  # "auto" or "force"
        self.scenarios = self.DEFAULT_SCENARIOS.copy()
        self.results = []  # Store ranking results
        
        # Ranking algorithm parameters
        self.rank_cutoff_increase = 0.06
        self.rank_weight_exponent = 1.65
        self.iterations = 1  # Number of weighted iterations (7 for custom cups)
    
    def set_pokemon_list(self, pokemon_list: List[Pokemon]):
        """Set the list of Pokemon to rank."""
        self.pokemon_list = pokemon_list
        if not self.targets:
            self.targets = pokemon_list.copy()
    
    def set_targets(self, targets: List[Pokemon]):
        """Set the list of Pokemon to rank against (meta)."""
        self.targets = targets
    
    def set_scenarios(self, scenarios: List):
        """Set custom ranking scenarios. Can accept RankingScenario objects or dicts."""
        converted_scenarios = []
        for scenario in scenarios:
            if isinstance(scenario, dict):
                # Convert dict to RankingScenario
                converted_scenarios.append(RankingScenario(
                    slug=scenario.get('slug', 'custom'),
                    shields=scenario.get('shields', [0, 0]),
                    energy=scenario.get('energy', [0, 0])
                ))
            else:
                converted_scenarios.append(scenario)
        self.scenarios = converted_scenarios
    
    def set_iterations(self, iterations: int):
        """Set number of weighted iterations."""
        self.iterations = iterations
    
    def calculate_battle_rating(self, attacker: Pokemon, defender: Pokemon, 
                              battle_result) -> Tuple[int, int]:
        """
        Calculate battle rating based on health and damage dealt.
        
        Args:
            attacker: Attacking Pokemon
            defender: Defending Pokemon
            battle_result: Result from battle simulation
            
        Returns:
            Tuple of (attacker_rating, defender_rating)
        """
        # Calculate current stats
        attacker_stats = attacker.calculate_stats()
        defender_stats = defender.calculate_stats()
        
        # Health rating: remaining HP as percentage
        attacker_health_rating = attacker.current_hp / attacker_stats.hp
        defender_health_rating = defender.current_hp / defender_stats.hp
        
        # Damage rating: damage dealt as percentage of opponent's total HP
        attacker_damage_rating = (defender_stats.hp - defender.current_hp) / defender_stats.hp
        defender_damage_rating = (attacker_stats.hp - attacker.current_hp) / attacker_stats.hp
        
        # Battle rating combines health remaining and damage dealt
        attacker_rating = int((attacker_health_rating + attacker_damage_rating) * 500)
        defender_rating = int((defender_health_rating + defender_damage_rating) * 500)
        
        # Apply win/loss multipliers
        win_multiplier = 1
        op_win_multiplier = 1
        
        if attacker_rating > defender_rating:
            op_win_multiplier = 0
        elif defender_rating > attacker_rating:
            win_multiplier = 0
        else:  # Tie
            win_multiplier = 0
            op_win_multiplier = 0
        
        # Adjust ratings based on shields and other factors
        # This is a simplified version - the original has more complex shield calculations
        
        return attacker_rating, defender_rating
    
    def rank_scenario(self, scenario: RankingScenario) -> List[Dict]:
        """
        Rank Pokemon for a specific scenario.
        
        Args:
            scenario: The ranking scenario to use
            
        Returns:
            List of ranking results for this scenario
        """
        rankings = []
        
        for i, pokemon in enumerate(self.pokemon_list):
            matchups = []
            total_rating = 0
            
            # Battle against all targets
            for target in self.targets:
                # Skip self-matchups (compare by object identity to handle duplicates)
                if pokemon is target or pokemon.species_id == target.species_id:
                    continue
                
                # Set up battle conditions
                pokemon.shields = scenario.shields[0]
                target.shields = scenario.shields[1]
                
                # Set energy advantage (simplified - original uses fast move calculations)
                if scenario.energy[0] > 0:
                    # Calculate energy from turns of advantage
                    fast_move_count = max(1, int((scenario.energy[0] * 500) / pokemon.fast_move.cooldown))
                    pokemon.start_energy = min(pokemon.fast_move.energy_gain * fast_move_count, 100)
                else:
                    pokemon.start_energy = 0
                    
                if scenario.energy[1] > 0:
                    fast_move_count = max(1, int((scenario.energy[1] * 500) / target.fast_move.cooldown))
                    target.start_energy = min(target.fast_move.energy_gain * fast_move_count, 100)
                else:
                    target.start_energy = 0
                
                # Run battle
                battle = Battle(pokemon, target)
                result = battle.simulate()
                
                # Calculate battle ratings
                attacker_rating, defender_rating = self.calculate_battle_rating(
                    pokemon, target, result
                )
                
                total_rating += attacker_rating
                
                matchups.append({
                    "opponent": target.species_id,
                    "rating": attacker_rating,
                    "opRating": defender_rating
                })
                
                # Reset Pokemon for next battle
                pokemon.reset()
                target.reset()
            
            # Calculate average rating
            avg_rating = total_rating / len(matchups) if matchups else 500
            
            rankings.append({
                "speciesId": pokemon.species_id,
                "speciesName": pokemon.species_name,
                "rating": avg_rating,
                "matches": matchups,
                "scores": [avg_rating]  # Will be updated in weighted iterations
            })
        
        # Apply weighted iterations
        rankings = self.apply_weighted_iterations(rankings, scenario)
        
        return rankings
    
    def apply_weighted_iterations(self, rankings: List[Dict], 
                                scenario: RankingScenario) -> List[Dict]:
        """
        Apply weighted iterations to the rankings.
        
        Args:
            rankings: Initial rankings
            scenario: The ranking scenario
            
        Returns:
            Updated rankings after weighted iterations
        """
        if not rankings:
            return rankings
            
        for iteration in range(self.iterations):
            # Find the best score in this iteration
            best_score = max(ranking["scores"][iteration] for ranking in rankings)
            
            for i, ranking in enumerate(rankings):
                total_score = 0
                total_weights = 0
                
                for j, match in enumerate(ranking["matches"]):
                    # Calculate weight based on opponent's strength
                    opponent_score = rankings[j]["scores"][iteration] if j < len(rankings) else 500
                    
                    # Weight calculation from original algorithm
                    weight = 1
                    if len(self.pokemon_list) == len(self.targets):
                        weight_base = max((opponent_score / best_score) - (0.1 + (self.rank_cutoff_increase * iteration)), 0)
                        weight = pow(weight_base, self.rank_weight_exponent)
                    
                    # Don't score Pokemon against themselves
                    if i == j:
                        weight = 0
                    
                    # Apply scoring adjustments from original algorithm
                    adj_rating = match["rating"]
                    
                    # Soft cap for wins over 700
                    if adj_rating > 700:
                        adj_rating = 700 + pow(adj_rating - 700, 0.5)
                    
                    # Harsh curve for losses under 300
                    if adj_rating < 300:
                        curve_adjustment = 300
                        adj_rating = pow(300, (curve_adjustment + adj_rating) / (300 + curve_adjustment))
                    
                    # Special handling for switches scenario
                    if scenario.slug == "switches" and adj_rating < 500:
                        weight *= (1 + (pow(500 - adj_rating, 2) / 20000))
                    
                    # Apply cutoff
                    if opponent_score / best_score < 0.1 + (self.rank_cutoff_increase * iteration):
                        weight = 0
                    
                    total_weights += weight
                    total_score += adj_rating * weight
                
                # Calculate weighted average
                if total_weights > 0:
                    weighted_score = total_score / total_weights
                else:
                    weighted_score = ranking["scores"][iteration]
                
                ranking["scores"].append(weighted_score)
        
        # Update final scores and sort
        for ranking in rankings:
            ranking["score"] = ranking["scores"][-1]  # Use final iteration score
        
        rankings.sort(key=lambda x: x["score"], reverse=True)
        
        return rankings
    
    def rank_all_scenarios(self) -> Dict[str, List[Dict]]:
        """
        Rank Pokemon across all scenarios.
        
        Returns:
            Dictionary mapping scenario names to ranking results
        """
        all_rankings = {}
        
        for scenario in self.scenarios:
            rankings = self.rank_scenario(scenario)
            all_rankings[scenario.slug] = rankings
        
        return all_rankings
    
    def calculate_overall_rankings(self, scenario_rankings: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Calculate overall rankings using geometric mean of scenario scores.
        
        Args:
            scenario_rankings: Rankings for each scenario
            
        Returns:
            Overall rankings
        """
        # Combine all scenario rankings
        pokemon_scores = {}
        
        for scenario_name, rankings in scenario_rankings.items():
            for ranking in rankings:
                species_id = ranking["speciesId"]
                if species_id not in pokemon_scores:
                    pokemon_scores[species_id] = {
                        "speciesId": species_id,
                        "speciesName": ranking["speciesName"],
                        "scores": [],
                        "scenario_scores": {},
                        "all_matchups": []  # Collect all matchups across scenarios
                    }
                
                # Normalize score to percentage of #1 Pokemon
                max_score = max(r["score"] for r in rankings)
                normalized_score = (ranking["score"] / max_score) * 100 if max_score > 0 else 0
                
                pokemon_scores[species_id]["scores"].append(normalized_score)
                pokemon_scores[species_id]["scenario_scores"][scenario_name] = normalized_score
                
                # Collect matchups from this scenario
                if "matches" in ranking:
                    pokemon_scores[species_id]["all_matchups"].extend(ranking["matches"])
        
        # Calculate overall scores using geometric mean with weighting
        overall_rankings = []
        
        for species_id, data in pokemon_scores.items():
            scores = data["scores"]
            
            if len(scores) >= 5:  # All scenarios present
                # Sort scores for weighted geometric mean
                sorted_scores = sorted(scores, reverse=True)
                
                # Calculate consistency score (simplified)
                consistency_score = min(scores) / max(scores) * 100 if max(scores) > 0 else 0
                
                # Weighted geometric mean calculation from original algorithm
                # Top scores weighted more heavily
                overall_score = pow(
                    pow(sorted_scores[0], 12) * 
                    pow(sorted_scores[1], 6) * 
                    pow(max(sorted_scores[2], sorted_scores[3]), 4) * 
                    pow(sorted_scores[4], 2) * 
                    pow(consistency_score, 2),
                    1/26
                )
                
                # Apply additional weighting for low scores
                if sorted_scores[4] <= 75 and consistency_score <= 75:
                    overall_score = pow(
                        pow(overall_score, 14) * 
                        pow(sorted_scores[4], 1) * 
                        pow(consistency_score, 1),
                        1/16
                    )
                
                # Calculate top matchups and counters from all matchups
                matchups, counters = self._calculate_top_matchups_and_counters(data["all_matchups"])
                
                # Scale score back to 0-1000 range (from 0-100)
                # Special case: if no matchups (empty list), keep default score of 500
                if len(data["all_matchups"]) == 0:
                    scaled_score = 500
                else:
                    scaled_score = overall_score * 10
                
                overall_rankings.append({
                    "speciesId": species_id,
                    "speciesName": data["speciesName"],
                    "score": round(scaled_score, 1),
                    "scores": scores,
                    "scenario_scores": data["scenario_scores"],
                    "matchups": matchups,
                    "counters": counters
                })
            elif len(scores) > 0:
                # Handle cases with fewer scenarios - use simple average
                overall_score = sum(scores) / len(scores)
                matchups, counters = self._calculate_top_matchups_and_counters(data["all_matchups"])
                
                # Scale score back to 0-1000 range (from 0-100)
                # Special case: if no matchups (empty list), keep default score of 500
                if len(data["all_matchups"]) == 0:
                    scaled_score = 500
                else:
                    scaled_score = overall_score * 10
                
                overall_rankings.append({
                    "speciesId": species_id,
                    "speciesName": data["speciesName"],
                    "score": round(scaled_score, 1),
                    "scores": scores,
                    "scenario_scores": data["scenario_scores"],
                    "matchups": matchups,
                    "counters": counters
                })
        
        # Sort by overall score
        overall_rankings.sort(key=lambda x: x["score"], reverse=True)
        
        return overall_rankings
    
    def _calculate_top_matchups_and_counters(self, all_matchups: List[Dict], limit: int = 5) -> Tuple[List[Dict], List[Dict]]:
        """
        Calculate top matchups (wins) and counters (losses) from all matchups.
        
        Args:
            all_matchups: List of all matchup results
            limit: Maximum number of matchups/counters to return
            
        Returns:
            Tuple of (top_matchups, top_counters)
        """
        # Aggregate matchups by opponent
        opponent_ratings = {}
        for matchup in all_matchups:
            opponent = matchup["opponent"]
            if opponent not in opponent_ratings:
                opponent_ratings[opponent] = {"rating": 0, "opRating": 0, "count": 0}
            opponent_ratings[opponent]["rating"] += matchup["rating"]
            opponent_ratings[opponent]["opRating"] += matchup["opRating"]
            opponent_ratings[opponent]["count"] += 1
        
        # Calculate average ratings
        matchup_list = []
        for opponent, data in opponent_ratings.items():
            avg_rating = data["rating"] / data["count"]
            avg_op_rating = data["opRating"] / data["count"]
            matchup_list.append({
                "opponent": opponent,
                "rating": avg_rating,
                "opRating": avg_op_rating
            })
        
        # Sort by rating (descending for matchups, ascending for counters)
        matchup_list.sort(key=lambda x: x["rating"], reverse=True)
        
        # Top matchups are the best wins (rating > 500)
        wins = [m for m in matchup_list if m["rating"] > 500]
        top_matchups = wins[:limit]
        
        # Counters are the worst losses (rating < 500)
        losses = [m for m in matchup_list if m["rating"] < 500]
        losses.sort(key=lambda x: x["rating"])  # Sort ascending for worst losses
        top_counters = losses[:limit]
        
        return top_matchups, top_counters
    
    def rank(self, scenarios: Optional[List[RankingScenario]] = None) -> List[Dict]:
        """
        Run complete ranking calculations.
        
        Args:
            scenarios: Custom scenarios to use (optional)
            
        Returns:
            List of overall ranking results
        """
        if not self.pokemon_list:
            return []
            
        if scenarios:
            self.set_scenarios(scenarios)
        
        # Rank all scenarios
        scenario_rankings = self.rank_all_scenarios()
        
        # Calculate overall rankings
        overall_rankings = self.calculate_overall_rankings(scenario_rankings)
        
        # Store results for later access
        self.results = {
            "overall": overall_rankings,
            "scenarios": scenario_rankings
        }
        
        return overall_rankings
    
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
                
                attacker_rating, _ = self.calculate_battle_rating(attacker, defender, result)
                matrix[attacker.species_id][defender.species_id] = attacker_rating
        
        return matrix
