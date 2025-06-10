"""

This module handles current system state, historical tracking, and validation
using the static thermal physics model.

"""

from typing import Optional, List, Tuple, Dict
from copy import deepcopy
import warnings
from ..thermal_model.heat_transfer_data import *
from ..thermal_model.heat_transfer import *