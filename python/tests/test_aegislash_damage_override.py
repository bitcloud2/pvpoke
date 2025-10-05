"""
Test Aegislash damage calculation overrides.

Tests the special damage calculation rules for Aegislash Shield form:
1. Fast moves always deal 1 damage
2. Charged moves use Blade form's attack stat

JavaScript Reference:
- DamageCalculator.js lines 41-48: Charged move attack stat override
- DamageCalculator.js lines 53-60, 76-83: Fast move damage override
- Battle.js lines 1307-1309: Fast move damage override in battle execution
"""

import pytest
from pvpoke.core.pokemon import Pokemon, Stats, IVs
from pvpoke.core.moves import FastMove, ChargedMove
from pvpoke.core.gamemaster import GameMaster
from pvpoke.battle.damage_calculator import DamageCalculator


@pytest.fixture
def gamemaster():
    """Load GameMaster data."""
    try:
        gm = GameMaster()
        return gm
    except FileNotFoundError:
        # If gamemaster not found, return None and tests will create manual Pokemon
        return None


@pytest.fixture
def aegislash_shield(gamemaster):
    """Create Aegislash Shield form for testing."""
    # Try to load from gamemaster first
    if gamemaster:
        aegislash = gamemaster.get_pokemon("aegislash_shield")
        if aegislash:
            aegislash.level = 40.0
            aegislash.ivs = IVs(atk=0, defense=15, hp=15)
            aegislash.active_form_id = "aegislash_shield"
            return aegislash
    
    # Create manually if not in gamemaster
    aegislash = Pokemon(
        species_id="aegislash_shield",
        species_name="Aegislash (Shield)",
        dex=681,
        base_stats=Stats(atk=97, defense=229, hp=155),
        types=["steel", "ghost"],
        fast_moves=["AEGISLASH_CHARGE_PSYCHO_CUT", "AEGISLASH_CHARGE_AIR_SLASH"],
        charged_moves=["FLASH_CANNON", "SHADOW_BALL", "GYRO_BALL"]
    )
    
    # Set up for Great League
    aegislash.level = 40.0
    aegislash.ivs = IVs(atk=0, defense=15, hp=15)
    aegislash.active_form_id = "aegislash_shield"
    
    return aegislash


@pytest.fixture
def aegislash_blade(gamemaster):
    """Create Aegislash Blade form for testing."""
    # Try to load from gamemaster first
    if gamemaster:
        blade = gamemaster.get_pokemon("aegislash_blade")
        if blade:
            blade.level = 20.0
            blade.ivs = IVs(atk=0, defense=15, hp=15)
            blade.active_form_id = "aegislash_blade"
            return blade
    
    # Create manually if not in gamemaster
    blade = Pokemon(
        species_id="aegislash_blade",
        species_name="Aegislash (Blade)",
        dex=681,
        base_stats=Stats(atk=229, defense=97, hp=155),
        types=["steel", "ghost"],
        fast_moves=["PSYCHO_CUT", "AIR_SLASH"],
        charged_moves=["FLASH_CANNON", "SHADOW_BALL", "GYRO_BALL"]
    )
    
    blade.level = 20.0  # Blade form has lower level in Great League
    blade.ivs = IVs(atk=0, defense=15, hp=15)
    blade.active_form_id = "aegislash_blade"
    
    return blade


@pytest.fixture
def opponent(gamemaster):
    """Create a standard opponent Pokemon."""
    # Try to load from gamemaster first
    if gamemaster:
        azumarill = gamemaster.get_pokemon("azumarill")
        if azumarill:
            azumarill.level = 40.0
            azumarill.ivs = IVs(atk=0, defense=15, hp=15)
            return azumarill
    
    # Create manually if not in gamemaster
    azumarill = Pokemon(
        species_id="azumarill",
        species_name="Azumarill",
        dex=184,
        base_stats=Stats(atk=112, defense=152, hp=225),
        types=["water", "fairy"]
    )
    
    azumarill.level = 40.0
    azumarill.ivs = IVs(atk=0, defense=15, hp=15)
    
    return azumarill


@pytest.fixture
def psycho_cut():
    """Create Psycho Cut fast move."""
    return FastMove(
        move_id="AEGISLASH_CHARGE_PSYCHO_CUT",
        name="Psycho Cut (Charge)",
        move_type="psychic",
        power=3,
        energy_gain=6,
        turns=1
    )


@pytest.fixture
def shadow_ball():
    """Create Shadow Ball charged move."""
    return ChargedMove(
        move_id="SHADOW_BALL",
        name="Shadow Ball",
        move_type="ghost",
        power=100,
        energy_cost=55
    )


class TestAegislashShieldFormFastMoveDamage:
    """Test that Aegislash Shield form fast moves always deal 1 damage."""
    
    def test_fast_move_deals_1_damage(self, aegislash_shield, opponent, psycho_cut):
        """Shield form fast moves should always deal 1 damage regardless of stats."""
        # Calculate damage
        damage = DamageCalculator.calculate_damage(
            aegislash_shield, 
            opponent, 
            psycho_cut
        )
        
        # Should always be 1 damage
        assert damage == 1, "Shield form fast moves should deal 1 damage"
    
    def test_fast_move_with_attack_buffs(self, aegislash_shield, opponent, psycho_cut):
        """Shield form fast moves should deal 1 damage even with attack buffs."""
        # Apply +4 attack buff
        aegislash_shield.stat_buffs = [4, 0]
        
        damage = DamageCalculator.calculate_damage(
            aegislash_shield,
            opponent,
            psycho_cut
        )
        
        assert damage == 1, "Shield form fast moves should deal 1 damage even with buffs"
    
    def test_fast_move_against_weak_defense(self, aegislash_shield, psycho_cut):
        """Shield form fast moves should deal 1 damage even against weak defense."""
        # Create a Pokemon with very low defense
        weak_defender = Pokemon(
            species_id="shuckle",
            species_name="Shuckle",
            dex=213,
            base_stats=Stats(atk=17, defense=396, hp=244),
            types=["bug", "rock"]
        )
        weak_defender.level = 10.0
        weak_defender.ivs = IVs(atk=0, defense=0, hp=0)
        weak_defender.stat_buffs = [-4, 0]  # -4 defense debuff
        
        damage = DamageCalculator.calculate_damage(
            aegislash_shield,
            weak_defender,
            psycho_cut
        )
        
        assert damage == 1, "Shield form fast moves should always deal 1 damage"


class TestAegislashShieldFormChargedMoveDamage:
    """Test that Aegislash Shield form charged moves use Blade form attack stat."""
    
    def test_charged_move_uses_blade_attack_great_league(self, aegislash_shield, opponent, shadow_ball):
        """Shield form charged moves should use Blade form attack stat in Great League."""
        # Calculate damage with battle_cp parameter
        damage = DamageCalculator.calculate_damage(
            aegislash_shield,
            opponent,
            shadow_ball,
            battle_cp=1500
        )
        
        # Get Blade form stats to verify
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        
        # Damage should be > 1 (not the 1 damage from fast moves)
        assert damage > 1, "Shield form charged moves should deal normal damage"
        
        # Verify it's using higher attack stat (Blade form has much higher attack)
        shield_stats = aegislash_shield.calculate_stats()
        assert blade_stats.atk > shield_stats.atk, "Blade form should have higher attack"
    
    def test_charged_move_uses_blade_attack_ultra_league(self, aegislash_shield, opponent, shadow_ball):
        """Shield form charged moves should use Blade form attack stat in Ultra League."""
        # Set up for Ultra League
        aegislash_shield.level = 50.0
        
        damage = DamageCalculator.calculate_damage(
            aegislash_shield,
            opponent,
            shadow_ball,
            battle_cp=2500
        )
        
        # Should deal significant damage using Blade form attack
        assert damage > 1, "Shield form charged moves should deal normal damage"
    
    def test_charged_move_with_buffs(self, aegislash_shield, opponent, shadow_ball):
        """Shield form charged moves should apply buffs to Blade form attack stat."""
        # Apply +2 attack buff
        aegislash_shield.stat_buffs = [2, 0]
        
        # Calculate damage without buffs
        aegislash_shield.stat_buffs = [0, 0]
        damage_no_buff = DamageCalculator.calculate_damage(
            aegislash_shield,
            opponent,
            shadow_ball,
            battle_cp=1500
        )
        
        # Calculate damage with buffs
        aegislash_shield.stat_buffs = [2, 0]
        damage_with_buff = DamageCalculator.calculate_damage(
            aegislash_shield,
            opponent,
            shadow_ball,
            battle_cp=1500
        )
        
        # Buffed damage should be higher
        assert damage_with_buff > damage_no_buff, "Buffs should increase damage"


class TestAegislashBladeFormDamage:
    """Test that Aegislash Blade form uses normal damage calculations."""
    
    def test_blade_fast_move_normal_damage(self, aegislash_blade, opponent):
        """Blade form fast moves should deal normal damage (not 1)."""
        # Create normal Psycho Cut (not the charge version)
        psycho_cut = FastMove(
            move_id="PSYCHO_CUT",
            name="Psycho Cut",
            move_type="psychic",
            power=3,
            energy_gain=9,
            turns=1
        )
        
        damage = DamageCalculator.calculate_damage(
            aegislash_blade,
            opponent,
            psycho_cut
        )
        
        # Should deal normal damage (> 1) because Blade form has high attack
        assert damage > 1, "Blade form fast moves should deal normal damage"
    
    def test_blade_charged_move_normal_damage(self, aegislash_blade, opponent, shadow_ball):
        """Blade form charged moves should use normal attack stat."""
        damage = DamageCalculator.calculate_damage(
            aegislash_blade,
            opponent,
            shadow_ball
        )
        
        # Should deal significant damage with Blade form's high attack
        assert damage > 1, "Blade form charged moves should deal normal damage"


class TestGetFormStats:
    """Test the get_form_stats method for Aegislash."""
    
    def test_shield_to_blade_great_league(self, aegislash_shield):
        """Test Shield -> Blade form stats calculation in Great League."""
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        shield_stats = aegislash_shield.calculate_stats()
        
        # Blade form should have higher attack, lower defense
        assert blade_stats.atk > shield_stats.atk, "Blade form should have higher attack"
        assert blade_stats.defense < shield_stats.defense, "Blade form should have lower defense"
    
    def test_shield_to_blade_ultra_league(self, aegislash_shield):
        """Test Shield -> Blade form stats calculation in Ultra League."""
        aegislash_shield.level = 50.0
        
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=2500)
        shield_stats = aegislash_shield.calculate_stats()
        
        # Blade form should have higher attack, lower defense
        assert blade_stats.atk > shield_stats.atk, "Blade form should have higher attack"
        assert blade_stats.defense < shield_stats.defense, "Blade form should have lower defense"
    
    def test_blade_to_shield_great_league(self, aegislash_blade):
        """Test Blade -> Shield form stats calculation in Great League."""
        shield_stats = aegislash_blade.get_form_stats("aegislash_shield", battle_cp=1500)
        blade_stats = aegislash_blade.calculate_stats()
        
        # Shield form should have lower attack, higher defense
        assert shield_stats.atk < blade_stats.atk, "Shield form should have lower attack"
        assert shield_stats.defense > blade_stats.defense, "Shield form should have higher defense"
    
    def test_level_adjustment_great_league(self, aegislash_shield):
        """Test that level is adjusted correctly for Great League."""
        # Shield level 40 -> Blade level should be ceil(40 * 0.5) + 1 = 21
        aegislash_shield.level = 40.0
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=1500)
        
        # Verify stats are calculated with adjusted level
        # The exact level calculation is internal, but we can verify stats are different
        shield_stats = aegislash_shield.calculate_stats()
        assert blade_stats.atk != shield_stats.atk
    
    def test_level_adjustment_ultra_league(self, aegislash_shield):
        """Test that level is adjusted correctly for Ultra League."""
        # Shield level 50 -> Blade level should be ceil(50 * 0.75) = 38
        aegislash_shield.level = 50.0
        blade_stats = aegislash_shield.get_form_stats("aegislash_blade", battle_cp=2500)
        
        shield_stats = aegislash_shield.calculate_stats()
        assert blade_stats.atk != shield_stats.atk


class TestDamageFromStatsWithAegislash:
    """Test calculate_damage_from_stats with Aegislash overrides."""
    
    def test_shield_fast_move_from_stats(self, aegislash_shield, opponent, psycho_cut):
        """Test that damage_from_stats respects Shield form fast move override."""
        shield_stats = aegislash_shield.calculate_stats()
        opponent_stats = opponent.calculate_stats()
        
        damage = DamageCalculator.calculate_damage_from_stats(
            attack=shield_stats.atk,
            defense=opponent_stats.defense,
            power=psycho_cut.power,
            effectiveness=1.0,
            stab=1.0,
            attacker=aegislash_shield,
            move=psycho_cut
        )
        
        assert damage == 1, "Shield form fast moves should deal 1 damage in damage_from_stats"
    
    def test_shield_charged_move_from_stats(self, aegislash_shield, opponent, shadow_ball):
        """Test that damage_from_stats uses Blade form attack for Shield form charged moves."""
        shield_stats = aegislash_shield.calculate_stats()
        opponent_stats = opponent.calculate_stats()
        
        # Without attacker/move parameters, should use provided attack stat
        damage_normal = DamageCalculator.calculate_damage_from_stats(
            attack=shield_stats.atk,
            defense=opponent_stats.defense,
            power=shadow_ball.power,
            effectiveness=1.0,
            stab=1.2
        )
        
        # With attacker/move parameters, should use Blade form attack
        damage_override = DamageCalculator.calculate_damage_from_stats(
            attack=shield_stats.atk,
            defense=opponent_stats.defense,
            power=shadow_ball.power,
            effectiveness=1.0,
            stab=1.2,
            attacker=aegislash_shield,
            move=shadow_ball,
            battle_cp=1500
        )
        
        # Override should use higher attack stat (Blade form)
        assert damage_override > damage_normal, "Shield form charged moves should use Blade attack"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
