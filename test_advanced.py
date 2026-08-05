#!/usr/bin/env python3
"""Advanced integration and performance tests for Pokemon game."""

import json
import sys
import time
import os
from pathlib import Path
from typing import List

# Fix encoding for Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / "src"))

# Track test results
test_results: List[dict] = []
start_time = time.time()


def test(name: str, description: str = ""):
    """Decorator for test functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            test_start = time.time()
            status = "PASS"
            error_msg = ""
            try:
                func(*args, **kwargs)
            except AssertionError as e:
                status = "FAIL"
                error_msg = f"Assertion: {str(e)}"
            except Exception as e:
                status = "ERROR"
                error_msg = f"Exception: {type(e).__name__}: {str(e)}"
            
            elapsed = time.time() - test_start
            test_results.append({
                "name": name,
                "description": description,
                "status": status,
                "error": error_msg,
                "time": elapsed
            })
            
            status_icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[ERROR]"
            print(f"\n{status_icon} {name} [{status}] ({elapsed:.2f}s)")
            if error_msg:
                print(f"  {error_msg}")
        
        return wrapper
    return decorator


# ============================================================================
# PHASE 5: INTEGRATION TESTS
# ============================================================================

print("=" * 80)
print("PHASE 5: INTEGRATION TESTS - Map loading and NPC interactions")
print("=" * 80)


@test("INTEG-001", "Load and verify map list")
def test_map_loading():
    """Test map files can be loaded from the assets directory."""
    from pokemon_game.core.tool import ASSETS
    
    map_dir = ASSETS / "map"
    tmx_files = list(map_dir.glob("*.tmx"))
    
    assert len(tmx_files) > 0, "No map files found"
    
    # Check for key maps
    map_names = {f.stem for f in tmx_files}
    required_maps = {"map_0", "house_0"}
    
    for required in required_maps:
        assert required in map_names, f"Missing required map: {required}"
    
    print(f"  Found {len(tmx_files)} map files: {sorted(f.stem for f in tmx_files)[:5]}...")


@test("INTEG-002", "Load multiple Pokemon sequentially")
def test_sequential_pokemon_loads():
    """Test creating multiple Pokemon in sequence."""
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.core.tool import asset_path
    import json
    
    pokemon_names = ["bulbasaur", "charmander", "squirtle"]
    loaded = []
    
    for name in pokemon_names:
        try:
            path = asset_path("json", "pokemon", f"{name}.json")
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            poke = Pokemon(data, 25)
            loaded.append(poke)
        except FileNotFoundError:
            print(f"  [Warning] {name}.json not found")
    
    assert len(loaded) >= 1, "Should load at least one Pokemon"
    print(f"  Loaded {len(loaded)} Pokemon successfully")


@test("INTEG-003", "Test complete battle flow")
def test_battle_flow():
    """Test a complete mock battle sequence."""
    from pokemon_game.systems.battle import Battle, calc_damage
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.entities.move import Move
    from pokemon_game.core.tool import asset_path
    import json
    
    # Create test Pokemon
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    player_poke = Pokemon(data, 50)
    enemy_poke = Pokemon(data, 50)
    
    # Simulate battle turns
    for turn in range(5):
        if player_poke.moves and enemy_poke.hp > 0:
            move = player_poke.moves[0]
            damage, eff, crit = calc_damage(player_poke, enemy_poke, move)
            
            # Apply damage
            old_hp = enemy_poke.hp
            enemy_poke.hp = max(0, enemy_poke.hp - damage)
            
            assert old_hp >= enemy_poke.hp, "HP should decrease after attack"
            assert enemy_poke.hp >= 0, "HP should not go negative"
    
    print(f"  Battle simulation: 5 turns completed, enemy at {enemy_poke.hp}/{enemy_poke.maxhp} HP")


@test("INTEG-004", "Save and load game state")
def test_save_load_cycle():
    """Test save/load serialization cycle."""
    from pokemon_game.systems.inventory import Inventory
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.core.tool import asset_path
    import json
    
    # Create initial state
    inv = Inventory()
    inv.add("potion", 10)
    inv.money = 5000
    
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    poke = Pokemon(data, 50)
    poke.hp = 42
    
    # Serialize
    inv_data = inv.to_dict()
    poke_data = poke.to_dict()
    
    # Deserialize
    inv2 = Inventory.from_dict(inv_data)
    poke2 = Pokemon.from_dict(poke_data)
    
    # Verify
    assert inv2.money == 5000, "Money should match"
    assert inv2.count("potion") == 10, "Potion count should match"
    assert poke2.hp == 42, "Pokemon HP should match"
    assert poke2.level == 50, "Pokemon level should match"
    
    print("  Save/load cycle: OK")


@test("INTEG-005", "Test NPC/Dialogue data loading")
def test_dialogue_loading():
    """Test that dialogue files can be loaded."""
    from pokemon_game.core.tool import ASSETS
    
    dialogue_dir = ASSETS / "dialogues"
    csv_files = list(dialogue_dir.glob("*.csv"))
    
    assert len(csv_files) > 0, "No dialogue files found"
    
    # Parse one dialogue file
    if csv_files:
        import csv
        first_file = csv_files[0]
        with open(first_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) > 0, "Dialogue file should have content"
        print(f"  Loaded {len(csv_files)} dialogue files")


@test("INTEG-006", "Full team operations")
def test_team_operations():
    """Test creating and managing a full Pokemon team."""
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.core.tool import asset_path
    import json
    
    team = []
    
    # Create a team of 6
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    for i in range(6):
        poke = Pokemon(data, 20 + i * 5)
        team.append(poke)
    
    # Verify team operations
    assert len(team) == 6, "Team should have 6 members"
    
    # Test fainted Pokemon
    team[0].hp = 0
    alive = [p for p in team if p.hp > 0]
    assert len(alive) == 5, "Should have 5 alive Pokemon"
    
    # Test team serialization
    team_data = [p.to_dict() for p in team]
    team_restored = [Pokemon.from_dict(d) for d in team_data]
    
    assert len(team_restored) == 6, "Restored team should have 6 members"
    assert team_restored[0].hp == 0, "Fainted status should be preserved"
    
    print(f"  Team operations: OK (6 Pokemon, {len(alive)} alive)")


@test("INTEG-007", "Inventory usage chain (buy -> use -> check)")
def test_inventory_usage_chain():
    """Test complete inventory operations chain."""
    from pokemon_game.systems.inventory import Inventory
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.core.tool import asset_path
    import json
    
    inv = Inventory()
    inv.money = 2000
    
    # Buy potion
    initial_money = inv.money
    success = inv.buy("potion", 2)
    assert success, "Buy should succeed"
    assert inv.money < initial_money, "Money should decrease"
    assert inv.count("potion") == 2, "Should have 2 potions"
    
    # Use potion on Pokemon
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    poke = Pokemon(data, 50)
    poke.hp = 50  # Set to low HP
    
    ok, msg = inv.use_on_pokemon("potion", poke)
    assert ok, "Use should succeed"
    assert poke.hp > 50, "Pokemon should be healed"
    assert inv.count("potion") == 1, "Should have 1 potion left"
    
    print(f"  Inventory chain: OK ({msg[:30]}...)")


# ============================================================================
# PHASE 6: EDGE CASE & ROBUSTNESS TESTING
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 6: ROBUSTNESS TESTING - Error handling")
print("=" * 80)


@test("ROBUST-001", "Handle missing Pokemon JSON gracefully")
def test_missing_pokemon():
    """Test behavior with missing Pokemon data."""
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.core.tool import asset_path
    
    try:
        # Try to load a Pokemon that doesn't exist
        path = asset_path("json", "pokemon", "fakepokemon99999.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        print("  Correctly raised FileNotFoundError for missing Pokemon")


@test("ROBUST-002", "Handle corrupted/truncated JSON")
def test_corrupted_json():
    """Test behavior with malformed JSON."""
    import tempfile
    
    # Create a truncated JSON file
    truncated_json = '{"id": 1, "name": "Broken", "forms": [{'
    
    try:
        data = json.loads(truncated_json)
        assert False, "Should have raised JSONDecodeError"
    except json.JSONDecodeError:
        print("  Correctly caught JSONDecodeError for truncated JSON")


@test("ROBUST-003", "Pokemon with extreme IV values")
def test_extreme_ivs():
    """Test Pokemon with all IVs at extremes."""
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.core.tool import asset_path
    
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    poke = Pokemon(data, 50)
    
    # Manually set IVs to extremes
    poke.ivs = {key: 0 for key in poke.ivs.keys()}
    poke2 = Pokemon(data, 50)
    poke2.ivs = {key: 31 for key in poke2.ivs.keys()}
    
    # Recalculate stats
    low_hp = poke.update_stats("hp")
    high_hp = poke2.update_stats("hp")
    
    assert low_hp > 0, "Low IV Pokemon should have positive HP"
    assert high_hp > low_hp, "High IV Pokemon should have higher stats"
    
    print(f"  IV extremes: {low_hp} HP (IV=0) vs {high_hp} HP (IV=31)")


@test("ROBUST-004", "Move without power attribute")
def test_move_without_power():
    """Test move calculation when power is None/0."""
    from pokemon_game.systems.battle import calc_damage
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.entities.move import Move
    from pokemon_game.core.tool import asset_path
    import json
    
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    poke1 = Pokemon(data, 50)
    poke2 = Pokemon(data, 50)
    
    # Create a move with no power (status move)
    move_data = {"id": 0, "name": "Status", "power": None, "category": "status"}
    move = Move(move_data)
    
    damage, eff, crit = calc_damage(poke1, poke2, move)
    assert damage == 0, "Status move should deal 0 damage"
    
    print("  Status move handling: OK")


@test("ROBUST-005", "Very large team with heterogeneous levels")
def test_mixed_level_team():
    """Test team with varied Pokemon levels."""
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.core.tool import asset_path
    import json
    
    team = []
    
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    # Create team with levels: 5, 25, 50, 75, 100, 100
    levels = [5, 25, 50, 75, 100, 100]
    for level in levels:
        poke = Pokemon(data, level)
        team.append(poke)
    
    # Verify stats scale appropriately
    stats_by_level = [(p.level, p.hp) for p in team]
    
    for i in range(len(team) - 1):
        assert team[i].level <= team[i+1].level, "Levels should be non-decreasing"
        if team[i].level < team[i+1].level:
            assert team[i].hp < team[i+1].hp, "Higher level should have higher HP"
    
    print(f"  Mixed level team: {len(team)} Pokemon, levels {levels}")


@test("ROBUST-006", "Catch rate edge cases")
def test_catch_rate_edge_cases():
    """Test catch rate calculation with various HP values."""
    from pokemon_game.systems.battle import catch_rate
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.core.tool import asset_path
    import json
    
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    poke = Pokemon(data, 50)
    
    # Full HP - hardest to catch
    poke.hp = poke.maxhp
    rate_full = catch_rate(poke)
    
    # Half HP - medium difficulty
    poke.hp = poke.maxhp // 2
    rate_half = catch_rate(poke)
    
    # Low HP - easiest to catch
    poke.hp = 1
    rate_low = catch_rate(poke)
    
    assert 0 <= rate_full <= 1, "Catch rate should be 0-1"
    assert 0 <= rate_half <= 1, "Catch rate should be 0-1"
    assert 0 <= rate_low <= 1, "Catch rate should be 0-1"
    assert rate_low > rate_full, "Low HP should increase catch rate"
    
    print(f"  Catch rates: {rate_full:.2%} (full) -> {rate_half:.2%} (half) -> {rate_low:.2%} (low)")


# ============================================================================
# PHASE 7: PERFORMANCE TESTING
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 7: PERFORMANCE TESTING")
print("=" * 80)


@test("PERF-001", "Bulk Pokemon creation (100 Pokemon)")
def test_bulk_pokemon_creation():
    """Test creation of many Pokemon objects."""
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.core.tool import asset_path
    import json
    
    start = time.time()
    
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    pokemon_list = []
    for i in range(100):
        poke = Pokemon(data, (i % 100) + 1)
        pokemon_list.append(poke)
    
    elapsed = time.time() - start
    
    assert len(pokemon_list) == 100, "Should create 100 Pokemon"
    
    # Should complete in reasonable time (< 5 seconds for 100)
    assert elapsed < 5.0, f"Creation took too long: {elapsed:.2f}s"
    
    print(f"  Created 100 Pokemon in {elapsed:.2f}s ({1000*elapsed/100:.1f}ms per Pokemon)")


@test("PERF-002", "Damage calculation speed (1000 calculations)")
def test_damage_calculation_speed():
    """Test performance of damage calculations."""
    from pokemon_game.systems.battle import calc_damage
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.entities.move import Move
    from pokemon_game.core.tool import asset_path
    import json
    
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    poke1 = Pokemon(data, 50)
    poke2 = Pokemon(data, 50)
    
    move_data = {"id": 1, "name": "Tackle", "type": "normal", "power": 40, "category": "physical"}
    move = Move(move_data)
    
    start = time.time()
    
    for _ in range(1000):
        calc_damage(poke1, poke2, move)
    
    elapsed = time.time() - start
    
    # Should complete 1000 calculations in < 1 second
    assert elapsed < 1.0, f"Damage calculations took too long: {elapsed:.2f}s"
    
    print(f"  1000 damage calculations in {elapsed:.2f}s ({1000*elapsed:.1f}us per calc)")


@test("PERF-003", "Serialization performance (serialize 100 Pokemon)")
def test_serialization_speed():
    """Test performance of Pokemon serialization."""
    from pokemon_game.entities.pokemon import Pokemon
    from pokemon_game.core.tool import asset_path
    import json
    
    path = asset_path("json", "pokemon", "bulbasaur.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    pokemon_list = [Pokemon(data, 50) for _ in range(100)]
    
    start = time.time()
    
    serialized = []
    for poke in pokemon_list:
        serialized.append(poke.to_dict())
    
    elapsed = time.time() - start
    
    assert len(serialized) == 100, "Should serialize 100 Pokemon"
    assert elapsed < 1.0, f"Serialization took too long: {elapsed:.2f}s"
    
    print(f"  Serialized 100 Pokemon in {elapsed:.2f}s ({1000*elapsed/100:.1f}ms per Pokemon)")


@test("PERF-004", "Type effectiveness lookup speed")
def test_type_effectiveness_speed():
    """Test performance of type lookups."""
    from pokemon_game.systems.battle import type_effectiveness
    
    types_to_check = [
        ("fire", ["water", "ground"]),
        ("electric", ["water", "flying"]),
        ("grass", ["fire", "ice", "poison"]),
        ("normal", ["rock", "steel", "ghost"]),
    ]
    
    start = time.time()
    
    for _ in range(1000):
        for move_type, defender_types in types_to_check:
            type_effectiveness(move_type, defender_types)
    
    elapsed = time.time() - start
    
    # Should be very fast
    assert elapsed < 0.1, f"Type lookups took too long: {elapsed:.2f}s"
    
    print(f"  4000 type lookups in {elapsed:.2f}s ({elapsed*250:.1f}us per lookup)")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

integration_tests = [
    test_map_loading,
    test_sequential_pokemon_loads,
    test_battle_flow,
    test_save_load_cycle,
    test_dialogue_loading,
    test_team_operations,
    test_inventory_usage_chain,
]

for test_func in integration_tests:
    test_func()

robust_tests = [
    test_missing_pokemon,
    test_corrupted_json,
    test_extreme_ivs,
    test_move_without_power,
    test_mixed_level_team,
    test_catch_rate_edge_cases,
]

for test_func in robust_tests:
    test_func()

perf_tests = [
    test_bulk_pokemon_creation,
    test_damage_calculation_speed,
    test_serialization_speed,
    test_type_effectiveness_speed,
]

for test_func in perf_tests:
    test_func()

# ============================================================================
# FINAL REPORT
# ============================================================================

print("\n" + "=" * 80)
print("ADVANCED TEST SUMMARY")
print("=" * 80)

total_time = time.time() - start_time

passed = sum(1 for r in test_results if r["status"] == "PASS")
failed = sum(1 for r in test_results if r["status"] == "FAIL")
errors = sum(1 for r in test_results if r["status"] == "ERROR")

print(f"\nTotal Tests: {len(test_results)}")
print(f"[PASS] Passed: {passed}")
print(f"[FAIL] Failed: {failed}")
print(f"[ERROR] Errors: {errors}")
print(f"Total Time: {total_time:.2f}s")

if failed > 0 or errors > 0:
    print("\n" + "=" * 80)
    print("FAILED/ERROR TESTS:")
    print("=" * 80)
    for result in test_results:
        if result["status"] != "PASS":
            print(f"\n{result['name']} [{result['status']}]")
            if result["error"]:
                print(f"  {result['error']}")

exit(0 if failed == 0 and errors == 0 else 1)
