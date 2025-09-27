"""Battle AI for decision making."""

from typing import Optional, Dict, List
from ..core.pokemon import Pokemon
from ..core.moves import FastMove, ChargedMove
from .damage_calculator import DamageCalculator


class BattleAI:
    """
    AI for making battle decisions.
    This is a simplified version - full implementation will port the JavaScript AI logic.
    """
    
    @staticmethod
    def decide_action(attacker: Pokemon, defender: Pokemon, 
                     battle_context: Optional[Dict] = None) -> Dict:
        """
        Decide the best action for a Pokemon.
        
        Args:
            attacker: Pokemon making the decision
            defender: Opponent Pokemon
            battle_context: Additional battle context (shields, time, etc.)
            
        Returns:
            Action dictionary with type and move
        """
        # Default context
        if battle_context is None:
            battle_context = {
                "attacker_shields": attacker.shields,
                "defender_shields": defender.shields,
                "time_remaining": 240
            }
        
        # Check if we can use a charged move
        best_charged = BattleAI.select_charged_move(attacker, defender, battle_context)
        
        if best_charged:
            return {
                "type": "charged",
                "move": best_charged,
                "target": 0  # Will be set by battle
            }
        
        # Use fast move
        return {
            "type": "fast", 
            "move": attacker.fast_move,
            "target": 0
        }
    
    @staticmethod
    def select_charged_move(attacker: Pokemon, defender: Pokemon,
                           battle_context: Dict) -> Optional[ChargedMove]:
        """
        Select the best charged move to use.
        
        Args:
            attacker: Pokemon selecting move
            defender: Opponent Pokemon
            battle_context: Battle context
            
        Returns:
            Best charged move or None if shouldn't use one
        """
        available_moves = []
        
        # Check which moves have enough energy
        if attacker.charged_move_1 and attacker.energy >= attacker.charged_move_1.energy_cost:
            available_moves.append(attacker.charged_move_1)
        
        if attacker.charged_move_2 and attacker.energy >= attacker.charged_move_2.energy_cost:
            available_moves.append(attacker.charged_move_2)
        
        if not available_moves:
            return None
        
        # Simple selection: choose move with best damage per energy
        best_move = None
        best_efficiency = 0
        
        for move in available_moves:
            damage = DamageCalculator.calculate_damage(attacker, defender, move)
            efficiency = damage / move.energy_cost
            
            # Penalize self-debuffing moves
            if move.is_self_debuffing:
                efficiency *= 0.8
            
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_move = move
        
        return best_move
    
    @staticmethod
    def should_shield(attacker: Pokemon, defender: Pokemon, 
                     incoming_move: ChargedMove, shields_remaining: int) -> bool:
        """
        Decide whether to shield an incoming charged move.
        
        Args:
            attacker: Pokemon using the move
            defender: Pokemon deciding to shield
            incoming_move: The charged move being used
            shields_remaining: Number of shields available
            
        Returns:
            True if should shield
        """
        if shields_remaining <= 0:
            return False
        
        # Calculate potential damage
        damage = DamageCalculator.calculate_damage(attacker, defender, incoming_move)
        
        defender_stats = defender.calculate_stats()
        damage_percent = damage / defender_stats.hp
        
        # Simple heuristic: shield if damage > 50% of max HP
        if damage_percent > 0.5:
            return True
        
        # Shield if it would KO
        if damage >= defender.current_hp:
            return True
        
        return False
    
    @staticmethod
    def evaluate_matchup(pokemon1: Pokemon, pokemon2: Pokemon,
                        shields1: int = 2, shields2: int = 2) -> float:
        """
        Evaluate a matchup and return a score.
        
        Args:
            pokemon1: First Pokemon
            pokemon2: Second Pokemon
            shields1: Shields for Pokemon 1
            shields2: Shields for Pokemon 2
            
        Returns:
            Score from 0-1000 (500 = even matchup)
        """
        # This is a placeholder - full implementation would run simulations
        # For now, just compare stat products
        
        stats1 = pokemon1.calculate_stats()
        stats2 = pokemon2.calculate_stats()
        
        product1 = stats1.atk * stats1.defense * stats1.hp
        product2 = stats2.atk * stats2.defense * stats2.hp
        
        # Type effectiveness check
        effectiveness_score = 1.0
        
        # Simple scoring based on stat product ratio
        ratio = product1 / product2 if product2 > 0 else 1.0
        score = 500 * ratio
        
        return min(1000, max(0, score))
