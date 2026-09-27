#!/usr/bin/env python3
"""Fetch only STEP models referenced by the PCB's existing JLC footprints.

The UUID chain and conversion follow dsa-t/jlc-kicad-lib-loader 1.0.11.
`device.json` in the project's .elibz supplies model UUIDs and expected body
sizes. Raw downloads stay in a temporary directory; KiCad's Python normalizes
them into EASYEDA_MODELS so the existing ${KIPRJMOD} links work unchanged.
"""

from __future__ import annotations

import concurrent.futures
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

import requests


HERE = Path(__file__).resolve().parent
BOARD = HERE / "DAC_HPA.kicad_pcb"
LIBRARY = HERE / "JLC_Source/JLC_DAC_HPA.elibz"
OUTPUT = HERE / "EASYEDA_MODELS"
CACHE = Path(os.environ.get("DAC_HPA_MODEL_CACHE", "/private/tmp/dac-hpa-jlc-model-cache"))
KICAD_PYTHON = os.environ.get(
    "KICAD_PYTHON",
    "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3",
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://pro.easyeda.com/",
}
UUID = re.compile(r"[0-9a-f]{32}")


def required_titles() -> set[str]:
    source = BOARD.read_text(encoding="utf-8")
    return set(re.findall(
        r'\(model "\$\{KIPRJMOD\}/EASYEDA_MODELS/([^"/]+)\.step"', source
    ))


def model_catalog() -> dict[str, dict]:
    with zipfile.ZipFile(LIBRARY) as archive:
        devices = json.loads(archive.read("device.json"))["devices"]
    catalog = {}
    for device in devices.values():
        attrs = device["attributes"]
        title, uuid = attrs.get("3D Model Title"), attrs.get("3D Model")
        if title and uuid:
            uuid = uuid.split("|")[0]
            if not UUID.fullmatch(uuid):
                raise ValueError(f"Invalid model UUID for {title}")
            entry = {"title": title, "model_uuid": uuid,
                     "transform": attrs.get("3D Model Transform", ""),
                     "lcsc_code": device.get("product_code")}
            if title in catalog and catalog[title]["model_uuid"] != uuid:
                raise ValueError(f"Conflicting model UUIDs for {title}")
            catalog.setdefault(title, entry)
    return catalog


def get_json(url: str) -> dict:
    last = None
    for attempt in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("success") is not True:
                raise ValueError(f"EasyEDA did not return success: {str(result)[:200]}")
            return result["result"]
        except Exception as error:
            last = error
            time.sleep(1 + attempt)
    raise RuntimeError(f"Unable to read {url}: {last}")


def model_data(component: dict) -> dict:
    value = component.get("dataStr")
    if not value and component.get("dataStrId"):
        from Crypto.Cipher import AES
        response = requests.get(component["dataStrId"], headers=HEADERS, timeout=30)
        response.raise_for_status()
        encrypted = response.content
        cipher = AES.new(bytes.fromhex(component["key"]), AES.MODE_GCM,
                         nonce=bytes.fromhex(component["iv"]))
        value = gzip.GzipFile(fileobj=io.BytesIO(
            cipher.decrypt_and_verify(encrypted[:-16], encrypted[-16:])
        )).read().decode("utf-8")
    if not value:
        raise ValueError("Model component contains no dataStr")
    result = json.loads(value)
    if not UUID.fullmatch(result.get("model", "")):
        raise ValueError("Model component has no direct STEP UUID")
    return result


def fetch_one(entry: dict, cache: Path) -> dict:
    title = entry["title"]
    component_url = f'https://pro.easyeda.com/api/v2/components/{entry["model_uuid"]}'
    component = get_json(component_url)
    if component.get("uuid") != entry["model_uuid"]:
        raise ValueError(f"Unexpected metadata UUID for {title}")
    data = model_data(component)
    direct_uuid = data["model"]
    step_url = f"https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/{direct_uuid}"
    path = cache / f"{title}.step"
    if path.is_file() and path.stat().st_size > 1000 and path.read_bytes().startswith(b"ISO-10303-21;"):
        content = path.read_bytes()
        return {**entry, "direct_uuid": direct_uuid,
                "component_url": component_url, "step_url": step_url,
                "raw_path": str(path), "raw_bytes": len(content),
                "raw_sha256": hashlib.sha256(content).hexdigest()}
    last = None
    for attempt in range(3):
        try:
            response = requests.get(step_url, headers=HEADERS, timeout=90)
            response.raise_for_status()
            content = response.content
            if len(content) < 1000 or not content.startswith(b"ISO-10303-21;"):
                raise ValueError(f"Invalid STEP response for {title}")
            path.write_bytes(content)
            return {**entry, "direct_uuid": direct_uuid,
                    "component_url": component_url, "step_url": step_url,
                    "raw_path": str(path), "raw_bytes": len(content),
                    "raw_sha256": hashlib.sha256(content).hexdigest()}
        except Exception as error:
            last = error
            time.sleep(1 + attempt)
    raise RuntimeError(f"Unable to download STEP for {title}: {last}")


def main() -> None:
    titles = required_titles()
    catalog = model_catalog()
    missing = sorted(titles - catalog.keys())
    if missing:
        raise SystemExit(f"Board models missing from JLC source catalog: {missing}")
    OUTPUT.mkdir(exist_ok=True)
    provenance = OUTPUT / "MODEL_SOURCES.json"
    previous = json.loads(provenance.read_text()) if provenance.is_file() else []
    records_by_title = {item["title"]: item for item in previous}
    needed = [catalog[title] for title in sorted(titles)
              if not (OUTPUT / f"{title}.step").is_file()]
    print(f"Board references {len(titles)} JLC STEP titles; {len(needed)} need download", flush=True)
    if not needed:
        unrecorded = titles - records_by_title.keys()
        if unrecorded:
            raise SystemExit(f"STEP files lack source records: {sorted(unrecorded)}")
        return

    CACHE.mkdir(parents=True, exist_ok=True)
    fetched = []
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_one, entry, CACHE): entry["title"]
                   for entry in needed}
        for future in concurrent.futures.as_completed(futures):
            title = futures[future]
            try:
                item = future.result()
                fetched.append(item)
                print(f"Fetched {title}: {item['raw_bytes']:,} bytes", flush=True)
            except Exception as error:
                failed.append({"title": title, "error": str(error)})
                print(f"FAILED {title}: {error}", flush=True)

    for entry in sorted(fetched, key=lambda item: item["title"]):
        manifest = CACHE / (entry["title"] + ".json")
        manifest.write_text(json.dumps([entry], indent=2))
        log = CACHE / (entry["title"] + ".log")
        with log.open("w") as handle:
            completed = subprocess.run(
                [KICAD_PYTHON, str(HERE / "normalize_jlc_3d_models.py"),
                 str(manifest), str(OUTPUT)], stdout=handle, stderr=subprocess.STDOUT
            )
        if completed.returncode == 0:
            record = json.loads((OUTPUT / "MODEL_SOURCES.json").read_text())[0]
            print(f"Converted {entry['title']} with KiCad STEP utility", flush=True)
        else:
            # Some source STEP solids make KiCad's OpenCascade utility abort.
            # The original valid STEP is still usable in KiCad's 3D viewer;
            # retain it and flag its raw origin/alignment for visual review.
            destination = OUTPUT / (entry["title"] + ".step")
            shutil.copyfile(entry["raw_path"], destination)
            record = {key: value for key, value in entry.items() if key != "raw_path"}
            record.update({
                "converted_file": destination.name,
                "converted_bytes": destination.stat().st_size,
                "converted_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "warning": f"KiCad normalization exited {completed.returncode}; raw STEP retained",
            })
            print(f"Raw STEP retained for {entry['title']} after KiCad conversion failed", flush=True)
        records_by_title[entry["title"]] = record
    provenance.write_text(json.dumps(
        [records_by_title[title] for title in sorted(records_by_title)],
        indent=2, sort_keys=True
    ) + "\n")
    if failed:
        raise SystemExit(f"{len(failed)} JLC STEP downloads failed: {failed}")


if __name__ == "__main__":
    main()
