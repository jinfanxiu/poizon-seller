import json
import re
from enum import Enum
from typing import Any

import requests
from pydantic import BaseModel

from models.product import ProductInfo, ProductOption, SalesMetrics
from sellers.base import BaseSeller
from utils.matching import find_best_match, normalize_text
from utils.constants import BrandEnum


class MusinsaRankingType(Enum):
    ALL = "199"
    NEW = "200"
    RISING = "201"


class MusinsaRankingItem(BaseModel):
    product_id: str
    brand_name: str
    product_name: str
    price: int
    product_url: str
    image_url: str | None = None


class MusinsaSeller(BaseSeller):
    def __init__(self) -> None:
        super().__init__("Musinsa")
        # 랭킹 섹션 데이터를 가져오는 API URL 템플릿
        self.ranking_section_url = "https://api.musinsa.com/api2/hm/web/v5/pans/ranking?storeCode=musinsa&sectionId={section_id}&contentsId=&categoryCode=000&subPan=product&gf=A&ageBand=AGE_BAND_ALL"

    def search_by_brand(self, brand: BrandEnum, page: int = 1) -> list[ProductInfo]:
        """
        브랜드 키워드로 상품을 검색하고, 검색된 모든 상품의 상세 정보를 리스트로 반환합니다.
        페이지네이션을 지원합니다.
        """
        keyword = brand.value
        try:
            # 1. 검색 API 호출
            search_results = self._call_search_api(keyword, page=page)
            if not search_results:
                print(f"No search results found for brand: {keyword} (page {page})")
                return []

            print(f"Search API returned {len(search_results)} items for brand: {keyword} (page {page})")

            # 2. 검색된 모든 상품 ID 수집
            product_ids = []
            for item in search_results:
                product_id = str(item.get("goodsNo"))
                if product_id:
                    product_ids.append(product_id)

            # 3. 모든 상품의 상세 정보 조회
            product_infos = []
            for pid in product_ids:
                p_info = self.get_product_info(pid)
                if p_info:
                    product_infos.append(p_info)

            return product_infos

        except Exception as e:
            print(f"Error in search_by_brand: {e}")
            return []

    def search_product(self, keyword: str) -> list[ProductInfo]:
        """
        키워드(모델 번호 등)로 상품을 검색하고, 매칭되는 모든 상품의 상세 정보를 리스트로 반환합니다.
        상품명에서 모델 번호를 우선 추출하여 매칭을 시도하고, 실패 시 상세 정보를 조회하여 확인합니다.
        """
        try:
            # 1. 검색 API 호출
            search_results = self._call_search_api(keyword)
            if not search_results:
                print(f"No search results found for keyword: {keyword}")
                return []

            print(f"Search API returned {len(search_results)} items. Filtering by keyword: {keyword}")

            # 2. 매칭되는 상품 ID 수집
            matched_product_ids = []
            normalized_keyword = normalize_text(keyword)

            # 상위 20개 아이템 확인 (범위 확장)
            for item in search_results[:20]:
                product_id = str(item.get("goodsNo"))
                goods_name = item.get("goodsName", "")
                
                is_match = False
                
                # 1차 시도: 상품명에 키워드가 포함되어 있는지 확인 (가장 느슨한 조건)
                # 모델 번호 검색 시 상품명에 모델 번호가 포함되는 경우가 대부분임
                if normalized_keyword in normalize_text(goods_name):
                    is_match = True
                
                # 2차 시도: 상품명에서 추출한 모델 번호와 정확히 일치하는지 확인
                if not is_match:
                    extracted_model_no = self._extract_model_no_from_name(goods_name)
                    if extracted_model_no and normalize_text(extracted_model_no) == normalized_keyword:
                        is_match = True
                
                # 3차 시도: 상세 페이지 조회하여 style_no 확인 (정확도 확보)
                # 1, 2차에서 매칭되지 않았더라도 상위 3개는 확인해볼 가치가 있음
                if not is_match and search_results.index(item) < 3:
                    base_info = self._fetch_product_base_info(product_id)
                    if base_info:
                        style_no = base_info.get("style_no", "")
                        if style_no and normalize_text(style_no) == normalized_keyword:
                            is_match = True

                if is_match:
                    if product_id not in matched_product_ids:
                        matched_product_ids.append(product_id)

            if not matched_product_ids:
                print(f"No matching product found for keyword: {keyword}")
                return []

            print(f"Found {len(matched_product_ids)} matching products: {matched_product_ids}. Fetching details...")

            # 3. 매칭된 모든 상품의 상세 정보 조회
            product_infos = []
            for pid in matched_product_ids:
                p_info = self.get_product_info(pid)
                if p_info:
                    product_infos.append(p_info)

            return product_infos

        except Exception as e:
            print(f"Error in search_product: {e}")
            return []

    def _extract_model_no_from_name(self, goods_name: str) -> str | None:
        """
        상품명에서 모델 번호를 추출합니다.
        무신사 상품명 패턴 예: '클럽 프렌치 테리 크루 M - 블랙:화이트 / FN3889-010'
        """
        if "/" in goods_name:
            # 슬래시 뒤의 마지막 부분을 가져옴
            candidate = goods_name.split("/")[-1].strip()
            # 모델 번호처럼 생겼는지 간단한 체크 (길이 등)
            if len(candidate) > 3:
                return candidate
        return None

    def _call_search_api(self, keyword: str, page: int = 1) -> list[dict[str, Any]]:
        """무신사 검색 API를 호출합니다."""
        url = "https://api.musinsa.com/api2/dp/v1/plp/goods"
        params = {
            "gf": "A",
            "keyword": keyword,
            "sortCode": "POPULAR",
            "isUsed": "false",
            "page": str(page),
            "size": "60",
            "testGroup": "",
            "seen": "0",
            "seenAds": "",
            "caller": "SEARCH"
        }
        headers = {
            "accept": "application/json",
            "accept-language": "ko-KR,ko;q=0.9,zh-CN;q=0.8,zh;q=0.7,en-US;q=0.6,en;q=0.5",
            "origin": "https://www.musinsa.com",
            "referer": "https://www.musinsa.com/",
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Cookie": "_gf=A" 
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("list", [])
        except Exception as e:
            print(f"Error calling search API: {e}")
            return []

    def get_product_info(self, product_id: str) -> ProductInfo | None:
        """
        상품 상세 정보를 조회합니다.
        HTML 파싱을 통해 기본 정보를 얻고, API를 통해 옵션 및 재고 정보를 조회하여 결합합니다.
        """
        try:
            # 1. 기본 정보 (HTML 파싱)
            base_info = self._fetch_product_base_info(product_id)
            if not base_info:
                print(f"Failed to fetch base info for {product_id}")
                return None

            # 2. 옵션 정보
            options_data = self._fetch_options(product_id)
            if not options_data:
                print(f"Failed to fetch options for {product_id}")
                return None

            # 3. 재고 정보
            # 모든 옵션 값 ID 수집
            all_option_value_nos = []
            basic_options = options_data.get("data", {}).get("basic", [])
            for basic_option in basic_options:
                for value in basic_option.get("optionValues", []):
                    all_option_value_nos.append(value["no"])

            inventory_data = None
            if all_option_value_nos:
                inventory_data = self._fetch_inventory(product_id, all_option_value_nos)

            # 4. 옵션 생성
            product_options = self._build_product_options(
                product_id, base_info, options_data, inventory_data
            )

            # 5. ProductInfo 반환
            return ProductInfo(
                platform=self.name,
                model_no=base_info.get("style_no", product_id), # style_no 사용, 없으면 ID
                title=base_info["title"],
                image_url=base_info["image_url"],
                product_url=f"https://www.musinsa.com/products/{product_id}",
                options=product_options,
                sales_metrics=SalesMetrics(
                    velocity_score=0.0,
                    rank="0",
                    recent_sales_count=0,
                ),
            )

        except Exception as e:
            print(f"Error in get_product_info for {product_id}: {e}")
            return None

    def _fetch_product_base_info(self, product_id: str) -> dict[str, Any] | None:
        """상품 상세 페이지 HTML에서 __NEXT_DATA__를 추출하여 기본 정보를 파싱합니다."""
        url = f"https://www.musinsa.com/products/{product_id}"
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # __NEXT_DATA__ 추출
            start_marker = '<script id="__NEXT_DATA__" type="application/json">'
            end_marker = "</script>"
            start_index = response.text.find(start_marker)
            if start_index == -1:
                return None
            start_index += len(start_marker)
            end_index = response.text.find(end_marker, start_index)
            if end_index == -1:
                return None

            json_str = response.text[start_index:end_index]
            data = json.loads(json_str)

            meta_data = (
                data.get("props", {})
                .get("pageProps", {})
                .get("meta", {})
                .get("data", {})
            )
            if not meta_data:
                return None

            goods_nm = meta_data.get("goodsNm", "")
            style_no = meta_data.get("styleNo", "") # 스타일 번호 추출
            goods_images = meta_data.get("goodsImages", [])
            image_url = (
                f"https:{goods_images[0]['imageUrl']}" if goods_images else ""
            )
            
            # goodsPrice가 None일 수 있으므로 안전하게 처리
            goods_price = meta_data.get("goodsPrice") or {}
            
            # 가격 우선순위: couponPrice > salePrice > normalPrice
            # couponPrice가 null일 수도 있으므로 get으로 가져온 후 체크
            coupon_price = goods_price.get("couponPrice")
            sale_price = goods_price.get("salePrice", 0)
            normal_price = goods_price.get("normalPrice", 0)
            
            final_price = normal_price
            if coupon_price and coupon_price > 0:
                final_price = coupon_price
            elif sale_price > 0:
                final_price = sale_price

            return {
                "title": goods_nm,
                "style_no": style_no,
                "image_url": image_url,
                "price": final_price,
            }
        except Exception as e:
            print(f"Error fetching base info: {e}")
            return None

    def _fetch_options(self, product_id: str) -> dict[str, Any] | None:
        """상품 옵션 정보를 조회합니다."""
        # optKindCd=CLOTHES는 의류 기준이며, 다른 카테고리일 경우 변경이 필요할 수 있음
        url = f"https://goods-detail.musinsa.com/api2/goods/{product_id}/options?goodsSaleType=SALE&optKindCd=CLOTHES"
        headers = {
            "accept": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "referer": f"https://www.musinsa.com/products/{product_id}",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching options: {e}")
            return None

    def _fetch_inventory(
        self, product_id: str, option_value_nos: list[int]
    ) -> dict[str, Any] | None:
        """상품 재고 정보를 조회합니다."""
        url = f"https://goods-detail.musinsa.com/api2/goods/{product_id}/options/v2/prioritized-inventories"
        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "referer": f"https://www.musinsa.com/products/{product_id}",
            "origin": "https://www.musinsa.com",
        }
        payload = {"optionValueNos": option_value_nos}
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching inventory: {e}")
            return None

    def _build_product_options(
        self,
        product_id: str,
        base_info: dict[str, Any],
        options_data: dict[str, Any],
        inventory_data: dict[str, Any] | None,
    ) -> list[ProductOption]:
        """옵션 데이터와 재고 데이터를 결합하여 ProductOption 리스트를 생성합니다."""
        product_options = []

        # 재고 정보 매핑 (productVariantId -> inventory info)
        inventory_map = {}
        if inventory_data and "data" in inventory_data:
            for inv in inventory_data["data"]:
                # API 응답의 productVariantId가 optionItems의 no와 매칭됨
                inventory_map[inv["productVariantId"]] = inv

        option_items = options_data.get("data", {}).get("optionItems", [])
        basic_options = options_data.get("data", {}).get("basic", [])

        for item in option_items:
            variant_id = item.get("no")
            value_nos = item.get("optionValueNos", [])

            # 사이즈/컬러 구분 로직
            size_parts = []
            color_parts = []

            for basic in basic_options:
                opt_name = basic.get("name", "")
                for val in basic.get("optionValues", []):
                    if val["no"] in value_nos:
                        if "사이즈" in opt_name:
                            size_parts.append(val["name"])
                        elif "색상" in opt_name or "컬러" in opt_name:
                            color_parts.append(val["name"])
                        else:
                            # 기타 옵션은 사이즈에 붙임
                            size_parts.append(val["name"])

            size_name = " / ".join(size_parts) if size_parts else "ONE SIZE"
            color_name = " / ".join(color_parts) if color_parts else "ONE COLOR"

            # 재고 확인
            inv_info = inventory_map.get(variant_id)
            stock_status = "IN_STOCK"
            stock_quantity = None  # 남은 수량 (None이면 여유 있음)

            if inv_info:
                if inv_info.get("outOfStock"):
                    stock_status = "OUT_OF_STOCK"
                
                # remainQuantity가 있으면 설정 (null이면 None으로 유지)
                remain_qty = inv_info.get("remainQuantity")
                if remain_qty is not None:
                    stock_quantity = int(remain_qty)

            # 가격은 기본 가격 + 옵션 추가금
            option_price = base_info["price"] + item.get("price", 0)

            product_options.append(
                ProductOption(
                    sku_id=str(variant_id),
                    size=size_name,
                    color=color_name,
                    price=int(option_price),
                    currency="KRW",
                    stock_status=stock_status,
                    stock_quantity=stock_quantity,
                    image_url=base_info["image_url"],
                )
            )

        return product_options

    def _parse_product(self, item: dict[str, Any]) -> ProductInfo | None:
        """
        무신사 상품 JSON 데이터를 ProductInfo 객체로 변환합니다.
        제공된 JSON 구조(info, image 객체 포함)에 맞춰 파싱합니다.
        """
        try:
            # info 객체와 image 객체 추출
            info = item.get("info", {})
            image = item.get("image", {})

            # 필수 필드 추출
            # id: 상품 ID (최상위 id 필드 사용)
            product_id = str(item.get("id") or "")
            # productName: 상품명
            title = info.get("productName") or ""
            # url: 이미지 URL
            image_url = image.get("url") or ""

            if not product_id or not title:
                return None

            # 가격 정보 추출 (finalPrice)
            price = info.get("finalPrice") or 0

            # 랭킹 정보 추출
            rank = str(image.get("rank") or 0)

            # 옵션 생성 (목록 조회 시점에서는 사이즈/색상 상세 정보를 알 수 없으므로 대표값 설정)
            option = ProductOption(
                sku_id=product_id,  # SKU ID를 상품 ID로 대체
                size="ALL",  # 사이즈 정보 없음
                color="ALL",  # 색상 정보 없음
                price=int(price),
                currency="KRW",
                stock_status="IN_STOCK",
                image_url=image_url,
            )

            sales_metrics = SalesMetrics(
                velocity_score=0.0,
                rank=rank,
                recent_sales_count=0,  # 판매량 정보는 상세 페이지나 별도 필드 필요
            )

            return ProductInfo(
                platform=self.name,
                model_no=product_id,
                title=title,
                image_url=image_url,
                product_url=f"https://www.musinsa.com/app/goods/{product_id}",
                options=[option],
                sales_metrics=sales_metrics,
            )
        except Exception as e:
            print(f"Error parsing product {item.get('id')}: {e}")
            return None

    def fetch_ranking(
        self, ranking_type: MusinsaRankingType, brand_names: list[str] | None = None
    ) -> list[MusinsaRankingItem]:
        url = self.ranking_section_url.format(section_id=ranking_type.value)

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ko-KR,ko;q=0.9,zh-CN;q=0.8,zh;q=0.7,en-US;q=0.6,en;q=0.5",
            "origin": "https://www.musinsa.com",
            "priority": "u=1, i",
            "referer": "https://www.musinsa.com/",
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Cookie": "_gf=A; tr[vid]=694d0f4831b256.77282923; tr[vd]=1766657864; _gcl_au=1.1.2120483720.1766657864; _ga=GA1.1.238406552.1766657864; _fwb=1566kGoNaFmDZXuVD02lCHZ.1766657864629; _kmpid=km|musinsa.com|1766657864631|1ef82937-7c15-43c6-82f7-906037ab7f4a; _fbp=fb.1.1766657865269.625677774637477089; _pin_unauth=dWlkPVpUZGxZbUZsTmpNdE9UaGlNUzAwTXpObExXRmhNR0V0TldNeFlXSTVaV1l3TUdZMw; viewKind=3GridView; _hjSessionUser_1491926=eyJpZCI6Ijc5Yzg5ODgxLThlZGQtNTNkNC1iZmJmLThmYzUzY2MxZmQ0MSIsImNyZWF0ZWQiOjE3NjY2NTc4NjUyNTcsImV4aXN0aW5nIjp0cnVlfQ==; _tt_enable_cookie=1; _ttp=01KDAG86R3KTCEX9AZ6XEC9N0G_.tt.1; one_pc=TVVTSU5TQQ; app_atk=n2dSDpXeOk86GZi8k0UF5XgZOsfFaQp1VZFYK5ZcD0YOb2WZ6Ct89PHMTjK7Da0mahd3OQs9sefoZRrCLvvse9GB9YHhmLa4e5eiYkjoyPUaQHmksGN0pf7mSSFs2ul227TieSt7kMw3a1XwGL7%2Bs7izH7KYtkcGuMKSn9HF0M41OB0vssBYd9FTORgfxZ8X2Nf%2B3lhpOcNYOmmjqzQS4swapzUrMa8TjMwoZsmVAWkWaYSYTxtI%2FKOtJtIVTSEvMhNDB2Vsa%2FZvzUIOW2uBUGffKbh0CZUSzlbPHdsMGSIp3Miiso0dWGRAMGpxyJwCVE7Zb9obZVLgTGMbjJyPEjfKv9X5sMNO%2Flm1Cj8ggSsJb1kvL6WK9ouaoIjt%2F7l3Xg2OVqLAG6tjRaUi5hzTLDy0PdB%2FWu863jhObHSTWKDmPPX0pRFN1Vr12BCeWebuB4yFV4OhxvkIwqONxYde29yPyEAa01KPQt8FKTRSkvSfNtVbzOquVH4NLnVm%2BJVdsDI70zh3lYv9gWUmd%2B36MPPUmjrFEhvLgqedG%2Fr82gQBFDrhJwxUej3pXeis%2Bl%2FUK0ShPuPLhTMzHRHENMGCLUEMIPduuqC1Hp1vx8Fe9IDfPGwUNcg14TvYr8TUF%2F1wP3DlCh6WwfE4rEZbDhf6fCmAOEdFKonCOpeEWA%2FYH5zUrYBOk1nzG299xt3imD2DLje1WhwkSstEmpBGqCwgnBKK7DcxwGWR7kt%2FUsgOAblPc8vJPYl4kFCgAlrqk5JsRJTUw4hAxcwB3TGJTSnZ1w%3D%3D; app_rtk=08061d3c5b0c329fa75d22ee45053f9aa4120688; mss_last_login=20260107; cart_no=DZlGUx%2F8SlkXNKA7XkqwyZSHdiMKB0Z%2BMYyaUH4NHyw%3D; _ds_sessions=y; ab.storage.deviceId.1773491f-ef03-4901-baf8-dbf84e1de25b=%7B%22g%22%3A%224a91e4ba-f6f3-131e-9bcf-464fb37369bc%22%2C%22c%22%3A1766657891359%2C%22l%22%3A1769223750210%7D; ab.storage.userId.1773491f-ef03-4901-baf8-dbf84e1de25b=%7B%22g%22%3A%22cbe76bdf2183c0598040ded22a66622a%22%2C%22c%22%3A1767769355114%2C%22l%22%3A1769223750210%7D; mss_mac=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJjYmU3NmJkZjIxODNjMDU5ODA0MGRlZDIyYTY2NjIyYSIsImhhc2hlZFVpZCI6IjkwZWZiNWY5NDE1YTcwNzIxZTYxYzY2YjVlZWE3YzIzNjY4ODY1ZmFmN2MwNWRjNjk5YTMxNjc2YjFiNWYzNTQiLCJoYXNoZWRFbWFpbCI6ImUxZWNjOGNlZDQ2YTgxYTUwNjQ4ZjQxZjE4YWY2MTc3ZGI1OWMzZjlmOTU3ZjE5NWRlODgzZDI2MDBiYjlmMWMiLCJnZW5kZXIiOiJNIiwib3JkZXJDb3VudCI6IjE2NzIiLCJzZWxmQ2VydGlmeSI6dHJ1ZSwiaGFzaElkIjoiY2JlNzZiZGYyMTgzYzA1OTgwNDBkZWQyMmE2NjYyMmEiLCJtZW1iZXJHcm91cExpc3QiOlsiQkFTSUMiXSwib25lbWVtYmVySGFzaElkIjoiZDlmYWYyMGRhMDdjNjhjMDY0N2RiODc3ZWZmY2JhZDU2ZTFiMzkxNjdiMGQzYjA2YjU4NTdhODMyMGViZWRmNiIsImJpcnRoWWVhciI6IjE5OTAiLCJvcmRlckFtb3VudFJhbmdlIjoiMjY1MzDrp4zsm5DrjIAiLCJuaWNrbmFtZSI6IuyLrOqwge2VnO2ZjeuMgOqzoOq4gCIsImFnZUJhbmQiOiIzNSIsImdyb3VwTGV2ZWwiOiI5IiwiZXhwIjoxODAwNzYwMTc1LCJoYXNoZWRQaG9uZU51bWJlciI6IjhjNGRjNTI2YWE2MmE2NmJjNmQwYWZmNzAwNTUxNWVmMDgzNTRjZWE4NWZhOTFmZDQ0NDMxYzQwZGY3NmI5M2EiLCJpYXQiOjE3NjkyMjQxNzUsImFkQ29uc2VudFluIjoiWSIsInJlZ2lzdGVyRGF0ZSI6IjIwMjMtMDMtMzEiLCJ1c2VyQnVja2V0IjoiMzcifQ.G-Xz48ew8URJvv4iwYxx_0dWAHAlOxUyvRa-j6c60Wc; SimilarGoodsTooltipClosed=true; brand_notice_suare_43796=closed; cto_bundle=Hcx5yl9DanFxV2FWaWF5NWNRUU5qZiUyRkw0WnNIbDYxRGwwZ3AzZlpOa2lsTDZDRXlkenQ1ckNIUndoMU5MOWJIUm1kZ3I5SGxTTFpVOU5DdzZBdnRWRGMlMkZwYktQNWh4eWcxRGElMkZneXdMM2pwa0UlMkIyTVZuRllhVWRkaklyWHlIdEtBZUdndG5LWnhySnI5WmYwZkl4dkVYZG10ZyUzRCUzRA; ab.storage.sessionId.1773491f-ef03-4901-baf8-dbf84e1de25b=%7B%22g%22%3A%222db74505-ef86-9f41-1a3f-75b0192ba3d9%22%2C%22e%22%3A1769227749993%2C%22c%22%3A1769223750209%2C%22l%22%3A1769225949993%7D; ttcsid=1769224175191::Sf84H50PKTjtiiid6sgf.13.1769225953438.0; ttcsid_CF2AOI3C77UCCRP8DVQG=1769224175191::5vcYRjrDn49CLLg6QRRl.13.1769225953438.1; tr[vt]=1769229555; tr[vc]=3; tr[pv]=1; AMP_74a056ea4a=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJkNzM5MmY1Yi1hMmJmLTRjYzMtYTBiMS0yY2E5Yzc5OTExMDYlMjIlMkMlMjJ1c2VySWQlMjIlM0ElMjJjYmU3NmJkZjIxODNjMDU5ODA0MGRlZDIyYTY2NjIyYSUyMiUyQyUyMnNlc3Npb25JZCUyMiUzQTE3NjkwMDc0MTc0NjYlMkMlMjJvcHRPdXQlMjIlM0FmYWxzZSUyQyUyMmxhc3RFdmVudFRpbWUlMjIlM0ExNzY5MDA3NDE3NDY3JTJDJTIybGFzdEV2ZW50SWQlMjIlM0E3JTJDJTIycGFnZUNvdW50ZXIlMjIlM0EwJTdE; _hjSession_1491926=eyJpZCI6Ijc2YTYzM2YzLTgwMTctNGQ5My1hM2RmLTIyMzVhNjdmNjNjOCIsImMiOjE3NjkyMjk1NTYyODQsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; _ga_8PEGV51YTJ=GS2.1.s1769229117$o20$g0$t1769229556$j60$l0$h0; _gf=A",
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Failed to fetch ranking: {e}")
            return []

        results = []
        modules = data.get("data", {}).get("modules", [])

        for module in modules:
            # Check if module is a product column
            if not module.get("id", "").startswith("MULTICOLUMN"):
                continue

            items = module.get("items", [])
            for item in items:
                if not item.get("type", "").startswith("PRODUCT_COLUMN"):
                    continue

                info = item.get("info", {})
                brand_name = info.get("brandName", "")

                # Brand filtering
                if brand_names:
                    normalized_brand = normalize_text(brand_name)
                    normalized_targets = [normalize_text(b) for b in brand_names]
                    
                    # 포함 관계 확인 (예: "나이키" in "나이키(Nike)")
                    is_matched = any(t in normalized_brand or normalized_brand in t for t in normalized_targets)
                    if not is_matched:
                        continue

                product_id = str(item.get("id", ""))
                product_name = info.get("productName", "")
                price = info.get("finalPrice", 0)
                image_url = item.get("image", {}).get("url", "")

                ranking_item = MusinsaRankingItem(
                    product_id=product_id,
                    brand_name=brand_name,
                    product_name=product_name,
                    price=int(price),
                    product_url=f"https://www.musinsa.com/app/goods/{product_id}",
                    image_url=image_url,
                )
                results.append(ranking_item)

        return results


if __name__ == "__main__":
    musinsa_seller = MusinsaSeller()

    # Example usage: Search product
    keyword = "FN3889-010"
    print(f"Searching for {keyword}...")
    product_infos = musinsa_seller.search_product(keyword)
    
    if product_infos:
        print(f"Found {len(product_infos)} products.")
        for p in product_infos:
            print(f"- {p.title} ({p.model_no})")
            for opt in p.options:
                print(f"  {opt.size} / {opt.color}: {opt.price} ({opt.stock_status})")
    else:
        print("Product not found.")
