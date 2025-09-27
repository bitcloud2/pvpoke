"""Team ranking and composition analysis."""

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
    
    def rank_team(self, team: List[Pokemon], opponents: List[Pokemon]) -> Dict:
        """
        Rank a team against a list of opponents.
        
        Args:
            team: List of 3 Pokemon forming a team
            opponents: List of opponent Pokemon to test against
            
        Returns:
            Team ranking results
        """
        if len(team) != 3:
            raise ValueError("Team must contain exactly 3 Pokemon")
        
        team_scores = []
        coverage_matrix = {}
        
        for team_member in team:
            member_scores = []
            coverage_matrix[team_member.species_id] = {}
            
            for opponent in opponents:
                battle = Battle(team_member, opponent)
                result = battle.simulate()
                
                member_scores.append(result.rating1)
                coverage_matrix[team_member.species_id][opponent.species_id] = result.rating1
            
            avg_score = sum(member_scores) / len(member_scores) if member_scores else 500
            team_scores.append(avg_score)
        
        # Calculate team coverage
        team_coverage = self.calculate_coverage(coverage_matrix, opponents)
        
        return {
            "team": [p.species_id for p in team],
            "average_score": sum(team_scores) / len(team_scores),
            "individual_scores": team_scores,
            "coverage": team_coverage,
            "coverage_matrix": coverage_matrix
        }
    
    def calculate_coverage(self, coverage_matrix: Dict, opponents: List[Pokemon]) -> Dict:
        """
        Calculate team coverage metrics.
        
        Args:
            coverage_matrix: Matrix of matchup scores
            opponents: List of opponents
            
        Returns:
            Coverage metrics
        """
        covered = 0
        threats = []
        
        for opponent in opponents:
            best_matchup = 0
            best_counter = None
            
            for team_member, matchups in coverage_matrix.items():
                score = matchups.get(opponent.species_id, 0)
                if score > best_matchup:
                    best_matchup = score
                    best_counter = team_member
            
            if best_matchup >= 500:
                covered += 1
            else:
                threats.append({
                    "species": opponent.species_id,
                    "best_matchup": best_matchup,
                    "best_counter": best_counter
                })
        
        coverage_percent = (covered / len(opponents)) * 100 if opponents else 0
        
        return {
            "coverage_percent": coverage_percent,
            "covered_count": covered,
            "threat_count": len(threats),
            "top_threats": sorted(threats, key=lambda x: x["best_matchup"])[:5]
        }
    
    def suggest_teammate(self, current_team: List[Pokemon], 
                        candidates: List[Pokemon],
                        opponents: List[Pokemon]) -> List[Tuple[Pokemon, float]]:
        """
        Suggest the best teammate to add to a team.
        
        Args:
            current_team: Current team members (1-2 Pokemon)
            candidates: List of candidate Pokemon to choose from
            opponents: List of opponents to test against
            
        Returns:
            List of (Pokemon, score) tuples, sorted by score
        """
        if len(current_team) >= 3:
            raise ValueError("Team is already complete")
        
        suggestions = []
        
        # Find current team weaknesses
        current_coverage = {}
        for member in current_team:
            for opponent in opponents:
                battle = Battle(member, opponent)
                result = battle.simulate()
                
                if opponent.species_id not in current_coverage:
                    current_coverage[opponent.species_id] = result.rating1
                else:
                    current_coverage[opponent.species_id] = max(
                        current_coverage[opponent.species_id],
                        result.rating1
                    )
        
        # Test each candidate
        for candidate in candidates:
            # Skip if already on team
            if any(candidate.species_id == m.species_id for m in current_team):
                continue
            
            improvement = 0
            
            for opponent in opponents:
                current_best = current_coverage.get(opponent.species_id, 0)
                
                battle = Battle(candidate, opponent)
                result = battle.simulate()
                
                if result.rating1 > current_best:
                    improvement += (result.rating1 - current_best)
            
            suggestions.append((candidate, improvement))
        
        # Sort by improvement score
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:10]  # Return top 10 suggestions
