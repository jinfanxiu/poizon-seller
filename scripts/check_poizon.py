#!/usr/bin/env python3
"""
Poizon .env / passport 진단. 비밀값은 출력하지 않습니다.
  uv run python scripts/check_poizon.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib  # noqa: E402

import config  # noqa: E402
importlib.reload(config)
from sellers.poizon import PoizonSeller  # noqa: E402


def main() -> int:
    dt = (config.POIZON_DUTOKEN or "").strip()
    ck = (config.POIZON_COOKIE or "").strip()
    if not dt or not ck:
        print("[NG] POIZON_DUTOKEN / POIZON_COOKIE 중 비어 있음 (config.py 경로 .env 기준으로 로드)")
        return 1
    m = re.search(r"duToken=([^;]+)", ck, re.I)
    inc = m.group(1) if m else None
    sh = (getattr(config, "POIZON_SHUMEIID", None) or "").strip()
    print("dutoken len:", len(dt))
    print("cookie len:", len(ck))
    print("POIZON_SHUMEIID set:", bool(sh), "(DevTools에 있는 shumeiid — 없으면 401 가능)")
    if inc:
        print("duToken in cookie == POIZON_DUTOKEN:", "yes" if dt == inc else "no (MISMATCH: 같은 로그인 세션에서 둘 다 복사했는지 확인)")
    else:
        print("cookie에 duToken= 없음")
    p = PoizonSeller()
    r = p.search_product("test")
    code = r.get("code")
    msg = (r or {}).get("msg")
    print("search test code:", code, "msg:", msg)
    if code == 200:
        print("[OK] Poizon search API 200")
        return 0
    print(
        "\n[정리] 401 + passport 验证失败 이면 서버가 세션을 부정한 것이며, "
        "코드 서명/헤더 이름(소문 dutoken) 이 아니라 토큰/쿠키 유효성 이슈입니다."
    )
    print(
        "권장: Network에서 200인 merchant/search 요청의 Request Headers에 있는 "
        "POIZON_DUTOKEN, POIZON_COOKIE, 그리고 shumeiid → .env에 POIZON_SHUMEIID=..."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
