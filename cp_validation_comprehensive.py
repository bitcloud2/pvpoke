#!/usr/bin/env python3
"""
Comprehensive CP calculation validation between Python and JavaScript implementations.

This script tests CP calculations across various IV combinations, levels, and Pokemon
to ensure the Python implementation matches the JavaScript reference exactly.

Key differences found:
- Python uses: cp = floor(0.1 * atk * sqrt(def) * sqrt(hp))
- JavaScript uses: cp = floor((atk * sqrt(def) * sqrt(hp) * cpm^2) / 10)

Both should be mathematically equivalent, but we need to verify this across all scenarios.

Usage:
    pixi shell
    python cp_validation_comprehensive.py
"""

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

# Add python directory to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from pvpoke.core import GameMaster, Pokemon, Stats, IVs
from pvpoke.utils.cp_calculator import CPCalculator


@dataclass
class CPTestCase:
    """Test case for CP calculation validation."""
    pokemon_id: str
    base_stats: Stats
    ivs: IVs
    level: float
    shadow_type: str = "normal"
    expected_cp: int = None  # Will be calculated by JS reference
    description: str = ""


class CPValidationResult:
    """Results from CP calculation validation."""
    
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = []
        self.tolerance = 1  # Allow 1 CP difference due to rounding
    
    def add_test(self, test_case: CPTestCase, python_cp: int, js_reference_cp: int):
        """Add a test result."""
        self.total_tests += 1
        
        diff = abs(python_cp - js_reference_cp)
        
        if diff <= self.tolerance:
            self.passed_tests += 1
        else:
            self.failed_tests.append({
                'test_case': test_case,
                'python_cp': python_cp,
                'js_reference_cp': js_reference_cp,
                'difference': diff
            })
    
    def print_summary(self):
        """Print validation summary."""
        print(f"\n{'='*80}")
        print(f"CP CALCULATION VALIDATION SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%")
        print(f"Tolerance: ±{self.tolerance} CP")
        
        if self.failed_tests:
            print(f"\n{'='*80}")
            print(f"FAILED TESTS (showing first 10)")
            print(f"{'='*80}")
            
            for i, failed in enumerate(self.failed_tests[:10]):
                tc = failed['test_case']
                print(f"\n❌ Test {i+1}: {tc.description}")
                print(f"   Pokemon: {tc.pokemon_id}")
                print(f"   IVs: {tc.ivs.atk}/{tc.ivs.defense}/{tc.ivs.hp}")
                print(f"   Level: {tc.level}")
                print(f"   Shadow: {tc.shadow_type}")
                print(f"   Python CP: {failed['python_cp']}")
                print(f"   JS Reference CP: {failed['js_reference_cp']}")
                print(f"   Difference: {failed['difference']}")
            
            if len(self.failed_tests) > 10:
                print(f"\n... and {len(self.failed_tests) - 10} more failures")
        
        if self.passed_tests == self.total_tests:
            print(f"\n🎉 ALL TESTS PASSED! CP calculations are consistent!")
        else:
            print(f"\n⚠️  {len(self.failed_tests)} differences found. Review implementation.")


class JSReferenceCalculator:
    """JavaScript reference implementation for CP calculation."""
    
    # CPM values from JavaScript (levels 1-50 in 0.5 increments)
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
        """Get CP multiplier for a level (JavaScript implementation)."""
        # Levels are in 0.5 increments, so index = (level - 1) * 2
        index = int((level - 1) * 2)
        if 0 <= index < len(JSReferenceCalculator.CPM_VALUES):
            return JSReferenceCalculator.CPM_VALUES[index]
        return 0
    
    @staticmethod
    def calculate_cp(base_stats: Stats, ivs: IVs, level: float, shadow_type: str = "normal") -> int:
        """Calculate CP using JavaScript reference implementation."""
        cpm = JSReferenceCalculator.get_cpm(level)
        
        # Shadow bonuses/penalties (same as Python)
        shadow_atk_mult = 1.2 if shadow_type == "shadow" else 1.0
        shadow_def_mult = 0.833333 if shadow_type == "shadow" else 1.0
        
        # JavaScript formula: cp = floor((atk * sqrt(def) * sqrt(hp) * cpm^2) / 10)
        atk = (base_stats.atk + ivs.atk) * shadow_atk_mult
        defense = (base_stats.defense + ivs.defense) * shadow_def_mult
        hp = (base_stats.hp + ivs.hp)
        
        cp = math.floor((atk * math.sqrt(defense) * math.sqrt(hp) * (cpm ** 2)) / 10)
        return max(10, cp)


class CPValidator:
    """Validates CP calculations between Python and JavaScript implementations."""
    
    def __init__(self):
        self.gm = GameMaster()
        self.result = CPValidationResult()
    
    def generate_test_cases(self) -> List[CPTestCase]:
        """Generate comprehensive test cases for CP validation."""
        test_cases = []
        
        # Common Pokemon with different stat distributions
        pokemon_configs = [
            # High attack Pokemon
            ("mewtwo", Stats(atk=300, defense=182, hp=214)),
            ("machamp", Stats(atk=234, defense=159, hp=207)),
            ("dragonite", Stats(atk=263, defense=198, hp=209)),
            
            # Balanced Pokemon
            ("azumarill", Stats(atk=112, defense=152, hp=225)),
            ("medicham", Stats(atk=121, defense=152, hp=155)),
            ("altaria", Stats(atk=141, defense=201, hp=181)),
            
            # High defense Pokemon
            ("registeel", Stats(atk=143, defense=285, hp=190)),
            ("shuckle", Stats(atk=17, defense=396, hp=85)),
            ("bastiodon", Stats(atk=94, defense=286, hp=155)),
            
            # High HP Pokemon
            ("chansey", Stats(atk=60, defense=128, hp=487)),
            ("blissey", Stats(atk=129, defense=169, hp=496)),
            ("wobbuffet", Stats(atk=60, defense=106, hp=382)),
        ]
        
        # IV combinations to test
        iv_combinations = [
            # Perfect IVs
            IVs(15, 15, 15),
            # Zero IVs
            IVs(0, 0, 0),
            # PvP optimal (low attack)
            IVs(0, 15, 15),
            # High attack
            IVs(15, 0, 0),
            # Random combinations
            IVs(7, 13, 11),
            IVs(12, 8, 14),
            IVs(3, 9, 6),
            IVs(14, 2, 10),
            # Edge cases
            IVs(1, 1, 1),
            IVs(14, 14, 14),
        ]
        
        # Levels to test
        levels = [
            1.0, 1.5, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0,
            # Half levels
            2.5, 7.5, 12.5, 17.5, 22.5, 27.5, 32.5, 37.5, 42.5, 47.5,
            # Edge levels
            49.5, 50.0
        ]
        
        # Shadow types
        shadow_types = ["normal", "shadow"]
        
        # Generate all combinations
        test_id = 0
        for pokemon_id, base_stats in pokemon_configs:
            for ivs in iv_combinations:
                for level in levels:
                    for shadow_type in shadow_types:
                        test_id += 1
                        test_cases.append(CPTestCase(
                            pokemon_id=pokemon_id,
                            base_stats=base_stats,
                            ivs=ivs,
                            level=level,
                            shadow_type=shadow_type,
                            description=f"Test {test_id}: {pokemon_id} {ivs.atk}/{ivs.defense}/{ivs.hp} L{level} {shadow_type}"
                        ))
        
        return test_cases
    
    def validate_cp_calculations(self):
        """Run comprehensive CP calculation validation."""
        print("CP Calculation Validation")
        print("Comparing Python vs JavaScript reference implementations")
        print("=" * 80)
        
        test_cases = self.generate_test_cases()
        print(f"Generated {len(test_cases)} test cases")
        print("Testing across:")
        print("- 12 different Pokemon species")
        print("- 10 IV combinations")
        print("- 24 different levels")
        print("- Normal and Shadow variants")
        print()
        
        # Test a sample first to show progress
        sample_size = min(100, len(test_cases))
        print(f"Running sample of {sample_size} tests first...")
        
        for i, test_case in enumerate(test_cases[:sample_size]):
            if i % 20 == 0:
                print(f"Progress: {i}/{sample_size} tests completed")
            
            # Calculate CP using Python implementation
            python_cp = CPCalculator.calculate_cp(
                test_case.base_stats,
                test_case.ivs,
                test_case.level,
                test_case.shadow_type
            )
            
            # Calculate CP using JavaScript reference
            js_cp = JSReferenceCalculator.calculate_cp(
                test_case.base_stats,
                test_case.ivs,
                test_case.level,
                test_case.shadow_type
            )
            
            # Add to results
            self.result.add_test(test_case, python_cp, js_cp)
        
        print(f"\nCompleted {sample_size} tests")
        
        # If sample passes, run full suite
        if self.result.passed_tests == sample_size:
            print("✅ Sample tests passed! Running full test suite...")
            
            # Reset for full run
            self.result = CPValidationResult()
            
            for i, test_case in enumerate(test_cases):
                if i % 500 == 0:
                    print(f"Progress: {i}/{len(test_cases)} tests completed")
                
                # Calculate CP using Python implementation
                python_cp = CPCalculator.calculate_cp(
                    test_case.base_stats,
                    test_case.ivs,
                    test_case.level,
                    test_case.shadow_type
                )
                
                # Calculate CP using JavaScript reference
                js_cp = JSReferenceCalculator.calculate_cp(
                    test_case.base_stats,
                    test_case.ivs,
                    test_case.level,
                    test_case.shadow_type
                )
                
                # Add to results
                self.result.add_test(test_case, python_cp, js_cp)
        
        # Print results
        self.result.print_summary()
        
        return self.result.passed_tests == self.result.total_tests
    
    def test_specific_cases(self):
        """Test specific edge cases and known problematic scenarios."""
        print("\nTesting specific edge cases...")
        print("-" * 50)
        
        edge_cases = [
            # Very low level Pokemon
            CPTestCase("shuckle", Stats(17, 396, 85), IVs(0, 0, 0), 1.0, "normal", 
                      description="Shuckle L1 0/0/0 - minimum CP test"),
            
            # Very high level Pokemon
            CPTestCase("mewtwo", Stats(300, 182, 214), IVs(15, 15, 15), 50.0, "normal",
                      description="Mewtwo L50 15/15/15 - maximum CP test"),
            
            # Shadow Pokemon edge case
            CPTestCase("mewtwo", Stats(300, 182, 214), IVs(15, 15, 15), 40.0, "shadow",
                      description="Shadow Mewtwo L40 15/15/15 - shadow multiplier test"),
            
            # Very low attack Pokemon
            CPTestCase("shuckle", Stats(17, 396, 85), IVs(15, 15, 15), 40.0, "normal",
                      description="Shuckle L40 15/15/15 - extreme defense test"),
            
            # Very high HP Pokemon
            CPTestCase("chansey", Stats(60, 128, 487), IVs(0, 15, 15), 40.0, "normal",
                      description="Chansey L40 0/15/15 - extreme HP test"),
        ]
        
        for test_case in edge_cases:
            print(f"\nTesting: {test_case.description}")
            
            # Calculate using both methods
            python_cp = CPCalculator.calculate_cp(
                test_case.base_stats,
                test_case.ivs,
                test_case.level,
                test_case.shadow_type
            )
            
            js_cp = JSReferenceCalculator.calculate_cp(
                test_case.base_stats,
                test_case.ivs,
                test_case.level,
                test_case.shadow_type
            )
            
            print(f"  Python CP: {python_cp}")
            print(f"  JS Reference CP: {js_cp}")
            print(f"  Difference: {abs(python_cp - js_cp)}")
            
            if abs(python_cp - js_cp) <= 1:
                print("  ✅ PASS")
            else:
                print("  ❌ FAIL - Significant difference!")
    
    def compare_cpm_values(self):
        """Compare CPM values between Python and JavaScript implementations."""
        print("\nComparing CPM (CP Multiplier) values...")
        print("-" * 50)
        
        differences = []
        
        for level in [1.0, 1.5, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0]:
            python_cpm = CPCalculator.get_cpm(level)
            js_cpm = JSReferenceCalculator.get_cpm(level)
            
            diff = abs(python_cpm - js_cpm)
            if diff > 1e-10:  # Allow for floating point precision
                differences.append((level, python_cpm, js_cpm, diff))
        
        if differences:
            print("❌ CPM value differences found:")
            for level, py_cpm, js_cpm, diff in differences:
                print(f"  Level {level}: Python={py_cpm:.12f}, JS={js_cpm:.12f}, diff={diff:.2e}")
        else:
            print("✅ All CPM values match between implementations")
        
        return len(differences) == 0


def main():
    """Main validation function."""
    print("Comprehensive CP Calculation Validation")
    print("Comparing Python implementation against JavaScript reference")
    print("=" * 80)
    
    try:
        validator = CPValidator()
        
        # First, compare CPM values
        cpm_match = validator.compare_cpm_values()
        
        # Test specific edge cases
        validator.test_specific_cases()
        
        # Run comprehensive validation
        if cpm_match:
            success = validator.validate_cp_calculations()
        else:
            print("\n❌ CPM values don't match - skipping full validation")
            success = False
        
        if success:
            print("\n🎉 VALIDATION SUCCESSFUL!")
            print("✅ CP calculations are consistent between Python and JavaScript")
            print("✅ All test cases passed within tolerance")
            print("\nThe Python implementation can be trusted for CP calculations.")
            return 0
        else:
            print("\n⚠️  VALIDATION ISSUES FOUND")
            print("❌ Some CP calculations differ between implementations")
            print("Review the failed tests above to identify the root cause.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
