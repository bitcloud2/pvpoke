"""
Demonstration of the DecisionOption class and choose_option method.

This shows how the AI uses weighted decision making to select actions
during battle simulations.
"""

from pvpoke.battle.ai import ActionLogic, DecisionOption
from pvpoke.core.moves import ChargedMove


def demo_basic_decision_option():
    """Demonstrate basic DecisionOption creation and usage."""
    print("=" * 60)
    print("DecisionOption Class Demonstration")
    print("=" * 60)
    
    # Create some decision options
    options = [
        DecisionOption("CHARGED_MOVE_0", 40),  # 40% weight
        DecisionOption("CHARGED_MOVE_1", 30),  # 30% weight
        DecisionOption("FAST_MOVE", 20),       # 20% weight
        DecisionOption("WAIT", 10),            # 10% weight
    ]
    
    print("\nCreated decision options:")
    for opt in options:
        print(f"  - {opt.name}: weight={opt.weight}")
    
    # Simulate multiple choices to show distribution
    print("\nSimulating 1000 random choices:")
    choice_counts = {opt.name: 0 for opt in options}
    
    for _ in range(1000):
        chosen = ActionLogic.choose_option(options)
        choice_counts[chosen.name] += 1
    
    print("\nResults (should approximate the weights):")
    for name, count in choice_counts.items():
        percentage = (count / 1000) * 100
        print(f"  - {name}: {count} times ({percentage:.1f}%)")


def demo_lethal_move_detection():
    """Demonstrate DecisionOption with move references for lethal detection."""
    print("\n" + "=" * 60)
    print("DecisionOption with Move References")
    print("=" * 60)
    
    # Create mock moves
    lethal_move = ChargedMove(
        move_id="HYDRO_CANNON",
        name="Hydro Cannon",
        move_type="water",
        power=80,
        energy_cost=40,
        buffs=[1.0, 1.0],
        buff_chance=0.0,
        buff_target="self"
    )
    
    normal_move = ChargedMove(
        move_id="SURF",
        name="Surf",
        move_type="water",
        power=65,
        energy_cost=40,
        buffs=[1.0, 1.0],
        buff_chance=0.0,
        buff_target="self"
    )
    
    # Create decision options with move references
    options = [
        DecisionOption("CHARGED_MOVE_0", 10, lethal_move),
        DecisionOption("CHARGED_MOVE_1", 10, normal_move),
        DecisionOption("FAST_MOVE", 10, None)
    ]
    
    print("\nCreated decision options with move references:")
    for opt in options:
        move_info = f"({opt.move.name})" if opt.move else "(no move)"
        print(f"  - {opt.name}: weight={opt.weight} {move_info}")
    
    print("\nThe AI can now boost weights of lethal moves during decision making!")
    print("This enables smarter KO detection and prioritization.")


def demo_zero_weight_handling():
    """Demonstrate how zero-weight options are handled."""
    print("\n" + "=" * 60)
    print("Zero Weight Handling")
    print("=" * 60)
    
    # Create options with all zero weights
    options = [
        DecisionOption("OPTION_A", 0),
        DecisionOption("OPTION_B", 0),
        DecisionOption("OPTION_C", 0),
    ]
    
    print("\nCreated options with all zero weights:")
    for opt in options:
        print(f"  - {opt.name}: weight={opt.weight}")
    
    print("\nWhen all weights are zero, the first option is chosen:")
    chosen = ActionLogic.choose_option(options)
    print(f"  Chosen: {chosen.name}")
    print("\nThis prevents the AI from getting stuck when no good options exist.")


if __name__ == "__main__":
    demo_basic_decision_option()
    demo_lethal_move_detection()
    demo_zero_weight_handling()
    
    print("\n" + "=" * 60)
    print("✅ DecisionOption class is fully functional!")
    print("=" * 60)
