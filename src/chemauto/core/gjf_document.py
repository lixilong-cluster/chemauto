from __future__ import annotations

"""Read, inspect and rewrite Gaussian input files without discarding unknown data.

The editor intentionally keeps every Link1 section independent.  Common route
components are exposed as structured fields, while unrecognised keywords remain
in ``extra_tokens`` and all combo boxes in the GUI are editable.  This gives a
compact editor without pretending that a finite list can cover every Gaussian
keyword.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable

LINK1_RE = re.compile(r"^\s*--\s*link1\s*--\s*$", re.I)
CHARGE_MULT_RE = re.compile(r"^\s*(-?\d+)\s+(\d+)\s*$")


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_route(route: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    depth = 0
    for char in route.strip():
        if char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth = max(0, depth - 1)
            current.append(char)
        elif char.isspace() and depth == 0:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)
    if current:
        tokens.append("".join(current))
    return tokens


def token_key(token: str) -> str:
    low = token.strip().lower()
    if "=" in low:
        return low.split("=", 1)[0]
    if "(" in low:
        return low.split("(", 1)[0]
    return low


@dataclass
class RouteComponents:
    prefix: str = "#p"
    job: str = "sp"
    method: str = ""
    basis: str = ""
    opt: str = ""
    scf: str = ""
    integral: str = ""
    geom: str = ""
    guess: str = ""
    freq: str = ""
    extra_tokens: list[str] = field(default_factory=list)

    @classmethod
    def parse(cls, route: str) -> "RouteComponents":
        tokens = split_route(route)
        out = cls()
        if tokens and tokens[0].startswith("#"):
            out.prefix = tokens.pop(0)

        method_basis_taken = False
        job_tokens: list[str] = []
        extras: list[str] = []
        for token in tokens:
            low = token.lower()
            key = token_key(token)
            if not method_basis_taken and "/" in token and not low.startswith("iop("):
                out.method, out.basis = token.split("/", 1)
                method_basis_taken = True
            elif not method_basis_taken and key in {
                "hf", "rhf", "uhf", "rohf", "b3lyp", "ub3lyp", "pbe0", "pbe1pbe",
                "pbepbe", "upbepbe", "bpw91", "ubpw91", "bp86", "ubp86", "tpss",
                "utpss", "tpssh", "utpssh", "m062x", "um062x", "wb97xd", "uwb97xd",
                "r2scan", "ur2scan", "mp2", "ump2", "ccsd", "uccsd",
            }:
                out.method = token
                method_basis_taken = True
            elif key == "opt":
                out.opt = token
                job_tokens.append("opt")
            elif key == "freq":
                out.freq = token
                job_tokens.append("freq")
            elif key == "scf":
                out.scf = token
            elif key in {"int", "integral"}:
                out.integral = token
            elif key == "geom":
                out.geom = token
            elif key == "guess":
                out.guess = token
            elif key in {"sp", "stable", "irc", "scan", "force", "polar", "td", "pop"}:
                if key in {"sp", "stable", "irc", "scan", "force"}:
                    job_tokens.append(token)
                else:
                    extras.append(token)
            elif low in {"gen", "genecp", "chkbasis"} and not out.basis:
                out.basis = token
                method_basis_taken = True
            else:
                extras.append(token)

        if "opt" in job_tokens and "freq" in job_tokens:
            out.job = "opt freq"
        elif job_tokens:
            out.job = " ".join(job_tokens)
        else:
            out.job = "sp"
        out.extra_tokens = extras
        return out

    def build(self) -> str:
        tokens: list[str] = [self.prefix.strip() or "#p"]
        if self.method and self.basis:
            tokens.append(f"{self.method.strip()}/{self.basis.strip()}")
        elif self.method:
            tokens.append(self.method.strip())
        elif self.basis:
            tokens.append(self.basis.strip())

        job_low = self.job.strip().lower()
        if job_low in {"stable=opt", "stable(opt)"}:
            tokens.append("stable=opt")
        elif job_low == "stable":
            tokens.append("stable")
        elif "opt" in job_low:
            tokens.append(self.opt.strip() or "opt")
        elif job_low not in {"", "sp", "single point"}:
            tokens.extend(split_route(self.job))
        elif job_low == "sp":
            tokens.append("sp")
        if "freq" in job_low:
            tokens.append(self.freq.strip() or "freq")

        for value in (self.scf, self.integral, self.geom, self.guess):
            if value.strip():
                tokens.append(value.strip())
        tokens.extend(t.strip() for t in self.extra_tokens if t.strip())
        return " ".join(tokens)


@dataclass
class GJFLink:
    link0_lines: list[str]
    route: str
    title_lines: list[str]
    charge: int
    multiplicity: int
    coordinate_lines: list[str]
    tail_lines: list[str]
    components: RouteComponents = field(init=False)

    def __post_init__(self) -> None:
        self.components = RouteComponents.parse(self.route)

    def get_link0(self, key: str) -> str:
        pattern = re.compile(rf"^\s*%{re.escape(key)}\s*=\s*(.*?)\s*$", re.I)
        for line in self.link0_lines:
            match = pattern.match(line)
            if match:
                return match.group(1).strip().strip('"')
        return ""

    def set_link0(self, key: str, value: str) -> None:
        pattern = re.compile(rf"^\s*%{re.escape(key)}\s*=", re.I)
        value = value.strip()
        replacement = f"%{key}={value}" if value else ""
        for i, line in enumerate(self.link0_lines):
            if pattern.match(line):
                if replacement:
                    self.link0_lines[i] = replacement
                else:
                    self.link0_lines.pop(i)
                return
        if replacement:
            self.link0_lines.append(replacement)

    def has_custom_basis_tail(self) -> bool:
        if self.components.basis.lower() not in {"gen", "genecp"}:
            return True
        meaningful = [line for line in self.tail_lines if line.strip()]
        return bool(meaningful and any("****" in line for line in meaningful))

    def render(self) -> str:
        out: list[str] = []
        out.extend(self.link0_lines)
        out.append(self.components.build())
        out.append("")
        out.extend(self.title_lines or ["ChemAuto job"])
        out.append("")
        out.append(f"{self.charge} {self.multiplicity}")
        if self.coordinate_lines:
            out.extend(self.coordinate_lines)
        out.append("")
        out.extend(self.tail_lines)
        # Gaussian accepts extra blank lines; one terminating newline is enough.
        return "\n".join(out).rstrip() + "\n"


@dataclass
class GJFDocument:
    links: list[GJFLink]

    @classmethod
    def parse_text(cls, text: str) -> "GJFDocument":
        text = normalize_newlines(text)
        raw_sections: list[list[str]] = [[]]
        for line in text.split("\n"):
            if LINK1_RE.match(line):
                raw_sections.append([])
            else:
                raw_sections[-1].append(line)
        links = [parse_link(lines) for lines in raw_sections if any(x.strip() for x in lines)]
        if not links:
            raise ValueError("No Gaussian Link section was found.")
        return cls(links)

    @classmethod
    def from_file(cls, path: str | Path) -> "GJFDocument":
        p = Path(path)
        return cls.parse_text(p.read_text(encoding="utf-8", errors="ignore"))

    def render(self) -> str:
        return "\n--Link1--\n".join(link.render().rstrip() for link in self.links).rstrip() + "\n"

    def write(self, path: str | Path) -> Path:
        p = Path(path)
        p.write_text(self.render(), encoding="utf-8", newline="\n")
        return p


def parse_link(lines: list[str]) -> GJFLink:
    while lines and not lines[-1].strip():
        lines.pop()
    route_start = next((i for i, line in enumerate(lines) if line.lstrip().startswith("#")), None)
    if route_start is None:
        raise ValueError("A Link section has no route line beginning with '#'.")
    link0 = [line for line in lines[:route_start] if line.strip()]

    route_lines: list[str] = []
    i = route_start
    while i < len(lines) and (i == route_start or lines[i].strip()):
        route_lines.append(lines[i].strip())
        i += 1
    route = " ".join(x for x in route_lines if x)
    while i < len(lines) and not lines[i].strip():
        i += 1

    title: list[str] = []
    while i < len(lines) and lines[i].strip():
        title.append(lines[i])
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1

    cm_index = None
    charge = 0
    multiplicity = 1
    for j in range(i, len(lines)):
        match = CHARGE_MULT_RE.match(lines[j])
        if match:
            cm_index = j
            charge = int(match.group(1))
            multiplicity = int(match.group(2))
            break
    if cm_index is None:
        raise ValueError("A Link section has no charge/multiplicity line.")
    i = cm_index + 1

    coordinates: list[str] = []
    while i < len(lines) and lines[i].strip():
        coordinates.append(lines[i])
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    tail = lines[i:]
    return GJFLink(link0, route, title, charge, multiplicity, coordinates, tail)


def coordinates_from_xyz_text(xyz_text: str) -> list[str]:
    lines = [line.rstrip() for line in normalize_newlines(xyz_text).split("\n")]
    if not lines:
        return []
    try:
        int(lines[0].strip())
        lines = lines[2:]
    except Exception:
        pass
    return [line for line in lines if line.strip()]


def select_primary_gjf(source: str | Path) -> Path:
    """Resolve a source GJF/COM using deterministic, chemistry-friendly rules.

    Priority for a log/out file or directory:
      1. same stem as the log;
      2. same name as the calculation directory;
      3. the only GJF/COM in the directory;
      4. otherwise raise an ambiguity error so the GUI can ask the user.
    """
    p = Path(source).resolve()
    if p.suffix.lower() in {".gjf", ".com"} and p.is_file():
        return p
    directory = p if p.is_dir() else p.parent
    candidates = sorted(directory.glob("*.gjf")) + sorted(directory.glob("*.com"))
    if p.is_file() and p.suffix.lower() in {".log", ".out"}:
        for suffix in (".gjf", ".com"):
            same = p.with_suffix(suffix)
            if same.is_file():
                return same
    for suffix in (".gjf", ".com"):
        direct = directory / f"{directory.name}{suffix}"
        if direct.is_file():
            return direct
    if len(candidates) == 1:
        return candidates[0]
    names = ", ".join(x.name for x in candidates) or "none"
    raise ValueError(f"Cannot uniquely identify the primary GJF/COM in {directory}. Candidates: {names}")
