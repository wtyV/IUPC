# Figure and Table Plan v0

This file maps paper-ready figure/table numbers to generated result files.

## Figures

| Paper ID | Title | Source file | Main message |
|---|---|---|---|
| Fig. 1 | Wenchang launch azimuth geometry | `../results/figures/launch_geometry.svg` | Eastward launch maximizes rotation gain; minimum inclination is close to Wenchang latitude. |
| Fig. 2 | Two-launch LEO rendezvous architecture | `figures/fig2_architecture.svg` | Two CZ-10 launches place two cargo modules in LEO; docking is followed by combined TLI. |
| Fig. 3 | LEO rendezvous phasing estimate | `../results/figures/rendezvous_plan.svg` | A nearby phasing orbit can produce rendezvous within about 18-75 h with tens of m/s delta-v. |
| Fig. 4 | TLI delta-v versus parking altitude | `../results/figures/tli_delta_v.svg` | LEO-to-TLI delta-v is about 3.1 km/s over common parking altitudes. |
| Fig. 5 | TLI mass budget | `../results/figures/tli_mass_budget.svg` | The combined LEO stack mass remains within a plausible two-launch LEO wet-mass envelope. |
| Fig. 6 | ECI ascent altitude and inertial speed | `../results/figures/ascent_eci_altitude_speed.svg` | Tuned ascent reaches near-LEO altitude and speed. |
| Fig. 7 | Ascent mass and dynamic pressure | `../results/figures/ascent_mass_q.svg` | Shows stage mass decrease and max dynamic pressure scale. |
| Fig. 8 | Two-launch versus three-launch reliability | `../results/figures/mission_reliability.svg` | Three launches improve reliability but are treated as an extension, not the baseline. |
| Fig. 9 | Engine-cluster sensitivity | `../results/figures/engine_cluster_reliability.svg` | Large engine clusters are sensitive to single-engine reliability assumptions. |
| Fig. 10 | Full two-launch reliability chain | `../results/figures/mission_chain_reliability.svg` | Adding rendezvous and TLI reliability reduces total mission reliability below `R_launch^2`. |
| Fig. 11 | Rendezvous and TLI sensitivity | `../results/figures/mission_chain_sensitivity.svg` | The mission is sensitive to in-orbit operation reliability assumptions. |
| Fig. 12 | Optimization scores | `../results/figures/optimization_scores.svg` | Coarse grid search identifies workable pitch and rendezvous candidates. |

## Tables

| Paper ID | Title | Source file | Main message |
|---|---|---|---|
| Table 1 | Problem interpretation and assumptions | `../docs/assumptions_and_sources.md` | Defines modular 40 t cargo and LEO rendezvous interpretation. |
| Table 2 | Architecture comparison | `../results/tables/architecture_summary.csv` | Single direct launch rejected; two-launch LEO rendezvous selected. |
| Table 3 | LEO rendezvous plan | `../results/tables/rendezvous_plan.csv` | Baseline 300 km target and 260 km phasing orbit example. |
| Table 4 | TLI delta-v budget | `../results/tables/delta_v_budget.csv` | 300 km LEO TLI delta-v is about 3.108 km/s. |
| Table 5 | Nominal TLI mass budget | `../results/tables/tli_mass_budget.csv` | Nominal initial LEO stack is about 96.9 t. |
| Table 6 | ECI ascent terminal state | `../results/tables/baseline_summary.json` | Tuned ECI terminal state: about 306.9 km and 7.723 km/s. |
| Table 7 | Gravity model comparison | `../results/tables/gravity_model_comparison.csv` | J2 changes terminal altitude by about -2.27 km in the proxy model. |
| Table 8 | Reliability sweep | `../results/tables/reliability_sweep.csv` | Shows two-launch and three-launch reliability trends. |
| Table 9 | Full reliability chain | `../results/tables/mission_chain_reliability.csv` | Baseline chain reliability is about 0.871 when `R_launch=0.95`. |
| Table 10 | Rendezvous/TLI reliability sensitivity | `../results/tables/mission_chain_sensitivity.csv` | Reliability ranges from about 0.797 to 0.893 over the scanned in-orbit reliability assumptions. |
| Table 11 | Optimization summary | `../results/tables/optimization_summary.csv` | Best ECI pitch candidate is `pitch_end_time=305 s`, `final_pitch=10 deg`, `shape=1.4`. |

## Draft-Specific Figure

Fig. 2 is stored in this paper draft folder because it is a hand-authored architecture schematic rather than a numerical output from `run_baseline.py`.
