"""Download the CMIP6 monthly ensemble used by the CryoSENSE-HK projection layer.

Data acquisition only: no analysis happens here, and the analysis pipeline stays
in ``notebooks/Hakkari_ERA5_Land.ipynb``. The job is a script because it is a
long queued transfer against the Copernicus Climate Data Store rather than a step
that has to be re-run with the notebook.

Model selection is by availability, not by preference: every CMIP6 model that the
CDS serves with all four required variables across the historical, SSP2-4.5 and
SSP5-8.5 monthly collections is downloaded. The set was derived from the dataset
constraints file rather than chosen by hand, so the ensemble cannot be read as
cherry-picked.

``surface_snow_amount`` (snw, kg m-2 = mm w.e.) is the variable that lets the
projection be cross-checked against the ERA5-Land target in the same units. The
previous single-model setup compared snow water equivalent against snow thickness.

The Climate Data Store queues concurrent requests from one account behind each
other, so throughput comes from accounts rather than threads: each ``~/.cdsapirc*``
credential file gets its own worker and its own share of the request list, and a
worker walks its share one request at a time.

Usage:
    python scripts/download_cmip6_ensemble.py [--dry-run]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import logging
import sys
import time
import zipfile
from pathlib import Path

import cdsapi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cmip6")

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "nc_cilo_sat" / "SSP_ensemble"

DATASET = "projections-cmip6"

# Every model the CDS serves with tas, pr, prsn and snw across all three
# experiments at monthly resolution (checked against the dataset constraints).
MODELS = [
    "bcc_csm2_mr",
    "canesm5_canoe",
    "ec_earth3_cc",
    "ipsl_cm6a_lr",
    "miroc6",
    "miroc_es2l",
    "mpi_esm1_2_lr",
    "mri_esm2_0",
    "noresm2_mm",
    "taiesm1",
]

VARIABLES = {
    "near_surface_air_temperature": "tas",
    "precipitation": "pr",
    "snowfall_flux": "prsn",
    "surface_snow_amount": "snw",
}

# The historical window is the reference period the bias correction is fitted on;
# the scenario windows run to the end of the CMIP6 archive.
EXPERIMENTS = {
    "historical": range(1985, 2015),
    "ssp2_4_5": range(2015, 2100),
    "ssp5_8_5": range(2015, 2100),
}

# Wider than the 82-cell Hakkari domain so that a two-degree model still returns
# at least one land cell over the Cilo-Sat massif.
AREA = [38.5, 43.0, 36.5, 45.0]  # north, west, south, east
MONTHS = [f"{m:02d}" for m in range(1, 13)]


def target_path(short: str, model: str, experiment: str) -> Path:
    return OUT_DIR / f"{short}_{model}_{experiment}.zip"


def already_done(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with zipfile.ZipFile(path) as zf:
            return any(name.endswith(".nc") for name in zf.namelist())
    except zipfile.BadZipFile:
        return False


def read_credentials() -> list[tuple[str, str, str]]:
    """Return (name, url, key) for every ~/.cdsapirc* file holding a distinct key."""
    found, seen = [], set()
    for path in sorted(Path.home().glob(".cdsapirc*")):
        url = key = None
        for line in path.read_text().splitlines():
            if line.startswith("url:"):
                url = line.split(":", 1)[1].strip()
            elif line.startswith("key:"):
                key = line.split(":", 1)[1].strip()
        if url and key and key not in seen:
            seen.add(key)
            found.append((path.name, url, key))
    return found


def fetch(job: tuple[str, str, str], url: str, key: str) -> tuple[str, bool, str]:
    variable, model, experiment = job
    short = VARIABLES[variable]
    path = target_path(short, model, experiment)
    label = f"{short:5s} {model:15s} {experiment}"
    if already_done(path):
        return label, True, "cached"

    request = {
        "temporal_resolution": "monthly",
        "experiment": experiment,
        "variable": variable,
        "model": model,
        "year": [str(y) for y in EXPERIMENTS[experiment]],
        "month": MONTHS,
        "area": AREA,
    }
    start = time.time()
    try:
        cdsapi.Client(url=url, key=key, quiet=True, progress=False, retry_max=2).retrieve(
            DATASET, request, str(path))
    except Exception as exc:  # noqa: BLE001 - the CDS raises bare Exception subclasses
        path.unlink(missing_ok=True)
        return label, False, f"{type(exc).__name__}: {exc}"[:200]
    if not already_done(path):
        return label, False, "downloaded file holds no NetCDF payload"
    return label, True, f"{time.time() - start:.0f} s, {path.stat().st_size / 1024:.0f} KB"


def run_share(name: str, url: str, key: str, share: list[tuple[str, str, str]],
              counter: dict) -> list[tuple[str, str]]:
    """Walk one account's share of the request list, one request at a time."""
    failures = []
    for job in share:
        label, ok, note = fetch(job, url, key)
        counter["done"] += 1
        prefix = f"[{counter['done']:3d}/{counter['total']:3d}] {name:12s}"
        if ok:
            logger.info("%s %s  %s", prefix, label, note)
        else:
            failures.append((label, note))
            logger.error("%s %s  FAILED %s", prefix, label, note)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--models", default="",
                        help="comma-separated subset; the rest are assumed to come from the "
                             "Google Cloud CMIP6 archive, which has no request queue")
    args = parser.parse_args()

    selected = [m.strip() for m in args.models.split(",") if m.strip()] or MODELS
    unknown = set(selected) - set(MODELS)
    if unknown:
        logger.error("unknown models: %s", ", ".join(sorted(unknown)))
        return 1

    credentials = read_credentials()
    if not credentials:
        logger.error("no usable ~/.cdsapirc* credentials found")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs = [(variable, model, experiment)
            for variable in VARIABLES
            for model in selected
            for experiment in EXPERIMENTS]
    pending = [job for job in jobs
               if not already_done(target_path(VARIABLES[job[0]], job[1], job[2]))]
    logger.info("%d requests total, %d already on disk, %d to fetch across %d accounts",
                len(jobs), len(jobs) - len(pending), len(pending), len(credentials))
    if args.dry_run:
        for index, (name, _, _) in enumerate(credentials):
            share = pending[index::len(credentials)]
            logger.info("%s would take %d requests", name, len(share))
        return 0

    counter = {"done": 0, "total": len(pending)}
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(credentials)) as pool:
        futures = [pool.submit(run_share, name, url, key,
                               pending[index::len(credentials)], counter)
                   for index, (name, url, key) in enumerate(credentials)]
        for future in concurrent.futures.as_completed(futures):
            failures.extend(future.result())

    logger.info("finished: %d succeeded, %d failed", len(pending) - len(failures), len(failures))
    for label, note in failures:
        logger.error("failed: %s  %s", label, note)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
