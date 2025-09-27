"""Damage calculation logic for Pokemon GO PvP."""

import math
from typing import Optional
from ..core.pokemon import Pokemon
from ..core.moves import Move, FastMove, ChargedMove, TypeEffectiveness


class DamageCalculator:
    """Static methods for calculating damage in battles."""
    
    # Damage multipliers
    BONUS_MULTIPLIER = 1.3  # PvP damage bonus
    SHADOW_ATK_MULTIPLIER = 1.2
    SHADOW_DEF_MULTIPLIER = 0.8333333
    STAB_MULTIPLIER = 1.2  # Same Type Attack Bonus
    
    @staticmethod
    def calculate_damage(attacker: Pokemon, defender: Pokemon, move: Move, 
                        charge: float = 1.0, use_effective_stats: bool = True) -> int:
        """
        Calculate damage for a move.
        
        Args:
            attacker: Attacking Pokemon
            defender: Defending Pokemon  
            move: Move being used
            charge: Charge percentage for charged moves (0-1)
            use_effective_stats: Whether to use buffed stats
            
        Returns:
            Damage dealt (minimum 1)
        """
        # Get stats
        if use_effective_stats:
            attack = attacker.get_effective_stat(0)
            defense = defender.get_effective_stat(1)
        else:
            attacker_stats = attacker.calculate_stats()
            defender_stats = defender.calculate_stats()
            attack = attacker_stats.atk
            defense = defender_stats.defense
        
        # Get type effectiveness
        effectiveness = TypeEffectiveness.get_effectiveness(
            move.move_type, 
            defender.types
        )
        
        # Check for STAB
        stab = DamageCalculator.STAB_MULTIPLIER if move.move_type in attacker.types else 1.0
        
        # Charge multiplier for charged moves
        charge_multiplier = charge if isinstance(move, ChargedMove) else 1.0
        
        # Calculate base damage
        damage = math.floor(
            0.5 * move.power * attack / defense * stab * effectiveness * 
            charge_multiplier * DamageCalculator.BONUS_MULTIPLIER
        ) + 1
        
        return max(1, damage)  # Minimum damage is 1
    
    @staticmethod
    def calculate_breakpoint(defender: Pokemon, move: Move, target_damage: int,
                           effectiveness: float, defense_stat: float) -> float:
        """
        Calculate the attack stat needed to reach a damage breakpoint.
        
        Args:
            defender: Defending Pokemon
            move: Move being used
            target_damage: Desired damage value
            effectiveness: Type effectiveness multiplier
            defense_stat: Defender's defense stat
            
        Returns:
            Required attack stat
        """
        # Check for STAB (would need attacker info for this)
        stab = 1.0  # Default to no STAB for breakpoint calc
        
        # Solve for attack: damage = floor(0.5 * power * attack/defense * multipliers) + 1
        # attack = (damage - 1) * defense / (0.5 * power * multipliers)
        
        required_attack = ((target_damage - 1) * defense_stat) / (
            0.5 * move.power * stab * effectiveness * DamageCalculator.BONUS_MULTIPLIER
        )
        
        return required_attack
    
    @staticmethod
    def calculate_fast_move_damage(attacker: Pokemon, defender: Pokemon, 
                                  fast_move: FastMove) -> tuple[int, int]:
        """
        Calculate fast move damage and energy gain.
        
        Args:
            attacker: Attacking Pokemon
            defender: Defending Pokemon
            fast_move: Fast move being used
            
        Returns:
            Tuple of (damage, energy_gain)
        """
        damage = DamageCalculator.calculate_damage(attacker, defender, fast_move)
        energy_gain = fast_move.energy_gain
        
        return damage, energy_gain
    
    @staticmethod
    def calculate_charged_move_damage(attacker: Pokemon, defender: Pokemon,
                                     charged_move: ChargedMove,
                                     shields_remaining: int = 0) -> int:
        """
        Calculate charged move damage considering shields.
        
        Args:
            attacker: Attacking Pokemon
            defender: Defending Pokemon
            charged_move: Charged move being used
            shields_remaining: Number of shields defender has
            
        Returns:
            Damage dealt (1 if shielded)
        """
        if shields_remaining > 0:
            return 1  # Shielded damage
        
        return DamageCalculator.calculate_damage(attacker, defender, charged_move)
    
    @staticmethod
    def get_duel_rating(attacker: Pokemon, defender: Pokemon, 
                       attacker_hp_remaining: int, defender_hp_remaining: int) -> int:
        """
        Calculate battle rating (0-1000 scale).
        
        Args:
            attacker: Attacking Pokemon
            defender: Defending Pokemon
            attacker_hp_remaining: HP remaining for attacker
            defender_hp_remaining: HP remaining for defender
            
        Returns:
            Battle rating (500 = even, >500 = attacker wins)
        """
        attacker_stats = attacker.calculate_stats()
        defender_stats = defender.calculate_stats()
        
        # Calculate HP percentages
        attacker_hp_percent = attacker_hp_remaining / attacker_stats.hp
        defender_hp_percent = defender_hp_remaining / defender_stats.hp
        
        # Calculate damage percentages (how much damage dealt)
        attacker_damage_percent = 1 - defender_hp_percent
        defender_damage_percent = 1 - attacker_hp_percent
        
        # Combined rating
        rating = 500 * (attacker_hp_percent + attacker_damage_percent)
        
        return min(1000, max(0, int(rating)))
