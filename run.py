import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        return None

load_dotenv()

PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(str(PROJECT_ROOT))

from src.schemas import CandidateMasterCV
from src.tools.cv_extractor import extract_cv


CV_PATH = PROJECT_ROOT / "data" / "example-resume.pdf"
OUTPUT_DIR = PROJECT_ROOT / "data" / "extracted"
OUTPUT_PATH = OUTPUT_DIR / f"{CV_PATH.stem}.json"


def main():
    print("Running CV extraction stage...\n")

    extraction_result = extract_cv(str(CV_PATH))
    if extraction_result.get("error"):
        raise RuntimeError(extraction_result["error"])

    validated_cv = CandidateMasterCV.model_validate(extraction_result)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(validated_cv.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )

    print("===== EXTRACTION COMPLETE =====")
    print(f"Output JSON: {OUTPUT_PATH}")
    print(f"Candidate: {validated_cv.contact.full_name}")
    print(f"Skills: {len(validated_cv.skills)}")
    print(f"Work experiences: {len(validated_cv.work_experience)}")
    print(f"Education records: {len(validated_cv.education)}")

    if validated_cv.metadata.warnings:
        print("Warnings:")
        for warning in validated_cv.metadata.warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()