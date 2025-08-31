# AutoWatermark


AutoWatermark/
├── README.md              # 專案說明
├── requirements.txt       # 套件需求 (Pillow)
├── main.py                # 專案入口
├── watermark/             # 程式碼主體 (package)
│   ├── __init__.py
│   ├── cli.py             # 參數解析、主程式入口 (argparse)
│   ├── dfs_scanner.py     # DFS 掃描資料夾
│   ├── processor.py       # 處理單張圖片 (套用浮水印)
│   ├── utils.py           # 共用小工具 (例如判斷副檔名、建立資料夾)
├── examples/              # 範例資源
│   ├── input/             # 測試輸入資料夾 (放幾張圖)
│   ├── output/            # 預期輸出結果 (程式會產生)
│   └── watermark.png      # 範例浮水印圖
└── tests/                 # 測試用 (之後可加 pytest)
    └── test_basic.py


