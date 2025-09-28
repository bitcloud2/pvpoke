#!/usr/bin/env python3
"""
Debug CP calculation differences between Python and JavaScript implementations.

This script adds detailed logging to identify exactly where the calculations diverge.
"""

import math
import sys
from pathlib import Path

# Add python directory to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from pvpoke.core import Stats, IVs
from pvpoke.utils.cp_calculator import CPCalculator


class JSReferenceCalculator:
    """JavaScript reference implementation with detailed logging."""
    
    # CPM values from JavaScript implementation
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
    def calculate_cp_detailed(base_stats: Stats, ivs: IVs, level: float, shadow_type: str = "normal", debug: bool = False):
        """Calculate CP with detailed logging."""
        if debug:
            print(f"\n=== JavaScript Reference Calculation ===")
            print(f"Base stats: ATK={base_stats.atk}, DEF={base_stats.defense}, HP={base_stats.hp}")
            print(f"IVs: ATK={ivs.atk}, DEF={ivs.defense}, HP={ivs.hp}")
            print(f"Level: {level}")
            print(f"Shadow type: {shadow_type}")
        
        cpm = JSReferenceCalculator.get_cpm(level)
        if debug:
            print(f"CPM: {cpm:.12f}")
        
        # Shadow bonuses/penalties
        shadow_atk_mult = 1.2 if shadow_type == "shadow" else 1.0
        shadow_def_mult = 0.833333 if shadow_type == "shadow" else 1.0
        
        if debug:
            print(f"Shadow multipliers: ATK={shadow_atk_mult}, DEF={shadow_def_mult}")
        
        # JavaScript formula: cp = floor((atk * sqrt(def) * sqrt(hp) * cpm^2) / 10)
        base_atk = (base_stats.atk + ivs.atk) * shadow_atk_mult
        base_def = (base_stats.defense + ivs.defense) * shadow_def_mult
        base_hp = (base_stats.hp + ivs.hp)
        
        if debug:
            print(f"Base values: ATK={base_atk}, DEF={base_def}, HP={base_hp}")
        
        sqrt_def = math.sqrt(base_def)
        sqrt_hp = math.sqrt(base_hp)
        cpm_squared = cpm ** 2
        
        if debug:
            print(f"Intermediate: sqrt(DEF)={sqrt_def:.6f}, sqrt(HP)={sqrt_hp:.6f}, CPM^2={cpm_squared:.12f}")
        
        # JavaScript formula
        cp_float = (base_atk * sqrt_def * sqrt_hp * cpm_squared) / 10
        cp = math.floor(cp_float)
        final_cp = max(10, cp)
        
        if debug:
            print(f"CP calculation: ({base_atk} * {sqrt_def:.6f} * {sqrt_hp:.6f} * {cpm_squared:.12f}) / 10 = {cp_float:.6f}")
            print(f"Floored CP: {cp}")
            print(f"Final CP: {final_cp}")
        
        return final_cp


class PythonCalculatorDetailed:
    """Python implementation with detailed logging."""
    
    @staticmethod
    def calculate_cp_detailed(base_stats: Stats, ivs: IVs, level: float, shadow_type: str = "normal", debug: bool = False):
        """Calculate CP with detailed logging using Python implementation."""
        if debug:
            print(f"\n=== Python Implementation Calculation (FIXED) ===")
            print(f"Base stats: ATK={base_stats.atk}, DEF={base_stats.defense}, HP={base_stats.hp}")
            print(f"IVs: ATK={ivs.atk}, DEF={ivs.defense}, HP={ivs.hp}")
            print(f"Level: {level}")
            print(f"Shadow type: {shadow_type}")
        
        # Use the fixed CPCalculator
        cp = CPCalculator.calculate_cp(base_stats, ivs, level, shadow_type)
        
        if debug:
            # Show the internal calculation for comparison
            cpm = CPCalculator.get_cpm(level)
            print(f"CPM: {cpm:.12f}")
            
            shadow_atk_mult = 1.2 if shadow_type == "shadow" else 1.0
            shadow_def_mult = 0.833333 if shadow_type == "shadow" else 1.0
            print(f"Shadow multipliers: ATK={shadow_atk_mult}, DEF={shadow_def_mult}")
            
            # New JavaScript-compatible formula
            base_atk = (base_stats.atk + ivs.atk) * shadow_atk_mult
            base_def = (base_stats.defense + ivs.defense) * shadow_def_mult
            base_hp = (base_stats.hp + ivs.hp)
            
            print(f"Base values: ATK={base_atk}, DEF={base_def}, HP={base_hp}")
            
            sqrt_def = math.sqrt(base_def)
            sqrt_hp = math.sqrt(base_hp)
            cmp_squared = cpm ** 2
            
            print(f"Intermediate: sqrt(DEF)={sqrt_def:.6f}, sqrt(HP)={sqrt_hp:.6f}, CPM^2={cmp_squared:.12f}")
            
            cp_float = (base_atk * sqrt_def * sqrt_hp * cmp_squared) / 10
            print(f"CP calculation: ({base_atk} * {sqrt_def:.6f} * {sqrt_hp:.6f} * {cmp_squared:.12f}) / 10 = {cp_float:.6f}")
            print(f"Final CP: {cp}")
        
        return cp


def debug_specific_case():
    """Debug a specific failing case in detail."""
    print("Debugging Mewtwo L50 15/15/15 Normal")
    print("=" * 60)
    
    base_stats = Stats(atk=300, defense=182, hp=214)
    ivs = IVs(15, 15, 15)
    level = 50.0
    shadow_type = "normal"
    
    # Calculate using both methods with detailed logging
    python_cp = PythonCalculatorDetailed.calculate_cp_detailed(
        base_stats, ivs, level, shadow_type, debug=True
    )
    
    js_cp = JSReferenceCalculator.calculate_cp_detailed(
        base_stats, ivs, level, shadow_type, debug=True
    )
    
    print(f"\n=== COMPARISON ===")
    print(f"Python CP: {python_cp}")
    print(f"JavaScript CP: {js_cp}")
    print(f"Difference: {abs(python_cp - js_cp)}")
    
    # Let's also check if the formulas are mathematically equivalent
    print(f"\n=== MATHEMATICAL EQUIVALENCE CHECK ===")
    
    cpm = CPCalculator.get_cpm(level)
    print(f"CPM: {cpm:.12f}")
    
    # Python approach: multiply stats by CPM first, then calculate CP
    python_atk = (base_stats.atk + ivs.atk) * cpm
    python_def = (base_stats.defense + ivs.defense) * cpm
    python_hp = math.floor((base_stats.hp + ivs.hp) * cpm)
    
    print(f"Python effective stats: ATK={python_atk:.6f}, DEF={python_def:.6f}, HP={python_hp}")
    
    # JavaScript approach: use base stats + IVs, multiply by CPM^2 in formula
    js_base_atk = base_stats.atk + ivs.atk
    js_base_def = base_stats.defense + ivs.defense
    js_base_hp = base_stats.hp + ivs.hp
    
    print(f"JavaScript base stats: ATK={js_base_atk}, DEF={js_base_def}, HP={js_base_hp}")
    
    # Check if they should be equivalent
    # Python: 0.1 * (atk * cpm) * sqrt(def * cpm) * sqrt(hp * cpm)
    # = 0.1 * atk * cpm * sqrt(def) * sqrt(cpm) * sqrt(hp) * sqrt(cpm)
    # = 0.1 * atk * sqrt(def) * sqrt(hp) * cpm * cmp * cpm
    # = 0.1 * atk * sqrt(def) * sqrt(hp) * cpm^2
    # = (atk * sqrt(def) * sqrt(hp) * cpm^2) / 10
    
    # But wait - Python floors the HP first!
    print(f"\n=== KEY DIFFERENCE FOUND ===")
    print(f"Python HP (floored): {python_hp}")
    print(f"JavaScript HP (not floored): {js_base_hp}")
    print(f"HP difference: {python_hp - js_base_hp}")
    
    # Let's test without flooring HP in Python
    python_hp_no_floor = (base_stats.hp + ivs.hp) * cpm
    print(f"Python HP (no floor): {python_hp_no_floor:.6f}")
    
    # Recalculate Python CP without flooring HP
    cp_no_floor = 0.1 * python_atk * math.sqrt(python_def) * math.sqrt(python_hp_no_floor)
    cp_no_floor_final = math.floor(cp_no_floor)
    
    print(f"Python CP (no HP floor): {cp_no_floor_final}")
    print(f"Difference from JS: {abs(cp_no_floor_final - js_cp)}")


def debug_shadow_case():
    """Debug a shadow Pokemon case."""
    print("\n\nDebugging Shadow Mewtwo L40 15/15/15")
    print("=" * 60)
    
    base_stats = Stats(atk=300, defense=182, hp=214)
    ivs = IVs(15, 15, 15)
    level = 40.0
    shadow_type = "shadow"
    
    python_cp = PythonCalculatorDetailed.calculate_cp_detailed(
        base_stats, ivs, level, shadow_type, debug=True
    )
    
    js_cp = JSReferenceCalculator.calculate_cp_detailed(
        base_stats, ivs, level, shadow_type, debug=True
    )
    
    print(f"\n=== COMPARISON ===")
    print(f"Python CP: {python_cp}")
    print(f"JavaScript CP: {js_cp}")
    print(f"Difference: {abs(python_cp - js_cp)}")


def main():
    """Run detailed debugging."""
    print("CP Calculation Debugging")
    print("Identifying where Python and JavaScript calculations differ")
    print("=" * 80)
    
    # Debug the specific failing case
    debug_specific_case()
    
    # Debug a shadow case
    debug_shadow_case()
    
    print("\n" + "=" * 80)
    print("DEBUGGING COMPLETE")
    print("=" * 80)
    print("Key findings:")
    print("1. Check if HP flooring in Python is causing the difference")
    print("2. Verify shadow multiplier application order")
    print("3. Compare intermediate calculation steps")


if __name__ == "__main__":
    main()
