"""Render the Markdown sources in docs/ into the submission formats.

docs/article.md -> docs/article.docx   research article, IMRAD
docs/report.md  -> docs/report.docx    case-study report
docs/slides.md  -> docs/slides.pptx    presentation

Only the Markdown subset the sources actually use is supported: ATX headings, paragraphs,
bulleted and numbered lists, pipe tables, images with captions, blockquotes and inline
bold/italic/code. Anything richer belongs in the source document, not in this converter.

Markdown convention in docs/: one sentence per line. Consecutive non-blank lines are joined
into a single paragraph, which is standard Markdown and keeps the sources diff-friendly.
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PPTColor
from pptx.util import Inches as PInches, Pt as PPt

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
BODY_FONT, MONO_FONT = 'Times New Roman', 'Consolas'
INK = RGBColor(0x0B, 0x0B, 0x0B)
ACCENT = PPTColor(0x2A, 0x78, 0xD6)
SLIDE_INK = PPTColor(0x0B, 0x0B, 0x0B)
SLIDE_MUTED = PPTColor(0x52, 0x51, 0x4E)

INLINE = re.compile(r'(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)')


def blocks(md: str):
    """Split Markdown into (kind, payload) blocks in document order."""
    lines = md.split('\n')
    i, out = 0, []
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
        elif ln.startswith('#'):
            level = len(ln) - len(ln.lstrip('#'))
            out.append(('heading', (level, ln.lstrip('#').strip())))
            i += 1
        elif ln.startswith('!['):
            m = re.match(r'!\[(.*?)\]\((.*?)\)', ln.strip())
            out.append(('image', (m.group(1), m.group(2))))
            i += 1
        elif ln.lstrip().startswith('|'):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            rows = [r for r in rows if not all(set(c) <= set('-: ') for c in r)]
            out.append(('table', rows))
        elif re.match(r'\s*([-*]|\d+\.)\s', ln):
            items, ordered = [], bool(re.match(r'\s*\d+\.', ln))
            while i < len(lines) and re.match(r'\s*([-*]|\d+\.)\s', lines[i]):
                items.append(re.sub(r'^\s*([-*]|\d+\.)\s+', '', lines[i]))
                i += 1
            out.append(('list', (ordered, items)))
        elif ln.startswith('>'):
            buf = []
            while i < len(lines) and lines[i].startswith('>'):
                buf.append(lines[i].lstrip('> ').rstrip())
                i += 1
            out.append(('quote', ' '.join(buf)))
        else:
            buf = []
            while i < len(lines) and lines[i].strip() and not re.match(
                    r'\s*(#|!\[|\||>|[-*]\s|\d+\.\s)', lines[i]):
                buf.append(lines[i].strip())
                i += 1
            out.append(('para', ' '.join(buf)))
    return out


def runs(paragraph, text, size=12, italic=False, bold=False, font=BODY_FONT):
    """Write text into a python-docx paragraph, honouring inline **bold**, *italic* and `code`."""
    for part in INLINE.split(text):
        if not part:
            continue
        r = paragraph.add_run()
        if part.startswith('**') and part.endswith('**'):
            r.text, r.bold = part[2:-2], True
        elif part.startswith('`') and part.endswith('`'):
            r.text, r.font.name = part[1:-1], MONO_FONT
            r.font.size = Pt(size - 1.5)
        elif part.startswith('*') and part.endswith('*'):
            r.text, r.italic = part[1:-1], True
        else:
            r.text = part
        if r.font.name is None:
            r.font.name = font
        r.font.size = r.font.size or Pt(size)
        r.font.color.rgb = INK
        r.bold = r.bold or bold
        r.italic = r.italic or italic
    return paragraph


def to_docx(md_path: Path, out_path: Path):
    doc = Document()
    normal = doc.styles['Normal']
    normal.font.name, normal.font.size = BODY_FONT, Pt(12)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(6)
    for lvl in range(1, 5):
        s = doc.styles[f'Heading {lvl}']
        s.font.name, s.font.color.rgb = BODY_FONT, INK
        s.font.size = Pt({1: 16, 2: 13.5, 3: 12, 4: 12}[lvl])
        s.font.bold, s.font.italic = lvl < 4, lvl == 4

    for kind, payload in blocks(md_path.read_text(encoding='utf-8')):
        if kind == 'heading':
            level, text = payload
            if level == 1:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                runs(p, text, size=16, bold=True)
            else:
                doc.add_heading(text, min(level - 1, 4))
        elif kind == 'para':
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            runs(p, payload)
        elif kind == 'quote':
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            runs(p, payload, size=11, italic=True)
        elif kind == 'list':
            ordered, items = payload
            for it in items:
                p = doc.add_paragraph(style='List Number' if ordered else 'List Bullet')
                runs(p, it)
        elif kind == 'image':
            caption, rel = payload
            path = (md_path.parent / rel).resolve()
            doc.add_picture(str(path), width=Inches(6.2))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            if caption:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                runs(p, caption, size=10, italic=True)
        elif kind == 'table':
            header, *body = payload
            t = doc.add_table(rows=1, cols=len(header))
            t.style, t.alignment = 'Table Grid', WD_TABLE_ALIGNMENT.CENTER
            for cell, text in zip(t.rows[0].cells, header):
                cell.paragraphs[0].text = ''
                runs(cell.paragraphs[0], text, size=9.5, bold=True)
            for row in body:
                cells = t.add_row().cells
                for cell, text in zip(cells, row + [''] * (len(header) - len(row))):
                    cell.paragraphs[0].text = ''
                    runs(cell.paragraphs[0], text, size=9.5)
    doc.save(out_path)
    return out_path


BODY_TOP_IN = 1.55         # top of the content area, below the title rule
BODY_BOX_IN = 5.4          # height of the content area
CHARS_PER_LINE = 95        # fits the 11.7 inch box at 18 pt Calibri


def body_font_size(content) -> int:
    """Pick 18, 16 or 14 pt so the bullets of one slide fit the body box.

    PowerPoint's own autofit needs a rendering engine that python-pptx does not have, so the
    line count is estimated from the character count and the font stepped down until it fits.
    """
    items = [i for kind, payload in content if kind in ('list', 'para', 'quote')
             for i in (payload[1] if kind == 'list' else [payload])]
    if not items:
        return 18
    table_rows = sum(len(payload) for kind, payload in content if kind == 'table')
    room = BODY_BOX_IN - min(0.42 * table_rows, BODY_BOX_IN * 0.6) - (0.25 if table_rows else 0)
    for pt in (18, 16, 14):
        wrap = int(CHARS_PER_LINE * 18 / pt)
        lines = sum(max(1, -(-len(i) // wrap)) for i in items)
        if lines * (pt * 1.25 + max(6, pt // 2)) <= room * 72:
            return pt
    return 14


def to_pptx(md_path: Path, out_path: Path):
    """`## Title` opens a slide; bullets, one image and a `> ` takeaway line fill it."""
    prs = Presentation()
    prs.slide_width, prs.slide_height = PInches(13.333), PInches(7.5)
    blank = prs.slide_layouts[6]

    def new_slide(title):
        s = prs.slides.add_slide(blank)
        box = s.shapes.add_textbox(PInches(0.6), PInches(0.35), PInches(12.1), PInches(0.9))
        p = box.text_frame.paragraphs[0]
        r = p.add_run(); r.text = title
        r.font.size, r.font.bold, r.font.color.rgb, r.font.name = PPt(28), True, SLIDE_INK, 'Calibri'
        line = s.shapes.add_shape(1, PInches(0.6), PInches(1.2), PInches(1.6), PInches(0.045))
        line.fill.solid(); line.fill.fore_color.rgb = ACCENT; line.line.fill.background()
        line.shadow.inherit = False
        return s

    # group blocks into slides first, so the body font size can be fitted to the content
    decks, current = [], None
    for kind, payload in blocks(md_path.read_text(encoding='utf-8')):
        if kind == 'heading' and payload[0] <= 2:
            current = (payload[1], [])
            decks.append(current)
        elif current is not None:
            current[1].append((kind, payload))

    for title, content in decks:
        slide = new_slide(title)
        body = None
        font_pt = body_font_size(content)
        y = BODY_TOP_IN          # vertical cursor, so a table and its commentary never overlap
        for kind, payload in content:
            if kind == 'image':
                caption, rel = payload
                pic = slide.shapes.add_picture(str((md_path.parent / rel).resolve()),
                                               PInches(0.9), PInches(1.55), height=PInches(5.0))
                pic.left = int((prs.slide_width - pic.width) / 2)
                y += 5.0 + 0.2
                if caption:
                    tb = slide.shapes.add_textbox(PInches(0.6), PInches(6.75), PInches(12.1), PInches(0.5))
                    r = tb.text_frame.paragraphs[0].add_run(); r.text = caption
                    r.font.size, r.font.color.rgb, r.font.italic = PPt(12), SLIDE_MUTED, True
            elif kind in ('list', 'para', 'quote'):
                if body is None:
                    body = slide.shapes.add_textbox(PInches(0.8), PInches(y), PInches(11.7),
                                                    PInches(BODY_TOP_IN + BODY_BOX_IN - y)).text_frame
                    body.word_wrap = True
                    body._first = True
                items = payload[1] if kind == 'list' else [payload]
                for it in items:
                    p = body.paragraphs[0] if body._first else body.add_paragraph()
                    body._first = False
                    if kind == 'list':
                        r0 = p.add_run(); r0.text = '- '
                        r0.font.size, r0.font.color.rgb = PPt(font_pt), ACCENT
                    for part in INLINE.split(it):
                        if not part:
                            continue
                        r = p.add_run()
                        r.font.size, r.font.name = PPt(font_pt), 'Calibri'
                        r.font.color.rgb = SLIDE_INK
                        if part.startswith('**') and part.endswith('**'):
                            r.text, r.font.bold = part[2:-2], True
                        elif part.startswith('*') and part.endswith('*'):
                            r.text, r.font.italic = part[1:-1], True
                        elif part.startswith('`') and part.endswith('`'):
                            r.text, r.font.name = part[1:-1], 'Consolas'
                        else:
                            r.text = part
                        if kind == 'quote':
                            r.font.italic, r.font.color.rgb = True, SLIDE_MUTED
                    p.space_after = PPt(max(6, font_pt // 2))
            elif kind == 'table':
                header, *rowsx = payload
                n, m = len(rowsx) + 1, len(header)
                h = min(0.42, (BODY_TOP_IN + BODY_BOX_IN - y) / n) * n
                gt = slide.shapes.add_table(n, m, PInches(0.8), PInches(y),
                                            PInches(11.7), PInches(h)).table
                y += h + 0.25
                for j, h in enumerate(header):
                    c = gt.cell(0, j); c.text = h
                    c.text_frame.paragraphs[0].runs[0].font.size = PPt(13)
                    c.text_frame.paragraphs[0].runs[0].font.bold = True
                for i, row in enumerate(rowsx, 1):
                    for j, v in enumerate(row[:m]):
                        c = gt.cell(i, j); c.text = v
                        c.text_frame.paragraphs[0].runs[0].font.size = PPt(12)
    prs.save(out_path)
    return out_path, len(prs.slides.__iter__.__self__._sldIdLst)


def word_count(md_path: Path, exclude_headings: set[str]) -> int:
    """Body word count, skipping the sections the assignment excludes from the 3500-word limit."""
    total, skip = 0, False
    for kind, payload in blocks(md_path.read_text(encoding='utf-8')):
        if kind == 'heading':
            title = payload[1].lower()
            skip = payload[0] <= 2 and any(e in title for e in exclude_headings)
            continue
        if skip or kind in ('image', 'table'):
            continue
        text = payload[1] if kind == 'list' else payload
        text = ' '.join(text) if isinstance(text, list) else text
        total += len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'.-]*", re.sub(r'[*`]', '', str(text))))
    return total


if __name__ == '__main__':
    targets = sys.argv[1:] or ['article', 'report', 'slides']
    if 'article' in targets:
        p = to_docx(DOCS / 'article.md', DOCS / 'article.docx')
        n = word_count(DOCS / 'article.md',
                       {'abstract', 'keywords', 'conclusion', 'references', 'title'})
        print(f'{p.name}: {n} words in the counted sections (target 3500)')
        # the brief sets 3500 words as a floor for the counted sections, not a ceiling
        assert 3500 <= n <= 5000, f'article body is {n} words, outside the accepted band'
    if 'report' in targets:
        p = to_docx(DOCS / 'report.md', DOCS / 'report.docx')
        print(f'{p.name}: {word_count(DOCS / "report.md", set())} words total')
    if 'slides' in targets:
        p, n = to_pptx(DOCS / 'slides.md', DOCS / 'slides.pptx')
        print(f'{p.name}: {n} slides, {n - 1} excluding the title slide')
        assert 10 <= n - 1 <= 15, f'{n - 1} content slides, the brief asks for 10-15'
    print('documents ok')
