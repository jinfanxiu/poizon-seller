import unittest
from sellers.poizon import PoizonSeller
from models.product import ProductInfo

REAL_DUTOKEN = 'jFgarJUNT_N9WO0iYG90H7rbjdabJ19ivUZKllBq912xBxogFpDCyqjP6zkjQAbGbxnn90JqsHwkRgGIwcTjBp_NLtUWxZn3P3hib0W3Ay4fzq2Quw4jjcWEM1B5KjkHQAwl3pN4mJvlTHWCUyclzzAIMdkUHV9O17AQxfmZ+BWTsWNhrFmniJ6rsw4uGbYNBgsgeKnVh4xFSp4xkqI+aQcWQNr7CbfkxdkA10zVfFHc20aqXB8YQ+dmSwAOacvvtAMEf7xHc1z8eadvYgPkYqzeipDGcXHKHYCTYRIvVsW6gndMI5sIr5K53N4mCnqr8+EMe9uedMwCbOk8UTbvvS5dqeqIYkS6wpSmqURmGVeU9uU06G1W4sfbWbVFsZBGx2m7xOZjPG51gPM-'
REAL_COOKIE = 'fe_sensors_ssid=32754331-51d1-49ab-931d-696fc45faaeb; _scid=OOd_8W0Y2ZnY0ZJQW_gILyv8O3ROGi_J; _fbp=fb.1.1768801174503.137637527949170360; _ga=GA1.1.1154156648.1768801175; _ScCbts=%5B%5D; _sctr=1%7C1768748400000; language=en; _gcl_au=1.1.760710505.1768801200; _tt_enable_cookie=1; _ttp=01KFAC8SRAEXS35PS6C7BFKK5R_.tt.1; sk=9TxXGIYI4UbnzgP0deih9puTDVEgtJT1SXlAjmaqvUrqzHILKEPzINFAOmlSaLttXw2csLZtRlySYmlJtUrw5GNB6T21; _ee_channel=; _ee_platform=pc; _ee_channel_data=; boundToken=; uid=1000534072; accessToken=2yftJGwXmvE46loAni3GQYGzdqvT3I58qcCHIY43gkjTz43DAf1pRBbAbBZj1Yvm; tfstk=gBAs3zVwKndF8F3tDluUAwX2NnCX12lrGr_vrEFak1C9cEKyYtIV_dkvcHse_G8N6iFXrUC2QdY4Spxyy5RZIsPfssfx40lraRYGis3di-jbS6QfzRh46SLdsZkZCNwtaFYgJqVdPSlrGIaiONIvDOBL9aIL6NFvDkQdxZbYXZFtReIhvZQAXSQLvNb7BPKAM2TdxZCADnBtReIhksIxOzZCuA_v54WSZopaZpTOASFv6AX5VmIh-ZOC5OsRpOPv5B_1CgL9wD95oZ9JNOx-YRS9FCt5zhlL13T9enpJvXP1GepJG6dKvyS9EeOf_C3q66LJdUW610NNmhtMsB67kcKXvUvl6Cn0_GvvJIIe6qPf2L8lOwAqx5IXpKdNIsqtfsLCkg5zagGJz-aCES_C42gQn-Au55Eqw27ymOQhWbuIRkwcBwbBK2gQn-XO-NCjR2ZQn; feLoginExpire=1769422329000; feLoginss=1000534072; ttcsid_D38MK7RC77U5QJRHURB0=1768817574260::N0CaK6K5INyafPlweXUd.3.1768817623225.1; ttcsid=1768817574260::2T4byYqkSKQgazlZPrYB.3.1768817623225.0; duToken=jFgarJUNT_N9WO0iYG90H7rbjdabJ19ivUZKllBq912xBxogFpDCyqjP6zkjQAbGbxnn90JqsHwkRgGIwcTjBp_NLtUWxZn3P3hib0W3Ay4fzq2Quw4jjcWEM1B5KjkHQAwl3pN4mJvlTHWCUyclzzAIMdkUHV9O17AQxfmZ+BWTsWNhrFmniJ6rsw4uGbYNBgsgeKnVh4xFSp4xkqI+aQcWQNr7CbfkxdkA10zVfFHc20aqXB8YQ+dmSwAOacvvtAMEf7xHc1z8eadvYgPkYqzeipDGcXHKHYCTYRIvVsW6gndMI5sIr5K53N4mCnqr8+EMe9uedMwCbOk8UTbvvS5dqeqIYkS6wpSmqURmGVeU9uU06G1W4sfbWbVFsZBGx2m7xOZjPG51gPM-; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219bd4c078b961-0eb9586c70a76f8-1b525631-3686400-19bd4c078bad15%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E4%BB%98%E8%B4%B9%E5%B9%BF%E5%91%8A%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24latest_utm_source%22%3A%22seo%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTliZDRjMDc4Yjk2MS0wZWI5NTg2YzcwYTc2ZjgtMWI1MjU2MzEtMzY4NjQwMC0xOWJkNGMwNzhiYWQxNSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219bd4c078b961-0eb9586c70a76f8-1b525631-3686400-19bd4c078bad15%22%7D; _scid_r=NWd_8W0Y2ZnY0ZJQW_gILyv8O3ROGi_JFuAVcQ; _ga_9YMHX0NL8P=GS2.1.s1768831135$o3$g1$t1768834331$j60$l0$h0; _ee_timestamp=1768834902911; forterToken=4b29072455274d96b14fc8ea06c64e3a_1768834260101__UDF43-mnf-a4_24ck_'


class TestPoizonLiveApi(unittest.TestCase):
    def setUp(self) -> None:
        if not REAL_DUTOKEN or not REAL_COOKIE:
            self.skipTest("실제 토큰과 쿠키가 설정되지 않았습니다.")
        self.seller = PoizonSeller(dutoken=REAL_DUTOKEN, cookie=REAL_COOKIE)

    def test_get_product_info_integration(self) -> None:
        model_number = "SQ423SKTO2"
        print(f"\n[통합 조회 시작] 모델명: {model_number}")

        result: ProductInfo | None = self.seller.get_product_info(model_number)
        self.assertIsNotNone(result, "상품 정보를 찾을 수 없습니다.")

        print("\n" + "=" * 110)
        print(f"✅ 모델명: {result.model_no}")
        print(f"✅ 상품명: {result.title}")
        print(f"✅ 플랫폼: {result.platform}")

        if result.sales_metrics:
            print(f"📊 판매 점수: {result.sales_metrics.velocity_score:.2f}점 ({result.sales_metrics.rank})")

        print("=" * 110)
        print(f"{'SKU ID':<18} | {'색상':<10} | {'사이즈':<5} | {'가격(KRW)':<10} | {'KR노출가':<10} | {'CN노출가'}")
        print("-" * 110)

        for opt in result.options:
            print(f"{opt.sku_id:<18} | {opt.color:<10} | {opt.size:<5} | "
                  f"{opt.price:,}      | {opt.kr_leak_price or 0:,}      | {opt.cn_leak_price or 0:,}")

        print("-" * 110)
        self.assertTrue(len(result.options) > 0, "사이즈 정보가 없습니다.")


if __name__ == "__main__":
    unittest.main(verbosity=2)