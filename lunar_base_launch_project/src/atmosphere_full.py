"""Complete Standard Atmosphere Model (杨炳蔚 教材标准大气表).

Implements the full layered standard atmosphere with:
  - Geopotential height conversion
  - Temperature gradient layers (polytropic)
  - Isothermal layers
  - Hydrostatic pressure and density via ideal gas law
  - Speed of sound

Atmospheric layers (up to 86 km geopotential, extended to 120 km):
  Layer 0:  0-11 km,  T = T0 + L0*(H-H0),  L0 = -6.5 K/km  (troposphere)
  Layer 1: 11-20 km,  isothermal, T = 216.65 K             (tropopause)
  Layer 2: 20-32 km,  T = T1 + L2*(H-H1),  L2 = +1.0 K/km  (stratosphere)
  Layer 3: 32-47 km,  T = T2 + L3*(H-H2),  L3 = +2.8 K/km  (stratosphere)
  Layer 4: 47-51 km,  isothermal, T = 270.65 K             (stratopause)
  Layer 5: 51-71 km,  T = T4 + L5*(H-H4),  L5 = -2.8 K/km  (mesosphere)
  Layer 6: 71-84.852 km, T = T5 + L6*(H-H5), L6 = -2.0 K/km (mesosphere)
  Layer 7: 84.852-92 km, isothermal, T = 186.87 K           (mesopause)
  Layer 8: 92-120 km,  T increases (thermosphere start)

Reference: U.S. Standard Atmosphere 1976, 杨炳蔚《航空航天概论》标准大气表
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

# ── Physical constants ──────────────────────────────────────────────────────

G0 = 9.80665            # standard gravity, m/s^2
R_AIR = 287.05287       # gas constant for dry air, J/(kg·K)
GAMMA_AIR = 1.4         # ratio of specific heats
R_EARTH = 6371000.0     # Earth mean radius, m

# Sea-level reference
P0 = 101325.0           # Pa (sea-level pressure)
T0 = 288.15             # K  (sea-level temperature)
RHO0 = 1.225            # kg/m^3 (sea-level density)


@dataclass(frozen=True)
class AtmoLayer:
    """One layer of the standard atmosphere."""
    h_base_m: float         # geopotential height of lower boundary, m
    h_top_m: float          # geopotential height of upper boundary, m
    T_base_K: float         # temperature at lower boundary, K
    lapse_rate_K_per_m: float  # dT/dH, 0 for isothermal


# Layer definitions (geopotential heights)
_STANDARD_LAYERS: list[AtmoLayer] = [
    AtmoLayer(0.0,        11000.0,   288.15,  -0.0065),   # troposphere
    AtmoLayer(11000.0,    20000.0,   216.65,   0.0),       # tropopause
    AtmoLayer(20000.0,    32000.0,   216.65,   0.001),     # lower stratosphere
    AtmoLayer(32000.0,    47000.0,   228.65,   0.0028),    # upper stratosphere
    AtmoLayer(47000.0,    51000.0,   270.65,   0.0),       # stratopause
    AtmoLayer(51000.0,    71000.0,   270.65,  -0.0028),    # mesosphere
    AtmoLayer(71000.0,    84852.0,   214.65,  -0.002),     # upper mesosphere
    AtmoLayer(84852.0,    92000.0,   186.87,   0.0),       # mesopause
    AtmoLayer(92000.0,   120000.0,   186.87,   0.004),     # lower thermosphere
]


@dataclass(frozen=True)
class AtmoState:
    """Complete atmospheric state at a point."""
    altitude_geometric_m: float
    altitude_geopotential_m: float
    temperature_K: float
    pressure_Pa: float
    density_kg_m3: float
    speed_of_sound_m_s: float
    dynamic_viscosity_Pa_s: float


def geometric_to_geopotential(h_m: float) -> float:
    """Convert geometric altitude to geopotential altitude.

    H = R_E * h / (R_E + h)

    This accounts for the decrease of gravity with altitude.
    """
    if h_m <= 0.0:
        return 0.0
    return R_EARTH * h_m / (R_EARTH + h_m)


def geopotential_to_geometric(H_m: float) -> float:
    """Convert geopotential altitude to geometric altitude."""
    if H_m <= 0.0:
        return 0.0
    return R_EARTH * H_m / (R_EARTH - H_m)


def _find_layer(geopot_height_m: float) -> AtmoLayer:
    """Find the atmospheric layer containing the given geopotential height."""
    for layer in _STANDARD_LAYERS:
        if layer.h_base_m <= geopot_height_m < layer.h_top_m:
            return layer
    # Above defined layers: use last layer extrapolation
    last = _STANDARD_LAYERS[-1]
    if geopot_height_m >= last.h_top_m:
        return last
    # Below sea level
    return _STANDARD_LAYERS[0]


def _layer_state_at_height(layer: AtmoLayer, H_m: float) -> tuple[float, float, float]:
    """Compute T, p, rho at geopotential height H_m within given layer.

    Uses hydrostatic equilibrium and ideal gas law:

    For L != 0 (polytropic):
        T(H) = T_base + L * (H - h_base)
        p(H) = p_base * [T_base / T(H)] ^ (g0 / (R * L))
        rho(H) = p(H) / (R * T(H))

    For L = 0 (isothermal):
        T(H) = T_base
        p(H) = p_base * exp[-g0 * (H - h_base) / (R * T_base)]
        rho(H) = p(H) / (R * T_base)

    where g0 uses standard gravity for geopotential height.
    """
    dH = H_m - layer.h_base_m
    T = layer.T_base_K + layer.lapse_rate_K_per_m * dH

    # Get base pressure by integrating from sea level
    # We compute it recursively; for efficiency, this function
    # uses the recursive scheme from the bottom up
    p_base = _pressure_at_geopotential(layer.h_base_m)
    L = layer.lapse_rate_K_per_m

    if abs(L) > 1e-12:
        # Polytropic layer
        if T <= 0:
            T = 1e-6
        exponent = G0 / (R_AIR * L)
        p = p_base * (layer.T_base_K / T) ** exponent
    else:
        # Isothermal layer
        if T <= 0:
            T = 1e-6
        p = p_base * math.exp(-G0 * dH / (R_AIR * T))

    rho = p / (R_AIR * T)
    return T, p, rho


# Cache for base pressures to avoid recomputation
_BASE_PRESSURES: dict[float, float] = {0.0: P0}


def _pressure_at_geopotential(H_m: float) -> float:
    """Compute pressure at a geopotential height by walking up layers."""
    if H_m <= 0.0:
        return P0
    if H_m in _BASE_PRESSURES:
        return _BASE_PRESSURES[H_m]

    # Find the layer below and compute
    p = P0
    H_current = 0.0
    for layer in _STANDARD_LAYERS:
        if H_m <= layer.h_base_m:
            break
        # Integrate through this layer up to the next boundary
        H_next = min(H_m, layer.h_top_m)
        dH = H_next - layer.h_base_m
        L = layer.lapse_rate_K_per_m
        T_base = layer.T_base_K
        T_next = T_base + L * (H_next - layer.h_base_m)

        if abs(L) > 1e-12:
            if T_next <= 0:
                T_next = 1e-6
            exponent = G0 / (R_AIR * L)
            p = p * (T_base / T_next) ** exponent
        else:
            if T_base <= 0:
                T_base = 1e-6
            p = p * math.exp(-G0 * dH / (R_AIR * T_base))
        H_current = H_next

    _BASE_PRESSURES[H_m] = p
    return p


def standard_atmosphere(altitude_geometric_m: float) -> AtmoState:
    """Return full atmospheric state at a given geometric altitude.

    Implements the complete 杨炳蔚 standard atmosphere model using:
    - Geopotential height conversion (accounts for gravity variation)
    - Hydrostatic equation dp/dH = -rho * g0
    - Ideal gas law p = rho * R * T
    - Layer-wise temperature gradient model

    For h > 120 km: density decays exponentially as an extension.
    For h < 0: sea-level values are returned.
    """
    if altitude_geometric_m < 0.0:
        # Sea-level condition
        return AtmoState(
            altitude_geometric_m=0.0,
            altitude_geopotential_m=0.0,
            temperature_K=T0,
            pressure_Pa=P0,
            density_kg_m3=RHO0,
            speed_of_sound_m_s=math.sqrt(GAMMA_AIR * R_AIR * T0),
            dynamic_viscosity_Pa_s=_sutherland_viscosity(T0),
        )

    H = geometric_to_geopotential(altitude_geometric_m)

    if H >= 120000.0:
        # Extended thermosphere: exponential decay from 120 km
        # Based on mass spectrometer / incoherent scatter radar data
        # Density at 120 km ~ 2.44e-8 kg/m^3
        T_ext = 380.0  # K at 120 km, increasing
        H_120 = geometric_to_geopotential(120000.0)
        # Exponential scale height ~ 15 km
        H_scale = 15000.0
        rho_120 = 2.44e-8
        rho = rho_120 * math.exp(-(H - H_120) / H_scale)
        p = rho * R_AIR * T_ext
        return AtmoState(
            altitude_geometric_m=altitude_geometric_m,
            altitude_geopotential_m=H,
            temperature_K=T_ext,
            pressure_Pa=p,
            density_kg_m3=rho,
            speed_of_sound_m_s=math.sqrt(GAMMA_AIR * R_AIR * T_ext),
            dynamic_viscosity_Pa_s=_sutherland_viscosity(T_ext),
        )

    try:
        T, p, rho = _layer_state_at_height(_find_layer(H), H)
    except (ValueError, ZeroDivisionError):
        # Fallback: zero density at very high altitude
        rho = 0.0
        p = 0.0
        T = 186.87

    # Speed of sound: a = sqrt(gamma * R * T)
    sos = math.sqrt(GAMMA_AIR * R_AIR * max(T, 1e-6))

    return AtmoState(
        altitude_geometric_m=altitude_geometric_m,
        altitude_geopotential_m=H,
        temperature_K=T,
        pressure_Pa=p,
        density_kg_m3=rho,
        speed_of_sound_m_s=sos,
        dynamic_viscosity_Pa_s=_sutherland_viscosity(T),
    )


def density_kg_m3_full(h_m: float) -> float:
    """Convenience function: return density at geometric altitude."""
    return standard_atmosphere(h_m).density_kg_m3


def speed_of_sound_m_s(h_m: float) -> float:
    """Convenience function: return speed of sound at geometric altitude."""
    return standard_atmosphere(h_m).speed_of_sound_m_s


def temperature_K(h_m: float) -> float:
    """Convenience function: return temperature at geometric altitude."""
    return standard_atmosphere(h_m).temperature_K


def pressure_Pa(h_m: float) -> float:
    """Convenience function: return pressure at geometric altitude."""
    return standard_atmosphere(h_m).pressure_Pa


# ── Sutherland viscosity formula ────────────────────────────────────────────

def _sutherland_viscosity(T_K: float) -> float:
    """Sutherland's formula for dynamic viscosity of air.

    mu = mu_ref * (T / T_ref)^(3/2) * (T_ref + S) / (T + S)

    where mu_ref = 1.716e-5 Pa·s at T_ref = 273.15 K, S = 110.4 K.
    """
    mu_ref = 1.716e-5
    T_ref = 273.15
    S = 110.4
    T = max(T_K, 1e-6)
    return mu_ref * (T / T_ref) ** 1.5 * (T_ref + S) / (T + S)


# ── Wind model ──────────────────────────────────────────────────────────────

def horizontal_wind_m_s(latitude_deg: float, altitude_geometric_m: float) -> tuple[float, float]:
    """Simplified seasonal/latitudinal wind model.

    Returns (eastward_component_m_s, northward_component_m_s).

    Based on the Horizontal Wind Model (HWM) simplified for mid-latitude
    launch site applications. At Wenchang (19.6°N), the predominant
    upper-level winds are easterly trade winds near the tropopause and
    westerly in the stratosphere.

    This is a simplified model for trajectory sensitivity analysis.
    Full HWM14 should be used for operational analysis.
    """
    h_km = altitude_geometric_m / 1000.0
    lat = latitude_deg

    if h_km < 0.5:
        return (0.0, 0.0)

    if h_km <= 18.0:
        # Troposphere: easterly trades, increasing with altitude
        # Peak ~ 25 m/s easterly near tropopause
        eastward = -5.0 - 15.0 * (h_km / 18.0)
        northward = 2.0 * math.sin(math.pi * h_km / 18.0)  # small meridional
    elif h_km <= 35.0:
        # Lower stratosphere: reverses to westerly
        frac = (h_km - 18.0) / 17.0
        eastward = -20.0 + 35.0 * frac  # transitions from -20 to +15
        northward = 1.0 * math.sin(math.pi * frac)
    elif h_km <= 60.0:
        # Upper stratosphere / lower mesosphere
        eastward = 15.0 - 40.0 * ((h_km - 35.0) / 25.0)  # back to easterly
        northward = -3.0 * math.sin(math.pi * (h_km - 35.0) / 25.0)
    else:
        # Mesosphere and above: wind decays
        eastward = -25.0 * math.exp(-(h_km - 60.0) / 20.0)
        northward = 0.0

    return (eastward, northward)
