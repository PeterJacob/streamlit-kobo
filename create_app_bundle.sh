#!/bin/bash
# Creates a minimal macOS .app bundle that launches the PyWebView app
# using the project's uv-managed virtual environment.

set -e

APP_NAME="Kobo Flashcards"
BUNDLE_ID="com.petersmit.kobo-flashcards"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$PROJECT_DIR/dist/$APP_NAME.app"

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Launcher script (unquoted heredoc so $PROJECT_DIR expands)
cat > "$APP_DIR/Contents/MacOS/$APP_NAME" << LAUNCHER
#!/bin/bash
cd "$PROJECT_DIR"
exec uv run python app.py
LAUNCHER
chmod +x "$APP_DIR/Contents/MacOS/$APP_NAME"

# Info.plist
cat > "$APP_DIR/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleVersion</key>
    <string>0.1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
</dict>
</plist>
PLIST

# Copy icon if it exists
if [ -f "$PROJECT_DIR/icon.icns" ]; then
    cp "$PROJECT_DIR/icon.icns" "$APP_DIR/Contents/Resources/icon.icns"
    # Add icon key to plist
    /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string icon" "$APP_DIR/Contents/Info.plist"
fi

echo "Created $APP_DIR"
echo "You can copy it to /Applications or drag it to the Dock."
