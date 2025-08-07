import fitz  # PyMuPDF
import os

# Path to the PDF
pdf_path = "data/Cracking the AP Economics Macro & Micro Exams, 2018 Edition_ -- Review, Princeton(Contributor) -- Penguin Random House LLC, New York, NY, 2017 -- 9781524710057 -- 1cf122260738a27d81d8cc62e9069d80 -- Anna's Archive.pdf"

if os.path.exists(pdf_path):
    print(f"PDF found at: {pdf_path}")
    
    # Open the PDF
    doc = fitz.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    
    # Get the table of contents
    toc = doc.get_toc()
    print("\nTable of Contents (first 20 entries):")
    for i, entry in enumerate(toc[:20]):
        level, title, page = entry
        print(f"{'  ' * (level-1)}{title} ... page {page}")
    
    # Look for microeconomics section
    print("\nSearching for Microeconomics chapters...")
    for i, entry in enumerate(toc):
        level, title, page = entry
        if "micro" in title.lower() or "scarcity" in title.lower() or "choice" in title.lower():
            print(f"{'  ' * (level-1)}{title} ... page {page}")
    
    doc.close()
else:
    print(f"PDF not found at: {pdf_path}")