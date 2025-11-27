#!/usr/bin/env python3
"""
Test script to debug wmic output parsing
"""
import subprocess
import sys

def test_wmic_command(cmd, description):
    """Test a wmic command and show raw output"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"Return code: {result.returncode}")
        print(f"\nRaw stdout (repr):")
        print(repr(result.stdout))
        print(f"\nRaw stdout (display):")
        print(result.stdout)
        print(f"\nStdout lines:")
        lines = result.stdout.strip().split('\n')
        for i, line in enumerate(lines):
            print(f"  Line {i}: {repr(line)}")
        
        if len(lines) > 1:
            value = lines[1].strip()
            print(f"\nExtracted value (line 1, stripped): {repr(value)}")
            print(f"Value length: {len(value)}")
            print(f"Is empty: {not value}")
        else:
            print("\nNot enough lines in output")
            
        if result.stderr:
            print(f"\nStderr:")
            print(result.stderr)
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("WMIC Output Parser Test")
    print("="*60)
    
    # Test motherboard serial
    test_wmic_command(
        ["wmic", "baseboard", "get", "serialnumber"],
        "Motherboard Serial Number"
    )
    
    # Test BIOS serial
    test_wmic_command(
        ["wmic", "bios", "get", "serialnumber"],
        "BIOS Serial Number"
    )
    
    # Test System UUID
    test_wmic_command(
        ["wmic", "csproduct", "get", "uuid"],
        "System UUID"
    )
    
    print("\n" + "="*60)
    print("Test Complete")

