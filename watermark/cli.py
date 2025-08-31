# watermark/cli.py
import argparse
import json
from pathlib import Path
from watermark.dfs_scanner import dfs_walk
from watermark.processor import process_image

def main():
    # 第一輪 parser 只抓 --config
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", help="Path to JSON config file")
    pre_args, remaining_argv = pre_parser.parse_known_args()


    defaults = {}

    # 如果有輸入 --config，就用使用者給的
    if pre_args.config:
        config_path = Path(pre_args.config)
    else:
        # 否則就預設找 main.py 同層的 config.json
        config_path = Path(__file__).resolve().parent.parent / "config.json"

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            defaults = json.load(f)
    else:
        print(f"[WARN] Config file not found: {config_path}, using only CLI arguments.")


    parser = argparse.ArgumentParser(
        description="Batch add watermark to images (DFS folder scan).",
        parents=[pre_parser]
    )
    parser.set_defaults(**defaults)

    parser.add_argument("--input", required="input" not in defaults, help="Input folder path")
    parser.add_argument("--output", required="output" not in defaults, help="Output folder path")
    parser.add_argument("--text", help="Text watermark")
    parser.add_argument("--wm-image", help="Image watermark path (png recommended)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output files if exist")
    parser.add_argument("--ext", default="jpg,jpeg,png", help="Comma separated extensions (default: jpg,jpeg,png)")




    args = parser.parse_args(remaining_argv)
    input_root = Path(args.input).resolve()
    output_root = Path(args.output).resolve()

    if not input_root.exists():
        raise SystemExit(f"[ERROR] Input folder not found: {input_root}")

    print(f"[INFO] Input 資料夾為 {input_root} ...")
    print(f"[INFO] Output 資料夾為 {output_root} ...")
    

    allowed_exts = {e.strip().lower() for e in args.ext.split(",")}
    for file_path in dfs_walk(input_root): 
        if file_path.suffix.lower().lstrip(".") not in allowed_exts:
            continue
        rel_path = file_path.relative_to(input_root)
        output_path = output_root / rel_path
        process_image(file_path, output_path, args)
