#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stable_test GJF Engine V1.7.2 check-path

Fixes:
1. BPW91 / UBPW91 and common unrestricted functionals are recognized.
2. Gaussian basis names are recognized case-insensitively:
   6-311+G(d), 6-311+g(d), 6-311+G*, 6-311G**, 6-31+G(d), etc.
3. Link1 stable/stable=opt uses ChkBasis by default, so the stability step
   always reads the same basis from the checkpoint instead of silently falling
   back to STO-3G.
4. Original %chk is respected.
5. V1.6-style right-click CLI is retained.
"""

import re
import os
import shutil
import shlex
import sys
import argparse


class ChemAutoGJFHandler:
    def __init__(self):
        self.steps = []
        self.warnings = []
        self.filename = ""

        self.KNOWN_FUNCTIONALS = {
            # GGA / meta-GGA / hybrids
            "bp86", "ubp86",
            "bpw91", "ubpw91",
            "pbepbe", "upbepbe",
            "pbe1pbe", "upbe1pbe",
            "b3lyp", "ub3lyp",
            "tpsstpss", "utpsstpss",
            "tpssh", "utpssh",
            "m06", "um06",
            "m06l", "um06l",
            "m062x", "um062x",
            "bhandhlyp", "ubhandhlyp",
            "cam-b3lyp", "ucam-b3lyp",
            "wb97xd", "uwb97xd",
            "b97d", "ub97d",
            "b2plyp", "ub2plyp",
            "mpw2plyp", "umpw2plyp",
            # wavefunction methods often used in route position
            "hf", "uhf", "rhf", "rohf",
            "mp2", "ump2", "omp2",
            "ccsd", "uccsd", "ccsd(t)", "uccsd(t)",
        }

        self.FUNCTIONAL_ALIASES = {
            "pbe": "pbepbe",
            "upbe": "upbepbe",
            "pbe0": "pbe1pbe",
            "upbe0": "upbe1pbe",
            "tpss": "tpsstpss",
            "utpss": "utpsstpss",
            "m06-2x": "m062x",
            "um06-2x": "um062x",
            "m06-l": "m06l",
            "um06-l": "um06l",
        }

        self.KNOWN_BASIS_SETS = {
            "chkbasis", "gen", "genecp",
            "sto-3g", "3-21g", "6-21g", "4-31g",
            "lanl2dz", "sdd",
            "def2svp", "def2svpd",
            "def2tzvp", "def2tzvpd",
            "def2tzvpp", "def2tzvppd",
            "def2qzvp", "def2qzvpd", "def2qzvpp", "def2qzvppd",
            "cc-pvdz", "cc-pvtz", "cc-pvqz",
            "aug-cc-pvdz", "aug-cc-pvtz", "aug-cc-pvqz",
        }

    # ------------------------------
    # Route recognition helpers
    # ------------------------------
    def _normalize_token(self, token):
        return token.strip().lower()

    def _is_functional_or_method(self, token_lower):
        return token_lower in self.KNOWN_FUNCTIONALS or token_lower in self.FUNCTIONAL_ALIASES

    def _is_basis(self, token_lower):
        t = token_lower.strip()

        if t in self.KNOWN_BASIS_SETS:
            return True

        # Gaussian Pople-style basis sets:
        # 6-31G(d), 6-31+G(d), 6-311+G*, 6-311++G(2d,p), 6-311G**, etc.
        if re.match(r"^(?:3-21|4-31|6-21|6-31|6-311)(?:\+\+|\+)?g(?:\([0-9a-z,*/+\-]+\)|\*+)?$", t):
            return True

        # def2 family, including def2-TZVPPD / def2tzvppd.
        if re.match(r"^def2-?[a-z0-9]+$", t):
            return True

        # correlation-consistent families.
        if re.match(r"^(?:aug-|jun-|jul-|may-)?cc-pv[dtq56]z(?:-pp)?$", t):
            return True

        return False

    def _canonical_method(self, method_lower):
        return self.FUNCTIONAL_ALIASES.get(method_lower, method_lower)

    # ------------------------------
    # Parser
    # ------------------------------
    def load_from_text(self, text, filename="default"):
        self.filename = filename
        self.steps = []
        self.warnings = []

        text = re.sub(r"\r+\n", "\n", text)
        text = text.replace("\r", "\n")

        raw_steps = re.split(r"^\s*--link1--\s*$", text, flags=re.MULTILINE | re.IGNORECASE)

        for step_idx, step_text in enumerate(raw_steps):
            if not step_text.strip():
                continue

            blocks = [b.strip() for b in re.split(r"\n\s*\n", step_text.strip()) if b.strip()]
            step_data = self._process_blocks(blocks, step_idx + 1)
            self._validate_step(step_data)
            self.steps.append(step_data)

    def _process_blocks(self, blocks, step_id):
        step_data = {
            "step_id": step_id,
            "link0": {},
            "route": {},
            "title": "",
            "molecule": {"charge": "", "multiplicity": "", "coords": ""},
            "additional": []
        }

        if not blocks:
            return step_data

        control_lines = blocks[0].split("\n")
        route_raw = []
        for line in control_lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            if line_stripped.startswith("%"):
                if "=" in line_stripped:
                    key, val = line_stripped[1:].split("=", 1)
                    step_data["link0"][key.strip().lower()] = val.strip()
                else:
                    self.warnings.append(f"[Step {step_id}] Link0 行无法解析：{line_stripped}")

            elif line_stripped.startswith("#"):
                route_raw.append(line_stripped)

            elif route_raw:
                route_raw.append(line_stripped)

        step_data["route"] = self._parse_route_section(" ".join(route_raw))

        if len(blocks) > 1:
            step_data["title"] = blocks[1]

        if len(blocks) > 2:
            lines = blocks[2].split("\n")
            if lines and len(lines[0].split()) >= 2:
                step_data["molecule"]["charge"], step_data["molecule"]["multiplicity"] = lines[0].split()[:2]
                step_data["molecule"]["coords"] = "\n".join(lines[1:])
            else:
                step_data["additional"].append(blocks[2])

        if len(blocks) > 3:
            step_data["additional"].extend(blocks[3:])

        return step_data

    def _parse_route_section(self, route_str):
        parsed = {
            "print_level": "",
            "method": "",
            "basis_set": "",
            "job_types": [],
            "options": {},
            "standalone_opts": [],
            "raw": route_str
        }

        if not route_str.strip():
            return parsed

        # Protect options with parentheses: opt=(...), scf=(...), td=(...)
        pattern_parens = re.compile(r"([A-Za-z0-9_-]+)\s*=\s*\(([^)]*)\)")
        protected = []
        def repl_parens(match):
            key = match.group(1).lower()
            vals = [v.strip().lower() for v in re.split(r"[, ]+", match.group(2)) if v.strip()]
            parsed["options"][key] = vals
            token = f"__OPT{len(protected)}__"
            protected.append(match.group(0))
            return " "

        route_cleaned = pattern_parens.sub(repl_parens, route_str)

        # Protect single-value options: opt=calcall, guess=read, geom=check, int=superfine
        pattern_single = re.compile(r"([A-Za-z0-9_-]+)\s*=\s*([^\s/()]+)")
        route_cleaned2 = ""
        last = 0
        for match in pattern_single.finditer(route_cleaned):
            key = match.group(1).lower()
            val = match.group(2).strip().lower()
            parsed["options"][key] = [val]
            route_cleaned2 += route_cleaned[last:match.start()] + " "
            last = match.end()
        route_cleaned2 += route_cleaned[last:]
        route_cleaned = route_cleaned2

        tokens = route_cleaned.split()
        if not tokens:
            return parsed

        if tokens[0].startswith("#"):
            parsed["print_level"] = tokens.pop(0).lower()

        known_jobs = {"opt", "freq", "sp", "stable", "td", "nmr", "scan", "irc", "polar", "force"}

        for token in tokens:
            token_lower = self._normalize_token(token)

            if not token_lower:
                continue

            # method/basis written together
            if "/" in token_lower:
                method_raw, basis_raw = token_lower.split("/", 1)
                if method_raw:
                    parsed["method"] = self._canonical_method(method_raw)
                if basis_raw:
                    parsed["basis_set"] = basis_raw
                continue

            if token_lower in known_jobs:
                if token_lower not in parsed["job_types"]:
                    parsed["job_types"].append(token_lower)
                continue

            if self._is_functional_or_method(token_lower):
                parsed["method"] = self._canonical_method(token_lower)
                continue

            if self._is_basis(token_lower):
                parsed["basis_set"] = token_lower
                continue

            parsed["standalone_opts"].append(token_lower)

        return parsed

    def _validate_step(self, step_data):
        step_id = step_data["step_id"]
        method = step_data["route"].get("method", "").lower()
        basis = step_data["route"].get("basis_set", "").lower()
        additional_blocks = step_data.get("additional", [])

        if not method:
            self.warnings.append(f"[Step {step_id}] 警告：未能识别方法/泛函，追加 stable 时可能无法构建正确 route。")

        if not basis:
            self.warnings.append(f"[Step {step_id}] 警告：未能识别基组；新 Link1 将优先使用 ChkBasis。")

        if basis in ["gen", "genecp"] and not additional_blocks:
            self.warnings.append(f"[Step {step_id}] 警告：基组为 {basis}，但未检测到附加自定义基组块。")

        if basis in self.KNOWN_FUNCTIONALS or basis in self.FUNCTIONAL_ALIASES:
            self.warnings.append(f"[Step {step_id}] 警告：基组位置疑似出现泛函名称：{basis}")

    # ------------------------------
    # Modifier
    # ------------------------------
    def add_stability_check(self, mode="stable"):
        if not self.steps:
            return False, "无计算步骤。"

        for step in self.steps:
            r = step["route"]
            if "stable" in r.get("job_types", []) or "stable" in r.get("options", {}):
                return False, f"第 {step['step_id']} 步已存在波函数稳定性测试，跳过修改。"

        step1 = self.steps[0]
        base_name = self.filename if self.filename else "default"

        original_chk = step1["link0"].get("chk", "").strip()
        chk_filename = original_chk or f"{base_name}.chk"
        step1["link0"]["chk"] = chk_filename

        original_method = step1["route"].get("method", "")
        original_basis = step1["route"].get("basis_set", "")

        # For Link1 stability calculation, ChkBasis is safest:
        # 1) simple basis: exact same basis from chk;
        # 2) Gen/GenECP: avoids missing custom basis block;
        # 3) prevents accidental Gaussian fallback to STO-3G.
        link1_basis = "chkbasis" if original_basis else ""

        link1_step = {
            "step_id": len(self.steps) + 1,
            "link0": {},
            "route": {
                "print_level": step1["route"].get("print_level", "#p"),
                "method": original_method,
                "basis_set": link1_basis,
                "job_types": [],
                "options": {
                    "guess": ["read"],
                    "geom": ["check"]
                },
                "standalone_opts": []
            },
            "title": f"Wavefunction Stability Check ({mode})",
            "molecule": {
                "charge": step1["molecule"].get("charge", ""),
                "multiplicity": step1["molecule"].get("multiplicity", ""),
                "coords": ""
            },
            "additional": []
        }

        if "nprocshared" in step1["link0"]:
            link1_step["link0"]["nprocshared"] = step1["link0"]["nprocshared"]
        if "mem" in step1["link0"]:
            link1_step["link0"]["mem"] = step1["link0"]["mem"]

        # Inherit safe standalone/options such as int=superfine, nosymm, scf=xqc.
        blacklisted = {"opt", "freq", "guess", "geom", "stable", "sp", "td", "nmr", "scan", "irc", "force"}
        for key, vals in step1["route"].get("options", {}).items():
            if key not in blacklisted:
                link1_step["route"]["options"][key] = list(vals)

        for opt in step1["route"].get("standalone_opts", []):
            if opt.lower() not in blacklisted:
                link1_step["route"]["standalone_opts"].append(opt)

        if mode == "stable=opt":
            link1_step["link0"]["oldchk"] = chk_filename
            link1_step["link0"]["chk"] = f"{base_name}-stable.chk"
            link1_step["route"]["options"]["stable"] = ["opt"]
        elif mode == "stable":
            # Stable check should not write back into the opt/freq checkpoint.
            # Copy original chk to a separate check chk via %oldchk/%chk,
            # then run stable on the copied checkpoint.
            chk_root, chk_ext = os.path.splitext(chk_filename)
            check_chk_filename = f"{chk_root}-check{chk_ext or '.chk'}"
            link1_step["link0"]["oldchk"] = chk_filename
            link1_step["link0"]["chk"] = check_chk_filename
            link1_step["route"]["job_types"].append("stable")
        else:
            return False, f"未知 mode: {mode}"

        if not original_method:
            return False, "未能识别原始方法/泛函，已停止，避免生成无方法的错误 Link1。"

        self.steps.append(link1_step)
        return True, "成功追加 Link1 稳定性测试；Check 模式使用 %oldchk 复制原 chk 到 原chk名-check.chk，原 chk 不被直接写入。"

    # ------------------------------
    # Builder
    # ------------------------------
    def build_text(self):
        out_lines = []

        for idx, step in enumerate(self.steps):
            if idx > 0:
                out_lines.append("--link1--")

            for key, val in step.get("link0", {}).items():
                out_lines.append(f"%{key}={val}")

            route_str = self._build_route_string(step.get("route", {}))
            out_lines.append(route_str if route_str else step.get("route", {}).get("raw", ""))
            out_lines.append("")

            if step.get("title"):
                out_lines.append(step["title"])
                out_lines.append("")

            charge = step.get("molecule", {}).get("charge")
            mult = step.get("molecule", {}).get("multiplicity")
            coords = step.get("molecule", {}).get("coords")

            if charge and mult:
                out_lines.append(f"{charge} {mult}")
                if coords:
                    out_lines.append(coords)
                out_lines.append("")

            if step.get("additional"):
                for block in step["additional"]:
                    out_lines.append(block)
                    out_lines.append("")

        out_lines.extend(["", ""])
        return "\n".join(out_lines)

    def _build_route_string(self, route):
        if not route:
            return ""

        parts = []
        if route.get("print_level"):
            parts.append(route["print_level"])

        method = route.get("method", "")
        basis = route.get("basis_set", "")

        if method and basis:
            parts.append(f"{method}/{basis}")
        elif method:
            parts.append(method)
        elif basis:
            # Do not silently delete basis; expose it if method is missing.
            parts.append(basis)

        if route.get("job_types"):
            parts.extend(route["job_types"])

        for key, val_list in route.get("options", {}).items():
            if not val_list:
                continue
            if len(val_list) == 1:
                parts.append(f"{key}={val_list[0]}")
            else:
                parts.append(f"{key}=({','.join(val_list)})")

        if route.get("standalone_opts"):
            parts.extend(route["standalone_opts"])

        return " ".join(parts)


# ------------------------------
# File / CLI helpers
# ------------------------------
def normalize_mode(mode):
    mode = (mode or "").strip().lower()
    aliases = {
        "check": "stable",
        "add-check": "stable",
        "add_check": "stable",
        "stable-check": "stable",
        "stable_check": "stable",
        "stable": "stable",
        "add-stable": "stable=opt",
        "add_stable": "stable=opt",
        "stableopt": "stable=opt",
        "stable-opt": "stable=opt",
        "stable_opt": "stable=opt",
        "stable=opt": "stable=opt",
    }
    if mode not in aliases:
        raise ValueError("mode 只能是 stable/check 或 stable=opt/add-stable。")
    return aliases[mode]


def read_text_safely(filepath):
    with open(filepath, "rb") as f:
        raw = f.read()

    candidates = ["utf-8-sig"] if raw.startswith(b"\xef\xbb\xbf") else []
    candidates.extend(["utf-8", "gbk", "latin-1"])

    for enc in candidates:
        try:
            text = raw.decode(enc)
            text = re.sub(r"\r+\n", "\n", text)
            text = text.replace("\r", "\n")
            return text, enc
        except UnicodeDecodeError:
            continue

    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"\r+\n", "\n", text).replace("\r", "\n")
    return text, "utf-8"


def collect_gjf_from_one_path(path):
    path = str(path).strip().strip("\"'")
    valid_files = []

    if not path or not os.path.exists(path):
        return valid_files

    if os.path.isfile(path) and path.lower().endswith(".gjf"):
        valid_files.append(path)
    elif os.path.isdir(path):
        for filename in os.listdir(path):
            fpath = os.path.join(path, filename)
            if os.path.isfile(fpath) and filename.lower().endswith(".gjf"):
                valid_files.append(fpath)

    return valid_files


def process_gjf_file(filepath, mode):
    try:
        mode = normalize_mode(mode)
        content, enc = read_text_safely(filepath)

        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]

        handler = ChemAutoGJFHandler()
        handler.load_from_text(content, filename=base_name)

        if handler.warnings:
            print(f"  [诊断] {filename} 存在语法隐患:")
            for w in handler.warnings:
                print(f"    - {w}")

        success, msg = handler.add_stability_check(mode=mode)

        if success:
            new_content = handler.build_text()
            out_enc = enc if enc not in ("latin-1",) else "utf-8"
            with open(filepath, "w", encoding=out_enc, newline="\n") as f:
                f.write(new_content)

            label = "Add Check / stable" if mode == "stable" else "Add Stable / stable=opt"
            print(f"  [成功] {filename} -> {label}: {msg} (已直接覆盖，无 .bak)")
        else:
            print(f"  [跳过] {filename} -> {msg}")

    except Exception as e:
        print(f"  [失败] {filepath} 处理时发生系统错误: {e}")


def parse_user_input_to_files(raw_input):
    valid_files = []
    raw_input = str(raw_input).strip()

    valid_files.extend(collect_gjf_from_one_path(raw_input))
    if valid_files:
        return list(dict.fromkeys(valid_files))

    try:
        paths = shlex.split(raw_input, posix=False)
    except ValueError:
        paths = raw_input.split()

    for p in paths:
        valid_files.extend(collect_gjf_from_one_path(p))

    return list(dict.fromkeys(valid_files))


def run_batch(paths, mode):
    mode = normalize_mode(mode)
    all_files = []

    for raw in paths:
        all_files.extend(collect_gjf_from_one_path(raw))

    all_files = list(dict.fromkeys(all_files))

    if not all_files:
        print("\n❌ 未检测到任何有效的 .gjf 文件，请检查路径。")
        return 1

    print("\n" + "=" * 50)
    print(f"✅ 成功提取 {len(all_files)} 个任务，待处理队列：")
    print("=" * 50)
    for idx, fpath in enumerate(all_files, 1):
        print(f"  [{idx:02d}] {fpath}")

    print("\n[系统] 开始执行批量处理...")
    print("-" * 50)
    for fpath in all_files:
        process_gjf_file(fpath, mode)
    print("-" * 50)
    print("🎉 批量处理完毕！")
    return 0


def parse_cli_args(argv):
    parser = argparse.ArgumentParser(
        description="stable_test: add Gaussian wavefunction stability Link1 section, no bak."
    )
    parser.add_argument(
        "--mode",
        choices=["stable", "stable=opt", "check", "add-check", "add-stable"],
        help="stable/check = 只添加 Stable 检查；stable=opt/add-stable = 添加 Stable=Opt。"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="一个或多个 .gjf 文件路径或文件夹路径。"
    )
    return parser, parser.parse_args(argv)


def main():
    print("==============================================")
    print("       stable_test GJF 工具 no-bak no-icon        ")
    print("==============================================")

    while True:
        print("\n=== 主菜单 ===")
        print("1. 添加波函数稳定性检测 (Stable Check)")
        print("q. 退出程序")
        choice = input("\n请选择功能编号:\n").strip()

        if choice.lower() == "q":
            print("退出程序。")
            break

        if choice != "1":
            print("无效的输入，请重新选择。")
            continue

        print("\n  -- 波函数检测模式 --")
        print("  1. stable (仅检查波函数稳定性)")
        print("  2. stable=opt (检查并在不稳定时优化至稳定波函数)")
        sub_choice = input("\n  请选择模式 (1/2):\n").strip()

        if sub_choice == "1":
            mode = "stable"
        elif sub_choice == "2":
            mode = "stable=opt"
        else:
            print("  无效的选择，返回主菜单。")
            continue

        raw = input("\n📁 请拖入文件或文件夹并按回车执行:\n")
        if not raw.strip():
            continue

        gjf_files = parse_user_input_to_files(raw)
        run_batch(gjf_files, mode)


def cli_or_interactive_main():
    if len(sys.argv) > 1:
        parser, args = parse_cli_args(sys.argv[1:])
        if not args.mode or not args.paths:
            parser.print_help()
            return 2
        return run_batch(args.paths, args.mode)

    main()
    return 0


if __name__ == "__main__":
    sys.exit(cli_or_interactive_main())
