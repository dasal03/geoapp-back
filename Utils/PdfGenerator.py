import os
import pdfkit

LIBRARY_PATH = os.getenv("LIBRARY_PATH")


class PDFGenerator:
    """Class to generate PDF documents from HTML templates."""

    def __init__(self):
        """Initialize PDFGenerator with the path to wkhtmltopdf."""
        self.wkhtmltopdf_path = LIBRARY_PATH
        self.output_directory = "/temp"
        self.config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)

        # Ensure output directory exists
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

    def generate_pdf(
        self, template: str, output_pdf_name: str, content: dict
    ) -> str:
        """
        Generate a PDF file from the rendered HTML template.

        Args:
            template (str): The HTML template to render.
            output_pdf_name (str): The name of the output PDF file.
            content (dict): The data to render in the HTML template.

        Returns:
            str: The path to the generated PDF file.
        """
        try:
            # Render the HTML template with the content
            rendered_template = template.format(**content)

            # Ensure output path is correctly set
            pdf_path = os.path.join(self.output_directory, output_pdf_name)

            # Generate PDF from the rendered HTML string
            pdfkit.from_string(
                rendered_template, pdf_path, configuration=self.config
            )

            return pdf_path
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")
