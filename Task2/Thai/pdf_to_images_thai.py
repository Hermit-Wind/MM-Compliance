#!/usr/bin/env python3
"""
Convert Thai PDF files to images

This script converts all PDF files in the Thai dataset to PNG images.
Structure: Thai/Industry/Company/Company.pdf → images/Company_p001.png
"""

from pathlib import Path
from pdf2image import convert_from_path
from tqdm import tqdm


def pdf_to_images_thai(base_dir: Path, output_dir: Path):
    """
    Convert Thai PDF files to images
    
    Args:
        base_dir: Base directory containing industry folders
        output_dir: Output directory for images
    """
    base_dir = Path(base_dir)
    output_dir = Path(output_dir)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*80}")
    print(f"CONVERTING THAI PDF FILES TO IMAGES")
    print(f"{'='*80}")
    print(f"Input directory: {base_dir}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*80}\n")
    
    # Industry directories
    industries = ["Banking", "Commerce", "Energy"]
    
    # Collect all PDF files
    pdf_files = []
    for industry in industries:
        industry_dir = base_dir / industry
        
        if not industry_dir.exists():
            print(f"⚠️  Industry directory not found: {industry}")
            continue
        
        # Find all PDF files in company subdirectories
        for company_dir in industry_dir.iterdir():
            if not company_dir.is_dir():
                continue
            
            for pdf_file in company_dir.glob("*.pdf"):
                pdf_files.append(pdf_file)
    
    if not pdf_files:
        print(f"❌ No PDF files found in {base_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF files\n")
    
    # Convert each PDF
    total_pages = 0
    for pdf_path in tqdm(pdf_files, desc="Converting PDFs"):
        company_name = pdf_path.parent.name
        
        try:
            # Convert PDF to images
            pages = convert_from_path(pdf_path)
            
            if not pages:
                print(f"\n⚠️  No pages extracted from {pdf_path.name}")
                continue
            
            # Save each page
            for i, page in enumerate(pages, start=1):
                out_name = f"{company_name}_p{i:03d}.png"
                out_path = output_dir / out_name
                page.save(out_path, "PNG")
                total_pages += 1
        
        except Exception as e:
            print(f"\n❌ Error converting {pdf_path.name}: {e}")
            continue
    
    print(f"\n{'='*80}")
    print(f"✅ Conversion complete!")
    print(f"   Total PDFs: {len(pdf_files)}")
    print(f"   Total pages: {total_pages}")
    print(f"   Output directory: {output_dir}")
    print(f"{'='*80}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert Thai PDF files to images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert PDFs in current directory
  python pdf_to_images_thai.py
  
  # Specify custom directories
  python pdf_to_images_thai.py --base_dir Thai --output images
  
  # From Thai directory
  python pdf_to_images_thai.py --base_dir . --output images
        """
    )
    
    parser.add_argument(
        '--base_dir',
        type=str,
        default='.',
        help='Base directory containing industry folders (default: current directory)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='images',
        help='Output directory for images (default: images)'
    )
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir).resolve()
    output_dir = base_dir / args.output
    
    pdf_to_images_thai(base_dir, output_dir)


if __name__ == "__main__":
    main()