"""Battle AI for decision making - Full port of ActionLogic.js."""

import math
import random
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from ..core.pokemon import Pokemon
from ..core.moves import FastMove, ChargedMove
from .damage_calculator import DamageCalculator


@dataclass
class BattleState:
    """State used for dynamic programming in battle simulation."""
    energy: int
    opp_health: int
    turn: int
    opp_shields: int
    moves: List[ChargedMove]
    buffs: int
    chance: float


@dataclass
class TimelineAction:
    """An action to be performed in battle."""
    action_type: str  # "fast", "charged", "wait", "switch"
    actor: int
    turn: int
    value: int  # Move index for charged moves
    settings: Dict[str, Any]
    processed: bool = False
    valid: bool = False


@dataclass
class DecisionOption:
    """Option for randomized decision making."""
    name: str
    weight: int
    move: Optional[ChargedMove] = None  # Add move reference for lethal detection


@dataclass
class ShieldDecision:
    """Result of shield decision logic."""
    value: bool
    shield_weight: int
    no_shield_weight: int


class ActionLogic:
    """
    Full port of JavaScript ActionLogic for battle AI decision making.
    """
    
    @staticmethod
    def decide_action(battle, poke: Pokemon, opponent: Pokemon) -> Optional[TimelineAction]:
        """
        Run AI decision making to determine battle action this turn.
        
        Args:
            battle: Battle instance
            poke: Pokemon making the decision
            opponent: Opponent Pokemon
            
        Returns:
            TimelineAction or None for fast move
        """
        turns = battle.current_turn
        charged_move_ready = []  # Array containing how many turns to reach active charged attacks
        wins_cmp = poke.stats.atk >= opponent.stats.atk
        
        fast_damage = DamageCalculator.calculate_damage(poke, opponent, poke.fast_move)
        opp_fast_damage = DamageCalculator.calculate_damage(opponent, poke, opponent.fast_move)
        has_non_debuff = False
        
        # Get active charged moves
        active_charged_moves = []
        if poke.charged_move_1:
            active_charged_moves.append(poke.charged_move_1)
        if poke.charged_move_2:
            active_charged_moves.append(poke.charged_move_2)
        
        # If no Charged Moves at all, return
        if len(active_charged_moves) < 1:
            return None
        
        # Find fastest charged move
        fastest_charged_move = min(active_charged_moves, key=lambda m: m.energy_cost)
        
        # If no charged move ready or farm energy is on, always throw fast move
        if poke.energy < fastest_charged_move.energy_cost or getattr(poke, 'farm_energy', False):
            return None
        
        # Evaluate cooldown to reach each charge move
        for move in active_charged_moves:
            if not getattr(move, 'self_debuffing', False):
                has_non_debuff = True
            
            if poke.energy >= move.energy_cost:
                charged_move_ready.append(0)
            else:
                turns_needed = math.ceil((move.energy_cost - poke.energy) / poke.fast_move.energy_gain)
                charged_move_ready.append(turns_needed * poke.fast_move.turns)
        
        turns_to_live = float('inf')
        queue = []
        
        # Check if opponent is in the middle of a fast move and adjust accordingly
        if getattr(opponent, 'cooldown', 0) != 0:
            queue.append({
                'hp': poke.current_hp - opp_fast_damage,
                'op_energy': opponent.energy + opponent.fast_move.energy_gain,
                'turn': opponent.cooldown / 500,
                'shields': poke.shields
            })
        else:
            queue.append({
                'hp': poke.current_hp,
                'op_energy': opponent.energy,
                'turn': 0,
                'shields': poke.shields
            })
        
        # Check if opponent can KO in your fast move cooldown
        while queue:
            curr_state = queue.pop(0)
            
            # If turn > when you can act before your opponent, move to the next item
            if curr_state['hp'] > opp_fast_damage:
                if wins_cmp:
                    if curr_state['turn'] > poke.fast_move.turns:
                        continue
                else:
                    if curr_state['turn'] > poke.fast_move.turns + 1:
                        continue
            
            # Shield bait if shields are up, otherwise try to KO
            if curr_state['shields'] != 0:
                if curr_state['op_energy'] >= fastest_charged_move.energy_cost:
                    queue.insert(0, {
                        'hp': curr_state['hp'] - 1,
                        'op_energy': curr_state['op_energy'] - fastest_charged_move.energy_cost,
                        'turn': curr_state['turn'] + 1,
                        'shields': curr_state['shields'] - 1
                    })
            else:
                # Check if any charge move KO's, add results to queue
                opp_charged_moves = []
                if opponent.charged_move_1:
                    opp_charged_moves.append(opponent.charged_move_1)
                if opponent.charged_move_2:
                    opp_charged_moves.append(opponent.charged_move_2)
                
                for move in opp_charged_moves:
                    if curr_state['op_energy'] >= move.energy_cost:
                        move_damage = DamageCalculator.calculate_damage(opponent, poke, move)
                        
                        if move_damage >= curr_state['hp']:
                            turns_to_live = min(curr_state['turn'], turns_to_live)
                            
                            if poke.stats.atk > opponent.stats.atk and opponent.fast_move.cooldown % poke.fast_move.cooldown == 0:
                                turns_to_live += 1
                            
                            ActionLogic._log_decision(battle, poke, f" opponent has energy to use {move.move_id} and it would do {move_damage} damage. I have {turns_to_live} turn(s) to live, opponent has {curr_state['op_energy']}")
                            break
                        
                        queue.insert(0, {
                            'hp': curr_state['hp'] - move_damage,
                            'op_energy': curr_state['op_energy'] - move.energy_cost,
                            'turn': curr_state['turn'] + 1,
                            'shields': curr_state['shields']
                        })
            
            # Check if a fast move faints, add results to queue
            if curr_state['hp'] - opp_fast_damage <= 0:
                turns_to_live = min(curr_state['turn'] + opponent.fast_move.turns, turns_to_live)
                break
            else:
                queue.insert(0, {
                    'hp': curr_state['hp'] - opp_fast_damage,
                    'op_energy': curr_state['op_energy'] + opponent.fast_move.energy_gain,
                    'turn': curr_state['turn'] + opponent.fast_move.turns,
                    'shields': curr_state['shields']
                })
        
        # If you can't throw a fast move and live, throw whatever move you can with the most damage
        if turns_to_live != -1:
            # Various adjustments for specific timing scenarios
            if poke.current_hp <= opponent.fast_move.damage * 2 and opponent.fast_move.cooldown == 500:
                turns_to_live -= 1
            
            # Anticipate a Fast Move landing that has already initiated
            if (poke.current_hp <= opponent.fast_move.damage and 
                getattr(opponent, 'cooldown', 0) > 0 and 
                opponent.fast_move.cooldown > 500):
                turns_to_live = opponent.cooldown / 500
                
                if opponent.current_hp > poke.fast_move.damage:
                    turns_to_live -= 1
            
            # Anticipate a Fast Move landing if you use your Fast Move
            if (poke.current_hp <= opponent.fast_move.damage and 
                getattr(opponent, 'cooldown', 0) == 0 and 
                opponent.fast_move.cooldown <= poke.fast_move.cooldown + 500):
                if opponent.current_hp > poke.fast_move.damage:
                    turns_to_live -= 1
            
            if (turns_to_live * 500 < poke.fast_move.cooldown or 
                (turns_to_live * 500 == poke.fast_move.cooldown and not wins_cmp) or 
                (turns_to_live * 500 == poke.fast_move.cooldown and poke.current_hp <= opponent.fast_move.damage)):
                
                max_damage_move_index = 0
                prev_move_damage = -1
                
                for n in range(len(active_charged_moves) - 1, -1, -1):
                    # Find highest damage available move
                    if charged_move_ready[n] == 0:
                        move_damage = DamageCalculator.calculate_damage(poke, opponent, active_charged_moves[n])
                        
                        # If this move deals more damage than the other move, use it
                        if move_damage > prev_move_damage:
                            max_damage_move_index = n
                            prev_move_damage = move_damage
                        
                        # If the Pokemon can fire two of this move and deal more damage, use it
                        if (poke.energy >= active_charged_moves[n].energy_cost * 2 and 
                            poke.stats.atk > opponent.stats.atk and 
                            move_damage * 2 > prev_move_damage):
                            max_damage_move_index = n
                            prev_move_damage = move_damage * 2
                
                # If no moves available, throw fast move
                if prev_move_damage == -1:
                    ActionLogic._log_decision(battle, poke, f" uses a fast move because it has {turns_to_live} turn(s) before it is KO'd but has no energy.")
                    return None
                # Throw highest damage move
                else:
                    ActionLogic._log_decision(battle, poke, f" uses {active_charged_moves[max_damage_move_index].move_id} because it has {turns_to_live} turn(s) before it is KO'd.")
                    
                    return TimelineAction(
                        "charged",
                        poke.index,
                        turns,
                        max_damage_move_index,
                        {"shielded": False, "buffs": False, "priority": getattr(poke, 'priority', 0)}
                    )
        
        # ADVANCED LETHAL MOVE DETECTION (Steps 1G & 1H)
        # Check for lethal moves that can KO the opponent (basic + advanced detection)
        can_ko, lethal_move = ActionLogic.can_ko_opponent_advanced(poke, opponent)
        if can_ko:
            # Handle fast move case (lethal_move is None)
            if lethal_move is None:
                ActionLogic._log_decision(battle, poke, f" uses lethal fast move")
                return None  # Use fast move
            
            # Handle charged move case
            if lethal_move:
                # Find the index of the lethal move
                move_index = 0
                if poke.charged_move_1 == lethal_move:
                    move_index = 0
                elif poke.charged_move_2 == lethal_move:
                    move_index = 1
                
                ActionLogic._log_decision(battle, poke, f" uses lethal move {lethal_move.move_id}")
                
                return TimelineAction(
                    "charged",
                    poke.index,
                    turns,
                    move_index,
                    {"shielded": False, "buffs": False, "priority": getattr(poke, 'priority', 0)}
                )
        
        # MOVE TIMING OPTIMIZATION CHECK (Step 2C)
        # Check if we should optimize timing before proceeding with DP algorithm
        if ActionLogic.optimize_move_timing(battle, poke, opponent, turns_to_live):
            # Return None to use fast move instead of charged move (timing optimization)
            return None
        
        # DYNAMIC PROGRAMMING ALGORITHM FOR OPTIMAL MOVE SEQUENCING
        # ELEMENTS OF DP QUEUE: ENERGY, OPPONENT HEALTH, TURNS, OPPONENT SHIELDS, USED MOVES, ATTACK BUFF, CHANCE
        
        state_count = 0
        dp_queue = [BattleState(
            energy=poke.energy,
            opp_health=opponent.current_hp,
            turn=0,
            opp_shields=opponent.shields,
            moves=[],
            buffs=0,
            chance=1.0
        )]
        state_list = []
        final_state = None
        
        # Main DP queue processing loop
        while len(dp_queue) != 0:
            # A not very good way to prevent infinite loops
            if state_count >= 500:
                ActionLogic._log_decision(battle, poke, " considered too many states, likely an infinite loop")
                return None
            state_count += 1
            
            curr_state = dp_queue.pop(0)  # shift() equivalent
            dp_charged_move_ready = []
            
            # Set cap of 4 for buffs
            curr_state.buffs = min(4, curr_state.buffs)
            curr_state.buffs = max(-4, curr_state.buffs)
            
            # Found fastest way to defeat enemy, fastest = optimal in this case since damage taken is strictly dependent on time
            # Set final_state to curr_state and do more evaluation later
            if curr_state.opp_health <= 0:
                state_list.append(curr_state)
                final_state = curr_state
                
                if curr_state.chance == 1.0:
                    break
                else:
                    continue
            
            # STEP 1I: LETHAL DETECTION WITHIN DP ALGORITHM
            # Check for lethal moves at current state before evaluating charged moves
            temp_poke = ActionLogic._create_temp_pokemon_from_state(poke, curr_state)
            temp_opponent = ActionLogic._create_temp_opponent_from_state(opponent, curr_state)
            
            can_ko, lethal_move = ActionLogic.can_ko_opponent_advanced(temp_poke, temp_opponent)
            if can_ko and lethal_move:
                # Create immediate victory state
                victory_state = BattleState(
                    energy=curr_state.energy - lethal_move.energy_cost,
                    opp_health=0,  # Victory achieved
                    turn=curr_state.turn + 1,
                    opp_shields=max(0, curr_state.opp_shields - 1) if curr_state.opp_shields > 0 else 0,
                    moves=curr_state.moves + [lethal_move],
                    buffs=curr_state.buffs,
                    chance=curr_state.chance
                )
                
                state_list.append(victory_state)
                final_state = victory_state
                
                ActionLogic._log_decision(battle, poke, f" found lethal move {lethal_move.move_id} in DP state")
                
                # If this is a guaranteed victory (100% chance), break immediately
                if victory_state.chance == 1.0:
                    break
                else:
                    continue
            
            # Evaluate cooldown to reach each charge move
            for n in range(len(active_charged_moves)):
                if curr_state.energy >= active_charged_moves[n].energy_cost:
                    dp_charged_move_ready.append(0)
                else:
                    turns_needed = math.ceil((active_charged_moves[n].energy_cost - curr_state.energy) / poke.fast_move.energy_gain)
                    dp_charged_move_ready.append(turns_needed * poke.fast_move.turns)
            
            # Push states onto queue in order of TURN
            # Evaluate each charged move and create new states
            for n in range(len(active_charged_moves)):
                move = active_charged_moves[n]
                
                # Apply stat changes to pokemon attack (temporary buffs for calculation)
                current_stat_buffs = [poke.stat_buffs[0], poke.stat_buffs[1]] if hasattr(poke, 'stat_buffs') else [0, 0]
                
                # Calculate attack multiplier from buffs
                attack_mult = curr_state.buffs
                possible_attack_mult = attack_mult
                change_ttk_chance = 0.0
                
                # Apply move buffs if the move has them
                if hasattr(move, 'buffs') and move.buffs:
                    buff_apply_chance = getattr(move, 'buff_apply_chance', 1.0)
                    buff_target = getattr(move, 'buff_target', 'self')
                    
                    if buff_target == 'self' and len(move.buffs) >= 2:
                        # Attack buff is typically the first element
                        attack_buff = move.buffs[0] if move.buffs[0] != 1.0 else 0
                        if attack_buff != 0:
                            if buff_apply_chance < 1.0:
                                change_ttk_chance = buff_apply_chance
                                possible_attack_mult = min(4, max(-4, attack_mult + attack_buff))
                            else:
                                attack_mult = min(4, max(-4, attack_mult + attack_buff))
                
                # Calculate move damage with current buffs
                move_damage = DamageCalculator.calculate_damage(poke, opponent, move)
                
                # If move is ready (0 turns to wait)
                if dp_charged_move_ready[n] == 0:
                    new_energy = curr_state.energy - move.energy_cost
                    new_opp_health = curr_state.opp_health - move_damage
                    new_turn = curr_state.turn + 1
                    new_shields = curr_state.opp_shields
                    
                    # Handle shielding
                    if new_shields > 0:
                        new_shields -= 1
                        # If shielded, only 1 damage gets through
                        new_opp_health = curr_state.opp_health - 1
                    
                    # Check if we should insert this state
                    insert_element = True
                    
                    # Simple insertion for now - add to front of queue
                    if len(dp_queue) == 0:
                        new_moves = curr_state.moves + [move]
                        dp_queue.insert(0, BattleState(
                            energy=new_energy,
                            opp_health=new_opp_health,
                            turn=new_turn,
                            opp_shields=new_shields,
                            moves=new_moves,
                            buffs=attack_mult,
                            chance=curr_state.chance
                        ))
                        
                        # If move has chance of changing buffs, add that result too
                        if change_ttk_chance > 0:
                            dp_queue.insert(0, BattleState(
                                energy=new_energy,
                                opp_health=new_opp_health,
                                turn=new_turn,
                                opp_shields=new_shields,
                                moves=new_moves,
                                buffs=possible_attack_mult,
                                chance=curr_state.chance * change_ttk_chance
                            ))
                    else:
                        # Find correct insertion point based on turn priority
                        i = 0
                        insert = True
                        
                        while i < len(dp_queue) and dp_queue[i].turn <= new_turn:
                            # Check if this state is dominated by an existing state
                            if (dp_queue[i].opp_health <= new_opp_health and 
                                dp_queue[i].energy >= new_energy and 
                                dp_queue[i].buffs >= attack_mult and 
                                dp_queue[i].opp_shields <= new_shields):
                                insert = False
                                break
                            i += 1
                        
                        if insert:
                            new_moves = curr_state.moves + [move]
                            dp_queue.insert(i, BattleState(
                                energy=new_energy,
                                opp_health=new_opp_health,
                                turn=new_turn,
                                opp_shields=new_shields,
                                moves=new_moves,
                                buffs=attack_mult,
                                chance=curr_state.chance
                            ))
                            
                            # If move has chance of changing buffs, add that result too
                            if change_ttk_chance > 0:
                                dp_queue.insert(i, BattleState(
                                    energy=new_energy,
                                    opp_health=new_opp_health,
                                    turn=new_turn,
                                    opp_shields=new_shields,
                                    moves=new_moves,
                                    buffs=possible_attack_mult,
                                    chance=curr_state.chance * change_ttk_chance
                                ))
                
                # If move requires farming (not ready this turn)
                else:
                    # Calculate energy and health after farming
                    turns_to_farm = dp_charged_move_ready[n] // poke.fast_move.turns
                    fast_simulated_damage = DamageCalculator.calculate_damage(poke, opponent, poke.fast_move) * turns_to_farm
                    
                    new_energy = curr_state.energy - move.energy_cost + (poke.fast_move.energy_gain * turns_to_farm)
                    new_opp_health = curr_state.opp_health - move_damage - fast_simulated_damage
                    new_turn = curr_state.turn + dp_charged_move_ready[n] + 1
                    new_shields = curr_state.opp_shields
                    
                    # Handle shielding
                    if new_shields > 0:
                        new_shields -= 1
                        # If shielded, only fast move damage + 1 gets through
                        new_opp_health = curr_state.opp_health - fast_simulated_damage - 1
                    
                    # Insert state into queue
                    i = 0
                    insert_element = True
                    
                    if len(dp_queue) == 0:
                        new_moves = curr_state.moves + [move]
                        dp_queue.insert(0, BattleState(
                            energy=new_energy,
                            opp_health=new_opp_health,
                            turn=new_turn,
                            opp_shields=new_shields,
                            moves=new_moves,
                            buffs=attack_mult,
                            chance=curr_state.chance
                        ))
                    else:
                        # Find correct insertion point
                        while i < len(dp_queue) and dp_queue[i].turn < new_turn:
                            if (dp_queue[i].opp_health <= new_opp_health and 
                                dp_queue[i].energy >= new_energy and 
                                dp_queue[i].buffs >= attack_mult and 
                                dp_queue[i].opp_shields <= new_shields):
                                insert_element = False
                                break
                            i += 1
                        
                        if insert_element:
                            new_moves = curr_state.moves + [move]
                            dp_queue.insert(i, BattleState(
                                energy=new_energy,
                                opp_health=new_opp_health,
                                turn=new_turn,
                                opp_shields=new_shields,
                                moves=new_moves,
                                buffs=attack_mult,
                                chance=curr_state.chance
                            ))
        
        # Process final states and choose best move sequence
        if final_state is not None and final_state.moves:
            # STEP 1J & 1K: SHIELD BAITING LOGIC WITH DPE RATIO ANALYSIS
            # Apply enhanced shield baiting logic before returning the final move
            selected_move = ActionLogic._apply_shield_baiting_logic(
                poke, opponent, final_state.moves, active_charged_moves, battle
            )
            
            # Find the index of the selected move in active charged moves
            move_index = 0
            for i, move in enumerate(active_charged_moves):
                if move == selected_move:
                    move_index = i
                    break
            
            ActionLogic._log_decision(battle, poke, f" uses {selected_move.move_id} from optimal DP sequence (after baiting logic)")
            
            return TimelineAction(
                "charged",
                poke.index,
                turns,
                move_index,
                {"shielded": False, "buffs": False, "priority": getattr(poke, 'priority', 0)}
            )
        elif state_list:
            # Find the state with the highest chance of success
            best_state = max(state_list, key=lambda s: s.chance)
            
            if best_state.moves:
                # STEP 1J & 1K: SHIELD BAITING LOGIC WITH DPE RATIO ANALYSIS
                # Apply enhanced shield baiting logic before returning the final move
                selected_move = ActionLogic._apply_shield_baiting_logic(
                    poke, opponent, best_state.moves, active_charged_moves, battle
                )
                
                # Find the index of the selected move in active charged moves
                move_index = 0
                for i, move in enumerate(active_charged_moves):
                    if move == selected_move:
                        move_index = i
                        break
                
                ActionLogic._log_decision(battle, poke, f" uses {selected_move.move_id} from optimal DP sequence (after baiting logic)")
                
                return TimelineAction(
                    "charged",
                    poke.index,
                    turns,
                    move_index,
                    {"shielded": False, "buffs": False, "priority": getattr(poke, 'priority', 0)}
                )
        
        # No optimal charged move sequence found, use fast move
        return None
    
    @staticmethod
    def decide_random_action(battle, poke: Pokemon, opponent: Pokemon) -> Optional[TimelineAction]:
        """
        Select a randomized action for this turn.
        
        Args:
            battle: Battle instance
            poke: Pokemon making the decision
            opponent: Opponent Pokemon
            
        Returns:
            TimelineAction or None for fast move
        """
        fast_move_weight = 10
        has_knockout_move = False
        action_options = []
        charged_move_values = []
        turns = battle.current_turn
        
        # Get active charged moves
        active_charged_moves = []
        if poke.charged_move_1:
            active_charged_moves.append(poke.charged_move_1)
        if poke.charged_move_2:
            active_charged_moves.append(poke.charged_move_2)
        
        # Evaluate when to randomly use Charged Moves
        for i, move in enumerate(active_charged_moves):
            if poke.energy >= move.energy_cost:
                damage = DamageCalculator.calculate_damage(poke, opponent, move)
                charged_move_weight = round(poke.energy / 4)
                
                # Find best charged move for comparison
                best_charged_move = max(active_charged_moves, key=lambda m: DamageCalculator.calculate_damage(poke, opponent, m) / m.energy_cost)
                
                if poke.energy < best_charged_move.energy_cost:
                    charged_move_weight = round(poke.energy / 50)
                
                if has_knockout_move:
                    charged_move_weight = 0
                
                # Go for the KO if it's there
                if damage >= opponent.current_hp and opponent.shields == 0:
                    fast_move_weight = 0
                    has_knockout_move = True
                
                # Don't use Charged Move if it's strictly worse than the other option
                if (i > 0 and 
                    damage < DamageCalculator.calculate_damage(poke, opponent, active_charged_moves[0]) and 
                    move.energy_cost >= active_charged_moves[0].energy_cost and 
                    not getattr(move, 'self_buffing', False)):
                    charged_move_weight = 0
                
                # Use Charged Moves if capped on energy
                if poke.energy == 100:
                    charged_move_weight *= 2
                
                charged_move_values.append({
                    'move': move,
                    'damage': damage,
                    'weight': charged_move_weight,
                    'index': i
                })
        
        # Handle shield logic for multiple moves
        if len(charged_move_values) > 1:
            # If shields are up and both moves would KO, prefer non debuffing moves
            if (charged_move_values[0]['damage'] >= opponent.current_hp and 
                charged_move_values[1]['damage'] >= opponent.current_hp and 
                opponent.shields > 0):
                
                move0_debuff = getattr(charged_move_values[0]['move'], 'self_debuffing', False)
                move1_debuff = getattr(charged_move_values[1]['move'], 'self_debuffing', False)
                
                if (move0_debuff and not move1_debuff and 
                    charged_move_values[1]['move'].energy_cost <= charged_move_values[0]['move'].energy_cost):
                    charged_move_values[0]['weight'] = 0
                elif (move1_debuff and not move0_debuff and 
                      charged_move_values[0]['move'].energy_cost <= charged_move_values[1]['move'].energy_cost):
                    charged_move_values[1]['weight'] = 0
        
        # Build action options
        for i, move_value in enumerate(charged_move_values):
            action_options.append(DecisionOption(
                f"CHARGED_MOVE_{move_value['index']}", 
                move_value['weight'],
                move_value['move']  # Include move reference for lethal detection
            ))
        
        action_options.append(DecisionOption("FAST_MOVE", fast_move_weight, None))
        
        # STEP 1I: BOOST LETHAL MOVE WEIGHTS IN DECISION OPTIONS
        ActionLogic.boost_lethal_move_weight(action_options, poke, opponent)
        
        action_type = ActionLogic.choose_option(action_options)
        
        if action_type.name == "FAST_MOVE":
            return None
        elif action_type.name == "CHARGED_MOVE_0":
            return TimelineAction(
                "charged",
                poke.index,
                turns,
                0,
                {"shielded": False, "buffs": False, "priority": getattr(poke, 'priority', 0)}
            )
        elif action_type.name == "CHARGED_MOVE_1":
            return TimelineAction(
                "charged",
                poke.index,
                turns,
                1,
                {"shielded": False, "buffs": False, "priority": getattr(poke, 'priority', 0)}
            )
        
        return None
    
    @staticmethod
    def choose_option(options: List[DecisionOption]) -> DecisionOption:
        """Choose an option from an array based on weights."""
        option_bucket = []
        
        # Put all the options in bucket, multiple times for its weight value
        for option in options:
            for _ in range(option.weight):
                option_bucket.append(option.name)
        
        # If all options have 0 weight, just toss the first option in there
        if not option_bucket:
            option_bucket.append(options[0].name)
        
        index = random.randint(0, len(option_bucket) - 1)
        option_name = option_bucket[index]
        
        # Find the option object
        for option in options:
            if option.name == option_name:
                return option
        
        return options[0]  # Fallback
    
    @staticmethod
    def would_shield(battle, attacker: Pokemon, defender: Pokemon, move: ChargedMove) -> ShieldDecision:
        """
        Returns a decision for whether a Pokemon would shield a Charged Move.
        
        Args:
            battle: Battle instance
            attacker: Pokemon using the move
            defender: Pokemon deciding to shield
            move: The charged move being used
            
        Returns:
            ShieldDecision with value and weights
        """
        use_shield = False
        shield_weight = 1
        no_shield_weight = 2  # Used for randomized shielding decisions
        damage = DamageCalculator.calculate_damage(attacker, defender, move)
        
        post_move_hp = defender.current_hp - damage  # How much HP will be left after the attack
        
        # Capture current buffs for pokemon whose buffs will change
        current_buffs = None
        move_buffs = getattr(move, 'buffs', [1.0, 1.0])
        
        if move_buffs[0] > 1.0:
            current_buffs = [attacker.stat_buffs[0], attacker.stat_buffs[1]]
            # Apply temporary buffs for calculation
        else:
            current_buffs = [defender.stat_buffs[0], defender.stat_buffs[1]]
            # Apply temporary buffs for calculation
        
        fast_damage = DamageCalculator.calculate_damage(attacker, defender, attacker.fast_move)
        
        # Determine how much damage will be dealt per cycle to see if the defender will survive to shield the next cycle
        fast_attacks = math.ceil((move.energy_cost - max(attacker.energy - move.energy_cost, 0)) / attacker.fast_move.energy_gain) + 1
        fast_attack_damage = fast_attacks * fast_damage
        cycle_damage = (fast_attack_damage + 1) * defender.shields
        
        if post_move_hp <= cycle_damage:
            use_shield = True
            shield_weight = 2
        
        # Reset buffs to original (if we applied any)
        # This would be done here in a full implementation
        
        # If the defender can't afford to let a charged move connect, block
        fast_dpt = fast_damage / attacker.fast_move.turns
        
        attacker_charged_moves = []
        if attacker.charged_move_1:
            attacker_charged_moves.append(attacker.charged_move_1)
        if attacker.charged_move_2:
            attacker_charged_moves.append(attacker.charged_move_2)
        
        for charged_move in attacker_charged_moves:
            if attacker.energy + charged_move.energy_cost >= charged_move.energy_cost:
                charged_damage = DamageCalculator.calculate_damage(attacker, defender, charged_move)
                
                if charged_damage >= defender.current_hp / 1.4 and fast_dpt > 1.5:
                    use_shield = True
                    shield_weight = 4
                
                if charged_damage >= defender.current_hp - cycle_damage:
                    use_shield = True
                    shield_weight = 4
                
                if charged_damage >= defender.current_hp / 2 and fast_dpt > 2:
                    shield_weight = 12
        
        # Shield the first in a series of Attack debuffing moves like Superpower, if they would do major damage
        if getattr(move, 'self_attack_debuffing', False) and (damage / defender.current_hp > 0.55):
            use_shield = True
            shield_weight = 4
        
        # When a Pokemon is set to always bait, always return true for this value
        if hasattr(battle, 'get_mode') and battle.get_mode() == "simulate" and getattr(attacker, 'bait_shields', 0) == 2:
            use_shield = True
        
        return ShieldDecision(
            value=use_shield,
            shield_weight=shield_weight,
            no_shield_weight=no_shield_weight
        )
    
    # ========== MOVE TIMING OPTIMIZATION METHODS (Step 2B) ==========
    
    @staticmethod
    def calculate_target_cooldown(poke: Pokemon, opponent: Pokemon) -> int:
        """Calculate the target cooldown for optimal move timing."""
        target_cooldown = 500  # Default: throw when opponent has 500ms or less cooldown
        
        # Rule 1: Pokemon with 4+ turn moves (2000ms+) use 1000ms target
        if poke.fast_move.cooldown >= 2000:
            target_cooldown = 1000
        
        # Rule 2: 3-turn vs 5-turn matchup (1500ms vs 2500ms)
        if poke.fast_move.cooldown >= 1500 and opponent.fast_move.cooldown == 2500:
            target_cooldown = 1000
        
        # Rule 3: 2-turn vs 4-turn matchup (1000ms vs 2000ms)  
        if poke.fast_move.cooldown == 1000 and opponent.fast_move.cooldown == 2000:
            target_cooldown = 1000
        
        return target_cooldown
    
    @staticmethod
    def should_disable_timing_optimization(poke: Pokemon, opponent: Pokemon) -> bool:
        """Check if timing optimization should be disabled."""
        
        # Disable for same duration moves (no advantage possible)
        if poke.fast_move.cooldown == opponent.fast_move.cooldown:
            return True
        
        # Disable for evenly divisible longer moves (e.g., 4-turn vs 2-turn, 3-turn vs 1-turn)
        if (poke.fast_move.cooldown % opponent.fast_move.cooldown == 0 and 
            poke.fast_move.cooldown > opponent.fast_move.cooldown):
            return True
        
        return False
    
    @staticmethod
    def check_survival_conditions(battle, poke: Pokemon, opponent: Pokemon) -> bool:
        """Verify Pokemon can safely optimize timing without fainting."""
        
        # Don't optimize if about to faint from opponent's fast move
        if poke.current_hp <= opponent.fast_move.damage:
            return False
        
        # Don't optimize if opponent can KO with fast moves during our fast move
        fast_moves_in_window = math.floor((poke.fast_move.cooldown + 500) / opponent.fast_move.cooldown)
        if poke.current_hp <= opponent.fast_move.damage * fast_moves_in_window:
            return False
        
        return True
    
    @staticmethod
    def check_energy_conditions(battle, poke: Pokemon) -> bool:
        """Ensure energy won't overflow with timing optimization."""
        
        # Count queued fast moves
        queued_fast_moves = 0
        
        # Check if battle has get_queued_actions method (Step 2C implementation)
        if hasattr(battle, 'get_queued_actions'):
            try:
                queued_actions = battle.get_queued_actions()
                
                # Ensure we have a proper list (not a Mock object)
                if isinstance(queued_actions, list):
                    for action in queued_actions:
                        if (hasattr(action, 'actor') and hasattr(action, 'type') and
                            action.actor == poke.index and action.type == "fast"):
                            queued_fast_moves += 1
            except (AttributeError, TypeError):
                # Handle cases where battle is a mock or doesn't have proper implementation
                pass
        
        # Add 1 for the fast move we're considering
        queued_fast_moves += 1
        
        # Don't optimize if we'll exceed 100 energy
        future_energy = poke.energy + (poke.fast_move.energy_gain * queued_fast_moves)
        if future_energy > 100:
            return False
        
        return True
    
    @staticmethod
    def check_strategic_conditions(battle, poke: Pokemon, opponent: Pokemon, turns_to_live: int) -> bool:
        """Check strategic conditions for timing optimization."""
        
        # Get active charged moves
        active_charged_moves = []
        if poke.charged_move_1:
            active_charged_moves.append(poke.charged_move_1)
        if poke.charged_move_2:
            active_charged_moves.append(poke.charged_move_2)
        
        if not active_charged_moves:
            return False
        
        # Calculate planned turns (fast move + charged moves we can throw)
        planned_turns = poke.fast_move.turns + math.floor(poke.energy / active_charged_moves[0].energy_cost)
        
        # Add extra turn if we lose CMP (lower attack stat)
        if poke.stats.atk < opponent.stats.atk:
            planned_turns += 1
        
        # Don't optimize if we have fewer turns to live than planned actions
        if planned_turns > turns_to_live:
            return False
        
        # Don't optimize if we can KO opponent with a charged move (no shields)
        if opponent.shields == 0:
            for move in active_charged_moves:
                move_damage = DamageCalculator.calculate_damage(poke, opponent, move)
                if poke.energy >= move.energy_cost and move_damage >= opponent.current_hp:
                    return False
        
        # Don't optimize if opponent can KO us with their charged move
        opponent_charged_moves = []
        if opponent.charged_move_1:
            opponent_charged_moves.append(opponent.charged_move_1)
        if opponent.charged_move_2:
            opponent_charged_moves.append(opponent.charged_move_2)
        
        for move in opponent_charged_moves:
            fast_moves_needed = math.ceil((move.energy_cost - opponent.energy) / opponent.fast_move.energy_gain)
            fast_moves_in_window = math.floor(poke.fast_move.cooldown / opponent.fast_move.cooldown)
            turns_from_move = (fast_moves_needed * opponent.fast_move.turns) + 1
            
            move_damage = DamageCalculator.calculate_damage(opponent, poke, move)
            total_damage = move_damage + (opponent.fast_move.damage * fast_moves_in_window)
            
            # Account for shields
            if poke.shields > 0:
                total_damage = 1 + (opponent.fast_move.damage * fast_moves_in_window)
            
            if turns_from_move <= poke.fast_move.turns and total_damage >= poke.current_hp:
                return False
        
        return True
    
    @staticmethod
    def optimize_move_timing(battle, poke: Pokemon, opponent: Pokemon, turns_to_live: int) -> bool:
        """
        Main move timing optimization logic.
        
        Args:
            battle: Battle instance
            poke: Pokemon considering timing optimization
            opponent: Opponent Pokemon
            turns_to_live: Number of turns this Pokemon can survive
        
        Returns:
            True if should wait (optimize timing), False if should proceed with charged move
        """
        
        # Check if optimization is enabled (must be explicitly True)
        optimize_timing = getattr(poke, 'optimize_move_timing', False)
        if optimize_timing is not True:
            return False
        
        # Calculate target cooldown
        target_cooldown = ActionLogic.calculate_target_cooldown(poke, opponent)
        
        # Check if optimization should be disabled
        if ActionLogic.should_disable_timing_optimization(poke, opponent):
            target_cooldown = 0
        
        # Only optimize if opponent is at target cooldown or higher, and target > 0
        opponent_cooldown = getattr(opponent, 'cooldown', 0)
        if not ((opponent_cooldown == 0 or opponent_cooldown > target_cooldown) and target_cooldown > 0):
            return False
        
        # Run all safety and strategic checks
        if not ActionLogic.check_survival_conditions(battle, poke, opponent):
            return False
        
        if not ActionLogic.check_energy_conditions(battle, poke):
            return False
        
        if not ActionLogic.check_strategic_conditions(battle, poke, opponent, turns_to_live):
            return False
        
        # All checks passed - optimize timing
        ActionLogic._log_decision(battle, poke, " is optimizing move timing")
        return True  # Return early, don't throw charged move this turn
    
    # ========== LETHAL MOVE DETECTION METHODS (Steps 1G & 1H) ==========
    
    @staticmethod
    def can_ko_opponent(poke: Pokemon, opponent: Pokemon) -> Tuple[bool, Optional[ChargedMove]]:
        """
        Check if any available charged move can KO the opponent.
        
        Args:
            poke: Pokemon checking for lethal moves
            opponent: Opponent Pokemon
            
        Returns:
            Tuple of (can_ko: bool, lethal_move: Optional[ChargedMove])
        """
        # Only check when opponent has no shields (matches JS logic)
        if opponent.shields > 0:
            return False, None
        
        # Don't check if farming energy
        if getattr(poke, 'farm_energy', False):
            return False, None
        
        # Get active charged moves
        active_charged_moves = []
        if poke.charged_move_1:
            active_charged_moves.append(poke.charged_move_1)
        if poke.charged_move_2:
            active_charged_moves.append(poke.charged_move_2)
        
        lethal_moves = []
        
        # Check each charged move for lethal potential
        for i, move in enumerate(active_charged_moves):
            # Must have enough energy
            if poke.energy >= move.energy_cost:
                damage = ActionLogic.calculate_lethal_damage(poke, opponent, move)
                
                # Check if move can KO opponent
                if damage >= opponent.current_hp:
                    # Apply JavaScript logic constraints:
                    # - Don't throw self debuffing moves at this point
                    # - Only use first move, or second move if not baiting shields
                    # - Don't use if opponent will faint from fast move damage anyway
                    if (not getattr(move, 'self_debuffing', False) and
                        (i == 0 or (i == 1 and not getattr(poke, 'bait_shields', False))) and
                        opponent.current_hp > poke.fast_move.damage):
                        
                        lethal_moves.append((move, damage, i))
        
        if not lethal_moves:
            return False, None
        
        # Return the best lethal move (first available, matching JS priority)
        best_move = ActionLogic.select_best_lethal_move(lethal_moves)
        return True, best_move
    
    @staticmethod
    def calculate_lethal_damage(attacker: Pokemon, defender: Pokemon, move: ChargedMove) -> int:
        """
        Calculate damage for lethal move detection.
        
        Args:
            attacker: Pokemon using the move
            defender: Pokemon receiving the move
            move: Move being used
            
        Returns:
            Expected damage (no shield consideration since we only check when shields=0)
        """
        # Use standard damage calculation - shields already checked in can_ko_opponent
        return DamageCalculator.calculate_damage(attacker, defender, move)
    
    @staticmethod
    def select_best_lethal_move(lethal_moves: List[Tuple[ChargedMove, int, int]]) -> ChargedMove:
        """
        Select the best lethal move from available options.
        
        Args:
            lethal_moves: List of (move, damage, index) tuples
            
        Returns:
            The best lethal move (first available, matching JavaScript priority)
        """
        # JavaScript logic: use the first available lethal move (index 0 preferred over index 1)
        # Sort by move index to maintain JavaScript behavior
        lethal_moves.sort(key=lambda x: x[2])  # Sort by index (third element)
        return lethal_moves[0][0]  # Return the move (first element)
    
    # ========== SHIELD BAITING LOGIC METHODS (Step 1J) ==========
    
    @staticmethod
    def _apply_shield_baiting_logic(poke: Pokemon, opponent: Pokemon, 
                                   optimal_moves: List[ChargedMove], 
                                   active_charged_moves: List[ChargedMove],
                                   battle = None) -> ChargedMove:
        """
        Apply enhanced shield baiting logic with DPE ratio analysis and move reordering.
        
        Based on JavaScript ActionLogic lines 838-878:
        - Don't bait if the opponent won't shield
        - Check DPE ratio between moves (must be > 1.5x)
        - Ensure Pokemon has enough energy for the higher DPE move
        - Use would_shield prediction to determine if baiting is worthwhile
        - Enhanced with Step 1K DPE ratio analysis
        - Enhanced with Step 1L move reordering logic
        
        Args:
            poke: Pokemon making the decision
            opponent: Opponent Pokemon
            optimal_moves: Moves from DP algorithm
            active_charged_moves: All available charged moves
            battle: Battle instance for enhanced analysis
            
        Returns:
            The move to use (after baiting and reordering logic)
        """
        # Default to the first move from optimal sequence
        if not optimal_moves:
            return active_charged_moves[0] if active_charged_moves else None
        
        # STEP 1L: Apply move reordering logic first
        # Determine if Pokemon needs boost and if any moves are debuffing
        needs_boost = False  # TODO: Implement boost detection logic
        debuffing_move = any(getattr(move, 'self_debuffing', False) for move in optimal_moves)
        
        # Apply move reordering to the optimal moves
        reordered_moves = ActionLogic.apply_move_reordering_logic(
            poke, opponent, optimal_moves, active_charged_moves, 
            needs_boost, debuffing_move, battle
        )
        
        selected_move = reordered_moves[0] if reordered_moves else optimal_moves[0]
        
        # Don't bait if the opponent won't shield, or if we don't have bait_shields enabled
        if (not getattr(poke, 'bait_shields', False) or 
            opponent.shields <= 0 or 
            len(active_charged_moves) <= 1):
            return selected_move
        
        # STEP 1K: Enhanced DPE Ratio Analysis
        # Try the new DPE analysis first
        if ActionLogic.should_use_dpe_ratio_analysis(battle, poke, opponent, selected_move):
            enhanced_move = ActionLogic.analyze_dpe_ratios(battle, poke, opponent, selected_move)
            if enhanced_move:
                return enhanced_move
        
        # Fallback to original JavaScript logic for compatibility
        # JavaScript logic: compare activeChargedMoves[1] (higher energy) vs finalState.moves[0] (selected)
        # Find the higher energy move (typically the second move in active_charged_moves)
        higher_energy_move = None
        for move in active_charged_moves:
            if move != selected_move and move.energy_cost > selected_move.energy_cost:
                higher_energy_move = move
                break
        
        if higher_energy_move is None:
            return selected_move
        
        # Calculate DPE ratio using enhanced calculation
        current_dpe = ActionLogic.calculate_move_dpe(poke, opponent, selected_move)
        higher_dpe = ActionLogic.calculate_move_dpe(poke, opponent, higher_energy_move)
        
        if current_dpe <= 0:  # Avoid division by zero
            return selected_move
            
        dpe_ratio = higher_dpe / current_dpe
        
        # Check if Pokemon has enough energy for the higher energy move and DPE ratio > 1.5
        if (poke.energy >= higher_energy_move.energy_cost and dpe_ratio > 1.5):
            # Use would_shield to predict if opponent would shield the higher energy move
            # If they wouldn't shield it, use the higher energy move instead (no baiting needed)
            shield_decision = ActionLogic.would_shield(battle, poke, opponent, higher_energy_move)
            if not shield_decision.value:
                ActionLogic._log_decision(battle, poke, f" baiting: switching to {higher_energy_move.move_id} (DPE ratio: {dpe_ratio:.2f})")
                return higher_energy_move
        
        return selected_move
    
    # ========== DPE RATIO ANALYSIS METHODS (Step 1K) ==========
    
    @staticmethod
    def get_active_charged_moves(poke: Pokemon) -> List[ChargedMove]:
        """
        Get list of active charged moves for a Pokemon.
        
        Args:
            poke: Pokemon to get moves for
            
        Returns:
            List of active charged moves
        """
        active_moves = []
        if poke.charged_move_1:
            active_moves.append(poke.charged_move_1)
        if poke.charged_move_2:
            active_moves.append(poke.charged_move_2)
        return active_moves
    
    @staticmethod
    def calculate_move_dpe(poke: Pokemon, opponent: Pokemon, move) -> float:
        """
        Calculate Damage Per Energy for a move against specific opponent.
        
        Args:
            poke: Pokemon using the move
            opponent: Target opponent
            move: The move to calculate DPE for
            
        Returns:
            DPE value (damage / energy_cost)
        """
        if not hasattr(move, 'energy_cost') or move.energy_cost <= 0:
            return 0.0  # Fast moves have no energy cost
        
        # Calculate base damage
        damage = DamageCalculator.calculate_damage(poke, opponent, move)
        
        # Account for buff effects in DPE calculation (matching JavaScript logic)
        # Only apply buff multiplier if move actually has buffs
        if (hasattr(move, 'buffs') and move.buffs and 
            hasattr(move, 'buff_target') and move.buff_target in ["self", "opponent"]):
            buff_multiplier = ActionLogic.calculate_buff_dpe_multiplier(move)
            damage *= buff_multiplier
        
        return damage / move.energy_cost
    
    @staticmethod
    def calculate_buff_dpe_multiplier(move) -> float:
        """
        Calculate DPE multiplier for moves with buff effects.
        
        Based on JavaScript Pokemon.initializeMove lines 848-864:
        - Self-buffing moves (attack buffs): buffEffect = buffs[0] * (80 / energy)
        - Opponent debuffing moves (defense debuffs): buffEffect = abs(buffs[1]) * (80 / energy)
        - multiplier = (buffDivisor + (buffEffect * buffApplyChance)) / buffDivisor
        
        Args:
            move: Move to calculate buff multiplier for
            
        Returns:
            DPE multiplier (1.0 if no buffs)
        """
        if not hasattr(move, 'buffs') or not move.buffs:
            return 1.0
        
        buff_effect = 0
        
        # Self-buffing moves (attack buffs) - JavaScript uses > 0 for buff stages
        if (hasattr(move, 'buff_target') and move.buff_target == "self" and 
            len(move.buffs) > 0 and move.buffs[0] > 0):
            buff_effect = move.buffs[0] * (80 / move.energy_cost)
        
        # Opponent debuffing moves (defense debuffs) - JavaScript uses < 0 for debuff stages
        elif (hasattr(move, 'buff_target') and move.buff_target == "opponent" and 
              len(move.buffs) > 1 and move.buffs[1] < 0):
            buff_effect = abs(move.buffs[1]) * (80 / move.energy_cost)
        
        if buff_effect > 0:
            buff_apply_chance = getattr(move, 'buff_apply_chance', 1.0)
            buff_divisor = 4.0  # From GameMaster settings
            multiplier = (buff_divisor + (buff_effect * buff_apply_chance)) / buff_divisor
            return multiplier
        
        return 1.0
    
    @staticmethod
    def analyze_dpe_ratios(battle, poke: Pokemon, opponent: Pokemon, current_move) -> Optional:
        """
        Analyze DPE ratios to determine optimal move selection for baiting.
        
        Based on JavaScript ActionLogic lines 840-847:
        - Calculate DPE ratio between moves
        - Use 1.5x threshold for DPE advantage
        - Check opponent shield prediction
        - Validate energy requirements
        
        Args:
            battle: Current battle instance
            poke: Current Pokemon
            opponent: Opponent Pokemon  
            current_move: Currently selected move
            
        Returns:
            Better move if found, None otherwise
        """
        if (not getattr(poke, 'bait_shields', False) or 
            opponent.shields <= 0):
            return None
        
        active_moves = ActionLogic.get_active_charged_moves(poke)
        if len(active_moves) < 2:
            return None
        
        # Find the second move (higher energy, potentially higher DPE)
        second_move = None
        for move in active_moves:
            if move != current_move and poke.energy >= move.energy_cost:
                second_move = move
                break
        
        if not second_move:
            return None
        
        # Calculate DPE ratio using the enhanced DPE calculation
        current_dpe = ActionLogic.calculate_move_dpe(poke, opponent, current_move)
        second_dpe = ActionLogic.calculate_move_dpe(poke, opponent, second_move)
        
        if current_dpe <= 0:
            return None
        
        dpe_ratio = second_dpe / current_dpe
        
        # JavaScript uses 1.5x threshold for DPE ratio
        if dpe_ratio > 1.5:
            # Check if opponent would NOT shield the higher DPE move
            shield_decision = ActionLogic.would_shield(battle, poke, opponent, second_move)
            if not shield_decision.value:
                ActionLogic._log_decision(battle, poke, 
                    f" DPE analysis: switching to {second_move.move_id} (ratio: {dpe_ratio:.2f})")
                return second_move  # Use the more efficient move if opponent won't shield
        
        return None
    
    @staticmethod
    def validate_baiting_energy_requirements(poke: Pokemon, bait_move, follow_up_move) -> bool:
        """
        Validate that Pokemon can execute baiting strategy with available energy.
        
        Args:
            poke: Current Pokemon
            bait_move: The move to bait with
            follow_up_move: The follow-up move after baiting
            
        Returns:
            True if energy requirements are met
        """
        # Must have energy for bait move immediately
        if poke.energy < bait_move.energy_cost:
            return False
        
        # Calculate energy after bait move and fast moves needed for follow-up
        energy_after_bait = poke.energy - bait_move.energy_cost
        energy_needed_for_followup = follow_up_move.energy_cost - energy_after_bait
        
        if energy_needed_for_followup <= 0:
            return True  # Can immediately use follow-up move
        
        # Calculate fast moves needed to reach follow-up energy
        fast_moves_needed = math.ceil(energy_needed_for_followup / poke.fast_move.energy_gain)
        
        # For now, assume Pokemon can survive the fast moves needed
        # More sophisticated survival checking would require battle simulation
        return fast_moves_needed <= 5  # Reasonable limit
    
    @staticmethod
    def should_use_dpe_ratio_analysis(battle, poke: Pokemon, opponent: Pokemon, current_move) -> bool:
        """
        Determine if DPE ratio analysis should be applied.
        
        Args:
            battle: Current battle instance
            poke: Current Pokemon
            opponent: Opponent Pokemon
            current_move: Currently selected move
            
        Returns:
            True if DPE ratio analysis should be used
        """
        # Must have baiting enabled
        if not getattr(poke, 'bait_shields', False):
            return False
        
        # Opponent must have shields
        if opponent.shields <= 0:
            return False
        
        # Must have multiple charged moves
        active_moves = ActionLogic.get_active_charged_moves(poke)
        if len(active_moves) < 2:
            return False
        
        # Must have energy for at least one alternative move
        for move in active_moves:
            if move != current_move and poke.energy >= move.energy_cost:
                return True
        
        return False
    
    # ========== MOVE REORDERING LOGIC METHODS (Step 1L) ==========
    
    @staticmethod
    def apply_move_reordering_logic(poke: Pokemon, opponent: Pokemon, 
                                   optimal_moves: List[ChargedMove], 
                                   active_charged_moves: List[ChargedMove],
                                   needs_boost: bool = False,
                                   debuffing_move: bool = False,
                                   battle = None) -> List[ChargedMove]:
        """
        Apply move reordering logic based on JavaScript ActionLogic lines 849-878.
        
        Reordering rules:
        1. If not baiting shields or shields are down (and no debuffing moves), sort by damage
        2. If shields are up, prefer low energy moves that are more efficient
        3. If shields are down, prefer non-debuffing moves in certain conditions
        4. Force more efficient moves of same/similar energy costs
        
        Args:
            poke: Pokemon making the decision
            opponent: Opponent Pokemon
            optimal_moves: Moves from DP algorithm
            active_charged_moves: All available charged moves
            needs_boost: Whether Pokemon needs stat boosts
            debuffing_move: Whether any move is debuffing
            battle: Battle instance for logging
            
        Returns:
            Reordered list of moves
        """
        if not optimal_moves:
            return optimal_moves
        
        # Make a copy to avoid modifying the original
        reordered_moves = optimal_moves.copy()
        
        # Rule 1: If pokemon needs boost, we cannot reorder and no moves both buff and debuff
        if needs_boost:
            return reordered_moves
        
        # Rule 2: If not baiting shields or shields are down and no moves debuff, throw most damaging move first
        if (not getattr(poke, 'bait_shields', False) or 
            (opponent.shields == 0 and not debuffing_move)):
            
            ActionLogic._sort_moves_by_damage(poke, opponent, reordered_moves, battle)
        
        # Rule 3: If shields are up, prefer low energy moves that are more efficient
        if (opponent.shields > 0 and len(active_charged_moves) > 1 and 
            len(reordered_moves) > 0):
            
            reordered_moves[0] = ActionLogic._prefer_efficient_low_energy_move(
                poke, opponent, reordered_moves[0], active_charged_moves, battle)
        
        # Rule 4: If shields are down, prefer non-debuffing moves if both sides have significant HP remaining
        if (opponent.shields == 0 and len(active_charged_moves) > 1 and 
            len(reordered_moves) > 0):
            
            reordered_moves[0] = ActionLogic._prefer_non_debuffing_move_shields_down(
                poke, opponent, reordered_moves[0], active_charged_moves, battle)
        
        # Rule 5: Force more efficient move of the same energy
        if len(active_charged_moves) > 1 and len(reordered_moves) > 0:
            reordered_moves[0] = ActionLogic._force_efficient_same_energy_move(
                poke, opponent, reordered_moves[0], active_charged_moves, battle)
        
        # Rule 6: Force more efficient move of similar energy if chosen move is self debuffing
        if len(active_charged_moves) > 1 and len(reordered_moves) > 0:
            reordered_moves[0] = ActionLogic._force_efficient_similar_energy_move(
                poke, opponent, reordered_moves[0], active_charged_moves, battle)
        
        return reordered_moves
    
    @staticmethod
    def _sort_moves_by_damage(poke: Pokemon, opponent: Pokemon, moves: List[ChargedMove], battle = None):
        """
        Sort moves by damage output (highest damage first).
        
        Based on JavaScript ActionLogic lines 853-857.
        """
        def damage_comparator(move_a, move_b):
            damage_a = DamageCalculator.calculate_damage(poke, opponent, move_a)
            damage_b = DamageCalculator.calculate_damage(poke, opponent, move_b)
            return damage_b - damage_a  # Sort descending (highest damage first)
        
        # Python equivalent of JavaScript sort with custom comparator
        from functools import cmp_to_key
        moves.sort(key=cmp_to_key(damage_comparator))
        
        if battle and len(moves) > 1:
            ActionLogic._log_decision(battle, poke, f" reordering: sorted moves by damage")
    
    @staticmethod
    def _prefer_efficient_low_energy_move(poke: Pokemon, opponent: Pokemon, 
                                         current_move: ChargedMove, 
                                         active_charged_moves: List[ChargedMove],
                                         battle = None) -> ChargedMove:
        """
        Prefer low energy moves that are more efficient when shields are up.
        
        Based on JavaScript ActionLogic line 862:
        poke.activeChargedMoves[0].energy <= finalState.moves[0].energy && 
        poke.activeChargedMoves[0].dpe > finalState.moves[0].dpe && 
        (! poke.activeChargedMoves[0].selfDebuffing)
        """
        if len(active_charged_moves) < 1:
            return current_move
        
        # Get the lowest energy move (first in activeChargedMoves)
        lowest_energy_move = active_charged_moves[0]
        
        # Check conditions from JavaScript
        if (lowest_energy_move.energy_cost <= current_move.energy_cost and
            ActionLogic.calculate_move_dpe(poke, opponent, lowest_energy_move) > 
            ActionLogic.calculate_move_dpe(poke, opponent, current_move) and
            not getattr(lowest_energy_move, 'self_debuffing', False)):
            
            if battle:
                ActionLogic._log_decision(battle, poke, 
                    f" reordering: preferring efficient low energy move {lowest_energy_move.move_id}")
            return lowest_energy_move
        
        return current_move
    
    @staticmethod
    def _prefer_non_debuffing_move_shields_down(poke: Pokemon, opponent: Pokemon,
                                               current_move: ChargedMove,
                                               active_charged_moves: List[ChargedMove],
                                               battle = None) -> ChargedMove:
        """
        Prefer non-debuffing moves when shields are down if both sides have significant HP.
        
        Based on JavaScript ActionLogic line 867:
        finalState.moves[0].selfDebuffing && finalState.moves[0].energy > 50 && 
        (poke.hp / poke.stats.hp) > .5 && (finalState.moves[0].damage / opponent.hp) < .8
        """
        if (not getattr(current_move, 'self_debuffing', False) or
            current_move.energy_cost <= 50 or
            len(active_charged_moves) < 1):
            return current_move
        
        # Check HP conditions
        poke_hp_ratio = poke.current_hp / poke.stats.hp
        move_damage = DamageCalculator.calculate_damage(poke, opponent, current_move)
        damage_ratio = move_damage / opponent.current_hp
        
        if poke_hp_ratio > 0.5 and damage_ratio < 0.8:
            # Look for non-debuffing alternative (typically activeChargedMoves[0])
            alternative_move = active_charged_moves[0]
            if not getattr(alternative_move, 'self_debuffing', False):
                if battle:
                    ActionLogic._log_decision(battle, poke,
                        f" reordering: preferring non-debuffing move {alternative_move.move_id} (shields down)")
                return alternative_move
        
        return current_move
    
    @staticmethod
    def _force_efficient_same_energy_move(poke: Pokemon, opponent: Pokemon,
                                         current_move: ChargedMove,
                                         active_charged_moves: List[ChargedMove],
                                         battle = None) -> ChargedMove:
        """
        Force more efficient move of the same energy cost.
        
        Based on JavaScript ActionLogic line 872:
        poke.activeChargedMoves[0].energy == finalState.moves[0].energy && 
        poke.activeChargedMoves[0].dpe > finalState.moves[0].dpe && 
        (! poke.activeChargedMoves[0].selfDebuffing)
        """
        if len(active_charged_moves) < 1:
            return current_move
        
        alternative_move = active_charged_moves[0]
        
        if (alternative_move.energy_cost == current_move.energy_cost and
            ActionLogic.calculate_move_dpe(poke, opponent, alternative_move) >
            ActionLogic.calculate_move_dpe(poke, opponent, current_move) and
            not getattr(alternative_move, 'self_debuffing', False)):
            
            if battle:
                ActionLogic._log_decision(battle, poke,
                    f" reordering: forcing efficient same energy move {alternative_move.move_id}")
            return alternative_move
        
        return current_move
    
    @staticmethod
    def _force_efficient_similar_energy_move(poke: Pokemon, opponent: Pokemon,
                                            current_move: ChargedMove,
                                            active_charged_moves: List[ChargedMove],
                                            battle = None) -> ChargedMove:
        """
        Force more efficient move of similar energy if chosen move is self debuffing.
        
        Based on JavaScript ActionLogic line 877:
        poke.activeChargedMoves[0].energy - 10 <= finalState.moves[0].energy && 
        poke.activeChargedMoves[0].dpe > finalState.moves[0].dpe && 
        finalState.moves[0].selfDebuffing && (! poke.activeChargedMoves[0].selfDebuffing)
        """
        if (len(active_charged_moves) < 1 or
            not getattr(current_move, 'self_debuffing', False)):
            return current_move
        
        alternative_move = active_charged_moves[0]
        
        if (alternative_move.energy_cost - 10 <= current_move.energy_cost and
            ActionLogic.calculate_move_dpe(poke, opponent, alternative_move) >
            ActionLogic.calculate_move_dpe(poke, opponent, current_move) and
            not getattr(alternative_move, 'self_debuffing', False)):
            
            if battle:
                ActionLogic._log_decision(battle, poke,
                    f" reordering: forcing efficient similar energy move {alternative_move.move_id} (avoiding debuff)")
            return alternative_move
        
        return current_move
    
    # ========== ADVANCED LETHAL DETECTION METHODS (Step 1H) ==========
    
    @staticmethod
    def check_multi_move_lethal(poke: Pokemon, opponent: Pokemon) -> Tuple[bool, List[ChargedMove]]:
        """
        Check if combination of moves can KO opponent (e.g., charged move + fast move).
        
        Args:
            poke: Pokemon checking for lethal combinations
            opponent: Opponent Pokemon
            
        Returns:
            Tuple of (can_ko: bool, move_sequence: List[ChargedMove])
        """
        # Only check when opponent has no shields (matches basic lethal detection logic)
        if opponent.shields > 0:
            return False, []
        
        # Don't check if farming energy
        if getattr(poke, 'farm_energy', False):
            return False, []
        
        # Get active charged moves
        active_charged_moves = []
        if poke.charged_move_1:
            active_charged_moves.append(poke.charged_move_1)
        if poke.charged_move_2:
            active_charged_moves.append(poke.charged_move_2)
        
        # Check charged move + fast move combinations
        for charged_move in active_charged_moves:
            if poke.energy >= charged_move.energy_cost:
                charged_damage = ActionLogic.calculate_lethal_damage(poke, opponent, charged_move)
                fast_damage = ActionLogic.calculate_lethal_damage(poke, opponent, poke.fast_move)
                
                # Calculate remaining HP after charged move
                remaining_hp = opponent.current_hp - charged_damage
                
                # Check if fast move can finish the opponent
                if remaining_hp > 0 and fast_damage >= remaining_hp:
                    # Apply same constraints as basic lethal detection
                    if (not getattr(charged_move, 'self_debuffing', False) and
                        opponent.current_hp > poke.fast_move.damage):  # Don't use if opponent would faint from fast move anyway
                        return True, [charged_move]  # Return just the charged move, fast move is implied
        
        return False, []
    
    @staticmethod
    def calculate_buffed_lethal_damage(attacker: Pokemon, defender: Pokemon, move: ChargedMove, 
                                     attack_buff: int = 0, defense_buff: int = 0) -> int:
        """
        Calculate lethal damage considering current buff/debuff states.
        
        Args:
            attacker: Pokemon using the move
            defender: Pokemon receiving the move
            move: Move being used
            attack_buff: Attack buff stage (-4 to +4)
            defense_buff: Defense buff stage (-4 to +4)
            
        Returns:
            Expected damage with buffs applied
        """
        # Get current attack multiplier
        attack_multiplier = ActionLogic.get_attack_multiplier(attack_buff)
        
        # Get current defense multiplier  
        defense_multiplier = ActionLogic.get_defense_multiplier(defense_buff)
        
        # Calculate base damage with standard method first
        base_damage = DamageCalculator.calculate_damage(attacker, defender, move)
        
        # Apply buff multipliers to the damage
        # This is a simplified approach - in a full implementation, we'd modify the stats before damage calculation
        buffed_damage = int(base_damage * attack_multiplier / defense_multiplier)
        
        return max(1, buffed_damage)  # Minimum 1 damage
    
    @staticmethod
    def get_attack_multiplier(buff_stage: int) -> float:
        """Convert buff stage to attack multiplier."""
        multipliers = {-4: 0.5, -3: 0.571, -2: 0.667, -1: 0.8, 0: 1.0, 
                      1: 1.25, 2: 1.5, 3: 1.75, 4: 2.0}
        return multipliers.get(buff_stage, 1.0)
    
    @staticmethod
    def get_defense_multiplier(buff_stage: int) -> float:
        """Convert buff stage to defense multiplier."""
        multipliers = {-4: 2.0, -3: 1.75, -2: 1.5, -1: 1.25, 0: 1.0,
                      1: 0.8, 2: 0.667, 3: 0.571, 4: 0.5}
        return multipliers.get(buff_stage, 1.0)
    
    @staticmethod
    def handle_special_lethal_cases(poke: Pokemon, opponent: Pokemon) -> Tuple[bool, Optional[ChargedMove]]:
        """
        Handle special lethal scenarios.
        
        Args:
            poke: Pokemon checking for special lethal cases
            opponent: Opponent Pokemon
            
        Returns:
            Tuple of (can_ko: bool, lethal_move: Optional[ChargedMove])
            
        Cases:
        1. Opponent at 1 HP (any move is lethal)
        2. Opponent with very low HP (2-5 HP)
        3. Self-debuffing moves that might still be lethal
        """
        # Only check when opponent has no shields (consistent with basic lethal detection)
        if opponent.shields > 0:
            return False, None
        
        # Don't check if farming energy
        if getattr(poke, 'farm_energy', False):
            return False, None
        
        # Case 1: Opponent at 1 HP (common after shielded charged move)
        if opponent.current_hp == 1:
            # Any move will KO, prefer fast move to save energy (but we return None for fast move)
            # Check if we have any charged moves available first
            active_charged_moves = []
            if poke.charged_move_1:
                active_charged_moves.append(poke.charged_move_1)
            if poke.charged_move_2:
                active_charged_moves.append(poke.charged_move_2)
            
            # If we have charged moves with energy, use the most efficient one
            available_moves = []
            for move in active_charged_moves:
                if poke.energy >= move.energy_cost:
                    available_moves.append(move)
            
            if available_moves:
                # Use the lowest energy cost move
                best_move = min(available_moves, key=lambda m: m.energy_cost)
                return True, best_move
            else:
                # Use fast move (return None to indicate fast move)
                return True, None
        
        # Case 2: Very low HP opponent (2-5 HP)
        if 2 <= opponent.current_hp <= 5:
            # Check if fast move is sufficient (return None for fast move)
            fast_damage = ActionLogic.calculate_lethal_damage(poke, opponent, poke.fast_move)
            if fast_damage >= opponent.current_hp:
                return True, None  # Use fast move
        
        # Case 3: Self-debuffing moves (like Superpower) - check if they're still lethal
        active_charged_moves = []
        if poke.charged_move_1:
            active_charged_moves.append(poke.charged_move_1)
        if poke.charged_move_2:
            active_charged_moves.append(poke.charged_move_2)
        
        for move in active_charged_moves:
            if (poke.energy >= move.energy_cost and 
                getattr(move, 'self_debuffing', False)):
                # Calculate damage before self-debuff applies
                damage = ActionLogic.calculate_lethal_damage(poke, opponent, move)
                if damage >= opponent.current_hp:
                    return True, move
        
        return False, None
    
    @staticmethod
    def select_best_lethal_move_advanced(lethal_moves: List[Tuple[ChargedMove, int, int]], 
                                       multi_move_options: List[ChargedMove],
                                       special_case_move: Optional[ChargedMove]) -> ChargedMove:
        """
        Select the most efficient lethal move from all available options.
        
        Args:
            lethal_moves: List of (move, damage, index) tuples from basic detection
            multi_move_options: List of moves from multi-move combinations
            special_case_move: Move from special case handling
            
        Returns:
            The best lethal move based on priority ordering
            
        Priority order (matching JavaScript ActionLogic behavior):
        1. Fast moves (represented as None - handled by caller)
        2. Special case moves (opponent at 1 HP) - prefer lowest energy cost
        3. Single lethal moves - prefer move index 0, then lowest energy cost
        4. Buffed lethal moves - prefer lowest energy cost
        5. Multi-move combinations (as backup) - prefer lowest energy cost
        """
        all_options = []
        
        # Add basic lethal moves with JavaScript-style priority
        for move, damage, index in lethal_moves:
            # JavaScript prefers move index 0 over index 1, then energy efficiency
            priority_score = (index * 1000) + move.energy_cost  # Index 0 gets lower score
            all_options.append((move, priority_score, 'basic', index, damage))
        
        # Add multi-move options (these require charged + fast, so higher priority score)
        for move in multi_move_options:
            # Multi-move combinations are less efficient, significant penalty
            priority_score = 5000 + move.energy_cost  # High base score for multi-move
            all_options.append((move, priority_score, 'multi', 0, 0))
        
        # Add special case move
        if special_case_move:
            # Special cases get high priority (very low score)
            priority_score = special_case_move.energy_cost  # Just energy cost, no penalties
            all_options.append((special_case_move, priority_score, 'special', 0, 0))
        
        if not all_options:
            return None
        
        # Sort by priority score (lower is better)
        # This naturally handles: special cases first, then basic moves by index/energy, then multi-moves
        all_options.sort(key=lambda x: x[1])
        
        return all_options[0][0]  # Return the best move
    
    @staticmethod
    def calculate_move_efficiency_score(move: ChargedMove, damage: int, move_type: str, index: int = 0) -> float:
        """
        Calculate efficiency score for lethal move prioritization.
        
        Args:
            move: The charged move
            damage: Damage the move would deal
            move_type: Type of lethal detection ('basic', 'multi', 'special', 'buffed')
            index: Move index (0 or 1)
            
        Returns:
            Efficiency score (lower is better)
        """
        # Base score is energy cost
        score = move.energy_cost
        
        # JavaScript-style move index preference (index 0 preferred)
        if move_type == 'basic':
            score += index * 100  # Penalty for move index 1
        
        # Type-based adjustments
        type_penalties = {
            'special': -50,    # Special cases get priority
            'basic': 0,        # No penalty for basic lethal moves
            'buffed': 25,      # Slight penalty for buffed moves (less reliable)
            'multi': 200       # Significant penalty for multi-move combinations
        }
        
        score += type_penalties.get(move_type, 0)
        
        # Slight preference for higher damage (overkill scenarios)
        # But energy efficiency is more important
        score -= (damage / 100)  # Small bonus for higher damage
        
        # Penalty for self-debuffing moves (like Superpower)
        if getattr(move, 'self_debuffing', False):
            score += 50
        
        return score
    
    @staticmethod
    def _create_temp_pokemon_from_state(poke: Pokemon, state: BattleState) -> Pokemon:
        """
        Create a temporary Pokemon object with state values for lethal detection.
        
        Args:
            poke: Original Pokemon
            state: Current DP state
            
        Returns:
            Temporary Pokemon with state values
        """
        # Create a shallow copy of the Pokemon and update state values
        import copy
        temp_poke = copy.copy(poke)
        
        # Update with state values
        temp_poke.energy = state.energy
        temp_poke.current_hp = poke.current_hp  # HP doesn't change in DP states for attacker
        
        # Apply buff state to attack stat (temporary for calculation)
        if hasattr(temp_poke, 'stat_buffs'):
            temp_poke.stat_buffs = [state.buffs, temp_poke.stat_buffs[1]]
        else:
            temp_poke.stat_buffs = [state.buffs, 0]
        
        return temp_poke
    
    @staticmethod
    def _create_temp_opponent_from_state(opponent: Pokemon, state: BattleState) -> Pokemon:
        """
        Create a temporary opponent Pokemon object with state values for lethal detection.
        
        Args:
            opponent: Original opponent Pokemon
            state: Current DP state
            
        Returns:
            Temporary opponent with state values
        """
        # Create a shallow copy of the opponent and update state values
        import copy
        temp_opponent = copy.copy(opponent)
        
        # Update with state values
        temp_opponent.current_hp = state.opp_health
        temp_opponent.shields = state.opp_shields
        # Opponent energy doesn't change in our DP states, so keep original
        
        return temp_opponent

    @staticmethod
    def boost_lethal_move_weight(options: List[DecisionOption], poke: Pokemon, opponent: Pokemon) -> None:
        """
        Boost the weight of lethal moves in decision options.
        
        Args:
            options: List of decision options to modify
            poke: Current Pokemon
            opponent: Opponent Pokemon
        """
        for option in options:
            # Check if this option represents a lethal move
            if option.move:
                # Calculate damage for this move
                damage = DamageCalculator.calculate_damage(poke, opponent, option.move)
                
                # Account for shields
                if opponent.shields > 0:
                    damage = 1  # Shields reduce charged move damage to 1
                
                if damage >= opponent.current_hp:
                    # Significantly boost weight for lethal moves
                    option.weight *= 10
                    
                    # Extra boost for energy-efficient lethal moves
                    if option.move.energy_cost <= 35:
                        option.weight *= 2  # Low-cost charged moves get extra boost
                    
                    # Slight penalty for self-debuffing lethal moves (still prioritized but less so)
                    if getattr(option.move, 'self_debuffing', False):
                        option.weight = int(option.weight * 0.8)

    @staticmethod
    def can_ko_opponent_advanced(poke: Pokemon, opponent: Pokemon) -> Tuple[bool, Optional[ChargedMove]]:
        """
        Advanced lethal move detection that combines all detection methods.
        
        Args:
            poke: Pokemon checking for lethal moves
            opponent: Opponent Pokemon
            
        Returns:
            Tuple of (can_ko: bool, lethal_move: Optional[ChargedMove])
            None for lethal_move indicates fast move should be used
        """
        # Check basic lethal moves first
        basic_lethal, basic_move = ActionLogic.can_ko_opponent(poke, opponent)
        
        # Check multi-move combinations
        multi_lethal, multi_moves = ActionLogic.check_multi_move_lethal(poke, opponent)
        
        # Check special cases
        special_lethal, special_move = ActionLogic.handle_special_lethal_cases(poke, opponent)
        
        # Check buff-enhanced lethal moves (moves that aren't normally lethal but become lethal with buffs)
        buff_lethal, buff_move = ActionLogic.check_buffed_lethal_moves(poke, opponent)
        
        # If no lethal options found
        if not (basic_lethal or multi_lethal or special_lethal or buff_lethal):
            return False, None
        
        # Handle fast move case (special case returned None)
        if special_lethal and special_move is None:
            return True, None  # Use fast move
        
        # Collect all lethal moves for priority selection
        lethal_moves = []
        if basic_lethal and basic_move:
            # Find the index of the basic move
            move_index = 0
            if poke.charged_move_1 == basic_move:
                move_index = 0
            elif poke.charged_move_2 == basic_move:
                move_index = 1
            
            damage = ActionLogic.calculate_lethal_damage(poke, opponent, basic_move)
            lethal_moves.append((basic_move, damage, move_index))
        
        # Add buff-enhanced lethal moves
        if buff_lethal and buff_move:
            move_index = 0
            if poke.charged_move_1 == buff_move:
                move_index = 0
            elif poke.charged_move_2 == buff_move:
                move_index = 1
            
            # Get current buff states
            attack_buff = getattr(poke, 'stat_buffs', [0, 0])[0] if hasattr(poke, 'stat_buffs') else 0
            defense_buff = getattr(opponent, 'stat_buffs', [0, 0])[1] if hasattr(opponent, 'stat_buffs') else 0
            
            damage = ActionLogic.calculate_buffed_lethal_damage(poke, opponent, buff_move, attack_buff, defense_buff)
            lethal_moves.append((buff_move, damage, move_index))
        
        multi_move_options = multi_moves if multi_lethal else []
        
        # Select the best option
        best_move = ActionLogic.select_best_lethal_move_advanced(
            lethal_moves, multi_move_options, special_move
        )
        
        return True, best_move
    
    @staticmethod
    def check_buffed_lethal_moves(poke: Pokemon, opponent: Pokemon) -> Tuple[bool, Optional[ChargedMove]]:
        """
        Check if any moves become lethal when considering current buff/debuff states.
        
        Args:
            poke: Pokemon checking for buffed lethal moves
            opponent: Opponent Pokemon
            
        Returns:
            Tuple of (can_ko: bool, lethal_move: Optional[ChargedMove])
        """
        # Only check when opponent has no shields (consistent with other lethal detection)
        if opponent.shields > 0:
            return False, None
        
        # Don't check if farming energy
        if getattr(poke, 'farm_energy', False):
            return False, None
        
        # Get current buff states
        attack_buff = getattr(poke, 'stat_buffs', [0, 0])[0] if hasattr(poke, 'stat_buffs') else 0
        defense_buff = getattr(opponent, 'stat_buffs', [0, 0])[1] if hasattr(opponent, 'stat_buffs') else 0
        
        # If no buffs are active, skip this check
        if attack_buff == 0 and defense_buff == 0:
            return False, None
        
        # Get active charged moves
        active_charged_moves = []
        if poke.charged_move_1:
            active_charged_moves.append(poke.charged_move_1)
        if poke.charged_move_2:
            active_charged_moves.append(poke.charged_move_2)
        
        # Check each charged move with buff consideration
        for move in active_charged_moves:
            if poke.energy >= move.energy_cost:
                # Calculate damage with current buffs
                buffed_damage = ActionLogic.calculate_buffed_lethal_damage(
                    poke, opponent, move, attack_buff, defense_buff
                )
                
                # Calculate normal damage for comparison
                normal_damage = ActionLogic.calculate_lethal_damage(poke, opponent, move)
                
                # Only consider this a "buffed lethal" if buffs made the difference
                if buffed_damage >= opponent.current_hp and normal_damage < opponent.current_hp:
                    # Apply same constraints as basic lethal detection
                    if (not getattr(move, 'self_debuffing', False) and
                        opponent.current_hp > poke.fast_move.damage):
                        return True, move
        
        return False, None
    
    @staticmethod
    def _log_decision(battle, poke: Pokemon, message: str):
        """Log a decision for debugging purposes."""
        if hasattr(battle, 'log_decision'):
            battle.log_decision(poke, message)
        # Could also print or log to a file for debugging


# Legacy compatibility methods
class BattleAI:
    """
    Legacy wrapper for ActionLogic to maintain compatibility.
    """
    
    @staticmethod
    def decide_action(attacker: Pokemon, defender: Pokemon, 
                     battle_context: Optional[Dict] = None) -> Dict:
        """
        Decide the best action for a Pokemon using the full AI logic.
        
        Args:
            attacker: Pokemon making the decision
            defender: Opponent Pokemon
            battle_context: Additional battle context (shields, time, etc.)
            
        Returns:
            Action dictionary with type and move
        """
        # Create a mock battle object for the ActionLogic
        class MockBattle:
            def __init__(self):
                self.current_turn = battle_context.get('turn', 0) if battle_context else 0
            
            def log_decision(self, poke, message):
                pass  # Could implement logging here
        
        mock_battle = MockBattle()
        action = ActionLogic.decide_action(mock_battle, attacker, defender)
        
        if action:
            return {
                "type": action.action_type,
                "move": attacker.charged_move_1 if action.value == 0 else attacker.charged_move_2,
                "target": 0
            }
        
        # Use fast move
        return {
            "type": "fast", 
            "move": attacker.fast_move,
            "target": 0
        }
    
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
        
        # Create a mock battle object
        class MockBattle:
            def get_mode(self):
                return "simulate"
        
        mock_battle = MockBattle()
        decision = ActionLogic.would_shield(mock_battle, attacker, defender, incoming_move)
        return decision.value