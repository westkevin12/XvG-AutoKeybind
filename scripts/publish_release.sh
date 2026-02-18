#!/bin/bash
# scripts/publish_release.sh

# Exit on error
set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/publish_release.sh <version>"
    exit 1
fi

# Check if tag exists locally
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "Tag '$VERSION' already exists locally."
    read -p "Do you want to (d)elete and recreate it, (u)se existing, or (a)bort? [d/u/a]: " choice
    case "$choice" in 
        d|D ) 
            echo "Deleting local tag '$VERSION'..."
            git tag -d "$VERSION"
            ;;
        u|U )
            echo "Using existing tag..."
            # GitHub CLI might still complain if not pushed, but maybe --target handles it?
            # Or we just push it first?
            git push origin "$VERSION" || echo "Warning: Failed to push tag. Continuing..."
            ;;
        * )
            echo "Aborted."
            exit 1
            ;;
    esac
fi

echo "Preparing to publish release $VERSION..."

# Define Artifacts
EXE_PATH="dist/windows/XvGKeybind.exe"
LINUX_PATH="dist/XvG-AutoKeybind"
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
    # Try alternate path from build_installer.sh just in case
    if [ -f "dist/linux/XvGKeybind" ]; then
        ARGS+=("dist/linux/XvGKeybind")
        echo "Found Linux binary at dist/linux/XvGKeybind"
    else
        echo "Warning: Linux binary not found at $LINUX_PATH or dist/linux/XvGKeybind. Publishing without it."
    fi
fi

# Run gh release create
echo "Creating GitHub Release with: ${ARGS[*]}..."
gh release create "${ARGS[@]}" --title "$VERSION" --notes-file "$RELEASE_NOTES"

echo "Release $VERSION published successfully!"
