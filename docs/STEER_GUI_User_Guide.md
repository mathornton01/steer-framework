<p style="text-align:center;"><img src="./images/steer-blue-logo.png" width="50%"></p>

## STEER Framework GUI User Guide

##### Version 1.0.0

### Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Launching the GUI](#launching-the-gui)
4. [Application Overview](#application-overview)
5. [Selecting an Entropy Source](#selecting-an-entropy-source)
6. [Browsing Available Tests](#browsing-available-tests)
7. [Building a Test Plan](#building-a-test-plan)
8. [Configuring Parameters](#configuring-parameters)
9. [Running Tests](#running-tests)
10. [Viewing Results](#viewing-results)
11. [Reviewing the Execution Log](#reviewing-the-execution-log)
12. [Browsing Test Documentation](#browsing-test-documentation)
13. [Window Management](#window-management)
14. [Keyboard and Mouse Reference](#keyboard-and-mouse-reference)
15. [Troubleshooting](#troubleshooting)

---

### Introduction

The STEER GUI provides a graphical interface for running statistical tests on entropy sources using the STEER (STandard Entropy Evaluation Report) Framework. It supports five test batteries:

- **NIST Statistical Test Suite (STS)** - 15 tests from the NIST SP 800-22 standard
- **Diehard / Dieharder Battery** - 28 tests (Marsaglia originals, DAB, and RGB extensions)
- **TestU01 Crush Battery** - 31 tests from Pierre L'Ecuyer's TestU01 library
- **AIS 20/31** - 9 BSI entropy certification tests (Procedure A and Procedure B)
- **Anametric Causal Model Tests** - 2 Python-based causal inference tests (Pearl and Rubin models)

The GUI allows you to select tests, configure parameters, execute test runs, view detailed results, and browse comprehensive documentation for every test — all from a single interface.

---

### Prerequisites

- **Python 3.10 or later**
- **PyQt6** (`pip install PyQt6>=6.7.0`)
- **Built STEER test binaries** (run `./build.sh` first, or use a platform installer)
- **On Windows:** WSL with Ubuntu 24.04 is required for executing C-based tests

---

### Launching the GUI

**From the command line:**

```bash
python src/steer-gui/main.py
```

**With an explicit framework root:**

```bash
python src/steer-gui/main.py --root /path/to/steer-framework
```

**Using a platform launcher** (created by the installer):

- **Windows:** Double-click `steer-gui.bat` or the desktop shortcut
- **Linux:** Run `steer-gui` from the terminal, or click the STEER Framework desktop entry
- **macOS:** Open `STEER Framework.app`, or run `steer-gui` from the terminal

On startup, the application displays an animated splash screen while initializing. It automatically locates the STEER framework directory by searching parent directories for `build_files/test_names.txt`. If automatic detection fails, a file dialog will prompt you to locate the framework root manually.

---

### Application Overview

The main window is divided into three columns separated by adjustable splitters:

```
+------------------------------------------------------------------+
| [Logo] STEER Framework                            [_] [□] [X]   |
+------------------------------------------------------------------+
| Entropy: [path/to/file.bin] [Browse]  Validation: [dropdown ▼]  |
+------------------------------------------------------------------+
|  Available Tests  |  Planned Analysis  |  Results / Log / Docs   |
|                   |                    |                          |
|  ▼ NIST (15)      |  Test 1 (1×1M)    |  [Results] [Log] [Docs] |
|    Frequency      |  Test 2 (1×1M)    |                          |
|    Block Freq.    |  Test 3 (1×1M)    |   (result content)       |
|    Runs           |                    |                          |
|    ...            | Parameters:        |                          |
|  ▼ Diehard (28)   |  Streams: [1    ] |                          |
|    Birthday...    |  Length:  [1000K ] |                          |
|    Parking Lot    |  Alpha:   [0.01  ] |                          |
|    ...            |  Report:  [full ▼] |                          |
|  ▼ TestU01 (31)   |                    |                          |
|    Serial Over    | [Apply to All]     |                          |
|    Close Pairs    |                    |                          |
|    ...            | [====RUN TESTS====]|                          |
+------------------------------------------------------------------+
| Ready · 74/77 tests available · 0 test(s) planned · /path/root  |
+------------------------------------------------------------------+
```

**Column 1 — Available Tests:** A tree view of all discovered tests, grouped by battery.

**Column 2 — Planned Analysis:** The tests you have queued for execution, with parameter controls below.

**Column 3 — Results / Log / Documentation:** Three tabs showing test results, the execution log, and comprehensive test documentation.

The **status bar** at the bottom shows the number of available/total tests, the count of planned tests, and the framework root path.

---

### Selecting an Entropy Source

Before running any tests, you must specify an entropy source — a binary file (`.bin`) containing the random data to be tested.

**Option A — Browse for a file:**
1. Click the **Browse** button next to the Entropy field.
2. A file dialog opens, defaulting to the `data/` directory in the framework root.
3. Select a `.bin` file and click Open.

**Option B — Use a validation data file:**
1. Click the **Validation** dropdown on the right side of the entropy bar.
2. Select one of the pre-installed validation files (e.g., `e.bin`, `pi.bin`, `sha1.bin`, `sqrt2.bin`, `sqrt3.bin`).
3. These are standard reference datasets for validating that tests produce expected results.

The selected file path appears in the Entropy field. Tests cannot be executed until an entropy source is selected.

---

### Browsing Available Tests

The left column shows all tests discovered from the framework, organized into collapsible category groups:

| Category | Count | Language | Description |
|----------|-------|----------|-------------|
| NIST Statistical Tests | 15 | C | NIST SP 800-22 standard tests |
| Diehard Tests | 28 | C | Marsaglia, DAB, and RGB statistical tests |
| TestU01 Tests | 31 | C | Pierre L'Ecuyer's Crush battery |
| Anametric Causal Tests | 2 | Python | Pearl and Rubin causal model tests |

Each test item shows its display name and a language indicator (**C** in gray or **Python** in orange).

**Grayed-out tests** indicate that the test executable has not been built yet. Hover over a grayed-out test to see the tooltip "Executable not built yet."

Tests marked with an asterisk (*) in the TestU01 category indicate tests that have a similar counterpart in the NIST STS battery.

**To select tests:**
- Click a single test to select it.
- Hold **Ctrl** and click to select multiple individual tests.
- Hold **Shift** and click to select a contiguous range.
- Use **Ctrl+A** to select all tests.

**To view documentation for a test:**
- Double-click any test to jump to its documentation in the Documentation tab.

---

### Building a Test Plan

The middle column is your test plan — the list of tests queued for execution.

**Adding tests to the plan:**
1. Select one or more tests in the Available Tests tree.
2. Click the **Add to Plan >>** button below the tree.
3. The selected tests appear in the Planned Analysis list with default parameters.

Each planned test shows a compact summary of its configuration:

```
Frequency (1 × 1M, alpha=0.01)
```

This indicates 1 stream of 1,000,000 bits with alpha = 0.01. Test-specific parameters are also shown when applicable (e.g., `size=256`).

**Removing tests from the plan:**
- Select one or more tests in the Planned Analysis list, then click **<< Remove**.
- Click **Clear All** to empty the entire plan.

**Plan management tips:**
- You can add the same test multiple times with different parameters.
- Tests execute in the order they appear in the plan.
- The plan is stored in memory only — it is not saved when the application closes.

---

### Configuring Parameters

When you select a test in the Planned Analysis list, the Parameters section below becomes active, showing "Editing: *Test Name*".

#### Common Parameters

All tests share these four parameters:

| Parameter | Control | Default | Range | Description |
|-----------|---------|---------|-------|-------------|
| **Streams** | Spin box | 1 | 1 – 10,000 | Number of bitstreams to test |
| **Length** | Spin box | 1,000,000 | 1,024 – 100,000,000 | Length of each bitstream in bits |
| **Alpha** | Decimal spin box | 0.01 | 0.0001 – 0.5 | Significance level for pass/fail |
| **Report** | Dropdown | full | full / standard / summary | Level of detail in the output report |

#### Test-Specific Parameters

Some tests expose additional parameters below the common ones. These appear automatically based on the selected test. For example:

- **3D Sphere** — "Num Points" (default 4000, range 100–50000)
- **Craps** — "Num Games" (default 200000, range 1000–1000000)
- **RGB Minimum Distance** — "Dimension" (default 2) and "Num Points" (default 4000)
- **Close Pairs** — "Points" (default 8000) and "Dimension" (default 2)
- **Random Walk** — "Walk Length" (default 1000)

Changes to parameters take effect immediately — the plan item label updates to reflect the new values.

#### Causal Model Bit Position Configuration

When a **Pearl Causal Model** or **Rubin Causal Model** test is selected in the plan, a **"Configure Bit Positions…"** button appears below the common parameters. Clicking it opens a pop-out dialog where you assign each bit position within a block to one of three roles:

| Role | Color | Purpose |
|------|-------|---------|
| **Treatment** | Cyan | Defines the treatment variable — blocks are grouped by treatment tuple |
| **Outcome** | Green | The measured outcome positions compared across groups |
| **Covariate** | Orange | Used only by Rubin for propensity score matching; ignored by Pearl |

Click any cell to cycle its role: **Treatment → Outcome → Covariate**.

The dialog also exposes model-specific parameters:

| Parameter | Models | Default | Description |
|-----------|--------|---------|-------------|
| **Block size** | Both | 6 | Subsequence length — the number of bit positions per block |
| **Alphabet size (k)** | Both | 3 | Number of discrete symbol levels (binary = 2, ternary = 3, etc.) |
| **State bits** | Pearl only | 2 | Sliding window length for the state-transition graph |
| **Null simulations** | Pearl only | 200 | Monte Carlo iterations for the empirical null distribution |

**Pearl methodology:** Groups blocks by treatment tuple, normalizes outcomes by treatment anchor via modular arithmetic, builds state-transition graphs per group, and computes pairwise Jaccard similarity. An empirical null distribution is simulated to derive the p-value.

**Rubin methodology:** Uses covariate positions for propensity score matching via multinomial logistic regression. Matched treatment-control pairs are compared by Hamming distance on outcome positions. The test statistic is the average mismatch proportion versus the null expectation $(1 - 1/k)$.

The plan label updates to show the assigned positions, e.g., `T=[0,1] O=[2,3,4,5]`.

#### Applying Parameters to All Tests

Click **Apply to All** to copy the current common parameters (Streams, Length, Alpha, Report Level) to every test in the plan. This does **not** affect test-specific parameters.

---

### Running Tests

1. Ensure an entropy source is selected (the Entropy field is not empty).
2. Ensure at least one test is in the Planned Analysis list.
3. Click the **RUN TESTS** button.

During execution:
- The **RUN TESTS** button is replaced by a **STOP** button.
- A **progress bar** appears showing completion percentage.
- A **progress label** shows "N of M tests complete."
- The **Log tab** automatically receives real-time output from each test.

Tests execute **sequentially** — one at a time, in plan order. Each test launches as a subprocess:
- On **Linux/macOS**, the test binary runs natively.
- On **Windows**, the test binary runs inside WSL (Ubuntu 24.04) with automatic path conversion.

**To cancel a test run:**
Click the **STOP** button. The currently running test will be terminated and remaining tests will be skipped. The log will show "[STOPPED] Test run cancelled by user."

When all tests complete, the progress label updates to "Done: N passed, M failed" and the Results tab displays the results.

---

### Viewing Results

After test execution, the **Results** tab shows three sub-tabs:

#### Summary Tab

For a **single test**, the summary shows:
- A large **evaluation badge** — PASS (green), FAIL (red), or INCONCLUSIVE (orange)
- **Test Name** and program details
- **Entropy Source** file path
- **Duration** of the test
- **Platform** (OS and architecture)
- Individual **probability values** with color-coded status indicators

For a **batch of tests**, the summary shows:
- Overall badge — "ALL PASSED" (green) or "N FAILED" (red)
- Stats line — "X passed, Y failed, Z total"
- Per-test rows with colored status dots and PASS/FAIL badges

#### Details Tab

A hierarchical tree view showing the full structure of the report:
- **Configuration** level — each configuration's evaluation
- **Test** level — each test's evaluation
- **Calculations** — probability values, chi-squared statistics, z-scores, etc.
- **Criteria** — individual pass/fail criteria with color coding

All nodes are expanded by default for easy browsing.

#### JSON Tab

The raw JSON report with syntax highlighting:
- **Keys** in blue/bold
- **Strings** in green
- **Numbers** in orange
- **Booleans/null** in orange/yellow

Click **Copy to Clipboard** to copy the full JSON for external use.

---

### Reviewing the Execution Log

The **Log** tab provides a detailed chronological record of the test run:

```
Running: Frequency
  [stdout from test binary]
Frequency: PASS
  Evaluation: pass

Running: Block Frequency
  [stdout from test binary]
Block Frequency: FAIL (exit code 1)
  Evaluation: fail

---
Batch complete: 1 passed, 1 failed out of 2 tests
```

The log uses a monospace font for readability. It auto-scrolls to the bottom as new output arrives. The log is cleared at the start of each new test run.

---

### Browsing Test Documentation

The **Documentation** tab provides comprehensive reference material for every test in the framework.

**Left sidebar:** A scrollable list of tests grouped by category:
- NIST Statistical Test Suite
- Diehard Statistical Test Battery
- Dieharder DAB Tests
- Dieharder RGB Tests
- TestU01 Crush Battery
- Causal Model Tests

**Right content area:** Click any test to view its full documentation:
- **Summary** — One-line description in a highlighted box
- **Description** — Detailed explanation of what the test does
- **Mathematical Basis** — Formulas and statistical methodology (monospace formatting)
- **Parameters** — Table of configurable parameters with descriptions
- **Interpretation** — What PASS and FAIL mean for this specific test
- **Recommendations** — Guidance on when and how to use the test
- **Example Applications** — Real-world use cases
- **Program Name** — The executable name for CLI usage

You can also access documentation by **double-clicking** any test in the Available Tests tree, which automatically switches to the Documentation tab and scrolls to that test.

---

### Window Management

The STEER GUI uses a custom frameless window with these controls:

| Control | Location | Action |
|---------|----------|--------|
| **Minimize** (─) | Top-right | Minimizes the window |
| **Maximize** (□) | Top-right | Toggles between maximized and normal size |
| **Close** (✕) | Top-right | Closes the application |
| **Title bar drag** | Top bar | Click and drag to move the window |
| **Title bar double-click** | Top bar | Toggles maximize state |
| **Resize grip** | Bottom-right corner | Drag to resize the window |
| **Column splitters** | Between columns | Drag to resize column widths |

The window position and size are saved automatically and restored on next launch.

---

### Keyboard and Mouse Reference

| Action | Shortcut |
|--------|----------|
| Select single test | Click |
| Select multiple tests | Ctrl + Click |
| Select range of tests | Shift + Click |
| Select all tests | Ctrl + A |
| View test documentation | Double-click test in Available Tests |
| Move window | Drag title bar |
| Toggle maximize | Double-click title bar |
| Resize window | Drag bottom-right corner |
| Adjust column widths | Drag splitter handles |
| Copy JSON report | Click "Copy to Clipboard" in JSON tab |

---

### Troubleshooting

**"Executable not built yet" on all tests**

The C test binaries have not been compiled. Run the build script first:
```bash
./build.sh --build
```
On Windows, this must be run inside WSL:
```cmd
wsl -d Ubuntu-24.04 -- bash build.sh --build
```

**No entropy source files in the Validation dropdown**

Ensure the `data/validation/nist-sts/` directory exists in the framework root and contains `.bin` files. These are created during the build or packaging process.

**Tests fail immediately with exit code -1**

This typically indicates that the entropy source file is too small for the requested bitstream length. Try reducing the **Length** parameter or using a larger entropy file.

**On Windows, tests hang or fail to start**

Verify that WSL is installed and Ubuntu-24.04 is available:
```cmd
wsl --list --verbose
```
If Ubuntu-24.04 is not listed, install it:
```cmd
wsl --install -d Ubuntu-24.04
```

**GUI fails to start with "No module named PyQt6"**

Install the required Python dependency:
```bash
pip install PyQt6>=6.7.0
```

**Framework root not detected automatically**

Use the `--root` argument to specify the path explicitly:
```bash
python src/steer-gui/main.py --root /path/to/steer-framework
```

**Parameter changes not reflected**

Ensure you click on the test in the Planned Analysis list before editing parameters. Changes apply only to the currently selected planned test. Use **Apply to All** to propagate common parameters to all planned tests.

---

### Output Files

Test execution creates output files in the `results/gui/` directory:

```
results/gui/
├── params/
│   └── nist_sts_frequency_test_params_20260310_143022.json
└── nist_sts_frequency_test_20260310_143022.json
```

- **Parameter files** (`params/`) contain the JSON parameter sets sent to each test.
- **Report files** contain the full JSON test report with results, evaluations, and metrics.

These files persist after the application closes and can be reviewed later or processed by external tools.

---

### Test Battery Quick Reference

#### NIST STS Tests (15)

| Test | Description |
|------|-------------|
| Frequency | Proportion of ones vs zeros in entire sequence |
| Block Frequency | Proportion of ones within M-bit blocks |
| Runs | Oscillation between ones and zeros |
| Longest Run of Ones | Longest run of ones within M-bit blocks |
| Rank | Rank of disjoint sub-matrices |
| Discrete Fourier Transform | Peak heights in spectral domain |
| Non-overlapping Template | Occurrences of aperiodic templates |
| Overlapping Template | Occurrences of m-bit run of ones |
| Universal Statistical | Compressibility via Maurer's test |
| Linear Complexity | Length of LFSR for sequence generation |
| Serial | Frequency of all 2^m m-bit patterns |
| Approximate Entropy | Similar to Serial, compares block frequencies |
| Cumulative Sums | Maximal excursion of random walk |
| Random Excursions | Cycles in cumulative sum random walk |
| Random Excursions Variant | Deviations from expected visits in walk |

#### Diehard Tests (28)

| Test | Parameters | Notes |
|------|------------|-------|
| Birthday Spacings | — | |
| Parking Lot | — | |
| Minimum Distance | — | |
| Squeeze | — | |
| Overlapping Permutations | — | |
| Rank 32x32 | — | Binary matrix rank |
| Rank 6x8 | — | Binary matrix rank |
| Bitstream | — | Missing 20-bit words |
| OPSO | — | Suspect (Dieharder warning) |
| OQSO | — | Suspect (Dieharder warning) |
| DNA | — | Suspect (Dieharder warning) |
| Count 1s (Stream) | — | Byte popcount patterns |
| Count 1s (Byte) | — | Byte selection variant |
| 3D Sphere | Num Points | Minimum distance in 3D cube |
| Sums | — | DEPRECATED — DO NOT USE |
| Runs | — | Ascending/descending runs |
| Craps | Num Games | Craps game simulation |
| Marsaglia-Tsang GCD | Num Pairs | GCD value distribution |
| DAB Bytedistrib | — | Byte distribution |
| DAB DCT | Block Size | Frequency-domain analysis |
| DAB Filltree | Tree Depth | Tree filling (unreliable) |
| DAB Filltree2 | Tree Depth | Improved tree filling |
| DAB Monobit2 | Block Size | Most effective Dieharder test |
| RGB Bitdist | N-tuple | Bit pattern distribution |
| RGB Minimum Distance | Dimension, Num Points | Multi-dimensional min distance |
| RGB Permutations | Tuple Size | Non-overlapping permutations |
| RGB Lagged Sum | Lag | Suspect — false positives |
| RGB KS Test | — | Kolmogorov-Smirnov uniformity |

#### TestU01 Crush Tests (31)

| Test | Parameters |
|------|------------|
| Serial Over | Dimension, Bits/Value |
| Close Pairs | Points, Dimension |
| Collision Over | Bits/Window, Num Values |
| GCD | Num Pairs |
| Linear Complexity | Block Size |
| Appearance Spacings | — |
| Sum Collector | Group Size |
| Savir2 | Group Size |
| Coupon Collector | Num Coupons |
| Weight Distribution | Group Size |
| Close Pairs Bit Match | Num Bits |
| Simplified Poker | Hand Size, Categories |
| Gap | Lower, Upper |
| Collision Permut | Tuple Size |
| Max of T | Group Size, Num Bins |
| Run | Max Run Length |
| Permutation | Tuple Size |
| Sample Product | Group Size |
| Sample Mean | Group Size |
| Sample Correlation | — |
| Random Walk | Walk Length |
| Hamming Weight | Block Size |
| Hamming Correlation | Block Size |
| Hamming Independence | Block Size |
| String Run | Max Run Length |
| Autocorrelation | Lag |
| Periods in Strings | Block Size |
| Longest Head Run | Block Size |
| Fourier Spectral | — |
| Entropy Discretization | Block Size |
| Multinomial Bits Over | Tuple Size |
