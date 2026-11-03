"""Import the six explicitly supplied OEM volumes into ignored local storage."""
import hashlib
import json
import re
import shutil
from pathlib import Path
from pypdf import PdfReader

NAMES = [
    'MB-01 COMPONENT NO.1 (CODE BOOK).pdf',
    'MB-02 COMPONENT NO.2   (FITTING AND ACCESSORIES).pdf',
    'MB-03 MAINTENANCE.pdf',
    'MB-04 OPERATION AND DATA.pdf',
    'MB-05 MANOEUVRING SYSTEM.pdf',
    'MB-06 LIST OF SPARE PARTS AND TOOLS (MAIN ENGINE).pdf',
]

def import_volumes(folder, library):
    library.parent.mkdir(parents=True, exist_ok=True)
    docs = json.loads(library.read_text(encoding='utf-8')) if library.exists() else []
    report = []
    for number, name in enumerate(NAMES, 1):
        source = folder / name
        ident = f'OEM-MB{number:02}'
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if any(d.get('sha256') == digest for d in docs):
            report.append(dict(id=ident, status='Already imported'))
            continue
        reader = PdfReader(source)
        chunks, empty = [], []
        for page_number, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or '').strip()
            if len(re.sub(r'\W', '', text)) < 30:
                empty.append(page_number)
            if text:
                for part_number, offset in enumerate(range(0, len(text), 6000), 1):
                    suffix = f'-part{part_number}' if len(text) > 6000 else ''
                    chunks.append(dict(id=f'{ident}-p{page_number}{suffix}', locator=f'Physical PDF page {page_number}' + (f', part {part_number}' if suffix else ''), text=text[offset:offset+6000]))
        doc = dict(id=ident, category='OEM engine manuals', filename=name,
            scope='Primary technical reference for the fictional main-engine installation. MITSUI-MAN B&W supplied instruction-book set; applicability, serial-specific data and later service letters must be verified. Not a substitute for shipboard authorization.',
            status=f'Text extracted where available; {len(empty)} low-text/image pages require visual review or OCR',
            pages=len(reader.pages), sha256=digest, edition='Volume identifiers as supplied; complete revision status unverified',
            imported='2026-10-31', validity='Scenario technical source of truth; exact engine variant/serial and applicable revisions not yet verified',
            ocr_pending_pages=empty, chunks=chunks)
        shutil.copy2(source, library.parent / name)
        docs.append(doc)
        library.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding='utf-8')
        report.append(dict(id=ident, pages=len(reader.pages), excerpts=len(chunks), low_text_pages=len(empty)))
        print(json.dumps(report[-1]), flush=True)
    (library.parent/'oem-import-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report

if __name__ == '__main__':
    import_volumes(Path('C:/Users/rahul/AppData/Local/Temp'), Path(__file__).with_name('local-data')/'references.json')
