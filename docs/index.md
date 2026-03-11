---
layout: default
title: Anametric STEER
---

<div class="hero">
  <div class="hero-logos">
    <img src="images/Ana_color_horiz_V2.svg" alt="Anametric" class="hero-logo-anametric">
    <span class="hero-logo-divider">×</span>
    <img src="images/steer-blue-logo.png" alt="STEER" class="hero-logo-steer">
  </div>
  <h1>Anametric <strong>STEER</strong></h1>
  <p class="subtitle">Statistical Testing of Entropy Evaluation Report</p>
  <p class="subtitle" style="font-size:0.9rem; margin-top:4px; color:var(--text-muted);">
    A comprehensive framework for evaluating random number generators and entropy sources through rigorous statistical &amp; causal testing.
  </p>
  <div class="hero-links">
    <a href="#getting-started" class="btn-primary">Get Started</a>
    <a href="STEER_GUI_User_Guide" class="btn-outline">GUI Guide</a>
    <a href="https://github.com/mathornton01/steer-framework" class="btn-outline" target="_blank">View on GitHub</a>
  </div>
</div>

---

## Overview

Anametric STEER improves the accessibility, usability, and scalability of statistical entropy testing. It implements **76 statistical tests** across four major test batteries, all accessible through both a command-line interface and a modern graphical application.

<div class="battery-grid">
  <div class="battery-card">
    <h4>NIST STS</h4>
    <p><span class="count">15</span> tests</p>
    <p>SP 800-22 Rev 1a — the worldwide standard for RNG certification.</p>
  </div>
  <div class="battery-card">
    <h4>Diehard / Dieharder</h4>
    <p><span class="count">28</span> tests</p>
    <p>Marsaglia, Bauer (DAB), and Brown (RGB) battery suites.</p>
  </div>
  <div class="battery-card">
    <h4>TestU01 Crush</h4>
    <p><span class="count">31</span> tests</p>
    <p>Pierre L'Ecuyer's stringent test library.</p>
  </div>
  <div class="battery-card featured">
    <h4>Causal Model Tests</h4>
    <p><span class="count">2</span> tests</p>
    <p>Pearl &amp; Rubin causal inference — <em>an Anametric innovation.</em></p>
  </div>
</div>

<div class="causal-highlight">
  <h3><span class="badge">Featured</span> Causal Inference Test Battery</h3>
  <p>
    Anametric STEER uniquely integrates <strong>causal inference methodology</strong> into entropy evaluation — going beyond correlation to probe whether deviations from randomness arise from genuine structural patterns.
  </p>
  <p>
    <strong>Pearl Causal Model (PCM)</strong> — Uses structural causal modeling to test whether observed bit patterns exhibit directional causal dependencies that a truly random source should not produce.
  </p>
  <p>
    <strong>Rubin Causal Model (RCM)</strong> — Applies the potential-outcomes framework to evaluate whether subpopulations of a bitstream show treatment-effect-like deviations, indicating non-random structure.
  </p>
  <p style="margin-top:16px; font-size:0.9rem; color:var(--text-muted);">
    These tests complement traditional statistical batteries by detecting failure modes that frequency- and pattern-based tests may miss.
  </p>
</div>

---

## GUI Application

The Anametric STEER GUI provides a complete graphical interface for selecting tests, configuring parameters, executing test runs, and reviewing results — all without touching the command line.

### Main Window

<p align="center">
  <img src="screenshots/gui-main-window.svg" alt="STEER GUI Main Window" width="900"><br>
  <em>The main Anametric STEER GUI window with test selection, parameter configuration, and results display.</em>
</p>

### Test Selection and Planning

Browse all 76 tests organized by battery. Select individual tests or entire batteries, configure parameters, and queue them for execution.

<p align="center">
  <img src="screenshots/gui-test-selection.svg" alt="Test Selection" width="900"><br>
  <em>Selecting tests from the NIST STS, Diehard, TestU01, and Causal Model batteries.</em>
</p>

### Parameter Configuration

Each test exposes configurable parameters — common settings like bitstream count, length, and significance level, plus test-specific parameters like dimension, block size, or tuple size.

<p align="center">
  <img src="screenshots/gui-parameters.svg" alt="Parameter Configuration" width="900"><br>
  <em>Configuring common and test-specific parameters for a planned test.</em>
</p>

### Test Execution

Run your test plan with real-time progress tracking. Tests execute sequentially with live output streaming to the log.

<p align="center">
  <img src="screenshots/gui-running.svg" alt="Test Execution" width="900"><br>
  <em>Test execution in progress with real-time progress tracking.</em>
</p>

### Results and Reporting

View results in a structured summary, drill into detailed hierarchical breakdowns, or examine the raw JSON report with syntax highlighting.

<p align="center">
  <img src="screenshots/gui-results-summary.svg" alt="Results Summary" width="900"><br>
  <em>Test results summary showing pass/fail evaluation and probability values.</em>
</p>

<p align="center">
  <img src="screenshots/gui-results-details.svg" alt="Results Details" width="900"><br>
  <em>Detailed hierarchical view of test configurations, calculations, and criteria.</em>
</p>

### Integrated Documentation

Browse comprehensive documentation for every test directly within the application — including mathematical basis, parameter descriptions, result interpretation, and recommendations.

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

### Causal Model Tests (2 tests) — <em style="color:var(--accent-gold);">Anametric Innovation</em>

Python-based tests applying causal inference methodology to entropy evaluation — a capability unique to Anametric STEER:

- **Pearl Causal Model (PCM)** — Structural causal modeling to detect directional dependencies in bitstreams that violate randomness assumptions
- **Rubin Causal Model (RCM)** — Potential outcomes framework to identify treatment-effect-like deviations across bitstream subpopulations

These tests detect failure modes that purely statistical batteries may miss, providing deeper insight into RNG quality.

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

Anametric STEER builds on foundational work by:

- **NIST** — Statistical Test Suite (SP 800-22 Rev 1a)
- **George Marsaglia** — Diehard Battery of Tests of Randomness
- **Robert G. Brown** — Dieharder: A Random Number Test Suite (RGB tests)
- **David Bauer** — Dieharder DAB test extensions
- **Pierre L'Ecuyer & Richard Simard** — TestU01 statistical testing library
