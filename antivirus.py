#!/usr/bin/env python3
"""SentinelAV: escáner antivirus local con firmas, heurística, cuarentena y monitoreo."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import stat
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_DB = Path("signatures.json")
DEFAULT_QUARANTINE = Path("quarantine")
DEFAULT_REPORTS = Path("reports")

SUSPICIOUS_EXTENSIONS = {
    ".exe",
    ".dll",
    ".bat",
    ".cmd",
    ".ps1",
    ".vbs",
    ".scr",
    ".hta",
    ".js",
    ".jar",
    ".wsf",
}

SUSPICIOUS_KEYWORDS = {
    "powershell -enc",
    "invoke-expression",
    "mimikatz",
    "net user",
    "reg add",
    "certutil -urlcache",
    "wget http",
    "curl http",
    "frombase64string",
    "new-object net.webclient",
}

PROFILE_THRESHOLDS = {
    "balanced": 45,
    "strict": 30,
    "paranoid": 20,
}


@dataclass
class Detection:
    file_path: str
    reason: str
    score: int
    digest: str | None = None


@dataclass
class ScanStats:
    scanned_files: int = 0
    skipped_files: int = 0
    matched_signatures: int = 0
    matched_heuristics: int = 0


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    ent = 0.0
    n = len(data)
    for count in freq:
        if count:
            p = count / n
            ent -= p * math.log2(p)
    return ent


def load_signatures(db_path: Path) -> dict[str, str]:
    if not db_path.exists():
        return {}
    raw = json.loads(db_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("El archivo de firmas debe ser un objeto JSON {sha256: nombre}.")
    return {str(k).lower(): str(v) for k, v in raw.items()}


def should_exclude(path: Path, excludes: Sequence[Path]) -> bool:
    for exc in excludes:
        try:
            path.relative_to(exc)
            return True
        except ValueError:
            continue
    return False


def iter_files(target: Path, recursive: bool = True) -> Iterable[Path]:
    if target.is_file():
        yield target
        return
    iterator = target.rglob("*") if recursive else target.glob("*")
    for path in iterator:
        if path.is_file():
            yield path


def heuristic_score(path: Path) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    suffix = path.suffix.lower()
    if suffix in SUSPICIOUS_EXTENSIONS:
        score += 25
        reasons.append("extensión ejecutable/scripting")

    try:
        st = path.stat()
        if st.st_size > 40 * 1024 * 1024:
            score += 10
            reasons.append("archivo inusualmente grande")
        if not (st.st_mode & stat.S_IRUSR):
            score += 15
            reasons.append("permiso de lectura anómalo")
    except OSError:
        score += 20
        reasons.append("error al leer metadatos")

    try:
        sample = path.read_bytes()[:512 * 1024]
        text_sample = sample.decode("utf-8", errors="ignore").lower()
        if suffix in SUSPICIOUS_EXTENSIONS:
            for kw in SUSPICIOUS_KEYWORDS:
                if kw in text_sample:
                    score += 20
                    reasons.append(f"keyword sospechosa: {kw}")

        if entropy(sample) > 7.4 and len(sample) > 16 * 1024:
            score += 20
            reasons.append("alta entropía (ofuscación/packing)")
    except OSError:
        score += 10
        reasons.append("no se pudo abrir para análisis")

    return score, reasons


def quarantine_file(path: Path, quarantine_dir: Path) -> Path:
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    dst = quarantine_dir / f"{timestamp}_{path.name}.quarantined"
    shutil.move(str(path), str(dst))
    return dst


def write_report(report_dir: Path, payload: dict) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"scan_{ts}.json"
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return report_path


def scan_path(
    target: Path,
    signatures: dict[str, str],
    threshold: int,
    excludes: Sequence[Path],
) -> tuple[list[Detection], ScanStats]:
    detections: list[Detection] = []
    stats = ScanStats()

    for file in iter_files(target):
        if should_exclude(file, excludes):
            stats.skipped_files += 1
            continue

        stats.scanned_files += 1
        try:
            digest = sha256sum(file).lower()
            if digest in signatures:
                detections.append(
                    Detection(
                        file_path=str(file),
                        reason=f"firma conocida: {signatures[digest]}",
                        score=100,
                        digest=digest,
                    )
                )
                stats.matched_signatures += 1
                continue
        except OSError:
            detections.append(
                Detection(file_path=str(file), reason="no se pudo calcular hash", score=50)
            )
            stats.matched_heuristics += 1
            continue

        h_score, reasons = heuristic_score(file)
        if h_score >= threshold:
            detections.append(
                Detection(
                    file_path=str(file),
                    reason="; ".join(reasons),
                    score=h_score,
                    digest=digest,
                )
            )
            stats.matched_heuristics += 1

    return detections, stats


def print_report(detections: list[Detection], stats: ScanStats) -> None:
    if not detections:
        print("✅ No se detectaron amenazas.")
    else:
        print(f"⚠️ Detectadas {len(detections)} posibles amenazas:\n")
        for d in detections:
            print(f"- {d.file_path} | score={d.score} | {d.reason}")

    print("\nResumen:")
    print(f"- Archivos escaneados: {stats.scanned_files}")
    print(f"- Archivos excluidos: {stats.skipped_files}")
    print(f"- Coincidencias por firma: {stats.matched_signatures}")
    print(f"- Coincidencias heurísticas: {stats.matched_heuristics}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SentinelAV - escáner antivirus local (firmas + heurística + cuarentena)."
    )
    parser.add_argument("target", type=Path, help="Archivo o carpeta a escanear")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Base de firmas JSON")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_THRESHOLDS.keys()),
        default="balanced",
        help="Perfil de sensibilidad para heurística",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="Umbral heurístico personalizado (0-100). Sobrescribe --profile",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Ruta a excluir (se puede repetir)",
    )
    parser.add_argument(
        "--quarantine",
        action="store_true",
        help="Mueve archivos detectados a cuarentena",
    )
    parser.add_argument(
        "--quarantine-dir",
        type=Path,
        default=DEFAULT_QUARANTINE,
        help="Carpeta de cuarentena",
    )
    parser.add_argument(
        "--json-report",
        action="store_true",
        help="Guardar reporte JSON en carpeta reports/",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORTS,
        help="Carpeta para reportes JSON",
    )
    parser.add_argument(
        "--watch",
        type=int,
        default=0,
        help="Monitoreo continuo: reescanea cada N segundos (0 desactiva)",
    )
    return parser.parse_args()


def run_once(args: argparse.Namespace) -> int:
    if not args.target.exists():
        print(f"❌ Ruta no encontrada: {args.target}")
        return 2

    try:
        signatures = load_signatures(args.db)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"❌ Error cargando base de firmas: {exc}")
        return 3

    threshold = args.threshold if args.threshold is not None else PROFILE_THRESHOLDS[args.profile]
    excludes = [Path(p).resolve() for p in args.exclude]
    detections, stats = scan_path(args.target.resolve(), signatures, threshold, excludes)

    print_report(detections, stats)

    quarantine_map: list[dict[str, str]] = []
    if args.quarantine and detections:
        print("\nMoviendo a cuarentena...")
        for d in detections:
            try:
                src = Path(d.file_path)
                if src.exists():
                    dst = quarantine_file(src, args.quarantine_dir)
                    quarantine_map.append({"from": d.file_path, "to": str(dst)})
                    print(f"  -> {d.file_path} => {dst}")
            except OSError as exc:
                print(f"  ❌ Error en cuarentena para {d.file_path}: {exc}")

    if args.json_report:
        payload = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "target": str(args.target),
            "threshold": threshold,
            "stats": asdict(stats),
            "detections": [asdict(d) for d in detections],
            "quarantine": quarantine_map,
        }
        path = write_report(args.report_dir, payload)
        print(f"\n📝 Reporte JSON: {path}")

    return 1 if detections else 0


def main() -> int:
    args = parse_args()

    if args.watch <= 0:
        return run_once(args)

    print(f"👀 Monitoreo activo: escaneo cada {args.watch}s. Ctrl+C para salir.")
    exit_code = 0
    try:
        while True:
            print("\n=== Nuevo ciclo de escaneo ===")
            cycle_code = run_once(args)
            if cycle_code > exit_code:
                exit_code = cycle_code
            time.sleep(args.watch)
    except KeyboardInterrupt:
        print("\n⏹️ Monitoreo detenido por usuario.")
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
