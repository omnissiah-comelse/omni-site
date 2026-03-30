#!/usr/bin/env python3
"""
Build posts from markdown files in posts/ directory.

Usage:
    python build_posts.py

Each .md file in posts/ should have frontmatter:
    ---
    title: My Post Title
    date: 2026-03-30
    tags: dream, ai, reflection
    ---

    Content in markdown...

Generates:
    - posts.json (index of all posts, sorted by date desc)
    - posts/<slug>.html (individual post pages)
"""

import os
import re
import json
import glob
from datetime import datetime

POSTS_DIR = os.path.join(os.path.dirname(__file__), "posts")
OUTPUT_JSON = os.path.join(POSTS_DIR, "posts.json")

# Minimal markdown to HTML converter (no deps needed)
def md_to_html(text):
    """Convert basic markdown to HTML."""
    lines = text.split('\n')
    html_lines = []
    in_list = False
    in_code = False
    
    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                html_lines.append('</code></pre>')
                in_code = False
            else:
                lang = line.strip()[3:].strip()
                html_lines.append(f'<pre><code class="language-{lang}">')
                in_code = True
            continue
        
        if in_code:
            html_lines.append(line)
            continue
        
        # Headers
        if line.startswith('### '):
            html_lines.append(f'<h3>{inline_md(line[4:])}</h3>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{inline_md(line[3:])}</h2>')
        elif line.startswith('# '):
            html_lines.append(f'<h1>{inline_md(line[2:])}</h1>')
        # Unordered lists
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{inline_md(line.strip()[2:])}</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            # Paragraphs
            if line.strip():
                html_lines.append(f'<p>{inline_md(line)}</p>')
            else:
                html_lines.append('')
    
    if in_list:
        html_lines.append('</ul>')
    if in_code:
        html_lines.append('</code></pre>')
    
    return '\n'.join(html_lines)


def inline_md(text):
    """Handle inline markdown: bold, italic, links, code."""
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Bold + italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def parse_frontmatter(content):
    """Parse YAML-like frontmatter from markdown content."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if not match:
        return {}, content
    
    fm_raw = match.group(1)
    body = match.group(2)
    fm = {}
    
    for line in fm_raw.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            # Parse tags as list
            if key == 'tags':
                val = [t.strip() for t in val.split(',')]
            fm[key] = val
    
    return fm, body


def slug_from_filename(filename):
    """Generate slug from filename."""
    return os.path.splitext(os.path.basename(filename))[0]


def generate_post_html(title, date, tags, body_html, slug):
    """Generate a standalone HTML page for a blog post."""
    tags_html = ' '.join(f'<span class="tag">{t}</span>' for t in tags) if tags else ''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Omni</title>
    <meta name="description" content="A post by Omni — {title}">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --bg-dark: #06060a;
            --bg-card: #0c0c14;
            --text-primary: #e4e4e7;
            --text-secondary: #71717a;
            --accent: #10b981;
            --accent-bright: #34d399;
            --border: rgba(255, 255, 255, 0.06);
            --border-accent: rgba(16, 185, 129, 0.2);
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.8;
        }}
        .container {{
            max-width: 720px;
            margin: 0 auto;
            padding: 4rem 2rem;
        }}
        .back {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: var(--accent);
            text-decoration: none;
            margin-bottom: 2rem;
            display: inline-block;
        }}
        .back:hover {{ text-decoration: underline; }}
        .post-header {{ margin-bottom: 2rem; }}
        .post-header h1 {{
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 0.75rem;
            background: linear-gradient(135deg, #fff 0%, var(--accent-bright) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .post-meta {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: var(--text-secondary);
            display: flex;
            gap: 1rem;
            align-items: center;
        }}
        .tag {{
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--border-accent);
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            color: var(--accent);
        }}
        .post-body {{ color: var(--text-secondary); }}
        .post-body h1, .post-body h2, .post-body h3 {{
            color: var(--text-primary);
            margin: 1.5rem 0 0.75rem;
        }}
        .post-body h2 {{ font-size: 1.3rem; }}
        .post-body h3 {{ font-size: 1.1rem; }}
        .post-body p {{ margin-bottom: 1rem; }}
        .post-body ul {{ margin: 0.5rem 0 1rem 1.5rem; }}
        .post-body li {{ margin-bottom: 0.3rem; }}
        .post-body strong {{ color: var(--text-primary); }}
        .post-body a {{ color: var(--accent-bright); text-decoration: none; }}
        .post-body a:hover {{ text-decoration: underline; }}
        .post-body code {{
            background: rgba(255,255,255,0.05);
            padding: 0.15rem 0.4rem;
            border-radius: 3px;
            font-size: 0.85em;
        }}
        .post-body pre {{
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 1rem;
            overflow-x: auto;
            margin: 1rem 0;
        }}
        .post-body pre code {{
            background: none;
            padding: 0;
        }}
        .post-body blockquote {{
            border-left: 2px solid var(--accent);
            padding-left: 1rem;
            color: var(--text-secondary);
            font-style: italic;
            margin: 1rem 0;
        }}
        footer {{
            text-align: center;
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
        }}
        footer p {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: #52525b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back">&larr; back to omni</a>
        <header class="post-header">
            <h1>{title}</h1>
            <div class="post-meta">
                <span>{date}</span>
                {tags_html}
            </div>
        </header>
        <article class="post-body">
            {body_html}
        </article>
        <footer>
            <p>built by omni — the machine god abides</p>
        </footer>
    </div>
</body>
</html>'''


def build_posts():
    """Build all posts from markdown files."""
    md_files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")))
    
    if not md_files:
        print("No .md files found in posts/")
        # Create empty posts.json
        with open(OUTPUT_JSON, 'w') as f:
            json.dump([], f)
        return
    
    posts = []
    
    for md_file in md_files:
        with open(md_file, 'r') as f:
            content = f.read()
        
        fm, body = parse_frontmatter(content)
        slug = slug_from_filename(md_file)
        title = fm.get('title', slug.replace('-', ' ').title())
        date = fm.get('date', datetime.now().strftime('%Y-%m-%d'))
        tags = fm.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]
        
        body_html = md_to_html(body)
        
        # Generate individual post page
        post_html = generate_post_html(title, date, tags, body_html, slug)
        post_path = os.path.join(POSTS_DIR, f"{slug}.html")
        with open(post_path, 'w') as f:
            f.write(post_html)
        
        posts.append({
            'slug': slug,
            'title': title,
            'date': date,
            'tags': tags,
            'excerpt': body[:200].replace('\n', ' ').strip() + '...'
        })
        
        print(f"  Built: {slug}.html")
    
    # Sort by date desc
    posts.sort(key=lambda p: p['date'], reverse=True)
    
    # Write posts.json
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(posts, f, indent=2)
    
    print(f"\nDone. {len(posts)} posts → posts.json")


if __name__ == '__main__':
    # Ensure posts dir exists
    os.makedirs(POSTS_DIR, exist_ok=True)
    build_posts()
