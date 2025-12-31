from pathlib import Path
from typing import List

def read_data_file(filename: str, encoding: str = "utf-8") -> str:
	"""
	Leer un archivo de datos desde el directorio 'data'.
	"""
	if not filename.exists():
		raise FileNotFoundError(f"Data file not found: {filename}")
	return filename.read_text(encoding=encoding)






