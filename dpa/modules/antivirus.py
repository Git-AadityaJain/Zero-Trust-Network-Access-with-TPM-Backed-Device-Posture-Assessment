"""
Windows Antivirus/EDR detection
"""
import subprocess
import logging

logger = logging.getLogger("dpa.antivirus")

def check_antivirus() -> dict:
    """
    Check antivirus/EDR software status
    
    Returns:
        dict: Antivirus status information
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object displayName, productState | ConvertTo-Json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            import json
            av_products = json.loads(result.stdout)
            
            if not isinstance(av_products, list):
                av_products = [av_products]
            
            if av_products:
                # Get first AV product
                av = av_products[0]
                product_name = av.get("displayName", "Unknown")
                product_state = av.get("productState", 0)
                
                # Decode product state (hex value)
                # Bit 12-15: Running state (0x1000 = running)
                # Bit 8-11: Definition state (0x0100 = updated)
                running = (product_state & 0x1000) != 0
                
                return {
                    "installed": True,
                    "running": running,
                    "product_name": product_name
                }
            else:
                return {
                    "installed": False,
                    "running": False,
                    "product_name": "None"
                }
        
        logger.warning("Failed to check antivirus status via PowerShell")
        return {
            "installed": False,
            "running": False,
            "product_name": "Unknown"
        }
        
    except Exception as e:
        logger.error(f"Error checking antivirus: {e}")
        return {
            "installed": False,
            "running": False,
            "product_name": "Unknown"
        }
