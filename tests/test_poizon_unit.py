"""PoizonSeller 단위: 네트워크 없이 서명·헤더."""

import re

import pytest

import config
from sellers.poizon import PoizonSeller


def _make_seller(**kwargs) -> PoizonSeller:
    defaults: dict = {
        "dutoken": "D" * 20,
        "cookie": "sk=skval123; other=x; duToken=ddtoken",
        "shumeiid": "shumeiid_test_123",
        "referer": "https://seller.poizon.com/main/goods/search",
    }
    defaults.update(kwargs)
    return PoizonSeller(**defaults)


def test_get_headers_includes_dutoken_sk_shumeiid_lang() -> None:
    p = _make_seller()
    h = p._get_headers()
    assert h["dutoken"] == "D" * 20
    assert h["Cookie"] == p.cookie
    assert h.get("sk") == "skval123"
    assert h.get("shumeiid") == "shumeiid_test_123"
    assert h.get("lang") == "ko"
    assert "goods/search" in h.get("referer", "")


def test_sk_header_extracted_from_cookie() -> None:
    p = PoizonSeller(
        dutoken="t",
        cookie="a=b; sk=my_session_key; c=d",
        shumeiid="s",
    )
    assert p._get_headers()["sk"] == "my_session_key"


def test_shumeiid_from_config_when_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "POIZON_SHUMEIID", "from_cfg", raising=False)
    p = PoizonSeller(dutoken="t", cookie="sk=1; t=2")
    assert p._get_headers().get("shumeiid") == "from_cfg"


def test_shumeiid_kwarg_overrides_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "POIZON_SHUMEIID", "from_cfg", raising=False)
    p = PoizonSeller(dutoken="t", cookie="sk=1; t=2", shumeiid="over")
    assert p._get_headers()["shumeiid"] == "over"


def test_generate_sign_stable_and_32char_hex() -> None:
    p = _make_seller()
    payload = {
        "current": 1,
        "identifyStatusEnable": True,
        "keyword": "JI0079",
        "page": 1,
        "pageNum": 1,
        "pageSize": 10,
    }
    a = p._generate_sign(payload)
    b = p._generate_sign(payload)
    assert a == b
    assert re.fullmatch(r"[0-9a-f]{32}", a) is not None
    # 키 순서와 무관 동일
    c = p._generate_sign(
        {
            "pageNum": 1,
            "identifyStatusEnable": True,
            "pageSize": 10,
            "keyword": "JI0079",
            "current": 1,
            "page": 1,
        }
    )
    assert a == c


def test_referer_override() -> None:
    p = PoizonSeller(
        dutoken="t",
        cookie="sk=x",
        shumeiid="s",
        referer="https://custom.example.com/path",
    )
    assert p.base_headers["referer"] == "https://custom.example.com/path"
