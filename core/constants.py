from enum import Enum
from typing import Final

CURRENT_CONTRACT_VERSION: Final[str] = "1.0"

class Severity(Enum):
    LOW = "info" # Informational/Inventory
    MED = "visibility/config" # Configuration/Visibility gap (e.g., missing permissions)
    HIGH = "op_impact" # Operational impact/Exploitable vulnerability
    CRITICAL = "money/legal_risk" # Immediate Financial, Legal, or Reputational risk
