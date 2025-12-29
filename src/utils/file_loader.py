from pathlib import Path
from typing import List




def read_data_file(filename: str, encoding: str = "utf-8") -> str:
	"""Read and return the text content of `data/<filename>`.

	Raises FileNotFoundError if the file does not exist.
	"""
	# path = _DATA_DIR / filename
	if not filename.exists():
		raise FileNotFoundError(f"Data file not found: {filename}")
	return filename.read_text(encoding=encoding)


def load_cv(filename: str = "cv_candidato1.txt") -> str:
	"""Load the candidate CV text from the data directory (default filename provided)."""
	return read_data_file(filename)


def load_offer(filename: str = "oferta.txt") -> str:
	"""Load the job offer text from the data directory (default filename provided)."""
	return read_data_file(filename)



