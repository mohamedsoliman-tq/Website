#!/usr/bin/env python3
import sys
import re
import argparse
import html

def convert_markdown_to_html(markdown_text):
    html_text = markdown_text
    
    # Handle headers
    html_text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_text, flags=re.MULTILINE)
    html_text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_text, flags=re.MULTILINE)
    html_text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_text, flags=re.MULTILINE)
    html_text = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html_text, flags=re.MULTILINE)
    html_text = re.sub(r'^##### (.*?)$', r'<h5>\1</h5>', html_text, flags=re.MULTILINE)
    html_text = re.sub(r'^###### (.*?)$', r'<h6>\1</h6>', html_text, flags=re.MULTILINE)
    
    # Handle bold
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    html_text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html_text)
    
    # Handle italic
    html_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_text)
    html_text = re.sub(r'_(.*?)_', r'<em>\1</em>', html_text)
    
    # Handle code blocks
    html_text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html_text, flags=re.DOTALL)
    
    # Handle inline code
    html_text = re.sub(r'`(.*?)`', r'<code>\1</code>', html_text)
    
    # Handle links
    html_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" class="read-more">\1</a>', html_text)
    
    # Handle images
    html_text = re.sub(r'!\[\[(.*?)\]\]', r'<img src="pics/\1" alt="\1">', html_text)
    html_text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1">', html_text)
    
    # Handle horizontal rules
    html_text = re.sub(r'^---$', '<hr>', html_text, flags=re.MULTILINE)
    
    # Handle unordered lists - fixed to include indented content
    def replace_ul(match):
        content = match.group(0)
        # Split by list item markers
        items = re.split(r'(?=^\* )', content, flags=re.MULTILINE)
        items = [item for item in items if item.strip()]
        
        list_html = '<ul>\n'
        for item in items:
            # Remove the list marker from the first line
            item_content = re.sub(r'^\* ', '', item)
            # Replace newlines within the item with spaces or <br> tags as needed
            item_content = re.sub(r'\n\s+', ' ', item_content)
            list_html += f'  <li>{item_content}</li>\n'
        list_html += '</ul>'
        return list_html
    
    # Find unordered list blocks (bullet points and their content)
    html_text = re.sub(r'(^\* .*?(?:\n\s+.*?)*)(?:\n(?!\s+)|\Z)', replace_ul, html_text, flags=re.MULTILINE | re.DOTALL)
    
    # Handle ordered lists - fixed to include indented content
    def replace_ol(match):
        content = match.group(0)
        # Split by ordered list item markers (e.g., "1. ", "2. ")
        items = re.split(r'(?=^\d+\. )', content, flags=re.MULTILINE)
        items = [item for item in items if item.strip()]
        
        list_html = '<ol>\n'
        for item in items:
            # Remove the list marker from the first line (e.g., "1. ")
            item_content = re.sub(r'^\d+\. ', '', item)
            # Preserve paragraph structure within list items but join consecutive lines
            item_content = re.sub(r'\n\s+', ' ', item_content)
            list_html += f'  <li>{item_content}</li>\n'
        list_html += '</ol>'
        return list_html
    
    # Find ordered list blocks (numbered items and their content)
    html_text = re.sub(r'(^\d+\. .*?(?:\n\s+.*?)*)(?:\n(?!\s+)|\Z)', replace_ol, html_text, flags=re.MULTILINE | re.DOTALL)
    
    # Handle paragraphs (must be done last)
    paragraphs = []
    in_special_block = False
    
    for line in html_text.split('\n'):
        if line.strip() == '':
            in_special_block = False
            paragraphs.append(line)
            continue
            
        if line.startswith(('<h1>', '<h2>', '<h3>', '<h4>', '<h5>', '<h6>', '<ul>', '<ol>', '<pre>', '</ul>', '</ol>', '</pre>', '<hr>')):
            in_special_block = True
            paragraphs.append(line)
            continue
            
        if not in_special_block and not line.startswith(('  <li>', '</ul>', '</ol>')):
            paragraphs.append(f'<p>{line}</p>')
        else:
            paragraphs.append(line)
            
    html_text = '\n'.join(paragraphs)
    
    # Add section divs around headers and their content
    def add_sections(html_content):
        # First, split by h1, h2, etc.
        pattern = r'<h[1-6]>.*?</h[1-6]>'
        sections = re.split(pattern, html_content)
        headers = re.findall(pattern, html_content)
        
        # Reconstruct with section divs
        result = []
        
        # Add intro content before first header if it exists
        if sections[0].strip():
            result.append(f'<div class="section">{sections[0]}</div>')
        
        # Combine headers with their respective content
        for i in range(len(headers)):
            if i < len(sections) - 1:
                section_id = re.sub(r'[^a-zA-Z0-9]', '-', re.sub(r'<.*?>', '', headers[i]).lower())
                result.append(f'<div class="section" id="{section_id}">{headers[i]}{sections[i+1]}</div>')
        
        return ''.join(result)
    
    html_text = add_sections(html_text)
    
    # Custom CSS based on provided styles
    custom_css = '''
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;700&display=swap');

    :root {
        --primary-black: #000000;
        --green-accent: #78BE20;
        --dark-green: #5a9419;
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: 'Space Grotesk', sans-serif;
    }

    body {
        background-color: var(--primary-black);
        color: var(--green-accent);
        line-height: 1.6;
    }

    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }

    .section {
        padding: 4rem 0;
        border-bottom: 1px solid #001a00;
    }

    /* Navigation Styles */
    nav {
        background: rgba(0, 0, 0, 0.95);
        padding: 1rem;
        position: sticky;
        top: 0;
        border-bottom: 2px solid var(--green-accent);
        z-index: 100;
    }

    nav ul {
        display: flex;
        justify-content: space-around;
        list-style: none;
    }

    nav a {
        color: var(--green-accent);
        text-decoration: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }

    nav a:hover {
        color: var(--dark-green);
        text-shadow: 0 0 10px var(--green-accent);
    }

    /* Hero Section Styles */
    .hero {
        text-align: center;
        padding: 4rem 0;
        background: linear-gradient(45deg, var(--primary-black), #001100);
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--green-accent);
        margin-bottom: 1rem;
    }

    h1 {
        font-size: 3.5rem;
        text-shadow: 0 0 15px var(--green-accent);
    }

    h2 {
        font-size: 2.5rem;
    }

    p {
        color: var(--dark-green);
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }

    /* Code blocks */
    pre {
        background: #000a00;
        padding: 1.5rem;
        border-radius: 5px;
        border: 1px solid var(--green-accent);
        overflow-x: auto;
        margin: 1.5rem 0;
    }

    code {
        font-family: monospace;
        color: var(--green-accent);
    }

    /* List styling */
    ul, ol {
        margin-left: 2rem;
        margin-bottom: 1.5rem;
        color: var(--dark-green);
    }

    li {
        margin-bottom: 0.5rem;
    }

    /* Links */
    a {
        color: var(--green-accent);
        text-decoration: none;
        transition: all 0.3s;
    }

    a:hover {
        color: var(--dark-green);
        text-shadow: 0 0 10px var(--green-accent);
    }

    .read-more {
        display: inline-block;
        margin-top: 10px;
        padding: 8px 12px;
        font-size: 1rem;
        font-weight: bold;
        color: var(--green-accent);
        text-decoration: none;
        border: 1px solid var(--green-accent);
        border-radius: 5px;
        transition: all 0.3s ease;
    }

    .read-more:hover {
        background-color: var(--green-accent);
        color: var(--primary-black);
        box-shadow: 0 0 10px var(--green-accent);
    }

    /* Images */
    img {
        max-width: 100%;
        border: 1px solid var(--green-accent);
        border-radius: 5px;
        margin: 1rem 0;
    }

    /* Horizontal rule */
    hr {
        border: none;
        height: 1px;
        background-color: var(--green-accent);
        margin: 2rem 0;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        h1 {
            font-size: 2.5rem;
        }
        
        .container {
            padding: 1rem;
        }
        
        .section {
            padding: 2rem 0;
        }
    }

    footer {
        text-align: center;
        padding: 2rem;
        color: var(--green-accent);
    }
    '''
    
    # Create the complete HTML document
    html_document = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converted Markdown</title>
    <style>
{custom_css}
    </style>
</head>
<body>
    <nav>
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/Projects.html">Projects</a></li>
            <li><a href="/Blogs.html">Blog</a></li>
        </ul>
    </nav>
    <div class="container">
{html_text}
        <footer>
        <p>&copy; 2025 T4QI. All rights reserved.</p>
    </footer>
    </div>
</body>
</html>'''
    
    return html_document

def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to HTML with custom styling')
    parser.add_argument('input_file', nargs='?', type=argparse.FileType('r', encoding='utf-8'), default=sys.stdin,
                        help='Input Markdown file (default: stdin)')
    parser.add_argument('output_file', nargs='?', type=argparse.FileType('w', encoding='utf-8'), default=sys.stdout,
                        help='Output HTML file (default: stdout)')
    parser.add_argument('--add-nav', action='store_true', help='Add navigation menu')
    
    args = parser.parse_args()
    
    markdown_text = args.input_file.read()
    html_output = convert_markdown_to_html(markdown_text)
    
    # Optional: Add navigation if requested
    if args.add_nav:
        # Extract headers to build navigation
        headers = re.findall(r'<h[1-6]>(.*?)</h[1-6]>', html_output)
        nav_items = []
        for header in headers:
            header_id = re.sub(r'[^a-zA-Z0-9]', '-', header.lower())
            nav_items.append(f'<li><a href="#{header_id}">{header}</a></li>')
        
        nav_html = f'''<nav>
    <ul>
        {''.join(nav_items)}
    </ul>
</nav>'''
        
        # Insert navigation after body tag
        html_output = html_output.replace('<body>', f'<body>\n{nav_html}')
    
    args.output_file.write(html_output)

if __name__ == "__main__":
    main()