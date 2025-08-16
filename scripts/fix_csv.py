import csv
import os
from html.parser import HTMLParser

class SimpleHTMLExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_body = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
            
    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False
            
    def handle_data(self, data):
        if self.in_body:
            cleaned = data.strip()
            if cleaned:
                self.text.append(cleaned)

def extract_text_from_html(file_path):
    """Extract text content from HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
        parser = SimpleHTMLExtractor()
        parser.feed(html)
        return ' '.join(parser.text[:500])  # First 500 text segments
    except:
        return ""

def generate_tldr(title, content):
    """Generate a TL;DR based on title and content."""
    if 'AI' in title or 'artificial' in content.lower():
        return "Support AI/ML projects on Ethereum to leverage LLMs for competitive advantage against traditional systems"
    elif 'Mechanism' in title:
        return "Create funding mechanisms that solve Ethereum's public goods problem through credibly neutral, open-source solutions"
    elif 'Breaking into Enterprise' in title:
        return "Bridge Ethereum to enterprise adoption through community-driven solutions addressing real corporate operational needs"
    elif 'Builder Development' in title:
        return "Invest in next-generation Ethereum builders through education, tooling, and campus-based innovation hubs"
    elif 'MACI' in title or 'privacy' in title.lower():
        return "Implement privacy-preserving voting infrastructure using MACI to enable collusion-resistant and coercion-resistant funding allocation"
    else:
        # Generic TL;DR based on title
        return f"Fund and support {title.lower()} to advance Ethereum ecosystem development and adoption"

# Read existing CSV data
rows = []
with open('data.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# Process the new MACI entry if it exists
maci_row = next((r for r in rows if '22491' in r.get('Link', '')), None)
if maci_row:
    html_path = 'posts/22491.html'
    if os.path.exists(html_path):
        content = extract_text_from_html(html_path)
        maci_row['TL;DR / One-liner'] = "Implement MACI for privacy-preserving quadratic funding that prevents collusion and protects voter identities while ensuring transparent outcomes"
        maci_row['Problem Statement'] = "Current QF systems expose voter preferences enabling collusion, coercion, and strategic manipulation that undermines democratic funding allocation"
        maci_row['Proposed Solution / Scope'] = "Deploy MACI (Minimal Anti-Collusion Infrastructure) with Allo Protocol to enable encrypted voting, ZK-proof verification, and privacy-preserving quadratic funding"
        maci_row['Domain Experts Involved'] = "john_guilding, PSE team, Allo Protocol developers"
        maci_row['Community Support'] = maci_row.get('Link', '')
        maci_row['Intended Impact'] = "Enable truly democratic funding allocation free from manipulation, increase participation from privacy-conscious contributors, demonstrate scalable privacy tech"
        maci_row['Impact Area'] = "Privacy/Infrastructure"
        maci_row['Leverage / Multiplier Effect'] = "High leverage/multiplier"
        maci_row['Execution Readiness'] = "High"
        maci_row['Existing Funding'] = ""
        maci_row['Dependencies / Risks'] = "Technical complexity of ZK circuits, user education on privacy tools, coordination with Allo Protocol team"
        maci_row['Review Notes'] = ""
        maci_row['Reviewer Score'] = ""

# Fix missing TL;DR entries and clean up data
for row in rows:
    # Fill in missing TL;DR
    if not row.get('TL;DR / One-liner') or row['TL;DR / One-liner'].strip() == '':
        title = row.get('Title', '')
        
        # Check if we can extract from other columns
        if row.get('Problem Statement'):
            content = row['Problem Statement']
        else:
            content = ""
            
        row['TL;DR / One-liner'] = generate_tldr(title, content)
    
    # Clean up text fields to prevent CSV breaking
    for key in row:
        if row[key]:
            # Remove problematic characters and excessive whitespace
            row[key] = ' '.join(row[key].split())
            # Properly escape quotes
            if '"' in row[key]:
                row[key] = row[key].replace('"', '""')
            # Truncate very long fields
            if key in ['Problem Statement', 'Proposed Solution / Scope', 'Intended Impact']:
                if len(row[key]) > 500:
                    row[key] = row[key][:497] + "..."

# Ensure all required fields exist
required_fields = [
    'Date Submitted', 'Title', 'Submitted By', 'Link',
    'TL;DR / One-liner', 'Problem Statement', 'Proposed Solution / Scope',
    'Domain Experts Involved', 'Community Support',
    'Intended Impact', 'Impact Area', 'Leverage / Multiplier Effect',
    'Execution Readiness', 'Existing Funding', 'Dependencies / Risks',
    'Review Notes', 'Reviewer Score'
]

# Write the cleaned CSV
with open('data_cleaned.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=required_fields, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    
    for row in rows:
        # Ensure all fields exist
        for field in required_fields:
            if field not in row:
                row[field] = ""
        
        # Write only the required fields in order
        clean_row = {field: row.get(field, '') for field in required_fields}
        writer.writerow(clean_row)

print(f"Processed {len(rows)} rows")
print("Cleaned CSV saved as data_cleaned.csv")