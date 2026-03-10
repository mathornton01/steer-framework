---
layout: default
title: STEER Framework
---

<p align="center">
  <img src="images/steer-blue-logo.png" alt="STEER Framework Logo" width="320">
</p>

<h2 align="center">Statistical Testing of Entropy Evaluation Report</h2>

<p align="center">
  A comprehensive, open-source framework for evaluating the quality of random number generators and entropy sources through rigorous statistical testing.
</p>

<p align="center">
  <a href="https://github.com/mathornton01/steer-framework">View on GitHub</a> &middot;
  <a href="#getting-started">Getting Started</a> &middot;
  <a href="STEER_User_Guide">CLI Guide</a> &middot;
  <a href="STEER_GUI_User_Guide">GUI Guide</a>
</p>

---

## Overview

The STEER Framework improves the accessibility, usability, and scalability of statistical entropy testing. It implements **76 statistical tests** across four major test batteries, all accessible through both a command-line interface and a modern graphical application.

| Battery | Tests | Origin |
|---------|------:|--------|
| **NIST Statistical Test Suite** | 15 | NIST SP 800-22 Rev 1a |
| **Diehard / Dieharder** | 28 | George Marsaglia, David Bauer, Robert G. Brown |
| **TestU01 Crush** | 31 | Pierre L'Ecuyer |
| **Causal Model Tests** | 2 | Pearl and Rubin causal inference models |

---

## GUI Application

The STEER GUI provides a complete graphical interface for selecting tests, configuring parameters, executing test runs, and reviewing results — all without touching the command line.

### Main Window

<!-- SCREENSHOT PLACEHOLDER: Replace with actual screenshot of the main STEER GUI window showing the three-column layout with Available Tests, Planned Analysis, and Results tabs -->
<p align="center">
  <img src="screenshots/gui-main-window.svg" alt="STEER GUI Main Window" width="900"><br>
  <em>The main STEER GUI window with test selection, parameter configuration, and results display.</em>
</p>

### Test Selection and Planning

Browse all 76 tests organized by battery. Select individual tests or entire batteries, configure parameters, and queue them for execution.

<!-- SCREENSHOT PLACEHOLDER: Replace with actual screenshot showing the Available Tests tree expanded with tests selected and added to the Planned Analysis list -->
<p align="center">
  <img src="screenshots/gui-test-selection.svg" alt="Test Selection" width="900"><br>
  <em>Selecting tests from the NIST STS, Diehard, and TestU01 batteries.</em>
</p>

### Parameter Configuration

Each test exposes configurable parameters — common settings like bitstream count, length, and significance level, plus test-specific parameters like dimension, block size, or tuple size.

<!-- SCREENSHOT PLACEHOLDER: Replace with actual screenshot showing the parameter editing panel with both common and test-specific parameters visible -->
<p align="center">
  <img src="screenshots/gui-parameters.svg" alt="Parameter Configuration" width="900"><br>
  <em>Configuring common and test-specific parameters for a planned test.</em>
</p>

### Test Execution

Run your test plan with real-time progress tracking. Tests execute sequentially with live output streaming to the log.

<!-- SCREENSHOT PLACEHOLDER: Replace with actual screenshot showing a test run in progress with the progress bar and log output visible -->
<p align="center">
  <img src="screenshots/gui-running.svg" alt="Test Execution" width="900"><br>
  <em>Test execution in progress with real-time progress tracking.</em>
</p>

### Results and Reporting

View results in a structured summary, drill into detailed hierarchical breakdowns, or examine the raw JSON report with syntax highlighting.

<!-- SCREENSHOT PLACEHOLDER: Replace with actual screenshot showing the Results tab with the Summary sub-tab displaying a PASS result with probability values -->
<p align="center">
  <img src="screenshots/gui-results-summary.svg" alt="Results Summary" width="900"><br>
  <em>Test results summary showing pass/fail evaluation and probability values.</em>
</p>

<!-- SCREENSHOT PLACEHOLDER: Replace with actual screenshot showing the Results tab with the Details sub-tab displaying the hierarchical tree of configurations, tests, and criteria -->
<p align="center">
  <img src="screenshots/gui-results-details.svg" alt="Results Details" width="900"><br>
  <em>Detailed hierarchical view of test configurations, calculations, and criteria.</em>
</p>

### Integrated Documentation

Browse comprehensive documentation for every test directly within the application — including mathematical basis, parameter descriptions, result interpretation, and recommendations.

<!-- SCREENSHOT PLACEHOLDER: Replace with actual screenshot showing the Documentation tab with a test selected in the left sidebar and its full documentation displayed on the right -->
<p align="center">
  <img src="screenshots/gui-documentation.svg" alt="Documentation Browser" width="900"><br>
  <em>Built-in documentation browser with mathematical details and usage guidance.</em>
</p>

---

## Test Batteries

### NIST Statistical Test Suite (15 tests)

The foundational battery from [NIST SP 800-22](https://csrc.nist.gov/publications/detail/sp/800-22/rev-1a/final), used worldwide for certifying random number generators:

- Frequency (Monobit), Block Frequency, Runs, Longest Run of Ones
- Rank, Discrete Fourier Transform, Non-overlapping Template Matching
- Overlapping Template Matching, Universal Statistical, Linear Complexity
- Serial, Approximate Entropy, Cumulative Sums
- Random Excursions, Random Excursions Variant

### Diehard / Dieharder Battery (28 tests)

The complete Dieharder battery combining George Marsaglia's original Diehard tests with extensions by David Bauer (DAB) and Robert G. Brown (RGB):

**Original Marsaglia Tests:** Birthday Spacings, Parking Lot, Minimum Distance, Squeeze, Overlapping Permutations, Rank 32x32, Rank 6x8, Bitstream, OPSO, OQSO, DNA, Count 1s (Stream & Byte), 3D Sphere, Sums, Runs, Craps, Marsaglia-Tsang GCD

**DAB Extensions:** Bytedistrib, DCT, Filltree, Filltree2, Monobit2

**RGB Extensions:** Bitdist, Minimum Distance, Permutations, Lagged Sum, KS Test

> **Suite Warnings:** Some tests carry warnings from the original Dieharder suite — OPSO, OQSO, and DNA are marked as *suspect*; Sums is *deprecated*; RGB Lagged Sum is known for *false positives*; DAB Filltree is marked as *potentially unreliable*.

### TestU01 Crush Battery (31 tests)

Tests from Pierre L'Ecuyer's TestU01 library, widely regarded as one of the most stringent test suites available:

Serial Over, Close Pairs, Collision Over, GCD, Linear Complexity, Appearance Spacings, Sum Collector, Savir2, Coupon Collector, Weight Distribution, Close Pairs Bit Match, Simplified Poker, Gap, Collision Permut, Max of T, Run, Permutation, Sample Product, Sample Mean, Sample Correlation, Random Walk, Hamming Weight/Correlation/Independence, String Run, Autocorrelation, Periods in Strings, Longest Head Run, Fourier Spectral, Entropy Discretization, Multinomial Bits Over

### Causal Model Tests (2 tests)

Python-based tests using causal inference methodology:

- **Pearl Causal Model** — Structural causal model analysis
- **Rubin Causal Model** — Potential outcomes framework analysis

---

## Getting Started

### Quick Install

**Windows:**
```cmd
cd steer-framework\installers
install_windows.bat
```

**Linux:**
```bash
cd steer-framework/installers
bash install_linux.sh
```

**macOS:**
```bash
cd steer-framework/installers
bash install_macos.sh
```

The installer handles Python dependencies, C compiler setup, building all 74 test binaries, and creating GUI launcher shortcuts.

### Build from Source

```bash
git clone https://github.com/mathornton01/steer-framework.git
cd steer-framework
bash build.sh
```

### Launch the GUI

```bash
python src/steer-gui/main.py
```

Or use the launcher created by the installer (`steer-gui` on Linux/macOS, `steer-gui.bat` on Windows).

### Run Tests via CLI

```bash
# Run a single test
./bin/linux/x64/Debug/nist_sts_frequency_test \
  -l full -e data/random.bin \
  -p test/validation/nist-sts/frequency/parameters_pi.json \
  -r results/frequency_report.json -R

# Run a test schedule
./bin/linux/x64/Debug/steer_test_scheduler \
  -s schedules/validation_test_schedule.json
```

---

## Architecture

```
steer-framework/
├── src/
│   ├── nist-sts/          # 15 NIST STS test implementations (C)
│   ├── diehard/           # 28 Diehard test implementations (C)
│   ├── testu01/           # 31 TestU01 test implementations (C)
│   ├── python-tests/      # 2 causal model tests (Python)
│   └── steer-gui/         # PyQt6 graphical application
├── include/               # STEER C library headers
├── docs/                  # User Guide, Developer Guide, GUI Guide
├── build_files/           # Test name registries and build templates
├── installers/            # Platform-specific installers
└── sdk/python/            # Python SDK for test integration
```

Each C test implements the STEER test shell API with 7 standard callbacks (`GetTestInfo`, `GetParametersInfo`, `InitTest`, `GetConfigurationCount`, `SetReport`, `ExecuteTest`, `FinalizeTest`) ensuring consistent parameter handling, reporting, and evaluation across all batteries.

---

## Documentation

- **[CLI User Guide](STEER_User_Guide)** — Command-line tools, build system, test scheduling, and validation
- **[GUI User Guide](STEER_GUI_User_Guide)** — Graphical application walkthrough with all features
- **[Developer Guide](STEER_Developer_Guide)** — Adding custom tests, framework internals, and API reference

---

## Platform Support

| Platform | CLI Tests | GUI | Installer |
|----------|-----------|-----|-----------|
| **Linux** (x64, arm64) | Native | Native | `install_linux.sh` |
| **macOS** (x64, arm64) | Native | Native | `install_macos.sh` |
| **Windows** (x64) | Via WSL | Native | `install_windows.bat` |

---

## Credits

The STEER Framework builds on foundational work by:

- **NIST** — Statistical Test Suite (SP 800-22 Rev 1a)
- **George Marsaglia** — Diehard Battery of Tests of Randomness
- **Robert G. Brown** — Dieharder: A Random Number Test Suite (RGB tests)
- **David Bauer** — Dieharder DAB test extensions
- **Pierre L'Ecuyer & Richard Simard** — TestU01 statistical testing library

<p align="center">
  <img src="images/anametric-logo.png" alt="Anametric" height="60">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/ddics-logo.png" alt="Darwin Deason Institute for Cyber Security" height="60">
</p>

<p align="center">
  <a href="https://github.com/mathornton01/steer-framework">GitHub</a> &middot;
  <a href="https://github.com/mathornton01/steer-framework/issues">Issues</a> &middot;
  MIT License
</p>
