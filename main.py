import csv
import time
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import config
from sellers.musinsa import MusinsaSeller, MusinsaRankingType
from sellers.poizon import PoizonSeller
from utils.comparator import ProductComparator
from utils.constants import BrandEnum, TARGET_BRANDS as DEFAULT_TARGET_BRANDS


def get_kst_now():
    """현재 시간을 한국 시간(KST)으로 반환합니다."""
    utc_now = datetime.now(timezone.utc)
    kst_now = utc_now + timedelta(hours=9)
    return kst_now


def cleanup_old_files(directory: Path, keep_count: int = 5):
    """
    지정된 디렉토리에서 오래된 CSV 파일을 삭제하여 최신 파일만 남깁니다.
    """
    if not directory.exists():
        return

    files = sorted(directory.glob("*.csv"), key=os.path.getmtime)
    
    if len(files) > keep_count:
        files_to_delete = files[:-keep_count]
        print(f"\n[Cleanup] Found {len(files)} files in {directory}. Deleting {len(files_to_delete)} old files...")
        
        for file in files_to_delete:
            try:
                file.unlink()
                print(f"  - Deleted: {file.name}")
            except Exception as e:
                print(f"  - Failed to delete {file.name}: {e}")
    else:
        print(f"\n[Cleanup] File count ({len(files)}) in {directory} is within limit ({keep_count}). No deletion needed.")


def run_ranking_collection(musinsa_seller, comparator, output_dir, kst_now):
    """랭킹 데이터 수집 및 비교"""
    print(f"Fetching rankings for {DEFAULT_TARGET_BRANDS}...")
    
    ranking_types = [
        MusinsaRankingType.NEW,
        MusinsaRankingType.RISING,
        MusinsaRankingType.ALL
    ]
    
    unique_products = {}
    
    for r_type in ranking_types:
        print(f"  - Fetching {r_type.name} ranking...")
        rankings = musinsa_seller.fetch_ranking(r_type, brand_names=DEFAULT_TARGET_BRANDS)
        if rankings:
            for item in rankings:
                if item.product_id not in unique_products:
                    unique_products[item.product_id] = item
        time.sleep(1)

    if not unique_products:
        print("No items found.")
        return

    print(f"Found {len(unique_products)} unique items. Starting comparison...")
    
    # 결과 저장 경로
    timestamp = kst_now.strftime("%Y-%m-%d_%H-%M-%S")
    output_file = output_dir / f"{timestamp}.csv"
    
    process_and_save(list(unique_products.values()), musinsa_seller, comparator, output_file, kst_now)
    cleanup_old_files(output_dir, keep_count=5)


def run_brand_search_collection(musinsa_seller, comparator, output_dir, kst_now):
    """브랜드 검색 데이터 수집 및 비교"""
    # 환경 변수에서 옵션 가져오기
    brands_str = os.environ.get("TARGET_BRANDS", "")
    pages_str = os.environ.get("TARGET_PAGES", "1")
    
    if not brands_str:
        print("[Error] No brands specified for brand_search mode.")
        return

    target_brands = [b.strip() for b in brands_str.split(",") if b.strip()]
    
    # 페이지 파싱 (예: "1", "1-3", "1,2,3")
    target_pages = []
    if "-" in pages_str:
        start, end = map(int, pages_str.split("-"))
        target_pages = list(range(start, end + 1))
    else:
        target_pages = [int(p) for p in pages_str.split(",") if p.strip().isdigit()]

    print(f"Starting brand search for {target_brands} on pages {target_pages}...")
    
    for brand_name in target_brands:
        # BrandEnum에서 해당 브랜드 찾기
        try:
            brand_enum = next(b for b in BrandEnum if b.value == brand_name)
        except StopIteration:
            print(f"  [Warning] Unknown brand: {brand_name}. Skipping.")
            continue
            
        all_products = []
        for page in target_pages:
            print(f"  - Searching {brand_name} (Page {page})...")
            products = musinsa_seller.search_by_brand(brand_enum, page=page)
            all_products.extend(products)
            time.sleep(1)
            
        if not all_products:
            print(f"  -> No products found for {brand_name}.")
            continue
            
        print(f"  -> Found {len(all_products)} products for {brand_name}. Starting comparison...")
        
        # 브랜드별로 파일 저장
        timestamp = kst_now.strftime("%Y-%m-%d_%H-%M-%S")
        output_file = output_dir / f"{timestamp}_{brand_enum.name}.csv"
        
        # ProductInfo 리스트를 바로 처리 (랭킹 아이템과 구조가 다름에 주의)
        # process_and_save는 RankingItem 리스트를 받도록 되어 있으므로, 
        # ProductInfo 리스트를 처리하는 별도 로직이나 어댑터 필요.
        # 여기서는 process_and_save를 수정하여 두 타입을 모두 지원하도록 함.
        process_and_save(all_products, musinsa_seller, comparator, output_file, kst_now)
        cleanup_old_files(output_dir, keep_count=5)


def process_and_save(items, musinsa_seller, comparator, output_file, kst_now):
    """상품 리스트를 비교하고 CSV로 저장"""
    results = []
    
    for i, item in enumerate(items):
        # item이 RankingItem인지 ProductInfo인지 확인
        if hasattr(item, 'product_id'): # RankingItem
            brand_name = item.brand_name
            product_name = item.product_name
            product_id = item.product_id
            model_no = None # 상세 조회 필요
        else: # ProductInfo
            brand_name = item.platform # 또는 별도 브랜드 필드 (현재 ProductInfo엔 브랜드 필드가 명확치 않음)
            # ProductInfo에는 brand_name 필드가 없으므로, title이나 다른 곳에서 유추하거나
            # search_by_brand 호출 시 브랜드를 알고 있으므로 그걸 써야 함.
            # 하지만 여기서는 item 객체만 넘어오므로... 
            # ProductInfo에 brand 필드를 추가하는게 좋겠지만, 일단 title 사용
            product_name = item.title
            product_id = "" # ProductInfo에는 ID가 없을 수도 있음 (검색 결과인 경우)
            model_no = item.model_no
            
            # ProductInfo인 경우 이미 상세 정보가 있으므로 get_product_info 호출 불필요할 수 있음
            # 하지만 model_no가 확실하다면 바로 비교
        
        print(f"[{i+1}/{len(items)}] {product_name}")
        
        try:
            # 모델 번호가 없으면 상세 조회 (RankingItem인 경우)
            if not model_no:
                product_info = musinsa_seller.get_product_info(product_id)
                if not product_info or not product_info.model_no:
                    print("  -> Skip: No model number")
                    continue
                model_no = product_info.model_no
                # ProductInfo인 경우 brand_name 보정
                if not brand_name or brand_name == "Musinsa":
                     # 상세 정보에서 브랜드를 가져올 수 있다면 좋음 (현재는 없음)
                     pass

            # 비교 수행
            comparison_result = comparator.compare_product(model_no)
            if not comparison_result:
                print("  -> Skip: Comparison failed")
                continue
            
            # 결과 데이터 구성
            has_profit = False
            for comp in comparison_result.comparisons:
                if comp.is_profitable:
                    has_profit = True
                    
            for comp in comparison_result.comparisons:
                results.append({
                    "Brand": brand_name, # 정확한 브랜드명을 위해선 ProductInfo 개선 필요
                    "Product Name": product_name,
                    "Model No": model_no,
                    "Size": comp.size,
                    "EU Size": comp.eu_size or "-",
                    "Color": comp.color,
                    "Musinsa Price": comp.musinsa_price,
                    "Musinsa Stock": comp.musinsa_stock_status,
                    "Poizon Price": comp.poizon_price,
                    "Poizon Stock": comp.poizon_stock_status,
                    "Profit": comp.price_diff,
                    "Margin (%)": comp.profit_margin,
                    "Status": "PROFIT" if comp.is_profitable else ("LOSS" if comp.musinsa_stock_status == "IN_STOCK" and comp.poizon_price > 0 else "N/A"),
                    "Poizon Score": comparison_result.poizon_sales_score,
                    "Poizon Rank": comparison_result.poizon_sales_rank,
                    "Image URL": comparison_result.image_url,
                    "Musinsa URL": comp.musinsa_url,
                    "Has Profit": has_profit,
                    "Updated At": kst_now.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            time.sleep(1.5)
            
        except Exception as e:
            print(f"  -> Error: {e}")
            continue

    # CSV 저장
    if results:
        fieldnames = [
            "Brand", "Product Name", "Model No", "Size", "EU Size", "Color", 
            "Musinsa Price", "Musinsa Stock", "Poizon Price", "Poizon Stock", 
            "Profit", "Margin (%)", "Status", "Poizon Score", "Poizon Rank",
            "Image URL", "Musinsa URL", "Has Profit", "Updated At"
        ]
        
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"Saved {len(results)} rows to {output_file}")
    else:
        print("No results to save.")


def main():
    kst_now = get_kst_now()
    print(f"[{kst_now}] Starting data collection (KST)...")

    # 초기화
    musinsa_seller = MusinsaSeller()
    
    dutoken = config.POIZON_DUTOKEN
    cookie = config.POIZON_COOKIE
    
    if not dutoken or not cookie:
        print("[Error] Poizon credentials not found. Please check .env or config.py")
        return

    poizon_seller = PoizonSeller(dutoken=dutoken, cookie=cookie)
    comparator = ProductComparator(musinsa_seller, poizon_seller)

    # 실행 모드 확인 (환경 변수)
    mode = os.environ.get("EXECUTION_MODE", "ranking")
    
    if mode == "brand_search":
        output_dir = Path("data/brand_search")
        output_dir.mkdir(parents=True, exist_ok=True)
        run_brand_search_collection(musinsa_seller, comparator, output_dir, kst_now)
    else:
        output_dir = Path("data/ranking")
        output_dir.mkdir(parents=True, exist_ok=True)
        run_ranking_collection(musinsa_seller, comparator, output_dir, kst_now)

if __name__ == "__main__":
    main()
