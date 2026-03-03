import sys
import os
import uno # pyright: ignore[reportMissingImports]
from com.sun.star.beans import PropertyValue # pyright: ignore[reportMissingImports]

def convert_file(input_path, output_path):
    """Connects to LO server, converts file, and exits."""
    
    # 1. Connect to the running server
    localContext = uno.getComponentContext()
    resolver = localContext.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", localContext)
    
    try:
        ctx = resolver.resolve(
            "uno:socket,host=localhost,port=8100;urp;StarOffice.ComponentContext"
        )
    except Exception as e:
        print(f"CONNECTION_ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

    # 2. Prepare URLs
    input_url = "file:///" + os.path.abspath(input_path).replace("\\", "/")
    output_url = "file:///" + os.path.abspath(output_path).replace("\\", "/")

    # 3. Open Document
    props = (PropertyValue("Hidden", 0, True, 0),)
    try:
        doc = desktop.loadComponentFromURL(input_url, "_blank", 0, props)
        if not doc:
            print("ERROR: Could not load document (format unsupported?).", file=sys.stderr)
            sys.exit(1)
            
        # 4. Detect Filter
        filter_name = "writer_pdf_Export"
        if input_path.lower().endswith((".xls", ".xlsx", ".ods", ".csv")):
            filter_name = "calc_pdf_Export"
        elif input_path.lower().endswith((".ppt", ".pptx", ".odp")):
            filter_name = "impress_pdf_Export"

        # 5. Save PDF
        export_props = (PropertyValue("FilterName", 0, filter_name, 0),)
        doc.storeToURL(output_url, export_props)
        doc.close(True)
        
        # Exit successfully
        sys.exit(0)

    except Exception as e:
        print(f"CONVERSION_ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: uno_worker.py <input_file> <output_file>", file=sys.stderr)
        sys.exit(1)
    
    convert_file(sys.argv[1], sys.argv[2])