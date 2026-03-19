from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import pandas as pd


class ComponentType(Enum):
    TITLE = "Title"
    TEXT_BLOCK = "Text"
    TABLE = "Table"


@dataclass
class ReportComponent:
    type: ComponentType
    label: str
    text: str = ""
    dataframe: Optional[pd.DataFrame] = field(default=None, repr=False)
