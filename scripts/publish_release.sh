#!/bin/bash
# scripts/publish_release.sh

# Exit on error
set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/publish_release.sh <version>"
    exit 1
fi

echo "Preparing to publish release $VERSION..."

# Define Artifacts
EXE_PATH="dist/windows/XvGKeybind.exe"
LINUX_PATH="dist/linux/XvGKeybind"
INSTALLER_PATH="Output/XvGAutoSetup.exe"
RELEASE_NOTES="RELEASE.md"

# Check artifacts (Warn if missing, but try to proceed with what we have?)
# Better to fail if critical ones are missing.
if [ ! -f "$EXE_PATH" ]; then
    # Fallback check if it's in older location or user ran old script?
    if [ -f "dist/XvGKeybind.exe" ]; then
        EXE_PATH="dist/XvGKeybind.exe"
    else
        echo "Error: Windows Executable not found at $EXE_PATH"
        exit 1
    fi
fi

if [ ! -f "$INSTALLER_PATH" ]; then
     echo "Error: Installer not found at $INSTALLER_PATH"
     exit 1
fi

ARGS=("$VERSION" "$EXE_PATH" "$INSTALLER_PATH")

if [ -f "$LINUX_PATH" ]; then
    ARGS+=("$LINUX_PATH")
else
    echo "Warning: Linux binary not found at $LINUX_PATH. Publishing without it."
fi

# Run gh release create
echo "Creating GitHub Release with: ${ARGS[*]}..."
gh release create "${ARGS[@]}" --title "$VERSION" --notes-file "$RELEASE_NOTES"

echo "Release $VERSION published successfully!"
