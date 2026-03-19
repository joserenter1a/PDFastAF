from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

from model.component import ReportComponent, ComponentType

_BADGE_STYLE: dict[ComponentType, tuple[str, str]] = {
    ComponentType.TITLE:      ("#4a90d9", "white"),
    ComponentType.TEXT_BLOCK: ("#7b68ee", "white"),
    ComponentType.TABLE:      ("#2e8b57", "white"),
}


class ComponentWidget(QWidget):
    def __init__(self, component: ReportComponent, parent=None):
        super().__init__(parent)
        self.component = component

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        bg, fg = _BADGE_STYLE.get(component.type, ("#888", "white"))
        badge = QLabel(component.type.value)
        badge.setFixedWidth(46)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background:{bg}; color:{fg}; border-radius:3px;"
            f" padding:2px 4px; font-size:10px; font-weight:bold;"
        )

        label = QLabel(component.label)
        label.setStyleSheet("font-size:12px;")

        layout.addWidget(badge)
        layout.addWidget(label, 1)
