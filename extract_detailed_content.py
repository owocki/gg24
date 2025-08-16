#!/usr/bin/env python3
"""
Script to extract detailed content from HTML forum posts and populate CSV with structured data.
Focuses on extracting meaningful content from post bodies to fill out comprehensive analysis.
"""

import os
import re
import csv
from bs4 import BeautifulSoup
from urllib.parse import unquote
import html


def clean_text(text):
    """Clean and normalize text content."""
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove special chars that might break CSV
    text = text.replace('"', "'").replace('\n', ' ').replace('\r', ' ')
    return text


def extract_post_content(html_file):
    """Extract structured content from an HTML post file."""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('title')
        title = ""
        if title_elem:
            title = title_elem.get_text().split(' - ')[0].strip()
        
        # Extract post content - look for div with class='post' and itemprop='text'
        post_div = soup.find('div', {'class': 'post', 'itemprop': 'text'})
        
        if not post_div:
            print(f"Warning: No post content found in {html_file}")
            return None
        
        # Get all text content
        full_text = post_div.get_text()
        
        # Extract specific sections
        sections = {
            'tldr': '',
            'problem': '',
            'solution': '',
            'impact': '',
            'experts': '',
            'funding': '',
            'timeline': '',
            'domain_info': '',
            'success_metrics': '',
            'sensemaking': ''
        }
        
        # Split text into paragraphs for analysis
        paragraphs = [p.strip() for p in full_text.split('\n') if p.strip()]
        
        current_section = None
        section_content = []
        
        for para in paragraphs:
            para_lower = para.lower()
            
            # Identify section headers
            if 'tldr' in para_lower or 'tl;dr' in para_lower:
                if current_section and section_content:
                    sections[current_section] = ' '.join(section_content)
                current_section = 'tldr'
                section_content = [para]
            elif 'problem' in para_lower and ('impact' in para_lower or 'statement' in para_lower):
                if current_section and section_content:
                    sections[current_section] = ' '.join(section_content)
                current_section = 'problem'
                section_content = [para]
            elif any(word in para_lower for word in ['solution', 'scope', 'proposal', 'proposed']):
                if current_section and section_content:
                    sections[current_section] = ' '.join(section_content)
                current_section = 'solution'
                section_content = [para]
            elif 'sensemaking' in para_lower and 'analysis' in para_lower:
                if current_section and section_content:
                    sections[current_section] = ' '.join(section_content)
                current_section = 'sensemaking'
                section_content = [para]
            elif 'gitcoin' in para_lower and ('role' in para_lower or 'fundraising' in para_lower):
                if current_section and section_content:
                    sections[current_section] = ' '.join(section_content)
                current_section = 'funding'
                section_content = [para]
            elif 'success' in para_lower and ('measurement' in para_lower or 'metrics' in para_lower):
                if current_section and section_content:
                    sections[current_section] = ' '.join(section_content)
                current_section = 'success_metrics'
                section_content = [para]
            elif 'domain information' in para_lower or 'domain info' in para_lower:
                if current_section and section_content:
                    sections[current_section] = ' '.join(section_content)
                current_section = 'domain_info'
                section_content = [para]
            elif 'timeline' in para_lower:
                if current_section and section_content:
                    sections[current_section] = ' '.join(section_content)
                current_section = 'timeline'
                section_content = [para]
            else:
                if current_section:
                    section_content.append(para)
        
        # Don't forget the last section
        if current_section and section_content:
            sections[current_section] = ' '.join(section_content)
        
        # Extract domain experts from various sections
        experts_text = ""
        experts_patterns = [
            r'domain experts?[:\s]+([^.]*)',
            r'stewards?[:\s]+([^.]*)',
            r'judges?[:\s]+([^.]*)',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:, [A-Z][a-z]+ [A-Z][a-z]+)*)',
            r'@\w+'
        ]
        
        for pattern in experts_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                experts_text += ' '.join(matches) + ' '
        
        # Determine impact area based on content
        impact_area = "General"
        area_keywords = {
            'AI/ML': ['ai', 'artificial intelligence', 'machine learning', 'llm', 'chatbot'],
            'DeFi': ['defi', 'decentralized finance', 'trading', 'liquidity', 'swap'],
            'Governance': ['governance', 'voting', 'dao', 'proposal', 'paradox management'],
            'Infrastructure': ['infrastructure', 'developer tooling', 'core', 'protocol'],
            'Privacy': ['privacy', 'kyc', 'zero-knowledge', 'private'],
            'Data': ['data', 'analytics', 'standards', 'open data'],
            'Enterprise': ['enterprise', 'corporate', 'business'],
            'Community': ['community', 'popup', 'residency', 'builder', 'coordination']
        }
        
        content_lower = full_text.lower()
        for area, keywords in area_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                impact_area = area
                break
        
        # Determine execution readiness based on content indicators
        execution_readiness = "Medium"  # Default
        if any(phrase in content_lower for phrase in ['prototype', 'mvp', 'already built', 'existing', 'live', 'deployed']):
            execution_readiness = "High"
        elif any(phrase in content_lower for phrase in ['concept', 'early stage', 'research', 'theoretical']):
            execution_readiness = "Low"
        
        # Extract funding/budget information
        funding_info = ""
        funding_patterns = [
            r'\$[\d,]+',
            r'[\d,]+\s*eth',
            r'budget',
            r'funding',
            r'cost'
        ]
        
        for pattern in funding_patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                funding_info += ' '.join(matches) + ' '
        
        # Build the extracted data
        extracted_data = {
            'title': clean_text(title),
            'tldr': clean_text(sections['tldr'][:300]),  # Limit length
            'problem_statement': clean_text(sections['problem'][:500]),
            'proposed_solution': clean_text(sections['solution'][:500]),
            'domain_experts': clean_text(experts_text[:200]),
            'intended_impact': clean_text(sections['success_metrics'][:400]),
            'impact_area': impact_area,
            'leverage_multiplier': "Standard impact",  # Default
            'execution_readiness': execution_readiness,
            'dependencies_risks': clean_text(funding_info[:300]),
            'full_content_length': len(full_text)
        }
        
        return extracted_data
        
    except Exception as e:
        print(f"Error processing {html_file}: {e}")
        return None


def update_csv_with_extracted_data():
    """Update the CSV file with extracted data from HTML posts."""
    
    # Read existing CSV to get the structure
    csv_file = '/Users/owocki/Sites/gg24/data_updated.csv'
    posts_dir = '/Users/owocki/Sites/gg24/posts'
    
    # Get list of HTML files
    html_files = [f for f in os.listdir(posts_dir) if f.endswith('.html')]
    html_files.sort()
    
    print(f"Found {len(html_files)} HTML files to process")
    
    # Process each HTML file
    extracted_data = {}
    for html_file in html_files:
        post_id = html_file.replace('.html', '').strip()
        file_path = os.path.join(posts_dir, html_file)
        
        print(f"Processing {html_file}...")
        data = extract_post_content(file_path)
        if data:
            extracted_data[post_id] = data
    
    # Read existing CSV
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Create mapping of links to post IDs
    link_to_post_id = {}
    for row in rows:
        if 'Link' in row and row['Link']:
            # Extract post ID from URL
            match = re.search(r'/(\d+)(?:\s*$|\?)', row['Link'])
            if match:
                link_to_post_id[match.group(1)] = row
    
    # Update rows with extracted data
    updated_rows = []
    for row in rows:
        if 'Link' in row and row['Link']:
            # Find matching post ID
            match = re.search(r'/(\d+)(?:\s*$|\?)', row['Link'])
            if match:
                post_id = match.group(1)
                if post_id in extracted_data:
                    data = extracted_data[post_id]
                    # Update the row with extracted data
                    row['TL;DR / One-liner'] = data['tldr']
                    row['Problem Statement'] = data['problem_statement'] 
                    row['Proposed Solution / Scope'] = data['proposed_solution']
                    row['Domain Experts Involved'] = data['domain_experts']
                    row['Intended Impact'] = data['intended_impact']
                    row['Impact Area'] = data['impact_area']
                    row['Leverage / Multiplier Effect'] = data['leverage_multiplier']
                    row['Execution Readiness'] = data['execution_readiness']
                    row['Dependencies / Risks'] = data['dependencies_risks']
                    print(f"Updated data for post {post_id} - {data['title']}")
        
        updated_rows.append(row)
    
    # Write updated CSV
    output_file = '/Users/owocki/Sites/gg24/data_updated_detailed.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if updated_rows:
            writer = csv.DictWriter(f, fieldnames=updated_rows[0].keys())
            writer.writeheader()
            writer.writerows(updated_rows)
    
    print(f"Updated CSV saved to {output_file}")
    print(f"Processed {len(extracted_data)} posts successfully")
    
    return output_file


if __name__ == "__main__":
    output_file = update_csv_with_extracted_data()
    print(f"Analysis complete. Results saved to: {output_file}")