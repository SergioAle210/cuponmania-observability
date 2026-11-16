"""Validador Python opcional: HTTP local controlado, sin Kibana ni Docker.

Compose utiliza curl y no ejecuta esta utilidad. Estas pruebas no atribuyen
validación semántica del JSON al servicio kibana-setup.
"""

from contextlib import contextmanager
from copy import deepcopy
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
from threading import Thread

import pytest

from elk.kibana import import_objects as importer


OBJECTS_PATH = Path(__file__).resolve().parents[2] / "elk/kibana/saved-objects.ndjson"


@pytest.fixture
def expected_objects():
    rows = [json.loads(line) for line in OBJECTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {(row["type"], row["id"]) for row in rows}
    assert rows and len(rows) == len(expected)
    return expected


def confirmed_result(expected):
    return {
        "success": True,
        "successCount": len(expected),
        "successResults": [{"type": kind, "id": object_id} for kind, object_id in sorted(expected)],
    }


@contextmanager
def local_import_endpoint(response_body):
    """Capture one real multipart POST and respond with a controlled HTTP 200."""
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            content = self.rfile.read(int(self.headers["Content-Length"]))
            received.append({"path": self.path, "headers": self.headers, "body": content})
            payload = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", received
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()


def test_cli_imports_all_objects_and_sends_valid_multipart(expected_objects, capsys):
    response = confirmed_result(expected_objects)
    with local_import_endpoint(response) as (url, received):
        exit_code = importer.main(["--url", url, "--file", str(OBJECTS_PATH)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert json.loads(captured.out) == response
    assert len(received) == 1
    request = received[0]
    assert request["path"] == "/api/saved_objects/_import?overwrite=true"
    assert request["headers"]["kbn-xsrf"] == "true"
    message = BytesParser(policy=policy.default).parsebytes(
        ("Content-Type: " + request["headers"]["Content-Type"] + "\r\nMIME-Version: 1.0\r\n\r\n").encode()
        + request["body"]
    )
    assert message.is_multipart()
    parts = list(message.iter_parts())
    assert len(parts) == 1
    assert parts[0].get_param("name", header="Content-Disposition") == "file"
    assert parts[0].get_filename() == "saved-objects.ndjson"
    assert parts[0].get_content_type() == "application/x-ndjson"
    assert parts[0].get_payload(decode=True) == OBJECTS_PATH.read_bytes()


@pytest.mark.parametrize("object_count", [1, 13])
def test_optional_cli_adapts_to_changed_export_size(tmp_path, capsys, object_count):
    """Adding/removing objects must not require changing a hardcoded count."""
    rows = [{"type": "index-pattern", "id": f"qa-view-{i}",
             "attributes": {"title": f"qa-events-{i}-*"}, "references": []}
            for i in range(object_count)]
    path = tmp_path / "changed-export.ndjson"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    expected = {(row["type"], row["id"]) for row in rows}
    response = confirmed_result(expected)
    with local_import_endpoint(response) as (url, received):
        exit_code = importer.main(["--url", url, "--file", str(path)])
    captured = capsys.readouterr()
    assert exit_code == 0 and captured.err == ""
    assert len(received) == 1
    assert json.loads(captured.out) == response


@pytest.mark.parametrize("failure", ["success_false", "partial_errors"])
def test_http_200_does_not_hide_failed_or_partial_import(expected_objects, capsys, failure):
    response = confirmed_result(expected_objects)
    if failure == "success_false":
        response["success"] = False
    else:
        response["errors"] = [{"type": "lens", "id": "cm-trafico", "error": {"type": "missing_references"}}]
    with local_import_endpoint(response) as (url, received):
        exit_code = importer.main(["--url", url, "--file", str(OBJECTS_PATH)])
    captured = capsys.readouterr()
    assert len(received) == 1
    assert exit_code == 1
    assert captured.out == ""
    assert "Importación de Kibana fallida" in captured.err


@pytest.mark.parametrize("corruption", ["missing", "duplicate", "foreign"])
def test_success_count_alone_cannot_confirm_missing_or_wrong_objects(expected_objects, corruption):
    response = confirmed_result(expected_objects)
    if corruption == "missing":
        response["successResults"].pop()
    elif corruption == "duplicate":
        response["successResults"][-1] = deepcopy(response["successResults"][0])
    else:
        response["successResults"][-1]["id"] = "unexpected-object"
    assert response["successCount"] == len(expected_objects)
    with pytest.raises(ValueError):
        importer.validate_response(response, expected_objects)


def test_connection_refused_returns_exit_one_without_success_output(capsys):
    # Reserving but not listening prevents another process from taking this port.
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{reservation.getsockname()[1]}"
        exit_code = importer.main(["--url", url, "--file", str(OBJECTS_PATH)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Importación de Kibana fallida" in captured.err


@pytest.mark.parametrize("invalid_source", ["duplicate", "empty"])
def test_invalid_source_fails_before_any_http_request(tmp_path, expected_objects, capsys, invalid_source):
    content = OBJECTS_PATH.read_bytes().splitlines()
    if invalid_source == "duplicate":
        content[-1] = content[0]
    else:
        content = []
    invalid_path = tmp_path / "invalid.ndjson"
    invalid_path.write_bytes(b"\n".join(content) + b"\n")
    with local_import_endpoint(confirmed_result(expected_objects)) as (url, received):
        exit_code = importer.main(["--url", url, "--file", str(invalid_path)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert not received
    assert captured.out == ""
    assert "Importación de Kibana fallida" in captured.err
