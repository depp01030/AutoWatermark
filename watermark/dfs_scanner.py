from pathlib import Path
from typing import Iterator, Iterable

def dfs_walk(root: Path) -> Iterator[Path]:
    """
    深度優先走訪 root 底下的所有「檔案」並依序 yield。
    - 以名稱排序確保結果可重現（deterministic）。
    - 不追蹤目錄型 symlink，避免循環。
    - 目錄權限不足或讀取競態將被安全略過。
    """
    root = Path(root)
    if not root.exists():
        print("Input 資料夾不存在")
        return

    stack: list[Path] = [root]
    seen_dirs: set[Path] = set()

    while stack:
        cur = stack.pop()

        try:
            if cur.is_dir():
                # 跳過指向目錄的 symlink
                if cur.is_symlink():
                    continue

                # 用實體路徑避免循環
                try:
                    real = cur.resolve()
                except Exception:
                    real = cur
                if real in seen_dirs:
                    continue
                seen_dirs.add(real)

                # 依名稱排序；為了 DFS 正確順序，推入 stack 時反向壓入
                try:
                    children = sorted(cur.iterdir(), key=lambda p: p.name)
                except PermissionError:
                    continue  # 沒權限就略過
                for child in reversed(children):
                    stack.append(child)
            else:
                yield cur
        except FileNotFoundError:
            # 檔案在掃描過程中被移除：略過
            continue
