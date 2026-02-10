import os
import csv
import json
import re
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Set

# Optional deps
try:
    from rapidfuzz import fuzz, process  # type: ignore
    HAS_RAPIDFUZZ = True
except Exception:
    HAS_RAPIDFUZZ = False

try:
    from reportlab.lib.pagesizes import letter  # type: ignore
    from reportlab.pdfgen import canvas as pdf_canvas  # type: ignore
    HAS_REPORTLAB = True
except Exception:
    HAS_REPORTLAB = False

# =============================
# CONFIG
# =============================
BASE_DIR = r"C:\SyrHousing"
DATA_FILE = os.path.join(BASE_DIR, "Data", "grants_db.csv")
REPORT_DIR = os.path.join(BASE_DIR, "Reports")
SCAN_PS1 = os.path.join(BASE_DIR, "run_scan.ps1")
LOGO_PATH = os.path.join(BASE_DIR, "Assets", "Phoneix Logo.png")
HOME_PROFILE_PATH = os.path.join(BASE_DIR, "Data", "my_home_profile.json")
CHECKLIST_DIR = os.path.join(REPORT_DIR, "Checklists")

FIELDS = [
    "ProgramId", "Name", "Jurisdiction", "ProgramType", "MenuCategory",
    "RepairTags", "PriorityRank", "MaxBenefit", "StatusOrDeadline",
    "Agency", "Phone", "Email", "Website", "EligibilitySummary",
    "IncomeGuidance", "DocsChecklist", "LastVerified"
]

CORE_COLUMNS = ["Name", "MenuCategory", "PriorityRank", "MaxBenefit", "StatusOrDeadline", "Agency", "Phone", "Website"]


# =============================
# HELPERS
# =============================
def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def safe_open(path: str) -> None:
    try:
        os.startfile(path)  # type: ignore[attr-defined]
    except Exception as e:
        messagebox.showerror("Open failed", str(e))

def latest_report_path(report_dir: str) -> Optional[str]:
    if not os.path.exists(report_dir):
        return None
    files = [f for f in os.listdir(report_dir) if f.lower().endswith(".txt")]
    if not files:
        return None
    full = [os.path.join(report_dir, f) for f in files]
    full.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return full[0]

def load_csv(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def normalize_tags(s: str) -> Set[str]:
    if not s:
        return set()
    parts = [p.strip().lower() for p in s.split(";")]
    return {p for p in parts if p}

def parse_priority_rank(v: str) -> float:
    try:
        return float(str(v).strip())
    except Exception:
        return 0.0

def resize_photoimage(img: tk.PhotoImage, max_w: int = 260, max_h: int = 110) -> tk.PhotoImage:
    w, h = img.width(), img.height()
    if w <= 0 or h <= 0:
        return img
    fx = max(1, (w + max_w - 1) // max_w)
    fy = max(1, (h + max_h - 1) // max_h)
    f = max(fx, fy)
    return img if f <= 1 else img.subsample(f, f)

def load_home_profile() -> Dict:
    default = {
        "city": "Syracuse",
        "county": "Onondaga",
        "senior": True,
        "fixed_income": True,
        "repair_needs": ["heating", "roof", "structural"]
    }
    try:
        if os.path.exists(HOME_PROFILE_PATH):
            with open(HOME_PROFILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in default.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        pass
    return default

def save_home_profile(profile: Dict) -> None:
    ensure_dir(os.path.dirname(HOME_PROFILE_PATH))
    with open(HOME_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

def program_text(p: Dict[str, str]) -> str:
    parts = [p.get(k, "") for k in [
        "Name", "MenuCategory", "ProgramType", "RepairTags", "MaxBenefit",
        "StatusOrDeadline", "Agency", "EligibilitySummary", "IncomeGuidance",
        "DocsChecklist", "Website"
    ]]
    return " ".join([str(x) for x in parts if x])

def tokenize(text: str) -> Set[str]:
    text = (text or "").lower()
    return set(re.findall(r"[a-z0-9']{3,}", text))

def load_latest_scan_report_text() -> str:
    p = latest_report_path(REPORT_DIR)
    if not p:
        return ""
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""

# =============================
# RANKING
# =============================
def compute_rank(program: Dict[str, str], profile: Dict) -> Tuple[int, List[str]]:
    score = 0
    why: List[str] = []

    ptype = (program.get("ProgramType") or "").strip().lower()
    if "grant" in ptype:
        score += 35; why.append("+35: ProgramType indicates GRANT (preferred vs loans).")
    elif "deferred" in ptype or "forg" in ptype:
        score += 25; why.append("+25: Deferred/forgivable assistance.")
    elif "loan" in ptype:
        score += 10; why.append("+10: Loan product (less favorable than grants).")
    else:
        score += 12; why.append("+12: ProgramType unspecified; treated as general assistance.")

    cat = (program.get("MenuCategory") or "").strip().lower()
    if "urgent" in cat or "safety" in cat:
        score += 20; why.append("+20: URGENT SAFETY category aligns with critical repairs.")
    elif "health" in cat:
        score += 12; why.append("+12: HEALTH HAZARDS category.")
    elif "aging" in cat or "access" in cat:
        score += 10; why.append("+10: AGING IN PLACE/accessibility category.")
    elif "energy" in cat:
        score += 10; why.append("+10: ENERGY & BILLS category.")
    else:
        score += 6; why.append("+6: General category.")

    need = {str(n).strip().lower() for n in profile.get("repair_needs", []) if str(n).strip()}
    tags = normalize_tags(program.get("RepairTags") or "")
    hits = sorted(need.intersection(tags))
    if hits:
        pts = min(30, 10 * len(hits))
        score += pts
        why.append(f"+{pts}: Matches repair needs: {', '.join(hits)}.")
    else:
        score += 4
        why.append("+4: No explicit repair-tag match; verify scope.")

    jur = (program.get("Jurisdiction") or "").strip().lower()
    agency = (program.get("Agency") or "").strip().lower()
    if "syracuse" in jur or "syracuse" in agency:
        score += 10; why.append("+10: Syracuse/local administration.")
    elif "onondaga" in jur or "onondaga" in agency:
        score += 8; why.append("+8: Onondaga County/local administration.")
    elif "nys" in jur or "new york" in jur or "hcr" in agency or "nyserda" in agency:
        score += 6; why.append("+6: NY State program (often available locally).")
    else:
        score += 3; why.append("+3: Non-local jurisdiction; verify local availability.")

    blob = " ".join([
        program.get("Name", ""),
        program.get("EligibilitySummary", ""),
        program.get("IncomeGuidance", ""),
        program.get("DocsChecklist", "")
    ]).lower()

    if profile.get("senior", False):
        if "60" in blob or "62" in blob or "senior" in blob or "elderly" in blob:
            score += 8; why.append("+8: Senior/age wording detected.")
        else:
            score += 2; why.append("+2: Senior wording not detected; verify eligibility by phone.")

    if profile.get("fixed_income", False):
        if "income" in blob or "ami" in blob or "low income" in blob or "very-low" in blob:
            score += 6; why.append("+6: Income-based wording detected.")
        else:
            score += 2; why.append("+2: Income rules not stated; verify by phone.")

    pr = parse_priority_rank(program.get("PriorityRank", ""))
    if pr > 0:
        bump = int(min(10, pr / 10))
        if bump > 0:
            score += bump; why.append(f"+{bump}: Incorporates existing PriorityRank ({pr}).")

    score = max(0, min(100, int(score)))
    why.append(f"Final Score: {score}/100 (heuristic triage).")
    return score, why

# =============================
# CHATBOT (OFFLINE)
# =============================
def best_program_matches(question: str, programs: List[Dict[str, str]], limit: int = 5) -> List[Tuple[int, Dict[str, str]]]:
    q = question.strip()
    if not q:
        return []

    if HAS_RAPIDFUZZ:
        choices = {p.get("ProgramId", ""): program_text(p) for p in programs}
        pid_to_prog = {p.get("ProgramId", ""): p for p in programs}
        res = process.extract(q, choices, scorer=fuzz.WRatio, limit=limit)  # type: ignore
        out: List[Tuple[int, Dict[str, str]]] = []
        for (_text, score, pid) in res:
            prog = pid_to_prog.get(pid)
            if prog:
                out.append((int(score), prog))
        return out

    qtok = tokenize(q)
    scored: List[Tuple[int, Dict[str, str]]] = []
    for p in programs:
        ptok = tokenize(program_text(p))
        inter = len(qtok.intersection(ptok))
        denom = max(1, len(qtok))
        score = int(100 * (inter / denom))
        scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]

def chatbot_answer(question: str, programs: List[Dict[str, str]], profile: Dict) -> str:
    q = question.strip()
    if not q:
        return "Ask about roof/heating/structural programs, lead, accessibility, weatherization, or how to apply."

    matches = best_program_matches(q, programs, limit=5)
    scan_text = load_latest_scan_report_text()

    lines: List[str] = []
    lines.append("Local Grant Agent (offline mode)\n")
    lines.append(f"Profile: senior={profile.get('senior')}, fixed_income={profile.get('fixed_income')}, repairs={profile.get('repair_needs')}\n")
    lines.append("\nTop matches:\n")

    if not matches:
        lines.append("- No strong matches. Try: roof, furnace, heating, structural, lead, ramps, weatherization.\n")
    else:
        for score, p in matches:
            rank, why = compute_rank(p, profile)
            lines.append(f"\n[{p.get('Name','(no name)')}]")
            lines.append(f"\n  MatchScore: {score}/100 | Rank: {rank}/100")
            lines.append(f"\n  Category: {p.get('MenuCategory','')} | Type: {p.get('ProgramType','')}")
            lines.append(f"\n  Benefit: {p.get('MaxBenefit','')} | Status: {p.get('StatusOrDeadline','')}")
            lines.append(f"\n  Agency: {p.get('Agency','')} | Phone: {p.get('Phone','')}")
            lines.append(f"\n  Website: {p.get('Website','')}")
            lines.append("\n  Why: " + "; ".join(why[:4]) + "\n")

    if scan_text:
        snippet = scan_text[:800].strip()
        lines.append("\nLatest scan context (snippet):\n")
        lines.append(snippet + ("\n...\n" if len(scan_text) > 800 else "\n"))

    lines.append("\nNext step:\n- If you share household size + approximate income, I can guide what to ask agencies to confirm eligibility.\n")
    return "".join(lines)

# =============================
# CHECKLIST (TXT + PDF)
# =============================
def checklist_text(program: Dict[str, str], profile: Dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    needs = ", ".join(profile.get("repair_needs", []))
    lines: List[str] = []
    lines.append("SYRHOUSING – PROGRAM CHECKLIST\n")
    lines.append("=" * 36 + "\n")
    lines.append(f"Generated: {now}\n\n")
    lines.append(f"Program: {program.get('Name','')}\n")
    lines.append(f"Agency:  {program.get('Agency','')}\n")
    lines.append(f"Phone:   {program.get('Phone','')}\n")
    lines.append(f"Website: {program.get('Website','')}\n")
    lines.append(f"Benefit: {program.get('MaxBenefit','')}\n")
    lines.append(f"Status:  {program.get('StatusOrDeadline','')}\n")

    lines.append("\nYour home profile:\n")
    lines.append(f"- Senior: {profile.get('senior')}\n")
    lines.append(f"- Fixed income: {profile.get('fixed_income')}\n")
    lines.append(f"- Repairs needed: {needs}\n")

    lines.append("\nEligibility (database):\n")
    lines.append((program.get("EligibilitySummary","") or "(blank)").strip() + "\n")

    lines.append("\nIncome guidance (database):\n")
    lines.append((program.get("IncomeGuidance","") or "(blank)").strip() + "\n")

    lines.append("\nDocument checklist:\n")
    docs = (program.get("DocsChecklist","") or "").strip()
    if docs:
        lines.append(docs + "\n")
    else:
        lines.append("- Photo ID\n")
        lines.append("- Proof of ownership / purchase contract\n")
        lines.append("- Proof of income (SSA award letter, pension)\n")
        lines.append("- Contractor estimates for roof/heating/structural\n")
        lines.append("- Photos of problem areas\n")

    lines.append("\nCall script (questions):\n")
    lines.append("1) Are applications open now? Next intake date?\n")
    lines.append("2) Do roof/heating/structural repairs qualify? Any caps?\n")
    lines.append("3) Grant vs deferred loan vs loan? Any lien/forgiveness?\n")
    lines.append("4) Income limit (AMI %, household size)?\n")
    lines.append("5) Timeline and emergency-track options?\n")
    return "".join(lines)

def save_checklist(program: Dict[str, str], profile: Dict) -> Tuple[str, Optional[str]]:
    ensure_dir(CHECKLIST_DIR)
    pid = (program.get("ProgramId", "") or "program").strip() or "program"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_path = os.path.join(CHECKLIST_DIR, f"Checklist_{pid}_{stamp}.txt")
    pdf_path = os.path.join(CHECKLIST_DIR, f"Checklist_{pid}_{stamp}.pdf")

    text = checklist_text(program, profile)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    pdf_out = None
    if HAS_REPORTLAB:
        c = pdf_canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        x, y = 50, height - 50
        c.setFont("Helvetica", 10)
        for line in text.splitlines():
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 50
            c.drawString(x, y, line[:120])
            y -= 14
        c.save()
        pdf_out = pdf_path

    return txt_path, pdf_out

# =============================
# APP
# =============================
class SyrHousingApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SyrHousing – Senior Housing Grant Agent")
        try:
            self.root.state("zoomed")
        except Exception:
            self.root.geometry("1500x900")
        self.root.minsize(1200, 800)

        self.APP_NAME = "SyrHousing Grant Agent"
        self.APP_VERSION = "1.0.0"
        self._build_menu()

        self.profile = load_home_profile()
        self.all_rows = load_csv(DATA_FILE)
        self.filtered_rows = list(self.all_rows)

        self.paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True)

        self.left_shell = ttk.Frame(self.paned, width=470)
        self.right_shell = ttk.Frame(self.paned)
        self.left_shell.pack_propagate(False)

        self.paned.add(self.left_shell, weight=0)
        self.paned.add(self.right_shell, weight=1)

        self._build_left_scrollable()
        self._build_right_tabs()

        self.root.after(150, self._set_initial_sash)
        self._refresh_table()

    # -----------------------------
    # MENU BAR + ABOUT
    # -----------------------------
    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Run Scan Now", command=self.run_scan)
        file_menu.add_command(label="Open Latest Daily Scan Report", command=self.open_latest_report)
        file_menu.add_separator()
        file_menu.add_command(label="Open Reports Folder", command=self.open_reports_folder)
        file_menu.add_command(label="Open Checklists Folder", command=self.open_checklists_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Reload CSV from Disk", command=self.reload_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Preset: Core Columns", command=self.preset_core)
        tools_menu.add_command(label="Preset: All Columns", command=self.preset_all)
        tools_menu.add_command(label="Choose Columns…", command=self.choose_columns)
        tools_menu.add_separator()
        tools_menu.add_command(label="Generate Checklist (Selected Program)", command=self.generate_checklist_selected)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _show_about(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("About")
        win.geometry("520x320")
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win, padding=(14, 14))
        frm.pack(fill="both", expand=True)

        try:
            if os.path.exists(LOGO_PATH):
                img = tk.PhotoImage(file=LOGO_PATH)
                img = resize_photoimage(img, max_w=220, max_h=100)
                win._about_logo = img  # keep ref
                ttk.Label(frm, image=win._about_logo).pack(anchor="w")
        except Exception:
            pass

        ttk.Label(frm, text=self.APP_NAME, font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(10, 2))
        ttk.Label(frm, text=f"Version: {self.APP_VERSION}", font=("Segoe UI", 10)).pack(anchor="w")

        txt = (
            "Tracks Syracuse/Onondaga homeowner repair programs and helps prioritize\n"
            "options for seniors on fixed income.\n\n"
            "Includes: ranking, scan/report workflow, checklist generator, offline chatbot.\n"
        )
        ttk.Label(frm, text=txt, justify="left").pack(anchor="w", pady=(10, 12))

        ttk.Button(frm, text="Close", command=win.destroy).pack(anchor="e")

    # -----------------------------
    # Layout helpers
    # -----------------------------
    def _set_initial_sash(self) -> None:
        try:
            self.paned.sashpos(0, 470)
        except Exception:
            pass

    # -----------------------------
    # LEFT PANEL (SCROLLABLE)
    # -----------------------------
    def _build_left_scrollable(self) -> None:
        self.left_canvas = tk.Canvas(self.left_shell, highlightthickness=0)
        self.left_vsb = ttk.Scrollbar(self.left_shell, orient="vertical", command=self.left_canvas.yview)
        self.left_hsb = ttk.Scrollbar(self.left_shell, orient="horizontal", command=self.left_canvas.xview)
        self.left_canvas.configure(yscrollcommand=self.left_vsb.set, xscrollcommand=self.left_hsb.set)

        self.left_canvas.pack(side="left", fill="both", expand=True)
        self.left_vsb.pack(side="right", fill="y")
        self.left_hsb.pack(side="bottom", fill="x")

        self.left = ttk.Frame(self.left_canvas, padding=(12, 12))
        self.left_window = self.left_canvas.create_window((0, 0), window=self.left, anchor="nw")

        self.left.bind("<Configure>", lambda e: self._update_left_scrollregion())
        self.left_canvas.bind("<Configure>", self._sync_left_width)

        self.left_canvas.bind("<Enter>", lambda e: self.left_canvas.bind_all("<MouseWheel>", self._left_mousewheel))
        self.left_canvas.bind("<Leave>", lambda e: self.left_canvas.unbind_all("<MouseWheel>"))
        self.left_canvas.bind("<Enter>", lambda e: self.left_canvas.bind_all("<Shift-MouseWheel>", self._left_shift_mousewheel))
        self.left_canvas.bind("<Leave>", lambda e: self.left_canvas.unbind_all("<Shift-MouseWheel>"))

        header = ttk.Frame(self.left)
        header.pack(fill="x", pady=(0, 10))

        self.logo_img = None
        if os.path.exists(LOGO_PATH):
            try:
                img = tk.PhotoImage(file=LOGO_PATH)
                img = resize_photoimage(img, max_w=260, max_h=110)
                self.logo_img = img
                ttk.Label(header, image=self.logo_img).pack(anchor="w")
            except Exception as e:
                ttk.Label(header, text=f"(Logo load failed: {e})").pack(anchor="w")

        ttk.Label(header, text="SyrHousing Grant Agent", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(6, 0))
        ttk.Separator(self.left).pack(fill="x", pady=10)

        ttk.Label(self.left, text="My Home Profile (ranking inputs)", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.profile_lbl = ttk.Label(self.left, text=self._profile_text(), wraplength=420, justify="left")
        self.profile_lbl.pack(anchor="w", pady=(4, 6))
        ttk.Button(self.left, text="Edit My Home Profile…", command=self._edit_profile).pack(fill="x", pady=2)

        ttk.Separator(self.left).pack(fill="x", pady=10)

        ttk.Label(self.left, text="Repair Tag Filter", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.tag_var = tk.StringVar(value="ALL")

        all_tags: Set[str] = set()
        for r in self.all_rows:
            all_tags |= normalize_tags(r.get("RepairTags", ""))

        self.tag_combo = ttk.Combobox(self.left, textvariable=self.tag_var, values=["ALL"] + sorted(all_tags), state="readonly")
        self.tag_combo.pack(fill="x", pady=(4, 6))
        self.tag_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())

        row_btn = ttk.Frame(self.left)
        row_btn.pack(fill="x", pady=(0, 6))
        ttk.Button(row_btn, text="Apply Filter", command=self.apply_filter).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(row_btn, text="Clear", command=self.clear_filter).pack(side="left", expand=True, fill="x", padx=(4, 0))

        ttk.Separator(self.left).pack(fill="x", pady=10)

        ttk.Label(self.left, text="Scan & Reports", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Button(self.left, text="Run Scan Now (Updates + Report)", command=self.run_scan).pack(fill="x", pady=2)
        ttk.Button(self.left, text="Open Latest Daily Scan Report", command=self.open_latest_report).pack(fill="x", pady=2)
        ttk.Button(self.left, text="Open Reports Folder", command=self.open_reports_folder).pack(fill="x", pady=2)

        ttk.Separator(self.left).pack(fill="x", pady=10)

        ttk.Label(self.left, text="Columns", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Button(self.left, text="Preset: Core", command=self.preset_core).pack(fill="x", pady=2)
        ttk.Button(self.left, text="Preset: All Fields", command=self.preset_all).pack(fill="x", pady=2)
        ttk.Button(self.left, text="Choose Columns…", command=self.choose_columns).pack(fill="x", pady=2)

        ttk.Separator(self.left).pack(fill="x", pady=10)

        ttk.Button(self.left, text="Generate Checklist (Selected Program)", command=self.generate_checklist_selected).pack(fill="x", pady=2)
        ttk.Button(self.left, text="Open Checklists Folder", command=self.open_checklists_folder).pack(fill="x", pady=2)

        ttk.Separator(self.left).pack(fill="x", pady=10)
        ttk.Button(self.left, text="Reload CSV from Disk", command=self.reload_data).pack(fill="x", pady=2)

        self._update_left_scrollregion()

    def _update_left_scrollregion(self) -> None:
        self.left_canvas.update_idletasks()
        bbox = self.left_canvas.bbox("all")
        if bbox:
            self.left_canvas.configure(scrollregion=bbox)

    def _sync_left_width(self, event) -> None:
        self.left_canvas.itemconfigure(self.left_window, width=event.width)

    def _left_mousewheel(self, event) -> None:
        self.left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _left_shift_mousewheel(self, event) -> None:
        self.left_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _profile_text(self) -> str:
        needs = ", ".join(self.profile.get("repair_needs", []))
        return f"City: {self.profile.get('city')} | County: {self.profile.get('county')}\nSenior: {self.profile.get('senior')} | Fixed income: {self.profile.get('fixed_income')}\nRepairs: {needs}"

    def _edit_profile(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Edit My Home Profile")
        win.geometry("520x380")
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win, padding=(12, 12))
        frm.pack(fill="both", expand=True)

        city_var = tk.StringVar(value=str(self.profile.get("city", "Syracuse")))
        county_var = tk.StringVar(value=str(self.profile.get("county", "Onondaga")))
        senior_var = tk.BooleanVar(value=bool(self.profile.get("senior", True)))
        fixed_var = tk.BooleanVar(value=bool(self.profile.get("fixed_income", True)))
        repairs_var = tk.StringVar(value=";".join(self.profile.get("repair_needs", ["heating", "roof", "structural"])))

        ttk.Label(frm, text="City").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=city_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="County").grid(row=1, column=0, sticky="w")
        ttk.Entry(frm, textvariable=county_var).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Checkbutton(frm, text="Senior (60+/62+)", variable=senior_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Checkbutton(frm, text="Fixed income", variable=fixed_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(frm, text="Repair needs (semicolon separated)").grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 2))
        ttk.Entry(frm, textvariable=repairs_var).grid(row=5, column=0, columnspan=2, sticky="ew")

        frm.columnconfigure(1, weight=1)

        def save():
            self.profile = {
                "city": city_var.get().strip() or "Syracuse",
                "county": county_var.get().strip() or "Onondaga",
                "senior": bool(senior_var.get()),
                "fixed_income": bool(fixed_var.get()),
                "repair_needs": [r.strip().lower() for r in repairs_var.get().split(";") if r.strip()]
            }
            save_home_profile(self.profile)
            self.profile_lbl.configure(text=self._profile_text())
            self._refresh_table()
            win.destroy()

        btn = ttk.Frame(win, padding=(12, 0, 12, 12))
        btn.pack(fill="x")
        ttk.Button(btn, text="Save", command=save).pack(side="right", padx=6)
        ttk.Button(btn, text="Cancel", command=win.destroy).pack(side="right")

    # -----------------------------
    # RIGHT SIDE: NOTEBOOK TABS
    # -----------------------------
    def _build_right_tabs(self) -> None:
        self.nb = ttk.Notebook(self.right_shell)
        self.nb.pack(fill="both", expand=True)

        self.tab_programs = ttk.Frame(self.nb)
        self.tab_chat = ttk.Frame(self.nb)

        self.nb.add(self.tab_programs, text="Programs")
        self.nb.add(self.tab_chat, text="Chatbot")

        self._build_programs_tab(self.tab_programs)
        self._build_chat_tab(self.tab_chat)

    def _build_programs_tab(self, parent) -> None:
        self.right_paned = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        self.right_paned.pack(fill="both", expand=True)

        self.table_frame = ttk.Frame(self.right_paned)
        self.detail_frame = ttk.Frame(self.right_paned)

        self.right_paned.add(self.table_frame, weight=3)
        self.right_paned.add(self.detail_frame, weight=2)

        self._build_table(self.table_frame)
        self._build_detail(self.detail_frame)

    def _build_table(self, parent) -> None:
        container = ttk.Frame(parent, padding=(10, 10))
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(container, columns=FIELDS, show="headings")
        self.vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")

        for c in FIELDS:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=200, anchor="w", stretch=False)

        self.tree["displaycolumns"] = CORE_COLUMNS
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Shift-MouseWheel>", lambda e: self.tree.xview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _build_detail(self, parent) -> None:
        frm = ttk.Frame(parent, padding=(10, 10))
        frm.pack(fill="both", expand=True)
        frm.rowconfigure(1, weight=1)
        frm.columnconfigure(0, weight=1)

        ttk.Label(frm, text="Program Details + Ranking Explanation", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")

        self.detail_text = tk.Text(frm, wrap="word", height=12)
        self.detail_vsb = ttk.Scrollbar(frm, orient="vertical", command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=self.detail_vsb.set)

        self.detail_text.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self.detail_vsb.grid(row=1, column=1, sticky="ns", pady=(6, 0))

        self._set_detail("Select a program to see details and ranking logic.\n")

    def _set_detail(self, text: str) -> None:
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", text)
        self.detail_text.configure(state="disabled")

    def _selected_program(self) -> Optional[Dict[str, str]]:
        sel = self.tree.selection()
        if not sel:
            return None
        item = sel[0]
        values = self.tree.item(item, "values")
        if not values:
            return None

        pid = values[0] if len(values) > 0 else ""
        if pid:
            for r in self.filtered_rows:
                if r.get("ProgramId", "") == pid:
                    return r

        name = values[1] if len(values) > 1 else ""
        for r in self.filtered_rows:
            if r.get("Name", "") == name:
                return r
        return None

    def _on_select(self, _evt=None) -> None:
        program = self._selected_program()
        if not program:
            return

        score, why = compute_rank(program, self.profile)
        program["PriorityRank"] = str(score)

        lines: List[str] = []
        lines.append(f"NAME: {program.get('Name','')}\n")
        lines.append(f"SCORE: {score}/100\n")
        lines.append(f"CATEGORY: {program.get('MenuCategory','')}\n")
        lines.append(f"TYPE: {program.get('ProgramType','')}\n")
        lines.append(f"BENEFIT: {program.get('MaxBenefit','')}\n")
        lines.append(f"STATUS: {program.get('StatusOrDeadline','')}\n")
        lines.append(f"AGENCY: {program.get('Agency','')}\n")
        lines.append(f"PHONE: {program.get('Phone','')}\n")
        lines.append(f"EMAIL: {program.get('Email','')}\n")
        lines.append(f"WEBSITE: {program.get('Website','')}\n")

        lines.append("\n--- Eligibility Summary ---\n")
        lines.append((program.get("EligibilitySummary", "") or "(blank)").strip() + "\n")

        lines.append("\n--- Income Guidance ---\n")
        lines.append((program.get("IncomeGuidance", "") or "(blank)").strip() + "\n")

        lines.append("\n--- Docs Checklist ---\n")
        lines.append((program.get("DocsChecklist", "") or "(blank)").strip() + "\n")

        lines.append("\n--- Why this ranked ---\n")
        lines.extend([f"- {x}\n" for x in why])

        self._set_detail("".join(lines))

    # -----------------------------
    # CHAT TAB
    # -----------------------------
    def _build_chat_tab(self, parent) -> None:
        outer = ttk.Frame(parent, padding=(10, 10))
        outer.pack(fill="both", expand=True)
        outer.rowconfigure(1, weight=1)
        outer.columnconfigure(0, weight=1)

        ttk.Label(outer, text="Chatbot (offline mode) – uses your CSV + latest scan", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")

        self.chat_log = tk.Text(outer, wrap="word", height=18)
        self.chat_log.grid(row=1, column=0, sticky="nsew", pady=(8, 8))
        chat_vsb = ttk.Scrollbar(outer, orient="vertical", command=self.chat_log.yview)
        self.chat_log.configure(yscrollcommand=chat_vsb.set)
        chat_vsb.grid(row=1, column=1, sticky="ns", pady=(8, 8))

        entry_row = ttk.Frame(outer)
        entry_row.grid(row=2, column=0, columnspan=2, sticky="ew")
        entry_row.columnconfigure(0, weight=1)

        self.chat_q = tk.StringVar()
        self.chat_entry = ttk.Entry(entry_row, textvariable=self.chat_q)
        self.chat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(entry_row, text="Ask", command=self._chat_ask).grid(row=0, column=1)

        self.chat_entry.bind("<Return>", lambda e: self._chat_ask())
        self._chat_append("Assistant", "Ask about roof/heating/structural programs, lead, accessibility, weatherization, or how to apply.")

    def _chat_append(self, who: str, text: str) -> None:
        self.chat_log.configure(state="normal")
        self.chat_log.insert("end", f"{who}: {text}\n\n")
        self.chat_log.configure(state="disabled")
        self.chat_log.see("end")

    def _chat_ask(self) -> None:
        q = self.chat_q.get().strip()
        if not q:
            return
        self.chat_q.set("")
        self._chat_append("You", q)
        ans = chatbot_answer(q, self.filtered_rows, self.profile)
        self._chat_append("Assistant", ans)

    # -----------------------------
    # FILTER + REFRESH
    # -----------------------------
    def _refresh_table(self) -> None:
        scored: List[Dict[str, str]] = []
        for r in self.filtered_rows:
            s, _ = compute_rank(r, self.profile)
            r["PriorityRank"] = str(s)
            scored.append(r)

        scored.sort(key=lambda x: parse_priority_rank(x.get("PriorityRank", "")), reverse=True)

        self.tree.delete(*self.tree.get_children())
        for r in scored:
            self.tree.insert("", "end", values=[r.get(f, "") for f in FIELDS])

        kids = self.tree.get_children()
        if kids:
            self.tree.selection_set(kids[0])
            self.tree.see(kids[0])
            self._on_select()

    def apply_filter(self) -> None:
        tag = (self.tag_var.get() or "ALL").strip().lower()
        if tag == "all":
            self.filtered_rows = list(self.all_rows)
        else:
            self.filtered_rows = [r for r in self.all_rows if tag in normalize_tags(r.get("RepairTags", ""))]
        self._refresh_table()

    def clear_filter(self) -> None:
        self.tag_var.set("ALL")
        self.filtered_rows = list(self.all_rows)
        self._refresh_table()

    # -----------------------------
    # SCAN / REPORTS
    # -----------------------------
    def run_scan(self) -> None:
        if not os.path.exists(SCAN_PS1):
            messagebox.showerror("Scan", f"Missing:\n{SCAN_PS1}")
            return
        try:
            subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", SCAN_PS1])
            messagebox.showinfo("Scan", "Scan started.\nWhen finished, open the latest report.")
        except Exception as e:
            messagebox.showerror("Scan failed", str(e))

    def open_reports_folder(self) -> None:
        ensure_dir(REPORT_DIR)
        safe_open(REPORT_DIR)

    def open_latest_report(self) -> None:
        p = latest_report_path(REPORT_DIR)
        if not p:
            messagebox.showinfo("Reports", "No report found yet. Run a scan first.")
            return
        safe_open(p)

    # -----------------------------
    # COLUMNS
    # -----------------------------
    def preset_core(self) -> None:
        self.tree["displaycolumns"] = CORE_COLUMNS

    def preset_all(self) -> None:
        self.tree["displaycolumns"] = FIELDS

    def choose_columns(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Choose Columns")
        win.geometry("520x650")
        win.transient(self.root)
        win.grab_set()

        vars_by_col: Dict[str, tk.BooleanVar] = {}
        box = ttk.Frame(win, padding=(10, 10))
        box.pack(fill="both", expand=True)

        canvas = tk.Canvas(box, highlightthickness=0)
        sb = ttk.Scrollbar(box, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)

        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        current = set(self.tree["displaycolumns"])
        for c in FIELDS:
            v = tk.BooleanVar(value=(c in current))
            vars_by_col[c] = v
            ttk.Checkbutton(inner, text=c, variable=v).pack(anchor="w", pady=2)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        bottom = ttk.Frame(win, padding=(10, 10))
        bottom.pack(fill="x")

        def apply():
            cols = [c for c in FIELDS if vars_by_col[c].get()]
            if "Name" not in cols:
                cols.insert(0, "Name")
            self.tree["displaycolumns"] = cols
            win.destroy()

        ttk.Button(bottom, text="Apply", command=apply).pack(side="right", padx=6)
        ttk.Button(bottom, text="Cancel", command=win.destroy).pack(side="right")

    # -----------------------------
    # CHECKLISTS
    # -----------------------------
    def generate_checklist_selected(self) -> None:
        program = self._selected_program()
        if not program:
            messagebox.showinfo("Checklist", "Select a program first.")
            return
        txt_path, pdf_path = save_checklist(program, self.profile)
        msg = f"Saved:\n{txt_path}"
        if pdf_path:
            msg += f"\n{pdf_path}"
        else:
            msg += "\n(PDF not created: install reportlab)"
        messagebox.showinfo("Checklist created", msg)

    def open_checklists_folder(self) -> None:
        ensure_dir(CHECKLIST_DIR)
        safe_open(CHECKLIST_DIR)

    # -----------------------------
    # RELOAD
    # -----------------------------
    def reload_data(self) -> None:
        self.all_rows = load_csv(DATA_FILE)
        self.filtered_rows = list(self.all_rows)

        all_tags: Set[str] = set()
        for r in self.all_rows:
            all_tags |= normalize_tags(r.get("RepairTags", ""))

        self.tag_combo.configure(values=["ALL"] + sorted(all_tags))
        self._refresh_table()


def main() -> None:
    root = tk.Tk()
    SyrHousingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
