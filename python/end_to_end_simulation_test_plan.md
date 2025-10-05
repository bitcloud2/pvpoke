# End-to-End Battle Simulation Test Plan

## Overview

This document tracks the implementation of comprehensive end-to-end battle simulation tests and cross-validation with JavaScript to ensure the Python implementation matches the JavaScript version exactly.

## Current Status

### ✅ **COMPLETED (~70% of Battle AI)**

1. **DP Queue Algorithm (Steps 1A-1C)** ✅
   - Basic DP queue structure
   - State management with buff capping
   - Move evaluation loop with charged move readiness

2. **Move Timing Optimization (Steps 1D-1F)** ✅
   - Target cooldown calculation
   - Timing optimization checks
   - Battle context integration

3. **Lethal Move Detection (Steps 1G-1I)** ✅
   - Basic and advanced lethal detection
   - Multi-move lethal combinations
   - DP algorithm integration

4. **Shield Baiting Logic (Steps 1J-1L)** ✅
   - Basic shield baiting with DPE calculations
   - DPE ratio analysis (1.5x threshold)
   - Move reordering logic

5. **High Priority Baiting Fixes (Step 1K+)** ✅
   - Self-buffing move exceptions
   - wouldShield method validation
   - Low health edge cases

6. **Integrated Baiting (Step 1N)** ✅
   - Baiting logic integrated into DP algorithm
   - Comprehensive testing

7. **End-to-End Battle Simulations (Phase 1, Steps 1-2)** ✅
   - Full battle simulations with baiting enabled/disabled (8 tests)
   - Multi-turn baiting sequences (8 tests)
   - Turn-by-turn validation and timeline analysis

### ❌ **REMAINING WORK**

#### **End-to-End Scenarios:**
- ✅ Full battle simulations with baiting enabled vs disabled (COMPLETED)
- ✅ Multi-turn baiting sequences (bait → shield → follow-up) (COMPLETED)
- ❌ Complex scenarios with multiple Pokemon and shield counts (Step 3)
- ❌ Performance testing to ensure DP integration doesn't slow down battles (Step 4)

#### **Cross-Validation:**
- ❌ Side-by-side JavaScript comparison on identical battle scenarios (Steps 5-7)

---

## Phase 1: End-to-End Battle Simulation Tests

### **Step 1: Full Battle Simulations with Baiting Enabled vs Disabled**

**Status:** ✅ **COMPLETED**

**Goal:** Create tests that run complete battles and compare outcomes with baiting on/off

**Implementation Tasks:**
1. ✅ Create `tests/test_e2e_baiting_comparison.py`
2. ✅ Set up identical battle scenarios
3. ✅ Run with `bait_shields=True` and `bait_shields=False`
4. ✅ Compare:
   - Winner
   - Final HP values
   - Total damage dealt
   - Shield usage patterns
   - Turn counts

**Test Cases Implemented:**
1. ✅ `test_azumarill_vs_altaria` - Swampert vs Azumarill (Hydro Cannon 40E vs Earthquake 65E)
2. ✅ `test_medicham_vs_azumarill` - Medicham vs Azumarill (Ice Punch 40E vs Psychic 55E)
3. ✅ `test_registeel_vs_altaria` - Registeel vs Azumarill (Focus Blast 50E vs Flash Cannon 55E)
4. ✅ `test_skarmory_vs_azumarill` - Skarmory vs Azumarill (Sky Attack 50E vs Brave Bird 55E)
5. ✅ `test_galarian_stunfisk_vs_azumarill` - G-Fisk vs Azumarill (Rock Slide 45E vs Earthquake 65E)
6. ✅ `test_shield_configuration_2v1` - Shield advantage scenario (2v1)
7. ✅ `test_shield_configuration_1v2` - Shield disadvantage scenario (1v2)
8. ✅ `test_no_shields_no_baiting` - No shields scenario (0v0)

**Acceptance Criteria:**
- [x] At least 5 different matchups tested (8 total tests created)
- [x] Baiting system runs without errors
- [x] Shield usage patterns documented via comparison output
- [x] Damage output compared (HP differences tracked)
- [x] All tests pass consistently (8/8 passing)

**Files Created:**
- ✅ `python/tests/test_e2e_baiting_comparison.py` (441 lines, 8 test cases)

**Key Findings:**
- Baiting logic is integrated and functional
- Battle outcomes vary based on baiting settings
- System correctly handles different shield configurations
- Even without shields, baiting logic may affect move selection based on DPE calculations
- All 8 tests pass reliably

---

### **Step 2: Multi-Turn Baiting Sequences**

**Status:** ✅ **COMPLETED**

**Goal:** Test complex baiting scenarios across multiple turns

**Test Cases Implemented:**
1. ✅ `test_successful_bait_sequence` - Altaria vs Azumarill (Dragon Pulse 35E, Sky Attack 45E)
2. ✅ `test_failed_bait_sequence` - Medicham vs Registeel (low HP scenario)
3. ✅ `test_energy_building_for_expensive_move` - Swampert vs Azumarill (Hydro Cannon 40E, Earthquake 65E)
4. ✅ `test_multi_shield_bait_sequence` - G-Fisk vs Azumarill (Rock Slide 45E, Earthquake 65E)
5. ✅ `test_bait_with_self_buffing_move` - Medicham vs Azumarill (Power-Up Punch exception)
6. ✅ `test_bait_with_self_debuffing_move` - Registeel vs Azumarill (self-debuff avoidance)
7. ✅ `test_shield_advantage_baiting_behavior` - Shield advantage scenario (2v1)
8. ✅ `test_shield_disadvantage_baiting_behavior` - Shield disadvantage scenario (1v2)

**Acceptance Criteria:**
- [x] All 8 baiting sequence types tested (exceeded 4 minimum)
- [x] Turn-by-turn validation implemented via BattleSequenceAnalyzer
- [x] Energy tracking verified (approximated via timeline)
- [x] Shield usage patterns validated
- [x] Decision logging shows correct strategy via detailed timeline analysis

**Files Created:**
- ✅ `python/tests/test_e2e_baiting_sequences.py` (580 lines, 8 test cases)

**Key Features:**
- `BattleSequenceAnalyzer` class for comprehensive timeline analysis
- Detailed tracking of charged move sequences
- Shield usage pattern analysis
- Turn-by-turn event logging
- Support for self-buffing/debuffing move exceptions
- Shield advantage/disadvantage scenarios

**Key Findings:**
- All 8 tests pass consistently
- Timeline logging provides detailed battle sequence information
- Baiting logic correctly handles various scenarios
- Shield usage patterns are properly tracked
- Move sequences are documented and validated

---

### **Step 3: Complex Multi-Pokemon Scenarios**

**Status:** ❌ Not Started

**Goal:** Test battles with different shield configurations

**Test Cases:**

#### 3.1: Shield Configuration Tests
```python
def test_2v2_shields_maximum_baiting_priority():
    """Test 2v2 shields (maximum baiting priority)."""
    # Both Pokemon have 2 shields
    # Baiting should be most aggressive
    # Assert: Bait moves preferred over nuke moves

def test_2v1_shields_shield_advantage():
    """Test 2v1 shields (shield advantage)."""
    # Player has 2 shields, opponent has 1
    # Less aggressive baiting needed
    # Assert: May use nuke moves earlier

def test_1v2_shields_shield_disadvantage():
    """Test 1v2 shields (shield disadvantage)."""
    # Player has 1 shield, opponent has 2
    # Must bait opponent shields efficiently
    # Assert: Aggressive baiting to even shield count

def test_0v0_shields_no_baiting():
    """Test 0v0 shields (no baiting needed)."""
    # No shields available
    # Baiting logic should be disabled
    # Assert: Always use highest damage moves

def test_1v0_shields_no_baiting_needed():
    """Test 1v0 shields (shield advantage, no baiting)."""
    # Player has shield, opponent doesn't
    # No need to bait
    # Assert: Use optimal damage moves
```

#### 3.2: Complex Matchup Tests
```python
def test_complex_matchup_with_buffs_and_baiting():
    """Test matchup with self-buffing moves and baiting."""
    # Medicham (Power-Up Punch, Ice Punch) vs Azumarill
    # Test interaction of buffs and baiting
    # Assert: Buff moves used appropriately

def test_complex_matchup_with_debuffs_and_baiting():
    """Test matchup with self-debuffing moves and baiting."""
    # Registeel (Superpower, Focus Blast) vs Altaria
    # Test avoidance of debuff moves during baiting
    # Assert: Superpower avoided when baiting

def test_complex_matchup_with_timing_optimization():
    """Test matchup with move timing optimization."""
    # Pokemon with different fast move durations
    # Test timing optimization + baiting interaction
    # Assert: Timing optimization doesn't interfere with baiting
```

**Acceptance Criteria:**
- [ ] All 8 test cases implemented
- [ ] Shield configurations validated
- [ ] Baiting priority adjusts based on shield count
- [ ] Complex interactions (buffs/debuffs/timing) tested
- [ ] All tests pass consistently

**Files to Create:**
- `python/tests/test_e2e_shield_scenarios.py`
- `python/tests/test_e2e_complex_matchups.py`

---

### **Step 4: Performance Testing**

**Status:** ❌ Not Started

**Goal:** Ensure DP algorithm doesn't slow down battles significantly

**Metrics to Measure:**

#### 4.1: Baseline Performance (No DP/Baiting)
```python
def test_baseline_performance_simple_battle():
    """Measure baseline performance without DP algorithm."""
    import time
    
    # Simple battle: Azumarill vs Registeel
    # No baiting, no timing optimization
    # Run 100 battles
    
    start = time.time()
    for _ in range(100):
        battle = create_simple_battle()
        battle.simulate()
    baseline_time = time.time() - start
    
    print(f"Baseline: {baseline_time:.2f}s for 100 battles")
    print(f"Average: {baseline_time/100*1000:.2f}ms per battle")
    
    # Store baseline for comparison
    return baseline_time
```

#### 4.2: DP Algorithm Performance
```python
def test_dp_algorithm_performance_overhead():
    """Measure performance impact of DP algorithm."""
    import time
    
    baseline = test_baseline_performance_simple_battle()
    
    # Same matchup with DP enabled
    start = time.time()
    for _ in range(100):
        battle = create_battle_with_dp()
        battle.simulate()
    dp_time = time.time() - start
    
    overhead = (dp_time - baseline) / baseline * 100
    
    print(f"With DP: {dp_time:.2f}s for 100 battles")
    print(f"Average: {dp_time/100*1000:.2f}ms per battle")
    print(f"Overhead: {overhead:.1f}%")
    
    # Assert less than 100% slowdown (less than 2x slower)
    assert overhead < 100, f"DP overhead too high: {overhead:.1f}%"
```

#### 4.3: Stress Test
```python
def test_performance_stress_test_complex_matchup():
    """Stress test with complex matchup."""
    import time
    
    # Complex matchup: Many charged moves, buffs, shields
    # Medicham vs Azumarill (both have 2 charged moves, 2 shields)
    
    start = time.time()
    for _ in range(100):
        battle = create_complex_battle_with_full_ai()
        battle.simulate()
    complex_time = time.time() - start
    
    print(f"Complex with full AI: {complex_time:.2f}s for 100 battles")
    print(f"Average: {complex_time/100*1000:.2f}ms per battle")
    
    # Assert reasonable performance (< 500ms per battle)
    avg_time_ms = complex_time / 100 * 1000
    assert avg_time_ms < 500, f"Battle too slow: {avg_time_ms:.1f}ms"
```

#### 4.4: Profiling
```python
def test_profile_dp_algorithm_bottlenecks():
    """Profile DP algorithm to identify bottlenecks."""
    import cProfile
    import pstats
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run 10 battles with full AI
    for _ in range(10):
        battle = create_battle_with_full_ai()
        battle.simulate()
    
    profiler.disable()
    
    # Print top 20 time-consuming functions
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    # Identify if any single function takes > 30% of time
    # (would indicate a bottleneck)
```

**Performance Targets:**
- [ ] Baseline: < 50ms per simple battle
- [ ] With DP: < 100ms per battle (< 100% overhead)
- [ ] Complex: < 500ms per battle
- [ ] No single function > 30% of total time

**Acceptance Criteria:**
- [ ] All performance tests pass
- [ ] Overhead is acceptable (< 100%)
- [ ] No major bottlenecks identified
- [ ] Performance metrics documented

**Files to Create:**
- `python/tests/test_e2e_performance.py`
- `python/performance_results.md` (documentation)

---

## Phase 2: Cross-Validation with JavaScript

### **Step 5: Set Up JavaScript Battle Execution**

**Status:** ❌ Not Started

**Goal:** Run actual JavaScript battles, not mocked results

**Approach: Node.js Execution (Recommended)**

#### 5.1: Extract JavaScript Battle Code
```javascript
// js_battle_runner.js
const fs = require('fs');

// Load GameMaster and Battle classes
// (Extract from src/js/GameMaster.js, src/js/battle/*.js)

function runBattle(config) {
    // Parse config JSON
    const pokemon1Config = config.pokemon1;
    const pokemon2Config = config.pokemon2;
    
    // Create Pokemon instances
    const pokemon1 = createPokemon(pokemon1Config);
    const pokemon2 = createPokemon(pokemon2Config);
    
    // Create and run battle
    const battle = new Battle();
    battle.setNewPokemon(pokemon1, 0);
    battle.setNewPokemon(pokemon2, 1);
    battle.simulate();
    
    // Return results as JSON
    return {
        winner: battle.getWinner(),
        pokemon1_hp: pokemon1.hp,
        pokemon2_hp: pokemon2.hp,
        turns: battle.getTurns(),
        timeline: battle.getTimeline(),
        decisions: battle.getDecisionLog()
    };
}

// Read config from stdin
const config = JSON.parse(fs.readFileSync(0, 'utf-8'));
const result = runBattle(config);
console.log(JSON.stringify(result));
```

#### 5.2: Python Wrapper
```python
# python/pvpoke/utils/js_battle_runner.py
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

class JavaScriptBattleRunner:
    """Run JavaScript battles from Python for validation."""
    
    def __init__(self):
        self.js_runner_path = Path(__file__).parent.parent.parent.parent / "js_battle_runner.js"
        
    def run_battle(self, pokemon1_config: Dict, pokemon2_config: Dict) -> Dict[str, Any]:
        """Run a battle using JavaScript implementation."""
        
        config = {
            "pokemon1": pokemon1_config,
            "pokemon2": pokemon2_config
        }
        
        # Run Node.js script
        result = subprocess.run(
            ["node", str(self.js_runner_path)],
            input=json.dumps(config),
            capture_output=True,
            text=True,
            check=True
        )
        
        return json.loads(result.stdout)
```

**Implementation Tasks:**
- [ ] Extract necessary JavaScript files
- [ ] Create standalone Node.js runner
- [ ] Test JavaScript runner independently
- [ ] Create Python wrapper
- [ ] Validate wrapper works correctly

**Files to Create:**
- `js_battle_runner.js` (root directory)
- `python/pvpoke/utils/js_battle_runner.py`

---

### **Step 6: Create JavaScript Comparison Test Suite**

**Status:** ❌ Not Started

**Goal:** Compare Python vs JavaScript on identical scenarios

#### 6.1: Basic Matchup Tests
```python
def test_js_comparison_azumarill_vs_registeel():
    """Compare Python vs JavaScript: Azumarill vs Registeel."""
    
    config = {
        "pokemon1": {
            "species": "azumarill",
            "cp": 1500,
            "fast_move": "BUBBLE",
            "charged_moves": ["ICE_BEAM", "HYDRO_PUMP"]
        },
        "pokemon2": {
            "species": "registeel",
            "cp": 1500,
            "fast_move": "LOCK_ON",
            "charged_moves": ["FOCUS_BLAST", "FLASH_CANNON"]
        }
    }
    
    # Run Python battle
    py_result = run_python_battle(config)
    
    # Run JavaScript battle
    js_result = run_javascript_battle(config)
    
    # Compare results
    assert py_result["winner"] == js_result["winner"]
    assert abs(py_result["pokemon1_hp"] - js_result["pokemon1_hp"]) <= 1
    assert abs(py_result["pokemon2_hp"] - js_result["pokemon2_hp"]) <= 1
    assert abs(py_result["turns"] - js_result["turns"]) <= 2
```

#### 6.2: Baiting Scenario Tests
```python
def test_js_comparison_baiting_altaria_vs_azumarill():
    """Compare baiting behavior: Altaria vs Azumarill."""
    
    config = {
        "pokemon1": {
            "species": "altaria",
            "cp": 1500,
            "fast_move": "DRAGON_BREATH",
            "charged_moves": ["DRAGON_PULSE", "SKY_ATTACK"],
            "bait_shields": True,
            "shields": 2
        },
        "pokemon2": {
            "species": "azumarill",
            "cp": 1500,
            "fast_move": "BUBBLE",
            "charged_moves": ["ICE_BEAM", "HYDRO_PUMP"],
            "shields": 2
        }
    }
    
    # Run both implementations
    py_result = run_python_battle(config)
    js_result = run_javascript_battle(config)
    
    # Compare shield usage
    assert py_result["shields_used"] == js_result["shields_used"]
    
    # Compare move selection (first 10 turns)
    for turn in range(min(10, len(py_result["timeline"]))):
        py_move = py_result["timeline"][turn]["move"]
        js_move = js_result["timeline"][turn]["move"]
        assert py_move == js_move, f"Turn {turn}: {py_move} != {js_move}"
```

#### 6.3: Complex Scenario Tests
```python
def test_js_comparison_self_buffing_medicham():
    """Compare self-buffing move behavior: Medicham."""
    # Test Power-Up Punch and Ice Punch
    
def test_js_comparison_self_debuffing_registeel():
    """Compare self-debuffing move behavior: Registeel."""
    # Test Superpower avoidance during baiting
    
def test_js_comparison_timing_optimization():
    """Compare timing optimization behavior."""
    # Test with different fast move durations
```

#### 6.4: Edge Case Tests
```python
def test_js_comparison_lethal_move_detection():
    """Compare lethal move detection."""
    # Setup: Opponent at low HP
    # Assert: Both choose lethal move
    
def test_js_comparison_energy_capping():
    """Compare energy capping at 100."""
    # Setup: High energy gain scenario
    # Assert: Both cap at 100 energy
    
def test_js_comparison_cmp_ties():
    """Compare CMP tie handling."""
    # Setup: Pokemon with same attack stat
    # Assert: Same CMP resolution
```

**Test Matrix:**

| Category | Test Count | Status |
|----------|------------|--------|
| Basic Matchups | 5 | ❌ |
| Baiting Scenarios | 5 | ❌ |
| Complex Scenarios | 5 | ❌ |
| Edge Cases | 5 | ❌ |
| **Total** | **20** | **0/20** |

**Acceptance Criteria:**
- [ ] All 20 comparison tests pass
- [ ] Winners match in 100% of cases
- [ ] HP values within ±1 in 95% of cases
- [ ] Turn counts within ±2 in 95% of cases
- [ ] Move selections match in 90% of cases

**Files to Create:**
- `python/tests/test_js_comparison_basic.py`
- `python/tests/test_js_comparison_baiting.py`
- `python/tests/test_js_comparison_complex.py`
- `python/tests/test_js_comparison_edge_cases.py`

---

### **Step 7: Validate Decision-Making Logic**

**Status:** ❌ Not Started

**Goal:** Ensure AI makes same decisions as JavaScript turn-by-turn

#### 7.1: Decision Logging Infrastructure
```python
# python/pvpoke/battle/decision_logger.py
class DecisionLogger:
    """Log AI decisions for comparison with JavaScript."""
    
    def __init__(self):
        self.decisions = []
    
    def log_decision(self, turn: int, pokemon_index: int, decision: Dict):
        """Log a single decision."""
        self.decisions.append({
            "turn": turn,
            "pokemon": pokemon_index,
            "action": decision["action"],
            "move": decision["move"],
            "reason": decision["reason"],
            "energy": decision["energy"],
            "hp": decision["hp"]
        })
    
    def export_json(self) -> str:
        """Export decisions as JSON for comparison."""
        return json.dumps(self.decisions, indent=2)
```

#### 7.2: Turn-by-Turn Comparison
```python
def test_turn_by_turn_decision_parity():
    """Compare Python and JavaScript decisions turn-by-turn."""
    
    config = create_test_config()
    
    # Run Python battle with logging
    py_battle = run_python_battle_with_logging(config)
    py_decisions = py_battle.get_decision_log()
    
    # Run JavaScript battle with logging
    js_battle = run_javascript_battle_with_logging(config)
    js_decisions = js_battle.get_decision_log()
    
    # Compare turn-by-turn
    for turn in range(min(len(py_decisions), len(js_decisions))):
        py_dec = py_decisions[turn]
        js_dec = js_decisions[turn]
        
        assert py_dec["action"] == js_dec["action"], \
            f"Turn {turn}: Action {py_dec['action']} != {js_dec['action']}"
        
        assert py_dec["move"] == js_dec["move"], \
            f"Turn {turn}: Move {py_dec['move']} != {js_dec['move']}"
```

#### 7.3: Divergence Analysis
```python
def test_identify_decision_divergence_points():
    """Identify where Python and JavaScript decisions diverge."""
    
    config = create_test_config()
    
    py_decisions = run_python_battle_with_logging(config)
    js_decisions = run_javascript_battle_with_logging(config)
    
    divergence_points = []
    
    for turn in range(min(len(py_decisions), len(js_decisions))):
        py_dec = py_decisions[turn]
        js_dec = js_decisions[turn]
        
        if py_dec["move"] != js_dec["move"]:
            divergence_points.append({
                "turn": turn,
                "python": py_dec,
                "javascript": js_dec,
                "reason": analyze_divergence(py_dec, js_dec)
            })
    
    # Report divergence points
    if divergence_points:
        print(f"Found {len(divergence_points)} divergence points:")
        for dp in divergence_points:
            print(f"  Turn {dp['turn']}: {dp['reason']}")
    
    # Assert acceptable divergence rate (< 5%)
    divergence_rate = len(divergence_points) / len(py_decisions) * 100
    assert divergence_rate < 5, f"Divergence rate too high: {divergence_rate:.1f}%"
```

**Acceptance Criteria:**
- [ ] Decision logging implemented in both Python and JavaScript
- [ ] Turn-by-turn comparison working
- [ ] Divergence analysis identifies differences
- [ ] Divergence rate < 5% for all test scenarios
- [ ] All divergences documented and explained

**Files to Create:**
- `python/pvpoke/battle/decision_logger.py`
- `python/tests/test_decision_parity.py`
- `python/decision_divergence_report.md`

---

## Implementation Timeline

### **Week 1: End-to-End Tests**
- **Day 1-2:** Step 1 - Baiting enabled/disabled comparison (5 tests)
- **Day 3-4:** Step 2 - Multi-turn sequences (4 tests)
- **Day 5:** Step 3 - Multi-Pokemon scenarios (8 tests)

**Deliverables:**
- 17 new end-to-end tests
- Test coverage report
- Initial performance baseline

### **Week 2: Performance & JavaScript Setup**
- **Day 1-2:** Step 4 - Performance testing (4 tests)
- **Day 3-5:** Step 5 - JavaScript execution setup

**Deliverables:**
- Performance test suite
- JavaScript battle runner
- Python wrapper for JS execution

### **Week 3: Cross-Validation**
- **Day 1-3:** Step 6 - JavaScript comparison tests (20 tests)
- **Day 4-5:** Step 7 - Decision-making validation

**Deliverables:**
- 20 JavaScript comparison tests
- Decision logging infrastructure
- Divergence analysis report

---

## Success Criteria

### **End-to-End Tests**
- [ ] All 17 end-to-end tests pass consistently
- [ ] Baiting behavior validated in multiple scenarios
- [ ] Shield usage patterns documented
- [ ] Performance overhead < 100%

### **Cross-Validation**
- [ ] All 20 JavaScript comparison tests pass
- [ ] Winners match in 100% of cases
- [ ] HP values within ±1 in 95% of cases
- [ ] Turn counts within ±2 in 95% of cases
- [ ] Move selections match in 90% of cases
- [ ] Decision divergence rate < 5%

### **Documentation**
- [ ] All test files created and documented
- [ ] Performance results documented
- [ ] Divergence analysis report completed
- [ ] Known differences documented

---

## Files to Create

### Test Files
1. `python/tests/test_e2e_baiting_comparison.py` (Step 1)
2. `python/tests/test_e2e_baiting_sequences.py` (Step 2)
3. `python/tests/test_e2e_shield_scenarios.py` (Step 3)
4. `python/tests/test_e2e_complex_matchups.py` (Step 3)
5. `python/tests/test_e2e_performance.py` (Step 4)
6. `python/tests/test_js_comparison_basic.py` (Step 6)
7. `python/tests/test_js_comparison_baiting.py` (Step 6)
8. `python/tests/test_js_comparison_complex.py` (Step 6)
9. `python/tests/test_js_comparison_edge_cases.py` (Step 6)
10. `python/tests/test_decision_parity.py` (Step 7)

### Infrastructure Files
11. `js_battle_runner.js` (Step 5)
12. `python/pvpoke/utils/js_battle_runner.py` (Step 5)
13. `python/pvpoke/battle/decision_logger.py` (Step 7)

### Documentation Files
14. `python/performance_results.md` (Step 4)
15. `python/decision_divergence_report.md` (Step 7)

---

## Progress Tracking

### Phase 1: End-to-End Tests
- [x] Step 1: Baiting Enabled/Disabled (8/8 tests) ✅ **COMPLETED**
- [x] Step 2: Multi-Turn Sequences (8/8 tests) ✅ **COMPLETED**
- [ ] Step 3: Multi-Pokemon Scenarios (0/8 tests)
- [ ] Step 4: Performance Testing (0/4 tests)

**Phase 1 Progress: 16/28 tests (57%)**

### Phase 2: Cross-Validation
- [ ] Step 5: JavaScript Setup (0/5 tasks)
- [ ] Step 6: JavaScript Comparison (0/20 tests)
- [ ] Step 7: Decision Validation (0/3 tasks)

**Phase 2 Progress: 0/28 tasks (0%)**

### Overall Progress
**Total: 16/56 tasks (29%)**

---

## Notes

- All tests should be run with `pixi run python -m pytest` as per workspace rules
- Performance tests should be run separately from regular tests (may be slow)
- JavaScript comparison requires Node.js to be installed
- Decision logging may impact performance, use only for validation
- Document any acceptable divergences between Python and JavaScript

---

## Next Steps

1. **Start with Step 1:** Create basic baiting comparison tests
2. **Validate approach:** Ensure first test works before proceeding
3. **Iterate:** Build on successful tests
4. **Document:** Keep this file updated with progress

**Current Focus:** Step 1 - Full Battle Simulations with Baiting Enabled vs Disabled
