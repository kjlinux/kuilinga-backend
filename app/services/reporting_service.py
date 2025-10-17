import pandas as pd
from fastapi.responses import StreamingResponse
from weasyprint import HTML
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Any
from datetime import datetime

class ReportingService:
    """
    A service to handle the generation of reports in different formats (PDF, Excel, CSV).
    """

    def __init__(self, template_dir: str = "app/templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.env.globals['now'] = datetime.utcnow

    def _render_html(self, template_name: str, context: Dict[str, Any]) -> str:
        """Renders an HTML template with the given context."""
        template = self.env.get_template(template_name)
        return template.render(context)

    async def generate_pdf_from_html(
        self, template_name: str, context: Dict[str, Any], filename: str
    ) -> StreamingResponse:
        """
        Generates a PDF from an HTML template and returns it as a streaming response.
        """
        html_content = self._render_html(template_name, context)
        pdf_bytes = HTML(string=html_content).write_pdf()

        file_like = BytesIO(pdf_bytes)

        headers = {
            "Content-Disposition": f"attachment; filename={filename}"
        }
        return StreamingResponse(file_like, media_type="application/pdf", headers=headers)

    async def generate_excel(
        self, data: List[Dict[str, Any]], filename: str
    ) -> StreamingResponse:
        """
        Generates an Excel file from a list of dictionaries and returns it as a streaming response.
        """
        df = pd.DataFrame(data)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        output.seek(0)

        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        return StreamingResponse(output, headers=headers)

    async def generate_csv(
        self, data: List[Dict[str, Any]], filename: str
    ) -> StreamingResponse:
        """
        Generates a CSV file from a list of dictionaries and returns it as a streaming response.
        """
        df = pd.DataFrame(data)

        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv",
        }

        # To stream a text-based format, we need an iterator
        return StreamingResponse(output, headers=headers)

reporting_service = ReportingService()