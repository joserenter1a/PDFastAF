import pathlib

from model.report_config import ReportConfig
from model.report_document import ReportDocument

THIS_DIRECTORY = pathlib.Path(__file__).parent


class PDFGenerator:
    def __init__(self):
        self.output_path = THIS_DIRECTORY / "buf.pdf"
        self._document = ReportDocument()

    def generate(self, config: ReportConfig):
        self._document.build(config, self.output_path)
