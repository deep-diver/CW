# ConformWeb

> **Do LLM-Generated Web Apps Behave Correctly? A Contract-Grounded Benchmark for Behavioral Conformance**

This repository contains the supplementary materials for the above paper, submitted for double-blind review.

## Overview

ConformWeb is a contract-grounded protocol and benchmark that evaluates whether LLM-generated web applications preserve behavioral correctness under dynamic, multi-step interaction. The benchmark is instantiated across **24 validated instances** spanning **6 application families** and **4 complexity tiers**, scaling to **756 private scenarios** and **6,433 semantic steps**. Across **2,160 evaluation runs**, only 252 achieve full conformance (**11.7% strict pass rate**).

## Repository Structure

```
.
├── ConformWeb.pdf              # Paper manuscript
├── detoxbench/                 # Core evaluation framework
│   ├── core/                   # State management, assertions, logging, models
│   ├── dsl/                    # Contract DSL compiler, scenario sets, web bridge
│   ├── web/                    # Browser evaluator, local server
│   ├── cohorts.py              # Cohort configuration loader
│   └── dashboard.py            # Evaluation dashboard
├── targets/web/                # Benchmark instances (6 families × multiple tiers)
│   ├── stayflow_concierge/     # Travel booking
│   ├── freshcart_market/       # Grocery e-commerce
│   ├── clinic_shift_command/   # Clinical operations
│   ├── campus_registrar_command/ # Academic registration
│   ├── media_campaign_launch_desk/ # Marketing campaign
│   └── homefix_hub/            # Home services
├── reports/conformweb_visualizations/
│   ├── data/                   # Final CSV rollups and raw traces
│   ├── figures/                # Paper figures (PDF)
│   ├── tables/                 # Paper tables (CSV/TeX)
│   ├── contract_pack/          # Contract language spec and bundled contracts/scenarios
│   └── validation_report.md    # Full 2160-run validation report
├── tools/                      # Figure generation, auditing, and experiment scripts
├── tests/                      # Unit tests
├── docs/                       # Design documentation
├── tables/                     # Additional table artifacts
├── cohorts/                    # Cohort YAML configurations
└── pyproject.toml              # Python project configuration
```

## Benchmark Instances

Each instance under `targets/web/` contains:

| Artifact | Description |
|---|---|
| `contract.dsl.yaml` | Public behavioral contract defining admissible actions, observations, and relations |
| `scenarios.public.dsl.yaml` | Disclosed representative workflows |
| `scenarios.private.dsl.yaml` | Hidden evaluation scenarios (strictly grounded in the public contract) |
| `reference_app/` | Reference implementation (HTML/CSS/JS) |
| `cohorts/` | Batch-level metadata (`manifest.json`, `aggregate.json`, `progress.jsonl`) |

### Application Families

| Family | Description | Tiers |
|---|---|---|
| StayFlow Concierge | Travel itinerary and booking management | A, B, C |
| FreshCart Market | Grocery e-commerce with cart and checkout | A, B, C, D |
| Clinic Shift Command | Clinical staff scheduling and handoff | A, B, C, D |
| Campus Registrar Command | Academic course registration and enrollment | A, B, C, D |
| Media Campaign Launch Desk | Marketing campaign management | A, B, C, D |
| HomeFix Hub | Home service booking and dispatch | A, B, C, D |

### Complexity Tiers

- **Tier A**: Core happy-path workflows with linear state transitions
- **Tier B**: Multi-role interactions and conditional routing
- **Tier C**: Long-horizon dependencies with persistence and cross-page state
- **Tier D**: Full behavioral depth with authorization, projections, and service boundaries

## Key Results

| Metric | Value |
|---|---|
| Total evaluation runs | 2,160 |
| Strict full-pass rate | 11.7% (252/2,160) |
| Scenario-level conformance (S_scen) | 36.7% |
| Step-level progress (S_step) | 49.4% |
| Frontier model full-pass rate | 24.2% |
| Mini model full-pass rate | 0.8% |

See `reports/conformweb_visualizations/validation_report.md` for the complete per-model and per-family breakdown.

## Setup

Requires Python 3.11+:

```bash
pip install -e ".[dev]"
playwright install chromium
```

## Reproducing Figures and Tables

From the repository root:

```bash
# Build the main figure pack
python tools/build_conformweb_figure_pack.py

# Build pair comparison figures
python tools/build_conformweb_pair_figure.py

# Export figure source data
python tools/export_conformweb_figure_source_data.py

# Build the main model experiment table
python tools/build_main_model_experiment_table.py

# Audit private scenario admissibility
python tools/audit_private_admissibility.py
```

Source data for all figures and tables is in `reports/conformweb_visualizations/data/`.

## Running Tests

```bash
pytest
```

## Contract Language

The contract DSL defines three components per instance:

1. **Actions** (`AC`): Browser operations — control actions, inputs, uploads, role changes, navigation, reloads
2. **Observations** (`OC`): Evidence channels — application state, browser metadata, service calls, rendered projections
3. **Relations** (`RC`): Behavioral checks — state transitions, validation, persistence, authorization effects

A private scenario is admissible (`τ ⪯ C`) only if every action, observation reference, and check can be resolved through the public contract. See `reports/conformweb_visualizations/contract_pack/` for the language specification and bundled artifacts.

## Validation

The 2,160-run validation report confirms:

- All 24 instances validated with complete coverage
- Zero missing or excluded runs after fill
- Per-model rollups derived from evaluation reports, not inferred from group aggregates

See `reports/conformweb_visualizations/validation_report.md` and `reports/conformweb_visualizations/private_admissibility_audit.md`.

## Manifest

Every included file, its original repository path, size, and inclusion reason is listed in `PACK_MANIFEST.csv`. Large artifacts (screenshots, per-run event logs, generated app directories, browser traces) are excluded from this submission pack; their aggregate results are preserved in the included CSV rollups and batch-level metadata.
