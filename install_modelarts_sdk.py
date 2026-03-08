#!/usr/bin/env python3
"""Install the ModelArts SDK from the wheel file."""

import subprocess
import sys

def install_modelarts():
    """Install ModelArts SDK from wheel file."""
    wheel_path = "src/modelarts-1.0.0-py2.py3-none-any.whl"
    
    print("Installing ModelArts SDK...")
    print(f"Wheel file: {wheel_path}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", wheel_path, "--force-reinstall"],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ ModelArts SDK installed successfully!")
            
            # Test import
            print("\nTesting import...")
            import modelarts
            print(f"ModelArts version: {getattr(modelarts, '__version__', 'unknown')}")
            print(f"Available modules: {dir(modelarts)}")
            
        else:
            print("\n❌ Installation failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = install_modelarts()
    sys.exit(0 if success else 1)
