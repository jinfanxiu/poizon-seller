"""Pytest. 기본 ``pytest`` 는 ``-m e2e`` 를 제외(``pyproject.toml``)."""


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "e2e: Poizon/무신사 등 실 API(크리덴셜·네트워크)")
