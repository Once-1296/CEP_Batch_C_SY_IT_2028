from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    username: str
    role: str
