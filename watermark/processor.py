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

def _font_for_scale_simple(font_path, img_h, scale, min_px=10, max_px=512):
    size = max(min_px, min(max_px, int(round(img_h * scale)* 1.5)))
    return _load_font(font_path, size), size
def process_image(src_path: Path, dst_path: Path, args):
    """
    將文字 args.text 重複鋪在圖片中央的單條水平帶上，整體置中、兩邊不裁切字樣。
    """
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # 參數（有就取 CLI/config，否則用預設）
    text: str = getattr(args, "text", None)
    if not text:
        raise SystemExit("[ERROR] No text provided. Use --text or config.json.")


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

        ## handle font_size calculate ##
        font_size_default: int = getattr(args, "font_size", 48)
        font_path: str | None = getattr(args, "font", None)
        # 取參數
        font_scale: float | None = getattr(args, "font_scale", None)

        # ... 開圖、算出 W, H 之後：
        font_min   = getattr(args, "font_min_size", 10)
        font_max   = getattr(args, "font_max_size", 512)

        if font_scale is not None:
            font, font_size = _font_for_scale_simple(font_path, H, font_scale, font_min, font_max)
        else:
            # 用固定大小（保留你原本邏輯）
            font_size = font_size_default 

        font = _load_font(font_path, font_size)
        opacity: float = getattr(args, "opacity", 0.25)
        gap = int(font_size * 0.5)


        # 建立同尺寸透明層，先在上面畫字，最後再合成
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        font = _load_font(font_path, font_size)

        # 量測單個「完整字串」的寬高
        text_w, text_h = _measure_text(draw, text, font)
        if text_w <= 0 or text_h <= 0:
            print(f"[WARN] Text measurement invalid for '{text}'. Skip.")
            return

        # 設定置中座標
        cx = W // 2
        y = (H - text_h) // 2  # 垂直置中

        alpha_255 = int(255 * max(0.0, min(1.0, opacity)))
        fill = (255, 255, 255, alpha_255)
        stroke_fill = (0, 0, 0, alpha_255) if use_stroke else None

        # ==== 改造：滿版鋪字（允許切邊） ====
        # 從中心開始往左右鋪滿
        # 起始位置：讓第一個字串剛好在畫布中心置中
        start_x = cx - text_w // 2

        # 往左鋪
        x = start_x
        while x + text_w > 0:
            if use_stroke and stroke_width > 0:
                draw.text((x, y), text, font=font, fill=fill,
                          stroke_width=stroke_width, stroke_fill=stroke_fill)
            else:
                draw.text((x, y), text, font=font, fill=fill)
            x -= text_w + gap

        # 往右鋪
        x = start_x + text_w + gap
        while x < W:
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
        print(f"[OK] {src_path} -> {dst_path} (font_size={font_size}, gap={gap}, opacity={opacity})")
