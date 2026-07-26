import sys
from pathlib import Path

# package `app` nằm ở ui/backend — thêm vào path khi chạy pytest từ repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
