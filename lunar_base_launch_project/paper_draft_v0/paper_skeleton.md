# Paper Skeleton v0

Working title:

```text
A Two-Launch Long March 10 Architecture for Delivering 40 t Modular Lunar Base Cargo to an Earth-Moon Transfer Orbit
```

## Abstract placeholder

Draft later. Must include:

- A single Long March 10 cannot directly deliver 40 t to TLI under public 27 t TLI capability.
- The 40 t lunar-base cargo is treated as modular raw material.
- Baseline architecture: two Long March 10 launches, each sending about 20 t cargo plus interface elements to LEO.
- The two modules rendezvous and dock in LEO, then the combined stack performs TLI.
- Reliability is modeled as `R_total = R_launch^2 R_rendezvous R_TLI`.
- Main numerical values: 300 km LEO TLI delta-v about 3.108 km/s; nominal LEO stack mass about 96.9 t; ECI ascent terminal altitude about 306.9 km.

## 1. Restatement of the Problem

Purpose:

- Explain the task in our own words.
- State that the goal is Earth-Moon transfer orbit, not lunar landing.
- State that 40 t is interpreted as total modular cargo.

Figures/tables:

- Table 1: Problem interpretation and main assumptions.

## 2. Vehicle and Mission Assumptions

Purpose:

- Explain why Long March 10 is selected.
- Separate public parameters from modeling assumptions.
- Explain Wenchang launch site.
- Explain reference to China's two-launch crewed lunar plan as an architecture analogy.

Figures/tables:

- Table 2: Long March 10 and Starship comparison.
- Table 3: Public values and assumed values.
- Fig. 1: Wenchang launch azimuth and rotation gain.

## 3. Mission Architecture

Purpose:

- Compare four architectures:
  - A: single direct TLI, rejected.
  - B: two launches, LEO rendezvous, combined TLI, baseline.
  - C: three-launch 2-out-of-3 reliability extension.
  - D: single-body 40 t LEO assembly backup.
- Explain why Architecture B is selected.

Figures/tables:

- Fig. 2: Two-launch LEO rendezvous architecture schematic.
- Table 4: Architecture comparison.

## 4. LEO Rendezvous and Docking Model

Purpose:

- Describe the phasing-orbit model.
- Define target orbit, phasing orbit, relative drift rate and wait time.
- Present the baseline 300 km target / 260 km phasing example.

Figures/tables:

- Fig. 3: LEO rendezvous phasing estimate.
- Table 5: Rendezvous plan and delta-v.

## 5. Earth-Moon Transfer Model

Purpose:

- Derive the Hohmann-style TLI estimate.
- Present TLI delta-v versus LEO altitude.
- Present the mass budget for the combined TLI stack.

Figures/tables:

- Fig. 4: TLI delta-v versus LEO altitude.
- Fig. 5: TLI mass budget versus Isp and structural fraction.
- Table 6: Nominal TLI mass budget.

## 6. Ascent Trajectory Model

Purpose:

- Describe the 2D proxy ascent model.
- Describe the ECI/J2 point-mass model.
- Show tuned pitch program and terminal state.
- Compare spherical gravity and J2.

Figures/tables:

- Fig. 6: ECI ascent altitude and inertial speed.
- Fig. 7: Ascent mass and dynamic pressure.
- Table 7: Tuned ECI ascent terminal state.
- Table 8: Gravity model comparison.

## 7. Reliability Model

Purpose:

- Explain engine-cluster reliability.
- Explain two-launch mission reliability.
- Explain full mission chain reliability:

```text
R_total = R_launch^2 R_rendezvous R_TLI
```

- Show sensitivity to launch, rendezvous and TLI reliability.

Figures/tables:

- Fig. 8: Two-launch versus three-launch mission reliability.
- Fig. 9: Engine-cluster sensitivity.
- Fig. 10: Full reliability chain versus launch reliability.
- Fig. 11: Rendezvous and TLI reliability sensitivity.
- Table 9: Reliability summary.

## 8. Optimization

Purpose:

- Explain coarse grid search.
- Present optimized ECI pitch parameters.
- Present rendezvous candidate ranking.

Figures/tables:

- Fig. 12: Optimization score comparison.
- Table 10: Optimization summary.

## 9. Strengths and Weaknesses

Strengths:

- Uses public Long March 10 TLI capability conservatively.
- Converts 40 t cargo into a modular two-launch logistics problem.
- Uses LEO rendezvous to reduce single-launch burden.
- Includes reliability, mass budget, ascent, transfer and sensitivity analysis.

Weaknesses:

- Long March 10 detailed staging data are not fully public.
- ECI ascent model remains a point-mass proxy.
- TLI model is Hohmann-style and does not use full ephemeris.
- Rendezvous model is first-order phasing only.

## 10. Conclusion placeholder

Draft later. Must include:

- Baseline recommendation: two Long March 10 launches, 20 t cargo module each, LEO rendezvous and combined TLI.
- Single launch is rejected because 40 t exceeds public 27 t TLI capability.
- Key numbers: TLI delta-v 3.108 km/s, LEO stack 96.9 t, nominal reliability chain 0.871 for selected assumptions.

## References placeholder

Use the sources already recorded in:

```text
../docs/assumptions_and_sources.md
```

