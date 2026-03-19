import pathlib
import pandas
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QVBoxLayout,
    QPlainTextEdit,
)
from PyQt6 import uic, QtCore
from PyQt6.QtCore import Qt, QSize, QTimer

from model.component import ComponentType, ReportComponent
from model.report_config import ReportConfig
from controller.pdf_generator import PDFGenerator
from view.widgets.component_widget import ComponentWidget

THIS_DIRECTORY = pathlib.Path(__file__).parent

_SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


class DropList(QListWidget):
    fileDropped = QtCore.pyqtSignal(pathlib.Path)
    reordered = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.model().rowsMoved.connect(self._enforce_title_pin)

    # ------------------------------------------------------------------ drag
    def dragEnterEvent(self, event):
        if event.source() is self or event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.source() is self:
            super().dragMoveEvent(event)  # preserves drop-indicator rendering
        elif event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.source() is self:
            super().dropEvent(event)  # Qt handles the internal move
        elif event.mimeData().hasUrls():
            path = pathlib.Path(event.mimeData().urls()[0].toLocalFile())
            if path.suffix.lower() in _SUPPORTED_EXTENSIONS:
                event.setDropAction(Qt.DropAction.CopyAction)
                event.accept()
                self.fileDropped.emit(path)
            else:
                event.ignore()

    # --------------------------------------------------- component management
    def add_component(self, component: ReportComponent):
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, component)
        widget = ComponentWidget(component)
        item.setSizeHint(QSize(-1, 36))
        if component.type == ComponentType.TITLE:
            self.insertItem(0, item)
        else:
            self.addItem(item)
        self.setItemWidget(item, widget)

    def update_component(self, component: ReportComponent):
        """Refresh the widget for an already-present component (e.g. title text changed)."""
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.ItemDataRole.UserRole) is component:
                widget = ComponentWidget(component)
                item.setSizeHint(QSize(-1, 36))
                self.setItemWidget(item, widget)
                return

    def ordered_components(self) -> list[ReportComponent]:
        return [
            self.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.count())
        ]

    # ---------------------------------------------------------- title pinning
    def _enforce_title_pin(self):
        for i in range(self.count()):
            item = self.item(i)
            comp = item.data(Qt.ItemDataRole.UserRole)
            if comp and comp.type == ComponentType.TITLE and i != 0:
                taken = self.takeItem(i)
                self.insertItem(0, taken)
                widget = ComponentWidget(comp)
                taken.setSizeHint(QSize(-1, 36))
                self.setItemWidget(taken, widget)
                break
        self.reordered.emit()


class ReportCreator(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(THIS_DIRECTORY.parent / "view" / "ui" / "report.ui", self)
        self.dragframe = self.findChild(QFrame, "dragframe")
        self.previewframe = self.findChild(QFrame, "previewframe")
        self.preview_layout = self.findChild(QVBoxLayout, "previewlayout")
        self.drag_layout = self.findChild(QVBoxLayout, "draglayout")
        self.title_edit = self.findChild(QLineEdit, "title_edit")
        self.text_block_edit = self.findChild(QPlainTextEdit, "text_block_edit")

        self.drop_list = DropList(self)
        self.preview = QWebEngineView()
        settings = self.preview.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        self.preview.loadFinished.connect(self._close_pdf_sidebar)
        self.preview.load(QtCore.QUrl.fromLocalFile(str(THIS_DIRECTORY / "buf.pdf")))

        self.preview_layout.addWidget(self.preview)
        self.drag_layout.addWidget(self.drop_list)

        self._config = ReportConfig()
        self._generator = PDFGenerator()
        self._generator.generate(self._config)

        self._editing_component: ReportComponent | None = None

        self.title_edit.returnPressed.connect(self._on_title_return)
        self.text_block_edit.setPlaceholderText("Type text block… Ctrl+Return to add")
        self.text_block_edit.installEventFilter(self)
        self.drop_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.drop_list.fileDropped.connect(self._on_file_dropped)
        self.drop_list.reordered.connect(self._rebuild_and_regenerate)

    # ------------------------------------------------------------------ events
    def eventFilter(self, obj, event):
        if (
            obj is self.text_block_edit
            and event.type() == QtCore.QEvent.Type.KeyPress
            and event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self._on_text_block_submit()
            return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------ slots
    def _on_title_return(self):
        text = self.title_edit.text().strip()
        if not text:
            return

        # Find existing title component and update it, or add a new one
        for comp in self.drop_list.ordered_components():
            if comp.type == ComponentType.TITLE:
                comp.text = text
                comp.label = text
                self.drop_list.update_component(comp)
                self._rebuild_and_regenerate()
                return

        component = ReportComponent(type=ComponentType.TITLE, label=text, text=text)
        self.drop_list.add_component(component)
        self._rebuild_and_regenerate()

    def _on_item_double_clicked(self, item: QListWidgetItem):
        comp = item.data(Qt.ItemDataRole.UserRole)
        if comp and comp.type == ComponentType.TEXT_BLOCK:
            self._editing_component = comp
            self.text_block_edit.setPlainText(comp.text)
            self.text_block_edit.setFocus()

    def _on_text_block_submit(self):
        text = self.text_block_edit.toPlainText().strip()
        if not text:
            return
        label = (text[:28] + "…") if len(text) > 28 else text
        if self._editing_component is not None:
            self._editing_component.text = text
            self._editing_component.label = label
            self.drop_list.update_component(self._editing_component)
            self._editing_component = None
        else:
            component = ReportComponent(type=ComponentType.TEXT_BLOCK, label=label, text=text)
            self.drop_list.add_component(component)
        self.text_block_edit.clear()
        self._rebuild_and_regenerate()

    def _on_file_dropped(self, path: pathlib.Path):
        if path.suffix.lower() == ".csv":
            df = pandas.read_csv(path)
        else:
            df = pandas.read_excel(path)
        component = ReportComponent(
            type=ComponentType.TABLE,
            label=path.name,
            dataframe=df,
        )
        self.drop_list.add_component(component)
        self._rebuild_and_regenerate()

    def _rebuild_and_regenerate(self):
        self._config.components = self.drop_list.ordered_components()
        self._generator.generate(self._config)
        self.preview.reload()

    # ----------------------------------------------------------------- close
    def closeEvent(self, event):
        for name in ("buf.pdf", "buf.csv"):
            f = THIS_DIRECTORY / name
            if f.exists():
                f.unlink()
        self._generator.generate(ReportConfig())
        super().closeEvent(event)

    # ---------------------------------------------------------- PDF sidebar
    def _close_pdf_sidebar(self, ok=True):
        if ok:
            QTimer.singleShot(200, self._run_close_sidebar_js)

    def _run_close_sidebar_js(self):
        self.preview.page().runJavaScript("""
            (function() {
                const viewer = document.querySelector('pdf-viewer');
                if (!viewer || !viewer.shadowRoot) return;
                const sidenav = viewer.shadowRoot.querySelector('viewer-pdf-sidenav');
                if (!sidenav) return;
                if (sidenav.hasAttribute('opened')) {
                    const toggle = viewer.shadowRoot.querySelector('#sidenavToggle');
                    if (toggle) toggle.click();
                }
            })();
        """)
