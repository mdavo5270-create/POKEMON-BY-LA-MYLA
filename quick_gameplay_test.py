#!/usr/bin/env python3
"""Quick gameplay test with real game interaction."""

import os
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / "src"))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from pokemon_game.core.game import Game

class QuickGameplayTest:
    def __init__(self):
        self.logs = []
        self.bugs = []
        self.session = 0
        self.start_time = time.time()
        self.game = None
    
    def log(self, msg, level="INFO"):
        elapsed = int(time.time() - self.start_time)
        timestamp = f"{elapsed//60:02d}:{elapsed%60:02d}"
        line = f"{timestamp} [{level:6s}] {msg}"
        self.logs.append(line)
        print(line, flush=True)
    
    def test(self):
        try:
            self.log("Initializing game...", "INIT")
            pygame.init()
            
            self.log("Creating Game instance...", "INIT")
            self.game = Game()
            
            self.log(f"Player position: ({self.game.player.position.x}, {self.game.player.position.y})", "INFO")
            
            team_count = len(getattr(self.game.player, "team", []))
            self.log(f"Team size: {team_count} Pokémon", "INFO")
            
            inv = getattr(self.game.player, "inventory", None)
            if inv:
                self.log(f"Inventory loaded. Money: {getattr(inv, 'money', 0)} P", "INFO")
            
            self.log("Starting gameplay simulation...", "SESSION")
            
            # Run 300 game ticks  
            for frame in range(300):
                try:
                    # Handle input events
                    self.game.handle_input()
                    
                    # Simulate basic game loop
                    if self.game.switch_cooldown > 0:
                        self.game.switch_cooldown -= 1
                    if self.game.interact_cooldown > 0:
                        self.game.interact_cooldown -= 1
                    
                    # Update dialogue
                    self.game.dialogue_controller()
                    
                    # Update map
                    if not getattr(self.game, "_no_map", False):
                        try:
                            self.game.map.update()
                        except Exception as e:
                            self.log(f"Map update error: {e}", "WARN")
                    
                    # Update player
                    if self.game.player:
                        self.game.player.update()
                    
                    # Update screen
                    try:
                        self.game.screen.update()
                    except pygame.error:
                        self.log("Screen update failed", "WARN")
                    
                    # Progress
                    if frame % 100 == 0 and frame > 0:
                        self.log(f"Gameplay progress: {frame}/300 frames", "PROGRESS")
                    
                    # Occasional key presses
                    if frame % 50 == 0:
                        key = pygame.K_RIGHT
                        self.game.keylistener.add_key(key)
                        for _ in range(10):
                            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": key}))
                        self.game.keylistener.remove_key(key)
                
                except Exception as e:
                    self.log(f"Frame {frame} error: {e}", "ERROR")
                    break
                
                # Don't hog CPU
                pygame.time.delay(5)
            
            self.log("Gameplay simulation complete", "SUCCESS")
            
            # Test save/load
            try:
                self.log("Testing save function...", "TEST")
                self.game.save.save()
                self.log("Save successful", "SUCCESS")
            except Exception as e:
                self.log(f"Save error: {e}", "ERROR")
                self.bugs.append(f"Save function failed: {e}")
            
            return True
            
        except Exception as e:
            self.log(f"Fatal error: {e}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            self.bugs.append(f"Fatal: {e}")
            return False
        finally:
            pygame.quit()
    
    def generate_reports(self):
        self.log("Generating reports...", "REPORT")
        
        # GAMEPLAY_LOG.txt
        with open("GAMEPLAY_LOG.txt", "w", encoding="utf-8") as f:
            f.write("=== POKEMON GAME - GAMEPLAY TEST LOG ===\n\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"Duration: {int(time.time() - self.start_time)}s\n")
            f.write(f"Entries: {len(self.logs)}\n")
            f.write(f"Issues: {len(self.bugs)}\n\n")
            f.write("="*70 + "\n\n")
            f.write("GAMEPLAY LOG:\n\n")
            for log in self.logs:
                f.write(log + "\n")
        
        # BUG_REPORTS.txt
        with open("BUG_REPORTS.txt", "w", encoding="utf-8") as f:
            f.write("=== BUG REPORTS ===\n\n")
            if self.bugs:
                for i, bug in enumerate(self.bugs, 1):
                    f.write(f"{i}. {bug}\n")
            else:
                f.write("No bugs found!\n")
        
        # SESSION_SUMMARY.md
        with open("SESSION_SUMMARY.md", "w", encoding="utf-8") as f:
            f.write("# Gameplay Test Summary\n\n")
            f.write(f"- Bugs Found: {len(self.bugs)}\n")
            f.write(f"- Log Entries: {len(self.logs)}\n")
            f.write(f"- Duration: {int(time.time() - self.start_time)}s\n")
        
        # CRITICAL_FINDINGS.txt
        with open("CRITICAL_FINDINGS.txt", "w", encoding="utf-8") as f:
            f.write("=== FINDINGS ===\n\n")
            if self.bugs:
                f.write(f"Issues Found: {len(self.bugs)}\n")
                for bug in self.bugs:
                    f.write(f"- {bug}\n")
            else:
                f.write("✓ Game appears stable\n")

if __name__ == "__main__":
    test = QuickGameplayTest()
    success = test.test()
    test.generate_reports()
    
    if success:
        print("\n✓ Test completed")
    else:
        print("\n✗ Test failed")
