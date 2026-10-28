# Offline scouting workbench implementation plan

> **For agentic workers:** execute natively with the executing-plans and test-driven-development workflows. The user's instruction to start authorizes continuous implementation.

**Goal:** deliver a usable offline screenshot annotation, army confirmation, and entry-plan preview app, the first milestone of the final research.

**Architecture:** one standard-library Python HTTP process bound to loopback, with a static vanilla-JavaScript canvas UI. Images and saved sessions stay in the browser. The Python endpoint receives validated normalized annotations/army data and returns inventory-feasible heuristic candidates. No game inputs, capture hooks, model downloads, or invented probabilities.

**Stack:** Python 3.11+, unittest, browser Canvas, plain HTML/CSS/JavaScript. No third-party runtime packages.

**Spec:** research/FINAL_RESEARCH.md, especially architecture, minimal stack and perception/preview milestones.

## Global constraints
- Markdown is the documentation format; preserve all research artifacts.
- User PC: Windows, Ryzen 5 4600H, GTX 1650 Ti,16GB RAM. Existing bundled Python can run this milestone.
- This milestone uses manual annotations/army confirmation; label that clearly. Synthetic demo is clearly marked.
- Heuristic entry cost is not success probability or predicted destruction. No98% or15second performance claims.
- Every plan point must fall inside a user-confirmed deployment rectangle. Do not infer legal space from screen edges.
- Input changes invalidate previous candidates. Import validates dimensions, enums, counts, IDs and image data.
- HTTP serves only explicit app assets/API, bound127.0.0.1; reject cross-origin requests and oversized payloads.
- No Git repository exists; work in place without inventing commits/worktrees.

## Design direction
Screenshot-first workspace with an ivory-white canvas surround, blue slate header (#18364a), teal deployment markings (#147d72), orange selected-entry accent (#d97732), ink text (#203644), and quiet gray borders (#dce4e9). Segoe UI for controls. Large map on the left, compact Army/Map/Plans inspector on the right; no decorative animation or dashboard metrics.

## Review focus
1. Malformed/nonfinite geometry must never yield a plan outside the image or legal region.
2. Candidate allocations/reserves must preserve exactly the confirmed available quantities.
3. Missing scouting/army confirmation, center, Town Hall or zones must produce actionable needs-input results.
4. Screenshot/import/edit changes must invalidate asynchronous plan results and preserve recoverable sessions.
5. Local endpoints must reject arbitrary file requests, cross-origin mutation, oversized input and invalid JSON.

## Task1: planning core
**Files:** coc_advisor/planner.py; tests/test_planner.py.
**Consumes:** JSON session {schema_version,mode,town_hall,army_confirmed,scene_confirmed,center,army,annotations} with normalized image geometry. Unit fields {id,name,count,level,role,domain}; annotation fields {id,kind,x,y,w,h}.
**Produces:** analyze(session) -> JSON {status,issues,candidates,unknowns,success_probability:null,planning_ms}; each candidate includes clock, entry, cost, steps and reserves.
- [x] Write real-behavior tests for valid/missing inputs, finite bounds, IDs/enums, legal points, quantity conservation, empty/mixed armies and directional defense costs; run RED.
- [x] Implement validation and bounded entry ranking; run GREEN.
- [x] Keep spells/cleanup reserved for manual decisions; no simulated pathing or damage.

## Task2: local app boundary
**Files:** coc_advisor/server.py, __main__.py, web/index.html, web/app.js, web/style.css; tests/test_server.py.
**Produces:** GET explicit assets and POST /api/plan; start via python -m coc_advisor. Actual HTTP integration tests cover request limits, JSON/errors, origins and asset allowlist.
- [x] Write server integration tests and run RED.
- [x] Implement server and screenshot-first UI with demo, annotation tools, army editor, confirmation, candidate overlay, undo and session export/import.
- [x] Run tests and check JavaScript syntax.

## Task3: usable launch and verification
**Files:** start.cmd, README.md, .gitignore, HANDOVER.md.
- [x] Launch locally; exercise demo->plans, screenshot/import editing, missing-input feedback and session roundtrip in the browser.
- [x] Inspect UI at desktop and narrow widths, keyboard controls and fresh-state invalidation.
- [x] One fresh reviewer inspects the whole milestone; resolve material findings with regression tests.
- [x] Record actual tests/limitations and replace the authoritative root handover.
