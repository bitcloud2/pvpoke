"""GameMaster data loader and manager."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .pokemon import Pokemon, Stats, IVs
from .moves import FastMove, ChargedMove


@dataclass
class League:
    """League/cup configuration."""
    name: str
    cp: int
    include: List[str] = None  # Include rules
    exclude: List[str] = None  # Exclude rules


class GameMaster:
    """
    Loads and manages game data from the gamemaster.json file.
    Provides access to Pokemon, moves, and league configurations.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize GameMaster with data directory.
        
        Args:
            data_dir: Path to data directory. If None, uses default location.
        """
        if data_dir is None:
            # Default to src/data directory relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            data_dir = project_root / "src" / "data"
        
        self.data_dir = Path(data_dir)
        self.data: Dict[str, Any] = {}
        self.pokemon_map: Dict[str, Pokemon] = {}
        self.fast_move_map: Dict[str, FastMove] = {}
        self.charged_move_map: Dict[str, ChargedMove] = {}
        
        # Load the data
        self.load_gamemaster()
        self.process_pokemon()
        self.process_moves()
    
    def load_gamemaster(self):
        """Load the gamemaster.json file."""
        gamemaster_path = self.data_dir / "gamemaster.json"
        
        if not gamemaster_path.exists():
            # Try minified version
            gamemaster_path = self.data_dir / "gamemaster.min.json"
        
        if not gamemaster_path.exists():
            raise FileNotFoundError(f"GameMaster file not found at {gamemaster_path}")
        
        with open(gamemaster_path, 'r') as f:
            self.data = json.load(f)
        
        print(f"Loaded GameMaster with {len(self.data.get('pokemon', []))} Pokemon and {len(self.data.get('moves', []))} moves")
    
    def process_pokemon(self):
        """Process Pokemon data into Pokemon objects."""
        for poke_data in self.data.get('pokemon', []):
            # Create Stats object
            base_stats = Stats(
                atk=poke_data['baseStats']['atk'],
                defense=poke_data['baseStats']['def'],
                hp=poke_data['baseStats']['hp']
            )
            
            # Create Pokemon object
            types = poke_data.get('types', [])
            pokemon = Pokemon(
                species_id=poke_data['speciesId'],
                species_name=poke_data['speciesName'],
                dex=poke_data.get('dex', 0),
                base_stats=base_stats,
                types=[types[0] if len(types) > 0 else None, types[1] if len(types) > 1 else None],
                fast_moves=poke_data.get('fastMoves', []),
                charged_moves=poke_data.get('chargedMoves', []),
                legacy_moves=poke_data.get('legacyMoves', []),
                elite_moves=poke_data.get('eliteMoves', [])
            )
            
            # Store in map
            self.pokemon_map[pokemon.species_id] = pokemon
    
    def process_moves(self):
        """Process move data into Move objects."""
        for move_data in self.data.get('moves', []):
            move_id = move_data['moveId']
            
            if move_data.get('energyGain', 0) > 0:
                # Fast move
                fast_move = FastMove(
                    move_id=move_id,
                    name=move_data['name'],
                    move_type=move_data['type'],
                    power=move_data.get('power', 0),
                    energy_gain=move_data['energyGain'],
                    turns=move_data.get('turns', 1)
                )
                self.fast_move_map[move_id] = fast_move
            else:
                # Charged move
                buffs = [1.0, 1.0]  # Default no buffs
                if 'buffs' in move_data:
                    buffs = move_data['buffs']
                
                charged_move = ChargedMove(
                    move_id=move_id,
                    name=move_data['name'],
                    move_type=move_data['type'],
                    power=move_data.get('power', 0),
                    energy_cost=move_data.get('energy', 0),
                    buffs=buffs,
                    buff_target=move_data.get('buffTarget', 'self'),
                    buff_chance=move_data.get('buffChance', 1.0)
                )
                self.charged_move_map[move_id] = charged_move
    
    def get_pokemon(self, species_id: str) -> Optional[Pokemon]:
        """Get a Pokemon by species ID."""
        return self.pokemon_map.get(species_id)
    
    def get_fast_move(self, move_id: str) -> Optional[FastMove]:
        """Get a fast move by ID."""
        return self.fast_move_map.get(move_id)
    
    def get_charged_move(self, move_id: str) -> Optional[ChargedMove]:
        """Get a charged move by ID."""
        return self.charged_move_map.get(move_id)
    
    def get_pokemon_for_league(self, cp_limit: int, 
                               include_unreleased: bool = False,
                               include_shadows: bool = True) -> List[Pokemon]:
        """
        Get all Pokemon eligible for a specific league.
        
        Args:
            cp_limit: CP limit for the league
            include_unreleased: Whether to include unreleased Pokemon
            include_shadows: Whether to include shadow forms
            
        Returns:
            List of eligible Pokemon
        """
        eligible = []
        
        for poke_data in self.data.get('pokemon', []):
            # Skip unreleased if not requested
            if not include_unreleased and not poke_data.get('released', True):
                continue
            
            # Skip shadows if not requested
            if not include_shadows and '_shadow' in poke_data['speciesId']:
                continue
            
            # Create Pokemon and check if it can fit in CP limit
            pokemon = self.get_pokemon(poke_data['speciesId'])
            if pokemon:
                # Set max level and check minimum CP
                pokemon.level = 50
                pokemon.ivs = IVs(15, 15, 15)
                max_cp = pokemon.calculate_cp()
                
                # If max CP is above limit, it can be optimized down
                # If max CP is below limit, it will just use max level
                if max_cp >= cp_limit * 0.5:  # Rough filter for viability
                    eligible.append(pokemon)
        
        return eligible
    
    def get_formats(self) -> List[Dict]:
        """Get all available formats/cups."""
        return self.data.get('formats', [])
    
    def load_rankings(self, league: str = "all", cp: int = 1500, 
                      category: str = "overall") -> List[Dict]:
        """
        Load pre-calculated rankings from JSON files.
        
        Args:
            league: League/cup name
            cp: CP limit
            category: Ranking category (overall, leads, closers, etc.)
            
        Returns:
            List of ranking entries
        """
        ranking_path = self.data_dir / "rankings" / league / category / f"rankings-{cp}.json"
        
        if not ranking_path.exists():
            return []
        
        with open(ranking_path, 'r') as f:
            return json.load(f)
