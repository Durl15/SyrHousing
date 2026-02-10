# SetupSyrHousing.ps1
# Run in PowerShell to create the Syracuse Senior Housing Grant System

$ErrorActionPreference = "Stop"

$BasePath = "C:\SyrHousing"
$VenvPath = Join-Path $BasePath ".venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

Write-Host "=== Syracuse Senior Housing Grant System Setup ==="

# -----------------------------
# 1) Create Directory Structure
# -----------------------------
Write-Host "Creating directories at $BasePath ..."
New-Item -ItemType Directory -Force -Path $BasePath | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BasePath "Agents") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BasePath "Data") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BasePath "Logs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BasePath "Reports") | Out-Null

# -----------------------------
# 2) Create Agent Prompts
# -----------------------------
Write-Host "Writing agent prompts ..."

$GrantHunterPrompt = @"
ACT AS: The Syracuse Senior Housing Grant Specialist

MISSION:
Your goal is to find, verify, and organize home improvement funding for a senior citizen (62+) on a fixed income buying an older home in Syracuse/Onondaga County, NY.

OPERATIONAL MENU:
When I say 'Start', present this menu:
[1] URGENT SAFETY (Roofs, Furnaces, Electrical)
[2] HEALTH HAZARDS (Lead Paint, Asbestos, Mold)
[3] AGING IN PLACE (Ramps, Grab Bars, Lifts)
[4] ENERGY & BILLS (Insulation, Windows, Solar)
[5] HISTORIC RESTORATION (Facades, Porches)
[6] BUYING HELP (Down Payment, Closing Costs)
[7] GENERATE CHECKLIST for a specific program

KNOWLEDGE BASE (PRIORITIZE THESE):
- SHARP (City of Syracuse): Grants for exterior / code-related repairs (status may be seasonal).
- RESTORE (NYS): Emergency repairs for seniors 60+ (roof/heat/safety).
- Lead Hazard Control: Lead paint hazard reduction (older homes; windows/doors/siding often relevant).
- USDA 504: Rural repair grants (generally outside city limits; include as “check eligibility”).
- EmPower+ / Weatherization: Free energy upgrades.
- Home HeadQuarters loan/grant mixes: Urgent Care/Flex-type funds for major safety repairs.

OUTPUT RULES:
- Always list ELIGIBILITY (Income limits, Age, owner-occupied).
- Always list DEADLINES / STATUS (Open/Closed/Seasonal/Call to confirm).
- Always provide a PHONE NUMBER and WEBSITE when available.
- Compare options: If Program A is a grant and Program B is a loan, highlight Program A.
"@

$EvaluatorPrompt = @"
ACT AS: The Construction Bid & Grant Proposal Evaluator

MISSION:
Compare contractor quotes or grant application drafts to ensure the user (a senior on fixed income) is getting fair value and meeting requirements.

INPUT: User will paste:
A. A Grant Requirement list (e.g., 'Must fix roof to Energy Star standards')
B. A Contractor Quote (e.g., 'Roof replacement: $12,000')

ANALYSIS STEPS:
1) Compliance Check: Does the quote meet the grant's technical requirements?
2) Cost Analysis: Flag if >15% above expected range (Syracuse/Onondaga context).
3) Red Flags: Missing insurance, warranty, timeline, scope details, permit responsibility.
4) Senior Protection: Scam signals (large upfront deposit, vague terms, pressure tactics).

OUTPUT:
- Risk Score (1-10)
- Questions to ask the contractor
- Recommendation: Proceed / Negotiate / Reject
"@

$GrantHunterPrompt | Out-File -FilePath (Join-Path $BasePath "Agents\Grant_Hunter_Prompt.txt") -Encoding UTF8
$EvaluatorPrompt   | Out-File -FilePath (Join-Path $BasePath "Agents\Evaluator_Prompt.txt") -Encoding UTF8

# -----------------------------
# 3) Create Pre-Loaded Grant DB (CSV)
#    Categories tuned for repairs: roof/heating/structural/windows/doors/exterior etc.
# -----------------------------
Write-Host "Writing starter grants database ..."

$CsvContent = @"
Name,MenuCategory,RepairTags,Amount,Agency,StatusOrDeadline,Phone,Link,Notes
HHQ Urgent Care (Syracuse),URGENT SAFETY,""roof;heating;electrical;structural;plumbing;stairs"",Up to 20000,""Home HeadQuarters (HHQ)"",""Rolling - Call to confirm"",""(315) 474-1939"",""https://www.homehq.org/homeowner-loans-grants"",""Best fit for emergency roof/heating/safety issues in Syracuse; income limits apply.""
SHARP Grant (Syracuse),URGENT SAFETY,""exterior;roof;doors;windows;steps;railings"",Up to 3000,""Home HeadQuarters (HHQ)"",""Seasonal - often closed/reopens"",""(315) 474-1939"",""https://www.homehq.org/homeowner-loans-grants"",""Small emergency repairs; Syracuse owner-occupied; typically <80% AMI.""
NYS RESTORE (Senior 60+),URGENT SAFETY,""roof;heating;structural;electrical;plumbing;accessibility"",10000-20000,""NYS HCR (via local administrators)"",""Rolling / Funding cycles"",""Call HHQ / local administrator"",""https://hcr.ny.gov/restore-program"",""Emergency repairs for seniors; health/safety/livability.""
Lead Hazard Control / Healthy Homes,HEALTH HAZARDS,""lead;windows;doors;siding;paint"",Varies,""City/County Health Programs"",""Varies - Call to confirm"",""Call City/County Health"",""https://www.syr.gov/"",""Older homes: lead paint hazard reduction; may cover windows/doors/paint stabilization.""
Access to Home (NYS),AGING IN PLACE,""ramps;grab bars;bathroom;mobility"",Varies,""NYS HCR (local providers)"",""Rolling / Funding cycles"",""Call HHQ / AccessCNY"",""https://hcr.ny.gov/access-home-program"",""Accessibility modifications; disability/mobility limitations often required.""
AccessCNY E-Mods,AGING IN PLACE,""ramps;grab bars;bathroom;stairs"",Varies,""AccessCNY"",""Rolling - Call to confirm"",""(315) 455-7591"",""https://www.accesscny.org/services/emods/"",""Accessibility modifications; may coordinate with Access to Home.""
Weatherization (PEACE Inc.),ENERGY & BILLS,""insulation;air sealing;heating;windows"",100% Covered (if eligible),""PEACE Inc."",""Rolling"",""Call PEACE Inc."",""https://www.peace-caa.org/programs/energyhousing/"",""Energy upgrades; can reduce heating costs; eligibility applies.""
NYSERDA EmPower+,ENERGY & BILLS,""insulation;air sealing;appliances;drafts"",100% Covered (if eligible),""NYSERDA"",""Rolling"",""Call NYSERDA / provider"",""https://www.nyserda.ny.gov/All-Programs/EmPower-New-York"",""Energy efficiency assistance; may overlap with weatherization.""
Historic Facade / Exterior Restoration,HISTORIC RESTORATION,""facade;porch;exterior;windows"",Varies,""Varies by district/program"",""Varies - Check local programs"",""Call City planning / preservation"",""https://www.syr.gov/"",""Only applies if property is historic/district eligible; verify.""
Down Payment / Homebuyer Assistance,BUYING HELP,""down payment;closing costs"",Varies,""City/County/State programs"",""Varies - Check"",""Call City housing office"",""https://www.syr.gov/"",""Homebuyer assistance may exist; verify current availability.""
"@

$CsvContent | Out-File -FilePath (Join-Path $BasePath "Data\grants_db.csv") -Encoding UTF8

# -----------------------------
# 4) Create Python GUI App (menu-driven + chatbot)
# -----------------------------
Write-Host "Writing Python application (menu-driven GUI + chatbot) ..."

$PythonCode = @"
import os
import csv
import re
import json
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = r'C:\SyrHousing'
DATA_FILE = os.path.join(BASE_DIR, 'Data', 'grants_db.csv')
LOG_FILE = os.path.join(BASE_DIR, 'Logs', 'activity_log.txt')
PROMPT_GRANT_HUNTER = os.path.join(BASE_DIR, 'Agents', 'Grant_Hunter_Prompt.txt')
PROMPT_EVALUATOR = os.path.join(BASE_DIR, 'Agents', 'Evaluator_Prompt.txt')

MENU_CATEGORIES = [
    'URGENT SAFETY',
    'HEALTH HAZARDS',
    'AGING IN PLACE',
    'ENERGY & BILLS',
    'HISTORIC RESTORATION',
    'BUYING HELP',
    'GENERATE CHECKLIST'
]

REPAIR_TAGS = [
    'roof',
    'heating',
    'structural',
    'windows',
    'doors',
    'exterior',
    'electrical',
    'plumbing',
    'stairs',
    'lead',
    'mold',
    'insulation',
    'accessibility'
]


def log_event(msg: str) -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f'[{ts}] {msg}\n')


def load_text(path: str) -> str:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''


def load_grants() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def parse_tags(tag_str: str) -> set:
    if not tag_str:
        return set()
    parts = [p.strip().lower() for p in tag_str.split(';')]
    return set([p for p in parts if p])


def open_link(url: str) -> None:
    if url:
        webbrowser.open(url)


def normalize(s: str) -> str:
    return re.sub(r'\\s+', ' ', (s or '').strip().lower())


def chatbot_answer(question: str, grants: list[dict], grant_prompt: str) -> str:
    q = normalize(question)

    # quick routing
    if not q:
        return "Ask a question about a grant, eligibility, repair types (roof/heating), or what to apply for first."

    if 'start' == q:
        return (
            "Operational Menu:\\n"
            "[1] URGENT SAFETY (Roofs, Furnaces, Electrical)\\n"
            "[2] HEALTH HAZARDS (Lead Paint, Asbestos, Mold)\\n"
            "[3] AGING IN PLACE (Ramps, Grab Bars, Lifts)\\n"
            "[4] ENERGY & BILLS (Insulation, Windows, Solar)\\n"
            "[5] HISTORIC RESTORATION (Facades, Porches)\\n"
            "[6] BUYING HELP (Down Payment, Closing Costs)\\n"
            "[7] GENERATE CHECKLIST for a specific program\\n"
            "\\nTell me: 'Show urgent safety' or 'roof programs' or paste a program name for a checklist."
        )

    # common prioritization for your stated needs
    if any(k in q for k in ['roof', 'leak', 'furnace', 'heat', 'heating', 'structural']):
        # pick best matches by tags
        hits = []
        for g in grants:
            tags = parse_tags(g.get('RepairTags', ''))
            if any(k in q for k in ['roof', 'leak']) and 'roof' in tags:
                hits.append(g)
            elif any(k in q for k in ['furnace', 'heat', 'heating']) and 'heating' in tags:
                hits.append(g)
            elif 'structural' in q and 'structural' in tags:
                hits.append(g)

        if hits:
            lines = ["Top matches for your issue:"]
            for g in hits[:6]:
                lines.append(f"- {g['Name']} | Amount: {g['Amount']} | Status: {g['StatusOrDeadline']} | Phone: {g['Phone']}")
                lines.append(f"  Link: {g['Link']}")
            lines.append("\\nPriority order (typical): HHQ Urgent Care -> NYS RESTORE -> Weatherization/EmPower+ (if energy/heating). Call to confirm current openings.")
            return "\\n".join(lines)

    # search by program name
    for g in grants:
        if normalize(g.get('Name', '')) in q:
            return checklist_for_program(g)

    # keyword search over fields
    scored = []
    for g in grants:
        blob = " ".join([
            g.get('Name',''),
            g.get('MenuCategory',''),
            g.get('RepairTags',''),
            g.get('Notes',''),
            g.get('Agency','')
        ])
        blob_n = normalize(blob)
        score = 0
        for token in q.split(' '):
            if token and token in blob_n:
                score += 1
        if score > 0:
            scored.append((score, g))

    scored.sort(key=lambda x: x[0], reverse=True)

    if scored:
        lines = ["I found these relevant programs:"]
        for score, g in scored[:6]:
            lines.append(f"- {g['Name']} | Category: {g['MenuCategory']} | Amount: {g['Amount']} | Phone: {g['Phone']}")
            lines.append(f"  Link: {g['Link']}")
        lines.append("\\nIf you tell me your exact repair need (roof/heating/structural/windows/doors), I can narrow this down further.")
        return "\\n".join(lines)

    # fallback: show prompt excerpt guidance
    prompt_hint = grant_prompt.strip().splitlines()
    hint = "\\n".join(prompt_hint[:18]) if prompt_hint else ""
    return (
        "I couldn’t find a direct match in the local grant database.\\n"
        "Try asking: 'roof programs', 'heating help', 'urgent safety', 'lead paint', or paste a program name.\\n\\n"
        f"Grant Hunter Guidance (excerpt):\\n{hint}"
    )


def checklist_for_program(g: dict) -> str:
    return (
        f"PROGRAM CHECKLIST: {g.get('Name','')}\\n"
        f"Admin/Agency: {g.get('Agency','')}\\n"
        f"Menu Category: {g.get('MenuCategory','')}\\n"
        f"Repair Tags: {g.get('RepairTags','')}\\n"
        f"Amount: {g.get('Amount','')}\\n"
        f"Status/Deadline: {g.get('StatusOrDeadline','')}\\n"
        f"Phone: {g.get('Phone','')}\\n"
        f"Website: {g.get('Link','')}\\n\\n"
        "Documents to gather (typical):\\n"
        "- Proof of ownership + primary residence\\n"
        "- ID / age verification (senior)\\n"
        "- Income documentation (SSA letter, pension, etc.)\\n"
        "- Recent utility bills (if energy-related)\\n"
        "- Photos of damage + any code notices\\n"
        "- Contractor estimates (if required)\\n\\n"
        "Next action: Call the listed number and ask: 'Is funding open today and what is the current application process?'"
    )


class SyrHousingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SyrHousing: Senior Grant System (Menu + Chatbot)")
        self.root.geometry("1100x720")

        self.grants = load_grants()
        self.prompt_grant_hunter = load_text(PROMPT_GRANT_HUNTER)
        self.prompt_evaluator = load_text(PROMPT_EVALUATOR)

        # layout: left menu + main area
        self.main = tk.Frame(root)
        self.main.pack(fill="both", expand=True)

        self.left = tk.Frame(self.main, width=260, padx=10, pady=10)
        self.left.pack(side="left", fill="y")

        self.right = tk.Frame(self.main, padx=10, pady=10)
        self.right.pack(side="right", fill="both", expand=True)

        # left header
        tk.Label(self.left, text="Operational Menu", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 6))

        # menu buttons
        for cat in MENU_CATEGORIES:
            ttk.Button(self.left, text=cat, command=lambda c=cat: self.apply_menu_filter(c)).pack(fill="x", pady=2)

        ttk.Separator(self.left).pack(fill="x", pady=10)

        tk.Label(self.left, text="Repair Category Filter", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

        self.repair_var = tk.StringVar(value="(all)")
        repair_options = ["(all)"] + REPAIR_TAGS
        self.repair_combo = ttk.Combobox(self.left, values=repair_options, textvariable=self.repair_var, state="readonly")
        self.repair_combo.pack(fill="x")
        self.repair_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        ttk.Button(self.left, text="Clear Filters", command=self.clear_filters).pack(fill="x", pady=(8, 2))

        ttk.Separator(self.left).pack(fill="x", pady=10)

        ttk.Button(self.left, text="Generate Report", command=self.generate_report).pack(fill="x", pady=2)
        ttk.Button(self.left, text="Open Data Folder", command=self.open_data_folder).pack(fill="x", pady=2)

        # right: tabs
        self.tabs = ttk.Notebook(self.right)
        self.tabs.pack(fill="both", expand=True)

        self.tab_grants = tk.Frame(self.tabs)
        self.tab_chat = tk.Frame(self.tabs)

        self.tabs.add(self.tab_grants, text="Grants (Menu-Driven)")
        self.tabs.add(self.tab_chat, text="Chatbot")

        # --- Grants Tab UI ---
        self.filters = {
            "menu": None,       # one of MENU_CATEGORIES or None
            "repair": "(all)"   # one of REPAIR_TAGS or "(all)"
        }

        topbar = tk.Frame(self.tab_grants)
        topbar.pack(fill="x", pady=(0, 8))

        ttk.Button(topbar, text="View All Grants", command=self.view_all).pack(side="left", padx=4)
        ttk.Button(topbar, text="Check for Updates (placeholder)", command=self.check_updates_placeholder).pack(side="left", padx=4)
        ttk.Button(topbar, text="Program Checklist (selected)", command=self.show_selected_checklist).pack(side="left", padx=4)

        self.lbl_status = tk.Label(self.tab_grants, text="System Ready.", fg="green")
        self.lbl_status.pack(anchor="w", pady=(0, 8))

        cols = ("Name", "MenuCategory", "RepairTags", "Amount", "StatusOrDeadline", "Agency", "Phone", "Link")
        self.tree = ttk.Treeview(self.tab_grants, columns=cols, show="headings", height=18)

        headings = {
            "Name": "Program Name",
            "MenuCategory": "Menu Category",
            "RepairTags": "Repair Tags",
            "Amount": "Amount",
            "StatusOrDeadline": "Status/Deadline",
            "Agency": "Agency",
            "Phone": "Phone",
            "Link": "Website"
        }
        for c in cols:
            self.tree.heading(c, text=headings.get(c, c))

        self.tree.column("Name", width=240)
        self.tree.column("MenuCategory", width=140)
        self.tree.column("RepairTags", width=210)
        self.tree.column("Amount", width=110, anchor="center")
        self.tree.column("StatusOrDeadline", width=160)
        self.tree.column("Agency", width=170)
        self.tree.column("Phone", width=120)
        self.tree.column("Link", width=260)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.open_selected_link)

        # --- Chatbot Tab UI ---
        tk.Label(self.tab_chat, text="Grant Chatbot (Local)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 6))
        tk.Label(
            self.tab_chat,
            text="Ask about roof/heating/structural programs, 'Start' for the menu, or paste a program name.",
            fg="gray"
        ).pack(anchor="w", pady=(0, 8))

        self.chat_history = tk.Text(self.tab_chat, height=22, wrap="word")
        self.chat_history.pack(fill="both", expand=True, pady=(0, 8))
        self.chat_history.config(state="disabled")

        chat_entry_frame = tk.Frame(self.tab_chat)
        chat_entry_frame.pack(fill="x")

        self.chat_entry = tk.Entry(chat_entry_frame)
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.chat_entry.bind("<Return>", lambda e: self.chat_send())

        ttk.Button(chat_entry_frame, text="Send", command=self.chat_send).pack(side="right")

        # initial load
        self.view_all()

    def write_chat(self, who: str, text: str):
        self.chat_history.config(state="normal")
        self.chat_history.insert("end", f"{who}: {text}\n\n")
        self.chat_history.see("end")
        self.chat_history.config(state="disabled")

    def chat_send(self):
        q = self.chat_entry.get().strip()
        if not q:
            return
        self.chat_entry.delete(0, "end")
        self.write_chat("You", q)
        ans = chatbot_answer(q, self.grants, self.prompt_grant_hunter)
        self.write_chat("Agent", ans)
        log_event(f"CHAT Q: {q}")

    def open_data_folder(self):
        os.startfile(os.path.join(BASE_DIR, "Data"))

    def view_all(self):
        self.filters["menu"] = None
        self.repair_var.set("(all)")
        self.filters["repair"] = "(all)"
        self.apply_filters()
        self.lbl_status.config(text="Showing all grants.", fg="green")
        log_event("View all grants")

    def apply_menu_filter(self, menu_category: str):
        self.filters["menu"] = menu_category if menu_category != "GENERATE CHECKLIST" else None
        self.apply_filters()

        if menu_category == "GENERATE CHECKLIST":
            self.show_selected_checklist()
            return

        self.lbl_status.config(text=f"Filtered by menu: {menu_category}", fg="blue")
        log_event(f"Filter menu: {menu_category}")

    def apply_filters(self):
        repair = self.repair_var.get()
        self.filters["repair"] = repair

        # clear
        for i in self.tree.get_children():
            self.tree.delete(i)

        # filter dataset
        filtered = []
        for g in self.grants:
            if self.filters["menu"]:
                if (g.get("MenuCategory") or "").strip() != self.filters["menu"]:
                    continue

            if repair and repair != "(all)":
                tags = parse_tags(g.get("RepairTags", ""))
                if repair.lower() not in tags:
                    continue

            filtered.append(g)

        for g in filtered:
            self.tree.insert("", "end", values=(
                g.get("Name",""),
                g.get("MenuCategory",""),
                g.get("RepairTags",""),
                g.get("Amount",""),
                g.get("StatusOrDeadline",""),
                g.get("Agency",""),
                g.get("Phone",""),
                g.get("Link","")
            ))

        self.lbl_status.config(text=f"Results: {len(filtered)} programs.", fg="green")

    def clear_filters(self):
        self.filters["menu"] = None
        self.repair_var.set("(all)")
        self.filters["repair"] = "(all)"
        self.apply_filters()
        self.lbl_status.config(text="Filters cleared.", fg="green")
        log_event("Clear filters")

    def get_selected_program(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0]).get("values", [])
        if not vals:
            return None
        name = vals[0]
        for g in self.grants:
            if g.get("Name","") == name:
                return g
        return None

    def show_selected_checklist(self):
        g = self.get_selected_program()
        if not g:
            messagebox.showwarning("Checklist", "Select a program first (click a row) then press 'Program Checklist'.")
            return
        text = checklist_for_program(g)
        messagebox.showinfo("Program Checklist", text)
        log_event(f"Checklist generated: {g.get('Name','')}")

    def open_selected_link(self, event=None):
        g = self.get_selected_program()
        if not g:
            return
        url = g.get("Link","")
        if url:
            open_link(url)
            log_event(f"Open link: {g.get('Name','')}")

    def check_updates_placeholder(self):
        # This is a placeholder. Later we can add web scraping using requests/bs4.
        # For now, it logs the timestamp and tells the user to call to confirm openings.
        ts = datetime.now().strftime("%H:%M")
        self.lbl_status.config(text=f"Checked at {ts}: Use 'Phone' to confirm open/closed status.", fg="blue")
        messagebox.showinfo("Check Updates", "This build uses a local database. Next upgrade: add website scanning + daily notifications.")
        log_event("Check updates placeholder")

    def generate_report(self):
        report_path = os.path.join(BASE_DIR, "Reports", f"Grant_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        lines = []
        lines.append("SYRACUSE SENIOR HOUSING GRANT REPORT")
        lines.append("===================================")
        lines.append(f"Generated: {datetime.now()}")
        lines.append("")
        lines.append("Filters:")
        lines.append(f"- Menu: {self.filters['menu'] or '(none)'}")
        lines.append(f"- Repair: {self.filters['repair']}")
        lines.append("")

        # gather visible rows
        lines.append("Programs:")
        for child in self.tree.get_children():
            vals = self.tree.item(child).get("values", [])
            if not vals:
                continue
            lines.append(f"- {vals[0]} | Amount: {vals[3]} | Status: {vals[4]} | Phone: {vals[6]}")
            lines.append(f"  Tags: {vals[2]}")
            lines.append(f"  Website: {vals[7]}")
        lines.append("")
        lines.append("Recommended next step:")
        lines.append("- For roof/heating/structural: start with HHQ Urgent Care + ask about NYS RESTORE delivery locally.")
        lines.append("- Always call to confirm current openings and required documents.")
        lines.append("")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\\n".join(lines))

        messagebox.showinfo("Report Created", f"Report saved to:\\n{report_path}")
        log_event(f"Report generated: {report_path}")


def main():
    root = tk.Tk()
    app = SyrHousingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
"@

$PythonCode | Out-File -FilePath (Join-Path $BasePath "agent_gui.py") -Encoding UTF8

# -----------------------------
# 5) Create Virtual Environment (no activation required)
# -----------------------------
Write-Host "Creating virtual environment ..."

# Find Python 3.12 executable via launcher
$PyExe = & py -3.12 -c "import sys; print(sys.executable)"
if (-not $PyExe) {
    throw "Python 3.12 not found via py launcher. Run: py -0"
}

Write-Host "Using Python: $PyExe"

# Recreate venv cleanly
if (Test-Path $VenvPath) {
    Remove-Item -Recurse -Force $VenvPath
}

# Important: use call operator for quoted path
& "$PyExe" -m venv $VenvPath

# Ensure pip exists (some Windows venvs start minimal)
Write-Host "Bootstrapping pip in venv ..."
& $VenvPython -m ensurepip --upgrade | Out-Null

Write-Host "Installing packages into venv ..."
& $VenvPython -m pip install --upgrade pip | Out-Null
& $VenvPython -m pip install requests beautifulsoup4 | Out-Null

# -----------------------------
# 6) Finish
# -----------------------------
Write-Host ""
Write-Host "SUCCESS! System installed at C:\SyrHousing"
Write-Host "Next: run the GUI with:"
Write-Host "  $VenvPython C:\SyrHousing\agent_gui.py"
Write-Host ""
Write-Host "Files created:"
Write-Host " - Agents\Grant_Hunter_Prompt.txt"
Write-Host " - Agents\Evaluator_Prompt.txt"
Write-Host " - Data\grants_db.csv"
Write-Host " - agent_gui.py"
Write-Host ""
