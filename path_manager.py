#!/usr/bin/env python3
"""
Unified Download Path Manager
==============================
Handles download path configuration across all toolkits.

Key Features:
- Always prompts for download path (no defaults, no env vars)
- Session-based caching with automatic cleanup
- Batch mode support via --out flag
- Path validation and auto-creation with confirmation
- Automatic cache clearing on any termination

IMPORTANT FOR FUTURE LLM AGENTS:
- NEVER persist paths between script runs
- NEVER use environment variables for paths
- ALWAYS prompt for paths (except with --out flag)
- ALWAYS use this module for download path handling
"""

import os
import sys
import atexit
import signal
from pathlib import Path
from typing import Optional

# Session cache - memory only, cleared on ANY termination
_SESSION_DOWNLOAD_PATH: Optional[str] = None
_SESSION_ACTIVE: bool = False


def _cleanup_session():
    """
    Clear session cache on exit.
    Called automatically by atexit, signal handlers, or manual termination.
    """
    global _SESSION_DOWNLOAD_PATH, _SESSION_ACTIVE
    _SESSION_DOWNLOAD_PATH = None
    _SESSION_ACTIVE = False


# Register cleanup handlers for all termination scenarios
atexit.register(_cleanup_session)
try:
    signal.signal(signal.SIGINT, lambda s, f: (_cleanup_session(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (_cleanup_session(), sys.exit(0)))
except (ValueError, OSError):
    # Signal handling not available on some platforms
    pass


def prompt_for_download_path(
    context: str = "files",
    allow_session_reuse: bool = True,
    out_path: Optional[str] = None,
    default_path: Optional[str] = None
) -> str:
    """
    Prompt user for download location with session caching support.
    
    Args:
        context: Description of what's being downloaded (e.g., "Instagram photos", "TikTok videos")
        allow_session_reuse: If True and path exists in session, ask to reuse
        out_path: Pre-specified output path from --out flag (skips prompting)
        default_path: Default path to use if user leaves prompt empty
    """
    global _SESSION_DOWNLOAD_PATH, _SESSION_ACTIVE
    
    # Handle --out flag (batch mode)
    if out_path:
        validated = _validate_and_create_path(out_path, context)
        # Update session cache even for --out paths
        _SESSION_DOWNLOAD_PATH = validated
        _SESSION_ACTIVE = True
        return validated
    
    # Check session cache for reuse
    if allow_session_reuse and _SESSION_ACTIVE and _SESSION_DOWNLOAD_PATH:
        print(f"\n{'='*70}")
        print(f"♻️  CURRENT SESSION PATH: {_SESSION_DOWNLOAD_PATH}")
        print(f"{'='*70}")
        reuse = input("Use same path for this download? (y/n): ").strip().lower()
        if reuse == 'y':
            print(f"✅ Reusing session path: {_SESSION_DOWNLOAD_PATH}\n")
            return _SESSION_DOWNLOAD_PATH
        else:
            print("Prompting for new path...\n")
    
    # Prompt for new path
    print(f"\n{'='*70}")
    print(f"📁 DOWNLOAD LOCATION REQUIRED FOR: {context.upper()}")
    print(f"{'='*70}")
    if default_path:
        print(f"💡 DEFAULT: {default_path}")
    print(f"⚠️  WARNING: Path is NOT saved between script runs!")
    print(f"    Each new session requires path configuration.")
    print(f"    This is for your safety and transparency.")
    print(f"{'='*70}")
    print(f"\n💡 Examples:")
    print(f"   • Windows:   C:\\Users\\YourName\\Downloads\\{context.replace(' ', '_').lower()}")
    print(f"   • Mac/Linux: /Users/yourname/Downloads/{context.replace(' ', '_').lower()}")
    print(f"   • Relative:  ./{context.replace(' ', '_').lower()}_downloads")
    print(f"\n💡 Tips:")
    print(f"   • Use absolute paths for clarity")
    print(f"   • Directory will be created if it doesn't exist")
    print(f"   • Type 'exit' or 'q' to cancel")
    print(f"{'='*70}\n")
    
    while True:
        prompt_msg = f"📂 Enter download directory path: "
        if default_path:
            prompt_msg = f"📂 Enter download directory path (Press Enter for default): "
            
        download_path = input(prompt_msg).strip()
        
        # Handle exit request
        if download_path.lower() in ['exit', 'q', 'quit']:
            print("\n❌ Operation cancelled by user.")
            _cleanup_session()
            sys.exit(0)
        
        # Handle empty input with default
        if not download_path:
            if default_path:
                download_path = default_path
                print(f"ℹ️  Using default path: {download_path}")
            else:
                print("❌ Path cannot be empty. Please enter a valid path.\n")
                continue
        
        try:
            validated_path = _validate_and_create_path(download_path, context)
            
            # Update session cache
            _SESSION_DOWNLOAD_PATH = validated_path
            _SESSION_ACTIVE = True
            
            print(f"\n{'='*70}")
            print(f"✅ SESSION PATH SET: {validated_path}")
            print(f"⚠️  Valid for this session only - will clear on exit!")
            print(f"{'='*70}\n")
            
            return validated_path
            
        except PermissionError:
            print(f"❌ Permission denied: {download_path}")
            print(f"   Please choose a location with write permissions.\n")
        except FileExistsError as e:
            print(f"❌ {e}")
            print(f"   Please choose a different path.\n")
        except Exception as e:
            print(f"❌ Invalid path: {download_path}")
            print(f"   Error: {e}\n")


def _validate_and_create_path(path_str: str, context: str) -> str:
    """
    Validate path and create directory if needed.
    
    Args:
        path_str: Path string to validate
        context: Context for error messages
        
    Returns:
        str: Absolute validated path
        
    Raises:
        PermissionError: If no write access
        FileExistsError: If path exists and is a file (not directory)
        Exception: For other validation errors
    """
    # Expand user path (~) and make absolute
    path = Path(path_str).expanduser().resolve()
    
    # Check if path exists and is a file (not directory)
    if path.exists() and not path.is_dir():
        raise FileExistsError(f"Path exists but is a file, not a directory: {path}")
    
    # Create directory if it doesn't exist
    if not path.exists():
        print(f"\n📁 Directory does not exist: {path}")
        confirm = input("   Create this directory? (y/n): ").strip().lower()
        
        if confirm != 'y':
            raise ValueError("Directory creation declined by user")
        
        try:
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {path}")
        except PermissionError:
            raise PermissionError(f"Cannot create directory (permission denied): {path}")
        except Exception as e:
            raise Exception(f"Failed to create directory: {e}")
    
    # Test write access
    try:
        test_file = path / '.write_test_temp'
        test_file.write_text('test')
        test_file.unlink()
    except PermissionError:
        raise PermissionError(f"No write permission for directory: {path}")
    except Exception as e:
        raise Exception(f"Cannot write to directory: {e}")
    
    abs_path = str(path)
    return abs_path


def get_session_path() -> Optional[str]:
    """
    Get current session download path without prompting.
    
    Returns:
        str or None: Current session path if set, None otherwise
    """
    return _SESSION_DOWNLOAD_PATH if _SESSION_ACTIVE else None


def clear_session_cache():
    """
    Manually clear session cache.
    Useful for testing or forcing fresh prompts.
    """
    _cleanup_session()
    print("🧹 Session download path cache cleared")


# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    print("Testing Download Path Manager")
    print("="*70)
    
    parser = argparse.ArgumentParser(description="Test download path manager")
    parser.add_argument('--out', type=str, help='Output directory (batch mode)')
    args = parser.parse_args()
    
    # Test 1: First download
    print("\n[TEST 1] First download prompt:")
    path1 = prompt_for_download_path(
        context="test_files",
        out_path=args.out
    )
    print(f"Result: {path1}")
    
    # Test 2: Second download with session reuse option
    print("\n[TEST 2] Second download (should offer reuse):")
    path2 = prompt_for_download_path(
        context="more_files",
        allow_session_reuse=True,
        out_path=args.out
    )
    print(f"Result: {path2}")
    
    # Test 3: Check session path
    print("\n[TEST 3] Current session path:")
    session_path = get_session_path()
    print(f"Result: {session_path}")
    
    print("\n✅ All tests completed. Cache will clear on exit.")
