"""Fabric Optimization & Workshop Planning - Engagement Summary deck.

Reuses theme/helpers from build_fabric_target_arch_ppt.py.
"""
from __future__ import annotations
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from build_fabric_target_arch_ppt import (  # type: ignore
    Presentation, Inches, Pt, Emu, RGBColor, MSO_SHAPE, PP_ALIGN, MSO_ANCHOR,
    BG, ACCENT, ACCENT2, WHITE, SUBTEXT, CARD_BG, CARD_LINE,
    PHASE_RED, PHASE_ORG, PHASE_BLU, PHASE_LBL,
    SLIDE_W, SLIDE_H,
    make_prs, set_bg, add_text, add_bullets, add_card, add_circle,
    add_page_number, title,
)

PAGE = {"n": 0}
PRESENTER = "Naga Venkata Cheruvu, CSA  ·  Microsoft"


def footer(slide):
    add_text(slide, Inches(0.55), Inches(7.15), Inches(10), Inches(0.3),
             PRESENTER, size=9, color=SUBTEXT)


def pn(slide):
    PAGE["n"] += 1
    footer(slide)
    add_page_number(slide, PAGE["n"])


def add_link_line(slide, left, top, width, height, label, url, *,
                  size=12, label_color=ACCENT, url_color=WHITE):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r1 = p.add_run()
    r1.text = f"\u25B8  {label}  \u2014  "
    r1.font.name = "Segoe UI"; r1.font.size = Pt(size); r1.font.bold = True
    r1.font.color.rgb = label_color
    r2 = p.add_run()
    r2.text = url
    r2.font.name = "Segoe UI"; r2.font.size = Pt(size - 1)
    r2.font.color.rgb = url_color
    r2.hyperlink.address = url
    return tb


# ---------- Slides ----------
def s_title(prs, engagement, dt, customer_attendees, ms_attendees):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    add_text(s, Inches(0.55), Inches(0.45), Inches(3), Inches(0.4),
             "Microsoft", size=14, bold=True, color=WHITE)
    add_text(s, Inches(0.55), Inches(1.7), Inches(12), Inches(2.4),
             "Fabric Optimization\n& Workshop Planning",
             size=54, bold=True, color=ACCENT)
    add_text(s, Inches(0.55), Inches(4.6), Inches(12), Inches(0.5),
             engagement, size=18, color=SUBTEXT)
    add_text(s, Inches(0.55), Inches(5.05), Inches(12), Inches(0.5),
             f"Date: {dt}", size=14, color=SUBTEXT)
    add_text(s, Inches(0.55), Inches(5.65), Inches(6), Inches(0.4),
             "Customer Participants", size=13, bold=True, color=ACCENT)
    add_text(s, Inches(0.55), Inches(6.05), Inches(6), Inches(1.0),
             customer_attendees, size=12, color=WHITE)
    add_text(s, Inches(7.0), Inches(5.65), Inches(6), Inches(0.4),
             "Microsoft Team", size=13, bold=True, color=ACCENT)
    add_text(s, Inches(7.0), Inches(6.05), Inches(6), Inches(1.0),
             ms_attendees, size=12, color=WHITE)
    pn(s)


def s_agenda(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    panel = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                               Inches(0.4), Inches(0.5), Inches(4.0), Inches(6.5))
    panel.adjustments[0] = 0.06
    panel.fill.solid(); panel.fill.fore_color.rgb = RGBColor(0x22, 0x2F, 0x3D)
    panel.line.color.rgb = CARD_LINE
    add_text(s, Inches(0.7), Inches(3.0), Inches(3.5), Inches(1.2),
             "Agenda", size=54, bold=True, color=ACCENT)
    items = [
        ("Executive Summary", "Engagement progress and key themes"),
        ("Current State Assessment", "Observed issues across storage, design, and pipelines"),
        ("Work Completed To Date", "Joint progress across teams"),
        ("Key Discussion Areas", "Architecture, pipelines, ingestion, governance, environments"),
        ("Gaps & Risks", "Where clarity, validation, and ownership are needed"),
        ("Recommended Next Steps", "Concrete actions to stabilize and align"),
        ("Workshop Plus \u2014 Data Warehouse", "Proposed engagement and expected outcomes"),
        ("Demo Assets & References", "Working examples and Microsoft Learn alignment"),
        ("Additional Topics & Customer Asks", "Workflow, RBAC, agents, GHC, S3 policy, access"),
        ("Decisions Needed & Action Plan", "Owners, timeline, and follow-ups"),
    ]
    x = Inches(4.9); y = Inches(0.65)
    for head, sub in items:
        add_text(s, x, y, Inches(8), Inches(0.4), f"\u2022  {head}",
                 size=20, bold=True, color=WHITE)
        add_text(s, x + Inches(0.4), y + Inches(0.42), Inches(8), Inches(0.4),
                 sub, size=12, color=SUBTEXT)
        y += Inches(0.78)
    pn(s)


def s_exec_summary(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Executive Summary")
    add_bullets(s, Inches(0.6), Inches(1.55), Inches(12.2), Inches(3.0), [
        "Engagement focused on Microsoft Fabric optimization and forward roadmap planning",
        "Recent working sessions reviewed architecture, pipeline performance, and storage growth",
        "Joint Microsoft + customer collaboration has surfaced clear themes and early wins",
        "Several remediation actions are in flight; validation with current metrics is the next gate",
    ], size=17)

    themes = [
        ("OPTIMIZATION",   "Tune storage, pipelines, and table design to control cost and runtime"),
        ("STABILIZATION",  "Reduce repeat issues and operational firefighting"),
        ("ARCHITECTURE ALIGNMENT", "Confirm OneLake-centric target state and medallion pattern"),
    ]
    cw = Inches(4.05); ch = Inches(2.0)
    for i, (h, b) in enumerate(themes):
        left = Inches(0.55) + (cw + Inches(0.15)) * i
        top = Inches(4.95)
        add_card(s, left, top, cw, ch, accent_bar=ACCENT)
        add_text(s, left + Inches(0.3), top + Inches(0.2), cw - Inches(0.5), Inches(0.4),
                 h, size=12, bold=True, color=ACCENT)
        add_text(s, left + Inches(0.3), top + Inches(0.65), cw - Inches(0.5), Inches(1.3),
                 b, size=14, color=WHITE)
    pn(s)


def s_current_state(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Current State Assessment")

    cards = [
        ("Storage Growth & Inefficiencies",
         ["Rapid OneLake / warehouse growth without lifecycle controls",
          "Mix of Delta and non-optimized formats; lack of VACUUM / OPTIMIZE cadence",
          "Limited visibility into per-workspace and per-item storage cost"]),
        ("Data Duplication & Multiple Loads",
         ["Same source data ingested into multiple workspaces / items",
          "Copies created where OneLake shortcuts would suffice",
          "Overlapping ingestion paths drive compute and storage spend"]),
        ("Inefficient Table Design",
         ["VARCHAR / string-heavy schemas; missing type enforcement",
          "Sub-optimal partitioning / no clustering or V-Order in places",
          "Wide tables and weak relationships push work to semantic layer"]),
        ("Pipeline Performance & Runtime",
         ["Long-running notebooks and pipelines; intermittent failures",
          "Triple-write patterns and mixed concerns within a single pipeline",
          "Limited observability \u2014 hard to attribute slow stages"]),
    ]
    cw = Inches(6.15); ch = Inches(2.5)
    for i, (h, items) in enumerate(cards):
        r, c = divmod(i, 2)
        left = Inches(0.55) + (cw + Inches(0.15)) * c
        top = Inches(1.5) + (ch + Inches(0.15)) * r
        add_card(s, left, top, cw, ch, accent_bar=ACCENT)
        add_text(s, left + Inches(0.3), top + Inches(0.15), cw - Inches(0.5), Inches(0.4),
                 h, size=14, bold=True, color=ACCENT)
        add_bullets(s, left + Inches(0.3), top + Inches(0.6),
                    cw - Inches(0.5), ch - Inches(0.7), items, size=12)

    add_card(s, Inches(0.55), Inches(6.85), Inches(12.2), Inches(0.55),
             fill=RGBColor(0x32, 0x44, 0x55), accent_bar=ACCENT)
    add_text(s, Inches(0.9), Inches(6.9), Inches(11.5), Inches(0.5),
             "Note: Several remediation actions have started \u2014 validation with current metrics is pending.",
             size=12, bold=True, color=WHITE)
    pn(s)


def s_work_completed(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Work Completed To Date")

    add_text(s, Inches(0.6), Inches(1.5), Inches(6), Inches(0.5),
             "Improvements Delivered", size=20, bold=True, color=ACCENT)
    add_bullets(s, Inches(0.6), Inches(2.0), Inches(6), Inches(4.5), [
        "Initial review of high-cost workspaces and item-level storage",
        "Identified candidate tables for type/schema remediation",
        "Pilot pipeline refactor toward separated Bronze / Silver / Gold stages",
        "Early adoption of OneLake shortcuts to reduce duplicate loads",
        "Capacity utilization patterns reviewed; quick wins documented",
    ], size=14)

    add_text(s, Inches(7.0), Inches(1.5), Inches(6), Inches(0.5),
             "Collaboration Highlights", size=20, bold=True, color=ACCENT)
    add_bullets(s, Inches(7.0), Inches(2.0), Inches(6), Inches(4.5), [
        "Joint working sessions across data engineering, analytics, and platform teams",
        "Knowledge transfer on Fabric best practices and reference patterns",
        "Shared prior guidance and reference architectures with the customer team",
        "Aligned on a common vocabulary for next phases (EDW, medallion, shortcuts)",
        "Microsoft CSA/CSAM team engaged to support advisory hours utilization",
    ], size=14)

    add_card(s, Inches(0.55), Inches(6.55), Inches(12.2), Inches(0.7),
             fill=RGBColor(0x32, 0x44, 0x55), accent_bar=ACCENT)
    add_text(s, Inches(0.9), Inches(6.62), Inches(11.5), Inches(0.6),
             "Action: Build a consolidated \u2018completed vs pending\u2019 tracker as the single source of truth.",
             size=13, bold=True, color=WHITE)
    pn(s)


def s_discussion_areas(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Key Discussion Areas")
    cards = [
        ("Data Warehouse Architecture",
         "Fabric Warehouse vs Lakehouse selection; OneLake as the single data plane; "
         "shortcuts over data copies for downstream consumption."),
        ("Pipeline Design (Medallion)",
         "Bronze (raw) \u2192 Silver (cleansed, typed) \u2192 Gold (business-ready). "
         "Stage separation, ownership, and incremental processing."),
        ("Data Ingestion Patterns",
         "Fabric Mirroring for operational sources, Data Pipelines for orchestration, "
         "Dataflows Gen2 for SaaS, API ingestion via notebooks/eventstreams."),
        ("Governance & Lineage (Purview)",
         "Fabric native catalog and lineage first; Purview layered for cross-cloud "
         "discovery, glossary, certifications, and DLP."),
        ("Environment Strategy & CI/CD",
         "Workspace tiers (Dev / Test / Prod), Fabric Deployment Pipelines or "
         "fabric-cicd / Git integration for repeatable promotion."),
        ("Operating Model & Capacity",
         "Capacity sizing, autoscale considerations, workspace-to-capacity mapping, "
         "and chargeback visibility."),
    ]
    cw = Inches(4.05); ch = Inches(1.7)
    for i, (h, b) in enumerate(cards):
        r, c = divmod(i, 3)
        left = Inches(0.4) + (cw + Inches(0.1)) * c
        top  = Inches(1.5) + (ch + Inches(0.15)) * r
        add_card(s, left, top, cw, ch, accent_bar=ACCENT)
        add_text(s, left + Inches(0.3), top + Inches(0.15), cw - Inches(0.5), Inches(0.4),
                 h, size=13, bold=True, color=ACCENT)
        add_text(s, left + Inches(0.3), top + Inches(0.55), cw - Inches(0.5), ch - Inches(0.65),
                 b, size=11, color=WHITE)
    pn(s)


def s_architecture_diagram(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Suggested Target Architecture \u2014 Fabric")

    # Sources
    add_card(s, Inches(0.35), Inches(1.6), Inches(2.3), Inches(4.6),
             fill=RGBColor(0x2E, 0x44, 0x60), accent_bar=ACCENT2)
    add_text(s, Inches(0.5), Inches(1.75), Inches(2.1), Inches(0.4),
             "SOURCES", size=11, bold=True, color=ACCENT)
    for i, src in enumerate(["Azure SQL / Cosmos", "Snowflake / BigQuery",
                              "Salesforce / Workday", "SAP / Oracle",
                              "Files / APIs", "Streaming events"]):
        add_text(s, Inches(0.55), Inches(2.2) + Inches(0.55) * i,
                 Inches(2.0), Inches(0.4), f"\u2022 {src}", size=12, color=WHITE)

    # Ingestion column
    add_card(s, Inches(2.8), Inches(1.6), Inches(2.1), Inches(4.6),
             fill=RGBColor(0x2C, 0x40, 0x5A), accent_bar=ACCENT2)
    add_text(s, Inches(2.95), Inches(1.75), Inches(1.9), Inches(0.4),
             "INGESTION", size=11, bold=True, color=ACCENT)
    for i, p in enumerate(["Mirroring", "Data Pipelines", "Dataflows Gen2",
                            "Eventstreams", "Notebooks / API"]):
        add_text(s, Inches(3.0), Inches(2.25) + Inches(0.6) * i,
                 Inches(1.8), Inches(0.4), f"\u2022 {p}", size=12, color=WHITE)

    # OneLake medallion
    add_card(s, Inches(5.05), Inches(1.6), Inches(5.4), Inches(4.6),
             fill=RGBColor(0x22, 0x3A, 0x52), accent_bar=ACCENT)
    add_text(s, Inches(5.2), Inches(1.75), Inches(5.1), Inches(0.4),
             "ONELAKE \u2014 EDW (Lakehouse + Warehouse)",
             size=12, bold=True, color=ACCENT)
    layers = [
        ("BRONZE", RGBColor(0x8B, 0x5A, 0x2B), "Raw ingest"),
        ("SILVER", RGBColor(0x9A, 0xA5, 0xB1), "Cleansed / typed"),
        ("GOLD",   RGBColor(0xD4, 0xAF, 0x37), "Business-ready"),
    ]
    pw = Inches(1.65); ph = Inches(3.1)
    for i, (name, color, sub) in enumerate(layers):
        left = Inches(5.2) + (pw + Inches(0.1)) * i
        top = Inches(2.35)
        add_card(s, left, top, pw, ph, fill=RGBColor(0x2D, 0x3E, 0x52), accent_bar=color)
        add_text(s, left, top + Inches(0.3), pw, Inches(0.5),
                 name, size=16, bold=True, color=color, align=PP_ALIGN.CENTER)
        add_text(s, left, top + Inches(0.95), pw, Inches(0.5),
                 sub, size=11, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, Inches(5.2), Inches(5.7), Inches(5.2), Inches(0.4),
             "Pipeline A: B\u2192S    \u00B7    Pipeline B: S\u2192G",
             size=11, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)

    # Consumption
    add_card(s, Inches(10.6), Inches(1.6), Inches(2.4), Inches(4.6),
             fill=RGBColor(0x2E, 0x44, 0x60), accent_bar=ACCENT2, bar_side="right")
    add_text(s, Inches(10.75), Inches(1.75), Inches(2.2), Inches(0.4),
             "CONSUMPTION", size=11, bold=True, color=ACCENT)
    for i, c in enumerate(["Power BI / Semantic", "SQL endpoints",
                            "Data Science / ML", "Real-Time Analytics",
                            "Shortcuts \u2014 no copies"]):
        add_text(s, Inches(10.8), Inches(2.25) + Inches(0.6) * i,
                 Inches(2.2), Inches(0.4), f"\u2022 {c}", size=11, color=WHITE)

    # Governance bar
    add_card(s, Inches(0.35), Inches(6.5), Inches(12.65), Inches(0.7),
             fill=RGBColor(0x32, 0x44, 0x55), accent_bar=ACCENT)
    add_text(s, Inches(0.7), Inches(6.58), Inches(12.0), Inches(0.55),
             "Governance: Fabric Catalog & Lineage   \u2192   Purview (glossary, certifications, DLP, cross-cloud)   |   CI/CD: Git + Deployment Pipelines",
             size=11, bold=True, color=WHITE)
    pn(s)


def s_gaps_risks(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Gaps & Risks Identified")
    cards = [
        ("Clarity",
         "No single view of what is completed vs pending across recent remediation work",
         PHASE_ORG),
        ("Metrics Validation",
         "Improvements have not yet been validated against current storage and runtime metrics",
         PHASE_RED),
        ("Operational Stability",
         "Repeat issues and intermittent failures continue to consume team capacity",
         PHASE_RED),
        ("Deployment Strategy",
         "Environment tiers (Dev / Test / Prod) and CI/CD promotion model are not yet defined",
         PHASE_BLU),
        ("Ownership",
         "Boundary between platform, data engineering, and analytics ownership needs to be made explicit",
         PHASE_LBL),
        ("Governance Sequencing",
         "Risk of layering Purview before the data foundation is stable enough to benefit",
         PHASE_ORG),
    ]
    cw = Inches(4.05); ch = Inches(1.75)
    for i, (h, b, color) in enumerate(cards):
        r, c = divmod(i, 3)
        left = Inches(0.4) + (cw + Inches(0.1)) * c
        top  = Inches(1.55) + (ch + Inches(0.2)) * r
        add_card(s, left, top, cw, ch, accent_bar=color)
        add_text(s, left + Inches(0.3), top + Inches(0.15), cw - Inches(0.5), Inches(0.4),
                 h, size=13, bold=True, color=color)
        add_text(s, left + Inches(0.3), top + Inches(0.55), cw - Inches(0.5), ch - Inches(0.65),
                 b, size=11, color=WHITE)
    pn(s)


def s_next_steps(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Recommended Next Steps")
    add_bullets(s, Inches(0.6), Inches(1.55), Inches(12.2), Inches(5.0), [
        "Build a consolidated \u201Ccompleted vs pending\u201D tracker for all remediation items",
        "Validate recent improvements against current storage, runtime, and capacity metrics",
        "Re-share historical recommendations and prior guidance in a single reference pack",
        "Align stakeholders on the target architecture (OneLake EDW + medallion) and operating model",
        "Confirm workspace tiering (Dev / Test / Prod) and the CI/CD promotion approach",
        "Prepare for Workshop Plus \u2014 Data Warehouse focus, with prerequisites and success criteria",
        "Schedule a deep-dive review session to validate improvements and finalize the roadmap",
    ], size=16)
    pn(s)


def s_workshop(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Workshop Plus \u2014 Fabric Data Warehouse")

    add_text(s, Inches(0.6), Inches(1.5), Inches(6), Inches(0.5),
             "Why Now", size=20, bold=True, color=ACCENT)
    add_bullets(s, Inches(0.6), Inches(2.0), Inches(6), Inches(3.0), [
        "Architecture decisions are converging \u2014 ideal time for guided deep dive",
        "Data warehouse choices have outsized impact on cost and performance",
        "Hands-on guidance accelerates adoption of best practices",
        "Leverages existing advisory hours and Microsoft CSA support",
    ], size=14)

    add_text(s, Inches(7.0), Inches(1.5), Inches(6), Inches(0.5),
             "Expected Outcomes", size=20, bold=True, color=ACCENT)
    add_bullets(s, Inches(7.0), Inches(2.0), Inches(6), Inches(3.0), [
        "Confirmed Fabric Warehouse architecture and reference patterns",
        "Best-practice adoption for table design, partitioning, and V-Order",
        "Hands-on guidance for pipelines, ingestion, and SQL endpoint usage",
        "Aligned operating model: roles, environments, and CI/CD",
    ], size=14)

    # candidate topics row
    topics = ["Warehouse vs Lakehouse", "Medallion Pipelines",
              "Mirroring & Ingestion", "Performance Tuning",
              "CI/CD & Deployment", "Governance & Purview"]
    cw = Inches(2.05); ch = Inches(0.7)
    for i, t in enumerate(topics):
        r, c = divmod(i, 6)
        left = Inches(0.55) + (cw + Inches(0.1)) * c
        top = Inches(5.4) + (ch + Inches(0.15)) * r
        chip = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, cw, ch)
        chip.adjustments[0] = 0.4
        chip.fill.solid(); chip.fill.fore_color.rgb = RGBColor(0x2E, 0x44, 0x55)
        chip.line.color.rgb = ACCENT
        tf = chip.text_frame; tf.margin_left=tf.margin_right=Emu(0)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r1 = p.add_run(); r1.text = t
        r1.font.name="Segoe UI"; r1.font.size=Pt(11); r1.font.color.rgb = ACCENT
        r1.font.bold = True

    add_card(s, Inches(0.55), Inches(6.55), Inches(12.2), Inches(0.7),
             fill=RGBColor(0x32, 0x44, 0x55), accent_bar=ACCENT)
    add_text(s, Inches(0.9), Inches(6.62), Inches(11.5), Inches(0.55),
             "Recommendation: Schedule Workshop Plus and use available advisory hours for tailored follow-ups.",
             size=13, bold=True, color=WHITE)
    pn(s)


def s_decisions(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Decision Points Needed from Customer")
    add_bullets(s, Inches(0.6), Inches(1.55), Inches(12.2), Inches(5.0), [
        "Target architecture confirmation \u2014 OneLake EDW + medallion pattern",
        "Warehouse vs Lakehouse strategy for analytical workloads",
        "Workspace tiering and CI/CD approach (Deployment Pipelines / Git / fabric-cicd)",
        "Ownership boundaries across platform, data engineering, and analytics teams",
        "Priority domain(s) for Phase 2 pipeline refactor and metric validation",
        "Commitment to Workshop Plus dates and required participant roster",
        "Sequencing of Purview integration relative to data foundation maturity",
    ], size=16)
    pn(s)


def s_action_plan(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Action Plan \u2014 Owners & Timeline")

    # Microsoft column
    add_card(s, Inches(0.4), Inches(1.5), Inches(4.15), Inches(5.4),
             accent_bar=ACCENT2)
    add_text(s, Inches(0.55), Inches(1.65), Inches(3.9), Inches(0.4),
             "MICROSOFT TEAM", size=12, bold=True, color=ACCENT)
    add_bullets(s, Inches(0.55), Inches(2.1), Inches(3.9), Inches(4.7), [
        "Compile completed vs pending tracker",
        "Share historical guidance pack",
        "Draft Workshop Plus agenda",
        "Coordinate advisory-hour usage",
        "Provide reference architectures",
    ], size=12)

    # Customer column
    add_card(s, Inches(4.7), Inches(1.5), Inches(4.15), Inches(5.4),
             accent_bar=ACCENT)
    add_text(s, Inches(4.85), Inches(1.65), Inches(3.9), Inches(0.4),
             "CUSTOMER TEAM", size=12, bold=True, color=ACCENT)
    add_bullets(s, Inches(4.85), Inches(2.1), Inches(3.9), Inches(4.7), [
        "Confirm target architecture",
        "Provide current metrics for validation",
        "Nominate pilot domain for refactor",
        "Confirm Workshop Plus dates / attendees",
        "Identify decision owners by area",
    ], size=12)

    # Dependencies column
    add_card(s, Inches(9.0), Inches(1.5), Inches(4.0), Inches(5.4),
             accent_bar=PHASE_ORG)
    add_text(s, Inches(9.15), Inches(1.65), Inches(3.8), Inches(0.4),
             "DEPENDENCIES", size=12, bold=True, color=PHASE_ORG)
    add_bullets(s, Inches(9.15), Inches(2.1), Inches(3.8), Inches(4.7), [
        "Access to capacity / workspace metrics",
        "Source-system access for ingestion validation",
        "Availability of pilot-domain SMEs",
        "Approval for environment tiering changes",
        "Alignment on Purview readiness",
    ], size=12)

    add_card(s, Inches(0.4), Inches(7.0), Inches(12.6), Inches(0.4),
             fill=RGBColor(0x32, 0x44, 0x55), accent_bar=None, line=CARD_LINE)
    add_text(s, Inches(0.55), Inches(7.04), Inches(12.4), Inches(0.35),
             "Timeline: confirm dates jointly in the next review meeting.",
             size=11, color=SUBTEXT)
    pn(s)


def s_demo_assets(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Demo Assets \u2014 Built for This Engagement")

    repo_root = "https://github.com/ncheruvu-MSFT/msft-fabric-utils"

    # Fabric examples
    add_text(s, Inches(0.55), Inches(1.5), Inches(6), Inches(0.4),
             "Fabric \u2014 Warehouse, Lakehouse & Capacity",
             size=15, bold=True, color=ACCENT)
    fabric_links = [
        ("Warehouse & Lakehouse Metrics",
         f"{repo_root}/blob/main/notebooks/fabric-warehouse-lakehouse-metrics.ipynb"),
        ("Notebook & Pipeline Efficiency",
         f"{repo_root}/blob/main/notebooks/fabric-notebook-pipeline-efficiency.ipynb"),
        ("Warehouse Perf & OneLake Soft-Delete",
         f"{repo_root}/blob/main/notebooks/fabric-warehouse-performance-softdelete.ipynb"),
        ("Spark Monitoring Setup",
         f"{repo_root}/blob/main/notebooks/fabric-spark-monitoring-setup.ipynb"),
        ("Capacity / Region Migration Inventory",
         f"{repo_root}/tree/main/fabric-region-migration"),
        ("Fabric CI/CD Examples",
         f"{repo_root}/tree/main/fabric-cicd"),
    ]
    for i, (lbl, url) in enumerate(fabric_links):
        add_link_line(s, Inches(0.55), Inches(1.95) + Inches(0.42) * i,
                      Inches(6.3), Inches(0.4), lbl, url)

    # Governance & Purview examples
    add_text(s, Inches(7.0), Inches(1.5), Inches(6), Inches(0.4),
             "Governance, Purview & Security",
             size=15, bold=True, color=ACCENT)
    gov_links = [
        ("Fabric SDLC Governance (Purview)",
         f"{repo_root}/tree/main/fabric-sdlc-governance"),
        ("Purview \u2014 Glossary, Labels, DLP scripts",
         f"{repo_root}/tree/main/fabric-sdlc-governance/scripts"),
        ("Fabric Data Agent Governance",
         f"{repo_root}/tree/main/fabric-data-agent-governance"),
        ("OneLake Security Examples",
         f"{repo_root}/tree/main/fabric-onelake-security"),
        ("Azure Resource Inventory",
         f"{repo_root}/tree/main/azure-resource-inventory"),
        ("Reference Architecture & Docs",
         f"{repo_root}/tree/main/fabric-sdlc-governance/docs"),
    ]
    for i, (lbl, url) in enumerate(gov_links):
        add_link_line(s, Inches(7.0), Inches(1.95) + Inches(0.42) * i,
                      Inches(6.3), Inches(0.4), lbl, url)

    add_card(s, Inches(0.55), Inches(6.55), Inches(12.2), Inches(0.55),
             fill=RGBColor(0x32, 0x44, 0x55), accent_bar=ACCENT)
    add_text(s, Inches(0.85), Inches(6.6), Inches(11.5), Inches(0.45),
             f"Repository: {repo_root}",
             size=12, bold=True, color=WHITE)
    pn(s)


def s_references(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Microsoft Learn \u2014 Aligned References")

    add_text(s, Inches(0.55), Inches(1.45), Inches(6), Inches(0.4),
             "Fabric Architecture & Warehouse",
             size=14, bold=True, color=ACCENT)
    fabric_refs = [
        ("What is Microsoft Fabric",
         "https://learn.microsoft.com/fabric/fundamentals/microsoft-fabric-overview"),
        ("OneLake \u2014 The OneDrive for data",
         "https://learn.microsoft.com/fabric/onelake/onelake-overview"),
        ("Lakehouse overview",
         "https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview"),
        ("OneLake shortcuts",
         "https://learn.microsoft.com/fabric/onelake/onelake-shortcuts"),
        ("Medallion lakehouse architecture",
         "https://learn.microsoft.com/fabric/onelake/onelake-medallion-lakehouse-architecture"),
        ("Fabric Warehouse \u2014 What is it?",
         "https://learn.microsoft.com/fabric/data-warehouse/data-warehousing"),
        ("Warehouse performance guidelines",
         "https://learn.microsoft.com/fabric/data-warehouse/guidelines-warehouse-performance"),
        ("V-Order for Delta tables",
         "https://learn.microsoft.com/fabric/data-engineering/delta-optimization-and-v-order"),
    ]
    for i, (lbl, url) in enumerate(fabric_refs):
        add_link_line(s, Inches(0.55), Inches(1.85) + Inches(0.38) * i,
                      Inches(6.3), Inches(0.4), lbl, url, size=11)

    add_text(s, Inches(7.0), Inches(1.45), Inches(6), Inches(0.4),
             "Ingestion, Governance & CI/CD",
             size=14, bold=True, color=ACCENT)
    other_refs = [
        ("Fabric Mirroring overview",
         "https://learn.microsoft.com/fabric/mirroring/overview"),
        ("Data Pipelines overview",
         "https://learn.microsoft.com/fabric/data-factory/data-factory-overview"),
        ("Dataflows Gen2 overview",
         "https://learn.microsoft.com/fabric/data-factory/dataflows-gen2-overview"),
        ("Fabric Deployment Pipelines",
         "https://learn.microsoft.com/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines"),
        ("Fabric Git integration",
         "https://learn.microsoft.com/fabric/cicd/git-integration/intro-to-git-integration"),
        ("Purview & Fabric integration",
         "https://learn.microsoft.com/fabric/governance/microsoft-purview-fabric"),
        ("Purview Unified Catalog",
         "https://learn.microsoft.com/purview/unified-catalog"),
    ]
    for i, (lbl, url) in enumerate(other_refs):
        add_link_line(s, Inches(7.0), Inches(1.85) + Inches(0.38) * i,
                      Inches(6.3), Inches(0.4), lbl, url, size=11)
    pn(s)


def s_additional_topics(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Additional Topics & Customer Asks")
    add_text(s, Inches(0.55), Inches(1.25), Inches(12.3), Inches(0.35),
             "Open items to address in workshop / follow-up sessions \u2014 with demo coverage",
             size=12, color=SUBTEXT)

    # Two-column grid of topic cards: (title, demo-coverage line)
    items = [
        ("Resource Structure Recommendations",
         "Workspace, capacity & domain layout \u2014 covered in Target Architecture deck; demo: workspace/capacity inventory notebooks"),
        ("Workflow Recommendations",
         "Branch promotion, environments, release flow \u2014 demo: fabric-sdlc-governance/diagrams/branch-promotion.drawio"),
        ("Resource Management Approach",
         "TF vs fabric-cicd vs JSON\u2192API vs hybrid \u2014 demo: fabric-cicd/ examples and fabric_deploy.py"),
        ("GitHub Copilot Features & Capabilities",
         "Live demo of GHC in VS Code: chat, edits, agent mode, MCP tools, code review"),
        ("Agents",
         "Fabric Data Agents + governance \u2014 demo: fabric-data-agent-governance/notebooks & scripts"),
        ("Skills (Copilot / Agents)",
         "Custom skills, prompt files, AGENTS.md \u2014 walkthrough of repo's .github/copilot-instructions if present"),
        ("RBAC Roles Guidance",
         "Workspace + item-level + OneLake roles \u2014 demo: fabric-onelake-security/scripts & tests"),
        ("Code Review for \u201cFuture State\u201d",
         "Joint review of existing notebooks/pipelines vs target patterns \u2014 use GHC code review on selected files"),
        ("S3 Connector Policy Review",
         "OneLake S3 shortcut policy, egress, IAM \u2014 demo: shortcut + access policy walkthrough"),
        ("Access Provisioning",
         "Grant Naga (CSA) access to Fabric tenant + include on PR reviews for ongoing guidance"),
    ]

    col_w = Inches(6.15)
    row_h = Inches(1.05)
    gap_x = Inches(0.10)
    gap_y = Inches(0.12)
    left0 = Inches(0.55)
    top0 = Inches(1.75)
    for i, (head, body) in enumerate(items):
        col = i % 2
        row = i // 2
        left = left0 + (col_w + gap_x) * col
        top = top0 + (row_h + gap_y) * row
        add_card(s, left, top, col_w, row_h,
                 fill=CARD_BG, accent_bar=ACCENT)
        add_text(s, left + Inches(0.20), top + Inches(0.08),
                 col_w - Inches(0.30), Inches(0.35),
                 head, size=12, bold=True, color=WHITE)
        add_text(s, left + Inches(0.20), top + Inches(0.42),
                 col_w - Inches(0.30), Inches(0.60),
                 body, size=10, color=SUBTEXT)
    pn(s)


def s_followup(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
    title(s, "Next Meeting & Follow-Up")
    add_bullets(s, Inches(0.6), Inches(1.55), Inches(12.2), Inches(3.5), [
        "Schedule deep-dive review to validate improvements with live metrics",
        "Walk through consolidated completed vs pending tracker",
        "Decide Workshop Plus scheduling and prerequisites",
        "Confirm decision owners and timeline for outstanding items",
    ], size=17)

    add_card(s, Inches(0.55), Inches(5.0), Inches(12.2), Inches(1.6),
             fill=RGBColor(0x32, 0x44, 0x55), accent_bar=ACCENT)
    add_text(s, Inches(0.9), Inches(5.15), Inches(11.5), Inches(0.4),
             "GOAL", size=12, bold=True, color=ACCENT)
    add_text(s, Inches(0.9), Inches(5.55), Inches(11.5), Inches(1.0),
             "An aligned forward roadmap \u2014 a stable Fabric foundation, a clear workshop plan, "
             "and a shared view of progress for both teams.",
             size=15, color=WHITE)

    add_text(s, Inches(0.55), Inches(6.95), Inches(12.2), Inches(0.4),
             "Q&A", size=22, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
    pn(s)


def build(out_path: str,
          engagement: str,
          dt: str,
          customer_attendees: str,
          ms_attendees: str):
    prs = make_prs()
    s_title(prs, engagement, dt, customer_attendees, ms_attendees)
    s_agenda(prs)
    s_exec_summary(prs)
    s_current_state(prs)
    s_work_completed(prs)
    s_discussion_areas(prs)
    s_architecture_diagram(prs)
    s_gaps_risks(prs)
    s_next_steps(prs)
    s_workshop(prs)
    s_demo_assets(prs)
    s_references(prs)
    s_additional_topics(prs)
    s_decisions(prs)
    s_action_plan(prs)
    s_followup(prs)
    prs.save(out_path)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "docs",
        "fabric-engagement-summary.pptx"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build(
        out_path=out,
        engagement="Fabric Optimization & Workshop Planning",
        dt=date.today().strftime("%B %d, %Y"),
        customer_attendees="<Customer Lead>, <Data Engineering Lead>, <Analytics Lead>, <Platform Owner>",
        ms_attendees="<CSA>, <CSAM>, <Cloud Solution Specialist>, <Specialist - Fabric>",
    )
