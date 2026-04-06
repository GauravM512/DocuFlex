import json
import os
import sys

import uno  # pyright: ignore[reportMissingImports]
from com.sun.star.beans import PropertyValue  # pyright: ignore[reportMissingImports]


LO_ACCEPTOR = "uno:socket,host=localhost,port=8100;urp;StarOffice.ComponentContext"


def connect_desktop():
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )

    ctx = resolver.resolve(LO_ACCEPTOR)
    smgr = ctx.ServiceManager
    return smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)


def convert_file(desktop, input_path, output_path):
    """Converts a single file using an already-connected desktop."""

    input_url = "file:///" + os.path.abspath(input_path).replace("\\", "/")
    output_url = "file:///" + os.path.abspath(output_path).replace("\\", "/")

    props = (PropertyValue("Hidden", 0, True, 0),)
    doc = desktop.loadComponentFromURL(input_url, "_blank", 0, props)
    if not doc:
        raise RuntimeError("Could not load document (format unsupported?).")

    filter_name = "writer_pdf_Export"
    if input_path.lower().endswith((".xls", ".xlsx", ".ods", ".csv")):
        filter_name = "calc_pdf_Export"
    elif input_path.lower().endswith((".ppt", ".pptx", ".odp")):
        filter_name = "impress_pdf_Export"

    export_props = (PropertyValue("FilterName", 0, filter_name, 0),)
    try:
        doc.storeToURL(output_url, export_props)
    finally:
        doc.close(True)


def serve() -> None:
    try:
        desktop = connect_desktop()
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"CONNECTION_ERROR: {exc}"}), file=sys.stderr)
        sys.exit(1)

    print(json.dumps({"status": "ready"}), flush=True)

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            command = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"ok": False, "error": "Invalid command payload"}), flush=True)
            continue

        if command.get("action") == "shutdown":
            print(json.dumps({"ok": True, "action": "shutdown"}), flush=True)
            break

        input_path = command.get("input_path")
        output_path = command.get("output_path")
        if not input_path or not output_path:
            print(json.dumps({"ok": False, "error": "Missing input or output path"}), flush=True)
            continue

        try:
            convert_file(desktop, input_path, output_path)
            print(json.dumps({"ok": True}), flush=True)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}), flush=True)


def run_once(input_path: str, output_path: str) -> int:
    try:
        desktop = connect_desktop()
        convert_file(desktop, input_path, output_path)
        return 0
    except Exception as exc:
        print(f"CONVERSION_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--serve":
        serve()
    elif len(sys.argv) == 3:
        sys.exit(run_once(sys.argv[1], sys.argv[2]))
    else:
        print("Usage: uno_worker.py <input_file> <output_file> | uno_worker.py --serve", file=sys.stderr)
        sys.exit(1)