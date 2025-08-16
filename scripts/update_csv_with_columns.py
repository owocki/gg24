#!/usr/bin/env python3
"""
Script to extract TLDR, Problem, Solution, Domain Experts, Target projects, 
Impact Areas, Risks, and Funding Ask from HTML posts and update the CSV.
"""

import os
import re
import csv
from bs4 import BeautifulSoup
import html


def clean_text(text, max_len=100):
    """Clean and normalize text content to be concise."""
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove special chars that might break CSV
    text = text.replace('"', "'").replace('\n', ' ').replace('\r', ' ')
    
    # Make it concise - first sentence or max_len chars
    sentences = re.split(r'[.!?]', text)
    if sentences and sentences[0]:
        result = sentences[0].strip()
        if len(result) > max_len:
            result = result[:max_len-3] + "..."
        return result
    
    if len(text) > max_len:
        return text[:max_len-3] + "..."
    return text


def extract_tldr(text):
    """Extract concise TLDR."""
    patterns = [
        r'TLDR[;:]?\s*(.*?)(?:\n|$)',
        r'TL;DR[;:]?\s*(.*?)(?:\n|$)',
        r'tl;dr[;:]?\s*(.*?)(?:\n|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_text(match.group(1), 80)
    
    # If no TLDR, use first meaningful sentence
    sentences = re.split(r'[.!?]', text)
    for sent in sentences:
        if len(sent.strip()) > 20:
            return clean_text(sent, 80)
    return ""


def extract_problem(text):
    """Extract concise problem statement."""
    patterns = [
        r'Problem\s*(?:&|and)?\s*Impact[:]?\s*(.*?)(?=\n[A-Z]|\n\*|$)',
        r'Problem Statement[:]?\s*(.*?)(?=\n[A-Z]|\n\*|$)',
        r'Problem[:]?\s*(.*?)(?=\n[A-Z]|\n\*|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return clean_text(match.group(1), 100)
    
    # Look for problem-related keywords
    if 'challenge' in text.lower() or 'issue' in text.lower():
        sentences = text.split('.')
        for sent in sentences:
            if 'challenge' in sent.lower() or 'issue' in sent.lower():
                return clean_text(sent, 100)
    
    return ""


def extract_solution(text):
    """Extract concise solution."""
    patterns = [
        r'(?:Proposed\s+)?Solution[:]?\s*(.*?)(?=\n[A-Z]|\n\*|$)',
        r'Scope[:]?\s*(.*?)(?=\n[A-Z]|\n\*|$)',
        r'Proposal[:]?\s*(.*?)(?=\n[A-Z]|\n\*|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return clean_text(match.group(1), 100)
    
    # Look for solution keywords
    if 'build' in text.lower() or 'create' in text.lower() or 'develop' in text.lower():
        sentences = text.split('.')
        for sent in sentences:
            if any(word in sent.lower() for word in ['build', 'create', 'develop', 'implement']):
                return clean_text(sent, 100)
    
    return ""


def extract_experts(text):
    """Extract domain experts mentioned."""
    experts = []
    
    # Look for @mentions
    mentions = re.findall(r'@(\w+)', text)
    experts.extend(mentions[:3])  # Take first 3
    
    # Look for explicit expert mentions
    patterns = [
        r'Domain\s+[Ee]xperts?[:]?\s*([^.\n]*)',
        r'[Tt]eam[:]?\s*([^.\n]*)',
        r'[Ww]ritten\s+by[:]?\s*([^.\n]*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            names = match.group(1).strip()
            # Clean up the names
            names = re.sub(r'[@]', '', names)
            if names and len(names) < 100:
                experts.append(names)
                break
    
    # Deduplicate and join
    seen = set()
    unique_experts = []
    for e in experts:
        if e and e not in seen:
            seen.add(e)
            unique_experts.append(e)
    
    result = ', '.join(unique_experts[:5])
    return clean_text(result, 80) if result else ""


def extract_impact_area(text):
    """Determine impact area from content."""
    text_lower = text.lower()
    
    if 'defi' in text_lower or 'liquidity' in text_lower or 'swap' in text_lower:
        return "DeFi"
    elif 'governance' in text_lower or 'dao' in text_lower or 'voting' in text_lower:
        return "Governance"
    elif 'infrastructure' in text_lower or 'developer tool' in text_lower or 'core' in text_lower:
        return "Infrastructure"
    elif 'privacy' in text_lower or 'kyc' in text_lower or 'zero-knowledge' in text_lower:
        return "Privacy"
    elif 'data' in text_lower or 'analytics' in text_lower or 'metrics' in text_lower:
        return "Data"
    elif 'enterprise' in text_lower or 'corporate' in text_lower or 'business' in text_lower:
        return "Enterprise"
    elif 'community' in text_lower or 'popup' in text_lower or 'residency' in text_lower:
        return "Community"
    elif 'user experience' in text_lower or 'ux' in text_lower or 'consumer' in text_lower:
        return "UX/Consumer"
    elif 'funding' in text_lower or 'grant' in text_lower or 'pgf' in text_lower:
        return "Funding"
    elif 'ai' in text_lower or 'machine learning' in text_lower or 'llm' in text_lower:
        return "AI/ML"
    elif 'science' in text_lower or 'research' in text_lower or 'desci' in text_lower:
        return "Science"
    elif 'local' in text_lower or 'regen' in text_lower or 'sustainability' in text_lower:
        return "Localism"
    elif 'information market' in text_lower or 'prediction' in text_lower or 'infofi' in text_lower:
        return "InfoFi"
    else:
        return "General"


def extract_risks(text):
    """Extract risks and dependencies."""
    patterns = [
        r'[Rr]isks?[:]?\s*(.*?)(?=\n[A-Z]|\n\*|$)',
        r'[Dd]ependencies[:]?\s*(.*?)(?=\n[A-Z]|\n\*|$)',
        r'[Cc]hallenges?[:]?\s*(.*?)(?=\n[A-Z]|\n\*|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return clean_text(match.group(1), 100)
    
    # Look for risk-related keywords
    risk_keywords = ['risk', 'challenge', 'dependency', 'require', 'need', 'barrier']
    sentences = text.split('.')
    for sent in sentences:
        if any(kw in sent.lower() for kw in risk_keywords):
            return clean_text(sent, 100)
    
    return ""


def extract_funding(text):
    """Extract funding amounts and external funders."""
    amounts = []
    
    # Look for dollar amounts
    dollar_patterns = [
        r'\$[\d,]+(?:\s*(?:k|K|thousand|million|M))?',
        r'[\d,]+\s*(?:USD|usd)',
        r'[\d,]+\s*(?:ETH|eth|Eth)'
    ]
    
    for pattern in dollar_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        amounts.extend(matches[:2])  # Take first 2
    
    # Look for explicit funding mentions
    funding_patterns = [
        r'[Ff]unding\s+[Aa]sk[:]?\s*([^.\n]*)',
        r'[Bb]udget[:]?\s*([^.\n]*)',
        r'[Rr]equested\s+[Aa]mount[:]?\s*([^.\n]*)'
    ]
    
    for pattern in funding_patterns:
        match = re.search(pattern, text)
        if match:
            amount_text = match.group(1).strip()
            if amount_text and len(amount_text) < 50:
                amounts.append(amount_text)
                break
    
    # Look for external funders
    funder_patterns = [
        r'[Pp]artners?[:]?\s*([^.\n]*)',
        r'[Ff]unders?[:]?\s*([^.\n]*)',
        r'[Ss]ponsors?[:]?\s*([^.\n]*)'
    ]
    
    funders = []
    for pattern in funder_patterns:
        match = re.search(pattern, text)
        if match:
            funder_text = match.group(1).strip()
            if funder_text and len(funder_text) < 100:
                funders.append(funder_text)
                break
    
    # Combine amounts and funders
    result_parts = []
    if amounts:
        result_parts.append(' '.join(amounts[:2]))
    if funders:
        result_parts.append(funders[0])
    
    result = ' + '.join(result_parts) if result_parts else ""
    return clean_text(result, 100) if result else ""


def extract_target_projects(text):
    """Extract target projects or initiatives."""
    # Look for project names or specific initiatives mentioned
    patterns = [
        r'[Pp]rojects?[:]?\s*([^.\n]*)',
        r'[Ii]nitiatives?[:]?\s*([^.\n]*)',
        r'[Tt]arget[:]?\s*([^.\n]*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            projects = match.group(1).strip()
            if projects and len(projects) < 100:
                return clean_text(projects, 80)
    
    # Look for specific project mentions (capitalized names)
    project_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    # Filter out common words
    common_words = {'The', 'This', 'That', 'These', 'Those', 'Web', 'Ethereum', 'Gitcoin'}
    project_names = [p for p in project_names if p not in common_words and len(p) > 3]
    
    if project_names:
        return clean_text(', '.join(project_names[:3]), 80)
    
    return ""


def process_post(html_file):
    """Process a single HTML post file."""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('title')
        title = ""
        if title_elem:
            title = title_elem.get_text().split(' - ')[0].strip()
        
        # Extract post content
        post_div = soup.find('div', {'class': 'post', 'itemprop': 'text'})
        
        if not post_div:
            return None
        
        # Get all text content
        text = post_div.get_text()
        
        # Extract all required fields
        data = {
            'TLDR': extract_tldr(text),
            'Problem': extract_problem(text),
            'Solution': extract_solution(text),
            'Domain Experts': extract_experts(text),
            'Target projects': extract_target_projects(text),
            'Impact Areas': extract_impact_area(text),
            'Risks': extract_risks(text),
            'Funding Ask': extract_funding(text),
            'External Funders': extract_funding(text)  # Same extraction for now
        }
        
        return data
        
    except Exception as e:
        print(f"Error processing {html_file}: {e}")
        return None


def update_csv():
    """Update the CSV with new columns."""
    csv_file = '/Users/owocki/Sites/gg24/data/data.csv'
    posts_dir = '/Users/owocki/Sites/gg24/posts'
    
    # Get list of HTML files
    html_files = [f for f in os.listdir(posts_dir) if f.endswith('.html')]
    
    print(f"Processing {len(html_files)} posts...")
    
    # Process each HTML file
    extracted_data = {}
    for html_file in html_files:
        post_id = html_file.replace('.html', '').strip()
        file_path = os.path.join(posts_dir, html_file)
        
        data = process_post(file_path)
        if data:
            extracted_data[post_id] = data
    
    # Read existing CSV
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        existing_fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Add new columns
    new_fieldnames = existing_fieldnames + ['TLDR', 'Problem', 'Solution', 'Domain Experts', 
                                              'Target projects', 'Impact Areas', 'Risks', 
                                              'Funding Ask', 'External Funders']
    
    # Update rows with extracted data
    for row in rows:
        if 'Link' in row and row['Link']:
            # Find matching post ID from URL
            match = re.search(r'/(\d+)(?:\s*$|/|\?)', row['Link'])
            if match:
                post_id = match.group(1)
                if post_id in extracted_data:
                    data = extracted_data[post_id]
                    for key, value in data.items():
                        row[key] = value
    
    # Write updated CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Updated {csv_file} with new columns")


if __name__ == "__main__":
    update_csv()