# LivePyxel  [![arXiv](https://img.shields.io/badge/arXiv-2509.13504-b31b1b.svg)](https://arxiv.org/abs/2509.13504)



![logo livePyxel](./documentation/Figures/main_logo.png)

**LivePyxel** is a Python-based GUI for fast pixel annotation of images captured directly from a webcam feed. It’s designed to speed up dataset preparation for instance segmentation and other ML workflows.

---

## Tutorials
- **Getting started**: https://ugarcil.github.io/LivePyxel/tutorials.html

---

## Requirements
- **Python**: 3.9 – 3.12 recommended
- **OS**: Windows, macOS, or Linux
- **Core deps** (installed for you via pip unless using a conda env below):
  - PyQt5 (Qt5)
  - OpenCV (cv2)
  - NumPy

> Tip: If you’re on Windows and prefer Conda, see the **Conda** section; Conda’s Qt/OpenCV packages are very reliable there.

---

## Option A — Quick install from PyPI (recommended for users)

```bash
pip install --upgrade pip
pip install livepyxel
```

Run the app:

```bash
LivePyxel
# or
livepyxel
# or
python -m livepyxel
```

### (Optional) Create a virtual environment first
**Windows (PowerShell / cmd):**
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install livepyxel
LivePyxel
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install livepyxel
LivePyxel
```

---

## Option B — Conda environments

You can use Conda to manage Python and heavy binary deps (Qt, OpenCV, NumPy), and then install LivePyxel from PyPI **without** re-installing those deps via pip.

### 1) End users (install the released package)
Run the file **`environment.yml`** at the repo root

This will create a new env called livepyxel-env, then run the app:
```bash
conda activate livepyxel
LivePyxel
```


---

## Option C — From source with pip (no Conda)

For contributors who prefer pure pip/venv:

```bash
git clone https://github.com/UGarCil/LivePyxel.git
cd LivePyxel

python -m venv .venv
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install --upgrade pip
pip install -e .            # editable install for development
LivePyxel
```

If you have defined dev extras in `pyproject.toml`, you can do:
```bash
pip install -e ".[dev]"
```

---

## Troubleshooting

- **Command not found**: make sure your virtualenv/conda env is activated before running `LivePyxel`.
- **Black window / missing icons**: ensure you’re on the latest version and that package data is included (it is by default from PyPI). If running from source, verify `livepyxel/icons/` exists.
- **Import errors when running a module directly**: launch via `LivePyxel` or `python -m livepyxel` (not by `python livepyxel/imageAnnotator.py`) so package-relative imports work.
- **OpenCV or Qt conflicts in Conda**: stick to the Conda packages (`pyqt`, `opencv`, `numpy`) and use `pip ... --no-deps` for LivePyxel.
- **Python version**: prefer Python 3.9–3.12. Python 3.13 support is pending upstream wheels for some deps.

---

## License
This project is released under the **MIT License**. See `LICENSE` for details.

---

## Links
- **Docs & Tutorials**: https://ugarcil.github.io/LivePyxel/
- **Issues**: https://github.com/UGarCil/LivePyxel/issues
- **PyPI**: https://pypi.org/project/livepyxel/

---

## Bibtex [![arXiv](https://img.shields.io/badge/arXiv-2509.13504-b31b1b.svg)](https://arxiv.org/abs/2509.13504)
If you like LivePyxel please give is :star: and cite our work.

```latex
@misc{livepyxel,
      title={LivePyxel: Accelerating image annotations with a Python-integrated webcam live streaming}, 
      author={Uriel Garcilazo-Cruz and Joseph O. Okeme and Rodrigo A. Vargas-Hernández},
      year={2025},
      eprint={2509.13504},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2509.13504}, 
}
```
