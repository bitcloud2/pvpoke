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
    - Step 1C: Add Move Evaluation Loop
        - Implement the charged move readiness calculation
        - Add the basic state pushing logic
- **Move Timing Optimization**: Logic to reduce free turns (lines 237-345 in JS)  
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
