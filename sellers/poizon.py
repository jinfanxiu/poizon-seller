import hashlib
import json
import re
import time
from typing import Any

import requests
from pydantic import BaseModel

import config
from sellers.base import BaseSeller
from models.product import ProductInfo, ProductOption, SalesMetrics
from utils.matching import find_best_match
from utils.normalizer import DataNormalizer

class SkuIds(BaseModel):
    skuId: str
    globalSkuId: str
    dwSkuId: str

class SkuSizeInfo(BaseModel):
    ids: SkuIds
    skuId: str | None
    spuId: int | None
    image_url: str
    raw_prop: str
    size_kr: str
    size_eu: str
    size_us: str
    color: str

class SizePriceInfo(BaseModel):
    skuId: str
    size: str
    color: str
    krPrice: int
    cnPrice: int
    targetPrice: int
    isCheaperIn: str

class PriceSummary(BaseModel):
    productTitle: str
    articleNumber: str
    imageUrl: str
    sizeList: list[SizePriceInfo]

class SalesVelocityDetail(BaseModel):
    time_str: str
    elapsed_mins: int
    score: float

class SalesVelocity(BaseModel):
    velocity_score: float
    rank: str
    details: list[SalesVelocityDetail]

class PoizonSeller(BaseSeller):
    SALT: str = "048a9c4943398714b356a696503d2d36"

    def __init__(
        self,
        dutoken: str | None = None,
        cookie: str | None = None,
        shumeiid: str | None = None,
        referer: str | None = None,
    ) -> None:
        super().__init__(name="POIZON")
        self.last_api_error: str | None = None
        # 인자로 전달받지 않으면 config에서 가져옴
        raw_dutoken = dutoken or config.POIZON_DUTOKEN
        raw_cookie = cookie or config.POIZON_COOKIE
        
        # 공백 및 줄바꿈 제거 (GitHub Secrets 오류 방지)
        self.dutoken: str = raw_dutoken.strip() if raw_dutoken else ""
        self.cookie: str = raw_cookie.strip() if raw_cookie else ""
        # 브라우저는 Cookie 외에 동일 값을 "sk" 헤더에도 보냄(직접 전달). 없으면 쿠키에서 추출
        m_sk = re.search(r"(?:^|;)\s*sk=([^;]+)", self.cookie)
        self._sk_from_cookie: str = m_sk.group(1).strip() if m_sk else ""
        if shumeiid is not None:
            self._shumeiid: str = shumeiid.strip()
        else:
            self._shumeiid = (config.POIZON_SHUMEIID or "").strip()
        _ref = (
            (referer or config.POIZON_REFERER or "https://seller.poizon.com/main/goods/search")
            or "https://seller.poizon.com/main/goods/search"
        ).strip()
        if not self.dutoken or not self.cookie:
            print("[Warning] Poizon dutoken or cookie is missing. API calls may fail.")
        if not self._shumeiid and shumeiid is None:
            print(
                "[Warning] POIZON_SHUMEIID is empty. If API returns 401 (passport), copy "
                "'shumeiid' from a working merchant/search request in DevTools → .env"
            )
        if not self._sk_from_cookie:
            print(
                "[Warning] Cookie has no 'sk=…'. Poizon may need sk as header; use full Cookie from browser."
            )

        self.base_headers: dict[str, str] = {
            'accept': 'application/json',
            'accept-language': 'ko-KR,ko;q=0.9,zh-CN;q=0.8,zh;q=0.7,en-US;q=0.6,en;q=0.5',
            'channel': 'pc',
            'clientid': 'global',
            'content-type': 'application/json;charset=UTF-8',
            'lang': 'ko',
            'language': 'ko',
            'origin': 'https://seller.poizon.com',
            'priority': 'u=1, i',
            'referer': _ref,
            'sec-ch-ua': (
                '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"'
            ),
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'syscode': 'DU_USER_GLOBAL',
            'timezone': 'GMT+09:00',
            'user-agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
            ),
        }

    def _get_headers(self) -> dict[str, str]:
        headers = self.base_headers.copy()
        headers['dutoken'] = self.dutoken
        headers['Cookie'] = self.cookie
        if self._sk_from_cookie:
            headers['sk'] = self._sk_from_cookie
        if self._shumeiid:
            headers['shumeiid'] = self._shumeiid
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
            response = requests.post(
                final_url, headers=self._get_headers(), data=payload_json, timeout=60
            )
            try:
                data = response.json()
            except ValueError:
                data = {}

            if not response.ok:
                msg = data.get("msg") if isinstance(data, dict) else None
                err_detail = f" {msg}" if msg else f" (body: {response.text[:300]!r})"
                self.last_api_error = (
                    f"poizon request failed: {response.status_code} {response.reason} "
                    f"for {url}{err_detail}"
                )
                print(
                    f"Error sending request: {response.status_code} {response.reason} for {url}{err_detail}"
                )
                # 비-2xx여도 code/msg가 있으면 하위에서 처리 (401 passport 만료 등)
                return data if isinstance(data, dict) else {}

            time.sleep(2)
            return data
        except requests.exceptions.RequestException as e:
            self.last_api_error = f"poizon request exception for {url}: {e}"
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
        """
        공통 유틸리티 함수를 사용하여 매칭되는 상품을 찾습니다.
        """
        return find_best_match(product_list, search_keyword, key_field="articleNumber")

    def query_sale_now_info(self, spu_id: int) -> dict[str, Any]:
        url = "https://seller.poizon.com/api/v1/h5/gw/adapter/pc/bidding/query/querySaleNowInfo"
        payload = {"source": "PC", "spuId": spu_id}
        return self._send_request(url, payload)

    def extract_price_info(self, api_response: dict[str, Any]) -> PriceSummary:
        data = api_response.get('data', {})
        if not data:
            return PriceSummary(productTitle="", articleNumber="", imageUrl="", sizeList=[])

        product_title = data.get("skuInfos", [{}])[0].get("productName", "")
        article_number = data.get("articleNumber", "")
        image_url = data.get("logoUrl", "")
        size_list: list[SizePriceInfo] = []

        sku_infos = data.get("skuInfos", [])
        for sku in sku_infos:
            if sku.get("productType") == "SPU":
                continue

            sku_id = str(sku.get("skuId", ""))
            raw_desc = sku.get("propertyDesc", "")
            if "*#*" in raw_desc:
                parts = raw_desc.split("*#*")
                color_name = parts[0]
                size_name = parts[1]
            else:
                color_name = ""
                size_name = raw_desc

            kr_price = 0
            cn_price = 0

            groups = sku.get("salesVolumeGroups", [])
            for group in groups:
                if group.get("buttonCode") != 0:
                    continue
                infos = group.get("salesVolumeInfos", [])
                for info in infos:
                    area_id = info.get("areaId")
                    price_obj = info.get("price", {})
                    if not price_obj:
                        continue
                    amount = int(price_obj.get("money", {}).get("amount", 0))
                    if amount == 0:
                        continue
                    if area_id == "SALE_LOCAL_POIZON_LEAK":
                        kr_price = amount
                    elif area_id == "CN_LEAK":
                        cn_price = amount

            if kr_price > 0 or cn_price > 0:
                comp_kr = kr_price if kr_price > 0 else float('inf')
                comp_cn = cn_price if cn_price > 0 else float('inf')
                target_price = int(min(comp_kr, comp_cn))
                is_cheaper_in = "CN" if comp_cn < comp_kr else "KR"

                size_list.append(SizePriceInfo(
                    skuId=sku_id,
                    size=size_name,
                    color=color_name,
                    krPrice=kr_price,
                    cnPrice=cn_price,
                    targetPrice=target_price,
                    isCheaperIn=is_cheaper_in
                ))

        return PriceSummary(
            productTitle=product_title,
            articleNumber=article_number,
            imageUrl=image_url,
            sizeList=size_list
        )

    def query_product_detail_analytics(self, spu_id: int) -> dict[str, Any]:
        url = "https://seller.poizon.com/api/v1/h5/gw/intl-price-center/merchant/price/floatLayer/getMoreFloatingLayer"
        payload = {
            "spuId": spu_id,
            "source": 0,
            "timeRangeTypeCode": 0,
            "platformFlag": "PC"
        }
        return self._send_request(url, payload)

    def _parse_minutes_ago(self, time_str: str) -> int:
        s = time_str.replace(" ", "").strip()
        if "방금" in s:
            return 0
        if "분전" in s:
            try:
                mins = int(re.search(r'(\d+)', s).group(1))
                return mins
            except:
                return 1
        if "시간전" in s:
            try:
                hours = int(re.search(r'(\d+)', s).group(1))
                return hours * 60
            except:
                return 60
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
        if days > 0:
            return days * 24 * 60
        return 999999

    def calculate_sales_velocity(self, analytics_response: dict[str, Any]) -> SalesVelocity:
        data = analytics_response.get('data', {})
        trade_records = data.get('historyTradeRecord', {}).get('tradeRecordDTO', {}).get('tradeRecords', [])

        total_velocity_score = 0.0
        details: list[SalesVelocityDetail] = []
        BASE_POINT = 10000

        for trade in trade_records:
            time_str = trade.get('time', '')
            elapsed_mins = self._parse_minutes_ago(time_str)
            score = BASE_POINT / (elapsed_mins + 5)
            total_velocity_score += score
            details.append(SalesVelocityDetail(
                time_str=time_str,
                elapsed_mins=elapsed_mins,
                score=round(score, 2)
            ))

        velocity_rank = "F (정체)"
        if total_velocity_score >= 5000:
            velocity_rank = "SSS (미친 속도 🔥)"
        elif total_velocity_score >= 2000:
            velocity_rank = "S (폭발적)"
        elif total_velocity_score >= 500:
            velocity_rank = "A (매우 빠름)"
        elif total_velocity_score >= 100:
            velocity_rank = "B (양호)"
        elif total_velocity_score >= 20:
            velocity_rank = "C (보통)"

        return SalesVelocity(
            velocity_score=round(total_velocity_score, 2),
            rank=velocity_rank,
            details=details
        )

    def query_bidding_info(self, global_spu_id: int) -> dict[str, Any]:
        url = "https://seller.poizon.com/api/v1/h5/gw/adapter/pc/bidding/query/batchQueryNewBidding"
        payload = {
            "biddingType": -1,
            "globalSpuIds": [global_spu_id],
            "autoFillFulfillmentBiddingType": 1,
            "needShowSizeKey": True
        }
        return self._send_request(url, payload)

    def extract_sku_size_info(self, bidding_response: dict[str, Any]) -> list[SkuSizeInfo]:
        data = bidding_response.get('data', [])
        if not data:
            return []

        product_data = data[0]
        sku_list = product_data.get('skuInventoryInfoList', [])
        extracted_skus: list[SkuSizeInfo] = []

        for sku in sku_list:
            sku_id = str(sku.get('skuId', ''))
            spu_id = sku.get('spuId')
            image_url = sku.get('skuPic') or sku.get('logoUrl') or ''
            raw_prop = sku.get('spuPropNew') or sku.get('spuProp') or ''
            fallback_size = raw_prop.split(' ')[-1] if ' ' in raw_prop else raw_prop

            sku_ids = SkuIds(
                skuId=sku_id,
                globalSkuId=str(sku.get('globalSkuId', '')),
                dwSkuId=str(sku.get('dwSkuId', ''))
            )

            sku_info_data = {
                "ids": sku_ids,
                "skuId": sku_id,
                "spuId": spu_id,
                "image_url": image_url,
                "raw_prop": raw_prop,
                "size_kr": "N/A",
                "size_eu": "N/A",
                "size_us": "N/A",
                "color": ""
            }

            specs = sku.get('skuPropAllSpecification', [])
            if specs:
                for spec in specs:
                    key = spec.get('sizeKey')
                    val_str = spec.get('skuProp', '')
                    # 숫자만 추출 (예: "화이트 CHN 220" -> "220")
                    size_val = val_str.split(' ')[-1] if ' ' in val_str else val_str
                    
                    if key == 'KR':
                        sku_info_data['size_kr'] = size_val
                    elif key == 'CHN': # CHN 사이즈를 KR 사이즈로 취급
                        # CHN 사이즈에서 숫자만 추출 (예: "220")
                        nums = re.findall(r"[\d\.]+", val_str)
                        if nums:
                            sku_info_data['size_kr'] = nums[-1] # 보통 마지막 숫자가 사이즈
                    elif key == 'EU':
                        sku_info_data['size_eu'] = size_val
                    elif key == 'US Men':
                        sku_info_data['size_us'] = size_val
                    elif key in ['SIZE', 'Numeric Size']:
                        if sku_info_data['size_kr'] == "N/A":
                            sku_info_data['size_kr'] = size_val
                        if sku_info_data['size_eu'] == "N/A":
                            sku_info_data['size_eu'] = size_val

            region_info = sku.get('regionSalePvInfoList', [])
            for info in region_info:
                name = info.get('name', '')
                value = info.get('value', '')
                if '색상' in name or 'Color' in name:
                    sku_info_data['color'] = value
                if sku_info_data['size_kr'] == "N/A":
                    if '사이즈' in name or 'Size' in name:
                        sku_info_data['size_kr'] = value
                        sku_info_data['size_eu'] = value

            if sku_info_data['size_kr'] == "N/A":
                sku_info_data['size_kr'] = fallback_size
            if sku_info_data['size_eu'] == "N/A":
                sku_info_data['size_eu'] = fallback_size

            extracted_skus.append(SkuSizeInfo(**sku_info_data))

        return extracted_skus

    def get_product_info(self, model_number: str) -> ProductInfo | None:
        print(f"[Info] '{model_number}' 검색 시작...")
        search_res = self.search_product(model_number)
        if search_res.get('code') != 200:
            self.last_api_error = f"poizon search api error: {search_res.get('msg') or search_res.get('code')}"
            print(f"[Error] 검색 API 오류: {search_res.get('msg')}")
            return None

        product_list = search_res.get('data', {}).get('merchantSpuDtoList', [])
        matched_product = self.find_matching_product(product_list, model_number)

        if not matched_product:
            print(f"[Info] '{model_number}'에 해당하는 정확한 상품을 찾을 수 없습니다.")
            return None

        global_spu_id = matched_product.get('globalSpuId')
        article_number = matched_product.get('articleNumber')
        title = matched_product.get('title')

        print(f"[Info] 상품 매칭 성공: {title} (GID: {global_spu_id})")

        analytics_res = self.query_product_detail_analytics(global_spu_id)
        velocity_data = self.calculate_sales_velocity(analytics_res)

        sale_now_res = self.query_sale_now_info(global_spu_id)
        price_data = self.extract_price_info(sale_now_res)

        bidding_res = self.query_bidding_info(global_spu_id)
        sku_data = self.extract_sku_size_info(bidding_res)

        price_by_id = {item.skuId: item for item in price_data.sizeList if item.skuId}
        price_list = price_data.sizeList

        standard_options: list[ProductOption] = []

        for sku in sku_data:
            matched_price: SizePriceInfo | None = None
            sku_ids = sku.ids

            for id_key in ['skuId', 'globalSkuId', 'dwSkuId']:
                check_id = getattr(sku_ids, id_key, None)
                if check_id and check_id in price_by_id:
                    matched_price = price_by_id[check_id]
                    break

            if not matched_price:
                s_color = str(sku.color).strip()
                sku_size_candidates = [
                    str(sku.size_kr).strip(),
                    str(sku.size_eu).strip(),
                    str(sku.size_us).strip(),
                    str(sku.raw_prop).split(' ')[-1].strip()
                ]
                sku_size_candidates = [s for s in sku_size_candidates if s and s != "N/A"]

                for p_item in price_list:
                    p_size_str = str(p_item.size).strip()
                    p_color_str = str(p_item.color).strip()
                    p_full_str = f"{p_color_str} {p_size_str}"

                    if s_color and s_color not in p_full_str:
                        continue

                    is_size_match = False
                    p_tokens = re.split(r'[^a-zA-Z0-9.]', p_full_str)
                    for s_cand in sku_size_candidates:
                        if s_cand in p_tokens:
                            is_size_match = True
                            break

                    if is_size_match:
                        matched_price = p_item
                        break

            target_price = 0
            kr_leak_price = 0
            cn_leak_price = 0
            is_cheaper_in = "N/A"

            if matched_price:
                target_price = matched_price.targetPrice
                kr_leak_price = matched_price.krPrice
                cn_leak_price = matched_price.cnPrice
                is_cheaper_in = matched_price.isCheaperIn

            # 사이즈 결정: KR 사이즈가 있으면 사용, 없으면 EU 사이즈 사용
            final_size = sku.size_kr if sku.size_kr != "N/A" else sku.size_eu
            
            # EU 사이즈 정보 저장
            eu_size = sku.size_eu if sku.size_eu != "N/A" else None

            standard_options.append(ProductOption(
                sku_id=sku.skuId or "N/A",
                size=final_size,
                eu_size=eu_size,  # EU 사이즈 추가
                color=sku.color,
                price=target_price,
                currency="KRW",
                stock_status="IN_STOCK" if target_price > 0 else "OUT_OF_STOCK",
                image_url=sku.image_url,
                kr_leak_price=kr_leak_price,
                cn_leak_price=cn_leak_price,
                is_cheaper_in=is_cheaper_in,
                extra_ids={
                    "skuId": sku.ids.skuId,
                    "globalSkuId": sku.ids.globalSkuId,
                    "dwSkuId": sku.ids.dwSkuId,
                    "spuId": str(sku.spuId) if sku.spuId else ""
                }
            ))

        return ProductInfo(
            platform=self.name,
            model_no=article_number,
            title=title,
            image_url=matched_product.get('logoUrl'),
            options=standard_options,
            sales_metrics=SalesMetrics(
                velocity_score=velocity_data.velocity_score,
                rank=velocity_data.rank,
                recent_sales_count=len(velocity_data.details),
                last_sold_time=velocity_data.details[0].time_str if velocity_data.details else None
            )
        )