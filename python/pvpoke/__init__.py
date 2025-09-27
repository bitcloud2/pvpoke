"""
PvPoke Python - Pokemon GO PvP Battle Simulator
A Python port of the PvPoke.com battle simulator

This package provides a Python implementation of the PvPoke battle simulator,
including battle mechanics, damage calculations, and ranking systems for
Pokemon GO PvP battles.
"""

__version__ = "0.1.0"
__author__ = "PvPoke Python Port"
__all__ = ["core", "battle", "rankings", "utils"]

# Core imports for convenience
from pvpoke.core.pokemon import Pokemon
from pvpoke.core.moves import Move, FastMove, ChargedMove
from pvpoke.battle.battle import Battle
from pvpoke.utils.data_loader import DataLoader
