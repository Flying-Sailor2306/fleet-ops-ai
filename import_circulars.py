"""Local PDF import utility. Requires pypdf only when importing, not running app."""
import argparse
import hashlib
import json
import re
import shutil
from datetime import date
from pathlib import Path
from pypdf import PdfReader

# Only the circular identifiers explicitly supplied for this import batch.
BATCH_IDS = set('106-1 112-2 113-2 115-1 116-1 120-1 123-1 124-1 126-1 127-1 128-1 129-1 130-1 131-2 133-1 134-1 135-1 137-2 138-1 141-2 142-3 144-3 145-3 146-1 147-1 148-1 149-2 151-1 156-1 158-2 159-1 160-1 161-1 162-1 164-1 165-2 166-1 167-1 171-1 172-1 173-1 174-1 175-1 176-1 177-1 183-1 185-1 187-1 189-2 190-1 191-1 192-1 193-1 196-1 197-1 198-2 199-1 201-1 209-1 210-1 211-3 212-1'.split())

def import_batch(folder, library):
    library.parent.mkdir(parents=True, exist_ok=True)
    docs = json.loads(library.read_text(encoding='utf-8')) if library.exists() else []
    by_hash = {d['sha256']: d for d in docs}
    report = dict(imported=[], duplicates=[], errors=[], missing=[])
    found = set()
    for source in sorted(folder.glob('MC-*.pdf')):
        match = re.match(r'MC-(\d+-\d+)-', source.name)
        if not match or match[1] not in BATCH_IDS: continue
        found.add(match[1])
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest in by_hash:
            aliases = by_hash[digest].setdefault('aliases', [])
            if source.name != by_hash[digest]['filename'] and source.name not in aliases:
                aliases.append(source.name)
            report['duplicates'].append(source.name)
            continue
        ident = 'MC-' + match[1]
        if any(d['id'] == ident for d in docs): ident += '-' + digest[:8]
        try:
            reader = PdfReader(source)
            chunks, empty = [], []
            for number, page in enumerate(reader.pages, 1):
                text = (page.extract_text() or '').strip()
                if not text:
                    empty.append(number)
                    continue
                # Bound excerpt size while retaining physical PDF-page locators.
                parts = [text[i:i+6000] for i in range(0, len(text), 6000)]
                for i, part in enumerate(parts, 1):
                    suffix = f'-part{i}' if len(parts) > 1 else ''
                    chunks.append(dict(id=f'{ident}-p{number}{suffix}', locator=f'PDF page {number}' + (f', excerpt part {i}' if suffix else ''), text=part))
            doc = dict(id=ident, category='Circulars', filename=source.name,
                title=re.sub(r'-[a-z0-9]{6}$', '', source.stem).replace('-', ' '),
                scope='User-supplied Palau circular reference. Verify flag, vessel, voyage, dates and supersession before applying. Not a company SMS or OEM procedure.',
                status='Text extracted' if not empty else 'Partial text extraction; pages requiring OCR: ' + ', '.join(map(str, empty)),
                pages=len(reader.pages), sha256=digest, edition='Unverified — identifier taken from filename; current validity not checked',
                imported=date.today().isoformat(), validity='Unverified; may be historical, expired or superseded',
                chunks=chunks, ocr_pending_pages=empty)
            shutil.copy2(source, library.parent / source.name)
            docs.append(doc)
            by_hash[digest] = doc
            report['imported'].append(dict(id=ident, pages=doc['pages'], excerpts=len(chunks), ocr_pending=empty))
        except Exception as exc:
            report['errors'].append(dict(filename=source.name, error=str(exc)))
    report['missing'] = sorted(BATCH_IDS - found)
    library.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding='utf-8')
    (library.parent / 'circular-import-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    report = import_batch(args.folder, Path(__file__).with_name('local-data') / 'references.json')
    print(json.dumps(report, indent=2))
