"""py2app build configuration for Kobo → Anki Flashcards.

Usage:
    python setup_py2app.py py2app
"""

from setuptools import setup

APP = ["app.py"]
DATA_FILES = [
    (".", ["main.py", "anki_export.py", "kobo_date.txt"]),
    (".streamlit", [".streamlit/secrets.toml"]),
]
OPTIONS = {
    "argv_emulation": False,
    "packages": ["streamlit", "deepl", "elevenlabs", "webview"],
    "includes": ["pyobjc"],
    "plist": {
        "CFBundleName": "Kobo Flashcards",
        "CFBundleDisplayName": "Kobo Flashcards",
        "CFBundleIdentifier": "com.petersmit.kobo-flashcards",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
    },
    # Uncomment when you have an icon:
    # "iconfile": "icon.icns",
}

setup(
    name="Kobo Flashcards",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
