# Report Creator

A desktop application for building customizable PDF reports by dragging in tabular data files (CSV, Excel) and arranging them visually. Reports are rendered in real time using ReportLab and previewed inline.

---

## Architecture: MVC

The project follows a strict **Model-View-Controller** pattern, reflected directly in the directory structure.

```
report_creator/
├── main.py                  # Entry point
├── model/                   # Data and report state
│   ├── data_source.py       # Wraps a pandas DataFrame + file metadata
│   ├── report_config.py     # Report settings: title, page size, margins, styles
│   └── report_document.py   # Builds the ReportLab document from config + sources
├── controller/              # Business logic and signal wiring
│   ├── controller.py        # Main window controller (ReportCreator)
│   ├── pdf_generator.py     # Drives report_document → writes buf.pdf
│   └── file_handler.py      # File I/O, format detection, buffer management
└── view/                    # Qt UI definitions and custom widgets
    ├── ui/
    │   └── report.ui        # Main window layout (Qt Designer)
    └── widgets/
        ├── drop_list.py     # Drag-and-drop target (QListWidget subclass)
        ├── component_row.py # A single draggable report component in the sidebar
        └── preview.py       # QWebEngineView wrapper for PDF display
```

---

## Layers

### Model
Pure data — no Qt, no I/O side effects.

| Class | Responsibility |
|---|---|
| `DataSource` | Holds a `pd.DataFrame` plus metadata (filename, display label, column visibility/order) |
| `ReportConfig` | Stores report-level settings: title, author, page size, margins, table style presets |
| `ReportDocument` | Takes a `ReportConfig` + ordered list of `DataSource` objects and produces a ReportLab `SimpleDocTemplate` with `Table` flowables |

### Controller
Owns Qt signals/slots and drives model updates.

| Class | Responsibility |
|---|---|
| `ReportCreator` | Main `QWidget` — wires together widgets, reacts to user actions, triggers PDF regeneration |
| `PDFGenerator` | Calls `ReportDocument.build()` and writes output to `buf.pdf` |
| `FileHandler` | Detects CSV vs Excel, reads via pandas, returns `DataSource` objects |

### View
Qt widgets and `.ui` files — no business logic.

| Class | Responsibility |
|---|---|
| `DropList` | `QListWidget` subclass that accepts CSV/Excel file drops, emits `fileDropped(Path)` |
| `ComponentRow` | Represents one data source in the sidebar — drag handle, label, remove button |
| `preview.py` | Thin wrapper around `QWebEngineView` that reloads `buf.pdf` on demand |

---

## Data Flow

```
User drops file
    │
    ▼
DropList.dropEvent()
    │  emits fileDropped(path)
    ▼
ReportCreator (controller)
    │  calls FileHandler.load(path)
    ▼
FileHandler → pandas.read_csv / read_excel
    │  returns DataSource
    ▼
ReportCreator appends DataSource to ordered list
    │  adds ComponentRow to sidebar
    │  triggers regeneration
    ▼
PDFGenerator
    │  calls ReportDocument.build(config, sources)
    ▼
ReportLab → writes buf.pdf
    │
    ▼
QWebEngineView reloads buf.pdf → live preview updated
```

---

## Key Design Decisions

**MVC with thin views** — Views emit signals and display state. All logic lives in controller or model. This keeps `.ui` files and widget subclasses easy to replace or extend without touching business logic.

**Buffer file pattern** — `buf.pdf` acts as the live preview artifact. The PDF generator always overwrites it, and the viewer reloads it after each write. This avoids in-memory PDF streaming complexity with `QWebEngineView`.

**Ordered component list** — The sidebar shows report components as a reorderable list (`QListWidget` or `QListView`). The controller maintains a matching ordered list of `DataSource` objects. Reordering the list triggers regeneration.

**Incremental regeneration** — Any change (title edit, reorder, file add/remove) triggers a full PDF rebuild. ReportLab builds are fast enough for typical report sizes that this is acceptable without debouncing at first. A short debounce timer can be added later.

---

## Supported Input Formats

| Format | Extension | Reader |
|---|---|---|
| CSV | `.csv` | `pandas.read_csv` |
| Excel | `.xlsx`, `.xls` | `pandas.read_excel` |

---

## Dependencies

| Package | Role |
|---|---|
| PyQt6 | GUI framework |
| PyQt6-WebEngine | Inline PDF preview |
| pandas | Tabular data loading |
| reportlab | PDF generation |
| openpyxl | Excel file reading (pandas backend) |

---

## Development Setup

```bash
uv sync
uv run main.py
```

Requires Python 3.13+.

---

## Roadmap

- [ ] CSV drag-and-drop → table in PDF (core loop)
- [ ] Excel support
- [ ] Report title input → PDF header
- [ ] Reorderable component list in sidebar
- [ ] Table style customization (fonts, colors, column widths)
- [ ] Text block component (freeform paragraphs)
- [ ] Page size and orientation settings
- [ ] Export to named file (Save As)
- [ ] Multi-table layout (side by side)
