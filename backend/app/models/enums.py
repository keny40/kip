from enum import Enum


class RaceStatus(str, Enum):
    scheduled = "scheduled"
    open = "open"
    finished = "finished"
    cancelled = "cancelled"


class PlayerStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    retired = "retired"


class EntryStatus(str, Enum):
    confirmed = "confirmed"
    reserve = "reserve"
    scratched = "scratched"


class ResultStatus(str, Enum):
    finished = "finished"
    disqualified = "disqualified"
    withdrawn = "withdrawn"
    did_not_finish = "did_not_finish"
