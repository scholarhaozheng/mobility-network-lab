# Create the Boston native L3 environment

A clean Windows environment has been created from the exact 34-package Conda lock and three hash-pinned pip wheels. All 42 environment checks passed. A fresh rank-26/rank-52 native run and independent verification also passed, with zero difference from both historical objective values. The [clean-install receipt](../../experiments/environment-verification/boston-native-clean.json) records package identities, execution steps and numerical results.

Use Windows x86-64. The frozen controller uses Windows process and memory APIs. The normal repository command runs in its separate Python 3.12 environment; the native child uses Python 3.9.25. Do not replace the repository environment with the native one.

The [Conda explicit lock](../../environments/boston-native-win-64.lock) contains the exact 34-package transitive closure needed by Python, NumPy and IPOPT, including MKL, ASL, MUMPS and runtime libraries. Each official package URL includes its original archive MD5; the [manifest](../../environments/boston-native-manifest.json) also records SHA-256. The [pip requirements](../../environments/boston-native-pip.txt) pin three exact Windows CPython 3.9 wheels with SHA-256 hashes.

| Component | Pinned version | Distribution |
|---|---|---|
| Python | 3.9.25 | Conda |
| NumPy | 2.0.2 | Conda |
| IPOPT | 3.14.19 | Conda |
| MUMPS sequential | 5.8.1 | Conda dependency of IPOPT |
| Pyomo | 6.9.5 | PyPI Windows wheel |
| SciPy | 1.13.1 | PyPI Windows wheel |
| PLY | 3.11 | PyPI wheel, required by Pyomo |

The Boston native profile does not import pandas or psutil. They are not needed by this minimal environment; its process monitoring uses ctypes and PowerShell. This lock is specific to the Boston profile and is not a complete export of unrelated tools from the historical workstation.

Install [Conda for Windows](https://docs.conda.io/projects/conda/en/stable/user-guide/install/windows.html) if `conda` is unavailable, then open a PowerShell terminal where `conda` works. From the repository root, after completing the ordinary repository setup:

```powershell
# Windows x86-64; requires Conda. Clean installation and both native ranks were verified.
$nativePrefix = Join-Path (Get-Location) '.mcl-runtime\native-boston'
$nativePackageCache = Join-Path $env:LOCALAPPDATA 'mcl-native-pkgs'
$previousCondaPackageCache = $env:CONDA_PKGS_DIRS
try {
    $env:CONDA_PKGS_DIRS = $nativePackageCache
    conda create --yes --prefix $nativePrefix --file environments/boston-native-win-64.lock
    if ($LASTEXITCODE -ne 0) { throw 'Native Conda creation failed.' }
} finally {
    $env:CONDA_PKGS_DIRS = $previousCondaPackageCache
}
& (Join-Path $nativePrefix 'python.exe') -m pip install --no-deps --require-hashes -r environments/boston-native-pip.txt
if ($LASTEXITCODE -ne 0) { throw 'Native pip installation failed.' }
.\.venv\Scripts\python.exe tools/reproduction/check_boston_native_environment.py --prefix $nativePrefix
if ($LASTEXITCODE -ne 0) { throw 'Native environment identity check failed.' }
$env:MCL_NATIVE_PYTHON = Join-Path $nativePrefix 'python.exe'
$env:MCL_IPOPT = Join-Path $nativePrefix 'Library\bin\ipopt.exe'
.\.venv\Scripts\python.exe tools/mcl_reproduce.py run boston-native-l3-ranks26-52 --output results/boston-native-l3-ranks26-52
.\.venv\Scripts\python.exe tools/mcl_reproduce.py verify boston-native-l3-ranks26-52 --run results/boston-native-l3-ranks26-52
```

Create the prefix once. For subsequent runs, reuse it, rerun its identity check, set the two environment variables and choose a new result directory. The checker verifies exact Conda package versions/builds/hashes, Python and pip package versions, scientific-library imports and the IPOPT executable identity. It runs no optimizer and performs no installation. It passed against both the original runtime and the independently created clean environment. Keep the package-cache path short: the initial deeply nested cache hit Windows MAX_PATH while extracting setuptools; a shorter isolated cache resolved it without changing package versions. The commands restore the previous cache setting after Conda finishes.

The acquisition routes follow the [Conda explicit environment specification](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html#building-identical-conda-environments) and [pip hash-checking installation](https://pip.pypa.io/en/stable/topics/secure-installs/). The lock retains the exact Anaconda and conda-forge channels used by the verified installation; the listed packages retain their own license terms. No local package cache, machine path, credential or native binary is distributed.
