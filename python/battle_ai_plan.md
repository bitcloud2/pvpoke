# Battle AI Port - Missing Components from ActionLogic.js

## Overview
The Python implementation of PvPoke's battle AI is currently **~30% complete**. The JavaScript ActionLogic.js contains ~900 lines of sophisticated decision-making logic, and we've now implemented the core DP queue loop structure with comprehensive testing.

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
    - ⏳ Step 2A: Implement Target Cooldown Calculation
        - Add `optimize_move_timing` flag to Pokemon class
        - Implement cooldown-based targeting logic (500ms default, 1000ms for slow moves)
        - Add special case handling for different move duration combinations
        - Add logic to disable optimization for same/evenly divisible move durations
    - ⏳ Step 2B: Add Timing Optimization Checks
        - Implement faint prevention check (don't optimize if about to faint from fast move)
        - Add energy overflow prevention (don't go over 100 energy with queued fast moves)
        - Add turns-to-live vs planned-turns comparison
        - Add lethal charged move detection (don't optimize if can KO opponent)
        - Add opponent lethal move prevention (don't optimize if opponent can KO)
        - Add fast move KO prevention within timing window
    - ⏳ Step 2C: Integrate Battle Context Methods
        - Implement `get_queued_actions()` method in Battle class
        - Add `log_decision()` method for debugging output
        - Add queued fast move counting logic
        - Add timing optimization return logic (early exit when optimizing)  
- **Lethal Move Detection**: Throwing moves that will KO the opponent (lines 210-234 in JS)
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

✅ **Completed (~25%)**:
- Basic ActionLogic class structure
- Partial `decide_action` implementation (early exit conditions)
- `decide_random_action` method (mostly complete)
- `would_shield` method (basic implementation)
- `choose_option` method (complete)

❌ **Missing (~75%)**:
- Core DP algorithm for optimal move sequencing
- Move timing optimization
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
