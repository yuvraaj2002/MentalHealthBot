#!/usr/bin/env python3
"""
Simple Markdown to HTML Converter
Basic converter that takes file path as command line argument
"""

import sys
import os
import markdown
from pathlib import Path

def convert_md_to_html(md_file_path):
    """
    Convert Markdown file to HTML
    
    Args:
        md_file_path: Path to the Markdown file
        
    Returns:
        str: Path to the generated HTML file
    """
    try:
        # Check if file exists
        if not os.path.exists(md_file_path):
            print(f"❌ Error: File '{md_file_path}' not found")
            return None
        
        # Read Markdown file
        with open(md_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['fenced_code', 'tables', 'toc', 'codehilite']
        )
        
        # Create HTML document
        html_document = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{Path(md_file_path).stem}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #333;
            margin-top: 2rem;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""
        
        # Generate output filename
        output_path = Path(md_file_path).with_suffix('.html')
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_document)
        
        print(f"✅ Successfully converted: {md_file_path} → {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"❌ Error converting {md_file_path}: {str(e)}")
        return None

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python simple_md_converter.py <markdown_file_path>")
        print("Example: python simple_md_converter.py README.md")
        sys.exit(1)
    
    md_file_path = sys.argv[1]
    html_path = convert_md_to_html(md_file_path)
    
    if html_path:
        print(f"🎉 Conversion completed! HTML file: {html_path}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
