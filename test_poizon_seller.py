import json
import unittest
from typing import Any

from poizon_seller import PoizonSeller

REAL_DUTOKEN = 'jFgarJUNT_N9WO0iYG90H7rbjdabJ19ivUZKllBq912xBxogFpDCyqjP6zkjQAbGbxnn90JqsHwkRgGIwcTjBp_NLtUWxZn3P3hib0W3Ay4fzq2Quw4jjcWEM1B5KjkHQAwl3pN4mJvlTHWCUyclzzAIMdkUHV9O17AQxfmZ+BWTsWNhrFmniJ6rsw4uGbYNBgsgeKnVh4xFSp4xkqI+aQcWQNr7CbfkxdkA10zVfFHc20aqXB8YQ+dmSwAOacvvtAMEf7xHc1z8eadvYgPkYqzeipDGcXHKHYCTYRIvVsW6gndMI5sIr5K53N4mCnqr8+EMe9uedMwCbOk8UTbvvS5dqeqIYkS6wpSmqURmGVeU9uU06G1W4sfbWbVFsZBGx2m7xOZjPG51gPM-'
REAL_COOKIE = 'fe_sensors_ssid=32754331-51d1-49ab-931d-696fc45faaeb; _scid=OOd_8W0Y2ZnY0ZJQW_gILyv8O3ROGi_J; _fbp=fb.1.1768801174503.137637527949170360; _ga=GA1.1.1154156648.1768801175; _ScCbts=%5B%5D; _sctr=1%7C1768748400000; language=en; _gcl_au=1.1.760710505.1768801200; _tt_enable_cookie=1; _ttp=01KFAC8SRAEXS35PS6C7BFKK5R_.tt.1; sk=9TxXGIYI4UbnzgP0deih9puTDVEgtJT1SXlAjmaqvUrqzHILKEPzINFAOmlSaLttXw2csLZtRlySYmlJtUrw5GNB6T21; _ee_channel=; _ee_platform=pc; _ee_channel_data=; boundToken=; uid=1000534072; accessToken=2yftJGwXmvE46loAni3GQYGzdqvT3I58qcCHIY43gkjTz43DAf1pRBbAbBZj1Yvm; tfstk=gBAs3zVwKndF8F3tDluUAwX2NnCX12lrGr_vrEFak1C9cEKyYtIV_dkvcHse_G8N6iFXrUC2QdY4Spxyy5RZIsPfssfx40lraRYGis3di-jbS6QfzRh46SLdsZkZCNwtaFYgJqVdPSlrGIaiONIvDOBL9aIL6NFvDkQdxZbYXZFtReIhvZQAXSQLvNb7BPKAM2TdxZCADnBtReIhksIxOzZCuA_v54WSZopaZpTOASFv6AX5VmIh-ZOC5OsRpOPv5B_1CgL9wD95oZ9JNOx-YRS9FCt5zhlL13T9enpJvXP1GepJG6dKvyS9EeOf_C3q66LJdUW610NNmhtMsB67kcKXvUvl6Cn0_GvvJIIe6qPf2L8lOwAqx5IXpKdNIsqtfsLCkg5zagGJz-aCES_C42gQn-Au55Eqw27ymOQhWbuIRkwcBwbBK2gQn-XO-NCjR2ZQn; feLoginExpire=1769422329000; feLoginss=1000534072; ttcsid_D38MK7RC77U5QJRHURB0=1768817574260::N0CaK6K5INyafPlweXUd.3.1768817623225.1; ttcsid=1768817574260::2T4byYqkSKQgazlZPrYB.3.1768817623225.0; duToken=jFgarJUNT_N9WO0iYG90H7rbjdabJ19ivUZKllBq912xBxogFpDCyqjP6zkjQAbGbxnn90JqsHwkRgGIwcTjBp_NLtUWxZn3P3hib0W3Ay4fzq2Quw4jjcWEM1B5KjkHQAwl3pN4mJvlTHWCUyclzzAIMdkUHV9O17AQxfmZ+BWTsWNhrFmniJ6rsw4uGbYNBgsgeKnVh4xFSp4xkqI+aQcWQNr7CbfkxdkA10zVfFHc20aqXB8YQ+dmSwAOacvvtAMEf7xHc1z8eadvYgPkYqzeipDGcXHKHYCTYRIvVsW6gndMI5sIr5K53N4mCnqr8+EMe9uedMwCbOk8UTbvvS5dqeqIYkS6wpSmqURmGVeU9uU06G1W4sfbWbVFsZBGx2m7xOZjPG51gPM-; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219bd4c078b961-0eb9586c70a76f8-1b525631-3686400-19bd4c078bad15%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E4%BB%98%E8%B4%B9%E5%B9%BF%E5%91%8A%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24latest_utm_source%22%3A%22seo%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTliZDRjMDc4Yjk2MS0wZWI5NTg2YzcwYTc2ZjgtMWI1MjU2MzEtMzY4NjQwMC0xOWJkNGMwNzhiYWQxNSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219bd4c078b961-0eb9586c70a76f8-1b525631-3686400-19bd4c078bad15%22%7D; _scid_r=NWd_8W0Y2ZnY0ZJQW_gILyv8O3ROGi_JFuAVcQ; _ga_9YMHX0NL8P=GS2.1.s1768831135$o3$g1$t1768834331$j60$l0$h0; _ee_timestamp=1768834902911; forterToken=4b29072455274d96b14fc8ea06c64e3a_1768834260101__UDF43-mnf-a4_24ck_'


class TestPoizonMatching(unittest.TestCase):
    """
    [단위 테스트] 내부 매칭 로직(find_matching_product)을 검증합니다.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.seller = PoizonSeller(dutoken="DUMMY", cookie="DUMMY")

        cls.sample_products = [
            {"title": "나이키 백팩", "articleNumber": "BA5954-010"},
            {"title": "비비안 목걸이", "articleNumber": "63030006-W127"},
            {"title": "크록스 클로그", "articleNumber": "206302-001"},
            {"title": "카시오 시계", "articleNumber": "BA-110RG-7A"},
            {"title": "폴라 클렌저", "articleNumber": "Pola Cleansers New Arrival"},
            {"title": "유사 나이키", "articleNumber": "BA5954-011"}
        ]

    def test_exact_match(self) -> None:
        keyword = "BA5954-010"
        result = self.seller.find_matching_product(self.sample_products, keyword)
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(result['articleNumber'], "BA5954-010")

    def test_normalization_match(self) -> None:
        keyword = "ba5954010"
        result = self.seller.find_matching_product(self.sample_products, keyword)
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(result['articleNumber'], "BA5954-010")

    def test_fuzzy_similarity_match(self) -> None:
        keyword = "BA5954-01"
        result = self.seller.find_matching_product(self.sample_products, keyword)
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(result['articleNumber'], "BA5954-010")

    def test_short_keyword_safety(self) -> None:
        keyword = "5954"
        result = self.seller.find_matching_product(self.sample_products, keyword)
        self.assertIsNone(result)

    def test_no_match(self) -> None:
        keyword = "99999999"
        result = self.seller.find_matching_product(self.sample_products, keyword)
        self.assertIsNone(result)


class TestPoizonLiveApi(unittest.TestCase):
    """
    [통합 테스트] 실제 Poizon 서버 API 호출 테스트
    """

    def setUp(self) -> None:
        if not REAL_DUTOKEN or not REAL_COOKIE:
            self.skipTest("실제 토큰과 쿠키가 설정되지 않았습니다.")

        self.seller = PoizonSeller(dutoken=REAL_DUTOKEN, cookie=REAL_COOKIE)

    def test_search_api_response(self) -> None:
        """1. 검색 API 호출 확인"""
        keyword = "BA5954-010"
        response = self.seller.search_product(keyword)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get('code'), 200, f"API 요청 실패: {response.get('msg')}")

        data = response.get('data', {})
        self.assertIsNotNone(data)
        self.assertIn('merchantSpuDtoList', data)

    def test_search_and_find_integration(self) -> None:
        """2. 검색 후 매칭 확인"""
        keyword = "BA5954-010"

        api_res = self.seller.search_product(keyword)
        self.assertEqual(api_res.get('code'), 200)

        product_list = api_res.get('data', {}).get('merchantSpuDtoList', [])
        self.assertTrue(len(product_list) > 0)

        match = self.seller.find_matching_product(product_list, keyword)
        self.assertIsNotNone(match)
        if match:
            print(f"\n[매칭 확인] {keyword} -> {match.get('articleNumber')}")

    def test_fetch_price_by_size(self) -> None:
        """3. 사이즈별 가격 조회 확인 (구조 수정됨)"""
        keyword = "BA5954-010"

        # 1. 검색
        search_res = self.seller.search_product(keyword)
        self.assertEqual(search_res.get('code'), 200)

        product_list = search_res.get('data', {}).get('merchantSpuDtoList', [])
        target_product = self.seller.find_matching_product(product_list, keyword)
        self.assertIsNotNone(target_product)

        # globalSpuId 대신 API 응답에 있는 spuId나 globalSpuId 사용
        # 응답 예시에 globalSpuId가 있으므로 사용
        spu_id = target_product.get('globalSpuId')
        self.assertIsNotNone(spu_id)

        print(f"\n[상세 조회] 상품: {target_product['title']}, ID: {spu_id}")

        # 2. 상세 조회
        price_res = self.seller.query_sale_now_info(spu_id)
        self.assertEqual(price_res.get('code'), 200, f"조회 실패: {price_res.get('msg')}")

        data = price_res.get('data', {})

        sku_infos = data.get('skuInfos', [])
        self.assertTrue(len(sku_infos) > 0, "skuInfos 데이터가 없습니다.")

        print("-" * 50)
        print(f"{'옵션/사이즈':<20} | {'가격(KRW)':<15} | {'비고'}")
        print("-" * 50)

        for sku in sku_infos[:5]:
            # 옵션명 (예: 블랙, 270 등)
            size_name = sku.get('propertyDesc', 'Unknown')

            # 가격 정보 추출 (복잡한 구조 순회)
            price_text = "N/A"
            note = ""

            # salesVolumeGroups -> salesVolumeInfos 안에 가격이 있음
            groups = sku.get('salesVolumeGroups', [])
            if groups:
                # 첫 번째 그룹(보통 '지난 30일' 등)의 정보 사용
                infos = groups[0].get('salesVolumeInfos', [])
                for info in infos:
                    # 한국 최저가나 중국 최저가 중 하나를 가져옴
                    if 'price' in info:
                        price_obj = info['price']
                        price_text = price_obj.get('amountText', 'N/A')
                        # areaId로 구분 (예: CN_LEAK, SALE_LOCAL_POIZON_LOWEST)
                        note = info.get('areaId', '')
                        if price_text != 'N/A':
                            break

            print(f"{size_name:<20} | {price_text:<15} | {note}")
        print("-" * 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)
