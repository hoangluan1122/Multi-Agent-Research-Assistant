import asyncio
from unittest.mock import AsyncMock

import pytest
from app.services.paper_translation import translate_content
from app.services.llm_service import llm_service


def test_translation_success(monkeypatch):
    mock = AsyncMock(return_value={'title_vi': 'Phát hiện bệnh', 'abstract_vi': 'Sử dụng học sâu.'})
    monkeypatch.setattr(llm_service, 'generate_json', mock)
    result = asyncio.run(translate_content('Disease detection', 'Using deep learning.'))
    assert result['title_vi'] == 'Phát hiện bệnh'
    assert mock.call_args.kwargs['allow_mock'] is False


@pytest.mark.parametrize('value', [None, [], {}, {'raw_response': 'bad json'},
    {'title_vi': 123, 'abstract_vi': 'x'},
    {'title_vi': 'Disease detection', 'abstract_vi': 'Using deep learning.'},
    {'title_vi': 'Phát hiện bệnh', 'abstract_vi': ''}])
def test_invalid_translation_rejected(monkeypatch, value):
    monkeypatch.setattr(llm_service, 'generate_json', AsyncMock(return_value=value))
    with pytest.raises(ValueError):
        asyncio.run(translate_content('Disease detection', 'Using deep learning.'))


def test_missing_abstract_is_not_invented(monkeypatch):
    monkeypatch.setattr(llm_service, 'generate_json', AsyncMock(return_value={
        'title_vi': 'Phát hiện bệnh', 'abstract_vi': 'Invented text'}))
    assert asyncio.run(translate_content('Disease detection', None))['abstract_vi'] == ''


def test_offline_translation_does_not_use_mock(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', '')
    monkeypatch.setattr(llm_service, 'openai_client', None)
    with pytest.raises(RuntimeError):
        asyncio.run(llm_service.generate_json('Translate into Vietnamese', allow_mock=False))


# @trace: REQ-038, REQ-039
def test_generate_text_smart_fallback_normalizes_invalid_model(monkeypatch):
    """Kiểm tra tên model không tồn tại như gemini-3.7-flash được chuẩn hóa và tự động thử các model chuẩn."""
    from app.core.config import settings
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'AIzaSyFakeKeyValidFormat123456789')
    
    called_models = []
    class FakeGenaiModels:
        async def generate_content(self, model, contents, config):
            called_models.append(model)
            if model == "gemini-2.0-flash":
                class Resp:
                    text = '{"title_vi": "Cờ bạc", "abstract_vi": "Nghiên cứu"}'
                return Resp()
            raise ValueError(f"Model {model} not found")
            
    class FakeAio:
        models = FakeGenaiModels()

    class FakeClient:
        aio = FakeAio()

    monkeypatch.setattr(llm_service, 'genai_client', FakeClient())
    result = asyncio.run(llm_service.generate_json("prompt", model="gemini-3.7-flash", allow_mock=False))
    assert result.get("title_vi") == "Cờ bạc"
    assert "gemini-2.0-flash" in called_models

