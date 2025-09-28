#!/usr/bin/env python3
"""
CP Calculation Validation Test

This script validates CP calculations between Python and JavaScript implementations
by testing various IV combinations, levels, and Pokemon to ensure consistency.

Key findings from analysis:
- Python: cp = floor(0.1 * atk * sqrt(def) * sqrt(hp))
- JavaScript: cp = floor((atk * sqrt(def) * sqrt(hp) * cpm^2) / 10)

These should be mathematically equivalent since:
- Python: atk = (base_atk + iv_atk) * cpm * shadow_mult
- JavaScript: atk = (base_atk + iv_atk) * shadow_mult, then multiply by cpm^2 in formula

Usage:
    pixi shell
    python test_cp_validation.py
"""

import math
import sys
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

# Add python directory to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from pvpoke.core import Stats, IVs
from pvpoke.utils.cp_calculator import CPCalculator


@dataclass
class CPTestResult:
    """Result of a CP calculation test."""
    pokemon_name: str
    base_stats: Stats
    ivs: IVs
    level: float
    shadow_type: str
    python_cp: int
    js_reference_cp: int
    difference: int
    passed: bool


class JSReferenceCalculator:
    """JavaScript reference implementation for CP calculation."""
    
    # CPM values from JavaScript implementation (levels 1-50 in 0.5 increments)
    CPM_VALUES = [
        0.0939999967813491, 0.135137430784308, 0.166397869586944, 0.192650914456886,
        0.215732470154762, 0.236572655026622, 0.255720049142837, 0.273530381100769,
        0.290249884128570, 0.306057381335773, 0.321087598800659, 0.335445032295077,
        0.349212676286697, 0.362457748778790, 0.375235587358474, 0.387592411085168,
        0.399567276239395, 0.411193549517250, 0.422500014305114, 0.432926413410414,
        0.443107545375824, 0.453059953871985, 0.462798386812210, 0.472336077786704,
        0.481684952974319, 0.490855810259008, 0.499858438968658, 0.508701756943992,
        0.517393946647644, 0.525942508771329, 0.534354329109191, 0.542635762230353,
        0.550792694091796, 0.558830599438087, 0.566754519939422, 0.574569148039264,
        0.582278907299041, 0.589887911977272, 0.597400009632110, 0.604823657502073,
        0.612157285213470, 0.619404110566050, 0.626567125320434, 0.633649181622743,
        0.640652954578399, 0.647580963301656, 0.654435634613037, 0.661219263506722,
        0.667934000492096, 0.674581899290818, 0.681164920330047, 0.687684905887771,
        0.694143652915954, 0.700542893277978, 0.706884205341339, 0.713169102333341,
        0.719399094581604, 0.725575616972598, 0.731700003147125, 0.734741011137376,
        0.737769484519958, 0.740785574597326, 0.743789434432983, 0.746781208702482,
        0.749761044979095, 0.752729105305821, 0.755685508251190, 0.758630366519684,
        0.761563837528228, 0.764486065255226, 0.767397165298461, 0.770297273971590,
        0.773186504840850, 0.776064945942412, 0.778932750225067, 0.781790064808426,
        0.784636974334716, 0.787473583646825, 0.790300011634826, 0.792803950958807,
        0.795300006866455, 0.797803921486970, 0.800300002098083, 0.802803892322847,
        0.805299997329711, 0.807803863460723, 0.810299992561340, 0.812803834895026,
        0.815299987792968, 0.817803806620319, 0.820299983024597, 0.822803778631297,
        0.825299978256225, 0.827803750922782, 0.830299973487854, 0.832803753381377,
        0.835300028324127, 0.837803755931569, 0.840300023555755, 0.842803729034748,
        0.845300018787384, 0.847803702398935, 0.850300014019012, 0.852803676019539,
        0.855300009250640, 0.857803649892077, 0.860300004482269, 0.862803624012168,
        0.865299999713897
    ]
    
    @staticmethod
    def get_cpm(level: float) -> float:
        """Get CP multiplier for a level."""
        index = int((level - 1) * 2)
        if 0 <= index < len(JSReferenceCalculator.CPM_VALUES):
            return JSReferenceCalculator.CPM_VALUES[index]
        return 0
    
    @staticmethod
    def calculate_cp(base_stats: Stats, ivs: IVs, level: float, shadow_type: str = "normal") -> int:
        """Calculate CP using JavaScript reference implementation."""
        cpm = JSReferenceCalculator.get_cpm(level)
        
        # Shadow bonuses/penalties
        shadow_atk_mult = 1.2 if shadow_type == "shadow" else 1.0
        shadow_def_mult = 0.833333 if shadow_type == "shadow" else 1.0
        
        # JavaScript formula: cp = floor((atk * sqrt(def) * sqrt(hp) * cpm^2) / 10)
        atk = (base_stats.atk + ivs.atk) * shadow_atk_mult
        defense = (base_stats.defense + ivs.defense) * shadow_def_mult
        hp = (base_stats.hp + ivs.hp)
        
        cp = math.floor((atk * math.sqrt(defense) * math.sqrt(hp) * (cpm ** 2)) / 10)
        return max(10, cp)


def test_cpm_consistency():
    """Test that CPM values are consistent between implementations."""
    print("Testing CPM (CP Multiplier) consistency...")
    print("-" * 60)
    
    test_levels = [1.0, 1.5, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0]
    differences = []
    
    for level in test_levels:
        python_cpm = CPCalculator.get_cpm(level)
        js_cpm = JSReferenceCalculator.get_cpm(level)
        diff = abs(python_cpm - js_cpm)
        
        print(f"Level {level:4.1f}: Python={python_cpm:.12f}, JS={js_cpm:.12f}, diff={diff:.2e}")
        
        if diff > 1e-10:  # Allow for floating point precision
            differences.append((level, diff))
    
    if differences:
        print(f"\n❌ Found {len(differences)} CPM differences!")
        return False
    else:
        print(f"\n✅ All CPM values match!")
        return True


def test_cp_calculations():
    """Test CP calculations across various scenarios."""
    print("\nTesting CP calculations...")
    print("-" * 60)
    
    # Test cases with different stat distributions
    test_cases = [
        # High attack Pokemon
        ("Mewtwo", Stats(atk=300, defense=182, hp=214)),
        ("Machamp", Stats(atk=234, defense=159, hp=207)),
        
        # Balanced Pokemon
        ("Azumarill", Stats(atk=112, defense=152, hp=225)),
        ("Medicham", Stats(atk=121, defense=152, hp=155)),
        
        # High defense Pokemon
        ("Registeel", Stats(atk=143, defense=285, hp=190)),
        ("Shuckle", Stats(atk=17, defense=396, hp=85)),
        
        # High HP Pokemon
        ("Chansey", Stats(atk=60, defense=128, hp=487)),
        ("Wobbuffet", Stats(atk=60, defense=106, hp=382)),
    ]
    
    # IV combinations to test
    iv_tests = [
        ("Perfect", IVs(15, 15, 15)),
        ("Zero", IVs(0, 0, 0)),
        ("PvP Optimal", IVs(0, 15, 15)),
        ("High Attack", IVs(15, 0, 0)),
        ("Random 1", IVs(7, 13, 11)),
        ("Random 2", IVs(12, 8, 14)),
    ]
    
    # Levels to test
    levels = [1.0, 20.0, 40.0, 50.0]
    
    # Shadow types
    shadow_types = [("Normal", "normal"), ("Shadow", "shadow")]
    
    results = []
    total_tests = 0
    passed_tests = 0
    
    print(f"Running {len(test_cases)} × {len(iv_tests)} × {len(levels)} × {len(shadow_types)} = {len(test_cases) * len(iv_tests) * len(levels) * len(shadow_types)} tests")
    print()
    
    for pokemon_name, base_stats in test_cases:
        for iv_name, ivs in iv_tests:
            for level in levels:
                for shadow_name, shadow_type in shadow_types:
                    total_tests += 1
                    
                    # Calculate CP using both methods
                    python_cp = CPCalculator.calculate_cp(base_stats, ivs, level, shadow_type)
                    js_cp = JSReferenceCalculator.calculate_cp(base_stats, ivs, level, shadow_type)
                    
                    difference = abs(python_cp - js_cp)
                    passed = difference <= 1  # Allow 1 CP difference due to rounding
                    
                    if passed:
                        passed_tests += 1
                    
                    result = CPTestResult(
                        pokemon_name=pokemon_name,
                        base_stats=base_stats,
                        ivs=ivs,
                        level=level,
                        shadow_type=shadow_type,
                        python_cp=python_cp,
                        js_reference_cp=js_cp,
                        difference=difference,
                        passed=passed
                    )
                    results.append(result)
                    
                    # Show progress for every 50 tests
                    if total_tests % 50 == 0:
                        print(f"Progress: {total_tests} tests completed, {passed_tests} passed")
    
    # Print summary
    print(f"\nTest Results Summary:")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Show failed tests
    failed_results = [r for r in results if not r.passed]
    if failed_results:
        print(f"\nFailed Tests (showing first 10):")
        print("-" * 60)
        for i, result in enumerate(failed_results[:10]):
            print(f"{i+1}. {result.pokemon_name} {result.ivs.atk}/{result.ivs.defense}/{result.ivs.hp} "
                  f"L{result.level} {result.shadow_type}")
            print(f"   Python: {result.python_cp}, JS: {result.js_reference_cp}, "
                  f"Diff: {result.difference}")
        
        if len(failed_results) > 10:
            print(f"... and {len(failed_results) - 10} more failures")
    
    return passed_tests == total_tests


def test_edge_cases():
    """Test specific edge cases that might cause issues."""
    print("\nTesting edge cases...")
    print("-" * 60)
    
    edge_cases = [
        # Minimum CP case
        ("Shuckle L1 0/0/0", Stats(17, 396, 85), IVs(0, 0, 0), 1.0, "normal"),
        
        # Maximum CP case  
        ("Mewtwo L50 15/15/15", Stats(300, 182, 214), IVs(15, 15, 15), 50.0, "normal"),
        
        # Shadow multiplier test
        ("Shadow Mewtwo L40", Stats(300, 182, 214), IVs(15, 15, 15), 40.0, "shadow"),
        
        # Extreme defense
        ("Shuckle L40 15/15/15", Stats(17, 396, 85), IVs(15, 15, 15), 40.0, "normal"),
        
        # Extreme HP
        ("Chansey L40 0/15/15", Stats(60, 128, 487), IVs(0, 15, 15), 40.0, "normal"),
        
        # Half levels
        ("Azumarill L20.5", Stats(112, 152, 225), IVs(0, 15, 15), 20.5, "normal"),
        ("Medicham L15.5", Stats(121, 152, 155), IVs(0, 15, 15), 15.5, "normal"),
    ]
    
    all_passed = True
    
    for case_name, base_stats, ivs, level, shadow_type in edge_cases:
        python_cp = CPCalculator.calculate_cp(base_stats, ivs, level, shadow_type)
        js_cp = JSReferenceCalculator.calculate_cp(base_stats, ivs, level, shadow_type)
        difference = abs(python_cp - js_cp)
        passed = difference <= 1
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{case_name:25} | Python: {python_cp:4d} | JS: {js_cp:4d} | Diff: {difference:2d} | {status}")
        
        if not passed:
            all_passed = False
    
    return all_passed


def main():
    """Run all CP validation tests."""
    print("CP Calculation Validation Test")
    print("Comparing Python implementation vs JavaScript reference")
    print("=" * 80)
    
    try:
        # Test CPM consistency first
        cpm_ok = test_cpm_consistency()
        
        if not cpm_ok:
            print("\n❌ CPM values don't match - this will cause CP calculation differences")
            print("Fix CPM values before proceeding with full validation")
            return 1
        
        # Test edge cases
        edge_cases_ok = test_edge_cases()
        
        # Test comprehensive CP calculations
        cp_calculations_ok = test_cp_calculations()
        
        # Final summary
        print("\n" + "=" * 80)
        print("FINAL VALIDATION RESULTS")
        print("=" * 80)
        
        if cpm_ok and edge_cases_ok and cp_calculations_ok:
            print("🎉 ALL TESTS PASSED!")
            print("✅ CPM values are consistent")
            print("✅ Edge cases work correctly")
            print("✅ Comprehensive CP calculations match")
            print("\nThe Python CP calculation implementation is validated!")
            return 0
        else:
            print("⚠️  VALIDATION ISSUES FOUND:")
            if not cpm_ok:
                print("❌ CPM values differ between implementations")
            if not edge_cases_ok:
                print("❌ Some edge cases failed")
            if not cp_calculations_ok:
                print("❌ Some CP calculations differ")
            print("\nReview the failed tests above to identify issues.")
            return 1
    
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
