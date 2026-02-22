import json
import urllib.request
from pathlib import Path
from urllib.error import URLError


class AnkiConnectError(Exception):
    """Raised when AnkiConnect returns an error or is unreachable."""


def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, **params):
    try:
        requestJson = json.dumps(request(action, **params)).encode('utf-8')
        response = json.load(urllib.request.urlopen(
            urllib.request.Request('http://127.0.0.1:8765', requestJson),
            timeout=10,
        ))
    except (URLError, ConnectionError) as e:
        raise AnkiConnectError(
            "Cannot connect to AnkiConnect. Is Anki running with the AnkiConnect add-on?"
        ) from e
    if len(response) != 2:
        raise AnkiConnectError('response has an unexpected number of fields')
    if 'error' not in response:
        raise AnkiConnectError('response is missing required error field')
    if 'result' not in response:
        raise AnkiConnectError('response is missing required result field')
    if response['error'] is not None:
        raise AnkiConnectError(response['error'])
    return response['result']


def export_to_anki(flashcards: list[dict[str, str]]) -> None:
    """Create Flashcards in Anki based on the data provided.
    Input format: {"sentence": "", "translation": "", "audio_path": ""}

    Raises AnkiConnectError if Anki is unreachable or returns an error.
    """
    for i, flashcard in enumerate(flashcards):
        audio_path = Path(flashcard["audio_path"])
        if not audio_path.exists():
            raise AnkiConnectError(f"Audio file not found: {audio_path}")
        audio_file_name = audio_path.name

        try:
            invoke(
                "storeMediaFile",
                filename=audio_file_name,
                path=str(audio_path.resolve()),
            )
        except AnkiConnectError as e:
            raise AnkiConnectError(
                f"Failed to store audio for flashcard {i + 1}: {e}"
            ) from e

        try:
            invoke(
                "addNote",
                note={
                    "deckName": "ZZZ_inbox",
                    "modelName": "Basic",
                    "fields": {
                        "Front": f"[sound:{audio_file_name}]",
                        "Back": flashcard["sentence"] + "<br><br>" + flashcard["translation"],
                    },
                },
            )
        except AnkiConnectError as e:
            raise AnkiConnectError(
                f"Failed to add flashcard {i + 1}: {e}"
            ) from e