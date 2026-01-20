import hashlib
import json
import re
import time
from typing import Any

import requests


class PoizonSeller:
    SALT = "048a9c4943398714b356a696503d2d36"

    def __init__(self, dutoken: str, cookie: str):
        self.dutoken = dutoken
        self.cookie = cookie

        self.base_headers = {
            'accept': 'application/json',
            'accept-language': 'ko-KR,ko;q=0.9,zh-CN;q=0.8,zh;q=0.7,en-US;q=0.6,en;q=0.5',
            'channel': 'pc',
            'clientid': 'global',
            'content-type': 'application/json;charset=UTF-8',
            'language': 'ko',
            'origin': 'https://seller.poizon.com',
            'priority': 'u=1, i',
            'referer': 'https://seller.poizon.com/',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'syscode': 'DU_USER_GLOBAL',
            'timezone': 'GMT+09:00',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }

    def update_credentials(self, dutoken: str = None, cookie: str = None):
        if dutoken is not None:
            self.dutoken = dutoken
        if cookie is not None:
            self.cookie = cookie

    def _get_headers(self):
        headers = self.base_headers.copy()
        headers['dutoken'] = self.dutoken
        headers['Cookie'] = self.cookie
        return headers

    def _generate_sign(self, payload_dict: dict[str, Any]) -> str:
        sorted_keys = sorted(payload_dict.keys())
        sign_str = ""
        for k in sorted_keys:
            val = payload_dict[k]
            if val is None:
                continue

            if isinstance(val, list):
                if not val:
                    sign_str += f"{k}"
                else:
                    sorted_list = sorted(
                        [json.dumps(x, separators=(',', ':')) if isinstance(x, (dict, list)) else str(x) for x in val])
                    sign_str += f"{k}{','.join(sorted_list)}"
            elif isinstance(val, dict):
                sign_str += f"{k}{json.dumps(val, separators=(',', ':'))}"
            else:
                if isinstance(val, bool):
                    sign_str += f"{k}{str(val).lower()}"
                else:
                    sign_str += f"{k}{val}"

        sign_str += self.SALT
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    def _send_request(self, url: str, payload_dict: dict[str, Any]) -> dict[str, Any]:
        sign = self._generate_sign(payload_dict)
        final_url = f"{url}?sign={sign}"

        payload_json = json.dumps(payload_dict, separators=(',', ':'))

        try:
            response = requests.post(final_url, headers=self._get_headers(), data=payload_json)
            response.raise_for_status()
            time.sleep(2)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending request: {e}")
            return {}

    def search_product(self, keyword: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        url = "https://seller.poizon.com/api/v1/h5/gw/intl-merchant-platform/oversea/aurora-spu/merchant/search"

        payload = {
            "pageNum": page,
            "identifyStatusEnable": True,
            "pageSize": page_size,
            "keyword": keyword,
            "current": page,
            "page": page
        }

        return self._send_request(url, payload)

    def find_matching_product(self, product_list: list[dict[str, Any]], search_keyword: str) -> dict[str, Any] | None:
        import difflib

        if not product_list or not search_keyword:
            return None

        def normalize(text: str) -> str:
            if not text:
                return ""
            return re.sub(r'[^a-z0-9]', '', str(text).lower())

        target_keyword = normalize(search_keyword)
        if not target_keyword:
            return None

        for product in product_list:
            article_number = product.get('articleNumber')
            if article_number and normalize(article_number) == target_keyword:
                return product

        if len(target_keyword) <= 4:
            return None

        best_match = None
        highest_score = 0.0
        THRESHOLD = 0.8

        for product in product_list:
            article_number = product.get('articleNumber')
            if not article_number:
                continue

            norm_article = normalize(article_number)
            score = difflib.SequenceMatcher(None, target_keyword, norm_article).ratio()

            if score >= THRESHOLD and score > highest_score:
                highest_score = score
                best_match = product

        return best_match

    def query_sale_now_info(self, spu_id: int) -> dict[str, Any]:
        """
        globalSpuId를 사용하여 상품의 상세 판매 정보(사이즈별 가격, 재고 등)를 조회합니다.
        Endpoint: /querySaleNowInfo
        """
        url = "https://seller.poizon.com/api/v1/h5/gw/adapter/pc/bidding/query/querySaleNowInfo"

        payload = {
            "source": "PC",
            "spuId": spu_id
        }

        return self._send_request(url, payload)

    def extract_price_info(self, api_response: dict[str, Any]) -> dict[str, Any]:
        """
        API 응답(query_sale_now_info)에서 사이즈별 가격 정보를 추출하고 요약합니다.
        한국 노출가(SALE_LOCAL_POIZON_LEAK)와 중국 노출가(CN_LEAK) 중 더 낮은 가격을 계산합니다.
        """
        data = api_response.get('data', {})
        if not data:
            return {}

        # 기본 상품 정보
        summary = {
            "productTitle": data.get("skuInfos", [{}])[0].get("productName", ""),
            "articleNumber": data.get("articleNumber", ""),
            "imageUrl": data.get("logoUrl", ""),
            "sizeList": []
        }

        # SKU(사이즈)별 순회
        sku_infos = data.get("skuInfos", [])
        for sku in sku_infos:
            # SPU(헤더 정보)는 건너뜀
            if sku.get("productType") == "SPU":
                continue

            # 사이즈 명 추출 (예: "블랙*#*XS" -> "XS")
            raw_desc = sku.get("propertyDesc", "")
            size_name = raw_desc.split("*#*")[-1] if "*#*" in raw_desc else raw_desc

            # 가격 정보 초기화
            kr_price = None  # 한국 노출가
            cn_price = None  # 중국 노출가

            # salesVolumeGroups 확인 (보통 buttonCode: 0 이 일반 판매)
            groups = sku.get("salesVolumeGroups", [])
            for group in groups:
                # groupId '30'(30일 기준) 또는 '7' 등 로직에 따라 선택.
                # 여기서는 buttonCode 0(일반 입찰)인 데이터만 확인
                if group.get("buttonCode") != 0:
                    continue

                infos = group.get("salesVolumeInfos", [])
                for info in infos:
                    area_id = info.get("areaId")
                    price_obj = info.get("price", {})

                    # 가격이 없는 경우(None) 건너뜀
                    if not price_obj:
                        continue

                    amount = int(price_obj.get("money", {}).get("amount", 0))
                    if amount == 0:
                        continue

                    # 한국 노출 가능 가격
                    if area_id == "SALE_LOCAL_POIZON_LEAK":
                        kr_price = amount
                    # 중국 노출 가능 가격
                    elif area_id == "CN_LEAK":
                        cn_price = amount

            # 둘 중 하나라도 가격이 있으면 노출
            if kr_price or cn_price:
                # 비교를 위해 없는 가격은 무한대 처리
                comp_kr = kr_price if kr_price else float('inf')
                comp_cn = cn_price if cn_price else float('inf')

                # 최적 노출가 (더 낮은 가격)
                target_price = min(comp_kr, comp_cn)

                summary["sizeList"].append({
                    "size": size_name,
                    "krPrice": kr_price if kr_price else 0,  # 0이면 가격 없음
                    "cnPrice": cn_price if cn_price else 0,  # 0이면 가격 없음
                    "targetPrice": target_price,  # 실제 입력해야 할 가격
                    "isCheaperIn": "CN" if comp_cn < comp_kr else "KR"  # 어디가 더 싼지
                })

        return summary

    def query_product_detail_analytics(self, spu_id: int) -> dict[str, Any]:
        """
        상품의 상세 분석 데이터(판매 추세, 주문 기록 등)를 조회합니다.
        Endpoint: /getMoreFloatingLayer
        """
        url = "https://seller.poizon.com/api/v1/h5/gw/intl-price-center/merchant/price/floatLayer/getMoreFloatingLayer"

        payload = {
            "spuId": spu_id,
            "source": 0,
            "timeRangeTypeCode": 0,
            "platformFlag": "PC"
        }

        return self._send_request(url, payload)

    def analyze_product_performance(self, analytics_response: dict[str, Any]) -> dict[str, Any]:
        """
        상세 분석 데이터를 기반으로 상품의 판매 성과를 분석합니다.
        - 거래 추세(Trend): 일별 거래량 및 가격 추이
        - 최근 주문(Record): 최근 체결된 주문의 시간, 가격, 사이즈
        """
        data = analytics_response.get('data', {})
        if not data:
            return {"status": "No Data"}

        result = {
            "status": "Success",
            "trend_summary": {},
            "recent_orders": [],
            "last_sold_time": None
        }

        # 1. 판매 추세 분석 (historyTradeTrend)
        trend_data = data.get('historyTradeTrend', {}).get('overseaBiddingTradeTrendDTO', {})
        dates = trend_data.get('horizontals', [])
        prices = trend_data.get('verticals', [])

        if dates:
            result['trend_summary'] = {
                "period": f"{dates[0]} ~ {dates[-1]}",
                "data_points": len(dates),  # 데이터가 존재하는 날짜 수 (거래 활발도 지표)
                "avg_price_trend": prices[-5:] if prices else [],  # 최근 5일간 가격 흐름
                "last_price": prices[-1] if prices else 0
            }

        # 2. 최근 주문 기록 분석 (historyTradeRecord)
        record_data = data.get('historyTradeRecord', {}).get('tradeRecordDTO', {})
        trade_records = record_data.get('tradeRecords', [])

        for trade in trade_records[:10]:  # 최근 10건만 추출
            price_info = trade.get('price', {})
            amount = price_info.get('amountText', 'N/A')

            result['recent_orders'].append({
                "time": trade.get('time'),  # 예: "3시간 전"
                "size": trade.get('size'),  # 예: "XL, Black"
                "price": amount,  # 예: "90,000"
                "region": trade.get('address')  # 예: "Asia"
            })

        # 가장 최근 판매 시간 추출
        if result['recent_orders']:
            result['last_sold_time'] = result['recent_orders'][0]['time']

        return result

    def _parse_minutes_ago(self, time_str: str) -> int:
        """
        [내부 헬퍼] '3시간 전', '1일 전' 텍스트를 '분(Minute)' 단위 정수로 변환합니다.
        """
        s = time_str.replace(" ", "").strip()

        # 1. 방금/분 전 처리
        if "방금" in s:
            return 0
        if "분전" in s:
            try:
                mins = int(re.search(r'(\d+)', s).group(1))
                return mins
            except:
                return 1

        # 2. 시간 전 처리
        if "시간전" in s:
            try:
                hours = int(re.search(r'(\d+)', s).group(1))
                return hours * 60
            except:
                return 60

        # 3. 일/주/달/년 처리
        days = 0
        try:
            num = int(re.search(r'(\d+)', s).group(1))
            if "일전" in s:
                days = num
            elif "주전" in s:
                days = num * 7
            elif "달전" in s:
                days = num * 30
            elif "년전" in s:
                days = num * 365
        except:
            pass

        # 기본적으로 1일 이상이면 분으로 환산 (최소 1440분)
        if days > 0:
            return days * 24 * 60

        # 파싱 실패 시 아주 오래된 것으로 간주 (최하점)
        return 999999

    def calculate_sales_velocity(self, analytics_response: dict[str, Any]) -> dict[str, Any]:
        """
        [정밀 분석] 판매 속도(Velocity)를 계산합니다.
        시간이 지날수록 점수가 급격히 떨어지는 '감쇠 모델'을 사용하여
        '지금 당장' 잘 팔리는 상품을 확실하게 구분합니다.
        """
        data = analytics_response.get('data', {})
        trade_records = data.get('historyTradeRecord', {}).get('tradeRecordDTO', {}).get('tradeRecords', [])

        total_velocity_score = 0.0
        details = []

        # 가중치 상수 (점수 스케일 조절용)
        BASE_POINT = 10000

        for trade in trade_records:
            time_str = trade.get('time', '')

            # 1. 판매된 지 몇 분 지났는지 계산
            elapsed_mins = self._parse_minutes_ago(time_str)

            # 2. 감쇠 공식 적용: 점수 = 10000 / (경과분 + 5)
            # 분모에 5를 더하는 이유는 0분일 때 무한대를 방지하고 곡선을 완만하게 하기 위함
            score = BASE_POINT / (elapsed_mins + 5)

            total_velocity_score += score

            details.append({
                "time_str": time_str,
                "elapsed_mins": elapsed_mins,
                "score": round(score, 2)
            })

        # 등급 산정 (20개 데이터 기준 시뮬레이션 결과)
        velocity_rank = "F (정체)"
        if total_velocity_score >= 5000:
            velocity_rank = "SSS (미친 속도 🔥)"  # 방금~1시간 이내 다수
        elif total_velocity_score >= 2000:
            velocity_rank = "S (폭발적)"  # 1~3시간 이내 다수
        elif total_velocity_score >= 500:
            velocity_rank = "A (매우 빠름)"  # 하루 이내 다수
        elif total_velocity_score >= 100:
            velocity_rank = "B (양호)"  # 2~3일 이내 다수
        elif total_velocity_score >= 20:
            velocity_rank = "C (보통)"

        return {
            "velocity_score": round(total_velocity_score, 2),
            "rank": velocity_rank,
            "details": details
        }

    def query_bidding_info(self, global_spu_id: int) -> dict[str, Any]:
        """
        입찰(Bidding)에 필요한 SKU ID와 사이즈 정보를 조회합니다.
        Endpoint: /batchQueryNewBidding
        """
        url = "https://seller.poizon.com/api/v1/h5/gw/adapter/pc/bidding/query/batchQueryNewBidding"

        payload = {
            "biddingType": -1,
            "globalSpuIds": [global_spu_id],  # 리스트 형태임에 주의
            "autoFillFulfillmentBiddingType": 1,
            "needShowSizeKey": True
        }

        return self._send_request(url, payload)

    def extract_sku_size_info(self, bidding_response: dict[str, Any]) -> list[dict[str, Any]]:
        """
        입찰 정보에서 SKU ID와 사이즈(KR, EU 등) 정보를 보기 좋게 추출합니다.
        [수정] 의류 사이즈(XS, M, L 등)의 'SIZE' 키도 인식하여 KR/EU 필드에 호환되도록 매핑합니다.
        """
        data = bidding_response.get('data', [])
        if not data:
            return []

        # data는 리스트 형태이며 보통 1개의 상품 정보가 들어옴
        product_data = data[0]
        sku_list = product_data.get('skuInventoryInfoList', [])

        extracted_skus = []

        for sku in sku_list:
            sku_id = sku.get('skuId')
            raw_prop = sku.get('spuPropNew', '')  # 예: "화이트-블루 KR 250" 또는 "투명 핑크 SIZE 2XS"

            # 1. 기본 사이즈 추출 (문자열의 마지막 단어를 사이즈로 간주)
            # 예: "SIZE 2XS" -> "2XS", "KR 250" -> "250"
            # 스펙 정보가 없을 때를 대비한 기본값
            fallback_size = raw_prop.split(' ')[-1] if ' ' in raw_prop else raw_prop

            sku_info = {
                "skuId": sku_id,
                "raw_prop": raw_prop,
                "size_kr": "N/A",
                "size_eu": "N/A",
                "size_us": "N/A"
            }

            # 2. 상세 스펙에서 정확한 키 기반으로 사이즈 추출
            specs = sku.get('skuPropAllSpecification', [])

            for spec in specs:
                key = spec.get('sizeKey')
                val_str = spec.get('skuProp', '')

                # 값에서 사이즈만 추출 (마지막 단어)
                size_val = val_str.split(' ')[-1] if ' ' in val_str else val_str

                if key == 'KR':
                    sku_info['size_kr'] = size_val
                elif key == 'EU':
                    sku_info['size_eu'] = size_val
                elif key == 'US Men':
                    sku_info['size_us'] = size_val
                # [추가된 부분] 의류나 기타 잡화의 일반 사이즈 키 처리
                elif key == 'SIZE' or key == 'Numeric Size':
                    # KR/EU 칸이 비어있다면 이 값을 채워넣어 식별 가능하게 함
                    if sku_info['size_kr'] == "N/A":
                        sku_info['size_kr'] = size_val
                    if sku_info['size_eu'] == "N/A":
                        sku_info['size_eu'] = size_val

            # 3. 여전히 N/A라면 raw_prop에서 추출한 기본값 사용 (안전장치)
            if sku_info['size_kr'] == "N/A":
                sku_info['size_kr'] = fallback_size
            if sku_info['size_eu'] == "N/A":
                sku_info['size_eu'] = fallback_size

            extracted_skus.append(sku_info)

        return extracted_skus

    def get_product_info(self, model_number: str) -> dict[str, Any] | None:
        """
        [통합 메소드] 모델명을 입력받아 상품의 종합 정보(기본정보, 판매점수, 가격, SKU)를 반환합니다.
        가격 매칭 시 KR/EU/US 등 다양한 사이즈 표기를 교차 검증합니다.
        """
        # 1. 상품 검색
        print(f"[Info] '{model_number}' 검색 시작...")
        search_res = self.search_product(model_number)
        if search_res.get('code') != 200:
            print(f"[Error] 검색 API 오류: {search_res.get('msg')}")
            return None

        # 2. 정확한 상품 매칭
        product_list = search_res.get('data', {}).get('merchantSpuDtoList', [])
        matched_product = self.find_matching_product(product_list, model_number)

        if not matched_product:
            print(f"[Info] '{model_number}'에 해당하는 정확한 상품을 찾을 수 없습니다.")
            return None

        global_spu_id = matched_product.get('globalSpuId')
        article_number = matched_product.get('articleNumber')
        title = matched_product.get('title')

        print(f"[Info] 상품 매칭 성공: {title} (GID: {global_spu_id})")

        # 3. 판매 속도(Velocity) 점수 분석
        analytics_res = self.query_product_detail_analytics(global_spu_id)
        velocity_data = self.calculate_sales_velocity(analytics_res)

        # 4. 현재 판매가 및 최적 노출가 분석
        sale_now_res = self.query_sale_now_info(global_spu_id)
        price_data = self.extract_price_info(sale_now_res)

        # 5. 입찰용 SKU 및 사이즈 정보 조회
        bidding_res = self.query_bidding_info(global_spu_id)
        sku_data = self.extract_sku_size_info(bidding_res)

        # 6. 데이터 병합 (개선된 매칭 로직)
        # price_data의 sizeList를 딕셔너리로 변환 (Key: 사이즈명 문자열)
        price_map = {str(item['size']).strip(): item for item in price_data.get('sizeList', [])}

        merged_sizes = []
        for sku in sku_data:
            matched_price = {}

            # [핵심 수정] 매칭 확률을 높이기 위해 여러 키(KR, EU, US, Raw)로 시도
            # Adidas 같은 경우 price_map 키가 '36'(EU)일 수 있고, sku['size_kr']은 '220'일 수 있음
            keys_to_try = [
                str(sku.get('size_kr', '')).strip(),  # 1순위: KR
                str(sku.get('size_eu', '')).strip(),  # 2순위: EU (여기서 주로 매칭됨)
                str(sku.get('size_us', '')).strip(),  # 3순위: US
                str(sku.get('raw_prop', '')).split(' ')[-1].strip()  # 4순위: 원본 문자열의 마지막 단어
            ]

            for key in keys_to_try:
                if key and key in price_map:
                    matched_price = price_map[key]
                    break

            merged_sizes.append({
                "size_kr": sku['size_kr'],
                "size_eu": sku['size_eu'],
                "size_us": sku['size_us'],
                "sku_id": sku['skuId'],
                # 매칭된 가격 정보가 있으면 사용, 없으면 0
                "target_price": matched_price.get('targetPrice', 0),
                "kr_leak_price": matched_price.get('krPrice', 0),
                "cn_leak_price": matched_price.get('cnPrice', 0),
                "is_cheaper_in": matched_price.get('isCheaperIn', 'N/A')
            })

        # 7. 최종 결과 구성
        final_result = {
            "model_info": {
                "article_number": article_number,
                "title": title,
                "global_spu_id": global_spu_id,
                "image_url": matched_product.get('logoUrl')
            },
            "sales_score": {
                "velocity_score": velocity_data.get('velocity_score', 0),
                "rank": velocity_data.get('rank', 'F'),
                "recent_sales_count": len(velocity_data.get('details', []))
            },
            "sizes": merged_sizes
        }

        return final_result


if __name__ == '__main__':
    dutoken = 'jFgarJUNT_N9WO0iYG90H7rbjdabJ19ivUZKllBq912xBxogFpDCyqjP6zkjQAbGbxnn90JqsHwkRgGIwcTjBp_NLtUWxZn3P3hib0W3Ay4fzq2Quw4jjcWEM1B5KjkHQAwl3pN4mJvlTHWCUyclzzAIMdkUHV9O17AQxfmZ+BWTsWNhrFmniJ6rsw4uGbYNBgsgeKnVh4xFSp4xkqI+aQcWQNr7CbfkxdkA10zVfFHc20aqXB8YQ+dmSwAOacvvtAMEf7xHc1z8eadvYgPkYqzeipDGcXHKHYCTYRIvVsW6gndMI5sIr5K53N4mCnqr8+EMe9uedMwCbOk8UTbvvS5dqeqIYkS6wpSmqURmGVeU9uU06G1W4sfbWbVFsZBGx2m7xOZjPG51gPM-'
    cookie = 'fe_sensors_ssid=32754331-51d1-49ab-931d-696fc45faaeb; _scid=OOd_8W0Y2ZnY0ZJQW_gILyv8O3ROGi_J; _fbp=fb.1.1768801174503.137637527949170360; _ga=GA1.1.1154156648.1768801175; _ScCbts=%5B%5D; _sctr=1%7C1768748400000; language=en; _gcl_au=1.1.760710505.1768801200; _tt_enable_cookie=1; _ttp=01KFAC8SRAEXS35PS6C7BFKK5R_.tt.1; sk=9TxXGIYI4UbnzgP0deih9puTDVEgtJT1SXlAjmaqvUrqzHILKEPzINFAOmlSaLttXw2csLZtRlySYmlJtUrw5GNB6T21; _ee_channel=; _ee_platform=pc; _ee_channel_data=; boundToken=; uid=1000534072; accessToken=2yftJGwXmvE46loAni3GQYGzdqvT3I58qcCHIY43gkjTz43DAf1pRBbAbBZj1Yvm; tfstk=gBAs3zVwKndF8F3tDluUAwX2NnCX12lrGr_vrEFak1C9cEKyYtIV_dkvcHse_G8N6iFXrUC2QdY4Spxyy5RZIsPfssfx40lraRYGis3di-jbS6QfzRh46SLdsZkZCNwtaFYgJqVdPSlrGIaiONIvDOBL9aIL6NFvDkQdxZbYXZFtReIhvZQAXSQLvNb7BPKAM2TdxZCADnBtReIhksIxOzZCuA_v54WSZopaZpTOASFv6AX5VmIh-ZOC5OsRpOPv5B_1CgL9wD95oZ9JNOx-YRS9FCt5zhlL13T9enpJvXP1GepJG6dKvyS9EeOf_C3q66LJdUW610NNmhtMsB67kcKXvUvl6Cn0_GvvJIIe6qPf2L8lOwAqx5IXpKdNIsqtfsLCkg5zagGJz-aCES_C42gQn-Au55Eqw27ymOQhWbuIRkwcBwbBK2gQn-XO-NCjR2ZQn; feLoginExpire=1769422329000; feLoginss=1000534072; ttcsid_D38MK7RC77U5QJRHURB0=1768817574260::N0CaK6K5INyafPlweXUd.3.1768817623225.1; ttcsid=1768817574260::2T4byYqkSKQgazlZPrYB.3.1768817623225.0; duToken=jFgarJUNT_N9WO0iYG90H7rbjdabJ19ivUZKllBq912xBxogFpDCyqjP6zkjQAbGbxnn90JqsHwkRgGIwcTjBp_NLtUWxZn3P3hib0W3Ay4fzq2Quw4jjcWEM1B5KjkHQAwl3pN4mJvlTHWCUyclzzAIMdkUHV9O17AQxfmZ+BWTsWNhrFmniJ6rsw4uGbYNBgsgeKnVh4xFSp4xkqI+aQcWQNr7CbfkxdkA10zVfFHc20aqXB8YQ+dmSwAOacvvtAMEf7xHc1z8eadvYgPkYqzeipDGcXHKHYCTYRIvVsW6gndMI5sIr5K53N4mCnqr8+EMe9uedMwCbOk8UTbvvS5dqeqIYkS6wpSmqURmGVeU9uU06G1W4sfbWbVFsZBGx2m7xOZjPG51gPM-; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219bd4c078b961-0eb9586c70a76f8-1b525631-3686400-19bd4c078bad15%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E4%BB%98%E8%B4%B9%E5%B9%BF%E5%91%8A%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24latest_utm_source%22%3A%22seo%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTliZDRjMDc4Yjk2MS0wZWI5NTg2YzcwYTc2ZjgtMWI1MjU2MzEtMzY4NjQwMC0xOWJkNGMwNzhiYWQxNSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219bd4c078b961-0eb9586c70a76f8-1b525631-3686400-19bd4c078bad15%22%7D; _scid_r=NWd_8W0Y2ZnY0ZJQW_gILyv8O3ROGi_JFuAVcQ; _ga_9YMHX0NL8P=GS2.1.s1768831135$o3$g1$t1768834331$j60$l0$h0; _ee_timestamp=1768834902911; forterToken=4b29072455274d96b14fc8ea06c64e3a_1768834260101__UDF43-mnf-a4_24ck_'
