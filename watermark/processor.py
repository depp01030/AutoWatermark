from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont

def _load_font(font_path: str | None, size: int) -> ImageFont.ImageFont:
    if font_path:
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception as e:
            print(f"[WARN] Failed to load font '{font_path}', fallback to default: {e}")
    return ImageFont.load_default()

def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    # 用 textbbox 量測更準確
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return (r - l, b - t)

def process_image(src_path: Path, dst_path: Path, args):
    """
    將文字 args.text 重複鋪在圖片中央的單條水平帶上，整體置中、兩邊不裁切字樣。
    """
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # 參數（有就取 CLI/config，否則用預設）
    text: str = getattr(args, "text", None)
    if not text:
        raise SystemExit("[ERROR] No text provided. Use --text or config.json.")

    font_size: int = getattr(args, "font_size", 48)
    font_path: str | None = getattr(args, "font", None)
    opacity: float = getattr(args, "opacity", 0.25)
    gap: int = getattr(args, "gap", 24)
    margin: int = getattr(args, "margin", 16)
    use_stroke: bool = getattr(args, "stroke", False)
    stroke_width: int = getattr(args, "stroke_width", 2)
    overwrite: bool = getattr(args, "overwrite", False)

    if dst_path.exists() and not overwrite:
        print(f"[SKIP] Exists: {dst_path}")
        return

    # 開圖 + 依 EXIF 矯正方向
    with Image.open(src_path) as im:
        exif_bytes = im.info.get("exif")
        im = ImageOps.exif_transpose(im).convert("RGBA")
        W, H = im.size

        # 建立同尺寸透明層，先在上面畫字，最後再合成
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        font = _load_font(font_path, font_size)

        # 量測單個「完整字串」的寬高
        text_w, text_h = _measure_text(draw, text, font)
        if text_w <= 0 or text_h <= 0:
            print(f"[WARN] Text measurement invalid for '{text}'. Skip.")
            return

        # 可用寬度（左右保留 margin）
        usable_w = max(0, W - 2 * margin)

        # 計算最多可放多少「完整字串」
        # 放法：text 之間有固定 gap，總寬 = n*text_w + (n-1)*gap
        # 要求：總寬 <= usable_w，且 n >= 1 才畫
        n = 0
        if usable_w >= text_w:
            # 先至少能放 1 個
            n = 1 + max(0, (usable_w - text_w) // (text_w + gap))  # 粗估下界
            # 微調上/下界以確保不超過 usable_w
            while n * text_w + (n - 1) * gap > usable_w:
                n -= 1

        if n <= 0:
            # 空間太窄（字太大或 margin 太大）
            print(f"[WARN] Not enough width for one full token '{text}' on {src_path.name}. Skip.")
            return

        total_w = n * text_w + (n - 1) * gap
        start_x = (W - total_w) // 2               # 水平整體置中
        y = (H - text_h) // 2                      # 垂直置中（單行）

        # 準備顏色（白字 + 不透明度）
        alpha_255 = int(255 * max(0.0, min(1.0, opacity)))
        fill = (255, 255, 255, alpha_255)
        stroke_fill = (0, 0, 0, alpha_255) if use_stroke else None

        # 寫入 n 份 text：不裁切、不超出 usable_w，左右對稱
        x = start_x
        for i in range(n):
            if use_stroke and stroke_width > 0:
                draw.text((x, y), text, font=font, fill=fill,
                          stroke_width=stroke_width, stroke_fill=stroke_fill)
            else:
                draw.text((x, y), text, font=font, fill=fill)
            x += text_w + gap

        # 合成輸出
        composed = Image.alpha_composite(im, layer)

        # JPEG 轉回 RGB 存檔（保 EXIF 如可）
        save_kwargs = {}
        suffix = dst_path.suffix.lower()
        if suffix in (".jpg", ".jpeg"):
            composed = composed.convert("RGB")
            save_kwargs["quality"] = getattr(args, "quality", 90)
            if exif_bytes:
                save_kwargs["exif"] = exif_bytes

        composed.save(dst_path, **save_kwargs)
        print(f"[OK] {src_path} -> {dst_path} (n={n}, font_size={font_size}, gap={gap}, opacity={opacity})")
