import io
import json
from unittest.mock import patch
from workplace_ops import ai

class FakeResponse:
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def read(self, *_): return json.dumps({'models': [{'name': 'llama3.2:1b'}]}).encode()


def test_diagnostics_selects_exact_model(monkeypatch):
    monkeypatch.setenv('WORKPLACE_AI_MODE', 'ollama')
    monkeypatch.setenv('WORKPLACE_OLLAMA_MODEL', 'llama3.2:1b')
    with patch.object(ai, 'urlopen', return_value=FakeResponse()):
        result = ai.diagnostics()
    assert result['mode'] == 'ollama-local'
    assert result['ollama_reachable'] is True
    assert result['model_installed'] is True
    assert result['configured_model'] == 'llama3.2:1b'
    assert result['loopback_only'] is True


def test_diagnostics_detects_model_mismatch(monkeypatch):
    monkeypatch.setenv('WORKPLACE_OLLAMA_MODEL', 'llama3.2')
    with patch.object(ai, 'urlopen', return_value=FakeResponse()):
        result = ai.diagnostics()
    assert result['ollama_reachable'] is True
    assert result['model_installed'] is False


def test_diagnostics_handles_missing_service(monkeypatch):
    from urllib.error import URLError
    with patch.object(ai, 'urlopen', side_effect=URLError('not up')):
        result = ai.diagnostics()
    assert result['ollama_reachable'] is False
    assert result['model_installed'] is False
