"""Fetch the CMIP6 members that neither the cloud archive nor the CDS queue delivers.

Three routes serve the same published CMIP6 files. The Google Cloud archive is the
fastest but does not carry a complete member for every model. The Climate Data Store
carries them but queues ESGF-backed requests globally, and that queue has been
several hundred deep. ESGF itself serves the files over plain HTTP with no queue,
one file per year or per decade, so the remaining members are pulled from there and
subset to the massif locally.

Member choice is the first variant that carries all four variables across the
historical, SSP2-4.5 and SSP5-8.5 runs, matching the rule used for the cloud route.

Usage:
    python scripts/fetch_cmip6_from_esgf.py [--models a,b] [--dry-run]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import io
import json
import logging
import sys
import threading
import urllib.parse
import urllib.request
import warnings
from collections import defaultdict
from pathlib import Path

import pandas as pd
import xarray as xr

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger("esgf")

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "nc_cilo_sat" / "SSP_ensemble"
SEARCH = "https://esgf-node.llnl.gov/esg-search/search"

MODELS = {
    "ec_earth3_cc": "EC-Earth3-CC",
    "miroc_es2l": "MIROC-ES2L",
    "noresm2_mm": "NorESM2-MM",
    "taiesm1": "TaiESM1",
}
VARIABLES = {"tas": "Amon", "pr": "Amon", "prsn": "Amon", "snw": "LImon"}
EXPERIMENTS = {"historical": "historical", "ssp245": "ssp2_4_5", "ssp585": "ssp5_8_5"}
LAT_RANGE = (36.5, 38.5)
LON_RANGE = (43.0, 45.0)
HISTORICAL_YEARS = (1985, 2014)

# The NetCDF stack sits on HDF5, which is not thread safe. Reads of in-memory
# payloads have proved fine, but concurrent file opens and writes take the whole
# process down with no traceback, so every file touch goes through this lock.
FILE_LOCK = threading.Lock()


def search(**query) -> list[dict]:
    """Paged ESGF query. The index truncates large responses, so pages stay small
    and a page that arrives incomplete is simply asked for again."""
    query.setdefault("project", "CMIP6")
    query.setdefault("format", "application/solr+json")
    query.setdefault("distrib", "true")
    page = int(query.pop("limit", 200))
    docs, offset = [], 0
    while True:
        payload = None
        for attempt in range(4):
            url = SEARCH + "?" + urllib.parse.urlencode({**query, "limit": page, "offset": offset})
            try:
                with urllib.request.urlopen(url, timeout=120) as handle:
                    payload = json.loads(handle.read().decode())
                break
            except Exception as exc:  # noqa: BLE001 - transient index failures are routine
                if attempt == 3:
                    raise
                logger.debug("search retry %d (%s)", attempt + 1, str(exc)[:60])
                page = max(50, page // 2)
        found = payload["response"]["docs"]
        docs.extend(found)
        total = payload["response"]["numFound"]
        offset += len(found)
        if not found or offset >= total:
            return docs


def pick_member(source_id: str) -> tuple[str, str] | None:
    """First member and grid label carrying every variable in every experiment."""
    catalogue = defaultdict(set)
    grids = defaultdict(set)
    for variable, table in VARIABLES.items():
        for experiment in EXPERIMENTS:
            for doc in search(source_id=source_id, variable_id=variable, table_id=table,
                              experiment_id=experiment, type="Dataset"):
                for member in doc.get("member_id", []):
                    catalogue[(variable, experiment)].add(member)
                    for grid in doc.get("grid_label", []):
                        grids[(member, grid)].add((variable, experiment))
    needed = {(v, e) for v in VARIABLES for e in EXPERIMENTS}
    complete = [m for m in set().union(*catalogue.values())
                if all(m in catalogue[key] for key in needed)]
    if not complete:
        return None
    for member in sorted(complete, key=lambda m: (m != "r1i1p1f1", m)):
        for (candidate_member, grid), covered in grids.items():
            if candidate_member == member and covered >= needed:
                return member, grid
        # fall back to whichever grid covers the most of the requirement
        best = max((g for (m, g) in grids if m == member),
                   key=lambda g: len(grids[(member, g)]), default=None)
        if best:
            return member, best
    return None


def file_urls(source_id: str, member: str, grid: str, variable: str, table: str,
              experiment: str) -> list[list[str]]:
    """Every mirror of every file, so a dead node costs a retry and not a gap."""
    docs = search(source_id=source_id, variant_label=member, grid_label=grid,
                  variable_id=variable, table_id=table, experiment_id=experiment,
                  type="File")
    mirrors = defaultdict(list)
    for doc in docs:
        for entry in doc.get("url", []):
            if entry.endswith("HTTPServer"):
                mirrors[doc["title"]].append(entry.split("|")[0])
    return [sorted(set(mirrors[title]), key=lambda u: "diasjp" in u)  # that node times out
            for title in sorted(mirrors)]


def read_subset(urls: list[str]) -> xr.Dataset | None:
    """Try every mirror of one file twice before giving up on it."""
    payload = None
    for attempt in range(2):
        for url in urls:
            try:
                with urllib.request.urlopen(url, timeout=240) as handle:
                    payload = handle.read()
                break
            except Exception as exc:  # noqa: BLE001
                logger.debug("mirror failed %s: %s", url.split("/")[2], str(exc)[:60])
        if payload is not None:
            break
    if payload is None:
        logger.warning("  every mirror failed for %s", urls[0].split("/")[-1])
        return None
    ds = xr.open_dataset(io.BytesIO(payload))
    lon = ds["lon"]
    west, east = LON_RANGE
    if float(lon.min()) >= 0 and west < 0:
        west, east = west % 360, east % 360
    subset = ds.sel(lat=slice(*LAT_RANGE), lon=slice(west, east))
    if subset.sizes.get("lat", 0) == 0 or subset.sizes.get("lon", 0) == 0:
        subset = ds.sel(lat=[sum(LAT_RANGE) / 2], lon=[sum(LON_RANGE) / 2], method="nearest")
    return subset.load()


def expected_months(experiment: str) -> int:
    if experiment == "historical":
        return 12 * (HISTORICAL_YEARS[1] - HISTORICAL_YEARS[0] + 1)
    return 12 * (2099 - 2015 + 1)


def fetch_one(key: str, source_id: str, member: str, grid: str, variable: str,
              experiment: str, dry_run: bool) -> tuple[bool, str]:
    table = VARIABLES[variable]
    path = OUT_DIR / f"{variable}_{key}_{EXPERIMENTS[experiment]}.nc"
    wanted = expected_months(experiment)
    if path.exists() and path.stat().st_size > 0:
        with FILE_LOCK, xr.open_dataset(path) as existing:
            months = existing.sizes.get("time", 0)
        if months >= wanted:
            return True, f"cached, {months} months"
        # A short file means mirrors dropped out on an earlier pass. Refetch it
        # rather than let a gap reach the bias correction unnoticed.
        logger.info("  %-5s %-11s refetching: %d of %d months on disk",
                    variable, experiment, months, wanted)
        path.unlink()
    groups = file_urls(source_id, member, grid, variable, table, experiment)
    if not groups:
        return False, "no files published"
    if experiment == "historical":
        keep = [g for g in groups
                if any(str(year) in g[0].split("_")[-1]
                       for year in range(HISTORICAL_YEARS[0] - 10, HISTORICAL_YEARS[1] + 1))]
        groups = keep or groups
    if dry_run:
        return True, f"would fetch {len(groups)} files"

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        pieces = [piece for piece in pool.map(read_subset, groups) if piece is not None]
    if not pieces:
        return False, f"all {len(groups)} downloads failed"
    combined = xr.concat(pieces, dim="time").sortby("time")
    combined = combined[[variable]] if variable in combined else combined
    if experiment == "historical":
        combined = combined.sel(time=slice(f"{HISTORICAL_YEARS[0]}-01-01",
                                           f"{HISTORICAL_YEARS[1]}-12-31"))
    months = combined.sizes["time"]
    if months < wanted:
        # Reported, never silent: an incomplete series would bias the reference
        # period of the quantile mapping without changing anything visible.
        return False, (f"incomplete: {len(pieces)}/{len(groups)} files gave {months} of "
                       f"{wanted} months")
    with FILE_LOCK:
        combined.to_netcdf(path)
    return True, f"{len(pieces)}/{len(groups)} files, {months} months"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    selected = [m.strip() for m in args.models.split(",") if m.strip()] or list(MODELS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    provenance, failures = [], []
    for key in selected:
        source_id = MODELS[key]
        picked = pick_member(source_id)
        if picked is None:
            failures.append((key, "no member carries the full variable set"))
            logger.error("%s: no complete member published", key)
            continue
        member, grid = picked
        logger.info("%s (%s): member %s, grid %s", key, source_id, member, grid)
        # The index search dominates the wall clock, so the twelve variable and
        # experiment combinations are walked concurrently rather than one by one.
        combinations = [(variable, experiment) for variable in VARIABLES
                        for experiment in EXPERIMENTS]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(
                lambda combo: (combo, fetch_one(key, source_id, member, grid, combo[0],
                                                combo[1], args.dry_run)),
                combinations))
        for (variable, experiment), (ok, note) in results:
                if ok:
                    logger.info("  %-5s %-11s %s", variable, experiment, note)
                    if not args.dry_run and not note.startswith("cached"):
                        provenance.append({"model": key, "source_id": source_id,
                                           "member_id": member, "variable": variable,
                                           "experiment": EXPERIMENTS[experiment],
                                           "route": "esgf-http", "store": f"grid {grid}"})
                else:
                    failures.append((f"{key}/{variable}/{experiment}", note))
                    logger.error("  %-5s %-11s FAILED %s", variable, experiment, note)

    if provenance:
        record = pd.DataFrame(provenance)
        path = OUT_DIR / "cmip6_ensemble_provenance.csv"
        if path.exists():
            record = pd.concat([pd.read_csv(path), record], ignore_index=True).drop_duplicates(
                subset=["model", "variable", "experiment"], keep="last")
        record.to_csv(path, index=False)
        logger.info("provenance updated: %d triples on record", len(record))

    logger.info("finished with %d failures", len(failures))
    for what, why in failures:
        logger.error("failed: %s  %s", what, why)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
