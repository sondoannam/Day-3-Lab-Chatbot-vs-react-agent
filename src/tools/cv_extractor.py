import pdfplumber
from typing import Dict, Any


def extract_cv(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts text content from a CV PDF file using pdfplumber.
    Preserves layout by reading page by page and joining with newlines.

    Args:
        pdf_path: Absolute or relative path to the CV PDF file.

    Returns:
        A dict with:
        - "content": full extracted text as a single string
        - "pages": number of pages
        - "source": the original pdf_path
        - "error": error message string if extraction failed, else None
    """
    try:
        full_text = []

        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)

            for page in pdf.pages:
                # extract_text() preserves reading order better than raw chars
                page_text = page.extract_text(x_tolerance=2, y_tolerance=3)
                if page_text:
                    full_text.append(page_text.strip())

        return {
            "content": "\n\n".join(full_text),
            "pages": num_pages,
            "source": pdf_path,
            "error": None,
        }

    except FileNotFoundError:
        return {
            "content": "",
            "pages": 0,
            "source": pdf_path,
            "error": f"File not found: {pdf_path}",
        }
    except Exception as e:
        return {
            "content": "",
            "pages": 0,
            "source": pdf_path,
            "error": str(e),
        }


# Tool dict — this is what gets passed into ReActAgent(tools=[...])
cv_extractor_tool = {
    "name": "extract_cv",
    "description": (
        "Extracts the full text content from a CV PDF file. "
        "Input: the file path to the PDF. "
        "Output: the extracted CV text."
    ),
    "function": extract_cv,
}