"""Data loading utilities."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class DataLoader:
    """
    Utility class for loading game data files.
    Provides easy access to rankings, game master data, and other JSON files.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize DataLoader.
        
        Args:
            data_dir: Path to data directory. If None, uses default src/data location.
        """
        if data_dir is None:
            # Default to src/data directory relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            data_dir = project_root / "src" / "data"
        
        self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise ValueError(f"Data directory not found: {self.data_dir}")
    
    def load_json(self, file_path: str) -> Dict:
        """
        Load a JSON file.
        
        Args:
            file_path: Path to JSON file relative to data directory
            
        Returns:
            Parsed JSON data
        """
        full_path = self.data_dir / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        
        with open(full_path, 'r') as f:
            return json.load(f)
    
    def load_gamemaster(self) -> Dict:
        """Load the main gamemaster.json file."""
        try:
            return self.load_json("gamemaster.json")
        except FileNotFoundError:
            # Try minified version
            return self.load_json("gamemaster.min.json")
    
    def load_rankings(self, league: str = "all", cp: int = 1500,
                     category: str = "overall") -> List[Dict]:
        """
        Load Pokemon rankings.
        
        Args:
            league: League/cup name (e.g., "all", "premier", "classic")
            cp: CP limit (500, 1500, 2500, 10000)
            category: Ranking category (overall, leads, closers, switches, etc.)
            
        Returns:
            List of ranking entries
        """
        path = f"rankings/{league}/{category}/rankings-{cp}.json"
        
        try:
            return self.load_json(path)
        except FileNotFoundError:
            print(f"Rankings not found: {path}")
            return []
    
    def load_formats(self) -> List[Dict]:
        """Load available battle formats/cups."""
        try:
            # Formats are embedded in gamemaster
            gm = self.load_gamemaster()
            return gm.get("formats", [])
        except:
            return []
    
    def load_groups(self) -> Dict[str, List]:
        """Load Pokemon groups (e.g., starters, legendaries)."""
        groups = {}
        groups_dir = self.data_dir / "groups"
        
        if groups_dir.exists():
            for file_path in groups_dir.glob("*.json"):
                group_name = file_path.stem
                with open(file_path, 'r') as f:
                    groups[group_name] = json.load(f)
        
        return groups
    
    def get_great_league_meta(self, top_n: int = 30) -> List[Dict]:
        """
        Get top meta Pokemon for Great League.
        
        Args:
            top_n: Number of top Pokemon to return
            
        Returns:
            List of top ranked Pokemon
        """
        rankings = self.load_rankings("all", 1500, "overall")
        return rankings[:top_n] if rankings else []
    
    def get_ultra_league_meta(self, top_n: int = 30) -> List[Dict]:
        """
        Get top meta Pokemon for Ultra League.
        
        Args:
            top_n: Number of top Pokemon to return
            
        Returns:
            List of top ranked Pokemon
        """
        rankings = self.load_rankings("all", 2500, "overall")
        return rankings[:top_n] if rankings else []
    
    def get_master_league_meta(self, top_n: int = 30) -> List[Dict]:
        """
        Get top meta Pokemon for Master League.
        
        Args:
            top_n: Number of top Pokemon to return
            
        Returns:
            List of top ranked Pokemon
        """
        rankings = self.load_rankings("all", 10000, "overall")
        return rankings[:top_n] if rankings else []
    
    def save_json(self, data: Any, file_path: str):
        """
        Save data to a JSON file.
        
        Args:
            data: Data to save
            file_path: Path relative to data directory
        """
        full_path = self.data_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            json.dump(data, f, indent=2)
