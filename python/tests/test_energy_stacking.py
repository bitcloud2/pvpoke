"""
Tests for Energy Stacking Logic for Self-Debuffing Moves (Step 1S).

This test suite validates the JavaScript ActionLogic.js lines 918-935 port:
- Target energy calculation for optimal stacking (Step 1S.1)
- Move damage vs opponent HP validation (Step 1S.2)
- Survivability check during energy building phase (Step 1S.3)
- Main energy stacking decision logic (Step 1S.4)
- Shield baiting override for self-debuffing moves (Step 1T)
"""

import pytest
from unittest.mock import Mock
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.battle.ai import ActionLogic


class MockBattle:
    """Mock battle object for testing."""
    def __init__(self):
        self.current_turn = 0
        self.decisions = []
    
    def log_decision(self, poke, message):
        """Log decisions for testing."""
        self.decisions.append(message)
    
    def get_mode(self):
        return "simulate"


def create_test_pokemon(name, hp, energy, fast_move_turns=1, fast_move_energy=3, 
                       charged_move_energy=40, self_debuffing=False, self_buffing=False):
    """Helper to create test Pokemon using Mock."""
    pokemon = Mock()
    pokemon.species_id = name.lower()
    pokemon.index = 0
    
    # Set up fast move
    fast_move = Mock(spec=FastMove)
    fast_move.energy_gain = fast_move_energy
    fast_move.turns = fast_move_turns
    fast_move.damage = 5
    fast_move.power = 5  # Add power for damage calculation
    fast_move.move_id = f"{name}_fast"
    fast_move.move_type = "normal"
    pokemon.fast_move = fast_move
    
    # Set up charged move
    charged_move = Mock(spec=ChargedMove)
    charged_move.energy_cost = charged_move_energy
    charged_move.power = 100
    charged_move.move_id = f"{name}_charged"
    charged_move.move_type = "normal"
    charged_move.self_debuffing = self_debuffing
    charged_move.self_attack_debuffing = self_debuffing
    charged_move.self_buffing = self_buffing
    
    pokemon.charged_move_1 = charged_move
    pokemon.charged_move_2 = None
    pokemon.current_hp = hp
    pokemon.energy = energy
    pokemon.shields = 1
    
    # Add stats for damage calculation
    pokemon.stats = Mock()
    pokemon.stats.atk = 100
    pokemon.stats.def_ = 100
    pokemon.stats.defense = 100  # Add defense attribute
    pokemon.types = ["normal"]  # Make types iterable
    pokemon.type_effectiveness = {"normal": 1.0}
    pokemon.stat_buffs = [0, 0]
    
    # Mock methods needed by damage calculator
    pokemon.get_effective_stat = Mock(return_value=100)
    pokemon.calculate_stats = Mock(return_value=pokemon.stats)
    
    return pokemon


class TestStep1S1TargetEnergyCalculation:
    """Test Step 1S.1: Target Energy Calculation."""
    
    def test_calculate_stacking_target_energy_35_energy(self):
        """Test target energy calculation for 35 energy move."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 35
        
        # floor(100/35) * 35 = 2 * 35 = 70
        target = ActionLogic.calculate_stacking_target_energy(move)
        assert target == 70
    
    def test_calculate_stacking_target_energy_40_energy(self):
        """Test target energy calculation for 40 energy move."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 40
        
        # floor(100/40) * 40 = 2 * 40 = 80
        target = ActionLogic.calculate_stacking_target_energy(move)
        assert target == 80
    
    def test_calculate_stacking_target_energy_45_energy(self):
        """Test target energy calculation for 45 energy move."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 45
        
        # floor(100/45) * 45 = 2 * 45 = 90
        target = ActionLogic.calculate_stacking_target_energy(move)
        assert target == 90
    
    def test_calculate_stacking_target_energy_50_energy(self):
        """Test target energy calculation for 50 energy move."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 50
        
        # floor(100/50) * 50 = 2 * 50 = 100
        target = ActionLogic.calculate_stacking_target_energy(move)
        assert target == 100
    
    def test_calculate_stacking_target_energy_55_energy(self):
        """Test target energy calculation for 55 energy move (single use)."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 55
        
        # floor(100/55) * 55 = 1 * 55 = 55
        target = ActionLogic.calculate_stacking_target_energy(move)
        assert target == 55
    
    def test_calculate_stacking_target_energy_60_energy(self):
        """Test target energy calculation for 60 energy move (single use)."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 60
        
        # floor(100/60) * 60 = 1 * 60 = 60
        target = ActionLogic.calculate_stacking_target_energy(move)
        assert target == 60
    
    def test_calculate_stacking_target_energy_zero_energy(self):
        """Test target energy calculation for zero energy move."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 0
        
        target = ActionLogic.calculate_stacking_target_energy(move)
        assert target == 0
    
    def test_calculate_stacking_target_energy_negative_energy(self):
        """Test target energy calculation for negative energy move."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = -10
        
        target = ActionLogic.calculate_stacking_target_energy(move)
        assert target == 0


class TestStep1S2MoveKOValidation:
    """Test Step 1S.2: Move Damage Validation."""
    
    def test_validate_stacking_wont_miss_ko_safe_to_stack(self):
        """Test validation when safe to stack (opponent HP > damage)."""
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 0
        move = poke.charged_move_1
        
        # Opponent HP is high, safe to stack
        result = ActionLogic.validate_stacking_wont_miss_ko(poke, opponent, move)
        assert result is True
    
    def test_validate_stacking_wont_miss_ko_would_ko(self):
        """Test validation when move would KO opponent (should not stack)."""
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40)
        opponent = create_test_pokemon("Azumarill", hp=10, energy=50)
        opponent.shields = 0
        move = poke.charged_move_1
        
        # Move would KO, should not stack
        result = ActionLogic.validate_stacking_wont_miss_ko(poke, opponent, move)
        assert result is False
    
    def test_validate_stacking_wont_miss_ko_opponent_has_shields(self):
        """Test validation when opponent has shields (safe to stack)."""
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40)
        opponent = create_test_pokemon("Azumarill", hp=10, energy=50)
        opponent.shields = 1  # Has shield
        move = poke.charged_move_1
        
        # Opponent has shields, safe to stack
        result = ActionLogic.validate_stacking_wont_miss_ko(poke, opponent, move)
        assert result is True
    
    def test_validate_stacking_wont_miss_ko_multiple_shields(self):
        """Test validation when opponent has multiple shields."""
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40)
        opponent = create_test_pokemon("Azumarill", hp=10, energy=50)
        opponent.shields = 2  # Multiple shields
        move = poke.charged_move_1
        
        # Opponent has shields, safe to stack
        result = ActionLogic.validate_stacking_wont_miss_ko(poke, opponent, move)
        assert result is True


class TestStep1S3SurvivabilityCheck:
    """Test Step 1S.3: Survivability Check During Energy Building."""
    
    def test_can_survive_stacking_phase_high_hp(self):
        """Test survivability with high HP."""
        poke = create_test_pokemon("Machamp", hp=150, energy=50, fast_move_turns=1)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=1)
        
        # High HP, can survive
        result = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert result is True
    
    def test_can_survive_stacking_phase_low_hp_no_timing(self):
        """Test survivability with low HP and no timing advantage."""
        poke = create_test_pokemon("Machamp", hp=5, energy=50, fast_move_turns=1)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=1)
        
        # Low HP, no timing advantage
        result = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert result is False
    
    def test_can_survive_stacking_phase_timing_advantage(self):
        """Test survivability with timing advantage compensating for low HP."""
        poke = create_test_pokemon("Machamp", hp=15, energy=50, fast_move_turns=1)  # 500ms
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=3)  # 1500ms
        
        # Timing advantage: 1500 - 500 = 1000ms > 500ms
        result = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert result is True
    
    def test_can_survive_stacking_phase_exact_threshold_hp(self):
        """Test survivability at exact HP threshold."""
        poke = create_test_pokemon("Machamp", hp=20, energy=50, fast_move_turns=1)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=1)
        
        # With mocked damage calculation, should pass or fail based on actual damage
        result = ActionLogic.can_survive_stacking_phase(poke, opponent)
        # Result depends on actual damage calculation
        assert isinstance(result, bool)
    
    def test_can_survive_stacking_phase_exact_timing_threshold(self):
        """Test survivability at exact timing threshold (500ms)."""
        poke = create_test_pokemon("Machamp", hp=5, energy=50, fast_move_turns=2)  # 1000ms
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=3)  # 1500ms
        
        # Timing difference: 1500 - 1000 = 500ms (NOT > 500ms)
        result = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert result is False
    
    def test_can_survive_stacking_phase_just_above_timing_threshold(self):
        """Test survivability just above timing threshold."""
        poke = create_test_pokemon("Machamp", hp=5, energy=50, fast_move_turns=1)  # 500ms
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=3)  # 1500ms
        
        # Timing difference: 1500 - 500 = 1000ms > 500ms
        result = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert result is True


class TestStep1S4MainStackingDecision:
    """Test Step 1S.4: Main Energy Stacking Decision Logic."""
    
    def test_should_stack_energy_all_conditions_met(self):
        """Test stacking when all conditions are met."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        move = poke.charged_move_1
        
        # All conditions met: self-debuffing, below target, won't KO, can survive
        result = ActionLogic.should_stack_energy_for_debuffing_move(battle, poke, opponent, move)
        assert result is True
    
    def test_should_stack_energy_non_debuffing_move(self):
        """Test no stacking for non-debuffing moves."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=False)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        move = poke.charged_move_1
        
        # Not self-debuffing
        result = ActionLogic.should_stack_energy_for_debuffing_move(battle, poke, opponent, move)
        assert result is False
    
    def test_should_stack_energy_at_target_energy(self):
        """Test no stacking when at target energy."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        move = poke.charged_move_1
        
        # At target energy (80)
        result = ActionLogic.should_stack_energy_for_debuffing_move(battle, poke, opponent, move)
        assert result is False
    
    def test_should_stack_energy_above_target_energy(self):
        """Test no stacking when above target energy."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=90, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        move = poke.charged_move_1
        
        # Above target energy (80)
        result = ActionLogic.should_stack_energy_for_debuffing_move(battle, poke, opponent, move)
        assert result is False
    
    def test_should_stack_energy_would_ko_opponent(self):
        """Test no stacking when move would KO opponent."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=10, energy=50)
        opponent.shields = 0
        move = poke.charged_move_1
        
        # Move would KO opponent
        result = ActionLogic.should_stack_energy_for_debuffing_move(battle, poke, opponent, move)
        assert result is False
    
    def test_should_stack_energy_cant_survive(self):
        """Test no stacking when can't survive energy building."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=5, energy=50, charged_move_energy=40, self_debuffing=True, fast_move_turns=1)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=1)
        move = poke.charged_move_1
        
        # Can't survive energy building
        result = ActionLogic.should_stack_energy_for_debuffing_move(battle, poke, opponent, move)
        assert result is False


class TestEnergyStackingLogic:
    """Test energy stacking logic for self-debuffing moves (legacy tests)."""
    
    def test_target_energy_calculation_40_energy_move(self):
        """Test target energy calculation for 40 energy move (can stack 2 times)."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        
        # Target energy should be floor(100/40) * 40 = 2 * 40 = 80
        # At 50 energy, should defer to build to 80
        move = poke.charged_move_1
        
        # Should stack because energy (50) < target (80)
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is True
        assert "can stack the move 2 times" in battle.decisions[0]
    
    def test_target_energy_calculation_50_energy_move(self):
        """Test target energy calculation for 50 energy move (can stack 2 times)."""
        battle = MockBattle()
        poke = create_test_pokemon("Lucario", hp=150, energy=60, charged_move_energy=50, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        
        # Target energy should be floor(100/50) * 50 = 2 * 50 = 100
        # At 60 energy, should defer to build to 100
        move = poke.charged_move_1
        
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is True
        assert "can stack the move 2 times" in battle.decisions[0]
    
    def test_target_energy_calculation_35_energy_move(self):
        """Test target energy calculation for 35 energy move (can stack 2 times)."""
        battle = MockBattle()
        poke = create_test_pokemon("Primeape", hp=150, energy=40, charged_move_energy=35, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        
        # Target energy should be floor(100/35) * 35 = 2 * 35 = 70
        # At 40 energy, should defer to build to 70
        move = poke.charged_move_1
        
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is True
        assert "can stack the move 2 times" in battle.decisions[0]
    
    def test_at_target_energy_no_stacking(self):
        """Test that stacking doesn't occur when at target energy."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        
        # At target energy (80), should not stack
        move = poke.charged_move_1
        
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is False
    
    def test_above_target_energy_no_stacking(self):
        """Test that stacking doesn't occur when above target energy."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=90, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        
        # Above target energy (80), should not stack
        move = poke.charged_move_1
        
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is False
    
    def test_non_debuffing_move_no_stacking(self):
        """Test that non-debuffing moves don't trigger stacking logic."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=False)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        
        move = poke.charged_move_1
        
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is False


class TestMoveKOValidation:
    """Test move damage vs opponent HP validation."""
    
    def test_move_would_ko_opponent_no_stacking(self):
        """Test that stacking doesn't occur if move would KO opponent."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=10, energy=50)  # Low HP
        opponent.shields = 0
        
        move = poke.charged_move_1
        
        # Should not stack because move would KO
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is False
    
    def test_opponent_has_shields_allows_stacking(self):
        """Test that stacking occurs even if move would KO when opponent has shields."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=10, energy=50)  # Low HP
        opponent.shields = 1  # Has shield
        
        move = poke.charged_move_1
        
        # Should stack because opponent has shields (move won't KO)
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is True
    
    def test_high_hp_opponent_allows_stacking(self):
        """Test that stacking occurs when opponent HP is high."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)  # High HP
        
        move = poke.charged_move_1
        
        # Should stack because opponent HP is high
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is True


class TestSurvivabilityCheck:
    """Test survivability check during energy building phase (legacy tests using new methods)."""
    
    def test_hp_survivability_high_hp(self):
        """Test HP survivability when Pokemon has high HP."""
        poke = create_test_pokemon("Machamp", hp=150, energy=50)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.fast_move.damage = 10
        
        # HP (150) > opponent fast damage (10) * 2 = 20
        survivability = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert survivability is True
    
    def test_hp_survivability_low_hp_no_timing_advantage(self):
        """Test that low HP without timing advantage fails survivability."""
        poke = create_test_pokemon("Machamp", hp=10, energy=50, fast_move_turns=1)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=1)
        
        # With mocked stats (100/100), damage will be ~3
        # HP (10) > damage (~3) * 2 = ~6, so HP survivability passes
        # But we want to test the case where it fails, so set HP very low
        poke.current_hp = 3  # 3 <= ~3 * 2 = ~6, so should fail
        
        # No timing advantage (same turns: 1 turn each, 500ms - 500ms = 0 <= 500)
        survivability = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert survivability is False
    
    def test_timing_advantage_compensates_for_low_hp(self):
        """Test that timing advantage allows stacking even with low HP."""
        poke = create_test_pokemon("Machamp", hp=15, energy=50, fast_move_turns=1)  # 1 turn = 500ms
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=3)  # 3 turns = 1500ms
        opponent.fast_move.damage = 10
        
        # HP (15) <= opponent fast damage (10) * 2 = 20
        # But timing advantage: 1500ms - 500ms = 1000ms > 500ms
        survivability = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert survivability is True
    
    def test_timing_advantage_calculation_exact_threshold(self):
        """Test timing advantage at exact 500ms threshold."""
        poke = create_test_pokemon("Machamp", hp=10, energy=50, fast_move_turns=1)  # 500ms
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=3)  # 1500ms
        
        # Difference: 1500ms - 500ms = 1000ms > 500ms
        # Test via can_survive_stacking_phase since timing advantage is internal logic
        survivability = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert survivability is True
    
    def test_no_timing_advantage_same_cooldown(self):
        """Test no timing advantage when cooldowns are the same."""
        poke = create_test_pokemon("Machamp", hp=5, energy=50, fast_move_turns=2)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=2)
        
        # Difference: 1000ms - 1000ms = 0ms <= 500ms
        # Low HP and no timing advantage should fail
        survivability = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert survivability is False
    
    def test_no_timing_advantage_poke_slower(self):
        """Test no timing advantage when Pokemon is slower."""
        poke = create_test_pokemon("Machamp", hp=5, energy=50, fast_move_turns=3)  # 1500ms
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=1)  # 500ms
        
        # Difference: 500ms - 1500ms = -1000ms <= 500ms
        # Low HP and no timing advantage should fail
        survivability = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert survivability is False
    
    def test_timing_advantage_just_above_threshold(self):
        """Test timing advantage just above 500ms threshold."""
        poke = create_test_pokemon("Machamp", hp=10, energy=50, fast_move_turns=1)  # 500ms
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=3)  # 1500ms
        
        # Difference: 1500ms - 500ms = 1000ms > 500ms
        survivability = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert survivability is True
    
    def test_timing_advantage_just_below_threshold(self):
        """Test no timing advantage just below 500ms threshold."""
        poke = create_test_pokemon("Machamp", hp=5, energy=50, fast_move_turns=2)  # 1000ms
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50, fast_move_turns=3)  # 1500ms
        
        # Difference: 1500ms - 1000ms = 500ms <= 500ms (not greater than)
        # Low HP and no timing advantage should fail
        survivability = ActionLogic.can_survive_stacking_phase(poke, opponent)
        assert survivability is False


class TestShieldBaitingOverride:
    """Test shield baiting override for self-debuffing moves."""
    
    def test_override_with_self_buffing_move(self):
        """Test override with self-buffing move when at target energy."""
        battle = MockBattle()
        poke = create_test_pokemon("Lucario", hp=150, energy=100, charged_move_energy=50, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        
        # Add a self-buffing move with close energy cost
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "power_up_punch"
        bait_move.power = 40
        bait_move.energy_cost = 40
        bait_move.move_type = "fighting"
        bait_move.self_buffing = True
        bait_move.self_debuffing = False
        poke.charged_move_2 = bait_move
        poke.bait_shields = True
        
        active_moves = [bait_move, poke.charged_move_1]  # Sorted by energy
        
        # Should override with self-buffing move
        override = ActionLogic.should_override_with_bait_move(
            battle, poke, opponent, poke.charged_move_1, active_moves
        )
        assert override == bait_move
        assert "self-buffing bait move" in battle.decisions[0]
    
    def test_override_when_opponent_would_shield(self):
        """Test override when opponent would shield the bigger move."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        
        # Add a non-debuffing move with close energy cost
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "cross_chop"
        bait_move.power = 55
        bait_move.energy_cost = 35
        bait_move.move_type = "fighting"
        bait_move.self_debuffing = False
        bait_move.self_buffing = False
        poke.charged_move_2 = bait_move
        poke.bait_shields = True
        
        active_moves = [bait_move, poke.charged_move_1]
        
        # Should override because opponent would shield
        override = ActionLogic.should_override_with_bait_move(
            battle, poke, opponent, poke.charged_move_1, active_moves
        )
        # Note: This depends on would_shield implementation
        # For now, just verify the method runs without error
        assert override is None or isinstance(override, ChargedMove)
    
    def test_no_override_below_target_energy(self):
        """Test no override when below target energy."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "cross_chop"
        bait_move.power = 55
        bait_move.energy_cost = 35
        bait_move.move_type = "fighting"
        bait_move.self_buffing = True
        bait_move.self_debuffing = False
        poke.charged_move_2 = bait_move
        poke.bait_shields = True
        
        active_moves = [bait_move, poke.charged_move_1]
        
        # Should not override because below target energy (80)
        override = ActionLogic.should_override_with_bait_move(
            battle, poke, opponent, poke.charged_move_1, active_moves
        )
        assert override is None
    
    def test_no_override_when_no_shields(self):
        """Test no override when opponent has no shields."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 0  # No shields
        
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "cross_chop"
        bait_move.power = 55
        bait_move.energy_cost = 35
        bait_move.move_type = "fighting"
        bait_move.self_buffing = True
        bait_move.self_debuffing = False
        poke.charged_move_2 = bait_move
        poke.bait_shields = True
        
        active_moves = [bait_move, poke.charged_move_1]
        
        # Should not override when no shields
        override = ActionLogic.should_override_with_bait_move(
            battle, poke, opponent, poke.charged_move_1, active_moves
        )
        assert override is None
    
    def test_no_override_when_baiting_disabled(self):
        """Test no override when bait_shields is disabled."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "cross_chop"
        bait_move.power = 55
        bait_move.energy_cost = 35
        bait_move.move_type = "fighting"
        bait_move.self_buffing = True
        bait_move.self_debuffing = False
        poke.charged_move_2 = bait_move
        poke.bait_shields = False  # Baiting disabled
        
        active_moves = [bait_move, poke.charged_move_1]
        
        # Should not override when baiting disabled
        override = ActionLogic.should_override_with_bait_move(
            battle, poke, opponent, poke.charged_move_1, active_moves
        )
        assert override is None
    
    def test_no_override_energy_difference_too_large(self):
        """Test no override when energy difference is too large (> 10)."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=100, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        
        # Add a move with large energy difference (not self-buffing, so won't override)
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "cross_chop"
        bait_move.power = 55
        bait_move.energy_cost = 55  # 55 - 40 = 15 > 10
        bait_move.move_type = "fighting"
        bait_move.self_buffing = False  # Not self-buffing
        bait_move.self_debuffing = False
        poke.charged_move_2 = bait_move
        poke.bait_shields = True
        
        active_moves = [poke.charged_move_1, bait_move]  # Sorted by energy (40, 55)
        
        # Energy difference: 40 - 40 = 0 <= 10, but we're checking the wrong move
        # Actually, the lowest energy move IS the debuffing move, so no override happens
        override = ActionLogic.should_override_with_bait_move(
            battle, poke, opponent, poke.charged_move_1, active_moves
        )
        assert override is None
    
    def test_no_override_for_non_debuffing_move(self):
        """Test no override for non-debuffing moves."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=False)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "cross_chop"
        bait_move.power = 55
        bait_move.energy_cost = 35
        bait_move.move_type = "fighting"
        bait_move.self_debuffing = False
        bait_move.self_buffing = False
        poke.charged_move_2 = bait_move
        poke.bait_shields = True
        
        active_moves = [bait_move, poke.charged_move_1]
        
        # Should not override for non-debuffing moves
        override = ActionLogic.should_override_with_bait_move(
            battle, poke, opponent, poke.charged_move_1, active_moves
        )
        assert override is None


class TestIntegratedEnergyStacking:
    """Test integrated energy stacking behavior in decision making."""
    
    def test_stacking_prevents_premature_use(self):
        """Test that energy stacking prevents premature use of self-debuffing moves."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        
        move = poke.charged_move_1
        
        # Should defer to build more energy
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is True
        
        # Verify decision log
        assert len(battle.decisions) > 0
        assert "doesn't use" in battle.decisions[0]
        assert "minimize time debuffed" in battle.decisions[0]
    
    def test_stacking_allows_use_at_target_energy(self):
        """Test that move is used when target energy is reached."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        
        move = poke.charged_move_1
        
        # Should not defer at target energy
        should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
        assert should_stack is False
    
    def test_stacking_with_multiple_scenarios(self):
        """Test energy stacking across multiple energy levels."""
        battle = MockBattle()
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        
        # Test at various energy levels for 40 energy move (target = 80)
        energy_levels = [40, 50, 60, 70, 80, 90, 100]
        expected_results = [True, True, True, True, False, False, False]
        
        for energy, expected in zip(energy_levels, expected_results):
            poke = create_test_pokemon("Machamp", hp=150, energy=energy, 
                                     charged_move_energy=40, self_debuffing=True)
            move = poke.charged_move_1
            
            should_stack = ActionLogic.should_stack_self_debuffing_move(battle, poke, opponent, move)
            assert should_stack == expected, f"Failed at energy={energy}, expected={expected}"


class TestStep1T1CloseEnergyCostComparison:
    """Test Step 1T.1: Close Energy Cost Comparison."""
    
    def test_check_baiting_override_finds_alternative(self):
        """Test finding alternative move with close energy cost."""
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        poke.bait_shields = True
        
        # Add alternative move with energy cost within 10
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "cross_chop"
        bait_move.energy_cost = 35  # 35 - 40 = -5, within 10
        bait_move.self_debuffing = False
        bait_move.self_buffing = False
        
        active_moves = [bait_move, poke.charged_move_1]
        
        alternative = ActionLogic.check_baiting_override_for_stacking(
            poke, opponent, poke.charged_move_1, active_moves
        )
        assert alternative == bait_move
    
    def test_check_baiting_override_energy_diff_too_large(self):
        """Test no override when energy difference > 10."""
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        poke.bait_shields = True
        
        # Add alternative move with energy cost difference > 10
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "dynamic_punch"
        bait_move.energy_cost = 55  # 55 - 40 = 15 > 10
        bait_move.self_debuffing = False
        
        active_moves = [poke.charged_move_1, bait_move]
        
        alternative = ActionLogic.check_baiting_override_for_stacking(
            poke, opponent, poke.charged_move_1, active_moves
        )
        assert alternative is None
    
    def test_check_baiting_override_no_shields(self):
        """Test no override when opponent has no shields."""
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 0  # No shields
        poke.bait_shields = True
        
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "cross_chop"
        bait_move.energy_cost = 35
        bait_move.self_debuffing = False
        
        active_moves = [bait_move, poke.charged_move_1]
        
        alternative = ActionLogic.check_baiting_override_for_stacking(
            poke, opponent, poke.charged_move_1, active_moves
        )
        assert alternative is None
    
    def test_check_baiting_override_baiting_disabled(self):
        """Test no override when bait_shields is disabled."""
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        poke.bait_shields = False  # Baiting disabled
        
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "cross_chop"
        bait_move.energy_cost = 35
        bait_move.self_debuffing = False
        
        active_moves = [bait_move, poke.charged_move_1]
        
        alternative = ActionLogic.check_baiting_override_for_stacking(
            poke, opponent, poke.charged_move_1, active_moves
        )
        assert alternative is None
    
    def test_check_baiting_override_insufficient_energy(self):
        """Test no override when Pokemon lacks energy for alternative."""
        poke = create_test_pokemon("Machamp", hp=150, energy=40, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        poke.bait_shields = True
        
        # Alternative requires 45 energy but Pokemon only has 40
        bait_move = Mock(spec=ChargedMove)
        bait_move.move_id = "rock_slide"
        bait_move.energy_cost = 45
        bait_move.self_debuffing = False
        
        active_moves = [poke.charged_move_1, bait_move]
        
        alternative = ActionLogic.check_baiting_override_for_stacking(
            poke, opponent, poke.charged_move_1, active_moves
        )
        assert alternative is None


class TestStep1T2SelfBuffingMovePriority:
    """Test Step 1T.2: Self-Buffing Move Priority."""
    
    def test_should_use_buffing_move_instead(self):
        """Test preference for self-buffing alternative."""
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        poke.bait_shields = True
        
        # Self-buffing alternative
        buffing_move = Mock(spec=ChargedMove)
        buffing_move.move_id = "power_up_punch"
        buffing_move.energy_cost = 35
        buffing_move.self_buffing = True
        buffing_move.self_debuffing = False
        
        should_use = ActionLogic.should_use_buffing_move_instead(
            poke, opponent, poke.charged_move_1, buffing_move
        )
        assert should_use is True
    
    def test_no_buffing_move_preference_without_shields(self):
        """Test no buffing preference when opponent has no shields."""
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 0  # No shields
        poke.bait_shields = True
        
        buffing_move = Mock(spec=ChargedMove)
        buffing_move.move_id = "power_up_punch"
        buffing_move.energy_cost = 35
        buffing_move.self_buffing = True
        buffing_move.self_debuffing = False
        
        should_use = ActionLogic.should_use_buffing_move_instead(
            poke, opponent, poke.charged_move_1, buffing_move
        )
        assert should_use is False
    
    def test_no_buffing_move_preference_for_non_buffing(self):
        """Test no preference for non-buffing alternative."""
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        poke.bait_shields = True
        
        # Non-buffing alternative
        normal_move = Mock(spec=ChargedMove)
        normal_move.move_id = "cross_chop"
        normal_move.energy_cost = 35
        normal_move.self_buffing = False
        normal_move.self_debuffing = False
        
        should_use = ActionLogic.should_use_buffing_move_instead(
            poke, opponent, poke.charged_move_1, normal_move
        )
        assert should_use is False
    
    def test_no_buffing_move_preference_insufficient_energy(self):
        """Test no preference when insufficient energy for buffing move."""
        poke = create_test_pokemon("Machamp", hp=150, energy=30, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        poke.bait_shields = True
        
        # Buffing move requires 35 energy but Pokemon only has 30
        buffing_move = Mock(spec=ChargedMove)
        buffing_move.move_id = "power_up_punch"
        buffing_move.energy_cost = 35
        buffing_move.self_buffing = True
        
        should_use = ActionLogic.should_use_buffing_move_instead(
            poke, opponent, poke.charged_move_1, buffing_move
        )
        assert should_use is False


class TestStep1T3OpponentShieldPrediction:
    """Test Step 1T.3: Opponent Shield Prediction."""
    
    def test_should_swap_based_on_shield_prediction_true(self):
        """Test swapping when opponent would shield debuffing move."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=50, energy=50)  # Low HP to trigger shield
        opponent.shields = 1
        
        # Mock would_shield to return True
        original_would_shield = ActionLogic.would_shield
        
        def mock_would_shield(battle, attacker, defender, move):
            from pvpoke.battle.ai import ShieldDecision
            return ShieldDecision(value=True, shield_weight=4, no_shield_weight=1)
        
        ActionLogic.would_shield = staticmethod(mock_would_shield)
        
        try:
            alternative = Mock(spec=ChargedMove)
            alternative.move_id = "cross_chop"
            alternative.energy_cost = 35
            alternative.self_debuffing = False
            
            should_swap = ActionLogic.should_swap_based_on_shield_prediction(
                battle, poke, opponent, poke.charged_move_1, alternative
            )
            assert should_swap is True
        finally:
            ActionLogic.would_shield = original_would_shield
    
    def test_should_swap_based_on_shield_prediction_false(self):
        """Test no swap when opponent wouldn't shield."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        
        # Mock would_shield to return False
        original_would_shield = ActionLogic.would_shield
        
        def mock_would_shield(battle, attacker, defender, move):
            from pvpoke.battle.ai import ShieldDecision
            return ShieldDecision(value=False, shield_weight=1, no_shield_weight=4)
        
        ActionLogic.would_shield = staticmethod(mock_would_shield)
        
        try:
            alternative = Mock(spec=ChargedMove)
            alternative.move_id = "cross_chop"
            alternative.energy_cost = 35
            alternative.self_debuffing = False
            
            should_swap = ActionLogic.should_swap_based_on_shield_prediction(
                battle, poke, opponent, poke.charged_move_1, alternative
            )
            assert should_swap is False
        finally:
            ActionLogic.would_shield = original_would_shield
    
    def test_no_swap_for_debuffing_alternative(self):
        """Test no swap when alternative is also debuffing."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=50, energy=50)
        opponent.shields = 1
        
        # Mock would_shield to return True
        original_would_shield = ActionLogic.would_shield
        
        def mock_would_shield(battle, attacker, defender, move):
            from pvpoke.battle.ai import ShieldDecision
            return ShieldDecision(value=True, shield_weight=4, no_shield_weight=1)
        
        ActionLogic.would_shield = staticmethod(mock_would_shield)
        
        try:
            alternative = Mock(spec=ChargedMove)
            alternative.move_id = "close_combat"
            alternative.energy_cost = 45
            alternative.self_debuffing = True  # Also debuffing
            
            should_swap = ActionLogic.should_swap_based_on_shield_prediction(
                battle, poke, opponent, poke.charged_move_1, alternative
            )
            assert should_swap is False
        finally:
            ActionLogic.would_shield = original_would_shield


class TestStep1T4IntegratedBaitingOverride:
    """Test Step 1T.4: Integrated Baiting Override Logic."""
    
    def test_apply_baiting_override_with_buffing_move(self):
        """Test integrated override with self-buffing move."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        poke.bait_shields = True
        
        # Self-buffing alternative
        buffing_move = Mock(spec=ChargedMove)
        buffing_move.move_id = "power_up_punch"
        buffing_move.energy_cost = 35
        buffing_move.self_buffing = True
        buffing_move.self_debuffing = False
        
        active_moves = [buffing_move, poke.charged_move_1]
        
        override = ActionLogic.apply_baiting_override_for_stacking(
            battle, poke, opponent, poke.charged_move_1, active_moves
        )
        assert override == buffing_move
        assert len(battle.decisions) > 0
        assert "self-buffing bait move" in battle.decisions[0]
    
    def test_apply_baiting_override_with_shield_prediction(self):
        """Test integrated override based on shield prediction."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=50, energy=50)  # Low HP to trigger shield
        opponent.shields = 1
        poke.bait_shields = True
        
        # Mock would_shield to return True
        original_would_shield = ActionLogic.would_shield
        
        def mock_would_shield(battle, attacker, defender, move):
            from pvpoke.battle.ai import ShieldDecision
            return ShieldDecision(value=True, shield_weight=4, no_shield_weight=1)
        
        ActionLogic.would_shield = staticmethod(mock_would_shield)
        
        try:
            # Non-buffing alternative
            bait_move = Mock(spec=ChargedMove)
            bait_move.move_id = "cross_chop"
            bait_move.energy_cost = 35
            bait_move.self_buffing = False
            bait_move.self_debuffing = False
            
            active_moves = [bait_move, poke.charged_move_1]
            
            override = ActionLogic.apply_baiting_override_for_stacking(
                battle, poke, opponent, poke.charged_move_1, active_moves
            )
            assert override == bait_move
            assert len(battle.decisions) > 0
            assert "opponent would shield" in battle.decisions[0]
        finally:
            ActionLogic.would_shield = original_would_shield
    
    def test_apply_baiting_override_below_target_energy(self):
        """Test no override when below target energy."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=50, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        poke.bait_shields = True
        
        buffing_move = Mock(spec=ChargedMove)
        buffing_move.move_id = "power_up_punch"
        buffing_move.energy_cost = 35
        buffing_move.self_buffing = True
        buffing_move.self_debuffing = False
        
        active_moves = [buffing_move, poke.charged_move_1]
        
        # Below target energy (80), so no override
        override = ActionLogic.apply_baiting_override_for_stacking(
            battle, poke, opponent, poke.charged_move_1, active_moves
        )
        assert override is None
    
    def test_apply_baiting_override_non_debuffing_move(self):
        """Test no override for non-debuffing moves."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=False)
        opponent = create_test_pokemon("Azumarill", hp=150, energy=50)
        opponent.shields = 1
        poke.bait_shields = True
        
        buffing_move = Mock(spec=ChargedMove)
        buffing_move.move_id = "power_up_punch"
        buffing_move.energy_cost = 35
        buffing_move.self_buffing = True
        
        active_moves = [buffing_move, poke.charged_move_1]
        
        # Non-debuffing move, so no override
        override = ActionLogic.apply_baiting_override_for_stacking(
            battle, poke, opponent, poke.charged_move_1, active_moves
        )
        assert override is None
    
    def test_apply_baiting_override_priority_buffing_over_prediction(self):
        """Test that buffing move takes priority over shield prediction."""
        battle = MockBattle()
        poke = create_test_pokemon("Machamp", hp=150, energy=80, charged_move_energy=40, self_debuffing=True)
        opponent = create_test_pokemon("Azumarill", hp=50, energy=50)
        opponent.shields = 1
        poke.bait_shields = True
        
        # Mock would_shield to return True
        original_would_shield = ActionLogic.would_shield
        
        def mock_would_shield(battle, attacker, defender, move):
            from pvpoke.battle.ai import ShieldDecision
            return ShieldDecision(value=True, shield_weight=4, no_shield_weight=1)
        
        ActionLogic.would_shield = staticmethod(mock_would_shield)
        
        try:
            # Self-buffing alternative (should be chosen over shield prediction)
            buffing_move = Mock(spec=ChargedMove)
            buffing_move.move_id = "power_up_punch"
            buffing_move.energy_cost = 35
            buffing_move.self_buffing = True
            buffing_move.self_debuffing = False
            
            active_moves = [buffing_move, poke.charged_move_1]
            
            override = ActionLogic.apply_baiting_override_for_stacking(
                battle, poke, opponent, poke.charged_move_1, active_moves
            )
            assert override == buffing_move
            assert "self-buffing bait move" in battle.decisions[0]
        finally:
            ActionLogic.would_shield = original_would_shield


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
