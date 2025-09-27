"""Move classes and move-related data structures."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class MoveType(Enum):
    """Types of moves in Pokemon GO."""
    BUG = "bug"
    DARK = "dark"
    DRAGON = "dragon"
    ELECTRIC = "electric"
    FAIRY = "fairy"
    FIGHTING = "fighting"
    FIRE = "fire"
    FLYING = "flying"
    GHOST = "ghost"
    GRASS = "grass"
    GROUND = "ground"
    ICE = "ice"
    NORMAL = "normal"
    POISON = "poison"
    PSYCHIC = "psychic"
    ROCK = "rock"
    STEEL = "steel"
    WATER = "water"


@dataclass
class Move:
    """Base class for all moves."""
    move_id: str
    name: str
    move_type: str  # Using string for flexibility with data loading
    power: int
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.move_id}, name={self.name}, type={self.move_type}, power={self.power})"


@dataclass
class FastMove(Move):
    """Fast move with energy generation and cooldown."""
    energy_gain: int
    turns: int  # Number of turns (500ms each)
    
    @property
    def cooldown(self) -> int:
        """Get cooldown in milliseconds."""
        return self.turns * 500
    
    @property
    def dps(self) -> float:
        """Damage per second."""
        return self.power / (self.cooldown / 1000) if self.cooldown > 0 else 0
    
    @property
    def eps(self) -> float:
        """Energy per second."""
        return self.energy_gain / (self.cooldown / 1000) if self.cooldown > 0 else 0
    
    @property
    def damage(self) -> int:
        """Compatibility property for AI logic (will be set by damage calculator)."""
        return getattr(self, '_damage', self.power)
    
    def __repr__(self):
        return f"FastMove(id={self.move_id}, name={self.name}, power={self.power}, energy={self.energy_gain}, turns={self.turns})"


@dataclass
class ChargedMove(Move):
    """Charged move with energy cost and optional buffs/debuffs."""
    energy_cost: int
    
    # Buff/debuff effects [atk_change, def_change]
    buffs: List[float] = field(default_factory=lambda: [1.0, 1.0])
    buff_target: str = "self"  # "self" or "opponent"
    buff_chance: float = 1.0  # Probability of buff applying
    
    @property
    def is_self_debuffing(self) -> bool:
        """Check if move debuffs the user."""
        return self.buff_target == "self" and (self.buffs[0] < 1 or self.buffs[1] < 1)
    
    @property 
    def is_opponent_debuffing(self) -> bool:
        """Check if move debuffs the opponent."""
        return self.buff_target == "opponent" and (self.buffs[0] < 1 or self.buffs[1] < 1)
    
    @property
    def is_buffing(self) -> bool:
        """Check if move provides any buffs."""
        if self.buff_target == "self":
            return self.buffs[0] > 1 or self.buffs[1] > 1
        else:
            return False  # Opponent buffs are rare/non-existent
    
    @property
    def dpe(self) -> float:
        """Damage per energy."""
        return self.power / self.energy_cost if self.energy_cost > 0 else 0
    
    # Compatibility properties for AI logic
    @property
    def self_debuffing(self) -> bool:
        """Compatibility property for AI logic."""
        return self.is_self_debuffing
    
    @property
    def self_buffing(self) -> bool:
        """Compatibility property for AI logic."""
        return self.is_buffing
    
    @property
    def self_attack_debuffing(self) -> bool:
        """Check if move debuffs user's attack."""
        return self.buff_target == "self" and self.buffs[0] < 1
    
    @property
    def energy(self) -> int:
        """Compatibility property for AI logic."""
        return self.energy_cost
    
    @property
    def damage(self) -> int:
        """Compatibility property for AI logic (will be set by damage calculator)."""
        return getattr(self, '_damage', self.power)
    
    def __repr__(self):
        return f"ChargedMove(id={self.move_id}, name={self.name}, power={self.power}, energy={self.energy_cost})"


class TypeEffectiveness:
    """Type effectiveness chart for Pokemon GO."""
    
    # Type effectiveness multipliers
    SUPER_EFFECTIVE = 1.6
    NEUTRAL = 1.0
    NOT_VERY_EFFECTIVE = 0.625
    DOUBLE_RESIST = 0.390625  # When both types resist
    
    # Type chart: attacker_type -> {defender_type: multiplier}
    TYPE_CHART: Dict[str, Dict[str, float]] = {
        "normal": {"rock": 0.625, "ghost": 0.390625, "steel": 0.625},
        "fighting": {"normal": 1.6, "flying": 0.625, "poison": 0.625, "rock": 1.6, 
                    "bug": 0.625, "ghost": 0.390625, "steel": 1.6, "psychic": 0.625,
                    "ice": 1.6, "dark": 1.6, "fairy": 0.625},
        "flying": {"fighting": 1.6, "rock": 0.625, "bug": 1.6, "steel": 0.625,
                   "grass": 1.6, "electric": 0.625},
        "poison": {"poison": 0.625, "ground": 0.625, "rock": 0.625, "ghost": 0.625,
                   "steel": 0.390625, "grass": 1.6, "fairy": 1.6},
        "ground": {"flying": 0.390625, "poison": 1.6, "rock": 1.6, "bug": 0.625,
                   "steel": 1.6, "fire": 1.6, "grass": 0.625, "electric": 1.6},
        "rock": {"fighting": 0.625, "flying": 1.6, "ground": 0.625, "bug": 1.6,
                 "steel": 0.625, "fire": 1.6, "ice": 1.6},
        "bug": {"fighting": 0.625, "flying": 0.625, "poison": 0.625, "ghost": 0.625,
                "steel": 0.625, "fire": 0.625, "grass": 1.6, "psychic": 1.6, 
                "dark": 1.6, "fairy": 0.625},
        "ghost": {"normal": 0.390625, "ghost": 1.6, "psychic": 1.6, "dark": 0.625},
        "steel": {"rock": 1.6, "steel": 0.625, "fire": 0.625, "water": 0.625,
                  "electric": 0.625, "ice": 1.6, "fairy": 1.6},
        "fire": {"rock": 0.625, "bug": 1.6, "steel": 1.6, "fire": 0.625,
                 "water": 0.625, "grass": 1.6, "ice": 1.6, "dragon": 0.625},
        "water": {"ground": 1.6, "rock": 1.6, "fire": 1.6, "water": 0.625,
                  "grass": 0.625, "dragon": 0.625},
        "grass": {"flying": 0.625, "poison": 0.625, "ground": 1.6, "rock": 1.6,
                  "bug": 0.625, "steel": 0.625, "fire": 0.625, "water": 1.6,
                  "grass": 0.625, "dragon": 0.625},
        "electric": {"flying": 1.6, "ground": 0.390625, "water": 1.6, "grass": 0.625,
                     "electric": 0.625, "dragon": 0.625},
        "psychic": {"fighting": 1.6, "poison": 1.6, "steel": 0.625, "psychic": 0.625,
                    "dark": 0.390625},
        "ice": {"flying": 1.6, "ground": 1.6, "steel": 0.625, "fire": 0.625,
                "water": 0.625, "grass": 1.6, "ice": 0.625, "dragon": 1.6},
        "dragon": {"steel": 0.625, "dragon": 1.6, "fairy": 0.390625},
        "dark": {"fighting": 0.625, "ghost": 1.6, "psychic": 1.6, "dark": 0.625,
                 "fairy": 0.625},
        "fairy": {"fighting": 1.6, "poison": 0.625, "steel": 0.625, "fire": 0.625,
                  "dragon": 1.6, "dark": 1.6}
    }
    
    @classmethod
    def get_effectiveness(cls, attacker_type: str, defender_types: List[str]) -> float:
        """
        Calculate type effectiveness multiplier.
        
        Args:
            attacker_type: The type of the attacking move
            defender_types: List of defender's types (1 or 2 types)
            
        Returns:
            Effectiveness multiplier
        """
        multiplier = 1.0
        
        for defender_type in defender_types:
            if defender_type:  # Skip None/empty types
                type_mult = cls.TYPE_CHART.get(attacker_type, {}).get(defender_type, 1.0)
                multiplier *= type_mult
        
        return multiplier
    
    @classmethod
    def get_all_effectiveness(cls, defender_types: List[str]) -> Dict[str, float]:
        """
        Get effectiveness of all types against a defender.
        
        Args:
            defender_types: List of defender's types
            
        Returns:
            Dictionary of {attack_type: effectiveness}
        """
        result = {}
        for attack_type in cls.TYPE_CHART.keys():
            result[attack_type] = cls.get_effectiveness(attack_type, defender_types)
        return result
