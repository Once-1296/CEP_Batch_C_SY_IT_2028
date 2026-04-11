from dataclasses import dataclass, field
from typing import List


@dataclass
class Patient:
    id: int
    name: str
    phone: str
    current_medications: List[str] = field(default_factory=list)
    current_conditions: List[str] = field(default_factory=list)
    added_by: str = ""
