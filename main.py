import csv
import time
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import config
from sellers.musinsa import MusinsaSeller, MusinsaRankingType
from sellers.poizon import PoizonSeller
from utils.comparator import ProductComparator
from utils.constants import BrandEnum


def get_kst_now():
    """현재 시간을 한국 시간(KST)으로 반환합니다."""
    # UTC 시간 가져오기
    utc_now = datetime.now(timezone.utc)
    # KST는 UTC+9
    kst_now = utc_now + timedelta(hours=9)
    return kst_now


def cleanup_old_files(directory: Path, keep_count: int = 5):
    """
    지정된 디렉토리에서 오래된 CSV 파일을 삭제하여 최신 파일만 남깁니다.
    """
    if not directory.exists():
        return

    # CSV 파일 목록 가져오기
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


def main():
    kst_now = get_kst_now()
    print(f"[{kst_now}] Starting data collection (KST)...")

    # 1. 초기화
    musinsa_seller = MusinsaSeller()
    
    dutoken = config.POIZON_DUTOKEN
    cookie = config.POIZON_COOKIE
    
    if not dutoken or not cookie:
        print("[Error] Poizon credentials not found. Please check .env or config.py")
        return

    poizon_seller = PoizonSeller(dutoken=dutoken, cookie=cookie)
    comparator = ProductComparator(musinsa_seller, poizon_seller)

    # 결과 저장 경로 설정 (data/ranking/날짜_시간.csv)
    output_dir = Path("data/ranking")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 파일명에 한국 시간 적용 (YYYY-MM-DD_HH-MM-SS.csv)
    timestamp = kst_now.strftime("%Y-%m-%d_%H-%M-%S")
    output_file = output_dir / f"{timestamp}.csv"

    # 2. 랭킹 수집 (중복 제거)
    target_brands = [b.value for b in BrandEnum]
    ranking_types = [
        MusinsaRankingType.NEW,
        MusinsaRankingType.RISING,
        MusinsaRankingType.ALL
    ]
    
    unique_products = {}  # product_id -> item
    
    print(f"Fetching rankings for {target_brands}...")
    for r_type in ranking_types:
        print(f"  - Fetching {r_type.name} ranking...")
        rankings = musinsa_seller.fetch_ranking(r_type, brand_names=target_brands)
        if rankings:
            for item in rankings:
                if item.product_id not in unique_products:
                    unique_products[item.product_id] = item
        time.sleep(1)

    if not unique_products:
        print("No items found.")
        return

    print(f"Found {len(unique_products)} unique items. Starting comparison...")

    # 3. 비교 및 결과 수집
    results = []
    items_to_process = list(unique_products.values())
    
    for i, item in enumerate(items_to_process):
        print(f"[{i+1}/{len(items_to_process)}] {item.brand_name} - {item.product_name}")
        
        try:
            # 상세 정보 조회 (모델 번호 획득)
            product_info = musinsa_seller.get_product_info(item.product_id)
            if not product_info or not product_info.model_no:
                print("  -> Skip: No model number")
                continue
            
            model_no = product_info.model_no
            
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
                    "Brand": item.brand_name,
                    "Product Name": item.product_name,
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

    # 4. CSV 저장
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
        
        # 5. 오래된 파일 정리
        cleanup_old_files(output_dir, keep_count=5)

    else:
        print("No results to save.")

if __name__ == "__main__":
    main()
