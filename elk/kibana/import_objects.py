"""Importación local opcional con validación JSON; Compose utiliza import.sh y curl."""

import argparse
import json
from pathlib import Path
import sys
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4


def read_objects(path: Path) -> tuple[bytes, set[tuple[str, str]]]:
    content = path.read_bytes()
    objects = [json.loads(line) for line in content.splitlines() if line.strip()]
    expected = {(item["type"], item["id"]) for item in objects}
    if not objects or len(expected) != len(objects):
        raise ValueError("Se requiere un archivo no vacío con objetos únicos")
    return content, expected


def validate_response(result: dict, expected: set[tuple[str, str]]) -> None:
    if not isinstance(result, dict) or result.get("success") is not True:
        raise ValueError("Kibana no confirmó success=true")
    if result.get("errors") not in (None, []):
        raise ValueError("Kibana devolvió errores de importación")
    count = result.get("successCount")
    if type(count) is not int or count != len(expected):
        raise ValueError("Kibana no importó la cantidad esperada de objetos")
    results = result.get("successResults")
    if not isinstance(results, list) or len(results) != len(expected):
        raise ValueError("Falta la confirmación individual de los objetos importados")
    actual = {(item.get("type"), item.get("id")) for item in results if isinstance(item, dict)}
    if actual != expected:
        raise ValueError("Los objetos importados no coinciden con los esperados")


def import_objects(base_url: str, path: Path) -> dict:
    content, expected = read_objects(path)
    boundary = "cuponmania-" + uuid4().hex
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="saved-objects.ndjson"\r\n'
        "Content-Type: application/x-ndjson\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    request = Request(
        base_url.rstrip("/") + "/api/saved_objects/_import?overwrite=true",
        data=body,
        headers={"kbn-xsrf": "true", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with build_opener(ProxyHandler({})).open(request, timeout=60) as response:
        result = json.load(response)
    validate_response(result, expected)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://kibana:5601")
    parser.add_argument("--file", type=Path, default=Path(__file__).with_name("saved-objects.ndjson"))
    args = parser.parse_args(argv)
    try:
        result = import_objects(args.url, args.file)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Importación de Kibana fallida: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
