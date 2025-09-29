# Battle AI Port - Missing Components from ActionLogic.js

## Overview
The Python implementation of PvPoke's battle AI is currently **~40% complete**. The JavaScript ActionLogic.js contains ~900 lines of sophisticated decision-making logic, and we've now implemented the core DP queue loop structure and Move Timing Optimization with comprehensive testing.

## Missing Battle AI Components

### **1. INCOMPLETE MAIN DECISION LOGIC** 
The Python `decide_action` method is only **partially implemented** (lines 270-273 show "simplified" placeholder). The JavaScript version has **~900 lines** of complex decision-making logic that's missing:

- **Dynamic Programming Algorithm**: The massive DP queue system (lines 400-763 in JS) for optimal move sequencing
    - ✅ Step 1A: Implement the Basic DP Queue Structure (COMPLETED)
        - ✅ Add the DP queue initialization
        - ✅ Implement the main while DPQueue loop structure
        - ✅ Add basic state processing (without all the complex logic)
        - ✅ Add the state count limit to prevent infinite loops
        - ✅ Add comprehensive tests for the loop structure
        - This foundation is now complete with ~40 lines of code and full test coverage.
    - ✅ Step 1B: Add State Management
        - ✅ Implement state creation and queuing
        - ✅ Add buff capping logic (Math.min(4, Math.max(-4, buffs)))
        - ✅ Add the victory condition check (currState.oppHealth <= 0)
    - ✅ Step 1C: Add Move Evaluation Loop (COMPLETED)
        - ✅ Implement the charged move readiness calculation
        - ✅ Add comprehensive tests for charged move readiness
        - ✅ Verify calculation matches JavaScript behavior exactly
- **Move Timing Optimization**: Logic to reduce free turns (lines 237-345 in JS)
    - ✅ Step 1D: Implement Target Cooldown Calculation
        - ✅ Add `optimize_move_timing` flag to Pokemon class
        - ✅ Implement cooldown-based targeting logic (500ms default, 1000ms for slow moves)
        - ✅ Add special case handling for different move duration combinations
        - ✅ Add logic to disable optimization for same/evenly divisible move durations
    - ✅ Step 1E: Add Timing Optimization Checks
        - ✅ Implement faint prevention check (don't optimize if about to faint from fast move)
        - ✅ Add energy overflow prevention (don't go over 100 energy with queued fast moves)
        - ✅ Add turns-to-live vs planned-turns comparison
        - ✅ Add lethal charged move detection (don't optimize if can KO opponent)
        - ✅ Add opponent lethal move prevention (don't optimize if opponent can KO)
        - ✅ Add fast move KO prevention within timing window
    - ✅ Step 1F: Integrate Battle Context Methods (COMPLETED)
        - ✅ Implement `get_queued_actions()` method in Battle class
        - ✅ Add `log_decision()` method for debugging output
        - ✅ Add queued fast move counting logic
        - ✅ Add timing optimization return logic (early exit when optimizing)
        - ✅ Add main `optimize_move_timing()` method with full integration
        - ✅ Add comprehensive test coverage for all Step 2C components  
- **Lethal Move Detection**: Throwing moves that will KO the opponent (lines 210-234 in JS)
    - ✅ Step 1G: Implement Basic Lethal Move Detection (COMPLETED)
        - ✅ Add `can_ko_opponent()` method to check if any charged move can KO
        - ✅ Implement damage calculation with shield consideration
        - ✅ Add energy requirement validation
        - ✅ Add basic lethal move selection logic
        - ✅ Integrate lethal detection into main `decide_action()` method
        - ✅ Add comprehensive test coverage for all lethal detection scenarios
    - ✅ Step 1H: Add Advanced Lethal Detection Logic (COMPLETED)
        - ✅ Implement multi-move lethal combinations (charged + fast moves)
        - ✅ Add buff/debuff consideration in damage calculations
        - ✅ Handle special cases (opponent at 1 HP after shield)
        - ✅ Add priority ordering for multiple lethal moves
        - ✅ Add comprehensive test coverage for all advanced lethal detection scenarios
    - ✅ Step 1I: Integrate Lethal Detection with DP Algorithm (COMPLETED)
        - ✅ Add lethal move detection to DP state evaluation
        - ✅ Implement immediate victory state handling
        - ✅ Add lethal move weight boosting in decision options
        - ✅ Add comprehensive testing for lethal detection scenarios
- **Shield Baiting Logic**: Complex baiting strategies when shields are up (lines 820-847 in JS)
    - ✅ Step 1J: Implement Basic Shield Baiting Logic
        - ✅ Add `bait_shields` property to Pokemon class
        - ✅ Implement DPE (Damage Per Energy) calculation for moves
        - ✅ Add basic shield baiting decision logic
        - ✅ Integrate with `would_shield` prediction method
    - ✅ Step 1K: Add DPE Ratio Analysis (COMPLETED)
        - ✅ Implement DPE ratio comparison between moves
        - ✅ Add 1.5x DPE ratio threshold logic
        - ✅ Add opponent shield prediction for move selection
        - ✅ Add energy requirement validation for bait moves
    - ✅ Step 1L: Implement Move Reordering Logic (COMPLETED)
        - ✅ Add move sorting by damage when not baiting
        - ✅ Implement low-energy move preference when shields are up
        - ✅ Add self-debuffing move avoidance during baiting
        - ✅ Add energy-efficient move selection logic
    - ✅ Step 1M: Add Advanced Baiting Conditions (COMPLETED)
        - ✅ Implement "build up to expensive move" logic
        - ✅ Add self-buffing move exception handling
        - ✅ Add low health baiting prevention
        - ✅ Add close DPE move handling (within 10 energy)
    - ⏳ Step 1N: Integrate Shield Baiting with DP Algorithm
        - ⏳ Add baiting logic to DP state evaluation
        - ⏳ Implement baiting weight calculation in decision options
        - ⏳ Add comprehensive testing for all baiting scenarios
        - ⏳ Validate against JavaScript behavior
- **Self-Debuffing Move Handling**: Special logic for moves like Superpower (lines 918-935 in JS)
- **Energy Stacking**: Logic to stack multiple uses of debuffing moves (lines 919-935 in JS)
- **Aegislash Form Logic**: Special handling for form changes (lines 957-966 in JS)

### **2. MISSING SUPPORTING CLASSES**
The Python implementation lacks the `DecisionOption` class:

```python
@dataclass
class DecisionOption:
    name: str
    weight: int
```

### **3. INCOMPLETE SHIELD DECISION LOGIC**
The `would_shield` method exists but is **missing critical components**:
- **Buff/Debuff Handling**: Temporary stat changes during shield calculations
- **Cycle Damage Calculations**: Complex multi-turn damage projections
- **Attack Debuffing Move Detection**: Special shielding for moves like Superpower

### **4. MISSING POKEMON PROPERTIES**
The JavaScript version relies on Pokemon properties that may not exist in Python:
- `poke.activeChargedMoves` (vs current `charged_move_1/2`)
- `poke.fastestChargedMove` 
- `poke.bestChargedMove`
- `poke.farmEnergy` flag
- `poke.baitShields` setting
- `poke.optimizeMoveTiming` flag
- `poke.priority` for move ordering
- `poke.turnsToKO` calculation
- `opponent.turnsToKO` calculation

### **5. MISSING MOVE PROPERTIES**
Moves need additional properties:
- `move.selfDebuffing` flag
- `move.selfBuffing` flag  
- `move.selfAttackDebuffing` flag
- `move.buffApplyChance` probability
- `move.buffTarget` ("self" or "opponent")
- `move.buffs` array for stat changes
- `move.dpe` (damage per energy) calculation

### **6. MISSING BATTLE CONTEXT**
The battle system needs:
- `battle.getMode()` method ("simulate" vs "emulate")
- `battle.getQueuedActions()` for move timing optimization
- `battle.logDecision()` for debugging output
- Turn-based cooldown system integration

### **7. TRAINING AI INTEGRATION**
The JavaScript has a separate `TrainingAI` class with advanced features:
- **Switch Decision Logic**: When to switch Pokemon
- **Energy Guessing**: Estimating opponent energy levels  
- **Strategy Processing**: Different AI difficulty levels
- **Reaction Time Simulation**: Human-like delays

### **8. TIMELINE SYSTEM**
Missing timeline management:
- `TimelineEvent` class for battle history
- Action queuing and processing
- Turn-based execution order

## Move Timing Optimization - Detailed Implementation Plan

### Overview
Move Timing Optimization is a sophisticated system that prevents Pokemon from giving opponents "free turns" by timing charged moves optimally. The system analyzes fast move cooldowns and determines the best moments to throw charged moves to minimize opponent advantage.

### Core Concept
- **Free Turns**: When a Pokemon throws a charged move while the opponent is in the middle of a fast move, the opponent gets to complete their fast move "for free"
- **Target Cooldown**: The optimal opponent cooldown window (500ms or less) to throw charged moves
- **Timing Windows**: Calculated moments when throwing a charged move won't give the opponent extra fast moves

### Step 2A: Target Cooldown Calculation Logic

#### 2A.1: Basic Target Cooldown Rules
```python
def calculate_target_cooldown(self, poke: Pokemon, opponent: Pokemon) -> int:
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
```

#### 2A.2: Optimization Disabling Rules
```python
def should_disable_timing_optimization(self, poke: Pokemon, opponent: Pokemon) -> bool:
    """Check if timing optimization should be disabled."""
    
    # Disable for same duration moves (no advantage possible)
    if poke.fast_move.cooldown == opponent.fast_move.cooldown:
        return True
    
    # Disable for evenly divisible longer moves (e.g., 4-turn vs 2-turn, 3-turn vs 1-turn)
    if (poke.fast_move.cooldown % opponent.fast_move.cooldown == 0 and 
        poke.fast_move.cooldown > opponent.fast_move.cooldown):
        return True
    
    return False
```

### Step 2B: Timing Optimization Safety Checks

#### 2B.1: Survival Checks
```python
def check_survival_conditions(self, battle, poke: Pokemon, opponent: Pokemon) -> bool:
    """Verify Pokemon can safely optimize timing without fainting."""
    
    # Don't optimize if about to faint from opponent's fast move
    if poke.current_hp <= opponent.fast_move.damage:
        return False
    
    # Don't optimize if opponent can KO with fast moves during our fast move
    fast_moves_in_window = math.floor((poke.fast_move.cooldown + 500) / opponent.fast_move.cooldown)
    if poke.current_hp <= opponent.fast_move.damage * fast_moves_in_window:
        return False
    
    return True
```

#### 2B.2: Energy Management
```python
def check_energy_conditions(self, battle, poke: Pokemon) -> bool:
    """Ensure energy won't overflow with timing optimization."""
    
    # Count queued fast moves
    queued_fast_moves = 0
    queued_actions = battle.get_queued_actions()
    
    for action in queued_actions:
        if action.actor == poke.index and action.type == "fast":
            queued_fast_moves += 1
    
    # Add 1 for the fast move we're considering
    queued_fast_moves += 1
    
    # Don't optimize if we'll exceed 100 energy
    future_energy = poke.energy + (poke.fast_move.energy_gain * queued_fast_moves)
    if future_energy > 100:
        return False
    
    return True
```

#### 2B.3: Strategic Timing Checks
```python
def check_strategic_conditions(self, battle, poke: Pokemon, opponent: Pokemon, turns_to_live: int) -> bool:
    """Check strategic conditions for timing optimization."""
    
    # Calculate planned turns (fast move + charged moves we can throw)
    planned_turns = poke.fast_move.turns + math.floor(poke.energy / poke.active_charged_moves[0].energy_cost)
    
    # Add extra turn if we lose CMP (lower attack stat)
    if poke.stats.atk < opponent.stats.atk:
        planned_turns += 1
    
    # Don't optimize if we have fewer turns to live than planned actions
    if planned_turns > turns_to_live:
        return False
    
    # Don't optimize if we can KO opponent with a charged move (no shields)
    if opponent.shields == 0:
        for move in poke.active_charged_moves:
            move_damage = DamageCalculator.calculate_damage(poke, opponent, move)
            if poke.energy >= move.energy_cost and move_damage >= opponent.current_hp:
                return False
    
    # Don't optimize if opponent can KO us with their charged move
    for move in opponent.active_charged_moves:
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
```

### Step 2C: Battle Context Integration

#### 2C.1: Battle Class Extensions
```python
class Battle:
    def __init__(self):
        self.queued_actions = []  # List of TimelineAction objects
        self.debug_mode = False
    
    def get_queued_actions(self) -> List[TimelineAction]:
        """Return list of actions queued by all Pokemon."""
        return self.queued_actions
    
    def log_decision(self, pokemon: Pokemon, message: str) -> None:
        """Log AI decision for debugging."""
        if not self.debug_mode:
            return
        
        print(f"Turn {self.current_turn}: {pokemon.species_id} {message}")
```

#### 2C.2: Main Timing Optimization Logic
```python
def optimize_move_timing(self, battle, poke: Pokemon, opponent: Pokemon, turns_to_live: int) -> bool:
    """
    Main move timing optimization logic.
    
    Returns:
        True if should wait (optimize timing), False if should proceed with charged move
    """
    
    # Check if optimization is enabled
    if not getattr(poke, 'optimize_move_timing', False):
        return False
    
    # Calculate target cooldown
    target_cooldown = self.calculate_target_cooldown(poke, opponent)
    
    # Check if optimization should be disabled
    if self.should_disable_timing_optimization(poke, opponent):
        target_cooldown = 0
    
    # Only optimize if opponent is at target cooldown or higher, and target > 0
    if not ((opponent.cooldown == 0 or opponent.cooldown > target_cooldown) and target_cooldown > 0):
        return False
    
    # Run all safety and strategic checks
    if not self.check_survival_conditions(battle, poke, opponent):
        return False
    
    if not self.check_energy_conditions(battle, poke):
        return False
    
    if not self.check_strategic_conditions(battle, poke, opponent, turns_to_live):
        return False
    
    # All checks passed - optimize timing
    battle.log_decision(poke, " is optimizing move timing")
    return True  # Return early, don't throw charged move this turn
```

### Integration Points

#### Pokemon Class Extensions Needed:
- `optimize_move_timing: bool` - Flag to enable/disable timing optimization
- `active_charged_moves: List[Move]` - List of available charged moves
- `cooldown: int` - Current fast move cooldown (0 = ready to act)

#### Move Class Extensions Needed:
- `cooldown: int` - Move duration in milliseconds
- `turns: int` - Move duration in turns (cooldown / 500)
- `damage: int` - Cached damage calculation
- `energy_cost: int` - Energy required to use move
- `energy_gain: int` - Energy gained from using move (fast moves only)

#### Battle Class Extensions Needed:
- `get_queued_actions() -> List[TimelineAction]` - Return queued actions
- `log_decision(pokemon, message)` - Debug logging
- `current_turn: int` - Current battle turn number
- `debug_mode: bool` - Enable/disable debug output

### Testing Strategy

#### Unit Tests Needed:
1. **Target Cooldown Calculation**: Test all cooldown rules and edge cases
2. **Optimization Disabling**: Verify same/divisible move duration handling  
3. **Survival Checks**: Test faint prevention logic
4. **Energy Management**: Test overflow prevention
5. **Strategic Conditions**: Test turns-to-live and KO prevention logic
6. **Integration**: Test with Battle class methods

#### Integration Tests:
1. **Real Battle Scenarios**: Test optimization in actual battle simulations
2. **Performance Impact**: Ensure optimization doesn't slow down battles significantly
3. **JavaScript Parity**: Compare decisions with JavaScript implementation

### Performance Considerations
- Cache damage calculations where possible
- Limit queued action list size to prevent memory issues
- Consider disabling optimization in fast simulation modes
- Profile timing optimization impact on battle speed

## Lethal Move Detection - Detailed Implementation Plan

### Overview
Lethal Move Detection is a critical AI component that identifies when a Pokemon can knock out (KO) the opponent with available moves. This system ensures the AI prioritizes finishing moves when victory is achievable, preventing unnecessary prolonged battles or missed opportunities.

### Core Concept
- **Lethal Move**: Any move that can reduce opponent's HP to 0 or below
- **Shield Consideration**: Account for opponent shields reducing charged move damage to 1
- **Energy Validation**: Ensure Pokemon has sufficient energy to use the lethal move
- **Priority Ordering**: When multiple lethal moves exist, choose the most efficient one

### Step 1G: Basic Lethal Move Detection

#### 1G.1: Core Lethal Detection Method
```python
def can_ko_opponent(self, poke: Pokemon, opponent: Pokemon) -> Tuple[bool, Optional[Move]]:
    """
    Check if any available move can KO the opponent.
    
    Returns:
        Tuple of (can_ko: bool, lethal_move: Optional[Move])
    """
    lethal_moves = []
    
    # Check each charged move
    for move in poke.active_charged_moves:
        if poke.energy >= move.energy_cost:
            damage = self.calculate_lethal_damage(poke, opponent, move)
            if damage >= opponent.current_hp:
                lethal_moves.append((move, damage))
    
    # Check fast move (rare but possible at very low HP)
    fast_damage = self.calculate_lethal_damage(poke, opponent, poke.fast_move)
    if fast_damage >= opponent.current_hp:
        lethal_moves.append((poke.fast_move, fast_damage))
    
    if not lethal_moves:
        return False, None
    
    # Return the most efficient lethal move
    best_move = self.select_best_lethal_move(lethal_moves)
    return True, best_move
```

#### 1G.2: Lethal Damage Calculation
```python
def calculate_lethal_damage(self, attacker: Pokemon, defender: Pokemon, move: Move) -> int:
    """
    Calculate damage for lethal move detection, accounting for shields.
    
    Args:
        attacker: Pokemon using the move
        defender: Pokemon receiving the move
        move: Move being used
        
    Returns:
        Expected damage after shields/resistances
    """
    # Use standard damage calculation
    base_damage = DamageCalculator.calculate_damage(attacker, defender, move)
    
    # Account for shields on charged moves
    if move.move_type == "charged" and defender.shields > 0:
        # Shields reduce charged move damage to 1
        return 1
    
    return base_damage
```

#### 1G.3: Best Lethal Move Selection
```python
def select_best_lethal_move(self, lethal_moves: List[Tuple[Move, int]]) -> Move:
    """
    Select the most efficient lethal move from available options.
    
    Priority order:
    1. Fast moves (no energy cost)
    2. Lowest energy cost charged moves
    3. Highest damage (for overkill scenarios)
    """
    # Sort by priority: fast moves first, then by energy cost, then by damage
    def move_priority(move_damage_tuple):
        move, damage = move_damage_tuple
        if move.move_type == "fast":
            return (0, 0, -damage)  # Fast moves have highest priority
        else:
            return (1, move.energy_cost, -damage)  # Then by energy cost, then damage
    
    lethal_moves.sort(key=move_priority)
    return lethal_moves[0][0]  # Return the best move
```

### Step 1H: Advanced Lethal Detection Logic

#### 1H.1: Multi-Move Lethal Combinations
```python
def check_multi_move_lethal(self, poke: Pokemon, opponent: Pokemon) -> Tuple[bool, List[Move]]:
    """
    Check if combination of moves can KO opponent (e.g., charged move + fast move).
    
    Returns:
        Tuple of (can_ko: bool, move_sequence: List[Move])
    """
    # Check charged move + fast move combinations
    for charged_move in poke.active_charged_moves:
        if poke.energy >= charged_move.energy_cost:
            charged_damage = self.calculate_lethal_damage(poke, opponent, charged_move)
            fast_damage = self.calculate_lethal_damage(poke, opponent, poke.fast_move)
            
            total_damage = charged_damage + fast_damage
            
            # Account for potential HP after shield
            remaining_hp = opponent.current_hp
            if charged_move.move_type == "charged" and opponent.shields > 0:
                remaining_hp -= 1  # Shield reduces to 1 damage
            else:
                remaining_hp -= charged_damage
            
            # Check if fast move can finish
            if remaining_hp > 0 and fast_damage >= remaining_hp:
                return True, [charged_move, poke.fast_move]
    
    return False, []
```

#### 1H.2: Buff/Debuff Consideration
```python
def calculate_buffed_lethal_damage(self, attacker: Pokemon, defender: Pokemon, move: Move) -> int:
    """
    Calculate lethal damage considering current buff/debuff states.
    """
    # Get current attack multiplier
    attack_multiplier = self.get_attack_multiplier(attacker.attack_buff)
    
    # Get current defense multiplier  
    defense_multiplier = self.get_defense_multiplier(defender.defense_buff)
    
    # Calculate base damage with buffs
    base_damage = DamageCalculator.calculate_damage_with_buffs(
        attacker, defender, move, attack_multiplier, defense_multiplier
    )
    
    # Apply shield logic
    if move.move_type == "charged" and defender.shields > 0:
        return 1
    
    return base_damage

def get_attack_multiplier(self, buff_stage: int) -> float:
    """Convert buff stage to attack multiplier."""
    multipliers = {-4: 0.5, -3: 0.571, -2: 0.667, -1: 0.8, 0: 1.0, 
                  1: 1.25, 2: 1.5, 3: 1.75, 4: 2.0}
    return multipliers.get(buff_stage, 1.0)

def get_defense_multiplier(self, buff_stage: int) -> float:
    """Convert buff stage to defense multiplier."""
    multipliers = {-4: 2.0, -3: 1.75, -2: 1.5, -1: 1.25, 0: 1.0,
                  1: 0.8, 2: 0.667, 3: 0.571, 4: 0.5}
    return multipliers.get(buff_stage, 1.0)
```

#### 1H.3: Special Case Handling
```python
def handle_special_lethal_cases(self, poke: Pokemon, opponent: Pokemon) -> Tuple[bool, Optional[Move]]:
    """
    Handle special lethal scenarios.
    
    Cases:
    1. Opponent at 1 HP after shield (any move is lethal)
    2. Opponent with no shields but low HP
    3. Self-debuffing moves that might still be lethal
    """
    # Case 1: Opponent at 1 HP (common after shielded charged move)
    if opponent.current_hp == 1:
        # Any move will KO, prefer fast move to save energy
        return True, poke.fast_move
    
    # Case 2: Very low HP opponent (2-5 HP)
    if opponent.current_hp <= 5:
        # Check if fast move is sufficient
        fast_damage = self.calculate_lethal_damage(poke, opponent, poke.fast_move)
        if fast_damage >= opponent.current_hp:
            return True, poke.fast_move
    
    # Case 3: Self-debuffing moves (like Superpower)
    for move in poke.active_charged_moves:
        if poke.energy >= move.energy_cost and getattr(move, 'self_debuffing', False):
            # Calculate damage before self-debuff applies
            damage = self.calculate_lethal_damage(poke, opponent, move)
            if damage >= opponent.current_hp:
                return True, move
    
    return False, None
```

### Step 1I: Integration with DP Algorithm

#### 1I.1: DP State Lethal Check
```python
def evaluate_lethal_in_dp_state(self, state: DPState, poke: Pokemon, opponent: Pokemon) -> bool:
    """
    Check for lethal moves within DP algorithm state evaluation.
    
    Args:
        state: Current DP state being evaluated
        poke: Current Pokemon
        opponent: Opponent Pokemon
        
    Returns:
        True if lethal move found and state should be marked as victory
    """
    # Create temporary Pokemon with state values
    temp_poke = self.create_temp_pokemon_from_state(poke, state)
    temp_opponent = self.create_temp_opponent_from_state(opponent, state)
    
    # Check for lethal moves
    can_ko, lethal_move = self.can_ko_opponent(temp_poke, temp_opponent)
    
    if can_ko:
        # Mark this as a victory state
        state.victory = True
        state.best_move = lethal_move
        state.score = 1000  # High score for victory
        return True
    
    return False
```

#### 1I.2: Victory State Handling
```python
def handle_victory_state(self, state: DPState, lethal_move: Move) -> None:
    """
    Handle immediate victory when lethal move is found.
    
    Args:
        state: DP state that achieved victory
        lethal_move: The move that causes victory
    """
    # Set victory flag
    state.victory = True
    state.best_move = lethal_move
    
    # Set maximum score
    state.score = 1000
    
    # Clear opponent health to 0
    state.opp_health = 0
    
    # Log the victory
    self.battle.log_decision(state.pokemon, f"found lethal move: {lethal_move.name}")
```

#### 1I.3: Decision Weight Boosting
```python
def boost_lethal_move_weight(self, options: List[DecisionOption], poke: Pokemon, opponent: Pokemon) -> None:
    """
    Boost the weight of lethal moves in decision options.
    
    Args:
        options: List of decision options to modify
        poke: Current Pokemon
        opponent: Opponent Pokemon
    """
    for option in options:
        # Check if this option represents a lethal move
        if hasattr(option, 'move'):
            damage = self.calculate_lethal_damage(poke, opponent, option.move)
            if damage >= opponent.current_hp:
                # Significantly boost weight for lethal moves
                option.weight *= 10
                
                # Extra boost for energy-efficient lethal moves
                if option.move.move_type == "fast":
                    option.weight *= 2  # Fast moves cost no energy
                elif option.move.energy_cost <= 35:
                    option.weight *= 1.5  # Low-cost charged moves
```

### Integration Points

#### ActionLogic Class Extensions:
```python
class ActionLogic:
    def __init__(self, battle):
        self.battle = battle
        self.lethal_cache = {}  # Cache lethal calculations
    
    # Add all lethal detection methods here
    def can_ko_opponent(self, poke, opponent): ...
    def calculate_lethal_damage(self, attacker, defender, move): ...
    def select_best_lethal_move(self, lethal_moves): ...
    # ... etc
```

#### DP Algorithm Integration:
```python
def decide_action(self, poke: Pokemon, opponent: Pokemon) -> str:
    """Main decision method with lethal detection."""
    
    # Priority 1: Check for immediate lethal moves
    can_ko, lethal_move = self.can_ko_opponent(poke, opponent)
    if can_ko:
        self.battle.log_decision(poke, f"using lethal move: {lethal_move.name}")
        return lethal_move.name
    
    # Continue with DP algorithm for non-lethal scenarios
    # ... existing DP logic
```

### Testing Strategy

#### Unit Tests:
1. **Basic Lethal Detection**: Test single move KO scenarios
2. **Shield Interaction**: Test lethal detection with/without shields
3. **Energy Validation**: Test insufficient energy scenarios
4. **Multi-Move Combinations**: Test charged + fast move sequences
5. **Buff Consideration**: Test lethal detection with stat changes
6. **Special Cases**: Test 1 HP scenarios and edge cases

#### Integration Tests:
1. **DP Algorithm Integration**: Test lethal detection within DP states
2. **Decision Weight Boosting**: Verify lethal moves get priority
3. **Victory State Handling**: Test immediate victory scenarios
4. **Performance Impact**: Ensure lethal detection doesn't slow battles

#### Test Cases:
```python
def test_basic_lethal_detection():
    """Test basic lethal move detection."""
    # Setup: Opponent at 50 HP, Pokemon has 100 damage move with 50 energy
    # Expected: Should detect lethal move
    
def test_shield_blocks_lethal():
    """Test that shields prevent lethal detection."""
    # Setup: Opponent at 50 HP with 1 shield, Pokemon has 100 damage charged move
    # Expected: Should not detect as lethal (damage reduced to 1)
    
def test_fast_move_lethal():
    """Test fast move lethal detection."""
    # Setup: Opponent at 5 HP, Pokemon fast move does 10 damage
    # Expected: Should detect fast move as lethal
```

### Performance Considerations
- Cache lethal damage calculations for repeated checks
- Limit multi-move combination depth to prevent exponential complexity
- Use early returns when lethal move is found
- Consider disabling complex lethal detection in fast simulation modes

## Shield Baiting Logic - Detailed Implementation Plan

### Overview
Shield Baiting Logic is a sophisticated AI strategy that manipulates opponent shield usage by strategically choosing which charged moves to throw. The system analyzes move efficiency (DPE - Damage Per Energy) and predicts opponent shielding behavior to maximize damage output while conserving shields.

### Core Concept
- **Shield Baiting**: Using lower-energy, less efficient moves to force opponents to waste shields
- **DPE (Damage Per Energy)**: The efficiency metric `damage / energy_cost` used to compare moves
- **Bait Move**: A lower-energy move used to "bait" a shield before throwing a more powerful move
- **DPE Ratio**: Comparison between moves to determine if baiting is worthwhile (threshold: 1.5x)

### Step 2A: Basic Shield Baiting Logic

#### 2A.1: Pokemon Class Extensions
```python
class Pokemon:
    def __init__(self):
        # ... existing initialization
        self.bait_shields = False  # Flag to enable shield baiting behavior
        self.active_charged_moves = []  # List of available charged moves (sorted by energy cost)
    
    def calculate_move_dpe(self, move: Move, opponent: Pokemon) -> float:
        """
        Calculate Damage Per Energy for a move against specific opponent.
        
        Args:
            move: The move to calculate DPE for
            opponent: The target opponent
            
        Returns:
            DPE value (damage / energy_cost)
        """
        if move.energy_cost <= 0:
            return 0.0  # Fast moves have no energy cost
        
        damage = DamageCalculator.calculate_damage(self, opponent, move)
        
        # Account for buff effects in DPE calculation
        if hasattr(move, 'buffs') and move.buffs:
            buff_multiplier = self.calculate_buff_dpe_multiplier(move)
            damage *= buff_multiplier
        
        return damage / move.energy_cost
    
    def calculate_buff_dpe_multiplier(self, move: Move) -> float:
        """Calculate DPE multiplier for moves with buff effects."""
        if not hasattr(move, 'buffs') or not move.buffs:
            return 1.0
        
        buff_effect = 0
        
        # Self-buffing moves (attack buffs)
        if hasattr(move, 'buff_target') and move.buff_target == "self" and move.buffs[0] > 0:
            buff_effect = move.buffs[0] * (80 / move.energy_cost)
        
        # Opponent debuffing moves (defense debuffs)
        elif hasattr(move, 'buff_target') and move.buff_target == "opponent" and len(move.buffs) > 1 and move.buffs[1] < 0:
            buff_effect = abs(move.buffs[1]) * (80 / move.energy_cost)
        
        if buff_effect > 0:
            buff_apply_chance = getattr(move, 'buff_apply_chance', 1.0)
            buff_divisor = 4.0  # From GameMaster settings
            multiplier = (buff_divisor + (buff_effect * buff_apply_chance)) / buff_divisor
            return multiplier
        
        return 1.0
```

#### 2A.2: Basic Shield Baiting Decision
```python
def should_bait_shields(self, poke: Pokemon, opponent: Pokemon) -> Tuple[bool, Optional[Move]]:
    """
    Determine if Pokemon should bait shields and which move to use.
    
    Returns:
        Tuple of (should_bait: bool, bait_move: Optional[Move])
    """
    # Prerequisites for shield baiting
    if not poke.bait_shields:
        return False, None
    
    if opponent.shields <= 0:
        return False, None
    
    if len(poke.active_charged_moves) < 2:
        return False, None
    
    # Get moves sorted by energy cost (lowest first)
    moves = sorted(poke.active_charged_moves, key=lambda m: m.energy_cost)
    low_energy_move = moves[0]
    high_energy_move = moves[1]
    
    # Check if Pokemon has energy for both moves
    if poke.energy < low_energy_move.energy_cost:
        return False, None
    
    # Calculate DPE for both moves
    low_dpe = poke.calculate_move_dpe(low_energy_move, opponent)
    high_dpe = poke.calculate_move_dpe(high_energy_move, opponent)
    
    # Basic baiting condition: high energy move must be significantly more efficient
    if high_dpe / low_dpe < 1.2:  # Minimum efficiency threshold
        return False, None
    
    # Check if opponent would shield the low energy move
    shield_decision = self.would_shield(poke, opponent, low_energy_move)
    if not shield_decision['value']:
        return False, None  # No point baiting if opponent won't shield
    
    # Don't bait with self-debuffing moves
    if getattr(low_energy_move, 'self_debuffing', False):
        return False, None
    
    return True, low_energy_move
```

### Step 2B: DPE Ratio Analysis

#### 2B.1: Advanced DPE Ratio Logic
```python
def analyze_dpe_ratios(self, poke: Pokemon, opponent: Pokemon, current_move: Move) -> Optional[Move]:
    """
    Analyze DPE ratios to determine optimal move selection for baiting.
    
    Args:
        poke: Current Pokemon
        opponent: Opponent Pokemon  
        current_move: Currently selected move
        
    Returns:
        Better move if found, None otherwise
    """
    if not poke.bait_shields or opponent.shields <= 0 or len(poke.active_charged_moves) < 2:
        return None
    
    # Find the second move (higher energy, potentially higher DPE)
    second_move = None
    for move in poke.active_charged_moves:
        if move != current_move and poke.energy >= move.energy_cost:
            second_move = move
            break
    
    if not second_move:
        return None
    
    # Calculate DPE ratio
    current_dpe = poke.calculate_move_dpe(current_move, opponent)
    second_dpe = poke.calculate_move_dpe(second_move, opponent)
    
    if current_dpe <= 0:
        return None
    
    dpe_ratio = second_dpe / current_dpe
    
    # JavaScript uses 1.5x threshold for DPE ratio
    if dpe_ratio > 1.5:
        # Check if opponent would NOT shield the higher DPE move
        shield_decision = self.would_shield(poke, opponent, second_move)
        if not shield_decision['value']:
            return second_move  # Use the more efficient move if opponent won't shield
    
    return None
```

#### 2B.2: Energy Validation and Move Accessibility
```python
def validate_baiting_energy_requirements(self, poke: Pokemon, bait_move: Move, follow_up_move: Move) -> bool:
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
    
    # Check if Pokemon can survive the fast moves needed
    opponent_damage_per_turn = self.estimate_opponent_damage_per_turn(poke, opponent)
    total_damage_taken = opponent_damage_per_turn * fast_moves_needed
    
    return poke.current_hp > total_damage_taken
```

### Step 2C: Move Reordering Logic

#### 2C.1: Damage-Based Move Sorting
```python
def reorder_moves_by_damage(self, poke: Pokemon, opponent: Pokemon, moves: List[Move], baiting: bool) -> List[Move]:
    """
    Reorder moves based on damage output and baiting strategy.
    
    Args:
        poke: Current Pokemon
        opponent: Opponent Pokemon
        moves: List of available moves
        baiting: Whether currently baiting shields
        
    Returns:
        Reordered list of moves
    """
    if baiting or opponent.shields > 0:
        # When baiting or shields are up, prefer energy efficiency
        return sorted(moves, key=lambda m: (m.energy_cost, -poke.calculate_move_dpe(m, opponent)))
    else:
        # When not baiting and shields are down, prefer raw damage
        return sorted(moves, key=lambda m: -DamageCalculator.calculate_damage(poke, opponent, m))
```

#### 2C.2: Shield-Up Move Preference Logic
```python
def select_optimal_move_with_shields_up(self, poke: Pokemon, opponent: Pokemon, current_move: Move) -> Move:
    """
    Select optimal move when opponent has shields up.
    
    Priority:
    1. Low energy, high DPE moves
    2. Non-self-debuffing moves
    3. Moves that force shield usage
    """
    if len(poke.active_charged_moves) < 2:
        return current_move
    
    # Get the lowest energy move
    lowest_energy_move = min(poke.active_charged_moves, key=lambda m: m.energy_cost)
    
    # Check if lowest energy move is better than current selection
    if (lowest_energy_move.energy_cost <= current_move.energy_cost and
        poke.calculate_move_dpe(lowest_energy_move, opponent) > poke.calculate_move_dpe(current_move, opponent) and
        not getattr(lowest_energy_move, 'self_debuffing', False)):
        
        return lowest_energy_move
    
    return current_move
```

#### 2C.3: Self-Debuffing Move Avoidance
```python
def avoid_self_debuffing_during_baiting(self, poke: Pokemon, opponent: Pokemon, current_move: Move) -> Move:
    """
    Avoid using self-debuffing moves when baiting shields.
    
    Args:
        poke: Current Pokemon
        opponent: Opponent Pokemon
        current_move: Currently selected move
        
    Returns:
        Alternative move if current move should be avoided
    """
    if not poke.bait_shields or opponent.shields <= 0:
        return current_move
    
    if not getattr(current_move, 'self_debuffing', False):
        return current_move
    
    # Find alternative non-debuffing move
    for move in poke.active_charged_moves:
        if (move != current_move and 
            poke.energy >= move.energy_cost and
            not getattr(move, 'self_debuffing', False) and
            poke.calculate_move_dpe(move, opponent) > poke.calculate_move_dpe(current_move, opponent)):
            
            return move
    
    return current_move
```

### Step 2D: Advanced Baiting Conditions

#### 2D.1: Build-Up to Expensive Move Logic
```python
def should_build_up_to_expensive_move(self, poke: Pokemon, opponent: Pokemon) -> Tuple[bool, Optional[Move]]:
    """
    Determine if Pokemon should build energy for a more expensive, efficient move.
    
    Returns:
        Tuple of (should_build_up: bool, target_move: Optional[Move])
    """
    if not poke.bait_shields or opponent.shields <= 0 or len(poke.active_charged_moves) < 2:
        return False, None
    
    # Sort moves by energy cost
    moves = sorted(poke.active_charged_moves, key=lambda m: m.energy_cost)
    cheap_move = moves[0]
    expensive_move = moves[1]
    
    # Check if we don't have energy for expensive move yet
    if poke.energy >= expensive_move.energy_cost:
        return False, None
    
    # Check if expensive move has significantly better DPE
    cheap_dpe = poke.calculate_move_dpe(cheap_move, opponent)
    expensive_dpe = poke.calculate_move_dpe(expensive_move, opponent)
    
    if expensive_dpe / cheap_dpe <= 1.3:  # Not worth building up
        return False, None
    
    # Don't build up if we have an effective self-buffing move that's ready
    if (poke.energy >= cheap_move.energy_cost and 
        getattr(cheap_move, 'self_buffing', False) and
        expensive_dpe / cheap_dpe <= 1.5):
        return False, None
    
    return True, expensive_move
```

#### 2D.2: Self-Buffing Move Exception Handling
```python
def handle_self_buffing_move_exceptions(self, poke: Pokemon, opponent: Pokemon, current_move: Move) -> Move:
    """
    Handle special cases for self-buffing moves during baiting.
    
    Self-buffing moves may be worth using even if they're not the most efficient,
    due to their long-term damage increase.
    """
    if not getattr(current_move, 'self_buffing', False):
        return current_move
    
    # If we have a self-buffing move ready and baiting is enabled
    if poke.bait_shields and opponent.shields > 0:
        # Check if there's a significantly better alternative
        for move in poke.active_charged_moves:
            if (move != current_move and 
                poke.energy >= move.energy_cost and
                not getattr(move, 'self_debuffing', False)):
                
                current_dpe = poke.calculate_move_dpe(current_move, opponent)
                alt_dpe = poke.calculate_move_dpe(move, opponent)
                
                # Only switch if alternative is much better (accounting for buff value)
                if alt_dpe / current_dpe > 2.0:
                    return move
    
    return current_move
```

#### 2D.3: Low Health Baiting Prevention
```python
def should_prevent_baiting_low_health(self, poke: Pokemon, opponent: Pokemon) -> bool:
    """
    Determine if baiting should be prevented due to low health.
    
    When Pokemon has low health, it's better to use the most efficient move
    immediately rather than risk fainting while baiting.
    """
    health_ratio = poke.current_hp / poke.stats.hp
    
    # Prevent baiting if health is below 25% and energy is low
    if health_ratio < 0.25 and poke.energy < 70:
        return True
    
    # Prevent baiting if Pokemon might faint from opponent's next charged move
    for move in opponent.active_charged_moves:
        if opponent.energy >= move.energy_cost:
            damage = DamageCalculator.calculate_damage(opponent, poke, move)
            if damage >= poke.current_hp and poke.shields == 0:
                return True
    
    return False
```

#### 2D.4: Close Energy Move Handling
```python
def handle_close_energy_moves(self, poke: Pokemon, opponent: Pokemon, current_move: Move) -> Move:
    """
    Handle moves with similar energy costs (within 10 energy).
    
    When moves have similar energy costs, prefer the one with better DPE
    or special properties (buffing vs debuffing).
    """
    if len(poke.active_charged_moves) < 2:
        return current_move
    
    for alt_move in poke.active_charged_moves:
        if alt_move == current_move or poke.energy < alt_move.energy_cost:
            continue
        
        energy_diff = abs(alt_move.energy_cost - current_move.energy_cost)
        
        # Handle moves within 10 energy of each other
        if energy_diff <= 10:
            current_dpe = poke.calculate_move_dpe(current_move, opponent)
            alt_dpe = poke.calculate_move_dpe(alt_move, opponent)
            
            # Prefer non-debuffing moves when baiting
            if (poke.bait_shields and opponent.shields > 0 and
                getattr(current_move, 'self_debuffing', False) and
                not getattr(alt_move, 'self_debuffing', False) and
                alt_dpe / current_dpe > 0.7):
                return alt_move
            
            # Prefer buffing moves when not baiting or shields are down
            if (not poke.bait_shields or opponent.shields == 0):
                if (getattr(alt_move, 'self_buffing', False) and
                    not getattr(current_move, 'self_buffing', False)):
                    return alt_move
    
    return current_move
```

### Step 2E: Integration with DP Algorithm

#### 2E.1: DP State Baiting Evaluation
```python
def evaluate_baiting_in_dp_state(self, state: DPState, poke: Pokemon, opponent: Pokemon) -> None:
    """
    Evaluate shield baiting options within DP algorithm state.
    
    Args:
        state: Current DP state being evaluated
        poke: Current Pokemon
        opponent: Opponent Pokemon
    """
    if not poke.bait_shields or opponent.shields <= 0:
        return
    
    # Create temporary Pokemon with state values
    temp_poke = self.create_temp_pokemon_from_state(poke, state)
    temp_opponent = self.create_temp_opponent_from_state(opponent, state)
    
    # Evaluate baiting options
    should_bait, bait_move = self.should_bait_shields(temp_poke, temp_opponent)
    
    if should_bait and bait_move:
        # Calculate expected value of baiting vs not baiting
        bait_value = self.calculate_baiting_expected_value(temp_poke, temp_opponent, bait_move)
        
        # Update state score if baiting is beneficial
        if bait_value > state.score:
            state.score = bait_value
            state.best_move = bait_move
            state.strategy = "BAIT_SHIELDS"
```

#### 2E.2: Baiting Weight Calculation
```python
def calculate_baiting_weight(self, poke: Pokemon, opponent: Pokemon) -> int:
    """
    Calculate decision weight for shield baiting strategy.
    
    Returns:
        Weight value for baiting decision (higher = more likely)
    """
    if not poke.bait_shields or opponent.shields <= 0 or len(poke.active_charged_moves) < 2:
        return 0
    
    base_weight = 1
    
    # Increase weight based on DPE difference
    moves = sorted(poke.active_charged_moves, key=lambda m: m.energy_cost)
    low_dpe = poke.calculate_move_dpe(moves[0], opponent)
    high_dpe = poke.calculate_move_dpe(moves[1], opponent)
    
    if low_dpe > 0:
        dpe_ratio = high_dpe / low_dpe
        if dpe_ratio > 1.5:
            base_weight += int((dpe_ratio - 1.0) * 10)
    
    # Increase weight if behind on shields
    if poke.shields < opponent.shields:
        base_weight += 2
    
    # Decrease weight for very bad matchups
    damage_ratio = self.calculate_overall_damage_ratio(poke, opponent)
    if damage_ratio < 0.5:  # Taking much more damage than dealing
        base_weight = max(1, base_weight // 2)
    
    # Decrease weight for low health
    health_ratio = poke.current_hp / poke.stats.hp
    if health_ratio < 0.25:
        base_weight = max(1, base_weight // 3)
    
    return base_weight

def calculate_baiting_expected_value(self, poke: Pokemon, opponent: Pokemon, bait_move: Move) -> float:
    """
    Calculate expected value of using baiting strategy.
    
    Considers:
    - Probability opponent shields bait move
    - Damage from follow-up move after shield is wasted
    - Risk of not getting to use follow-up move
    """
    # Simulate baiting scenario
    shield_prob = self.estimate_shield_probability(poke, opponent, bait_move)
    
    if shield_prob < 0.5:
        return 0.0  # Not worth baiting if opponent likely won't shield
    
    # Calculate value of wasted opponent shield
    follow_up_moves = [m for m in poke.active_charged_moves if m != bait_move and poke.energy >= m.energy_cost]
    
    if not follow_up_moves:
        return 0.0
    
    best_follow_up = max(follow_up_moves, key=lambda m: poke.calculate_move_dpe(m, opponent))
    follow_up_damage = DamageCalculator.calculate_damage(poke, opponent, best_follow_up)
    
    # Expected value = probability of successful bait * follow-up damage
    return shield_prob * follow_up_damage * 0.1  # Scale factor for decision weight
```

### Integration Points

#### Pokemon Class Extensions Needed:
```python
class Pokemon:
    def __init__(self):
        # ... existing initialization
        self.bait_shields = False  # Enable/disable baiting behavior
        self.active_charged_moves = []  # Sorted list of available charged moves
    
    # Add all DPE calculation methods
    def calculate_move_dpe(self, move, opponent): ...
    def calculate_buff_dpe_multiplier(self, move): ...
```

#### Move Class Extensions Needed:
```python
class Move:
    def __init__(self):
        # ... existing initialization
        self.dpe = 0.0  # Damage per energy (calculated)
        self.self_buffing = False  # Move buffs self
        self.self_debuffing = False  # Move debuffs self
        self.self_attack_debuffing = False  # Move debuffs own attack
        self.buff_target = "none"  # "self", "opponent", "both"
        self.buffs = []  # Stat change values
        self.buff_apply_chance = 1.0  # Probability of applying buffs
```

#### ActionLogic Class Extensions:
```python
class ActionLogic:
    def __init__(self, battle):
        self.battle = battle
        self.baiting_cache = {}  # Cache baiting calculations
    
    # Add all baiting methods
    def should_bait_shields(self, poke, opponent): ...
    def analyze_dpe_ratios(self, poke, opponent, current_move): ...
    def reorder_moves_by_damage(self, poke, opponent, moves, baiting): ...
    # ... etc
```

### Testing Strategy

#### Unit Tests:
1. **DPE Calculation**: Test damage per energy calculations with various moves and buffs
2. **Basic Baiting Logic**: Test shield baiting decision making
3. **DPE Ratio Analysis**: Test 1.5x threshold and move selection
4. **Move Reordering**: Test damage-based vs efficiency-based sorting
5. **Advanced Conditions**: Test build-up logic, health checks, energy validation
6. **Self-Debuffing Avoidance**: Test avoidance of debuffing moves during baiting

#### Integration Tests:
1. **DP Algorithm Integration**: Test baiting within DP state evaluation
2. **Decision Weight Calculation**: Test baiting weight in decision options
3. **Real Battle Scenarios**: Test baiting in actual battle simulations
4. **JavaScript Parity**: Compare baiting decisions with JavaScript implementation

#### Test Cases:
```python
def test_basic_shield_baiting():
    """Test basic shield baiting with DPE difference."""
    # Setup: Pokemon with 35 energy move (DPE 2.0) and 50 energy move (DPE 3.5)
    # Expected: Should bait with 35 energy move when opponent has shields
    
def test_dpe_ratio_threshold():
    """Test 1.5x DPE ratio threshold for baiting."""
    # Setup: Moves with DPE ratio of 1.4 (below threshold)
    # Expected: Should not bait due to insufficient DPE advantage
    
def test_self_debuffing_avoidance():
    """Test avoidance of self-debuffing moves during baiting."""
    # Setup: Self-debuffing move vs normal move, opponent has shields
    # Expected: Should prefer non-debuffing move for baiting
```

### Performance Considerations
- Cache DPE calculations for repeated move evaluations
- Limit baiting analysis depth to prevent performance impact
- Use early returns when baiting conditions aren't met
- Consider disabling complex baiting logic in fast simulation modes

## Implementation Priority

### Phase 1: Core Decision Logic (High Priority)
1. **Complete `decide_action` method**: Implement the full DP algorithm from lines 400-763 in ActionLogic.js
2. **Add `DecisionOption` class**: Simple dataclass for weighted decision making
3. **Implement move timing optimization**: Logic to reduce free turns and optimize move usage

### Phase 2: Pokemon & Move Properties (Medium Priority)
1. **Extend Pokemon class**: Add missing properties like `farmEnergy`, `baitShields`, `optimizeMoveTiming`
2. **Extend Move classes**: Add buff/debuff properties and DPE calculations
3. **Add property calculation methods**: `fastestChargedMove`, `bestChargedMove`, etc.

### Phase 3: Advanced Features (Lower Priority)
1. **Complete shield decision logic**: Full buff handling and cycle damage calculations
2. **Timeline system**: Event management and action queuing
3. **TrainingAI port**: Advanced AI with difficulty levels and human-like behavior

### Phase 4: Integration & Testing
1. **Battle context methods**: `getMode()`, `getQueuedActions()`, `logDecision()`
2. **Comprehensive testing**: Validate AI decisions match JavaScript behavior
3. **Performance optimization**: Ensure DP algorithm runs efficiently

## Estimated Effort

- **Phase 1**: 1-2 weeks (most critical for basic AI functionality)
- **Phase 2**: 1 week (required for advanced decision making)
- **Phase 3**: 1-2 weeks (nice-to-have features)
- **Phase 4**: 1 week (testing and polish)

**Total: 4-6 weeks** for full parity with JavaScript ActionLogic.js

## Current Status

✅ **Completed (~65%)**:
- Basic ActionLogic class structure
- Complete DP queue algorithm implementation (Steps 1A-1C)
- Complete Move Timing Optimization system (Steps 1D-1F)
- Complete Basic Lethal Move Detection system (Step 1G)
- Complete Advanced Lethal Move Detection system (Step 1H)
- Complete Lethal Detection DP Integration system (Step 1I)
- Complete Shield Baiting Logic with DPE Ratio Analysis (Steps 1J-1K)
- Complete Move Reordering Logic system (Step 1L)
- Full `decide_action` implementation with DP algorithm, timing optimization, lethal detection, and move reordering
- `decide_random_action` method (complete with lethal weight boosting)
- `would_shield` method (basic implementation)
- `choose_option` method (complete)
- Battle context methods (`get_queued_actions`, `log_decision`, `get_mode`)
- Comprehensive test coverage for all implemented components

❌ **Missing (~35%)**:
- Advanced baiting conditions (Step 1M)
- Self-debuffing move handling
- Energy stacking logic
- Pokemon/Move property extensions
- Timeline system
- TrainingAI integration

## Files to Modify

1. **`python/pvpoke/battle/ai.py`**: Complete ActionLogic implementation
2. **`python/pvpoke/core/pokemon.py`**: Add missing Pokemon properties
3. **`python/pvpoke/core/moves.py`**: Add missing Move properties
4. **`python/pvpoke/battle/battle.py`**: Add battle context methods
5. **`python/pvpoke/battle/timeline.py`**: New file for timeline management
6. **`python/pvpoke/battle/training_ai.py`**: New file for TrainingAI port

## Notes

- The JavaScript ActionLogic is highly optimized for PvP battle scenarios
- The DP algorithm is the most complex part and critical for competitive AI
- Some JavaScript-specific optimizations may need Python adaptations
- Consider breaking large methods into smaller, testable functions
- Maintain compatibility with existing battle simulation code
