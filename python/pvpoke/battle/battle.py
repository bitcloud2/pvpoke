"""Battle simulation engine."""

from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum
from ..core.pokemon import Pokemon
from ..core.moves import Move, FastMove, ChargedMove
from .damage_calculator import DamageCalculator


class BattlePhase(Enum):
    """Phases of battle."""
    COUNTDOWN = "countdown"
    NEUTRAL = "neutral"
    SUSPEND_CHARGED = "suspend_charged"
    ANIMATE_CHARGED = "animate_charged"


@dataclass
class BattleResult:
    """Results of a battle simulation."""
    winner: int  # 0 or 1 for winner index
    pokemon1_hp: int
    pokemon2_hp: int
    rating1: int  # Battle rating for Pokemon 1
    rating2: int  # Battle rating for Pokemon 2
    turns: int
    time_remaining: float
    timeline: List[Dict] = field(default_factory=list)


class Battle:
    """
    Main battle simulation class.
    Handles turn-based combat between two Pokemon.
    """
    
    def __init__(self, pokemon1: Optional[Pokemon] = None, 
                 pokemon2: Optional[Pokemon] = None):
        """
        Initialize a battle between two Pokemon.
        
        Args:
            pokemon1: First Pokemon
            pokemon2: Second Pokemon
        """
        self.pokemon = [pokemon1, pokemon2]
        self.cp_limit = 1500  # Default to Great League
        self.time_limit = 240000  # 4 minutes in milliseconds
        self.turn_duration = 500  # 500ms per turn
        
        # Battle state
        self.current_time = 0
        self.current_turn = 0
        self.phase = BattlePhase.NEUTRAL
        self.timeline = []
        
        # Move cooldowns and energy
        self.cooldowns = [0, 0]
        self.queued_moves = [None, None]
        
    def set_pokemon(self, pokemon: Pokemon, index: int):
        """Set a Pokemon for battle."""
        if index not in [0, 1]:
            raise ValueError("Index must be 0 or 1")
        self.pokemon[index] = pokemon
        if pokemon:
            pokemon.reset()
    
    def simulate(self, log_timeline: bool = False) -> BattleResult:
        """
        Run a full battle simulation.
        
        Args:
            log_timeline: Whether to record detailed timeline
            
        Returns:
            BattleResult with battle outcome
        """
        # Validate Pokemon are set
        if not all(self.pokemon):
            raise ValueError("Both Pokemon must be set before simulation")
        
        # Reset battle state
        self.reset()
        
        # Main battle loop
        while self.current_time < self.time_limit:
            self.process_turn(log_timeline)
            
            # Check for faints
            if self.pokemon[0].current_hp <= 0 or self.pokemon[1].current_hp <= 0:
                break
            
            self.current_time += self.turn_duration
            self.current_turn += 1
        
        # Determine winner and ratings
        winner = 0 if self.pokemon[0].current_hp > 0 else 1
        
        rating1 = DamageCalculator.get_duel_rating(
            self.pokemon[0], self.pokemon[1],
            self.pokemon[0].current_hp, self.pokemon[1].current_hp
        )
        rating2 = 1000 - rating1
        
        return BattleResult(
            winner=winner,
            pokemon1_hp=self.pokemon[0].current_hp,
            pokemon2_hp=self.pokemon[1].current_hp,
            rating1=rating1,
            rating2=rating2,
            turns=self.current_turn,
            time_remaining=(self.time_limit - self.current_time) / 1000,
            timeline=self.timeline if log_timeline else []
        )
    
    def process_turn(self, log_timeline: bool = False):
        """Process a single turn of combat."""
        for i in range(2):
            if self.cooldowns[i] <= 0:
                # Pokemon can act
                action = self.decide_action(i)
                self.execute_action(i, action, log_timeline)
            else:
                # Reduce cooldown
                self.cooldowns[i] -= 1
    
    def decide_action(self, pokemon_index: int) -> Dict:
        """
        Decide what action a Pokemon should take.
        For now, uses simple logic. Will be enhanced with AI.
        """
        pokemon = self.pokemon[pokemon_index]
        opponent_index = 1 - pokemon_index
        
        # Check if can use charged move
        if pokemon.charged_move_1 and pokemon.energy >= pokemon.charged_move_1.energy_cost:
            return {
                "type": "charged",
                "move": pokemon.charged_move_1,
                "target": opponent_index
            }
        
        # Use fast move
        return {
            "type": "fast",
            "move": pokemon.fast_move,
            "target": opponent_index
        }
    
    def execute_action(self, pokemon_index: int, action: Dict, log_timeline: bool):
        """Execute a Pokemon's action."""
        if not action:
            return
        
        attacker = self.pokemon[pokemon_index]
        defender = self.pokemon[action["target"]]
        move = action["move"]
        
        if action["type"] == "fast":
            # Execute fast move
            damage, energy = DamageCalculator.calculate_fast_move_damage(
                attacker, defender, move
            )
            defender.current_hp = max(0, defender.current_hp - damage)
            attacker.energy = min(100, attacker.energy + energy)
            self.cooldowns[pokemon_index] = move.turns - 1
            
            if log_timeline:
                self.timeline.append({
                    "turn": self.current_turn,
                    "time": self.current_time,
                    "attacker": pokemon_index,
                    "action": "fast",
                    "move": move.move_id,
                    "damage": damage,
                    "energy": energy
                })
        
        elif action["type"] == "charged":
            # Execute charged move
            damage = DamageCalculator.calculate_charged_move_damage(
                attacker, defender, move, defender.shields
            )
            
            if defender.shields > 0:
                defender.shields -= 1
                damage = 1
            
            defender.current_hp = max(0, defender.current_hp - damage)
            attacker.energy -= move.energy_cost
            
            # Apply buffs/debuffs
            if move.buff_chance >= 1.0 or self.should_apply_buff(move.buff_chance):
                self.apply_buffs(pokemon_index, move)
            
            if log_timeline:
                self.timeline.append({
                    "turn": self.current_turn,
                    "time": self.current_time,
                    "attacker": pokemon_index,
                    "action": "charged",
                    "move": move.move_id,
                    "damage": damage,
                    "shielded": damage == 1
                })
    
    def apply_buffs(self, pokemon_index: int, move: ChargedMove):
        """Apply stat buffs/debuffs from a move."""
        if move.buff_target == "self":
            target = self.pokemon[pokemon_index]
        else:
            target = self.pokemon[1 - pokemon_index]
        
        # Apply attack buff
        if move.buffs[0] != 1.0:
            stages = self.get_buff_stages(move.buffs[0])
            target.stat_buffs[0] = max(-4, min(4, target.stat_buffs[0] + stages))
        
        # Apply defense buff  
        if move.buffs[1] != 1.0:
            stages = self.get_buff_stages(move.buffs[1])
            target.stat_buffs[1] = max(-4, min(4, target.stat_buffs[1] + stages))
    
    def get_buff_stages(self, multiplier: float) -> int:
        """Convert buff multiplier to stages."""
        if multiplier >= 2.0:
            return 2
        elif multiplier >= 1.5:
            return 1
        elif multiplier <= 0.5:
            return -2
        elif multiplier <= 0.75:
            return -1
        return 0
    
    def should_apply_buff(self, chance: float) -> bool:
        """Determine if a buff should apply based on chance."""
        import random
        return random.random() < chance
    
    def reset(self):
        """Reset battle to initial state."""
        self.current_time = 0
        self.current_turn = 0
        self.phase = BattlePhase.NEUTRAL
        self.timeline = []
        self.cooldowns = [0, 0]
        self.queued_moves = [None, None]
        
        for pokemon in self.pokemon:
            if pokemon:
                pokemon.reset()
