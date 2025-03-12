#!/usr/bin/env python3
import sys
import re
import argparse
import html
import os

def convert_markdown_to_html(markdown_text, filename=None):
    # Make a copy of the original for processing
    html_text = markdown_text

    if filename:
        # Remove the file extension and replace hyphens/underscores with spaces
        title = re.sub(r'\.(md|markdown)$', '', filename)
        title = re.sub(r'[-_]', ' ', title)
        title = title.title()  # Capitalize first letter of each word
    else:
        title = "Converted Markdown"
    
    # Pre-process to protect code blocks from other transformations
    code_blocks = {}
    code_block_count = 0
    
    # Extract code blocks and replace with placeholders
    def save_code_block(match):
        nonlocal code_block_count
        code_content = match.group(1).strip()
        language = ""
        # Check if the first line specifies a language
        first_line_match = re.match(r'^(\w+)\s*\n', code_content)
        if first_line_match:
            language = first_line_match.group(1)
            code_content = code_content[len(language):].strip()
        
        placeholder = f"CODE_BLOCK_PLACEHOLDER_{code_block_count}"
        code_blocks[placeholder] = (code_content, language)
        code_block_count += 1
        return placeholder
    
    html_text = re.sub(r'```(.*?)```', save_code_block, html_text, flags=re.DOTALL)
    
    # Handle inline code (protect from other transformations)
    inline_codes = {}
    inline_code_count = 0
    
    def save_inline_code(match):
        nonlocal inline_code_count
        code = match.group(1)
        placeholder = f"INLINE_CODE_PLACEHOLDER_{inline_code_count}"
        inline_codes[placeholder] = code
        inline_code_count += 1
        return placeholder
    
    html_text = re.sub(r'`([^`]+)`', save_inline_code, html_text)
    
    # Handle Obsidian specific syntax
    
    # Internal links [[Page]] or [[Page|Display Text]]
    def process_internal_link(match):
        parts = match.group(1).split('|')
        if len(parts) == 1:
            page = parts[0].strip()
            display = page
        else:
            page = parts[0].strip()
            display = parts[1].strip()
        
        # Convert page to kebab-case for URL
        url = page.lower().replace(' ', '-')
        return f'<a href="{url}.html" class="internal-link">{display}</a>'
    
    html_text = re.sub(r'\[\[(.*?)\]\]', process_internal_link, html_text)
    
    # Handle headers with proper id attributes for linking
    def header_with_id(match):
        level = len(match.group(1))
        content = match.group(2).strip()
        header_id = re.sub(r'[^a-zA-Z0-9]', '-', content.lower())
        return f'<h{level} id="{header_id}">{content}</h{level}>'
    
    html_text = re.sub(r'^(#{1,6})\s+(.*?)$', header_with_id, html_text, flags=re.MULTILINE)
    
    # Handle callout blocks (Obsidian specific)
    def process_callout(match):
        callout_type = match.group(1).lower() if match.group(1) else "note"
        title = match.group(2) if match.group(2) else callout_type.capitalize()
        content = match.group(3)
        
        # Process the content as markdown
        content_html = content.strip()
        # Convert paragraphs
        content_html = re.sub(r'([^\n]+)\n\n', r'<p>\1</p>\n\n', content_html)
        
        return f'<div class="callout callout-{callout_type}">\n<div class="callout-title">{title}</div>\n<div class="callout-content">{content_html}</div>\n</div>'
    
    html_text = re.sub(r'> \[!(\w+)\](?: *(.+?))?\n((?:>.*(?:\n|$))+)', process_callout, html_text)
    
    # Handle bold
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    html_text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html_text)
    
    # Handle italic
    html_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_text)
    html_text = re.sub(r'_(.*?)_', r'<em>\1</em>', html_text)
    
    # Handle strikethrough (common in Obsidian)
    html_text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', html_text)
    
    # Handle highlighting (common in Obsidian)
    html_text = re.sub(r'==(.*?)==', r'<mark>\1</mark>', html_text)
    
    # Handle block quotes
    def process_blockquote(match):
        content = match.group(1)
        # Remove the > from the start of each line
        content = re.sub(r'^>\s?', '', content, flags=re.MULTILINE)
        # Process paragraphs within blockquote
        content = re.sub(r'([^\n]+)\n\n', r'<p>\1</p>\n\n', content)
        return f'<blockquote>{content}</blockquote>'
    
    html_text = re.sub(r'((?:^>\s?.*\n?)+)', process_blockquote, html_text, flags=re.MULTILINE)
    
    # Handle links
    html_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" class="external-link">\1</a>', html_text)
    
    # Handle images - Obsidian style
    html_text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1" class="markdown-image">', html_text)
    
    # Handle horizontal rules
    html_text = re.sub(r'^---$', '<hr>', html_text, flags=re.MULTILINE)
    html_text = re.sub(r'^___$', '<hr>', html_text, flags=re.MULTILINE)
    html_text = re.sub(r'^\*\*\*$', '<hr>', html_text, flags=re.MULTILINE)
    
    # Handle unordered lists with proper nesting
    def process_ul(match):
        content = match.group(0)
        list_html = process_list_items(content, 'ul')
        return list_html
        
    def process_list_items(content, list_type):
        lines = content.split('\n')
        result = []
        current_level = 0
        stack = [(0, [])]  # (indent_level, items)
        
        for line in lines:
            if not line.strip():
                continue
                
            # Check indent level and bullet/number
            if list_type == 'ul':
                match = re.match(r'^(\s*)[-*+]\s+(.*)', line)
            else:  # ol
                match = re.match(r'^(\s*)\d+\.\s+(.*)', line)
                
            if not match:
                # Add as content to the last item
                if stack[-1][1]:
                    stack[-1][1][-1] += ' ' + line.strip()
                continue
                
            indent = len(match.group(1))
            item_content = match.group(2)
            
            # Determine the correct level based on indentation
            if indent > stack[-1][0]:
                # Start a new nested list
                new_list_items = []
                stack.append((indent, new_list_items))
                # Add this new list as the last item's sublist
                parent_items = stack[-2][1]
                if parent_items:
                    if isinstance(parent_items[-1], str):
                        parent_items[-1] = [parent_items[-1], (list_type, new_list_items)]
                    else:
                        parent_items[-1].append((list_type, new_list_items))
            elif indent < stack[-1][0]:
                # Go back to appropriate level
                while stack and indent < stack[-1][0]:
                    stack.pop()
            
            # Add item at current level
            stack[-1][1].append(item_content)
        
        # Build HTML from the data structure
        return build_list_html(stack[0][1], list_type)
            
    def build_list_html(items, list_type):
        result = f'<{list_type}>\n'
        
        for item in items:
            if isinstance(item, str):
                result += f'  <li>{item}</li>\n'
            else:
                text = item[0]
                sublists = item[1:]
                result += f'  <li>{text}\n'
                
                for sublist_type, sublist_items in sublists:
                    result += build_list_html(sublist_items, sublist_type)
                    
                result += '  </li>\n'
                
        result += f'</{list_type}>\n'
        return result
    
    # Find list blocks
    ul_pattern = r'(?:^|\n)(?:[ \t]*[-*+][ \t]+.+\n?)+(?:\n|$)'
    html_text = re.sub(ul_pattern, process_ul, html_text, flags=re.MULTILINE)
    
    # Find ordered list blocks
    ol_pattern = r'(?:^|\n)(?:[ \t]*\d+\.[ \t]+.+\n?)+(?:\n|$)'
    def process_ol(match):
        return process_list_items(match.group(0), 'ol')
    
    html_text = re.sub(ol_pattern, process_ol, html_text, flags=re.MULTILINE)
    
    # Handle tables
    def process_table(match):
        table_str = match.group(0).strip()
        lines = table_str.split('\n')
        
        # Skip if not enough lines for a table (header, separator, and at least one row)
        if len(lines) < 3:
            return table_str
            
        # Check if second line contains only |, -, and whitespace (separator line)
        if not re.match(r'^[\s\|\-:]+$', lines[1]):
            return table_str
            
        # Extract alignment from separator line
        alignments = []
        for cell in lines[1].strip('|').split('|'):
            cell = cell.strip()
            if cell.startswith(':') and cell.endswith(':'):
                alignments.append('center')
            elif cell.endswith(':'):
                alignments.append('right')
            else:
                alignments.append('left')
        
        html = '<table>\n<thead>\n<tr>\n'
        
        # Process header row
        header_cells = [cell.strip() for cell in lines[0].strip('|').split('|')]
        for i, cell in enumerate(header_cells):
            alignment = alignments[i] if i < len(alignments) else 'left'
            html += f'  <th align="{alignment}">{cell}</th>\n'
        
        html += '</tr>\n</thead>\n<tbody>\n'
        
        # Process data rows
        for line in lines[2:]:
            if not line.strip():
                continue
                
            html += '<tr>\n'
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            
            for i, cell in enumerate(cells):
                alignment = alignments[i] if i < len(alignments) else 'left'
                html += f'  <td align="{alignment}">{cell}</td>\n'
                
            html += '</tr>\n'
            
        html += '</tbody>\n</table>'
        return html
    
    # Find table blocks (lines containing | characters)
    table_pattern = r'(?:^|\n)(?:[^\n]*\|[^\n]*\n){2,}(?:[^\n]*\|[^\n]*\n?)*'
    html_text = re.sub(table_pattern, process_table, html_text, flags=re.MULTILINE)
    
    # Restore code blocks
    for placeholder, (code, language) in code_blocks.items():
        escaped_code = html.escape(code)
        if language:
            html_text = html_text.replace(placeholder, f'<pre><code class="language-{language}">{escaped_code}</code></pre>')
        else:
            html_text = html_text.replace(placeholder, f'<pre><code>{escaped_code}</code></pre>')
    
    # Restore inline code
    for placeholder, code in inline_codes.items():
        escaped_code = html.escape(code)
        html_text = html_text.replace(placeholder, f'<code>{escaped_code}</code>')
    
    # Handle paragraphs (must be done last)
    paragraphs = []
    in_special_block = False
    paragraph_buffer = []
    
    for line in html_text.split('\n'):
        # Skip if we're in a special block
        if line.strip() == '':
            if paragraph_buffer:
                # Flush paragraph buffer
                paragraphs.append(f'<p>{" ".join(paragraph_buffer)}</p>')
                paragraph_buffer = []
            paragraphs.append('')
            continue
        
        # Check if line is start of a special block
        if line.startswith(('<h1', '<h2', '<h3', '<h4', '<h5', '<h6', '<ul', '<ol', '<pre', '</ul', '</ol', '</pre', '<hr', '<table', '<blockquote', '<div class="callout')):
            # Flush paragraph buffer before starting special block
            if paragraph_buffer:
                paragraphs.append(f'<p>{" ".join(paragraph_buffer)}</p>')
                paragraph_buffer = []
            in_special_block = True
            paragraphs.append(line)
            continue
        
        # Check if line is end of a special block
        if line.startswith(('</h1', '</h2', '</h3', '</h4', '</h5', '</h6', '</ul', '</ol', '</pre', '</table', '</blockquote', '</div>')):
            in_special_block = False
            paragraphs.append(line)
            continue
        
        # If in special block, add line as is
        if in_special_block:
            paragraphs.append(line)
        else:
            # Not in a special block, add to paragraph buffer
            paragraph_buffer.append(line.strip())
    
    # Don't forget any remaining content in paragraph buffer
    if paragraph_buffer:
        paragraphs.append(f'<p>{" ".join(paragraph_buffer)}</p>')
    
    html_text = '\n'.join(paragraphs)
    
    # Add section divs around headers and their content
    def add_sections(html_content):
        # First, split by h1, h2, etc.
        pattern = r'<h[1-6][^>]*>.*?</h[1-6]>'
        sections = re.split(pattern, html_content)
        headers = re.findall(pattern, html_content)
        
        # Reconstruct with section divs
        result = []
        
        # Add intro content before first header if it exists
        if sections[0].strip():
            result.append(f'<div class="section intro">{sections[0]}</div>')
        
        # Combine headers with their respective content
        for i in range(len(headers)):
            if i < len(sections) - 1:
                header_content = re.sub(r'<.*?>', '', headers[i])
                section_id = re.sub(r'[^a-zA-Z0-9]', '-', header_content.lower())
                header_level = re.search(r'<h(\d)', headers[i]).group(1)
                result.append(f'<div class="section section-h{header_level}" id="section-{section_id}">{headers[i]}{sections[i+1]}</div>')
        
        return ''.join(result)
    
    html_text = add_sections(html_text)
    
    # Create the complete HTML document with meta tags and responsive design
    html_document = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Converted from Obsidian Markdown: {title}">
    <title>{title}</title>
    <link rel="stylesheet" href="/css/blog.css">
    <style>
        /* Additional styles for Obsidian-specific elements */
        .callout {
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 5px;
            border-left: 4px solid #4b6bfb;
            background-color: rgba(75, 107, 251, 0.1);
        }
        .callout-title {
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .callout-note { border-left-color: #4b6bfb; background-color: rgba(75, 107, 251, 0.1); }
        .callout-info { border-left-color: #0288d1; background-color: rgba(2, 136, 209, 0.1); }
        .callout-warning { border-left-color: #ffa726; background-color: rgba(255, 167, 38, 0.1); }
        .callout-danger { border-left-color: #ef5350; background-color: rgba(239, 83, 80, 0.1); }
        .callout-success { border-left-color: #66bb6a; background-color: rgba(102, 187, 106, 0.1); }
        .internal-link { color: #7c3aed; text-decoration: none; border-bottom: 1px dotted; }
        .internal-link:hover { text-decoration: underline; }
        mark { background-color: #fff176; padding: 0 2px; }
        .markdown-image { max-width: 100%; height: auto; display: block; margin: 1rem 0; }
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
        <article class="obsidian-content">
            {html_text}
        </article>
        <div class="section">
            <a href="/blogs/picoCTF/picoCTF.html" class="read-more">← Back to All Challenges</a>
        </div>
        <footer>
            <p>&copy; 2025 T4QI. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>'''
    
    return html_document

def main():
    parser = argparse.ArgumentParser(description='Convert Obsidian Markdown to HTML with custom styling')
    parser.add_argument('input_file', nargs='?', type=argparse.FileType('r', encoding='utf-8'), default=sys.stdin,
                        help='Input Obsidian Markdown file (default: stdin)')
    parser.add_argument('output_file', nargs='?', type=argparse.FileType('w', encoding='utf-8'), default=sys.stdout,
                        help='Output HTML file (default: stdout)')
    parser.add_argument('--add-nav', action='store_true', help='Add navigation menu from document headers')
    parser.add_argument('--graph-view', action='store_true', help='Add a visualization of document connections')
    
    args = parser.parse_args()
    
    markdown_text = args.input_file.read()
    
    # Get the filename if available
    filename = None
    if hasattr(args.input_file, 'name') and args.input_file.name != '<stdin>':
        filename = os.path.basename(args.input_file.name)
    
    html_output = convert_markdown_to_html(markdown_text, filename)
    
    # Optional: Add document-based navigation if requested
    if args.add_nav:
        # Extract headers to build navigation
        headers = re.findall(r'<h([1-6])[^>]*id="([^"]+)">(.*?)</h\1>', html_output)
        if headers:
            nav_items = []
            for level, header_id, header_text in headers:
                indent = '  ' * (int(level) - 1)
                nav_items.append(f'{indent}<li class="nav-h{level}"><a href="#section-{header_id}">{header_text}</a></li>')
            
            nav_html = f'''<div class="page-nav">
    <h2>Table of Contents</h2>
    <ul class="nav-list">
        {''.join(nav_items)}
    </ul>
</div>'''
            
            # Insert navigation after the article opening tag
            html_output = html_output.replace('<article class="obsidian-content">', f'<article class="obsidian-content">\n{nav_html}')
    
    # Optional: Add graph view visualization
    if args.graph_view and filename:
        # Extract all internal links
        internal_links = re.findall(r'<a href="([^"]+)" class="internal-link">', html_output)
        if internal_links:
            # Create a simple visualization placeholder
            graph_html = f'''<div class="graph-view">
    <h2>Document Connections</h2>
    <p>This document links to {len(set(internal_links))} other documents.</p>
    <ul class="link-list">
        {''.join(f'<li><a href="{link}">{link.replace(".html", "").replace("-", " ").title()}</a></li>' for link in sorted(set(internal_links)))}
    </ul>
</div>'''
            
            # Add before footer
            html_output = html_output.replace('<div class="section">', f'{graph_html}\n<div class="section">')
    
    args.output_file.write(html_output)

if __name__ == "__main__":
    main()