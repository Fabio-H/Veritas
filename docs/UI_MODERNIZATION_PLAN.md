# UI Modernization Plan — Veritas

> **English** · [Português](pt-BR/UI_MODERNIZATION_PLAN.md)
>
> Approved for execution across future sessions. Goal: a real-product feel
> (fluidity, feedback, responsiveness) while keeping the PySide6 stack — no
> rewriting in web tech. Each phase ends with green tests +
> `scripts/check_gui_layout.py` passing.

## Phase 1 — Motion (animations)

1. **Animated sidebar**: replace the abrupt `setFixedWidth()` with a
   `QPropertyAnimation` on the width (~200 ms, `OutCubic` easing), with label
   fades via `QGraphicsOpacityEffect` so the text doesn't "jump" when
   collapsing/expanding.
2. **Smooth layer accordion**: animate the body height when expanding a decode
   layer, instead of showing/hiding all at once.
3. **Page transition**: short crossfade when switching Quick Decode ↔ History
   in the `QStackedWidget`.

## Phase 2 — Feedback and micro-interactions

4. **"Copied!" toast**: a discreet floating notification (~1.5 s with fade)
   when copying an IOC or the final text, instead of no feedback.
5. **Decode button with embedded progress**: a "decoding" state inside the
   button itself (text + indicator), replacing the separate progress bar.
6. **Depth**: a soft shadow on cards (`QGraphicsDropShadowEffect`) and a more
   visible focus highlight on inputs.

## Phase 3 — Real responsiveness

7. **Auto-wrap**: stat pills and the action row reflow onto two lines
   (FlowLayout) on narrow windows, instead of squeezing.
8. **DPI scaling**: revisit fixed pt/px sizes for high-density monitors and
   the Windows scaling mode.
9. **IOC table**: smarter column resizing at small widths (priority to the
   Value column).

## Phase 4 — Real-app feel

10. **Window memory**: remember size, position and sidebar state between
    sessions (`QSettings`).
11. **Single instance**: launching the shortcut while the app is open brings
    the window to the front instead of opening a second copy.
12. **Distribution**: updated windowed PyInstaller build + eventually an
    installer (Inno Setup) with a Start Menu shortcut.

## Status (v0.5.0 — 2026-07-02)

| Item | Status |
|------|--------|
| 1. Animated sidebar | ✅ v0.5.0 |
| 2. Smooth accordion | ✅ v0.5.0 |
| 3. Page transition | ✅ v0.5.0 (crossfade) |
| 4. "Copied!" toast | ✅ v0.5.0 (+ exports) |
| 5. Decode button with embedded progress | kept as-is (text "Decoding..." + bar) |
| 6. Card shadows | ❌ intentionally dropped: Qt allows one graphics effect per widget (conflicts with the crossfade) and rasterizes the whole card on each repaint, hurting scroll |
| 7. Auto-wrap (pills) | ✅ v0.5.0 (FlowLayout) |
| 8. DPI scaling | partial (PassThrough already active); revisit on a real high-DPI monitor |
| 9. Responsive IOC table | ✅ v0.5.0 (Confidence auto-size) |
| 10. Window memory | ✅ v0.5.0 (QSettings) |
| 11. Single instance | ✅ v0.5.0 (QLocalServer) |
| 12. Windowed build + installer | ⏳ next (PyInstaller configured; Inno Setup pending) |

Extras from the UX research (outside the original plan), also in v0.5.0:
dark native title bar on Windows (Microsoft checklist: a native window should
match the theme) and a **Copy all IOCs** button (SOC guideline: from alert to
action in seconds, no copying row by row).

Items delivered before this plan: launching without a console window
(v0.4.0, `[project.gui-scripts]` + `Veritas.lnk` shortcut).
