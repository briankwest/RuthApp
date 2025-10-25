"""
PDF Generation Service
Adapted from mailer.py for generating professional letters for #10 windowed envelopes
"""
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from io import BytesIO

from pydantic import BaseModel, Field, field_validator
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from PIL import Image
from reportlab.lib.utils import ImageReader

from app.core.config import settings
from app.models.letter import LetterRecipient

logger = logging.getLogger(__name__)


# ============================================================================
# PDF CONFIGURATION MODELS (Pydantic)
# ============================================================================

class Margins(BaseModel):
    """Page margin configuration"""
    top: float = 1.25
    bottom: float = 1.25
    left: float = 1.25
    right: float = 1.25


class AddressPosition(BaseModel):
    """Address positioning for window alignment"""
    x: float
    y: float
    width: float
    height: Optional[float] = None


class DatePosition(BaseModel):
    """Date positioning configuration"""
    x: float = 0.5
    y: float = 1.75
    alignment: str = Field(default="left", pattern="^(left|center|right)$")


class Positioning(BaseModel):
    """Element positioning configuration"""
    unit: str = "inches"
    margins: Margins = Margins()
    return_address: AddressPosition = AddressPosition(x=0.5, y=0.625, width=3.5, height=1.0)
    recipient_address: AddressPosition = AddressPosition(x=0.75, y=2.0625, width=4.0, height=1.125)
    date_position: DatePosition = DatePosition(x=4.875, y=1.7, alignment="right")
    body_start_y: float = 3.67


class Formatting(BaseModel):
    """Text formatting configuration"""
    font_family: str = "Times-Roman"
    font_size: int = 11
    line_spacing: float = 1.5
    paragraph_spacing: int = 12
    justify_body: bool = False
    indent_paragraphs: bool = True
    indent_size: float = 0.5


class FoldLineStyle(BaseModel):
    """Fold line style configuration"""
    line_length_mm: int = 4
    margin_offset_mm: int = 3
    color: str = "#CCCCCC"
    line_width: float = 0.5
    line_style: str = Field(default="solid", pattern="^(solid|dashed)$")


class FoldLines(BaseModel):
    """Fold lines configuration"""
    enabled: bool = True
    positions: List[float] = [3.67, 7.33]
    style: FoldLineStyle = FoldLineStyle()


class HeaderContent(BaseModel):
    """Header content configuration"""
    enabled: bool = True
    left: str = ""
    center: str = ""
    right: str = ""


class Header(BaseModel):
    """Header configuration"""
    page_1: HeaderContent = HeaderContent(enabled=False)
    subsequent: HeaderContent = HeaderContent()
    font_size: int = 10
    color: str = "#333333"
    line_below: bool = True


class Footer(BaseModel):
    """Footer configuration"""
    enabled: bool = True
    left: str = ""
    center: str = "Page {page} of {total}"
    right: str = ""
    font_size: int = 10
    color: str = "#666666"
    line_above: bool = True


# ============================================================================
# PDF GENERATION ENGINE
# ============================================================================

class LetterPDFBuilder:
    """PDF generation engine for professional letters with windowed envelope support"""

    def __init__(self,
                 sender_name: str,
                 sender_street_1: str,
                 sender_city: str,
                 sender_state: str,
                 sender_zip: str,
                 recipient_name: str,
                 recipient_title: str,
                 recipient_street_1: str,
                 recipient_city: str,
                 recipient_state: str,
                 recipient_zip: str,
                 subject: str,
                 salutation: str,
                 body_paragraphs: List[str],
                 closing: str = "Respectfully",
                 sender_street_2: Optional[str] = None,
                 sender_email: Optional[str] = None,
                 sender_phone: Optional[str] = None,
                 recipient_street_2: Optional[str] = None,
                 recipient_honorific: Optional[str] = None,
                 recipient_organization: Optional[str] = None,
                 date: Optional[str] = None,
                 positioning: Optional[Positioning] = None,
                 formatting: Optional[Formatting] = None,
                 fold_lines: Optional[FoldLines] = None,
                 header: Optional[Header] = None,
                 footer: Optional[Footer] = None):
        """Initialize PDF builder with letter content"""

        self.sender_name = sender_name
        self.sender_street_1 = sender_street_1
        self.sender_street_2 = sender_street_2
        self.sender_city = sender_city
        self.sender_state = sender_state
        self.sender_zip = sender_zip
        self.sender_email = sender_email
        self.sender_phone = sender_phone

        self.recipient_name = recipient_name
        self.recipient_title = recipient_title
        self.recipient_honorific = recipient_honorific
        self.recipient_organization = recipient_organization
        self.recipient_street_1 = recipient_street_1
        self.recipient_street_2 = recipient_street_2
        self.recipient_city = recipient_city
        self.recipient_state = recipient_state
        self.recipient_zip = recipient_zip

        self.subject = subject
        self.salutation = salutation
        self.body_paragraphs = body_paragraphs
        self.closing = closing
        self.date = date or datetime.now().strftime("%Y-%m-%d")

        # Configuration
        self.positioning = positioning or Positioning()
        self.formatting = formatting or Formatting()
        self.fold_lines = fold_lines or FoldLines()
        self.header = header or Header()
        self.footer = footer or Footer()

        # PDF state
        self.buffer = BytesIO()
        self.canvas = None
        self.page_count = 0
        self.total_pages = 0
        self.current_y = 0
        self.page_width, self.page_height = letter

    def generate(self) -> bytes:
        """Generate the PDF letter and return as bytes"""
        try:
            # Initialize canvas
            self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
            self._set_document_properties()

            # First pass: calculate total pages needed
            self.total_pages = self._calculate_total_pages()

            # Reset for actual generation
            self.buffer = BytesIO()
            self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
            self._set_document_properties()
            self.page_count = 0

            # Generate all pages
            self._generate_pages()

            # Save and return PDF
            self.canvas.save()
            pdf = self.buffer.getvalue()
            self.buffer.close()

            logger.info(f"Generated PDF with {self.page_count} pages for {self.recipient_name}")
            return pdf

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise

    def _set_document_properties(self):
        """Set PDF document properties"""
        self.canvas.setTitle(f"Letter to {self.recipient_name}")
        self.canvas.setAuthor(self.sender_name)
        self.canvas.setSubject(self.subject)

    def _format_date(self) -> str:
        """Format date for display"""
        try:
            date_obj = datetime.strptime(self.date, "%Y-%m-%d")
            return date_obj.strftime("%B %d, %Y").replace(" 0", " ")
        except:
            return datetime.now().strftime("%B %d, %Y").replace(" 0", " ")

    def _calculate_total_pages(self) -> int:
        """Calculate total pages needed - accounts for orphan prevention"""
        temp_page_count = 1
        current_y = self.page_height - (self.positioning.body_start_y * inch)

        # Account for subject and salutation
        if self.subject:
            current_y -= self.formatting.paragraph_spacing * 1.5
        current_y -= self.formatting.font_size * self.formatting.line_spacing * 1.5

        # Calculate space for body paragraphs
        max_width = (self.page_width - self.positioning.margins.left * inch -
                    self.positioning.margins.right * inch)
        bottom_margin = 0.75 * inch
        page_third = (self.page_height - self.positioning.margins.top * inch) / 3

        i = 0
        while i < len(self.body_paragraphs):
            paragraph = self.body_paragraphs[i]

            # Check if this is likely a heading (same logic as _flow_body_text)
            is_heading = (paragraph.isupper() and
                         len(paragraph.split()) <= 10 and
                         not paragraph.rstrip().endswith(('.', '!', '?', ',')))

            # Wrap text to get actual lines
            lines = self._wrap_text(paragraph, max_width -
                                   (self.formatting.indent_size * inch if self.formatting.indent_paragraphs else 0))

            # Calculate space needed for entire paragraph
            space_needed = len(lines) * self.formatting.font_size * self.formatting.line_spacing
            if i < len(self.body_paragraphs) - 1:
                space_needed += self.formatting.paragraph_spacing

            # If this is a heading, apply orphan prevention logic
            if is_heading and i < len(self.body_paragraphs) - 1:
                # Get the next paragraph and calculate its space requirements
                next_para = self.body_paragraphs[i + 1]
                next_lines = self._wrap_text(next_para, max_width -
                                            (self.formatting.indent_size * inch if self.formatting.indent_paragraphs else 0))

                # We want at least 4 lines of the next paragraph to appear with the heading
                min_next_lines = min(4, max(2, len(next_lines) // 2))
                space_for_next = min_next_lines * self.formatting.font_size * self.formatting.line_spacing

                # Total space needed is heading + paragraph spacing + at least 4 lines of next paragraph
                min_space_needed = space_needed + space_for_next

                # Check both conditions: space needed AND bottom third rule
                if current_y < bottom_margin + min_space_needed or current_y < page_third:
                    # Move heading to next page
                    temp_page_count += 1
                    current_y = self.page_height - (self.positioning.margins.top * inch)

            # Check if paragraph fits on current page
            if current_y < bottom_margin + space_needed:
                temp_page_count += 1
                current_y = self.page_height - (self.positioning.margins.top * inch)

            # Account for the space used by this paragraph
            current_y -= space_needed
            i += 1

        # Account for closing and signature
        signature_space = 3 * inch
        if current_y < bottom_margin + signature_space:
            temp_page_count += 1

        return temp_page_count

    def _generate_pages(self):
        """Generate all pages of the letter"""
        self.page_count = 1

        # Page 1
        self._start_new_page()
        self._draw_return_address()
        self._draw_date()
        self._draw_recipient_address()
        self._draw_salutation()

        # Flow body text
        remaining_body = self._flow_body_text()

        # Continue on additional pages if needed
        while remaining_body:
            self.page_count += 1
            self._start_new_page()
            remaining_body = self._flow_body_text(remaining_body)

        # Add closing and signature
        self._draw_closing_signature()

    def _start_new_page(self):
        """Start a new page"""
        if self.page_count > 1:
            self.canvas.showPage()

        self._draw_fold_lines()
        self._draw_header()
        self._draw_footer()

        if self.page_count == 1:
            self.current_y = self.page_height - (self.positioning.body_start_y * inch)
        else:
            self.current_y = self.page_height - (self.positioning.margins.top * inch)

    def _draw_fold_lines(self):
        """Draw fold lines in margins"""
        if not self.fold_lines.enabled:
            return

        color_hex = self.fold_lines.style.color.lstrip('#')
        r, g, b = tuple(int(color_hex[i:i+2], 16)/255 for i in (0, 2, 4))
        self.canvas.setStrokeColor(colors.Color(r, g, b))
        self.canvas.setLineWidth(self.fold_lines.style.line_width)

        for fold_y in self.fold_lines.positions:
            y_pos = self.page_height - (fold_y * inch)
            left_x = self.fold_lines.style.margin_offset_mm * mm
            line_length = self.fold_lines.style.line_length_mm * mm

            self.canvas.line(left_x, y_pos, left_x + line_length, y_pos)
            right_x = self.page_width - left_x
            self.canvas.line(right_x - line_length, y_pos, right_x, y_pos)

    def _draw_header(self):
        """Draw page header"""
        if self.page_count == 1:
            if not self.header.page_1.enabled:
                return
            header_config = self.header.page_1
        else:
            if not self.header.subsequent.enabled:
                return
            header_config = self.header.subsequent

        self.canvas.setFont(self.formatting.font_family, self.header.font_size)
        color_hex = self.header.color.lstrip('#')
        r, g, b = tuple(int(color_hex[i:i+2], 16)/255 for i in (0, 2, 4))
        self.canvas.setFillColor(colors.Color(r, g, b))

        y_pos = self.page_height - (0.5 * inch)
        formatted_date = self._format_date()

        # Left content
        if header_config.left:
            left_text = header_config.left.format(page=self.page_count, formatted_date=formatted_date)
            left_x = self.positioning.margins.left * inch
            self.canvas.drawString(left_x, y_pos, left_text)

        # Center content with page number
        if header_config.center:
            center_text = header_config.center.format(page=self.page_count, formatted_date=formatted_date)
            text_width = stringWidth(center_text, self.formatting.font_family, self.header.font_size)
            self.canvas.drawString(self.page_width/2 - text_width/2, y_pos, center_text)

        # Right content
        if header_config.right:
            right_text = header_config.right.format(formatted_date=formatted_date, page=self.page_count)
            text_width = stringWidth(right_text, self.formatting.font_family, self.header.font_size)
            right_x = self.page_width - (self.positioning.margins.right * inch)
            self.canvas.drawString(right_x - text_width, y_pos, right_text)

        if self.header.line_below:
            self.canvas.setStrokeColor(colors.Color(0.8, 0.8, 0.8))
            self.canvas.setLineWidth(0.5)
            left_x = self.positioning.margins.left * inch
            right_x = self.page_width - (self.positioning.margins.right * inch)
            self.canvas.line(left_x, y_pos - 5, right_x, y_pos - 5)

        self.canvas.setFillColor(colors.black)
        self.canvas.setFont(self.formatting.font_family, self.formatting.font_size)

    def _draw_footer(self):
        """Draw page footer"""
        if not self.footer.enabled:
            return

        self.canvas.setFont(self.formatting.font_family, self.footer.font_size)
        color_hex = self.footer.color.lstrip('#')
        r, g, b = tuple(int(color_hex[i:i+2], 16)/255 for i in (0, 2, 4))
        self.canvas.setFillColor(colors.Color(r, g, b))

        y_pos = 0.5 * inch

        if self.footer.line_above:
            self.canvas.setStrokeColor(colors.Color(0.8, 0.8, 0.8))
            self.canvas.setLineWidth(0.5)
            left_x = self.positioning.margins.left * inch
            right_x = self.page_width - (self.positioning.margins.right * inch)
            self.canvas.line(left_x, y_pos + 15, right_x, y_pos + 15)

        # Center content (page numbers)
        center_text = self.footer.center.format(page=self.page_count, total=self.total_pages)
        if center_text:
            text_width = stringWidth(center_text, self.formatting.font_family, self.footer.font_size)
            self.canvas.drawString(self.page_width/2 - text_width/2, y_pos, center_text)

        self.canvas.setFillColor(colors.black)
        self.canvas.setFont(self.formatting.font_family, self.formatting.font_size)

    def _draw_return_address(self):
        """Draw return address in window position"""
        self.canvas.setFont(self.formatting.font_family, self.formatting.font_size)
        self.canvas.setFillColor(colors.black)

        x = self.positioning.return_address.x * inch
        y = self.page_height - (self.positioning.return_address.y * inch)

        lines = [self.sender_name, self.sender_street_1]
        if self.sender_street_2:
            lines.append(self.sender_street_2)
        lines.append(f"{self.sender_city}, {self.sender_state} {self.sender_zip}")

        for line in lines:
            self.canvas.drawString(x, y, line)
            y -= self.formatting.font_size * 1.2

    def _draw_date(self):
        """Draw date"""
        self.canvas.setFont(self.formatting.font_family, self.formatting.font_size)
        self.canvas.setFillColor(colors.black)

        y = self.page_height - (self.positioning.date_position.y * inch)
        formatted_date = self._format_date()

        if self.positioning.date_position.alignment == "right":
            x = (self.positioning.recipient_address.x + self.positioning.recipient_address.width) * inch
            text_width = stringWidth(formatted_date, self.formatting.font_family, self.formatting.font_size)
            self.canvas.drawString(x - text_width, y, formatted_date)
        else:
            x = self.positioning.date_position.x * inch
            self.canvas.drawString(x, y, formatted_date)

    def _draw_recipient_address(self):
        """Draw recipient address in window position"""
        self.canvas.setFont(self.formatting.font_family, self.formatting.font_size)

        x = self.positioning.recipient_address.x * inch
        y = self.page_height - (self.positioning.recipient_address.y * inch)

        lines = []

        # Name with honorific
        if self.recipient_honorific:
            lines.append(f"{self.recipient_honorific} {self.recipient_name}")
        else:
            lines.append(self.recipient_name)

        # Title
        if self.recipient_title:
            lines.append(self.recipient_title)

        # Street address (line 1)
        if self.recipient_street_1:
            lines.append(self.recipient_street_1)

        # Street address (line 2)
        if self.recipient_street_2:
            lines.append(self.recipient_street_2)

        # City, State ZIP (always add if we have city/state/zip)
        if self.recipient_city or self.recipient_state or self.recipient_zip:
            city_state_line = f"{self.recipient_city}, {self.recipient_state} {self.recipient_zip}".strip()
            # Remove trailing comma if no state/zip
            city_state_line = city_state_line.rstrip(',').strip()
            if city_state_line:
                lines.append(city_state_line)

        # Draw all lines
        for line in lines:
            if line:  # Skip empty lines
                self.canvas.drawString(x, y, line)
                y -= self.formatting.font_size * 1.2

    def _draw_salutation(self):
        """Draw salutation and subject"""
        self.canvas.setFont(self.formatting.font_family, self.formatting.font_size)
        x = self.positioning.margins.left * inch

        self.current_y -= self.formatting.paragraph_spacing

        # Draw subject if present
        if self.subject:
            if "Times" in self.formatting.font_family:
                bold_font = "Times-Bold"
            elif "Helvetica" in self.formatting.font_family:
                bold_font = "Helvetica-Bold"
            else:
                bold_font = "Helvetica-Bold"

            self.canvas.setFont(bold_font, self.formatting.font_size)
            self.canvas.drawString(x, self.current_y, self.subject)
            self.current_y -= self.formatting.paragraph_spacing * 1.5
            self.canvas.setFont(self.formatting.font_family, self.formatting.font_size)

        # Draw salutation
        self.canvas.drawString(x, self.current_y, f"{self.salutation},")
        self.current_y -= self.formatting.font_size * self.formatting.line_spacing * 1.5

    def _flow_body_text(self, remaining_text: Optional[List[str]] = None) -> List[str]:
        """Flow body text with multi-page support - keeps paragraphs together and prevents orphaned headings"""
        paragraphs = remaining_text if remaining_text else self.body_paragraphs

        x = self.positioning.margins.left * inch
        max_width = (self.page_width -
                    (self.positioning.margins.left + self.positioning.margins.right) * inch)
        bottom_margin = 0.75 * inch

        remaining = []

        for i, paragraph in enumerate(paragraphs):
            # Check if this is likely a heading (all caps, short, no ending punctuation)
            is_heading = (paragraph.isupper() and len(paragraph.split()) <= 10 and
                         not paragraph.rstrip().endswith(('.', '!', '?', ',')))

            # Wrap text first to know how many lines we need
            lines = self._wrap_text(paragraph, max_width -
                                   (self.formatting.indent_size * inch if self.formatting.indent_paragraphs else 0))

            # Calculate space needed for this entire paragraph
            lines_needed = len(lines)
            space_needed = lines_needed * self.formatting.font_size * self.formatting.line_spacing

            # Add paragraph spacing if not the last paragraph
            if i < len(paragraphs) - 1:
                space_needed += self.formatting.paragraph_spacing

            # If this is a heading, check if we have room for it plus at least 4 lines of the next paragraph
            if is_heading and i < len(paragraphs) - 1:
                # Get the next paragraph and calculate its space requirements
                next_para = paragraphs[i + 1]
                next_lines = self._wrap_text(next_para, max_width -
                                            (self.formatting.indent_size * inch if self.formatting.indent_paragraphs else 0))

                # We want at least 4 lines of the next paragraph to appear with the heading
                # or half the paragraph, whichever is smaller
                min_next_lines = min(4, max(2, len(next_lines) // 2))
                space_for_next = min_next_lines * self.formatting.font_size * self.formatting.line_spacing

                # Total space needed is heading + paragraph spacing + at least 4 lines of next paragraph
                min_space_needed = space_needed + space_for_next

                # Be more aggressive - if we're in the bottom third of the page, move to next
                page_third = (self.page_height - self.positioning.margins.top * inch) / 3

                if self.current_y < bottom_margin + min_space_needed or self.current_y < page_third:
                    # Move heading to next page
                    remaining = paragraphs[i:]
                    break
            # If the entire paragraph doesn't fit, move it to the next page
            elif self.current_y < bottom_margin + space_needed:
                remaining = paragraphs[i:]
                break

            # Draw paragraph
            para_x = x
            # First line of each paragraph gets indented (but not headings)
            if self.formatting.indent_paragraphs and not is_heading:
                first_line_x = para_x + self.formatting.indent_size * inch
            else:
                first_line_x = para_x

            # Draw all lines of the paragraph (we know they fit)
            for j, line in enumerate(lines):
                # Use indented position for first line only (not for headings)
                line_x = first_line_x if j == 0 and not is_heading else para_x
                self.canvas.drawString(line_x, self.current_y, line)
                self.current_y -= self.formatting.font_size * self.formatting.line_spacing

            # Add paragraph spacing - only if not the last paragraph
            if i < len(paragraphs) - 1:
                self.current_y -= self.formatting.paragraph_spacing

        return remaining

    def _wrap_text(self, text: str, max_width: float) -> List[str]:
        """Wrap text to fit within max width"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            text_width = stringWidth(test_line, self.formatting.font_family, self.formatting.font_size)

            if text_width > max_width and current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                current_line.append(word)

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _draw_closing_signature(self):
        """Draw closing and signature"""
        self.current_y -= self.formatting.paragraph_spacing * 2

        required_space = 3 * inch
        if self.current_y < self.positioning.margins.bottom * inch + required_space:
            self.page_count += 1
            self._start_new_page()

        x = self.positioning.margins.left * inch

        self.canvas.setFont(self.formatting.font_family, self.formatting.font_size)
        self.canvas.setFillColor(colors.black)
        self.canvas.drawString(x, self.current_y, f"{self.closing},")
        self.current_y -= 0.25 * inch

        # Reserve space for manual signature
        signature_space = 0.6 * inch
        self.current_y -= signature_space
        self.current_y -= 0.15 * inch

        # Draw typed name
        self.canvas.drawString(x, self.current_y, self.sender_name)
        self.current_y -= self.formatting.font_size * 1.2

        # Draw email if provided
        if self.sender_email:
            self.canvas.drawString(x, self.current_y, self.sender_email)
            self.current_y -= self.formatting.font_size * 1.2

        # Draw phone if provided
        if self.sender_phone:
            self.canvas.drawString(x, self.current_y, self.sender_phone)
            self.current_y -= self.formatting.font_size * 1.2


# ============================================================================
# PDF SERVICE
# ============================================================================

class PDFService:
    """Service for generating and managing PDFs"""

    def __init__(self):
        self.output_dir = Path(settings.upload_dir) / "pdfs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_pdf_for_recipient(self,
                                        letter_recipient: LetterRecipient,
                                        sender_name: str,
                                        sender_street_1: str,
                                        sender_city: str,
                                        sender_state: str,
                                        sender_zip: str,
                                        sender_street_2: Optional[str] = None,
                                        sender_email: Optional[str] = None,
                                        sender_phone: Optional[str] = None,
                                        include_email: bool = False,
                                        include_phone: bool = False) -> Dict[str, Any]:
        """Generate PDF for a letter recipient"""
        try:
            # Parse letter content
            content_parts = self._parse_letter_content(letter_recipient.personalized_content)

            # Get recipient address
            recipient_addr = letter_recipient.recipient_address

            # Create PDF builder
            # Note: Organization is not passed as it's not displayed in formal letters

            # Configure header to show recipient name and date on subsequent pages only
            header_config = Header(
                page_1=HeaderContent(enabled=False),
                subsequent=HeaderContent(
                    enabled=True,
                    left=letter_recipient.recipient_name,
                    right="{formatted_date}"
                )
            )

            builder = LetterPDFBuilder(
                sender_name=sender_name,
                sender_street_1=sender_street_1,
                sender_street_2=sender_street_2,
                sender_city=sender_city,
                sender_state=sender_state,
                sender_zip=sender_zip,
                sender_email=sender_email if include_email else None,
                sender_phone=sender_phone if include_phone else None,
                recipient_name=letter_recipient.recipient_name,
                recipient_title=letter_recipient.recipient_title,
                recipient_honorific=recipient_addr.get('honorific', 'The Honorable'),
                recipient_organization=None,  # Not displayed in formal letters
                recipient_street_1=recipient_addr.get('street_1', ''),
                recipient_street_2=recipient_addr.get('street_2'),
                recipient_city=recipient_addr.get('city', ''),
                recipient_state=recipient_addr.get('state', ''),
                recipient_zip=recipient_addr.get('zip', ''),
                subject=f"RE: {letter_recipient.personalized_subject or 'Important Matter'}",
                salutation=content_parts['salutation'],
                body_paragraphs=content_parts['body'],
                closing=content_parts['closing'],
                header=header_config
            )

            # Generate PDF
            pdf_bytes = builder.generate()

            # Save PDF to disk
            filename = f"{letter_recipient.id}.pdf"
            pdf_path = self.output_dir / filename

            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)

            logger.info(f"Generated PDF for recipient {letter_recipient.recipient_name}: {pdf_path}")

            return {
                'success': True,
                'pdf_path': str(pdf_path),
                'pdf_size': len(pdf_bytes),
                'filename': filename
            }

        except Exception as e:
            logger.error(f"Error generating PDF for recipient {letter_recipient.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_letter_content(self, letter_text: str) -> Dict[str, Any]:
        """Parse letter content into components"""
        lines = letter_text.strip().split('\n')

        # Find salutation
        salutation = "Dear Senator"
        salutation_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("Dear"):
                salutation = line.strip().rstrip(':').rstrip(',')
                salutation_idx = i
                break

        # Find closing
        closing = "Respectfully"
        closing_idx = len(lines) - 1
        closing_keywords = ['Sincerely', 'Respectfully', 'Best regards', 'Thank you', 'Yours truly']

        for i in range(len(lines) - 1, salutation_idx, -1):
            line = lines[i].strip().rstrip(',')
            if any(keyword in line for keyword in closing_keywords):
                closing = line
                closing_idx = i
                break

        # Extract body paragraphs
        body_lines = lines[salutation_idx + 1:closing_idx]

        paragraphs = []
        current_paragraph = []

        for line in body_lines:
            line = line.strip()
            if line:
                # Check if it's a heading
                if line.isupper() and len(line.split()) <= 10:
                    if current_paragraph:
                        paragraphs.append(' '.join(current_paragraph))
                        current_paragraph = []
                    paragraphs.append(line)
                else:
                    current_paragraph.append(line)
            elif current_paragraph:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []

        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))

        return {
            'salutation': salutation,
            'body': paragraphs,
            'closing': closing
        }

    async def get_pdf_path(self, recipient_id: str) -> Optional[str]:
        """Get the path to a generated PDF"""
        filename = f"{recipient_id}.pdf"
        pdf_path = self.output_dir / filename

        if pdf_path.exists():
            return str(pdf_path)
        return None

    async def delete_pdf(self, recipient_id: str) -> bool:
        """Delete a generated PDF"""
        try:
            filename = f"{recipient_id}.pdf"
            pdf_path = self.output_dir / filename

            if pdf_path.exists():
                pdf_path.unlink()
                logger.info(f"Deleted PDF: {pdf_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting PDF {recipient_id}: {e}")
            return False