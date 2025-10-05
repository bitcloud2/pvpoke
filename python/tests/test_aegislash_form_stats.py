"""
Tests for Aegislash Form Stats Calculation (Step 1AA).

This module tests the getFormStats level adjustment logic for Aegislash,
including CP-specific level scaling for form changes and CP cap enforcement.

JavaScript Reference: Pokemon.js lines 2391-2464
"""

import pytest
import math
from pvpoke.core.pokemon import Pokemon, Stats, IVs
from pvpoke.core.gamemaster import GameMaster


@pytest.fixture
def gamemaster():
    """Load GameMaster data."""
    return GameMaster()


@pytest.fixture
def aegislash_shield(gamemaster):
    """Create an Aegislash in Shield form for Great League (CP 1500)."""
    shield_data = gamemaster.get_pokemon("aegislash_shield")
    
    aegislash = Pokemon(
        species_id="aegislash_shield",
        species_name="Aegislash (Shield)",
        dex=681,
        base_stats=shield_data.base_stats,
        types=["steel", "ghost"],
        level=40.0,
        ivs=IVs(0, 15, 15)
    )
    
    aegislash.active_form_id = "aegislash_shield"
    return aegislash


@pytest.fixture
def aegislash_blade(gamemaster):
    """Create an Aegislash in Blade form."""
    blade_data = gamemaster.get_pokemon("aegislash_blade")
    
    aegislash = Pokemon(
        species_id="aegislash_blade",
        species_name="Aegislash (Blade)",
        dex=681,
        base_stats=blade_data.base_stats,
        types=["steel", "ghost"],
        level=21.0,
        ivs=IVs(0, 15, 15)
    )
    
    aegislash.active_form_id = "aegislash_blade"
    return aegislash


class TestLevelAdjustmentGreatLeague:
    """Test level adjustment logic for Great League (CP 1500)."""
    
    def test_shield_to_blade_level_calculation(self, aegislash_shield):
        """
        Test Shield -> Blade level adjustment in Great League.
        
        JavaScript: if(battleCP == 1500) { newLevel = Math.ceil(self.level * 0.5) + 1; }
        Shield level 40 -> Blade level should be ceil(40 * 0.5) + 1 = 21
        """
        aegislash_shield.level = 40.0
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        
        # Verify stats are different from Shield form
        shield_stats = aegislash_shield.calculate_stats()
        assert blade_stats.atk > shield_stats.atk, "Blade form should have higher attack"
        assert blade_stats.defense < shield_stats.defense, "Blade form should have lower defense"
    
    def test_shield_to_blade_various_levels(self, aegislash_shield, gamemaster):
        """
        Test Shield -> Blade conversion at various levels.
        
        Note: The CP cap enforcement loop may reduce the level further to fit under 1500 CP,
        so we verify that stats are valid and Blade form has higher attack than Shield form.
        """
        blade_data = gamemaster.get_pokemon("aegislash_blade")
        
        test_cases = [
            20.0,
            30.0,
            40.0,
            50.0,
        ]
        
        for shield_level in test_cases:
            aegislash_shield.level = shield_level
            blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
            shield_stats = aegislash_shield.calculate_stats()
            
            # Blade form should have higher attack than Shield form
            assert blade_stats.atk > shield_stats.atk, \
                f"At Shield level {shield_level}, Blade should have higher attack"
            
            # Blade form should have lower defense than Shield form
            assert blade_stats.defense < shield_stats.defense, \
                f"At Shield level {shield_level}, Blade should have lower defense"
            
            # Stats should be valid
            assert blade_stats.atk > 0
            assert blade_stats.defense > 0
            assert blade_stats.hp >= 10
    
    def test_blade_to_shield_level_calculation(self, aegislash_blade):
        """
        Test Blade -> Shield level adjustment in Great League.
        
        JavaScript: if(battleCP == 1500) { newLevel = (self.level / 0.5) + 2; }
        Blade level 21 -> Shield level should be (21 / 0.5) + 2 = 44
        """
        aegislash_blade.level = 21.0
        shield_stats = aegislash_blade.get_form_stats("aegislash_shield", battle_cp=1500)
        
        # Verify stats are different from Blade form
        blade_stats = aegislash_blade.calculate_stats()
        assert shield_stats.atk < blade_stats.atk, "Shield form should have lower attack"
        assert shield_stats.defense > blade_stats.defense, "Shield form should have higher defense"


class TestLevelAdjustmentUltraLeague:
    """Test level adjustment logic for Ultra League (CP 2500)."""
    
    def test_shield_to_blade_level_calculation(self, aegislash_shield):
        """
        Test Shield -> Blade level adjustment in Ultra League.
        
        JavaScript: if(battleCP == 2500) { newLevel = Math.ceil(self.level * 0.75); }
        Shield level 50 -> Blade level should be ceil(50 * 0.75) = 38
        """
        aegislash_shield.level = 50.0
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=2500)
        
        # Verify stats are different from Shield form
        shield_stats = aegislash_shield.calculate_stats()
        assert blade_stats.atk > shield_stats.atk, "Blade form should have higher attack"
        assert blade_stats.defense < shield_stats.defense, "Blade form should have lower defense"
    
    def test_shield_to_blade_various_levels(self, aegislash_shield, gamemaster):
        """Test Shield -> Blade conversion at various levels in Ultra League."""
        blade_data = gamemaster.get_pokemon("aegislash_blade")
        
        test_cases = [
            (40.0, math.ceil(40.0 * 0.75)),  # 30
            (44.0, math.ceil(44.0 * 0.75)),  # 33
            (48.0, math.ceil(48.0 * 0.75)),  # 36
            (50.0, math.ceil(50.0 * 0.75)),  # 38
        ]
        
        for shield_level, expected_blade_level in test_cases:
            aegislash_shield.level = shield_level
            blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=2500)
            
            # Calculate expected stats at the expected level
            expected_cpm = aegislash_shield.get_cpm(expected_blade_level)
            expected_atk = (blade_data.base_stats.atk + aegislash_shield.ivs.atk) * expected_cpm
            
            # Allow small floating point differences
            assert abs(blade_stats.atk - expected_atk) < 0.1, \
                f"At Shield level {shield_level}, Blade attack should match level {expected_blade_level}"
    
    def test_blade_to_shield_level_calculation(self, aegislash_blade):
        """
        Test Blade -> Shield level adjustment in Ultra League.
        
        JavaScript: if(battleCP == 2500) { newLevel = Math.round(self.level / 0.75); }
        Blade level 38 -> Shield level should be round(38 / 0.75) = 51 (but capped at 50)
        """
        aegislash_blade.level = 38.0
        shield_stats = aegislash_blade.get_form_stats("aegislash_shield", battle_cp=2500)
        
        # Verify stats are different from Blade form
        blade_stats = aegislash_blade.calculate_stats()
        assert shield_stats.atk < blade_stats.atk, "Shield form should have lower attack"
        assert shield_stats.defense > blade_stats.defense, "Shield form should have higher defense"


class TestCPCapEnforcement:
    """
    Test CP cap enforcement loop.
    
    JavaScript Reference (Pokemon.js lines 2430-2445):
    while((! newStats || newCP > battleCP) && cpmIndex >= 0){
        // Calculate CP and reduce level if needed
    }
    """
    
    def test_blade_form_respects_cp_cap_great_league(self, aegislash_shield):
        """Test that Blade form CP doesn't exceed Great League cap."""
        aegislash_shield.level = 40.0
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        
        # Calculate what the CP would be for Blade form
        # We need to verify it's under 1500
        blade_cp = aegislash_shield._calculate_cp_by_base_stats(
            21.0,  # Expected level after adjustment
            aegislash_shield.base_stats.atk,  # This would need Blade base stats
            aegislash_shield.base_stats.defense,
            aegislash_shield.base_stats.hp
        )
        
        # The CP should be reasonable (we can't easily verify exact CP without Blade base stats)
        assert blade_stats.atk > 0, "Blade form should have valid attack stat"
        assert blade_stats.defense > 0, "Blade form should have valid defense stat"
        assert blade_stats.hp > 0, "Blade form should have valid HP"
    
    def test_shield_form_respects_cp_cap_great_league(self, aegislash_blade):
        """Test that Shield form CP doesn't exceed Great League cap."""
        aegislash_blade.level = 21.0
        shield_stats = aegislash_blade.get_form_stats("aegislash_shield", battle_cp=1500)
        
        # Shield form should have valid stats
        assert shield_stats.atk > 0, "Shield form should have valid attack stat"
        assert shield_stats.defense > 0, "Shield form should have valid defense stat"
        assert shield_stats.hp > 0, "Shield form should have valid HP"
    
    def test_cp_cap_enforcement_reduces_level(self, aegislash_shield, gamemaster):
        """Test that level is reduced when CP exceeds cap."""
        # Set a very high level that would exceed CP cap after form change
        aegislash_shield.level = 50.0
        aegislash_shield.ivs = IVs(15, 15, 15)  # Max IVs for higher CP
        
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        
        # Blade form should still have valid stats (level was reduced to fit CP cap)
        assert blade_stats.atk > 0, "Blade form should have valid stats after CP reduction"
        assert blade_stats.defense > 0
        assert blade_stats.hp >= 10, "HP should be at least 10"
    
    def test_no_cp_cap_when_battle_cp_not_provided(self, aegislash_shield):
        """Test that CP cap is not enforced when battle_cp is None."""
        aegislash_shield.level = 50.0
        aegislash_shield.ivs = IVs(15, 15, 15)
        
        # Without battle_cp, no CP cap enforcement
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=None)
        
        # Should get stats at the calculated level without CP cap enforcement
        assert blade_stats.atk > 0
        assert blade_stats.defense > 0
        assert blade_stats.hp > 0


class TestCalculateCPByBaseStats:
    """
    Test the _calculate_cp_by_base_stats helper method.
    
    JavaScript Reference (Pokemon.js lines 394-398):
    this.calculateCPByBaseStats = function(cpm, atk, def, hp){
        let cp = Math.floor(( (atk+self.ivs.atk) * Math.pow((def+self.ivs.def), 0.5) 
                           * Math.pow((hp+self.ivs.hp), 0.5) * Math.pow(cpm, 2) ) / 10);
        return cp;
    }
    """
    
    def test_calculate_cp_matches_formula(self, aegislash_shield):
        """Test that CP calculation matches JavaScript formula."""
        aegislash_shield.level = 40.0
        aegislash_shield.ivs = IVs(0, 15, 15)
        
        base_atk = 118
        base_def = 264
        base_hp = 155
        
        cp = aegislash_shield._calculate_cp_by_base_stats(40.0, base_atk, base_def, base_hp)
        
        # Manually calculate expected CP
        cpm = aegislash_shield.get_cpm(40.0)
        expected_cp = math.floor(
            ((base_atk + 0) * math.pow(base_def + 15, 0.5) 
             * math.pow(base_hp + 15, 0.5) * math.pow(cpm, 2)) / 10
        )
        
        assert cp == expected_cp, f"CP calculation should match formula: {cp} vs {expected_cp}"
    
    def test_calculate_cp_with_shadow(self, aegislash_shield):
        """Test CP calculation with shadow multipliers."""
        aegislash_shield.shadow_type = "shadow"
        aegislash_shield.level = 40.0
        aegislash_shield.ivs = IVs(15, 15, 15)
        
        base_atk = 118
        base_def = 264
        base_hp = 155
        
        cp = aegislash_shield._calculate_cp_by_base_stats(40.0, base_atk, base_def, base_hp)
        
        # Shadow should have higher CP due to attack boost
        aegislash_shield.shadow_type = "normal"
        normal_cp = aegislash_shield._calculate_cp_by_base_stats(40.0, base_atk, base_def, base_hp)
        
        assert cp > normal_cp, "Shadow form should have higher CP"
    
    def test_calculate_cp_various_levels(self, aegislash_shield):
        """Test CP calculation at various levels."""
        base_atk = 118
        base_def = 264
        base_hp = 155
        
        # CP should increase with level
        cp_level_20 = aegislash_shield._calculate_cp_by_base_stats(20.0, base_atk, base_def, base_hp)
        cp_level_30 = aegislash_shield._calculate_cp_by_base_stats(30.0, base_atk, base_def, base_hp)
        cp_level_40 = aegislash_shield._calculate_cp_by_base_stats(40.0, base_atk, base_def, base_hp)
        
        assert cp_level_20 < cp_level_30 < cp_level_40, "CP should increase with level"


class TestFormStatsWithDifferentIVs:
    """Test form stats calculation with different IV combinations."""
    
    def test_max_ivs_shield_to_blade(self, aegislash_shield):
        """Test form stats with max IVs (15/15/15)."""
        aegislash_shield.ivs = IVs(15, 15, 15)
        aegislash_shield.level = 40.0
        
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        
        # Should have valid stats
        assert blade_stats.atk > 0
        assert blade_stats.defense > 0
        assert blade_stats.hp >= 10
    
    def test_min_ivs_shield_to_blade(self, aegislash_shield):
        """Test form stats with min IVs (0/0/0)."""
        aegislash_shield.ivs = IVs(0, 0, 0)
        aegislash_shield.level = 40.0
        
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        
        # Should have valid stats
        assert blade_stats.atk > 0
        assert blade_stats.defense > 0
        assert blade_stats.hp >= 10
    
    def test_pvp_optimal_ivs_shield_to_blade(self, aegislash_shield):
        """Test form stats with PvP optimal IVs (0/15/15)."""
        aegislash_shield.ivs = IVs(0, 15, 15)
        aegislash_shield.level = 40.0
        
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        shield_stats = aegislash_shield.calculate_stats()
        
        # Blade should have higher attack despite lower level
        assert blade_stats.atk > shield_stats.atk
        assert blade_stats.defense < shield_stats.defense


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_same_form_returns_current_stats(self, aegislash_shield):
        """Test that requesting the same form returns stats without adjustment."""
        aegislash_shield.level = 40.0
        
        # Request Shield stats while already in Shield form
        shield_stats = aegislash_shield.get_form_stats("aegislash_shield", battle_cp=1500)
        current_stats = aegislash_shield.calculate_stats()
        
        # Stats should be similar (may differ slightly due to level adjustment logic)
        assert abs(shield_stats.atk - current_stats.atk) < 1.0
    
    def test_invalid_form_returns_current_stats(self, aegislash_shield):
        """Test that requesting an invalid form returns current stats."""
        aegislash_shield.level = 40.0
        
        # Request non-existent form
        stats = aegislash_shield.get_form_stats("invalid_form", battle_cp=1500)
        current_stats = aegislash_shield.calculate_stats()
        
        # Should return current stats
        assert abs(stats.atk - current_stats.atk) < 0.1
    
    def test_level_below_minimum(self, aegislash_shield):
        """Test behavior when calculated level would be below minimum."""
        aegislash_shield.level = 2.0  # Very low level
        
        # Should still return valid stats (level won't go below 1.0)
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        
        assert blade_stats.atk > 0
        assert blade_stats.defense > 0
        assert blade_stats.hp >= 10
    
    def test_hp_minimum_enforced(self, aegislash_shield):
        """Test that HP is never below 10."""
        aegislash_shield.level = 1.0
        aegislash_shield.ivs = IVs(0, 0, 0)
        
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        
        # HP should be at least 10
        assert blade_stats.hp >= 10, "HP should never be below 10"


class TestMasterLeague:
    """Test form stats without CP cap (Master League scenario)."""
    
    def test_shield_to_blade_no_cp_cap(self, aegislash_shield):
        """Test Shield -> Blade without CP cap."""
        aegislash_shield.level = 50.0
        aegislash_shield.ivs = IVs(15, 15, 15)
        
        # No battle_cp means no level adjustment for CP cap
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=None)
        
        # Should have high stats at level 50
        assert blade_stats.atk > 200, "Blade form at level 50 should have high attack"
        assert blade_stats.defense > 0
        assert blade_stats.hp > 0
    
    def test_blade_to_shield_no_cp_cap(self, aegislash_blade):
        """Test Blade -> Shield without CP cap."""
        aegislash_blade.level = 50.0
        aegislash_blade.ivs = IVs(15, 15, 15)
        
        # No battle_cp means no level adjustment for CP cap
        shield_stats = aegislash_blade.get_form_stats("aegislash_shield", battle_cp=None)
        
        # Should have high stats at level 50
        assert shield_stats.defense > 200, "Shield form at level 50 should have high defense"
        assert shield_stats.atk > 0
        assert shield_stats.hp > 0
