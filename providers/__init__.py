"""HTTP-backed DRA rater adapters."""

from .aave_defaults import AaveDefaultsRater
from .base import RaterBase
from .defipunkd import DefiPunkdRater
from .defiscan import DefiscanRater
from .philidor import PhilidorRater
from .pharos import PharosRater
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
    "PhilidorRater",
    "PharosRater",
    "RaterBase",
    "StakingRewardsRater",
    "VaultscanRater",
    "WebacyRater",
    "XerberusPoolsRater",
    "XerberusRater",
    "YearnCurationRater",
]
