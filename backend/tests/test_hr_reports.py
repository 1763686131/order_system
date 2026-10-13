import http.client
import io
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from urllib.parse import quote

from flask import Flask
from werkzeug.serving import make_server, WSGIRequestHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from routes import hr_reports


REPORT_NAME = '\u68c0\u6d4b\u62a5\u544a 2026.pdf'
REPORT_DIRECTORY = '\u90e8\u95e8\u62a5\u544a'
PDF_CONTENT = b'%PDF-1.4\nreport response fixture\n%%EOF\n'


class QuietRequestHandler(WSGIRequestHandler):
    def log(self, kind, message, *args):
        pass


class ReportPreviewTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory(prefix='report-preview-')
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name) / '\u68c0\u6d4b\u62a5\u544a\u76ee\u5f55'
        directory = self.root / REPORT_DIRECTORY
        directory.mkdir(parents=True)
        (directory / REPORT_NAME).write_bytes(PDF_CONTENT)

        self.connection = sqlite3.connect(':memory:', check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.addCleanup(self.connection.close)
        self.connection.execute('''
            CREATE TABLE hr_reports (
                id TEXT PRIMARY KEY, filename TEXT, file_path TEXT,
                file_type TEXT, share_token TEXT, share_expire TEXT,
                file_hash TEXT, file_size INTEGER, uploader TEXT,
                created_at TEXT, updated_at TEXT
            )
        ''')
        self.connection.execute('''
            INSERT INTO hr_reports (id, filename, file_path, file_type, share_token)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            'report', REPORT_NAME, f'{REPORT_DIRECTORY}/{REPORT_NAME}',
            'pdf', 'report-share',
        ))
        self.connection.commit()

        @contextmanager
        def isolated_database():
            yield self.connection

        for attribute, replacement in (
            ('get_db', isolated_database),
            ('ensure_report_root', lambda: str(self.root)),
            ('current_identity', lambda fallback: fallback),
        ):
            patcher = patch.object(hr_reports, attribute, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.app = Flask(__name__)
        self.app.register_blueprint(hr_reports.hr_reports_bp)
        self.client = self.app.test_client()

    def test_unicode_name_and_directories_over_real_http(self):
        server = make_server('127.0.0.1', 0, self.app, request_handler=QuietRequestHandler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            for endpoint in ('download/report', 'share/report-share'):
                with self.subTest(endpoint=endpoint):
                    connection = http.client.HTTPConnection(
                        '127.0.0.1', server.server_port, timeout=3,
                    )
                    try:
                        connection.request('GET', f'/api/hr/reports/{endpoint}')
                        response = connection.getresponse()
                        content = response.read()
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.getheader('Content-Type'), 'application/pdf')
                        self.assertEqual(content, PDF_CONTENT)
                        disposition = response.getheader('Content-Disposition')
                        self.assertTrue(disposition.startswith('inline;'))
                        self.assertIn(
                            f"filename*=UTF-8''{quote(REPORT_NAME, safe='')}",
                            disposition,
                        )
                    finally:
                        connection.close()
        finally:
            server.shutdown()
            worker.join(timeout=3)
            server.server_close()

    def test_pdf_type_and_range_do_not_depend_on_os_mime_mapping(self):
        with patch.object(hr_reports.mimetypes, 'guess_type', return_value=('application/octet-stream', None)):
            for endpoint in ('download/report', 'share/report-share'):
                with self.subTest(endpoint=endpoint):
                    response = self.client.get(
                        f'/api/hr/reports/{endpoint}',
                        headers={'Range': 'bytes=0-7'},
                    )
                    try:
                        self.assertEqual(response.status_code, 206)
                        self.assertEqual(response.mimetype, 'application/pdf')
                        self.assertEqual(response.data, PDF_CONTENT[:8])
                        self.assertEqual(
                            response.headers['Content-Range'],
                            f'bytes 0-7/{len(PDF_CONTENT)}',
                        )
                    finally:
                        response.close()

    def test_chinese_upload_remains_a_pdf_and_can_be_previewed(self):
        for filename in (REPORT_NAME, '\u5458\u5de5\u4f53\u68c0\u62a5\u544a.pdf'):
            with self.subTest(filename=filename):
                response = self.client.post('/api/hr/reports/upload', data={
                    'file': (io.BytesIO(PDF_CONTENT), filename),
                    'folder_path': REPORT_DIRECTORY,
                })
                self.assertEqual(response.status_code, 200)
                uploaded = response.get_json()['file']
                self.assertEqual(uploaded['name'], filename)
                self.assertEqual(uploaded['type'], 'pdf')
                self.assertEqual(uploaded['path'], f'{REPORT_DIRECTORY}/{filename}')
                self.assertEqual((self.root / uploaded['path']).read_bytes(), PDF_CONTENT)

                preview = self.client.get(f'/api/hr/reports/download/{uploaded["id"]}')
                try:
                    self.assertEqual(preview.status_code, 200)
                    self.assertEqual(preview.mimetype, 'application/pdf')
                    self.assertTrue(preview.headers['Content-Disposition'].startswith('inline;'))
                    self.assertEqual(preview.data, PDF_CONTENT)
                finally:
                    preview.close()

    def test_images_remain_inline_and_documents_remain_attachments(self):
        for filename, file_type, expected_disposition, content in (
            ('photo.png', 'image', 'inline;', b'\x89PNG\r\n\x1a\n'),
            ('document.docx', 'word', 'attachment;', b'PK\x03\x04'),
        ):
            with self.subTest(filename=filename):
                (self.root / filename).write_bytes(content)
                self.connection.execute('''
                    INSERT INTO hr_reports (id, filename, file_path, file_type, share_token)
                    VALUES (?, ?, ?, ?, ?)
                ''', (filename, filename, filename, file_type, f'{filename}-share'))
                for endpoint in (f'download/{filename}', f'share/{filename}-share'):
                    response = self.client.get(f'/api/hr/reports/{endpoint}')
                    try:
                        self.assertEqual(response.status_code, 200)
                        self.assertTrue(
                            response.headers['Content-Disposition'].startswith(expected_disposition),
                        )
                        self.assertEqual(response.data, content)
                    finally:
                        response.close()

    def test_upload_filename_cannot_escape_the_report_directory(self):
        for filename in (
            f'../../{REPORT_NAME}',
            f'C:\\reports\\{REPORT_NAME}',
        ):
            with self.subTest(filename=filename):
                self.assertEqual(hr_reports.safe_upload_filename(filename), REPORT_NAME)
        self.assertEqual(hr_reports.safe_upload_filename('NUL.pdf'), '_NUL.pdf')
        with self.assertRaises(ValueError):
            hr_reports.safe_upload_filename('../..')

    def test_missing_reports_and_files_keep_returning_not_found(self):
        missing = self.client.get('/api/hr/reports/download/missing')
        self.assertEqual(missing.status_code, 404)

        self.connection.execute(
            'UPDATE hr_reports SET file_path = ? WHERE id = ?',
            ('missing.pdf', 'report'),
        )
        for endpoint in ('download/report', 'share/report-share'):
            with self.subTest(endpoint=endpoint):
                response = self.client.get(f'/api/hr/reports/{endpoint}')
                self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
