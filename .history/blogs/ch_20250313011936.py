import re
import argparse
import os
from pathlib import Path

def convert_obsidian_to_html(text):
    """
    Convert Obsidian markdown to HTML.
    """
    # Store converted text
    html = text
    
    # Handle wiki links [[Page]] or [[Page|Display Text]]
    def wiki_link_replacer(match):
        content = match.group(1)
        if "|" in content:
            page, display = content.split("|", 1)
            return f'<a href="{page.strip().replace(" ", "-").lower()}.html">{display.strip()}</a>'
        else:
            page = content.strip()
            return f'<a href="{page.replace(" ", "-").lower()}.html">{page}</a>'
    
    html = re.sub(r'\[\[(.*?)\]\]', wiki_link_replacer, html)
    
    # Handle headers
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.*?)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^###### (.*?)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    
    # Handle bold and italic
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    html = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html)
    html = re.sub(r'_(.*?)_', r'<em>\1</em>', html)
    
    # Handle code blocks
    html = re.sub(r'```(.*?)\n(.*?)```', r'<pre><code class="\1">\2</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
    
    # Handle lists
    # This is simplified and may need more complex handling for nested lists
    html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^(\d+)\. (.*?)$', r'<li>\2</li>', html, flags=re.MULTILINE)
    
    # Wrap consecutive list items in ul or ol tags
    html = re.sub(r'(<li>.*?</li>)\n(<li>.*?</li>)', r'\1\2', html, flags=re.DOTALL)
    html = re.sub(r'(^|\n)(<li>.*?</li>)(\n|$)', r'\1<ul>\2</ul>\3', html, flags=re.DOTALL)
    
    # Handle blockquotes
    html = re.sub(r'^> (.*?)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
    
    # Handle horizontal rules
    html = re.sub(r'^---+$', r'<hr />', html, flags=re.MULTILINE)
    
    # Handle links [text](url)
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
    
    # Handle images ![alt](url)
    html = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1" />', html)
    
    # Handle paragraphs (simplified)
    # We need to ensure we don't wrap already wrapped elements in <p> tags
    # This is a simplified approach and may need refinement
    lines = html.split('\n')
    in_paragraph = False
    result = []
    
    for line in lines:
        if line.strip() == '':
            if in_paragraph:
                result.append('</p>')
                in_paragraph = False
            result.append('')
        elif not re.match(r'^<(h\d|ul|ol|li|blockquote|pre|hr)', line):
            if not in_paragraph:
                result.append('<p>')
                in_paragraph = True
            result.append(line)
        else:
            if in_paragraph:
                result.append('</p>')
                in_paragraph = False
            result.append(line)
    
    if in_paragraph:
        result.append('</p>')
    
    html = '\n'.join(result)
    
    # Obsidian callouts (:::) - simplified version
    # Example: > [!note] This is a note
    html = re.sub(r'> \[!(.*?)\](.*?)$', r'<div class="callout callout-\1">\2</div>', html, flags=re.MULTILINE)
    
    # Obsidian tags
    html = re.sub(r'#(\w+)', r'<span class="tag">#\1</span>', html)
    
    return html

def wrap_with_html_document(body_html, title="Converted from Obsidian"):
    """
    Wrap the converted HTML content with proper HTML document structure.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .callout {{ background-color: #f8f9fa; border-left: 4px solid #6c757d; padding: 10px 15px; margin: 15px 0; }}
        .callout-note {{ border-left-color: #0d6efd; }}
        .callout-warning {{ border-left-color: #ffc107; }}
        .callout-danger {{ border-left-color: #dc3545; }}
        .callout-info {{ border-left-color: #0dcaf0; }}
        .callout-success {{ border-left-color: #198754; }}
        .tag {{ color: #6610f2; }}
        pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        blockquote {{ border-left: 3px solid #ced4da; padding-left: 15px; color: #6c757d; }}
    </style>
</head>
<body>
{body_html}
</body>
</html>"""

def process_file(input_file, output_dir=None):
    """
    Process a single markdown file and convert it to HTML.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Convert content
    html_content = convert_obsidian_to_html(content)
    
    # Wrap with HTML document
    title = os.path.basename(input_file).replace('.md', '')
    full_html = wrap_with_html_document(html_content, title)
    
    # Determine output path
    if output_dir:
        output_path = os.path.join(output_dir, os.path.basename(input_file).replace('.md', '.html'))
    else:
        output_path = input_file.replace('.md', '.html')
    
    # Write output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    return output_path

def process_directory(input_dir, output_dir=None):
    """
    Process all markdown files in a directory and its subdirectories.
    """
    if not output_dir:
        output_dir = input_dir
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    converted_files = []
    
    for root, dirs, files in os.walk(input_dir):
        # Determine the relative path to maintain directory structure
        rel_path = os.path.relpath(root, input_dir) if root != input_dir else ''
        current_output_dir = os.path.join(output_dir, rel_path) if rel_path else output_dir
        
        # Create the corresponding output directory
        if not os.path.exists(current_output_dir):
            os.makedirs(current_output_dir)
        
        # Process markdown files
        for file in files:
            if file.endswith('.md'):
                input_path = os.path.join(root, file)
                output_path = os.path.join(current_output_dir, file.replace('.md', '.html'))
                
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Convert content
                    html_content = convert_obsidian_to_html(content)
                    
                    # Wrap with HTML document
                    title = file.replace('.md', '')
                    full_html = wrap_with_html_document(html_content, title)
                    
                    # Write output file
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(full_html)
                    
                    converted_files.append((input_path, output_path))
                except Exception as e:
                    print(f"Error processing {input_path}: {e}")
    
    return converted_files

def main():
    parser = argparse.ArgumentParser(description='Convert Obsidian Markdown files to HTML.')
    parser.add_argument('input', help='Input markdown file or directory')
    parser.add_argument('-o', '--output', help='Output HTML file or directory')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        if not input_path.name.endswith('.md'):
            print(f"Error: Input file must be a markdown file (.md): {input_path}")
            return
        
        output_path = process_file(str(input_path), args.output)
        print(f"Converted {input_path} to {output_path}")
    
    elif input_path.is_dir():
        converted_files = process_directory(str(input_path), args.output)
        print(f"Converted {len(converted_files)} files:")
        for input_file, output_file in converted_files:
            print(f"  {input_file} -> {output_file}")
    
    else:
        print(f"Error: Input path does not exist: {input_path}")

if __name__ == "__main__":
    main()