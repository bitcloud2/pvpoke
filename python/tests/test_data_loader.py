"""Tests for data loading utilities."""

import unittest
import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pvpoke.utils.data_loader import DataLoader


class TestDataLoader(unittest.TestCase):
    """Test DataLoader class functionality."""
    
    def setUp(self):
        """Set up test data directory with mock files."""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create mock gamemaster data
        self.gamemaster_data = {
            "pokemon": [
                {"speciesId": "azumarill", "speciesName": "Azumarill"},
                {"speciesId": "medicham", "speciesName": "Medicham"}
            ],
            "moves": [
                {"moveId": "BUBBLE", "name": "Bubble"},
                {"moveId": "COUNTER", "name": "Counter"}
            ],
            "formats": [
                {"name": "Great League", "cp": 1500},
                {"name": "Ultra League", "cp": 2500}
            ]
        }
        
        # Create mock rankings data
        self.rankings_data = [
            {"speciesId": "azumarill", "score": 95.5, "rating": 1000},
            {"speciesId": "medicham", "score": 94.2, "rating": 980},
            {"speciesId": "skarmory", "score": 93.1, "rating": 960}
        ]
        
        # Create mock groups data
        self.starters_data = ["bulbasaur", "charmander", "squirtle"]
        self.legendaries_data = ["mewtwo", "lugia", "hooh"]
        
        # Write gamemaster file
        with open(self.test_path / "gamemaster.json", 'w') as f:
            json.dump(self.gamemaster_data, f)
        
        # Create rankings directory structure
        rankings_dir = self.test_path / "rankings" / "all" / "overall"
        rankings_dir.mkdir(parents=True)
        
        # Write rankings files
        with open(rankings_dir / "rankings-1500.json", 'w') as f:
            json.dump(self.rankings_data, f)
        
        with open(rankings_dir / "rankings-2500.json", 'w') as f:
            json.dump(self.rankings_data[:2], f)  # Less Pokemon for Ultra
        
        with open(rankings_dir / "rankings-10000.json", 'w') as f:
            json.dump(self.rankings_data[:1], f)  # Even less for Master
        
        # Create groups directory
        groups_dir = self.test_path / "groups"
        groups_dir.mkdir()
        
        # Write group files
        with open(groups_dir / "starters.json", 'w') as f:
            json.dump(self.starters_data, f)
        
        with open(groups_dir / "legendaries.json", 'w') as f:
            json.dump(self.legendaries_data, f)
        
        # Initialize DataLoader with test directory
        self.loader = DataLoader(data_dir=self.test_path)
    
    def tearDown(self):
        """Clean up test directory."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_data_loader_initialization(self):
        """Test DataLoader initializes correctly."""
        self.assertEqual(self.loader.data_dir, self.test_path)
        self.assertTrue(self.loader.data_dir.exists())
    
    def test_data_loader_invalid_directory(self):
        """Test DataLoader with invalid directory."""
        with self.assertRaises(ValueError):
            DataLoader(data_dir="/nonexistent/directory")
    
    def test_load_json_basic(self):
        """Test loading a JSON file."""
        data = self.loader.load_json("gamemaster.json")
        
        self.assertIsInstance(data, dict)
        self.assertIn("pokemon", data)
        self.assertIn("moves", data)
        self.assertEqual(len(data["pokemon"]), 2)
    
    def test_load_json_nested_path(self):
        """Test loading JSON from nested path."""
        data = self.loader.load_json("rankings/all/overall/rankings-1500.json")
        
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["speciesId"], "azumarill")
    
    def test_load_json_nonexistent_file(self):
        """Test loading nonexistent JSON file."""
        with self.assertRaises(FileNotFoundError):
            self.loader.load_json("nonexistent.json")
    
    def test_load_gamemaster(self):
        """Test loading gamemaster file."""
        data = self.loader.load_gamemaster()
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data, self.gamemaster_data)
    
    def test_load_gamemaster_minified_fallback(self):
        """Test fallback to minified gamemaster."""
        # Remove regular gamemaster
        (self.test_path / "gamemaster.json").unlink()
        
        # Create minified version
        with open(self.test_path / "gamemaster.min.json", 'w') as f:
            json.dump(self.gamemaster_data, f)
        
        # Should load minified version
        data = self.loader.load_gamemaster()
        self.assertEqual(data, self.gamemaster_data)
    
    def test_load_rankings_default(self):
        """Test loading rankings with default parameters."""
        rankings = self.loader.load_rankings()
        
        self.assertIsInstance(rankings, list)
        self.assertEqual(len(rankings), 3)
        self.assertEqual(rankings[0]["speciesId"], "azumarill")
    
    def test_load_rankings_different_leagues(self):
        """Test loading rankings for different leagues."""
        # Great League
        great = self.loader.load_rankings(league="all", cp=1500)
        self.assertEqual(len(great), 3)
        
        # Ultra League
        ultra = self.loader.load_rankings(league="all", cp=2500)
        self.assertEqual(len(ultra), 2)
        
        # Master League
        master = self.loader.load_rankings(league="all", cp=10000)
        self.assertEqual(len(master), 1)
    
    def test_load_rankings_different_categories(self):
        """Test loading rankings for different categories."""
        # Create additional category directories
        leads_dir = self.test_path / "rankings" / "all" / "leads"
        leads_dir.mkdir(parents=True)
        
        leads_data = [{"speciesId": "medicham", "score": 96.0}]
        with open(leads_dir / "rankings-1500.json", 'w') as f:
            json.dump(leads_data, f)
        
        # Load different categories
        overall = self.loader.load_rankings(category="overall")
        self.assertEqual(len(overall), 3)
        
        leads = self.loader.load_rankings(category="leads")
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["speciesId"], "medicham")
    
    def test_load_rankings_nonexistent(self):
        """Test loading nonexistent rankings."""
        rankings = self.loader.load_rankings(league="nonexistent", cp=9999)
        
        # Should return empty list
        self.assertEqual(rankings, [])
    
    def test_load_formats(self):
        """Test loading battle formats."""
        formats = self.loader.load_formats()
        
        self.assertIsInstance(formats, list)
        self.assertEqual(len(formats), 2)
        self.assertEqual(formats[0]["name"], "Great League")
        self.assertEqual(formats[0]["cp"], 1500)
    
    def test_load_groups(self):
        """Test loading Pokemon groups."""
        groups = self.loader.load_groups()
        
        self.assertIsInstance(groups, dict)
        self.assertEqual(len(groups), 2)
        
        # Check starters group
        self.assertIn("starters", groups)
        self.assertEqual(len(groups["starters"]), 3)
        self.assertIn("bulbasaur", groups["starters"])
        
        # Check legendaries group
        self.assertIn("legendaries", groups)
        self.assertEqual(len(groups["legendaries"]), 3)
        self.assertIn("mewtwo", groups["legendaries"])
    
    def test_load_groups_empty_directory(self):
        """Test loading groups from empty directory."""
        # Remove groups directory
        import shutil
        shutil.rmtree(self.test_path / "groups")
        
        groups = self.loader.load_groups()
        
        # Should return empty dict
        self.assertEqual(groups, {})
    
    def test_get_great_league_meta(self):
        """Test getting Great League meta Pokemon."""
        meta = self.loader.get_great_league_meta(top_n=2)
        
        self.assertIsInstance(meta, list)
        self.assertEqual(len(meta), 2)
        self.assertEqual(meta[0]["speciesId"], "azumarill")
        self.assertEqual(meta[1]["speciesId"], "medicham")
    
    def test_get_ultra_league_meta(self):
        """Test getting Ultra League meta Pokemon."""
        meta = self.loader.get_ultra_league_meta(top_n=5)
        
        self.assertIsInstance(meta, list)
        # Should return only available Pokemon (2 in our test data)
        self.assertEqual(len(meta), 2)
    
    def test_get_master_league_meta(self):
        """Test getting Master League meta Pokemon."""
        meta = self.loader.get_master_league_meta(top_n=10)
        
        self.assertIsInstance(meta, list)
        # Should return only available Pokemon (1 in our test data)
        self.assertEqual(len(meta), 1)
        self.assertEqual(meta[0]["speciesId"], "azumarill")
    
    def test_save_json(self):
        """Test saving data to JSON file."""
        test_data = {"test": "data", "value": 42}
        
        # Save to new file
        self.loader.save_json(test_data, "test_output.json")
        
        # Check file was created
        output_path = self.test_path / "test_output.json"
        self.assertTrue(output_path.exists())
        
        # Load and verify content
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, test_data)
    
    def test_save_json_nested_path(self):
        """Test saving JSON to nested path."""
        test_data = {"nested": "test"}
        
        # Save to nested path
        self.loader.save_json(test_data, "output/nested/test.json")
        
        # Check file and directories were created
        output_path = self.test_path / "output" / "nested" / "test.json"
        self.assertTrue(output_path.exists())
        
        # Verify content
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, test_data)
    
    def test_save_json_overwrite(self):
        """Test overwriting existing JSON file."""
        # Create initial file
        initial_data = {"version": 1}
        self.loader.save_json(initial_data, "overwrite_test.json")
        
        # Overwrite with new data
        new_data = {"version": 2, "updated": True}
        self.loader.save_json(new_data, "overwrite_test.json")
        
        # Load and verify new content
        output_path = self.test_path / "overwrite_test.json"
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, new_data)
        self.assertEqual(loaded_data["version"], 2)
    
    def test_default_data_directory(self):
        """Test DataLoader with default data directory."""
        # This will use the actual src/data directory if it exists
        # We'll just test that it initializes without error
        try:
            loader = DataLoader()
            # If successful, check that data_dir is set
            self.assertIsNotNone(loader.data_dir)
            self.assertTrue(loader.data_dir.is_absolute())
        except ValueError:
            # If src/data doesn't exist, that's fine for testing
            pass
    
    def test_load_json_with_encoding(self):
        """Test loading JSON with special characters."""
        # Create file with special characters
        special_data = {
            "name": "Pokémon",
            "description": "Special chars: ñ, ü, é, 中文",
            "emoji": "⚡️🔥💧"
        }
        
        special_path = self.test_path / "special.json"
        with open(special_path, 'w', encoding='utf-8') as f:
            json.dump(special_data, f, ensure_ascii=False)
        
        # Load and verify
        loaded = self.loader.load_json("special.json")
        
        self.assertEqual(loaded["name"], "Pokémon")
        self.assertIn("ñ", loaded["description"])
        self.assertIn("⚡️", loaded["emoji"])


if __name__ == "__main__":
    unittest.main()
