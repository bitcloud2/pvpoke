# PvPoke Python

A Python implementation of the PvPoke.com Pokemon GO PvP battle simulator.

## Overview

This is a Python port of the JavaScript/PHP PvPoke battle simulator, providing:
- Battle simulation between Pokemon
- Damage calculations
- CP optimization for leagues
- Ranking analysis
- Great/Ultra/Master League support

## Project Structure

```
python/
├── pvpoke/              # Main package
│   ├── core/           # Core data models (Pokemon, Moves, GameMaster)
│   ├── battle/         # Battle engine and AI
│   ├── rankings/       # Ranking calculation system
│   └── utils/          # Utilities (data loading, CP calculator)
├── tests/              # Unit tests
├── examples/           # Example usage scripts
└── requirements.txt    # Python dependencies
```

## Installation

The package uses only Python standard library for core functionality:

```bash
cd python
pip install -e .
```

## Quick Start

### Load Pokemon Data

```python
from pvpoke.core import GameMaster

gm = GameMaster()
pokemon = gm.get_pokemon("azumarill")
```

### Optimize for Great League

```python
pokemon.optimize_for_league(1500)  # Find best IVs for 1500 CP
print(f"Best IVs: {pokemon.ivs}")
print(f"Level: {pokemon.level}")
print(f"CP: {pokemon.cp}")
```

### Run a Battle

```python
from pvpoke.battle import Battle

# Set up two Pokemon
azumarill = gm.get_pokemon("azumarill")
stunfisk = gm.get_pokemon("stunfisk_galarian")

# Set moves
azumarill.fast_move = gm.get_fast_move("BUBBLE")
azumarill.charged_move_1 = gm.get_charged_move("ICE_BEAM")

stunfisk.fast_move = gm.get_fast_move("MUD_SHOT")
stunfisk.charged_move_1 = gm.get_charged_move("ROCK_SLIDE")

# Battle!
battle = Battle(azumarill, stunfisk)
result = battle.simulate()

print(f"Winner: Pokemon {result.winner + 1}")
print(f"Final HP: {result.pokemon1_hp} vs {result.pokemon2_hp}")
```

### Check Great League Rankings

```python
from pvpoke.utils import DataLoader

loader = DataLoader()
rankings = loader.get_great_league_meta(top_n=10)

for i, entry in enumerate(rankings, 1):
    print(f"{i}. {entry['speciesName']} - Score: {entry.get('score', 0)}")
```

## Examples

See the `examples/` directory for complete examples:
- `simple_battle.py` - Basic battle between two Pokemon
- `great_league_rankings.py` - Display and analyze Great League meta

Run examples:
```bash
python examples/simple_battle.py
python examples/great_league_rankings.py
```

## Current Features

### Implemented
- Pokemon data model with stats, IVs, and CP calculation
- Move system (Fast and Charged moves)
- Type effectiveness chart
- Basic battle simulation
- Damage calculations
- CP optimization for leagues
- Data loading from existing JSON files
- Great League ranking analysis

### In Progress
- Full battle AI logic
- Shield decision making
- Advanced battle mechanics (buffs/debuffs, switching)
- Ranking calculation system
- Team composition analysis

## Differences from JavaScript Version

This Python port aims to:
1. Maintain compatibility with existing data formats
2. Provide a cleaner, more Pythonic API
3. Enable easier data analysis and scripting
4. Support batch simulations and analysis

## Testing

Run tests (once implemented):
```bash
python -m pytest tests/
```

## Data Files

This implementation reads from the existing PvPoke data files in `src/data/`:
- `gamemaster.json` - Pokemon and move data
- `rankings/` - Pre-calculated rankings
- `formats.json` - League/cup definitions

## Contributing

This is a work in progress. Key areas for contribution:
1. Completing the battle AI port from JavaScript
2. Implementing the ranking calculation system
3. Adding more battle mechanics
4. Writing comprehensive tests
5. Performance optimizations

## License

Same as the main PvPoke project.
