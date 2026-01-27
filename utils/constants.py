from enum import Enum

class BrandEnum(Enum):
    NIKE = "나이키"
    ADIDAS = "아디다스"
    DESCENTE = "데상트"
    NORTHFACE = "노스페이스"
    KOLONSPORT = "코오롱스포츠"
    SALOMON = "살로몬"
    PUMA = "푸마"
    NEWBALANCE = "뉴발란스"
    SUARE = "수아레"
    FILA = "휠라"
    ARCTERYX = "아크테릭스"

# 타겟 브랜드 목록 (BrandEnum에서 자동 생성)
TARGET_BRANDS = [b.value for b in BrandEnum]

# 색상 매핑 테이블 (표준값: [동의어 리스트])
COLOR_MAP = {
    "black": ["blk", "블랙", "검정", "noir", "nero", "coreblack", "black"],
    "white": ["wht", "화이트", "흰색", "blanc", "white"],
    "grey": ["gry", "그레이", "회색", "charcoal", "차콜", "darkgrey", "lightgrey", "grey", "gray"],
    "navy": ["nvy", "네이비", "곤색", "navy"],
    "red": ["red", "레드", "빨강", "rouge"],
    "blue": ["blu", "블루", "파랑", "blue"],
    "green": ["grn", "그린", "초록", "green"],
    "yellow": ["ylw", "옐로우", "노랑", "yellow"],
    "orange": ["org", "오렌지", "주황", "orange"],
    "purple": ["ppl", "퍼플", "보라", "purple"],
    "beige": ["beg", "베이지", "lbeige", "lightbeige", "beige"],
    "cream": ["crm", "크림", "cream"],
    "ivory": ["ivr", "아이보리", "ivory"],
    "silver": ["slv", "실버", "은색", "silver"],
    "gold": ["gld", "골드", "금색", "gold"],
    "brown": ["brn", "브라운", "갈색", "brown"],
    "khaki": ["khk", "카키", "khaki"],
    "pink": ["pnk", "핑크", "분홍", "pink"],
    "mint": ["mnt", "민트", "mint"],
}

# EU -> KR 사이즈 변환 테이블 (신발 기준)
EU_TO_KR_MAP = {
    "35": "220", "35.5": "225",
    "36": "230", "36.5": "235",
    "37": "235", "37.5": "240",
    "38": "240", "38.5": "245",
    "39": "245", "39.5": "250",
    "40": "250", "40.5": "255",
    "41": "260", "41.5": "265",
    "42": "265", "42.5": "270",
    "43": "275", "43.5": "280",
    "44": "280", "44.5": "285",
    "45": "290", "45.5": "295",
    "46": "300",
}

# 의류 사이즈 변환 (EU/US -> KR)
CLOTHING_SIZE_MAP = {
    "XXS": "80", "XS": "85", "S": "90", "M": "95", "L": "100",
    "XL": "105", "XXL": "110", "2XL": "110", "3XL": "115"
}

# 의류 사이즈 역변환 (KR -> EU/US) - 매칭 보조용
KR_TO_CLOTHING_SIZE_MAP = {
    "80": "XXS", "85": "XS", "90": "S", "95": "M", "100": "L",
    "105": "XL", "110": "XXL", "115": "3XL"
}
