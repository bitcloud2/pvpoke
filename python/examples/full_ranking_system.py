#!/usr/bin/env python3
"""
Example demonstrating the complete ranking system.

This example shows how to use the full PvPoke ranking algorithm
to generate rankings for different scenarios and overall rankings.
"""

import sys
import os
import json
from typing import List, Dict

# Add the parent directory to the path so we can import pvpoke
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pvpoke.core.pokemon import Pokemon
from pvpoke.core.gamemaster import GameMaster
from pvpoke.rankings import Ranker, RankingScenario, OverallRanker, TeamRanker
from pvpoke.utils.cp_calculator import CPCalculator


def load_sample_pokemon(gm: GameMaster, cp_limit: int = 1500) -> List[Pokemon]:
    """Load a sample set of Pokemon for ranking."""
    
    # Sample of popular Great League Pokemon
    sample_species = [
        "altaria", "azumarill", "registeel", "cresselia", "medicham",
        "bastiodon", "swampert", "venusaur", "charizard", "meganium",
        "skarmory", "tropius", "whiscash", "lanturn", "umbreon",
        "hypno", "deoxys_defense", "stunfisk_galarian", "talonflame", "noctowl"
    ]
    
    pokemon_list = []
    cp_calc = CPCalculator()
    
    for species_id in sample_species:
        try:
            # Create Pokemon with optimal IVs for the CP limit
            pokemon = Pokemon(species_id, cp_limit)
            
            # Initialize with gamemaster data
            if pokemon.initialize(gm):
                # Set optimal IVs for the league
                optimal_ivs = cp_calc.get_optimal_ivs(pokemon.base_stats, cp_limit)
                pokemon.set_ivs(optimal_ivs["attack"], optimal_ivs["defense"], optimal_ivs["stamina"])
                
                # Auto-select best moves (simplified)
                if pokemon.fast_moves:
                    pokemon.select_move("fast", pokemon.fast_moves[0].move_id)
                if pokemon.charged_moves:
                    pokemon.select_move("charged", pokemon.charged_moves[0].move_id, 0)
                    if len(pokemon.charged_moves) > 1:
                        pokemon.select_move("charged", pokemon.charged_moves[1].move_id, 1)
                
                pokemon_list.append(pokemon)
                print(f"Loaded {pokemon.species_name}")
            else:
                print(f"Failed to initialize {species_id}")
                
        except Exception as e:
            print(f"Error loading {species_id}: {e}")
    
    return pokemon_list


def run_scenario_rankings(ranker: Ranker, pokemon_list: List[Pokemon]) -> Dict[str, List[Dict]]:
    """Run rankings for all scenarios."""
    
    print("\\n=== Running Scenario Rankings ===\")\n    \n    # Set up the ranker\n    ranker.set_pokemon_list(pokemon_list)\n    ranker.set_targets(pokemon_list)  # Rank against the same meta\n    ranker.set_iterations(3)  # Use multiple iterations for better accuracy\n    \n    scenario_rankings = {}\n    \n    for scenario in ranker.scenarios:\n        print(f\"Ranking scenario: {scenario.slug}\")\n        \n        # Rank this scenario\n        rankings = ranker.rank_scenario(scenario)\n        scenario_rankings[scenario.slug] = rankings\n        \n        # Show top 5 for this scenario\n        print(f\"Top 5 {scenario.slug}:\")\n        for i, ranking in enumerate(rankings[:5]):\n            print(f\"  {i+1}. {ranking['speciesName']} - Score: {ranking['score']:.1f}\")\n        print()\n    \n    return scenario_rankings\n\n\ndef run_overall_rankings(overall_ranker: OverallRanker, \n                        scenario_rankings: Dict[str, List[Dict]],\n                        pokemon_list: List[Pokemon]) -> List[Dict]:\n    \"\"\"Generate overall rankings from scenario rankings.\"\"\"\n    \n    print(\"\\n=== Generating Overall Rankings ===\")\n    \n    # Generate overall rankings\n    overall_rankings = overall_ranker.generate_overall_rankings(\n        scenario_rankings, pokemon_list\n    )\n    \n    print(\"\\nTop 10 Overall Rankings:\")\n    for i, ranking in enumerate(overall_rankings[:10]):\n        print(f\"  {i+1}. {ranking['speciesName']} - Score: {ranking['score']:.1f}\")\n        \n        # Show category breakdown\n        if 'scores' in ranking:\n            category_names = [\"leads\", \"closers\", \"switches\", \"chargers\", \"attackers\"]\n            category_scores = [f\"{score:.1f}\" for score in ranking['scores']]\n            print(f\"      Categories: {dict(zip(category_names, category_scores))}\")\n    \n    return overall_rankings\n\n\ndef run_team_analysis(team_ranker: TeamRanker, pokemon_list: List[Pokemon]):\n    \"\"\"Demonstrate team ranking and analysis.\"\"\"\n    \n    print(\"\\n=== Team Analysis ===\")\n    \n    # Create a sample team (top 3 from overall)\n    sample_team = pokemon_list[:3]\n    print(f\"\\nAnalyzing team: {[p.species_name for p in sample_team]}\")\n    \n    # Rank the team\n    team_results = team_ranker.rank_team(sample_team, pokemon_list)\n    \n    print(\"\\nTeam Member Performance:\")\n    for ranking in team_results[\"rankings\"]:\n        print(f\"  {ranking['speciesName']}: Score {ranking['score']:.1f}, Rating {ranking['rating']}\")\n    \n    print(f\"\\nTeam Coverage: {team_results['coverage']['coverage_percent']:.1f}%\")\n    print(f\"Safe Switches: {team_results['coverage']['safe_switch_percent']:.1f}%\")\n    \n    if team_results['coverage']['top_threats']:\n        print(\"\\nTop Threats:\")\n        for threat in team_results['coverage']['top_threats'][:3]:\n            print(f\"  {threat['species']}: Best matchup {threat['best_matchup']}\")\n    \n    # Analyze team synergy\n    synergy = team_ranker.analyze_team_synergy(sample_team)\n    print(f\"\\nTeam Synergy:\")\n    print(f\"  Type diversity: {synergy['type_diversity']} types\")\n    print(f\"  Balance score: {synergy['balance_score']}\")\n    \n    # Suggest a teammate for a 2-Pokemon team\n    if len(pokemon_list) > 3:\n        print(\"\\n=== Teammate Suggestions ===\")\n        partial_team = sample_team[:2]\n        candidates = pokemon_list[3:]  # Exclude the first 3\n        \n        suggestions = team_ranker.suggest_teammate(partial_team, candidates, pokemon_list)\n        \n        print(f\"\\nBest teammates for {[p.species_name for p in partial_team]}:\")\n        for i, (pokemon, score) in enumerate(suggestions[:5]):\n            print(f\"  {i+1}. {pokemon.species_name} - Improvement: {score:.1f}\")\n\n\ndef save_rankings_to_json(rankings: Dict, filename: str):\n    \"\"\"Save rankings to JSON file.\"\"\"\n    \n    # Convert to JSON-serializable format\n    json_data = {}\n    \n    for category, ranking_list in rankings.items():\n        json_data[category] = []\n        for ranking in ranking_list:\n            # Create a clean dictionary for JSON\n            clean_ranking = {\n                \"speciesId\": ranking[\"speciesId\"],\n                \"speciesName\": ranking[\"speciesName\"],\n                \"score\": ranking[\"score\"]\n            }\n            \n            # Add additional fields if present\n            for field in [\"scores\", \"scenario_scores\", \"stats\", \"moveset\"]:\n                if field in ranking:\n                    clean_ranking[field] = ranking[field]\n            \n            json_data[category].append(clean_ranking)\n    \n    with open(filename, 'w') as f:\n        json.dump(json_data, f, indent=2)\n    \n    print(f\"\\nRankings saved to {filename}\")\n\n\ndef main():\n    \"\"\"Main function demonstrating the complete ranking system.\"\"\"\n    \n    print(\"PvPoke Python - Complete Ranking System Demo\")\n    print(\"=\" * 50)\n    \n    # Initialize GameMaster\n    print(\"Loading GameMaster data...\")\n    gm = GameMaster()\n    \n    # For this demo, we'll use a simplified data structure\n    # In a real implementation, this would load from gamemaster.json\n    print(\"Note: Using simplified demo data\")\n    \n    # Load sample Pokemon\n    print(\"\\nLoading sample Pokemon...\")\n    pokemon_list = load_sample_pokemon(gm, cp_limit=1500)\n    \n    if not pokemon_list:\n        print(\"No Pokemon loaded. Cannot proceed with ranking.\")\n        return\n    \n    print(f\"Loaded {len(pokemon_list)} Pokemon for ranking\")\n    \n    # Initialize rankers\n    ranker = Ranker(cp_limit=1500)\n    overall_ranker = OverallRanker()\n    team_ranker = TeamRanker(cp_limit=1500)\n    \n    # Run scenario rankings\n    scenario_rankings = run_scenario_rankings(ranker, pokemon_list)\n    \n    # Generate overall rankings\n    overall_rankings = run_overall_rankings(overall_ranker, scenario_rankings, pokemon_list)\n    \n    # Add overall rankings to the results\n    all_rankings = scenario_rankings.copy()\n    all_rankings[\"overall\"] = overall_rankings\n    \n    # Run team analysis\n    run_team_analysis(team_ranker, pokemon_list)\n    \n    # Save results\n    save_rankings_to_json(all_rankings, \"sample_rankings.json\")\n    \n    print(\"\\n=== Ranking System Demo Complete ===\")\n    print(\"\\nThis demo shows the complete PvPoke ranking algorithm:\")\n    print(\"- Individual scenario rankings (leads, closers, switches, chargers, attackers)\")\n    print(\"- Weighted iterative algorithm for meta relevance\")\n    print(\"- Overall rankings using geometric mean\")\n    print(\"- Team analysis and synergy calculation\")\n    print(\"- Teammate suggestions\")\n    print(\"\\nThe Python implementation now matches the JavaScript algorithm!\")\n\n\nif __name__ == \"__main__\":\n    main()
