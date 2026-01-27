import shutil
from pathlib import Path

def move_csv_files():
    data_dir = Path("data")
    ranking_dir = data_dir / "ranking"
    ranking_dir.mkdir(parents=True, exist_ok=True)
    
    # data 폴더 바로 아래에 있는 csv 파일만 이동
    for file in data_dir.glob("*.csv"):
        if file.is_file():
            target = ranking_dir / file.name
            shutil.move(str(file), str(target))
            print(f"Moved: {file.name} -> ranking/")

if __name__ == "__main__":
    move_csv_files()
