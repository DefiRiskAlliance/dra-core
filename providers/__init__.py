"""HTTP-backed DRA rater adapters."""

from .aave_defaults import AaveDefaultsRater
from .base import RaterBase
from .defipunkd import DefiPunkdRater
from .defiscan import DefiscanRater
from .euler_defaults import EulerDefaultsRater
from .fluid_defaults import FluidDefaultsRater
from .lido_defaults import LidoDefaultsRater
from .mellow_defaults import MellowDefaultsRater
from .philidor import PhilidorRater
from .pharos import PharosRater
from .rocketpool_defaults import RocketPoolDefaultsRater
from .staking_rewards import StakingRewardsRater
from .vaultscan import VaultscanRater
from .webacy import WebacyRater
from .xerberus import XerberusRater
from .xerberus_pools import XerberusPoolsRater
from .yearn import YearnCurationRater

__all__ = [
    "AaveDefaultsRater",
    "DefiPunkdRater",
    "DefiscanRater",
    "EulerDefaultsRater",
    "FluidDefaultsRater",
    "LidoDefaultsRater",
    "MellowDefaultsRater",
    "PhilidorRater",
    "PharosRater",
    "RaterBase",
    "RocketPoolDefaultsRater",
    "StakingRewardsRater",
    "VaultscanRater",
    "WebacyRater",
    "XerberusPoolsRater",
    "XerberusRater",
    "YearnCurationRater",
]
