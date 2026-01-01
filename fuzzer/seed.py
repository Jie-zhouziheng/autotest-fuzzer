from dataclasses import dataclass, field
from typing import Set

@dataclass
class Seed:
    data: bytes
    execs: int = 0
    favored: bool = False
    crashed: bool = False
    coverage: Set[str] = field(default_factory=set)  # 模拟覆盖边集合

    def mark_favored(self):
        self.favored = True

    def mark_crash(self):
        self.crashed = True

    def __hash__(self):
        return hash(self.data)

    def __eq__(self, other):
        return isinstance(other, Seed) and self.data == other.data