"""Tests for GameMaster data loading and management."""

import unittest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.core import GameMaster, Pokemon, Stats, IVs
from pvpoke.core.moves import FastMove, ChargedMove


class TestGameMaster(unittest.TestCase):
    """Test GameMaster class functionality."""
    
    def setUp(self):
        """Set up test GameMaster with mock data."""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create mock gamemaster data
        self.mock_data = {
            "pokemon": [
                {
                    "speciesId": "azumarill",
                    "speciesName": "Azumarill",
                    "dex": 184,
                    "baseStats": {"atk": 112.2, "def": 152.3, "hp": 225},
                    "types": ["water", "fairy"],
                    "fastMoves": ["BUBBLE", "ROCK_SMASH"],
                    "chargedMoves": ["ICE_BEAM", "PLAY_ROUGH", "HYDRO_PUMP"],
                    "legacyMoves": [],
                    "eliteMoves": [],
                    "released": True
                },
                {
                    "speciesId": "medicham",
                    "speciesName": "Medicham",
                    "dex": 308,
                    "baseStats": {"atk": 121, "def": 152, "hp": 155},
                    "types": ["fighting", "psychic"],
                    "fastMoves": ["COUNTER", "PSYCHO_CUT"],
                    "chargedMoves": ["POWER_UP_PUNCH", "ICE_PUNCH", "PSYCHIC"],
                    "legacyMoves": [],
                    "eliteMoves": [],
                    "released": True
                },
                {
                    "speciesId": "azumarill_shadow",
                    "speciesName": "Azumarill (Shadow)",
                    "dex": 184,
                    "baseStats": {"atk": 112.2, "def": 152.3, "hp": 225},
                    "types": ["water", "fairy"],
                    "fastMoves": ["BUBBLE", "ROCK_SMASH"],
                    "chargedMoves": ["ICE_BEAM", "PLAY_ROUGH", "HYDRO_PUMP"],
                    "legacyMoves": [],
                    "eliteMoves": [],
                    "released": False
                }
            ],
            "moves": [
                {
                    "moveId": "BUBBLE",
                    "name": "Bubble",
                    "type": "water",
                    "power": 7,
                    "energyGain": 11,
                    "turns": 3
                },
                {
                    "moveId": "COUNTER",
                    "name": "Counter",
                    "type": "fighting",
                    "power": 8,
                    "energyGain": 7,
                    "turns": 2
                },
                {
                    "moveId": "ICE_BEAM",
                    "name": "Ice Beam",
                    "type": "ice",
                    "power": 90,
                    "energy": 55
                },
                {
                    "moveId": "POWER_UP_PUNCH",
                    "name": "Power-Up Punch",
                    "type": "fighting",
                    "power": 20,
                    "energy": 35,
                    "buffs": [1.25, 1.0],
                    "buffTarget": "self",
                    "buffChance": 1.0
                }
            ],
            "formats": [
                {
                    "name": "Great League",
                    "cp": 1500,
                    "include": [],
                    "exclude": []
                },
                {
                    "name": "Ultra League",
                    "cp": 2500,
                    "include": [],
                    "exclude": []
                }
            ]
        }
        
        # Write mock data to file
        gamemaster_path = self.test_path / "gamemaster.json"
        with open(gamemaster_path, 'w') as f:
            json.dump(self.mock_data, f)
        
        # Initialize GameMaster with test data
        self.gm = GameMaster(data_dir=self.test_path)
    
    def tearDown(self):
        """Clean up test directory."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_gamemaster_initialization(self):
        """Test GameMaster initializes correctly."""
        self.assertIsNotNone(self.gm.data)
        self.assertEqual(len(self.gm.pokemon_map), 3)
        self.assertEqual(len(self.gm.fast_move_map), 2)
        self.assertEqual(len(self.gm.charged_move_map), 2)
    
    def test_load_gamemaster_file(self):
        """Test loading gamemaster.json file."""
        self.assertIn("pokemon", self.gm.data)
        self.assertIn("moves", self.gm.data)
        self.assertIn("formats", self.gm.data)
        self.assertEqual(len(self.gm.data["pokemon"]), 3)
        self.assertEqual(len(self.gm.data["moves"]), 4)
    
    def test_process_pokemon(self):
        """Test Pokemon data is processed correctly."""
        # Check Azumarill
        azumarill = self.gm.get_pokemon("azumarill")
        self.assertIsNotNone(azumarill)
        self.assertEqual(azumarill.species_name, "Azumarill")
        self.assertEqual(azumarill.dex, 184)
        self.assertEqual(azumarill.types, ["water", "fairy"])
        self.assertAlmostEqual(azumarill.base_stats.atk, 112.2, places=1)
        self.assertAlmostEqual(azumarill.base_stats.defense, 152.3, places=1)
        self.assertEqual(azumarill.base_stats.hp, 225)
        
        # Check Medicham
        medicham = self.gm.get_pokemon("medicham")
        self.assertIsNotNone(medicham)
        self.assertEqual(medicham.species_name, "Medicham")
        self.assertEqual(medicham.types, ["fighting", "psychic"])
    
    def test_process_fast_moves(self):
        """Test fast moves are processed correctly."""
        # Check Bubble
        bubble = self.gm.get_fast_move("BUBBLE")
        self.assertIsNotNone(bubble)
        self.assertIsInstance(bubble, FastMove)
        self.assertEqual(bubble.name, "Bubble")
        self.assertEqual(bubble.move_type, "water")
        self.assertEqual(bubble.power, 7)
        self.assertEqual(bubble.energy_gain, 11)
        self.assertEqual(bubble.turns, 3)
        
        # Check Counter
        counter = self.gm.get_fast_move("COUNTER")
        self.assertIsNotNone(counter)
        self.assertEqual(counter.name, "Counter")
        self.assertEqual(counter.power, 8)
    
    def test_process_charged_moves(self):
        """Test charged moves are processed correctly."""
        # Check Ice Beam
        ice_beam = self.gm.get_charged_move("ICE_BEAM")
        self.assertIsNotNone(ice_beam)
        self.assertIsInstance(ice_beam, ChargedMove)
        self.assertEqual(ice_beam.name, "Ice Beam")
        self.assertEqual(ice_beam.move_type, "ice")
        self.assertEqual(ice_beam.power, 90)
        self.assertEqual(ice_beam.energy_cost, 55)
        
        # Check Power-Up Punch with buffs
        pup = self.gm.get_charged_move("POWER_UP_PUNCH")
        self.assertIsNotNone(pup)
        self.assertEqual(pup.name, "Power-Up Punch")
        self.assertEqual(pup.buffs, [1.25, 1.0])
        self.assertEqual(pup.buff_target, "self")
        self.assertEqual(pup.buff_chance, 1.0)
    
    def test_get_nonexistent_pokemon(self):
        """Test getting a Pokemon that doesn't exist."""
        pokemon = self.gm.get_pokemon("doesnotexist")
        self.assertIsNone(pokemon)
    
    def test_get_nonexistent_moves(self):
        """Test getting moves that don't exist."""
        fast_move = self.gm.get_fast_move("DOESNOTEXIST")
        self.assertIsNone(fast_move)
        
        charged_move = self.gm.get_charged_move("DOESNOTEXIST")
        self.assertIsNone(charged_move)
    
    def test_get_pokemon_for_league(self):
        """Test getting Pokemon eligible for a league."""
        # Great League
        great_league_pokemon = self.gm.get_pokemon_for_league(
            cp_limit=1500,
            include_unreleased=False,
            include_shadows=False
        )
        
        # Should include released non-shadow Pokemon
        species_ids = [p.species_id for p in great_league_pokemon]
        self.assertIn("azumarill", species_ids)
        self.assertIn("medicham", species_ids)
        self.assertNotIn("azumarill_shadow", species_ids)  # Unreleased
        
        # Include unreleased
        all_pokemon = self.gm.get_pokemon_for_league(
            cp_limit=1500,
            include_unreleased=True,
            include_shadows=True
        )
        
        species_ids = [p.species_id for p in all_pokemon]
        self.assertIn("azumarill_shadow", species_ids)
    
    def test_get_formats(self):
        """Test getting available formats."""
        formats = self.gm.get_formats()
        self.assertEqual(len(formats), 2)
        self.assertEqual(formats[0]["name"], "Great League")
        self.assertEqual(formats[0]["cp"], 1500)
        self.assertEqual(formats[1]["name"], "Ultra League")
        self.assertEqual(formats[1]["cp"], 2500)
    
    def test_load_rankings(self):
        """Test loading rankings from file."""
        # Create mock rankings file
        rankings_dir = self.test_path / "rankings" / "all" / "overall"
        rankings_dir.mkdir(parents=True)
        
        mock_rankings = [
            {"speciesId": "azumarill", "score": 95.5},
            {"speciesId": "medicham", "score": 94.2}
        ]
        
        with open(rankings_dir / "rankings-1500.json", 'w') as f:
            json.dump(mock_rankings, f)
        
        # Load rankings
        rankings = self.gm.load_rankings(league="all", cp=1500, category="overall")
        self.assertEqual(len(rankings), 2)
        self.assertEqual(rankings[0]["speciesId"], "azumarill")
        self.assertEqual(rankings[0]["score"], 95.5)
    
    def test_load_nonexistent_rankings(self):
        """Test loading rankings that don't exist."""
        rankings = self.gm.load_rankings(league="nonexistent", cp=9999, category="invalid")
        self.assertEqual(rankings, [])
    
    def test_missing_gamemaster_file(self):
        """Test handling of missing gamemaster file."""
        empty_dir = tempfile.mkdtemp()
        
        with self.assertRaises(FileNotFoundError):
            GameMaster(data_dir=empty_dir)
        
        import shutil
        shutil.rmtree(empty_dir)
    
    def test_minified_gamemaster_fallback(self):
        """Test fallback to gamemaster.min.json."""
        # Create directory with only minified version
        min_dir = tempfile.mkdtemp()
        min_path = Path(min_dir)
        
        # Write minified version
        with open(min_path / "gamemaster.min.json", 'w') as f:
            json.dump(self.mock_data, f)
        
        # Should load successfully
        gm = GameMaster(data_dir=min_path)
        self.assertIsNotNone(gm.data)
        self.assertEqual(len(gm.pokemon_map), 3)
        
        import shutil
        shutil.rmtree(min_dir)
    
    def test_pokemon_with_single_type(self):
        """Test handling Pokemon with single type."""
        # Add single-type Pokemon to test data
        single_type_data = self.mock_data.copy()
        single_type_data["pokemon"].append({
            "speciesId": "snorlax",
            "speciesName": "Snorlax",
            "dex": 143,
            "baseStats": {"atk": 190, "def": 169, "hp": 330},
            "types": ["normal"],  # Single type
            "fastMoves": ["LICK"],
            "chargedMoves": ["BODY_SLAM"],
            "legacyMoves": [],
            "eliteMoves": [],
            "released": True
        })
        
        # Reinitialize with new data
        test_dir = tempfile.mkdtemp()
        test_path = Path(test_dir)
        with open(test_path / "gamemaster.json", 'w') as f:
            json.dump(single_type_data, f)
        
        gm = GameMaster(data_dir=test_path)
        snorlax = gm.get_pokemon("snorlax")
        
        self.assertIsNotNone(snorlax)
        self.assertEqual(snorlax.types[0], "normal")
        self.assertIsNone(snorlax.types[1])
        
        import shutil
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    unittest.main()
