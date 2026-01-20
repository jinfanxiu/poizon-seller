import hashlib
import json
import re
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


if __name__ == '__main__':
    dutoken = 'jFgarJUNT_N9WO0iYG90H7rbjdabJ19ivUZKllBq912xBxogFpDCyqjP6zkjQAbGbxnn90JqsHwkRgGIwcTjBp_NLtUWxZn3P3hib0W3Ay4fzq2Quw4jjcWEM1B5KjkHQAwl3pN4mJvlTHWCUyclzzAIMdkUHV9O17AQxfmZ+BWTsWNhrFmniJ6rsw4uGbYNBgsgeKnVh4xFSp4xkqI+aQcWQNr7CbfkxdkA10zVfFHc20aqXB8YQ+dmSwAOacvvtAMEf7xHc1z8eadvYgPkYqzeipDGcXHKHYCTYRIvVsW6gndMI5sIr5K53N4mCnqr8+EMe9uedMwCbOk8UTbvvS5dqeqIYkS6wpSmqURmGVeU9uU06G1W4sfbWbVFsZBGx2m7xOZjPG51gPM-'
    cookie = 'fe_sensors_ssid=32754331-51d1-49ab-931d-696fc45faaeb; _scid=OOd_8W0Y2ZnY0ZJQW_gILyv8O3ROGi_J; _fbp=fb.1.1768801174503.137637527949170360; _ga=GA1.1.1154156648.1768801175; _ScCbts=%5B%5D; _sctr=1%7C1768748400000; language=en; _gcl_au=1.1.760710505.1768801200; _tt_enable_cookie=1; _ttp=01KFAC8SRAEXS35PS6C7BFKK5R_.tt.1; sk=9TxXGIYI4UbnzgP0deih9puTDVEgtJT1SXlAjmaqvUrqzHILKEPzINFAOmlSaLttXw2csLZtRlySYmlJtUrw5GNB6T21; _ee_channel=; _ee_platform=pc; _ee_channel_data=; boundToken=; uid=1000534072; accessToken=2yftJGwXmvE46loAni3GQYGzdqvT3I58qcCHIY43gkjTz43DAf1pRBbAbBZj1Yvm; tfstk=gBAs3zVwKndF8F3tDluUAwX2NnCX12lrGr_vrEFak1C9cEKyYtIV_dkvcHse_G8N6iFXrUC2QdY4Spxyy5RZIsPfssfx40lraRYGis3di-jbS6QfzRh46SLdsZkZCNwtaFYgJqVdPSlrGIaiONIvDOBL9aIL6NFvDkQdxZbYXZFtReIhvZQAXSQLvNb7BPKAM2TdxZCADnBtReIhksIxOzZCuA_v54WSZopaZpTOASFv6AX5VmIh-ZOC5OsRpOPv5B_1CgL9wD95oZ9JNOx-YRS9FCt5zhlL13T9enpJvXP1GepJG6dKvyS9EeOf_C3q66LJdUW610NNmhtMsB67kcKXvUvl6Cn0_GvvJIIe6qPf2L8lOwAqx5IXpKdNIsqtfsLCkg5zagGJz-aCES_C42gQn-Au55Eqw27ymOQhWbuIRkwcBwbBK2gQn-XO-NCjR2ZQn; feLoginExpire=1769422329000; feLoginss=1000534072; ttcsid_D38MK7RC77U5QJRHURB0=1768817574260::N0CaK6K5INyafPlweXUd.3.1768817623225.1; ttcsid=1768817574260::2T4byYqkSKQgazlZPrYB.3.1768817623225.0; duToken=jFgarJUNT_N9WO0iYG90H7rbjdabJ19ivUZKllBq912xBxogFpDCyqjP6zkjQAbGbxnn90JqsHwkRgGIwcTjBp_NLtUWxZn3P3hib0W3Ay4fzq2Quw4jjcWEM1B5KjkHQAwl3pN4mJvlTHWCUyclzzAIMdkUHV9O17AQxfmZ+BWTsWNhrFmniJ6rsw4uGbYNBgsgeKnVh4xFSp4xkqI+aQcWQNr7CbfkxdkA10zVfFHc20aqXB8YQ+dmSwAOacvvtAMEf7xHc1z8eadvYgPkYqzeipDGcXHKHYCTYRIvVsW6gndMI5sIr5K53N4mCnqr8+EMe9uedMwCbOk8UTbvvS5dqeqIYkS6wpSmqURmGVeU9uU06G1W4sfbWbVFsZBGx2m7xOZjPG51gPM-; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219bd4c078b961-0eb9586c70a76f8-1b525631-3686400-19bd4c078bad15%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E4%BB%98%E8%B4%B9%E5%B9%BF%E5%91%8A%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24latest_utm_source%22%3A%22seo%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTliZDRjMDc4Yjk2MS0wZWI5NTg2YzcwYTc2ZjgtMWI1MjU2MzEtMzY4NjQwMC0xOWJkNGMwNzhiYWQxNSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219bd4c078b961-0eb9586c70a76f8-1b525631-3686400-19bd4c078bad15%22%7D; _scid_r=NWd_8W0Y2ZnY0ZJQW_gILyv8O3ROGi_JFuAVcQ; _ga_9YMHX0NL8P=GS2.1.s1768831135$o3$g1$t1768834331$j60$l0$h0; _ee_timestamp=1768834902911; forterToken=4b29072455274d96b14fc8ea06c64e3a_1768834260101__UDF43-mnf-a4_24ck_'
