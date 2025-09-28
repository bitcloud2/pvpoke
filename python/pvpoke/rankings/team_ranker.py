"""Team ranking and composition analysis."""

import math
from typing import List, Dict, Optional, Tuple
from ..core.pokemon import Pokemon
from ..battle.battle import Battle


class TeamRanker:
    """
    Analyze team compositions and synergy.
    This is a simplified version - full implementation will port the JavaScript team ranking logic.
    """
    
    def __init__(self, cp_limit: int = 1500):
        """
        Initialize team ranker.
        
        Args:
            cp_limit: CP limit for the league
        """
        self.cp_limit = cp_limit
    
    def rank_team(self, team: List[Pokemon], opponents: List[Pokemon], 
                 shield_mode: str = "average", context: str = "team-builder") -> Dict:
        """
        Rank a team against a list of opponents using the complete algorithm.
        
        Args:
            team: List of 3 Pokemon forming a team
            opponents: List of opponent Pokemon to test against
            shield_mode: How to handle shield scenarios ("average", "single")
            context: Context for ranking ("team-builder", "battle", "matrix")
            
        Returns:
            Team ranking results
        """
        if len(team) != 3:
            raise ValueError("Team must contain exactly 3 Pokemon")
        
        rankings = []
        team_ratings = [[] for _ in range(len(team))]
        csv_data = ""
        
        # Shield test scenarios
        if shield_mode == "average":
            shield_scenarios = [[1, 1], [0, 0]]  # [opponent_shields, pokemon_shields]
        else:
            shield_scenarios = [[1, 1]]  # Single scenario
        
        # Rank each team member against all opponents
        for i, pokemon in enumerate(team):
            avg_rating = 0
            opponent_rating = 0
            matchups = []
            
            for opponent in opponents:
                # Skip self-matchups
                if pokemon.species_id == opponent.species_id:
                    continue
                
                shield_ratings = []
                
                # Test different shield scenarios
                for shields in shield_scenarios:
                    pokemon.shields = shields[1]
                    opponent.shields = shields[0]
                    
                    # Run battle
                    battle = Battle(pokemon, opponent)
                    result = battle.simulate()
                    
                    # Calculate battle ratings
                    pokemon_stats = pokemon.calculate_stats()
                    opponent_stats = opponent.calculate_stats()
                    
                    health_rating = pokemon.current_hp / pokemon_stats.hp
                    damage_rating = (opponent_stats.hp - opponent.current_hp) / opponent_stats.hp
                    
                    op_health_rating = opponent.current_hp / opponent_stats.hp
                    op_damage_rating = (pokemon_stats.hp - pokemon.current_hp) / pokemon_stats.hp
                    
                    rating = int((health_rating + damage_rating) * 500)
                    op_rating = int((op_health_rating + op_damage_rating) * 500)
                    
                    shield_ratings.append(rating)
                    
                    # Reset Pokemon for next battle
                    pokemon.reset()
                    opponent.reset()
                
                # Calculate average rating across shield scenarios
                if len(shield_ratings) > 1:
                    # Weighted average favoring 2-shield scenario
                    avg_pokemon_rating = round(pow(shield_ratings[0] * pow(shield_ratings[1], 3), 1/4))
                else:
                    avg_pokemon_rating = shield_ratings[0]
                
                avg_rating += avg_pokemon_rating
                
                # Calculate matchup score with alternative scoring
                score = 500
                alternative_score = 500
                
                if avg_pokemon_rating > 500:
                    alternative_score = avg_pokemon_rating
                    score = 500 + pow(avg_pokemon_rating - 500, 0.75)
                else:
                    score = avg_pokemon_rating / 2
                    alternative_score = avg_pokemon_rating / 2
                
                matchups.append({
                    "opponent": opponent.species_id,
                    "rating": avg_pokemon_rating,
                    "score": score,
                    "alternativeScore": alternative_score
                })
            
            # Calculate final ratings
            if matchups:
                avg_rating = int(avg_rating / len(matchups))
                matchup_score = sum(m["score"] for m in matchups) / len(matchups)
                matchup_alt_score = sum(m["alternativeScore"] for m in matchups) / len(matchups)
            else:
                avg_rating = 500
                matchup_score = 500
                matchup_alt_score = 500
            
            team_ratings[i] = [m["rating"] for m in matchups]
            team_ratings[i].sort(reverse=True)
            
            rankings.append({
                "speciesId": pokemon.species_id,
                "speciesName": pokemon.species_name,
                "rating": avg_rating,
                "score": matchup_score,
                "matchupAltScore": matchup_alt_score,
                "matchups": matchups
            })
        
        # Sort rankings based on context
        if context in ["team-builder", "team-counters"]:
            rankings.sort(key=lambda x: x["score"], reverse=True)
        elif context == "battle":
            rankings.sort(key=lambda x: x["rating"])
        
        # Calculate team coverage
        coverage_matrix = {}
        for i, member in enumerate(rankings):
            coverage_matrix[member["speciesId"]] = {
                m["opponent"]: m["rating"] for m in member["matchups"]
            }
        
        team_coverage = self.calculate_coverage(coverage_matrix, opponents)
        
        return {
            "rankings": rankings,
            "teamRatings": team_ratings,
            "coverage": team_coverage,
            "csv": csv_data
        }
    
    def calculate_coverage(self, coverage_matrix: Dict, opponents: List[Pokemon]) -> Dict:
        """
        Calculate team coverage metrics with enhanced analysis.
        
        Args:
            coverage_matrix: Matrix of matchup scores
            opponents: List of opponents
            
        Returns:
            Coverage metrics
        """
        covered = 0
        threats = []
        safe_switches = 0
        
        for opponent in opponents:
            best_matchup = 0
            best_counter = None
            safe_switch_count = 0
            
            for team_member, matchups in coverage_matrix.items():
                score = matchups.get(opponent.species_id, 0)
                if score > best_matchup:
                    best_matchup = score
                    best_counter = team_member
                
                # Count safe switches (rating >= 450)
                if score >= 450:
                    safe_switch_count += 1
            
            if best_matchup >= 500:
                covered += 1
            else:
                threats.append({
                    "species": opponent.species_id,
                    "best_matchup": best_matchup,
                    "best_counter": best_counter,
                    "safe_switches": safe_switch_count
                })
            
            if safe_switch_count >= 2:
                safe_switches += 1
        
        coverage_percent = (covered / len(opponents)) * 100 if opponents else 0
        safe_switch_percent = (safe_switches / len(opponents)) * 100 if opponents else 0
        
        return {
            "coverage_percent": coverage_percent,
            "covered_count": covered,
            "threat_count": len(threats),
            "safe_switch_percent": safe_switch_percent,
            "safe_switch_count": safe_switches,
            "top_threats": sorted(threats, key=lambda x: x["best_matchup"])[:5]
        }
    
    def suggest_teammate(self, current_team: List[Pokemon], 
                        candidates: List[Pokemon],
                        opponents: List[Pokemon],
                        meta_weights: Optional[Dict[str, float]] = None) -> List[Tuple[Pokemon, float]]:
        """
        Suggest the best teammate to add to a team with advanced scoring.
        
        Args:
            current_team: Current team members (1-2 Pokemon)
            candidates: List of candidate Pokemon to choose from
            opponents: List of opponents to test against
            meta_weights: Optional weights for meta relevance
            
        Returns:
            List of (Pokemon, score) tuples, sorted by score
        """
        if len(current_team) >= 3:
            raise ValueError("Team is already complete")
        
        suggestions = []
        
        # Calculate current team coverage
        current_coverage = {}
        current_weaknesses = []
        
        for opponent in opponents:
            best_rating = 0
            
            for member in current_team:
                battle = Battle(member, opponent)
                result = battle.simulate()
                
                # Calculate battle rating
                member_stats = member.calculate_stats()
                opponent_stats = opponent.calculate_stats()
                
                health_rating = member.current_hp / member_stats.hp
                damage_rating = (opponent_stats.hp - opponent.current_hp) / opponent_stats.hp
                rating = int((health_rating + damage_rating) * 500)
                
                if rating > best_rating:
                    best_rating = rating
                
                member.reset()
                opponent.reset()
            
            current_coverage[opponent.species_id] = best_rating
            
            # Identify weaknesses (losses or close matches)
            if best_rating < 500:
                weakness_severity = 500 - best_rating
                current_weaknesses.append({
                    "opponent": opponent.species_id,
                    "severity": weakness_severity,
                    "meta_weight": meta_weights.get(opponent.species_id, 1.0) if meta_weights else 1.0
                })
        
        # Test each candidate
        for candidate in candidates:
            # Skip if already on team
            if any(candidate.species_id == m.species_id for m in current_team):
                continue
            
            total_improvement = 0
            coverage_improvement = 0
            synergy_score = 0
            
            for opponent in opponents:
                current_best = current_coverage.get(opponent.species_id, 0)
                
                # Test candidate against opponent
                battle = Battle(candidate, opponent)
                result = battle.simulate()
                
                # Calculate battle rating
                candidate_stats = candidate.calculate_stats()
                opponent_stats = opponent.calculate_stats()
                
                health_rating = candidate.current_hp / candidate_stats.hp
                damage_rating = (opponent_stats.hp - opponent.current_hp) / opponent_stats.hp
                candidate_rating = int((health_rating + damage_rating) * 500)
                
                # Calculate improvement
                improvement = max(0, candidate_rating - current_best)
                
                # Weight improvement by meta relevance
                meta_weight = meta_weights.get(opponent.species_id, 1.0) if meta_weights else 1.0
                weighted_improvement = improvement * meta_weight
                
                total_improvement += weighted_improvement
                
                # Track coverage improvements (turning losses into wins)
                if current_best < 500 and candidate_rating >= 500:
                    coverage_improvement += 100 * meta_weight
                
                candidate.reset()
                opponent.reset()
            
            # Calculate type synergy with current team
            for member in current_team:
                # Simple type synergy calculation
                # Pokemon with complementary types get bonus points
                if hasattr(member, 'types') and hasattr(candidate, 'types'):
                    shared_types = set(member.types) & set(candidate.types)
                    if len(shared_types) == 0:  # No shared types = good diversity
                        synergy_score += 10
                    elif len(shared_types) == 1:  # One shared type = some overlap
                        synergy_score += 5
                    # Two shared types = too much overlap, no bonus
            
            # Calculate final score
            final_score = total_improvement + coverage_improvement + synergy_score
            
            suggestions.append((candidate, final_score))
        
        # Sort by final score
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:10]  # Return top 10 suggestions
    
    def set_shield_mode(self, mode: str):
        """Set shield testing mode."""
        self.shield_mode = mode
    
    def set_context(self, context: str):
        """Set ranking context."""
        self.context = context
    
    def analyze_team_synergy(self, team: List[Pokemon]) -> Dict:
        """
        Analyze team synergy and composition balance.
        
        Args:
            team: List of Pokemon in the team
            
        Returns:
            Synergy analysis results
        """
        if len(team) != 3:
            raise ValueError("Team must contain exactly 3 Pokemon")
        
        # Type coverage analysis
        all_types = set()
        type_counts = {}
        
        for pokemon in team:
            if hasattr(pokemon, 'types'):
                for ptype in pokemon.types:
                    all_types.add(ptype)
                    type_counts[ptype] = type_counts.get(ptype, 0) + 1
        
        # Role analysis (simplified)
        roles = {
            "lead": None,
            "safe_switch": None,
            "closer": None
        }
        
        # Assign roles based on stats and movesets (simplified)
        # This would normally be more sophisticated
        for i, pokemon in enumerate(team):
            if i == 0:
                roles["lead"] = pokemon.species_id
            elif i == 1:
                roles["safe_switch"] = pokemon.species_id
            else:
                roles["closer"] = pokemon.species_id
        
        return {
            "type_coverage": list(all_types),
            "type_counts": type_counts,
            "type_diversity": len(all_types),
            "roles": roles,
            "balance_score": min(100, len(all_types) * 10)  # Simplified balance score
        }
