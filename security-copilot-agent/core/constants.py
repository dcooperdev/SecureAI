from enum import Enum

CURRENT_CONTRACT_VERSION = "1.0"

class Severity(Enum):
    LOW = "info"
    MED = "visibility/config"
    HIGH = "op_impact"
    CRITICAL = "money/legal_risk"
