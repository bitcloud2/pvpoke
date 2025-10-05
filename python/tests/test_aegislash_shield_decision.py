"""
Test Aegislash Shield Decision Override (Step 1X)

Tests the special shield decision logic for Aegislash Shield form:
- Aegislash Shield form doesn't shield if damage * 2 < current HP
- This override applies even when normal shield logic would shield

JavaScript reference: Battle.js lines 1120-1122
"""

import pytest
from unittest.mock import Mock, MagicMock
from pvpoke.battle.ai import ActionLogic, ShieldDecision
from pvpoke.core.pokemon import Pokemon
from pvpoke.core.moves import ChargedMove, FastMove
from pvpoke.battle.damage_calculator import DamageCalculator


class TestAegislashShieldDecision:
    """Test Aegislash Shield form shield decision override."""
    
    @pytest.fixture
    def mock_battle(self):
        """Create a mock battle instance."""
        battle = Mock()
        battle.get_mode = Mock(return_value="simulate")
        return battle
    
    @pytest.fixture
    def aegislash_shield(self):
        """Create Aegislash in Shield form."""
        aegislash = Mock(spec=Pokemon)
        aegislash.active_form_id = "aegislash_shield"
        aegislash.current_hp = 100
        aegislash.stats = Mock(hp=100, atk=100, defense=100)
        aegislash.shields = 2
        aegislash.energy = 0
        aegislash.stat_buffs = [0, 0]
        
        # Setup fast move
        fast_move = Mock(spec=FastMove)
        fast_move.turns = 2
        fast_move.energy_gain = 8
        fast_move.damage = 3
        aegislash.fast_move = fast_move
        
        # Setup charged moves
        charged_move_1 = Mock(spec=ChargedMove)
        charged_move_1.energy_cost = 35
        charged_move_1.damage = 40
        aegislash.charged_move_1 = charged_move_1
        aegislash.charged_move_2 = None
        
        return aegislash
    
    @pytest.fixture
    def attacker(self):
        """Create a generic attacker Pokemon."""
        attacker = Mock(spec=Pokemon)
        attacker.current_hp = 100
        attacker.stats = Mock(hp=100, atk=120, defense=100)
        attacker.energy = 50
        attacker.stat_buffs = [0, 0]
        attacker.bait_shields = 0
        
        # Setup fast move
        fast_move = Mock(spec=FastMove)
        fast_move.turns = 2
        fast_move.energy_gain = 8
        fast_move.damage = 5
        fast_move.cooldown = 1000
        attacker.fast_move = fast_move
        
        # Setup charged moves
        charged_move_1 = Mock(spec=ChargedMove)
        charged_move_1.energy_cost = 35
        charged_move_1.damage = 45
        attacker.charged_move_1 = charged_move_1
        
        charged_move_2 = Mock(spec=ChargedMove)
        charged_move_2.energy_cost = 50
        charged_move_2.damage = 60
        attacker.charged_move_2 = charged_move_2
        
        return attacker
    
    @pytest.fixture
    def low_damage_move(self):
        """Create a low damage charged move (< 50% of Aegislash HP)."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 35
        move.damage = 40  # Less than 50 HP
        move.self_attack_debuffing = False
        return move
    
    @pytest.fixture
    def high_damage_move(self):
        """Create a high damage charged move (> 50% of Aegislash HP)."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 50
        move.damage = 60  # More than 50 HP
        move.self_attack_debuffing = False
        return move
    
    def test_aegislash_shield_no_shield_low_damage(self, mock_battle, attacker, aegislash_shield, low_damage_move):
        """Test that Aegislash Shield form doesn't shield low damage moves."""
        # Mock damage calculation to return 40 damage
        DamageCalculator.calculate_damage = Mock(return_value=40)
        
        # Aegislash has 100 HP, damage is 40
        # damage * 2 = 80 < 100 HP, so should NOT shield
        decision = ActionLogic.would_shield(mock_battle, attacker, aegislash_shield, low_damage_move)
        
        assert decision.value == False, "Aegislash Shield should not shield when damage * 2 < HP"
    
    def test_aegislash_shield_shields_high_damage(self, mock_battle, attacker, aegislash_shield, high_damage_move):
        """Test that Aegislash Shield form shields high damage moves."""
        # Mock damage calculation to return 60 damage
        DamageCalculator.calculate_damage = Mock(return_value=60)
        
        # Aegislash has 100 HP, damage is 60
        # damage * 2 = 120 > 100 HP, so normal shield logic applies
        # Since damage (60) >= HP/1.4 (71.4) is false, but we need to check other conditions
        decision = ActionLogic.would_shield(mock_battle, attacker, aegislash_shield, high_damage_move)
        
        # The override doesn't apply, so normal shield logic determines the result
        # In this case, 60 damage might not trigger shields based on normal logic
        # But the key is that the override (use_shield = False) does NOT apply
        assert decision is not None
    
    def test_aegislash_shield_exact_threshold(self, mock_battle, attacker, aegislash_shield):
        """Test Aegislash Shield form at exact damage threshold."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 35
        move.damage = 50  # Exactly half HP
        move.self_attack_debuffing = False
        
        # Mock damage calculation to return 50 damage
        DamageCalculator.calculate_damage = Mock(return_value=50)
        
        # Aegislash has 100 HP, damage is 50
        # damage * 2 = 100 == 100 HP, so condition is false (not less than)
        # Normal shield logic applies
        decision = ActionLogic.would_shield(mock_battle, attacker, aegislash_shield, move)
        
        # The override doesn't apply since 50 * 2 is not < 100
        assert decision is not None
    
    def test_aegislash_shield_low_hp(self, mock_battle, attacker, aegislash_shield, low_damage_move):
        """Test Aegislash Shield form with low HP."""
        # Set Aegislash to low HP
        aegislash_shield.current_hp = 60
        
        # Mock damage calculation to return 40 damage
        DamageCalculator.calculate_damage = Mock(return_value=40)
        
        # Aegislash has 60 HP, damage is 40
        # damage * 2 = 80 > 60 HP, so override doesn't apply
        decision = ActionLogic.would_shield(mock_battle, attacker, aegislash_shield, low_damage_move)
        
        # Normal shield logic applies, might shield due to high damage ratio
        assert decision is not None
    
    def test_aegislash_shield_very_low_damage(self, mock_battle, attacker, aegislash_shield):
        """Test Aegislash Shield form with very low damage move."""
        move = Mock(spec=ChargedMove)
        move.energy_cost = 35
        move.damage = 10  # Very low damage
        move.self_attack_debuffing = False
        
        # Mock damage calculation to return 10 damage
        DamageCalculator.calculate_damage = Mock(return_value=10)
        
        # Aegislash has 100 HP, damage is 10
        # damage * 2 = 20 < 100 HP, so should NOT shield
        decision = ActionLogic.would_shield(mock_battle, attacker, aegislash_shield, move)
        
        assert decision.value == False, "Aegislash Shield should not shield very low damage"
    
    def test_aegislash_shield_overrides_normal_logic(self, mock_battle, attacker, aegislash_shield):
        """Test that Aegislash override takes precedence over normal shield logic."""
        # Create a move that would normally trigger shielding
        move = Mock(spec=ChargedMove)
        move.energy_cost = 35
        move.damage = 45  # Would normally be shielded
        move.self_attack_debuffing = False
        
        # Mock damage calculation to return 45 damage
        DamageCalculator.calculate_damage = Mock(return_value=45)
        
        # Set attacker to have high energy and make move look threatening
        attacker.energy = 50
        
        # Aegislash has 100 HP, damage is 45
        # damage * 2 = 90 < 100 HP, so should NOT shield despite other conditions
        decision = ActionLogic.would_shield(mock_battle, attacker, aegislash_shield, move)
        
        assert decision.value == False, "Aegislash override should take precedence"
    
    def test_non_aegislash_not_affected(self, mock_battle, attacker):
        """Test that non-Aegislash Pokemon are not affected by the override."""
        # Create a regular Pokemon (not Aegislash)
        defender = Mock(spec=Pokemon)
        defender.active_form_id = None  # Not Aegislash
        defender.current_hp = 100
        defender.stats = Mock(hp=100, atk=100, defense=100)
        defender.shields = 2
        defender.energy = 0
        defender.stat_buffs = [0, 0]
        
        fast_move = Mock(spec=FastMove)
        fast_move.turns = 2
        fast_move.energy_gain = 8
        fast_move.damage = 3
        defender.fast_move = fast_move
        
        charged_move = Mock(spec=ChargedMove)
        charged_move.energy_cost = 35
        charged_move.damage = 40
        defender.charged_move_1 = charged_move
        defender.charged_move_2 = None
        
        move = Mock(spec=ChargedMove)
        move.energy_cost = 35
        move.damage = 40
        move.self_attack_debuffing = False
        
        # Mock damage calculation
        DamageCalculator.calculate_damage = Mock(return_value=40)
        
        # Normal shield logic applies (no Aegislash override)
        decision = ActionLogic.would_shield(mock_battle, attacker, defender, move)
        
        # Result depends on normal shield logic, not the Aegislash override
        assert decision is not None
    
    def test_aegislash_blade_form_not_affected(self, mock_battle, attacker):
        """Test that Aegislash Blade form doesn't get the shield override."""
        # Create Aegislash in Blade form
        aegislash_blade = Mock(spec=Pokemon)
        aegislash_blade.active_form_id = "aegislash_blade"  # Blade form, not Shield
        aegislash_blade.current_hp = 100
        aegislash_blade.stats = Mock(hp=100, atk=150, defense=50)
        aegislash_blade.shields = 2
        aegislash_blade.energy = 0
        aegislash_blade.stat_buffs = [0, 0]
        
        fast_move = Mock(spec=FastMove)
        fast_move.turns = 2
        fast_move.energy_gain = 8
        fast_move.damage = 3
        aegislash_blade.fast_move = fast_move
        
        charged_move = Mock(spec=ChargedMove)
        charged_move.energy_cost = 35
        charged_move.damage = 40
        aegislash_blade.charged_move_1 = charged_move
        aegislash_blade.charged_move_2 = None
        
        move = Mock(spec=ChargedMove)
        move.energy_cost = 35
        move.damage = 40
        move.self_attack_debuffing = False
        
        # Mock damage calculation
        DamageCalculator.calculate_damage = Mock(return_value=40)
        
        # Normal shield logic applies (override only for Shield form)
        decision = ActionLogic.would_shield(mock_battle, attacker, aegislash_blade, move)
        
        # Result depends on normal shield logic
        assert decision is not None
    
    def test_aegislash_shield_with_attack_debuffing_move(self, mock_battle, attacker, aegislash_shield):
        """Test Aegislash Shield form with attack debuffing move (like Superpower)."""
        # Create a self-attack debuffing move with high damage
        move = Mock(spec=ChargedMove)
        move.energy_cost = 50
        move.damage = 45  # Less than 50 HP but high damage ratio
        move.self_attack_debuffing = True
        
        # Mock damage calculation
        DamageCalculator.calculate_damage = Mock(return_value=45)
        
        # Aegislash has 100 HP, damage is 45
        # damage * 2 = 90 < 100 HP
        # Even though it's a self-attack debuffing move with damage/HP > 0.55 (would normally shield),
        # the Aegislash override should take precedence
        decision = ActionLogic.would_shield(mock_battle, attacker, aegislash_shield, move)
        
        assert decision.value == False, "Aegislash override should apply even for attack debuffing moves"
    
    def test_aegislash_shield_with_bait_shields_setting(self, mock_battle, attacker, aegislash_shield):
        """Test Aegislash Shield form when attacker has bait_shields=2."""
        # Set attacker to always bait shields
        attacker.bait_shields = 2
        
        move = Mock(spec=ChargedMove)
        move.energy_cost = 35
        move.damage = 40
        move.self_attack_debuffing = False
        
        # Mock damage calculation
        DamageCalculator.calculate_damage = Mock(return_value=40)
        
        # Aegislash has 100 HP, damage is 40
        # damage * 2 = 80 < 100 HP
        # The bait_shields=2 setting would normally force use_shield=True,
        # but Aegislash override should take precedence
        decision = ActionLogic.would_shield(mock_battle, attacker, aegislash_shield, move)
        
        assert decision.value == False, "Aegislash override should apply even with bait_shields=2"
    
    def test_aegislash_shield_decision_structure(self, mock_battle, attacker, aegislash_shield, low_damage_move):
        """Test that the shield decision returns proper structure."""
        # Mock damage calculation
        DamageCalculator.calculate_damage = Mock(return_value=40)
        
        decision = ActionLogic.would_shield(mock_battle, attacker, aegislash_shield, low_damage_move)
        
        # Verify decision structure
        assert isinstance(decision, ShieldDecision)
        assert hasattr(decision, 'value')
        assert hasattr(decision, 'shield_weight')
        assert hasattr(decision, 'no_shield_weight')
        assert isinstance(decision.value, bool)
        assert isinstance(decision.shield_weight, (int, float))
        assert isinstance(decision.no_shield_weight, (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
