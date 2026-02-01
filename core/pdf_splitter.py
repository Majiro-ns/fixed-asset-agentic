"""
PDF Splitter - サムネイルグリッド生成モジュール

PDFの全ページをサムネイル画像に変換し、グリッド状に配置した1枚の画像を生成する。
Gemini Vision APIに送信可能なサイズ（最大4MB程度）に収める。
"""

import io
from pathlib import Path
from typing import Optional, Tuple, List

# サムネイル設定
THUMBNAIL_WIDTH = 200
THUMBNAIL_HEIGHT = 280
GRID_PADDING = 10
PAGE_NUMBER_FONT_SIZE = 16
MAX_PAGES = 20  # 20ページ以上の場合は最初の20ページのみ
MAX_IMAGE_SIZE_BYTES = 4 * 1024 * 1024  # 4MB


def _calculate_grid_dimensions(
    num_pages: int, max_cols: int = 5
) -> Tuple[int, int]:
    """
    グリッドの行数と列数を計算する。

    Args:
        num_pages: ページ数
        max_cols: 最大列数

    Returns:
        (rows, cols) のタプル
    """
    if num_pages <= 0:
        return (0, 0)

    # ページ数が最大列数以下なら1行
    if num_pages <= max_cols:
        return (1, num_pages)

    # 複数行の場合
    cols = min(num_pages, max_cols)
    rows = (num_pages + cols - 1) // cols  # 切り上げ
    return (rows, cols)


def _render_page_to_thumbnail(
    page, width: int = THUMBNAIL_WIDTH, height: int = THUMBNAIL_HEIGHT
) -> "Image.Image":
    """
    PyMuPDFのページオブジェクトをサムネイル画像に変換する。

    Args:
        page: fitz.Page オブジェクト
        width: サムネイル幅
        height: サムネイル高さ

    Returns:
        PIL Image オブジェクト
    """
    from PIL import Image

    # ページの実際のサイズを取得
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height

    # アスペクト比を維持しながらスケールを計算
    scale_x = width / page_width
    scale_y = height / page_height
    scale = min(scale_x, scale_y)

    # PyMuPDFでレンダリング
    import fitz
    matrix = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    # PIL Imageに変換
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # 指定サイズに中央配置（余白は白）
    thumbnail = Image.new("RGB", (width, height), (255, 255, 255))
    paste_x = (width - img.width) // 2
    paste_y = (height - img.height) // 2
    thumbnail.paste(img, (paste_x, paste_y))

    return thumbnail


def _draw_page_number(
    img: "Image.Image", page_number: int, font_size: int = PAGE_NUMBER_FONT_SIZE
) -> "Image.Image":
    """
    サムネイル画像にページ番号をオーバーレイ描画する。

    Args:
        img: PIL Image オブジェクト
        page_number: ページ番号（1始まり）
        font_size: フォントサイズ

    Returns:
        ページ番号が描画されたPIL Image
    """
    from PIL import Image, ImageDraw, ImageFont

    # 画像をコピー（元画像を変更しない）
    result = img.copy()
    draw = ImageDraw.Draw(result)

    # フォント取得（デフォルトフォント使用）
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        try:
            # Linux/Mac用フォント
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except (OSError, IOError):
            # フォントが見つからない場合はデフォルト
            font = ImageFont.load_default()

    text = str(page_number)

    # テキストサイズを取得
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 右下に配置（パディング5px）
    padding = 5
    x = img.width - text_width - padding - 5
    y = img.height - text_height - padding - 5

    # 背景矩形（半透明風に白背景＋黒枠）
    rect_padding = 3
    draw.rectangle(
        [x - rect_padding, y - rect_padding,
         x + text_width + rect_padding, y + text_height + rect_padding],
        fill=(255, 255, 255),
        outline=(100, 100, 100),
        width=1
    )

    # ページ番号描画
    draw.text((x, y), text, fill=(0, 0, 0), font=font)

    return result


def _create_grid_image(
    thumbnails: List["Image.Image"],
    rows: int,
    cols: int,
    padding: int = GRID_PADDING
) -> "Image.Image":
    """
    サムネイル画像をグリッド状に配置した1枚の画像を生成する。

    Args:
        thumbnails: サムネイル画像のリスト
        rows: 行数
        cols: 列数
        padding: 画像間のパディング

    Returns:
        グリッド画像（PIL Image）
    """
    from PIL import Image

    if not thumbnails:
        # 空の場合は小さな白画像を返す
        return Image.new("RGB", (100, 100), (255, 255, 255))

    # サムネイルサイズ（最初のサムネイルから取得）
    thumb_width, thumb_height = thumbnails[0].size

    # グリッド全体のサイズを計算
    grid_width = cols * thumb_width + (cols + 1) * padding
    grid_height = rows * thumb_height + (rows + 1) * padding

    # グリッド画像を作成（背景は薄いグレー）
    grid = Image.new("RGB", (grid_width, grid_height), (240, 240, 240))

    # サムネイルを配置
    for idx, thumb in enumerate(thumbnails):
        row = idx // cols
        col = idx % cols
        x = padding + col * (thumb_width + padding)
        y = padding + row * (thumb_height + padding)
        grid.paste(thumb, (x, y))

    return grid


def _compress_image_to_size(
    img: "Image.Image", max_size_bytes: int = MAX_IMAGE_SIZE_BYTES
) -> bytes:
    """
    画像を指定サイズ以下になるまで圧縮する。

    Args:
        img: PIL Image オブジェクト
        max_size_bytes: 最大バイト数

    Returns:
        PNG画像のバイト列
    """
    # まずPNGで試す
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    png_bytes = buffer.getvalue()

    if len(png_bytes) <= max_size_bytes:
        return png_bytes

    # PNGが大きすぎる場合、画像サイズを縮小
    current_img = img.copy()
    scale = 0.9  # 10%ずつ縮小

    for _ in range(10):  # 最大10回試行
        new_width = int(current_img.width * scale)
        new_height = int(current_img.height * scale)

        if new_width < 100 or new_height < 100:
            break

        current_img = img.resize((new_width, new_height), resample=3)  # LANCZOS

        buffer = io.BytesIO()
        current_img.save(buffer, format="PNG", optimize=True)
        png_bytes = buffer.getvalue()

        if len(png_bytes) <= max_size_bytes:
            return png_bytes

        scale *= 0.9

    # それでも大きい場合はJPEGで圧縮
    buffer = io.BytesIO()
    current_img.save(buffer, format="JPEG", quality=85, optimize=True)
    jpeg_bytes = buffer.getvalue()

    if len(jpeg_bytes) <= max_size_bytes:
        return jpeg_bytes

    # 最終手段：JPEG品質を下げる
    for quality in [70, 55, 40, 30]:
        buffer = io.BytesIO()
        current_img.save(buffer, format="JPEG", quality=quality, optimize=True)
        jpeg_bytes = buffer.getvalue()
        if len(jpeg_bytes) <= max_size_bytes:
            return jpeg_bytes

    # それでもダメなら現状で返す
    return jpeg_bytes


def generate_thumbnail_grid(pdf_path: str, max_cols: int = 5) -> bytes:
    """
    PDFの全ページをサムネイル化し、グリッド画像を生成する。

    Args:
        pdf_path: PDFファイルパス
        max_cols: グリッドの最大列数（デフォルト5）

    Returns:
        PNG画像のバイト列（Gemini Vision API送信可能サイズ）

    Raises:
        FileNotFoundError: PDFファイルが存在しない場合
        ImportError: 必要なライブラリがない場合
        ValueError: 有効なページがない場合
    """
    import fitz  # PyMuPDF
    from PIL import Image

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # PDFを開く
    doc = fitz.open(str(path))

    try:
        num_pages = doc.page_count
        if num_pages == 0:
            raise ValueError("PDF has no pages")

        # 最大ページ数を制限
        pages_to_process = min(num_pages, MAX_PAGES)

        # グリッドサイズを計算
        rows, cols = _calculate_grid_dimensions(pages_to_process, max_cols)

        # 各ページをサムネイル化
        thumbnails: List[Image.Image] = []

        for page_idx in range(pages_to_process):
            page = doc.load_page(page_idx)

            # サムネイル生成
            thumb = _render_page_to_thumbnail(page)

            # ページ番号オーバーレイ
            thumb = _draw_page_number(thumb, page_idx + 1)

            thumbnails.append(thumb)

            # メモリ解放のため明示的にページを閉じる
            # （PyMuPDFは自動管理するが念のため）

        # グリッド画像を生成
        grid_image = _create_grid_image(thumbnails, rows, cols)

        # 圧縮して返す
        return _compress_image_to_size(grid_image)

    finally:
        doc.close()


def generate_thumbnail_grid_with_metadata(
    pdf_path: str, max_cols: int = 5
) -> dict:
    """
    サムネイルグリッドと共にメタデータも返す拡張版。

    Args:
        pdf_path: PDFファイルパス
        max_cols: グリッドの最大列数

    Returns:
        {
            "image_bytes": bytes,  # PNG/JPEG画像バイト列
            "total_pages": int,    # PDFの総ページ数
            "rendered_pages": int, # 実際にレンダリングしたページ数
            "grid_rows": int,      # グリッドの行数
            "grid_cols": int,      # グリッドの列数
            "image_size_bytes": int,  # 画像サイズ（バイト）
            "truncated": bool,     # ページが省略されたか
        }
    """
    import fitz
    from PIL import Image

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(str(path))

    try:
        num_pages = doc.page_count
        if num_pages == 0:
            raise ValueError("PDF has no pages")

        pages_to_process = min(num_pages, MAX_PAGES)
        truncated = num_pages > MAX_PAGES

        rows, cols = _calculate_grid_dimensions(pages_to_process, max_cols)

        thumbnails: List[Image.Image] = []

        for page_idx in range(pages_to_process):
            page = doc.load_page(page_idx)
            thumb = _render_page_to_thumbnail(page)
            thumb = _draw_page_number(thumb, page_idx + 1)
            thumbnails.append(thumb)

        grid_image = _create_grid_image(thumbnails, rows, cols)
        image_bytes = _compress_image_to_size(grid_image)

        return {
            "image_bytes": image_bytes,
            "total_pages": num_pages,
            "rendered_pages": pages_to_process,
            "grid_rows": rows,
            "grid_cols": cols,
            "image_size_bytes": len(image_bytes),
            "truncated": truncated,
        }

    finally:
        doc.close()


# テスト用エントリポイント
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_splitter.py <pdf_path> [output_path]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "thumbnail_grid.png"

    try:
        result = generate_thumbnail_grid_with_metadata(pdf_path)

        with open(output_path, "wb") as f:
            f.write(result["image_bytes"])

        print(f"Generated: {output_path}")
        print(f"  Total pages: {result['total_pages']}")
        print(f"  Rendered pages: {result['rendered_pages']}")
        print(f"  Grid: {result['grid_rows']} x {result['grid_cols']}")
        print(f"  Image size: {result['image_size_bytes']:,} bytes")
        if result["truncated"]:
            print(f"  Warning: PDF truncated (>{MAX_PAGES} pages)")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
