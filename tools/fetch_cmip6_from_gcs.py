"""Fetch the CMIP6 ensemble members that the Google Cloud CMIP6 archive carries.

The Climate Data Store serves the same CMIP6 files but queues ESGF-backed requests
globally: with two dozen slots shared across all users and several hundred requests
waiting, a single variable can sit for half an hour. The Google Cloud copy of the
archive (the Pangeo CMIP6 collection) has no queue and is stored as Zarr, so only
the handful of grid cells over the massif has to be read. A full 86-year monthly
series arrives in seconds.

Both routes deliver the same published CMIP6 data, so members are taken from
whichever route carries them and the source of each member is recorded in
``cmip6_ensemble_provenance.csv`` next to the files.

One member per model, chosen as the first variant that carries all four variables
across the historical, SSP2-4.5 and SSP5-8.5 runs. Models the cloud archive cannot
complete stay with the Climate Data Store script.

Usage:
    python scripts/fetch_cmip6_from_gcs.py [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys
import warnings
from pathlib import Path

import pandas as pd
import xarray as xr

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger("gcs")

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "nc_cilo_sat" / "SSP_ensemble"
CATALOGUE = "https://storage.googleapis.com/cmip6/pangeo-cmip6.csv"

# Keys are the names used by the Climate Data Store script so that both routes
# write files the notebook reads with one loader.
MODELS = {
    "bcc_csm2_mr": "BCC-CSM2-MR",
    "canesm5_canoe": "CanESM5-CanOE",
    "ipsl_cm6a_lr": "IPSL-CM6A-LR",
    "miroc6": "MIROC6",
    "mpi_esm1_2_lr": "MPI-ESM1-2-LR",
    "mri_esm2_0": "MRI-ESM2-0",
}

VARIABLES = {"tas": "Amon", "pr": "Amon", "prsn": "Amon", "snw": "LImon"}
EXPERIMENTS = ["historical", "ssp245", "ssp585"]

# Same box as the Climate Data Store requests: wider than the 82-cell domain so a
# two-degree model still returns a land cell over the massif.
LAT_RANGE = (36.5, 38.5)
LON_RANGE = (43.0, 45.0)
REFERENCE_YEARS = (1985, 2014)


def pick_member(catalogue: pd.DataFrame, source_id: str) -> str | None:
    """First variant carrying every variable in every experiment."""
    subset = catalogue[catalogue.source_id == source_id]
    for member in sorted(set(subset.member_id)):
        one = subset[subset.member_id == member]
        if all(len(one[(one.variable_id == variable) & (one.table_id == table)
                       & (one.experiment_id == experiment)]) > 0
               for variable, table in VARIABLES.items()
               for experiment in EXPERIMENTS):
            return member
    return None


def fetch(store: str, variable: str, path: Path) -> str:
    ds = xr.open_zarr(store, storage_options={"token": "anon"}, consolidated=True)
    lon = ds["lon"]
    west, east = LON_RANGE
    if float(lon.min()) >= 0 and west < 0:  # 0-360 grids
        west, east = west % 360, east % 360
    subset = ds[variable].sel(lat=slice(*LAT_RANGE), lon=slice(west, east))
    if subset.sizes.get("lat", 0) == 0 or subset.sizes.get("lon", 0) == 0:
        # A coarse grid can miss the box edges; fall back to the nearest cell.
        subset = ds[variable].sel(lat=[sum(LAT_RANGE) / 2], lon=[sum(LON_RANGE) / 2],
                                  method="nearest")
    subset = subset.load()
    subset.to_netcdf(path)
    ds.close()
    return f"{subset.sizes.get('lat', 0)}x{subset.sizes.get('lon', 0)} cells, {subset.sizes['time']} months"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("reading the Google Cloud CMIP6 catalogue")
    catalogue = pd.read_csv(CATALOGUE)

    provenance, failures = [], []
    for key, source_id in MODELS.items():
        member = pick_member(catalogue, source_id)
        if member is None:
            failures.append((key, "no member carries the full variable set"))
            logger.error("%s: no complete member on the cloud archive", key)
            continue
        logger.info("%s (%s): member %s", key, source_id, member)
        for variable, table in VARIABLES.items():
            for experiment in EXPERIMENTS:
                path = OUT_DIR / f"{variable}_{key}_{experiment.replace('ssp245', 'ssp2_4_5').replace('ssp585', 'ssp5_8_5')}.nc"
                if path.exists() and path.stat().st_size > 0:
                    logger.info("  %-5s %-11s cached", variable, experiment)
                    continue
                rows = catalogue[(catalogue.source_id == source_id)
                                 & (catalogue.member_id == member)
                                 & (catalogue.variable_id == variable)
                                 & (catalogue.table_id == table)
                                 & (catalogue.experiment_id == experiment)]
                if rows.empty:
                    failures.append((f"{key}/{variable}/{experiment}", "absent from the catalogue"))
                    continue
                store = rows.iloc[0].zstore
                if args.dry_run:
                    logger.info("  %-5s %-11s would fetch %s", variable, experiment, store)
                    continue
                try:
                    note = fetch(store, variable, path)
                except Exception as exc:  # noqa: BLE001
                    path.unlink(missing_ok=True)
                    failures.append((f"{key}/{variable}/{experiment}", f"{type(exc).__name__}: {exc}"[:160]))
                    logger.error("  %-5s %-11s FAILED %s", variable, experiment, exc)
                    continue
                logger.info("  %-5s %-11s %s", variable, experiment, note)
                provenance.append({"model": key, "source_id": source_id, "member_id": member,
                                   "variable": variable, "experiment": experiment,
                                   "route": "google-cloud-cmip6", "store": store})

    if provenance:
        record = pd.DataFrame(provenance)
        path = OUT_DIR / "cmip6_ensemble_provenance.csv"
        if path.exists():
            record = pd.concat([pd.read_csv(path), record], ignore_index=True).drop_duplicates(
                subset=["model", "variable", "experiment"], keep="last")
        record.to_csv(path, index=False)
        logger.info("provenance written for %d model-variable-experiment triples", len(record))

    logger.info("finished with %d failures", len(failures))
    for what, why in failures:
        logger.error("failed: %s  %s", what, why)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
