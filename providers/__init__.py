"""HTTP-backed DRA rater adapters."""

from .aave_defaults import AaveDefaultsRater
from .base import RaterBase
from .defiscan import DefiscanRater
from .philidor import PhilidorRater
from .pharos import PharosRater
from .staking_rewards import StakingRewardsRater
from .vaultscan import VaultscanRater
from .webacy import WebacyRater
from .xerberus import XerberusRater
from .yearn import YearnCurationRater

__all__ = [
    "AaveDefaultsRater",
    "DefiscanRater",
    "PhilidorRater",
    "PharosRater",
    "RaterBase",
    "StakingRewardsRater",
    "VaultscanRater",
    "WebacyRater",
    "XerberusRater",
    "YearnCurationRater",
]
