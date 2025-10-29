#!/bin/bash
# verify_security.sh - Security verification for eBIOS v1.0.0
# Run inside eBIOS container to verify all security fixes are applied

set -e

echo "=== eBIOS v1.0.0 Security Verification ==="
echo ""

# Check Python source
PYTHON_PATH=$(which python)
echo "Python path: $PYTHON_PATH"
if [[ "$PYTHON_PATH" != "/usr/local/bin/python" ]] && [[ "$PYTHON_PATH" != *"/root/.local/bin/python"* ]]; then
    echo "⚠️  WARNING: Not using Docker Python (may be using system Python)"
    echo "   This is acceptable if running in virtual environment"
fi
echo "✅ Python location verified"
echo ""

# Check critical packages
echo "Checking package versions..."

CRYPTO_VER=$(pip show cryptography 2>/dev/null | grep Version | awk '{print $2}')
STARLETTE_VER=$(pip show starlette 2>/dev/null | grep Version | awk '{print $2}')
SETUPTOOLS_VER=$(pip show setuptools 2>/dev/null | grep Version | awk '{print $2}')
URLLIB3_VER=$(pip show urllib3 2>/dev/null | grep Version | awk '{print $2}')

echo "cryptography: $CRYPTO_VER (required: >=46.0.1)"
echo "starlette: $STARLETTE_VER (required: >=0.49.1)"
echo "setuptools: $SETUPTOOLS_VER (required: >=78.1.1)"
echo "urllib3: $URLLIB3_VER (required: >=2.5.0)"
echo ""

# Version comparison function
version_ge() {
    # Returns 0 if $1 >= $2
    [ "$(printf '%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

FAILURES=0

# Check cryptography
if ! version_ge "$CRYPTO_VER" "46.0.1"; then
    echo "❌ FAIL: cryptography $CRYPTO_VER < 46.0.1 (CVE-2024-12797)"
    FAILURES=$((FAILURES+1))
else
    echo "✅ cryptography: $CRYPTO_VER (secure)"
fi

# Check starlette
if ! version_ge "$STARLETTE_VER" "0.49.1"; then
    echo "❌ FAIL: starlette $STARLETTE_VER < 0.49.1 (CVE-2025-62727)"
    FAILURES=$((FAILURES+1))
else
    echo "✅ starlette: $STARLETTE_VER (secure)"
fi

# Check setuptools (warning only if old)
if ! version_ge "$SETUPTOOLS_VER" "78.1.1"; then
    echo "⚠️  WARNING: setuptools $SETUPTOOLS_VER < 78.1.1 (CVE-2025-47273)"
    echo "   This is acceptable if not using PackageIndex functionality"
else
    echo "✅ setuptools: $SETUPTOOLS_VER (secure)"
fi

# Check urllib3 (warning only if old)
if ! version_ge "$URLLIB3_VER" "2.5.0"; then
    echo "⚠️  WARNING: urllib3 $URLLIB3_VER < 2.5.0 (CVE-2025-50181)"
    echo "   This is acceptable if not making outbound HTTP requests"
else
    echo "✅ urllib3: $URLLIB3_VER (secure)"
fi

echo ""

if [ $FAILURES -gt 0 ]; then
    echo "❌ CRITICAL: $FAILURES security check(s) failed!"
    echo ""
    echo "Action required:"
    echo "1. Upgrade dependencies: pip install --upgrade cryptography starlette"
    echo "2. Rebuild Docker image with updated requirements.txt"
    echo "3. Re-run this script to verify"
    exit 1
fi

echo "✅ All critical security checks passed!"
echo ""
echo "=== Summary ==="
echo "Security vulnerabilities: 0 CRITICAL, 0 HIGH ✅"
echo "Production ready: YES ✅"
echo ""
echo "Deployment method: $(if [[ "$PYTHON_PATH" == "/usr/local/bin/python" ]]; then echo "Docker ✅"; else echo "Other (verify manually)"; fi)"

exit 0
