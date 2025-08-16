#!/usr/bin/env python3
import os
import re
from html import unescape
from pathlib import Path

def extract_title(filepath):
    """Extract title from HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find title tag
    title_match = re.search(r'<title>([^<]+)</title>', content)
    if title_match:
        title = unescape(title_match.group(1))
        return title
    return None

def clean_filename(title):
    """Clean title to make it filesystem-friendly."""
    # Remove emojis and special unicode characters
    title = re.sub(r'[^\x00-\x7F]+', '', title)
    
    # Remove the " - Gitcoin Governance" suffix and category prefixes
    title = re.sub(r' - .*Gitcoin Governance$', '', title)
    
    # Remove HTML entities
    title = unescape(title)
    
    # Replace special characters with underscores
    title = re.sub(r'[/:&|<>*?"]', '_', title)
    
    # Replace multiple spaces with single space
    title = re.sub(r'\s+', ' ', title)
    
    # Trim and replace spaces with underscores
    title = title.strip().replace(' ', '_')
    
    # Remove multiple underscores
    title = re.sub(r'_+', '_', title)
    
    # Limit length to 100 characters
    if len(title) > 100:
        title = title[:100]
    
    return title + '.html'

def main():
    posts_dir = Path('posts')
    
    # Get all HTML files
    html_files = list(posts_dir.glob('*.html'))
    
    renames = []
    
    for filepath in html_files:
        title = extract_title(filepath)
        if title:
            new_filename = clean_filename(title)
            new_filepath = posts_dir / new_filename
            
            # Check if new filename already exists
            if new_filepath.exists() and new_filepath != filepath:
                # Add original ID to make unique
                base_name = new_filename[:-5]  # Remove .html
                orig_id = filepath.stem
                new_filename = f"{base_name}_{orig_id}.html"
                new_filepath = posts_dir / new_filename
            
            if filepath != new_filepath:
                renames.append((filepath, new_filepath))
                print(f"Will rename: {filepath.name} -> {new_filename}")
    
    if renames:
        print(f"\nProceeding with {len(renames)} renames...")
        for old_path, new_path in renames:
            old_path.rename(new_path)
            print(f"Renamed: {old_path.name} -> {new_path.name}")
        print(f"\nSuccessfully renamed {len(renames)} files.")
    else:
        print("No files need renaming.")

if __name__ == "__main__":
    main()