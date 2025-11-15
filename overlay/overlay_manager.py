"""
Safe overlay manager with timeouts and error handling
"""
import sys
import os
import subprocess
import json
import tempfile
import time
from typing import Optional

# Fix Qt plugin path conflict
os.environ.pop('QT_QPA_PLATFORM_PLUGIN_PATH', None)


class OverlayManager:
    """
    Manages overlay process with safety controls
    """
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.temp_file = None
        self.last_spawn_time = 0
        self.spawn_cooldown = 2.0  # Seconds between spawns
        self.process_timeout = 10.0  # Kill if unresponsive
        self.enabled = True  # Global kill switch
    
    def _ensure_process(self) -> bool:
        """Start overlay process if not running"""
        if not self.enabled:
            print("⚠️ Overlay disabled")
            return False
        
        # Rate limit spawning
        now = time.time()
        if now - self.last_spawn_time < self.spawn_cooldown:
            wait = self.spawn_cooldown - (now - self.last_spawn_time)
            print(f"⏳ Overlay spawn cooldown: {wait:.1f}s")
            time.sleep(wait)
        
        # Check if process is alive
        if self.process and self.process.poll() is None:
            return True
        
        # Clean up old process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                pass
        
        try:
            # Create temp file
            self.temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                delete=False,
                suffix='.json'
            )
            self.temp_file.close()
            
            # Get paths
            overlay_dir = os.path.dirname(__file__)
            project_root = os.path.dirname(overlay_dir)
            script_path = os.path.join(overlay_dir, 'overlay_process.py')
            
            # Setup environment
            env = os.environ.copy()
            python_path = env.get('PYTHONPATH', '')
            env['PYTHONPATH'] = f"{project_root}:{python_path}" if python_path else project_root
            
            # Spawn process
            print(f"🚀 Starting overlay process...")
            
            self.process = subprocess.Popen(
                [sys.executable, script_path, self.temp_file.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                cwd=project_root,
                env=env
            )
            
            self.last_spawn_time = time.time()
            
            # Wait for startup
            time.sleep(1.5)
            
            # Verify process started
            if self.process.poll() is not None:
                output = self.process.stdout.read() if self.process.stdout else ""
                print(f"❌ Overlay process failed: {output[:200]}")
                return False
            
            print("✅ Overlay process started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start overlay: {e}")
            return False
    
    def _send_command(self, command: str, data: dict) -> bool:
        """Send command to overlay process"""
        if not self._ensure_process():
            return False
        
        try:
            cmd_data = {'command': command, 'data': data}
            
            # Write command
            with open(self.temp_file.name, 'w') as f:
                json.dump(cmd_data, f)
            
            # Create trigger
            marker_file = self.temp_file.name + '.trigger'
            with open(marker_file, 'w') as f:
                f.write('trigger')
            
            # Give process time to read
            time.sleep(0.1)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to send overlay command: {e}")
            return False
    
    def add_circle(self, x: int, y: int):
        """Add circle at coordinates"""
        if self._send_command('add_circle', {'x': x, 'y': y}):
            print(f"✓ Circle at ({x}, {y})")
    
    def add_rect(self, x1: int, y1: int, x2: int, y2: int):
        """Add rectangle"""
        if self._send_command('add_rect', {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}):
            print(f"✓ Rectangle: ({x1},{y1}) to ({x2},{y2})")
    
    def clear(self):
        """Clear all shapes"""
        if self._send_command('clear', {}):
            print("✓ Shapes cleared")
    
    def close(self):
        """Close overlay process"""
        if self.process:
            try:
                self._send_command('close', {})
                time.sleep(0.5)
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                self.process.kill()
            finally:
                self.process = None
        
        # Clean up temp files
        if self.temp_file:
            try:
                os.unlink(self.temp_file.name)
                os.unlink(self.temp_file.name + '.trigger')
            except:
                pass
        
        print("✓ Overlay closed")
    
    def disable(self):
        """Disable overlay globally"""
        self.enabled = False
        self.close()
        print("⚠️ Overlay disabled")
    
    def enable(self):
        """Enable overlay"""
        self.enabled = True
        print("✓ Overlay enabled")


# Global instance
manager = OverlayManager()