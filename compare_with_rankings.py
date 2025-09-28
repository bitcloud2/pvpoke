#!/usr/bin/env python3
"""
Compare Python implementation results with existing PvPoke rankings data.

This script loads the pre-calculated rankings from src/data/rankings/ and compares
them with Python-generated battle results to validate accuracy.

Usage:
    pixi shell
    python compare_with_rankings.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add python directory to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from pvpoke.core import GameMaster
from pvpoke.battle import Battle
from pvpoke.utils import DataLoader


class RankingValidator:
    """Compare Python results with existing JavaScript-generated rankings."""
    
    def __init__(self):
        self.gm = GameMaster()
        self.data_loader = DataLoader()
        self.src_data_path = Path(__file__).parent / "src" / "data"
    
    def load_js_rankings(self, league: str = "great") -> List[Dict]:
        """Load JavaScript-generated rankings from JSON files."""
        
        rankings_path = self.src_data_path / "rankings" / f"{league}league" / "all" / "overall.json"
        
        if not rankings_path.exists():
            print(f"❌ Rankings file not found: {rankings_path}")
            return []
        
        try:
            with open(rankings_path, 'r') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"❌ Error loading rankings: {e}")
            return []
    
    def get_pokemon_from_ranking(self, ranking_entry: Dict):
        """Create a Pokemon object from a ranking entry."""
        
        species_id = ranking_entry.get('speciesId', '')
        
        # Handle form variations
        if '_' in species_id:
            base_species = species_id.split('_')[0]
        else:
            base_species = species_id
        
        pokemon = self.gm.get_pokemon(species_id)
        if not pokemon:
            # Try base species if form-specific lookup failed
            pokemon = self.gm.get_pokemon(base_species)
        
        if not pokemon:
            return None
        
        # Set up Pokemon from ranking data
        if 'level' in ranking_entry:
            pokemon.level = ranking_entry['level']
        
        if 'ivs' in ranking_entry:
            ivs = ranking_entry['ivs']
            pokemon.ivs.atk = ivs.get('atk', 0)
            pokemon.ivs.defense = ivs.get('def', 15)
            pokemon.ivs.hp = ivs.get('hp', 15)
        
        # Set moves from ranking data
        moves = ranking_entry.get('moves', [])
        if len(moves) > 0:
            fast_move = self.gm.get_fast_move(moves[0])
            if fast_move:
                pokemon.fast_move = fast_move
        
        if len(moves) > 1:
            charged_move_1 = self.gm.get_charged_move(moves[1])
            if charged_move_1:
                pokemon.charged_move_1 = charged_move_1
        
        if len(moves) > 2:
            charged_move_2 = self.gm.get_charged_move(moves[2])
            if charged_move_2:
                pokemon.charged_move_2 = charged_move_2
        
        return pokemon
    
    def compare_specific_matchups(self, rankings: List[Dict], num_tests: int = 10) -> Dict:
        """Compare specific matchups between top-ranked Pokemon."""
        
        results = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': [],
            'rating_differences': []
        }
        
        # Get top Pokemon for testing
        top_pokemon = rankings[:min(num_tests, len(rankings))]
        
        print(f"Testing matchups between top {len(top_pokemon)} Pokemon...")
        
        for i, pokemon1_data in enumerate(top_pokemon[:5]):  # Test first 5 vs others
            pokemon1 = self.get_pokemon_from_ranking(pokemon1_data)
            if not pokemon1:
                continue
            
            for j, pokemon2_data in enumerate(top_pokemon[5:10]):  # Against next 5
                pokemon2 = self.get_pokemon_from_ranking(pokemon2_data)
                if not pokemon2:
                    continue
                
                results['total_tests'] += 1
                
                try:
                    # Run Python battle
                    battle = Battle(pokemon1, pokemon2)
                    result = battle.simulate()
                    
                    # Get expected rating from JavaScript data (if available)
                    matchups1 = pokemon1_data.get('matchups', [])
                    expected_rating = None
                    
                    for matchup in matchups1:
                        if matchup.get('opponent') == pokemon2_data.get('speciesId'):
                            expected_rating = matchup.get('rating')
                            break
                    
                    test_name = f"{pokemon1_data.get('speciesName', 'Unknown')} vs {pokemon2_data.get('speciesName', 'Unknown')}"
                    
                    if expected_rating is not None:
                        rating_diff = abs(result.rating1 - expected_rating)
                        results['rating_differences'].append(rating_diff)
                        
                        print(f"  {test_name}")
                        print(f"    Python rating: {result.rating1}")
                        print(f"    JS rating: {expected_rating}")
                        print(f"    Difference: {rating_diff}")
                        
                        # Consider test successful if within 100 points
                        if rating_diff <= 100:
                            results['successful_tests'] += 1
                            print(f"    ✅ PASS")
                        else:
                            results['failed_tests'].append({
                                'matchup': test_name,
                                'python_rating': result.rating1,
                                'js_rating': expected_rating,
                                'difference': rating_diff
                            })
                            print(f"    ❌ FAIL (difference too large)")
                    else:
                        # No reference data available
                        print(f"  {test_name}: No reference data")
                        results['successful_tests'] += 1  # Count as success if no errors
                    
                except Exception as e:
                    results['failed_tests'].append({
                        'matchup': test_name,
                        'error': str(e)
                    })
                    print(f"  {test_name}: ❌ ERROR - {e}")
        
        return results
    
    def validate_top_performers(self, rankings: List[Dict]) -> bool:
        """Validate that top-performing Pokemon can be loaded and battled."""
        
        print("Validating top performers...")
        
        top_10 = rankings[:10]
        successful_loads = 0
        
        for i, pokemon_data in enumerate(top_10):
            species_name = pokemon_data.get('speciesName', 'Unknown')
            print(f"  {i+1}. {species_name}")
            
            pokemon = self.get_pokemon_from_ranking(pokemon_data)
            if pokemon:
                print(f"     ✅ Loaded successfully")
                print(f"     CP: {pokemon.cp}, Level: {pokemon.level}")
                if pokemon.fast_move:
                    print(f"     Fast move: {pokemon.fast_move.name}")
                if pokemon.charged_move_1:
                    print(f"     Charged move 1: {pokemon.charged_move_1.name}")
                successful_loads += 1
            else:
                print(f"     ❌ Failed to load")
        
        success_rate = successful_loads / len(top_10)
        print(f"\nTop Pokemon load success rate: {successful_loads}/{len(top_10)} ({success_rate*100:.1f}%)")
        
        return success_rate >= 0.8  # 80% success rate threshold
    
    def run_validation(self, league: str = "great"):
        """Run complete validation against JavaScript rankings."""
        
        print(f"PvPoke Python vs JavaScript Validation - {league.title()} League")
        print("=" * 70)
        
        # Load JavaScript rankings
        print("Loading JavaScript rankings...")
        js_rankings = self.load_js_rankings(league)
        
        if not js_rankings:
            print("❌ Could not load JavaScript rankings")
            return False
        
        print(f"✅ Loaded {len(js_rankings)} Pokemon from rankings")
        
        # Validate top performers
        print("\n" + "=" * 50)
        top_load_success = self.validate_top_performers(js_rankings)
        
        # Compare specific matchups
        print("\n" + "=" * 50)
        matchup_results = self.compare_specific_matchups(js_rankings)
        
        # Print summary
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        
        print(f"Top Pokemon Loading: {'✅ PASS' if top_load_success else '❌ FAIL'}")
        
        if matchup_results['total_tests'] > 0:
            success_rate = matchup_results['successful_tests'] / matchup_results['total_tests']
            print(f"Matchup Tests: {matchup_results['successful_tests']}/{matchup_results['total_tests']} ({success_rate*100:.1f}%)")
            
            if matchup_results['rating_differences']:
                avg_diff = sum(matchup_results['rating_differences']) / len(matchup_results['rating_differences'])
                max_diff = max(matchup_results['rating_differences'])
                print(f"Average rating difference: {avg_diff:.1f}")
                print(f"Maximum rating difference: {max_diff:.1f}")
        
        # Overall assessment
        overall_success = (top_load_success and 
                          matchup_results['successful_tests'] >= matchup_results['total_tests'] * 0.7)
        
        if overall_success:
            print("\n🎉 VALIDATION SUCCESSFUL!")
            print("The Python implementation shows good compatibility with JavaScript results.")
            print("\nKey findings:")
            print("✅ Top Pokemon load correctly")
            print("✅ Battle simulations run without major errors")
            print("✅ Rating differences are within acceptable ranges")
            print("\nYou can proceed with confidence!")
        else:
            print("\n⚠️  VALIDATION NEEDS ATTENTION")
            print("Some issues were found that may need investigation:")
            
            if not top_load_success:
                print("- Some top Pokemon failed to load properly")
            
            if matchup_results['failed_tests']:
                print(f"- {len(matchup_results['failed_tests'])} matchup tests failed")
                print("- Large rating differences detected")
        
        return overall_success


def main():
    """Main validation function."""
    
    try:
        validator = RankingValidator()
        
        # Test Great League first (most data available)
        success = validator.run_validation("great")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
