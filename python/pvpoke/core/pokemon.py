"""Pokemon class and related data structures."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import math


@dataclass
class Stats:
    """Pokemon stats (Attack, Defense, HP)."""
    atk: float
    defense: float  
    hp: int
    
    def __repr__(self):
        return f"Stats(atk={self.atk:.1f}, def={self.defense:.1f}, hp={self.hp})"


@dataclass
class IVs:
    """Individual Values for a Pokemon."""
    atk: int = 0
    defense: int = 0
    hp: int = 0
    
    def validate(self):
        """Ensure IVs are within valid range (0-15)."""
        for stat in [self.atk, self.defense, self.hp]:
            if not 0 <= stat <= 15:
                raise ValueError(f"IV must be between 0 and 15, got {stat}")


@dataclass
class Pokemon:
    """Represents a Pokemon with its stats, moves, and battle properties."""
    
    # Basic properties
    species_id: str
    species_name: str
    dex: int
    
    # Stats
    base_stats: Stats
    types: List[str]
    
    # Moves
    fast_moves: List[str] = field(default_factory=list)
    charged_moves: List[str] = field(default_factory=list)
    legacy_moves: List[str] = field(default_factory=list)
    elite_moves: List[str] = field(default_factory=list)
    
    # Battle properties
    level: float = 50.0
    ivs: IVs = field(default_factory=lambda: IVs(0, 0, 0))
    cp: int = 0
    hp: int = 0
    energy: int = 0
    shields: int = 2
    
    # Current battle state
    current_hp: int = 0
    stat_buffs: List[int] = field(default_factory=lambda: [0, 0])  # [atk, def]
    
    # Selected moves
    fast_move: Optional[object] = None
    charged_move_1: Optional[object] = None
    charged_move_2: Optional[object] = None
    
    # Shadow status
    shadow_type: str = "normal"  # "normal", "shadow", or "purified"
    
    # AI behavior properties
    farm_energy: bool = False
    bait_shields: bool = False
    optimize_move_timing: bool = False
    priority: int = 0
    index: int = 0  # Player index (0 or 1)
    
    # Battle state tracking
    cooldown: int = 0  # Cooldown in milliseconds
    turns_to_ko: int = -1  # Turns needed to KO opponent
    
    # Form-specific properties (for Pokemon like Aegislash)
    active_form_id: Optional[str] = None  # Current form ID (e.g., "aegislash_shield", "aegislash_blade")
    best_charged_move: Optional[object] = None  # Cached reference to best charged move
    
    # CP multipliers for each level (1-50)
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
    
    def get_cpm(self, level: float) -> float:
        """Get CP multiplier for a given level."""
        # Levels are in 0.5 increments, so index = (level - 1) * 2
        index = int((level - 1) * 2)
        return self.CPM_VALUES[index] if 0 <= index < len(self.CPM_VALUES) else 0
    
    def calculate_stats(self) -> Stats:
        """Calculate effective stats based on level and IVs."""
        cpm = self.get_cpm(self.level)
        
        # Shadow bonuses/penalties
        shadow_atk_mult = 1.2 if self.shadow_type == "shadow" else 1.0
        shadow_def_mult = 0.833333 if self.shadow_type == "shadow" else 1.0
        
        atk = (self.base_stats.atk + self.ivs.atk) * cpm * shadow_atk_mult
        defense = (self.base_stats.defense + self.ivs.defense) * cpm * shadow_def_mult
        hp = math.floor((self.base_stats.hp + self.ivs.hp) * cpm)
        
        return Stats(atk=atk, defense=defense, hp=hp)
    
    def calculate_cp(self) -> int:
        """Calculate CP based on current stats."""
        # Use CPCalculator for consistent CP calculation
        from ..utils.cp_calculator import CPCalculator
        return CPCalculator.calculate_cp(self.base_stats, self.ivs, self.level, self.shadow_type)
    
    def reset(self):
        """Reset Pokemon to initial battle state."""
        stats = self.calculate_stats()
        self.current_hp = stats.hp
        self.energy = 0
        self.stat_buffs = [0, 0]
        self.cooldown = 0
        self.turns_to_ko = -1
    
    @property
    def stats(self) -> Stats:
        """Get current effective stats (for compatibility with AI logic)."""
        return self.calculate_stats()
    
    def optimize_for_league(self, cp_limit: int):
        """Find the best IV combination for a given CP limit."""
        best_product = 0
        best_ivs = None
        best_level = 1
        
        # Try all IV combinations
        for atk_iv in range(16):
            for def_iv in range(16):
                for hp_iv in range(16):
                    self.ivs = IVs(atk=atk_iv, defense=def_iv, hp=hp_iv)
                    
                    # Find max level under CP limit
                    for level in [l/2 for l in range(2, 101)]:  # Levels 1-50 in 0.5 increments
                        self.level = level
                        cp = self.calculate_cp()
                        
                        if cp <= cp_limit:
                            stats = self.calculate_stats()
                            product = stats.atk * stats.defense * stats.hp
                            
                            if product > best_product:
                                best_product = product
                                best_ivs = IVs(atk=atk_iv, defense=def_iv, hp=hp_iv)
                                best_level = level
                        else:
                            break  # CP exceeded, no need to check higher levels
        
        if best_ivs:
            self.ivs = best_ivs
            self.level = best_level
            self.cp = self.calculate_cp()
            stats = self.calculate_stats()
            self.hp = stats.hp
            self.current_hp = stats.hp
    
    def reset(self):
        """Reset Pokemon to initial battle state."""
        stats = self.calculate_stats()
        self.current_hp = stats.hp
        self.energy = 0
        self.stat_buffs = [0, 0]
        self.shields = 2  # Reset shields to default
        
        # Reset buff apply meters for deterministic buff application
        self.reset_move_buff_meters()
        
    def reset_move_buff_meters(self):
        """Reset buff apply meters on moves for deterministic buff application."""
        # Reset charged move buff meters
        if self.charged_move_1 and hasattr(self.charged_move_1, 'buff_chance'):
            # Initialize like JavaScript: buffApplyMeter = buffApplyChance, except 50% starts at 0
            if self.charged_move_1.buff_chance == 0.5:
                self.charged_move_1.buff_apply_meter = 0.0
            else:
                self.charged_move_1.buff_apply_meter = self.charged_move_1.buff_chance
        
        if self.charged_move_2 and hasattr(self.charged_move_2, 'buff_chance'):
            # Initialize like JavaScript: buffApplyMeter = buffApplyChance, except 50% starts at 0
            if self.charged_move_2.buff_chance == 0.5:
                self.charged_move_2.buff_apply_meter = 0.0
            else:
                self.charged_move_2.buff_apply_meter = self.charged_move_2.buff_chance
    
    def initialize_aegislash_moves(self):
        """
        Initialize Aegislash Shield form charged moves with self-debuffing properties.
        
        For Aegislash Shield form, all charged moves are marked as self-debuffing with
        [0,0] buffs. This ensures the AI treats them appropriately when making decisions
        about move timing and baiting.
        
        JavaScript Reference (Pokemon.js lines 745-751):
        if(self.activeFormId == "aegislash_shield"){
            self.activeChargedMoves.forEach(move => {
                move.buffs = [0,0];
                move.buffTarget = self;
                move.selfDebuffing = true;
            });
        }
        """
        if self.active_form_id == "aegislash_shield":
            # Mark all charged moves as self-debuffing with [0,0] buffs
            if self.charged_move_1:
                self.charged_move_1.buffs = [0.0, 0.0]
                self.charged_move_1.buff_target = "self"
                # Note: self_debuffing is a property that checks buffs, so no need to set it
            
            if self.charged_move_2:
                self.charged_move_2.buffs = [0.0, 0.0]
                self.charged_move_2.buff_target = "self"
        
    def get_effective_stat(self, stat_index: int) -> float:
        """Get effective stat with buffs applied. 0=atk, 1=def."""
        stats = self.calculate_stats()
        base_stat = stats.atk if stat_index == 0 else stats.defense
        
        # Stat buff multipliers (4 stages: -4 to +4)
        buff_multipliers = [0.5, 0.5714, 0.6667, 0.8, 1.0, 1.25, 1.5, 1.75, 2.0]
        buff_value = int(self.stat_buffs[stat_index]) + 4  # Convert to 0-8 index
        buff_value = max(0, min(8, buff_value))  # Clamp to valid range
        
        return base_stat * buff_multipliers[buff_value]
    
    def get_form_stats(self, form_id: str, battle_cp: Optional[int] = None) -> Stats:
        """
        Get stats for an alternative form of this Pokemon.
        
        Used for Pokemon with form changes like Aegislash to calculate stats
        in their alternative form while maintaining the same IVs and adjusted level.
        
        JavaScript Reference (Pokemon.js lines 2391-2464):
        this.getFormStats = function(formId){
            let newForm = gm.getPokemonById(formId);
            let newLevel = self.level;
            // Form specific cases for Aegislash with level adjustments
        }
        
        Args:
            form_id: Species ID of the alternative form (e.g., "aegislash_blade")
            battle_cp: Battle CP limit (1500, 2500, etc.) for form-specific level adjustments
            
        Returns:
            Stats object with the alternative form's stats
        """
        from .gamemaster import GameMaster
        
        # Get the alternative form's base stats
        try:
            gm = GameMaster()
            alt_form = gm.get_pokemon(form_id)
        except (FileNotFoundError, Exception):
            # If GameMaster not available, return current stats
            alt_form = None
        
        if not alt_form:
            # If form not found, return current stats
            return self.calculate_stats()
        
        # Start with current level
        new_level = self.level
        
        # Apply form-specific level adjustments (primarily for Aegislash)
        if self.species_id != form_id:
            # Aegislash Blade form (Shield -> Blade)
            if form_id == "aegislash_blade":
                if battle_cp == 1500:
                    # Great League: Blade level = ceil(Shield level * 0.5) + 1
                    new_level = math.ceil(self.level * 0.5) + 1
                elif battle_cp == 2500:
                    # Ultra League: Blade level = ceil(Shield level * 0.75)
                    new_level = math.ceil(self.level * 0.75)
            
            # Aegislash Shield form (Blade -> Shield)
            elif form_id == "aegislash_shield":
                if battle_cp == 1500:
                    # Great League: Shield level = (Blade level / 0.5) + 2
                    new_level = (self.level / 0.5) + 2
                elif battle_cp == 2500:
                    # Ultra League: Shield level = round(Blade level / 0.75)
                    new_level = round(self.level / 0.75)
        
        # Calculate stats using alternative form's base stats with current IVs and adjusted level
        cpm = self.get_cpm(new_level)
        
        # Apply shadow multipliers if this Pokemon is shadow
        shadow_atk_mult = 1.2 if self.shadow_type == "shadow" else 1.0
        shadow_def_mult = 0.833333 if self.shadow_type == "shadow" else 1.0
        
        atk = (alt_form.base_stats.atk + self.ivs.atk) * cpm * shadow_atk_mult
        defense = (alt_form.base_stats.defense + self.ivs.defense) * cpm * shadow_def_mult
        hp = math.floor((alt_form.base_stats.hp + self.ivs.hp) * cpm)
        
        return Stats(atk=atk, defense=defense, hp=hp)
    
    def __repr__(self):
        return f"Pokemon(species={self.species_name}, cp={self.cp}, level={self.level}, ivs={self.ivs})"
