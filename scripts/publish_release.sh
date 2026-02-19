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
# Define Artifacts
EXE_PATH="dist/windows/XvG-AutoKeybind.exe"
LINUX_PATH="dist/release/XvG-AutoKeybind"
INSTALLER_PATH="Output/XvGAutoSetup.exe"
RELEASE_NOTES="RELEASE.md"

# Check artifacts (Warn if missing, but try to proceed with what we have?)
# Better to fail if critical ones are missing.
# Check artifacts
# Windows Artifacts (Optional on Linux host if not cross-compiling, but good to warn)
if [ ! -f "$EXE_PATH" ]; then
    # Fallback check
    if [ -f "dist/XvG-AutoKeybind.exe" ]; then
        EXE_PATH="dist/XvG-AutoKeybind.exe"
    else
        echo "Warning: Windows Executable not found at $EXE_PATH"
        EXE_PATH=""
    fi
fi

if [ ! -f "$INSTALLER_PATH" ]; then
     echo "Warning: Installer not found at $INSTALLER_PATH"
     INSTALLER_PATH=""
fi

ARGS=("$VERSION")
if [ -n "$EXE_PATH" ]; then ARGS+=("$EXE_PATH"); fi
if [ -n "$INSTALLER_PATH" ]; then ARGS+=("$INSTALLER_PATH"); fi

if [ -f "$LINUX_PATH" ]; then
    ARGS+=("$LINUX_PATH")
    # Also include the install script if present
    if [ -f "dist/release/install.sh" ]; then
        ARGS+=("dist/release/install.sh")
    fi
else
    # Try alternate path from build_installer.sh just in case
    if [ -f "dist/linux/XvG-AutoKeybind" ]; then
        ARGS+=("dist/linux/XvG-AutoKeybind")
        echo "Found Linux binary at dist/linux/XvG-AutoKeybind"
    else
        echo "Warning: Linux binary not found at $LINUX_PATH or dist/linux/XvG-AutoKeybind. Publishing without it."
    fi
fi

# Run gh release create
echo "Creating GitHub Release with: ${ARGS[*]}..."
gh release create "${ARGS[@]}" --title "$VERSION" --notes-file "$RELEASE_NOTES"

echo "Release $VERSION published successfully!"
