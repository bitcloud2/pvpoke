"""CP calculation and optimization utilities."""

import math
from typing import List, Tuple, Optional, Dict
from ..core.pokemon import Pokemon, IVs, Stats


class CPCalculator:
    """Utilities for CP calculations and IV optimization."""
    
    @staticmethod
    def calculate_cp(base_stats: Stats, ivs: IVs, level: float, 
                    shadow_type: str = "normal") -> int:
        """
        Calculate CP for given stats and level.
        
        Args:
            base_stats: Base stats of the Pokemon
            ivs: Individual values
            level: Pokemon level (1-50)
            shadow_type: "normal", "shadow", or "purified"
            
        Returns:
            Calculated CP
        """
        cpm = CPCalculator.get_cpm(level)
        
        # Shadow bonuses/penalties
        shadow_atk_mult = 1.2 if shadow_type == "shadow" else 1.0
        shadow_def_mult = 0.833333 if shadow_type == "shadow" else 1.0
        
        # Use JavaScript-compatible formula: cp = floor((atk * sqrt(def) * sqrt(hp) * cpm^2) / 10)
        # This is mathematically equivalent to the original but matches JS implementation exactly
        base_atk = (base_stats.atk + ivs.atk) * shadow_atk_mult
        base_def = (base_stats.defense + ivs.defense) * shadow_def_mult
        base_hp = (base_stats.hp + ivs.hp)
        
        cp = math.floor((base_atk * math.sqrt(base_def) * math.sqrt(base_hp) * (cpm ** 2)) / 10)
        return max(10, cp)
    
    @staticmethod
    def get_cpm(level: float) -> float:
        """Get CP multiplier for a level."""
        # CPM values for levels 1-50 (in 0.5 increments)
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
        
        index = int((level - 1) * 2)
        return CPM_VALUES[index] if 0 <= index < len(CPM_VALUES) else 0
    
    @staticmethod
    def find_optimal_ivs(base_stats: Stats, cp_limit: int,
                        level_cap: float = 50.0, 
                        min_level: float = 1.0) -> List[Tuple[IVs, float, int, float]]:
        """
        Find optimal IV combinations for a CP-limited league.
        
        Args:
            base_stats: Base stats of the Pokemon
            cp_limit: Maximum CP allowed
            level_cap: Maximum level to consider
            min_level: Minimum level to consider
            
        Returns:
            List of (IVs, level, CP, stat_product) tuples, sorted by stat product
        """
        results = []
        
        # Try all IV combinations
        for atk_iv in range(16):
            for def_iv in range(16):
                for hp_iv in range(16):
                    ivs = IVs(atk=atk_iv, defense=def_iv, hp=hp_iv)
                    
                    # Find maximum level under CP limit
                    best_level = min_level
                    best_cp = 0
                    
                    for level in [l/2 for l in range(int(min_level*2), int(level_cap*2)+1)]:
                        cp = CPCalculator.calculate_cp(base_stats, ivs, level)
                        
                        if cp <= cp_limit:
                            best_level = level
                            best_cp = cp
                        else:
                            break
                    
                    # Calculate stat product at best level
                    cpm = CPCalculator.get_cpm(best_level)
                    atk = (base_stats.atk + ivs.atk) * cpm
                    defense = (base_stats.defense + ivs.defense) * cpm
                    hp = math.floor((base_stats.hp + ivs.hp) * cpm)
                    stat_product = atk * defense * hp
                    
                    results.append((ivs, best_level, best_cp, stat_product))
        
        # Sort by stat product (highest first)
        results.sort(key=lambda x: x[3], reverse=True)
        
        return results
    
    @staticmethod
    def get_pvp_rank(base_stats: Stats, ivs: IVs, level: float,
                     cp_limit: int) -> Tuple[int, float]:
        """
        Get PvP rank for given IVs.
        
        Args:
            base_stats: Base stats
            ivs: IVs to evaluate
            level: Level of the Pokemon
            cp_limit: CP limit for the league
            
        Returns:
            Tuple of (rank, stat_product_percentage)
        """
        # Get all combinations
        all_combos = CPCalculator.find_optimal_ivs(base_stats, cp_limit)
        
        if not all_combos:
            return 4096, 0.0  # Max rank if no valid combinations
        
        # Calculate stat product for given IVs
        cpm = CPCalculator.get_cpm(level)
        atk = (base_stats.atk + ivs.atk) * cpm
        defense = (base_stats.defense + ivs.defense) * cpm
        hp = math.floor((base_stats.hp + ivs.hp) * cpm)
        stat_product = atk * defense * hp
        
        # Find rank
        max_product = all_combos[0][3]
        rank = 1
        
        for combo in all_combos:
            if abs(combo[3] - stat_product) < 0.01:  # Found matching product
                break
            rank += 1
        
        percentage = (stat_product / max_product * 100) if max_product > 0 else 0
        
        return rank, percentage
    
    @staticmethod
    def recommend_great_league_ivs(base_stats: Stats) -> List[Dict]:
        """
        Get recommended IV spreads for Great League.
        
        Args:
            base_stats: Base stats of the Pokemon
            
        Returns:
            Top 10 IV combinations with details
        """
        optimal = CPCalculator.find_optimal_ivs(base_stats, 1500)[:10]
        
        recommendations = []
        for i, (ivs, level, cp, product) in enumerate(optimal, 1):
            recommendations.append({
                "rank": i,
                "ivs": f"{ivs.atk}/{ivs.defense}/{ivs.hp}",
                "level": level,
                "cp": cp,
                "stat_product": int(product),
                "percentage": f"{(product / optimal[0][3] * 100):.1f}%" if optimal else "0%"
            })
        
        return recommendations
