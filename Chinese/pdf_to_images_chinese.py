# pdf_to_images_chinese.py
from pathlib import Path
from pdf2image import convert_from_path
from tqdm import tqdm

PDF_DIR = Path("pdf")
OUT_DIR = Path("images")

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"在 {PDF_DIR} 目录下没有找到 PDF 文件。")
        return

    for pdf_path in tqdm(pdf_files, desc="Converting PDFs"):
        pages = convert_from_path(pdf_path)
        if not pages:
            continue
        for i, page in enumerate(pages, start=1):
            out_name = f"{pdf_path.stem}_p{i:03d}.png"
            out_path = OUT_DIR / out_name
            page.save(out_path, "PNG")

if __name__ == "__main__":
    main()