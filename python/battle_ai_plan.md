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
    - Step 1H: Add Advanced Lethal Detection Logic
        - Implement multi-move lethal combinations (charged + fast moves)
        - Add buff/debuff consideration in damage calculations
        - Handle special cases (opponent at 1 HP after shield)
        - Add priority ordering for multiple lethal moves
    - Step 1I: Integrate Lethal Detection with DP Algorithm
        - Add lethal move detection to DP state evaluation
        - Implement immediate victory state handling
        - Add lethal move weight boosting in decision options
        - Add comprehensive testing for lethal detection scenarios
- **Shield Baiting Logic**: Complex baiting strategies when shields are up (lines 820-847 in JS)
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

✅ **Completed (~45%)**:
- Basic ActionLogic class structure
- Complete DP queue algorithm implementation (Steps 1A-1C)
- Complete Move Timing Optimization system (Steps 1D-1F)
- Complete Basic Lethal Move Detection system (Step 1G)
- Full `decide_action` implementation with DP algorithm, timing optimization, and lethal detection
- `decide_random_action` method (complete)
- `would_shield` method (basic implementation)
- `choose_option` method (complete)
- Battle context methods (`get_queued_actions`, `log_decision`, `get_mode`)
- Comprehensive test coverage for all implemented components

❌ **Missing (~60%)**:
- Shield baiting logic
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
