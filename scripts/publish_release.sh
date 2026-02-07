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
EXE_PATH="dist/XvGKeybind.exe"
INSTALLER_PATH="Output/XvGAutoSetup.exe"
RELEASE_NOTES="RELEASE.md"

# Check artifacts
if [ ! -f "$EXE_PATH" ]; then
    echo "Executable not found at $EXE_PATH. Did you run build_installer.sh?"
    exit 1
fi
if [ ! -f "$INSTALLER_PATH" ]; then
    echo "Installer not found at $INSTALLER_PATH. Did you run build_installer.sh?"
    exit 1
fi
if [ ! -f "$RELEASE_NOTES" ]; then
    echo "Release notes file not found at $RELEASE_NOTES."
    exit 1
fi

# Run gh release create
echo "Creating GitHub Release..."
gh release create "$VERSION" "$EXE_PATH" "$INSTALLER_PATH" --title "$VERSION" --notes-file "$RELEASE_NOTES"

echo "Release $VERSION published successfully!"
