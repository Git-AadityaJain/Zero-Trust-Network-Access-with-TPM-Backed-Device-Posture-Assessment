#!/bin/bash
# Script to clear TPM key and local enrollment data (Linux/Mac)
# Note: TPM key clearing on Linux requires different methods

echo "=========================================="
echo "Clearing TPM Key and Enrollment Data"
echo "=========================================="

# Step 1: Clear Local Enrollment Data
echo ""
echo "1. Clearing Local Enrollment Data..."

ENROLLMENT_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/ZTNA"
ENROLLMENT_FILE="$ENROLLMENT_DIR/enrollment.json"
CONFIG_FILE="$ENROLLMENT_DIR/config.json"
SECRET_FILE="$ENROLLMENT_DIR/secret.dat"
SALT_FILE="$ENROLLMENT_DIR/salt.dat"

FILES_CLEARED=0

if [ -f "$ENROLLMENT_FILE" ]; then
    rm -f "$ENROLLMENT_FILE"
    echo "   ✓ Deleted enrollment.json"
    FILES_CLEARED=$((FILES_CLEARED + 1))
else
    echo "   - enrollment.json not found (already cleared)"
fi

if [ -f "$SECRET_FILE" ]; then
    rm -f "$SECRET_FILE"
    echo "   ✓ Deleted secret.dat"
    FILES_CLEARED=$((FILES_CLEARED + 1))
else
    echo "   - secret.dat not found"
fi

if [ -f "$SALT_FILE" ]; then
    rm -f "$SALT_FILE"
    echo "   ✓ Deleted salt.dat"
    FILES_CLEARED=$((FILES_CLEARED + 1))
else
    echo "   - salt.dat not found"
fi

# Note: config.json is kept
echo "   - config.json kept (contains backend URL configuration)"

# Step 2: TPM Key Clearing (Linux-specific)
echo ""
echo "2. TPM Key Clearing..."
echo "   Note: TPM key clearing on Linux requires TPM2 tools"
echo "   If using TPM2, you may need to:"
echo "   - Use tpm2-tools to clear TPM keys"
echo "   - Or re-initialize TPM (requires physical access)"
echo "   - Or use TPM2_PCR_Reset if applicable"

# Check if TPM2 tools are available
if command -v tpm2_getcap &> /dev/null; then
    echo "   ✓ TPM2 tools found"
    echo "   To clear TPM keys, you may need to use:"
    echo "   - tpm2_evictcontrol (for persistent objects)"
    echo "   - tpm2_clear (requires physical presence)"
else
    echo "   - TPM2 tools not found"
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Files cleared: $FILES_CLEARED"
echo ""
echo "Next steps:"
echo "1. Run enrollment again: python -m dpa.cli.enroll_cli --enrollment-code YOUR_CODE"
echo "2. A new TPM key will be generated during enrollment"
echo ""

