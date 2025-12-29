from pathlib import Path
from typing import List


# Project root is two levels above this file (src/utils -> src -> project root)
_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "data"

def list_data_files() -> List[str]:
	"""Return a list of .txt filenames in the project's `data/` directory."""
	if not _DATA_DIR.exists():
		return []
	return [p.name for p in sorted(_DATA_DIR.glob("*.txt")) if p.is_file()]


def read_data_file(filename: str, encoding: str = "utf-8") -> str:
	"""Read and return the text content of `data/<filename>`.

	Raises FileNotFoundError if the file does not exist.
	"""
	path = _DATA_DIR / filename
	if not path.exists():
		raise FileNotFoundError(f"Data file not found: {path}")
	return path.read_text(encoding=encoding)


def load_cv(filename: str = "cv_candidato1.txt") -> str:
	"""Load the candidate CV text from the data directory (default filename provided)."""
	return read_data_file(filename)


def load_offer(filename: str = "oferta.txt") -> str:
	"""Load the job offer text from the data directory (default filename provided)."""
	return read_data_file(filename)



