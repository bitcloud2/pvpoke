"""Damage calculation logic for Pokemon GO PvP."""

import math
from typing import Optional, Union, List
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
                        charge: float = 1.0, use_effective_stats: bool = True,
                        battle_cp: Optional[int] = None) -> int:
        """
        Calculate damage for a move.
        
        Args:
            attacker: Attacking Pokemon
            defender: Defending Pokemon  
            move: Move being used
            charge: Charge percentage for charged moves (0-1)
            use_effective_stats: Whether to use buffed stats
            battle_cp: Battle CP limit for form-specific calculations (e.g., 1500, 2500)
            
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
        
        # Aegislash Shield form special case: Use Blade form attack for charged moves
        # JavaScript Reference (DamageCalculator.js lines 41-48):
        # switch(attacker.activeFormId){
        #     case "aegislash_shield":
        #         if(move.energy > 0){
        #             attackStat = attacker.getFormStats("aegislash_blade").atk;
        #         }
        #         break;
        # }
        if (hasattr(attacker, 'active_form_id') and 
            attacker.active_form_id == "aegislash_shield" and
            isinstance(move, ChargedMove)):
            # Use Blade form's attack stat for charged moves
            blade_stats = attacker.get_form_stats("aegislash_blade", battle_cp)
            attack = blade_stats.atk
            
            # Apply stat buffs if using effective stats
            if use_effective_stats and attacker.stat_buffs[0] != 0:
                buff_multipliers = [0.5, 0.5714, 0.6667, 0.8, 1.0, 1.25, 1.5, 1.75, 2.0]
                buff_value = int(attacker.stat_buffs[0]) + 4
                buff_value = max(0, min(8, buff_value))
                attack = attack * buff_multipliers[buff_value]
        
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
        
        # Aegislash Shield form special case: Fast moves always do 1 damage
        # JavaScript Reference (DamageCalculator.js lines 53-60, 76-83):
        # switch(attacker.activeFormId){
        #     case "aegislash_shield":
        #         if(move.energyGain > 0){
        #             damage = 1;
        #         }
        #         break;
        # }
        if (hasattr(attacker, 'active_form_id') and 
            attacker.active_form_id == "aegislash_shield" and
            isinstance(move, FastMove)):
            damage = 1
        
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
                                     shields_remaining: int = 0,
                                     shields: Optional[int] = None) -> int:
        """
        Calculate charged move damage considering shields.
        
        Args:
            attacker: Attacking Pokemon
            defender: Defending Pokemon
            charged_move: Charged move being used
            shields_remaining: Number of shields defender has
            shields: Alias for shields_remaining (for backwards compatibility)
            
        Returns:
            Damage dealt (1 if shielded)
        """
        # Support both parameter names
        shields_count = shields if shields is not None else shields_remaining
        
        if shields_count > 0:
            return 1  # Shielded damage
        
        return DamageCalculator.calculate_damage(attacker, defender, charged_move)
    
    @staticmethod
    def get_duel_rating(attacker: Pokemon, defender: Pokemon, 
                       attacker_hp_remaining: Optional[int] = None,
                       defender_hp_remaining: Optional[int] = None,
                       remaining_hp1: Optional[int] = None,
                       remaining_hp2: Optional[int] = None) -> int:
        """
        Calculate battle rating (0-1000 scale).
        
        Args:
            attacker: Attacking Pokemon
            defender: Defending Pokemon
            attacker_hp_remaining: HP remaining for attacker
            defender_hp_remaining: HP remaining for defender
            remaining_hp1: Alias for attacker_hp_remaining
            remaining_hp2: Alias for defender_hp_remaining
            
        Returns:
            Battle rating (500 = even, >500 = attacker wins)
        """
        # Support both parameter naming conventions
        hp1 = remaining_hp1 if remaining_hp1 is not None else attacker_hp_remaining
        hp2 = remaining_hp2 if remaining_hp2 is not None else defender_hp_remaining
        
        if hp1 is None or hp2 is None:
            raise ValueError("Must provide HP values for both Pokemon")
        
        attacker_stats = attacker.calculate_stats()
        defender_stats = defender.calculate_stats()
        
        # Calculate HP percentages
        attacker_hp_percent = hp1 / attacker_stats.hp
        defender_hp_percent = hp2 / defender_stats.hp
        
        # Calculate damage percentages (how much damage dealt)
        attacker_damage_percent = 1 - defender_hp_percent
        defender_damage_percent = 1 - attacker_hp_percent
        
        # Combined rating
        rating = 500 * (attacker_hp_percent + attacker_damage_percent)
        
        return min(1000, max(0, int(rating)))
    
    @staticmethod
    def get_type_effectiveness(move_type: str, defender_types: List[str]) -> float:
        """
        Get type effectiveness multiplier for a move against defender types.
        
        Args:
            move_type: Type of the move
            defender_types: List of defender's types
            
        Returns:
            Effectiveness multiplier
        """
        return TypeEffectiveness.get_effectiveness(move_type, defender_types)
    
    @staticmethod
    def calculate_damage_from_stats(attack: float, defense: float, power: int,
                                    effectiveness: float = 1.0, stab: float = 1.0,
                                    attacker: Optional[Pokemon] = None,
                                    move: Optional[Move] = None,
                                    battle_cp: Optional[int] = None) -> int:
        """
        Calculate damage from raw stats (for testing/analysis).
        
        JavaScript Reference (DamageCalculator.js lines 67-86):
        static damageByStats(attacker, defender, attack, defense, effectiveness, move){
            // For Pokemon which change forms before a charged attack, use the new form's attack stat
            if(attacker.formChange && attacker.formChange.trigger == "activate_charged" && move.energy > 0){
                attack = attacker.getFormStats(attacker.formChange.alternativeFormId).atk;
            }
            var damage = Math.floor(move.power * move.stab * (attack/defense) * effectiveness * 0.5 * DamageMultiplier.BONUS) + 1;
            // Form specific special cases
            switch(attacker.activeFormId){
                case "aegislash_shield":
                    if(move.energyGain > 0){
                        damage = 1;
                    }
                    break;
            }
            return damage;
        }
        
        Args:
            attack: Attack stat
            defense: Defense stat
            power: Move power
            effectiveness: Type effectiveness multiplier
            stab: STAB multiplier
            attacker: Optional attacker Pokemon for form-specific logic
            move: Optional move for form-specific logic
            battle_cp: Battle CP limit for form-specific calculations
            
        Returns:
            Damage dealt (minimum 1)
        """
        # Aegislash Shield form: Use Blade form attack for charged moves
        if (attacker and move and 
            hasattr(attacker, 'active_form_id') and 
            attacker.active_form_id == "aegislash_shield" and
            isinstance(move, ChargedMove)):
            blade_stats = attacker.get_form_stats("aegislash_blade", battle_cp)
            attack = blade_stats.atk
        
        damage = math.floor(
            0.5 * power * attack / defense * stab * effectiveness * 
            DamageCalculator.BONUS_MULTIPLIER
        ) + 1
        
        # Aegislash Shield form: Fast moves always do 1 damage
        if (attacker and move and
            hasattr(attacker, 'active_form_id') and 
            attacker.active_form_id == "aegislash_shield" and
            isinstance(move, FastMove)):
            damage = 1
        
        return max(1, damage)
