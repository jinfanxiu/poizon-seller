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
        keyword = "IT2491"

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

    def test_extract_price_logic(self) -> None:
        """4. 가격 정보 파싱 및 최적 노출가 계산 테스트"""
        keyword = "JQ9519"

        # 1. 검색
        search_res = self.seller.search_product(keyword)
        self.assertEqual(search_res.get('code'), 200)

        product_list = search_res.get('data', {}).get('merchantSpuDtoList', [])
        target_product = self.seller.find_matching_product(product_list, keyword)
        self.assertIsNotNone(target_product, "상품을 찾을 수 없습니다.")

        spu_id = target_product.get('globalSpuId')

        # 2. API 호출
        print(f"\n[데이터 분석 중] {target_product['title']} (ID: {spu_id})")
        api_response = self.seller.query_sale_now_info(spu_id)
        self.assertEqual(api_response.get('code'), 200)

        # 3. 데이터 파싱 메소드 실행 (핵심)
        parsed_data = self.seller.extract_price_info(api_response)

        # 4. 결과 출력 (표 형태)
        print("\n" + "=" * 70)
        print(f"모델명 : {parsed_data['articleNumber']}")
        print(f"상품명 : {parsed_data['productTitle']}")
        print("=" * 70)
        print(f"{'사이즈':<10} | {'한국노출가':<12} | {'중국노출가':<12} | {'🔥최적노출가(Min)':<15}")
        print("-" * 70)

        for item in parsed_data['sizeList']:
            kr = f"{item['krPrice']:,}" if item['krPrice'] else "N/A"
            cn = f"{item['cnPrice']:,}" if item['cnPrice'] else "N/A"
            target = f"{item['targetPrice']:,}"

            # 중국이 더 싸면 중국 가격에 강조 표시 (*)
            mark = "(*)" if item['isCheaperIn'] == 'CN' else ""

            print(f"{item['size']:<10} | {kr:<12} | {cn:<12} | {target:<15} {mark}")
        print("=" * 70)

        # 검증: 데이터가 비어있지 않은지
        self.assertTrue(len(parsed_data['sizeList']) > 0, "사이즈 리스트가 추출되지 않았습니다.")
        self.assertIsNotNone(parsed_data['articleNumber'])

    def test_product_performance_analytics(self) -> None:
        """6. 상품 상세 성과 분석(판매 추세 및 최근 주문) 테스트"""
        keyword = "IT2491"  # 테스트용 모델명 (아디다스 트랙탑 등 데이터가 있는 모델 추천)

        # 1. 검색으로 spuId 확보
        search_res = self.seller.search_product(keyword)
        self.assertEqual(search_res.get('code'), 200)

        product = self.seller.find_matching_product(search_res.get('data', {}).get('merchantSpuDtoList', []), keyword)
        self.assertIsNotNone(product, "상품을 찾을 수 없습니다.")

        # 주의: 이 API는 globalSpuId가 아니라 그냥 spuId(또는 검색 결과의 showSpuId)를 사용할 수도 있음
        # 응답 예시의 spuId는 12000195041 형태이므로 globalSpuId일 가능성이 높음
        target_spu_id = product.get('globalSpuId')

        print(f"\n[성과 분석] {product['title']} (ID: {target_spu_id})")

        # 2. 상세 분석 API 호출
        analytics_res = self.seller.query_product_detail_analytics(target_spu_id)
        self.assertEqual(analytics_res.get('code'), 200, f"API 호출 실패: {analytics_res.get('msg')}")

        # 3. 데이터 분석 메소드 실행
        report = self.seller.analyze_product_performance(analytics_res)

        # 4. 결과 리포트 출력
        trend = report.get('trend_summary', {})
        print("-" * 50)
        print(f"[추세 요약] 기간: {trend.get('period', 'N/A')}")
        print(f"  - 데이터 활성일수: {trend.get('data_points', 0)}일")
        print(f"  - 최근 가격 흐름: {trend.get('avg_price_trend')}")

        print(f"\n[최근 주문] 마지막 판매: {report.get('last_sold_time', '기록 없음')}")
        for order in report.get('recent_orders', [])[:5]:
            print(f"  - {order['time']:<8} | {order['size']:<15} | {order['price']}원")
        print("-" * 50)

        # 검증
        self.assertIsNotNone(report)
        self.assertIn('status', report)

    def test_sales_velocity_precision(self) -> None:
        """8. [정밀] 판매 속도(Velocity) 점수 테스트"""
        keyword = "IT2491"

        # 1. SpuId 확보
        search_res = self.seller.search_product(keyword)
        product = self.seller.find_matching_product(search_res.get('data', {}).get('merchantSpuDtoList', []), keyword)
        self.assertIsNotNone(product)
        target_spu_id = product.get('globalSpuId')

        # 2. 데이터 요청
        analytics_res = self.seller.query_product_detail_analytics(target_spu_id)
        self.assertEqual(analytics_res.get('code'), 200)

        # 3. [핵심] 정밀 속도 분석 실행
        velocity_result = self.seller.calculate_sales_velocity(analytics_res)

        print("\n" + "=" * 70)
        print(f"[🚀 판매 속도 정밀 분석] - {keyword}")
        print(f"총 속도 점수: {velocity_result['velocity_score']:,.2f} 점")
        print(f"현재 등급: {velocity_result['rank']}")
        print("=" * 70)
        print(f"{'판매 시점':<15} | {'경과 시간(분)':<15} | {'획득 점수'}")
        print("-" * 70)

        for item in velocity_result['details'][:15]:  # 상위 15개 확인
            print(f"{item['time_str']:<15} | {str(item['elapsed_mins']) + '분':<15} | {item['score']:.2f}")
        print("-" * 70)

        # 검증: 점수가 실수형인지 확인
        self.assertIsInstance(velocity_result['velocity_score'], float)

    def test_fetch_sku_for_bidding(self) -> None:
        """9. [입찰 준비] SKU ID 및 사이즈(KR/EU) 정보 조회 테스트"""
        keyword = "374764-21"  # 예시 데이터의 모델명 (푸마 스케이트보드화)

        # 1. 검색하여 globalSpuId 획득
        search_res = self.seller.search_product(keyword)
        self.assertEqual(search_res.get('code'), 200)

        product = self.seller.find_matching_product(search_res.get('data', {}).get('merchantSpuDtoList', []), keyword)
        self.assertIsNotNone(product, "상품을 찾을 수 없습니다.")
        target_global_id = product.get('globalSpuId')

        print(f"\n[입찰 정보 조회] {product['title']} (GID: {target_global_id})")

        # 2. 입찰 정보 API 호출
        bidding_res = self.seller.query_bidding_info(target_global_id)
        self.assertEqual(bidding_res.get('code'), 200, f"API 호출 실패: {bidding_res.get('msg')}")

        # 3. 데이터 정제 메소드 실행
        sku_list = self.seller.extract_sku_size_info(bidding_res)

        # 4. 결과 출력
        print("-" * 60)
        print(f"{'SKU ID':<15} | {'KR 사이즈':<10} | {'EU 사이즈':<10} | {'US 사이즈'}")
        print("-" * 60)

        for sku in sku_list:
            print(f"{sku['skuId']:<15} | {sku['size_kr']:<10} | {sku['size_eu']:<10} | {sku['size_us']}")
        print("-" * 60)

        # 검증
        self.assertTrue(len(sku_list) > 0, "SKU 목록이 비어있습니다.")
        # 첫 번째 SKU에 KR 사이즈가 있는지 확인 (보통 있음)
        self.assertNotEqual(sku_list[0]['size_kr'], "N/A")

    def test_get_product_info_integration(self) -> None:
        """10. [통합] 모델명으로 상품 종합 정보 조회 테스트"""
        model_number = "KC3334"  # 테스트용 모델명

        print(f"\n[통합 조회 시작] 모델명: {model_number}")

        # 1. 통합 메소드 실행
        result = self.seller.get_product_info(model_number)

        # 2. 검증: 결과가 None이 아니어야 함
        self.assertIsNotNone(result, "상품 정보를 찾을 수 없습니다.")

        # 3. 필수 키 검증 (데이터 구조 확인)
        self.assertIn('model_info', result)
        self.assertIn('sales_score', result)
        self.assertIn('sizes', result)

        # 4. 세부 데이터 검증
        model_info = result['model_info']
        sales_score = result['sales_score']
        sizes = result['sizes']

        print("-" * 60)
        print(f"✅ 모델명: {model_info['article_number']}")
        print(f"✅ 상품명: {model_info['title']}")
        print(f"✅ GID   : {model_info['global_spu_id']}")
        print(f"📊 판매 속도 점수: {sales_score['velocity_score']:.2f} ({sales_score['rank']})")
        print("-" * 60)

        # 사이즈 정보 출력 (상위 5개)
        print(f"{'SKU ID':<12} | {'KR':<5} | {'EU':<5} | {'목표가':<10} | {'KR노출가':<10} | {'CN노출가'}")
        print("-" * 60)
        for sku in sizes[:5]:
            print(f"{sku['sku_id']:<12} | {sku['size_kr']:<5} | {sku['size_eu']:<5} | "
                  f"{sku['target_price']:,}      | {sku['kr_leak_price']:,}      | {sku['cn_leak_price']:,}")
        print("-" * 60)

        # 사이즈 데이터가 최소 1개 이상 있어야 함
        self.assertTrue(len(sizes) > 0, "사이즈 정보가 없습니다.")
        # 첫 번째 사이즈의 가격 정보가 0이 아닌지 확인 (보통 가격이 있음)
        # 단, 재고가 없으면 0일 수 있으므로 경고만 출력하거나 패스
        if sizes and sizes[0]['target_price'] == 0:
            print("[Warning] 첫 번째 사이즈의 목표 가격이 0입니다. (품절 가능성)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
