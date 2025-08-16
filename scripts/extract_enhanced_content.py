#!/usr/bin/env python3
"""
Enhanced script to extract detailed content from HTML forum posts with better categorization and parsing.
Improved version that provides cleaner extraction and better impact area classification.
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


def classify_impact_area(content):
    """Classify the impact area based on content analysis."""
    content_lower = content.lower()
    
    # Define keyword patterns for each category
    categories = {
        'AI/ML': [
            'artificial intelligence', 'machine learning', 'llm', 'chatbot', 'ai builder',
            'neural network', 'deep learning', 'language model', 'ai integration'
        ],
        'DeFi': [
            'defi', 'decentralized finance', 'trading', 'liquidity', 'swap', 'dex',
            'yield', 'lending', 'borrowing', 'automated market maker', 'amm'
        ],
        'Governance': [
            'governance', 'voting', 'dao', 'proposal', 'paradox management', 'consensus',
            'decision making', 'community governance', 'token governance'
        ],
        'Infrastructure': [
            'infrastructure', 'developer tooling', 'core', 'protocol', 'sdk', 'api',
            'developer tools', 'devex', 'developer experience', 'blockchain infrastructure'
        ],
        'Privacy': [
            'privacy', 'kyc', 'zero-knowledge', 'private', 'zk', 'anonymity',
            'privacy preserving', 'confidential', 'secure identity'
        ],
        'Data': [
            'data standards', 'analytics', 'open data', 'data infrastructure',
            'data visualization', 'metrics', 'dashboard', 'indexing'
        ],
        'Enterprise': [
            'enterprise', 'corporate', 'business adoption', 'enterprise integration',
            'business use case', 'corporate adoption'
        ],
        'Community': [
            'community', 'popup', 'residency', 'builder development', 'coordination',
            'social coordination', 'network coordination', 'community building'
        ],
        'UX/Consumer': [
            'user experience', 'consumer apps', 'mass adoption', 'wallet', 'frontend',
            'user interface', 'usability', 'consumer products'
        ],
        'Funding/Meta': [
            'metafunding', 'funding mechanisms', 'pgf', 'public goods funding',
            'grant funding', 'capital allocation', 'funding infrastructure'
        ],
        'Localism/Regen': [
            'localism', 'regenerative', 'local communities', 'sustainability',
            'environmental', 'climate', 'local economy'
        ],
        'Information/Prediction': [
            'information markets', 'prediction markets', 'information finance',
            'forecasting', 'truth', 'information systems'
        ]
    }
    
    # Score each category
    scores = {}
    for category, keywords in categories.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        if score > 0:
            scores[category] = score
    
    # Return the category with highest score, or 'General' if no match
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    else:
        return 'General'


def assess_execution_readiness(content):
    """Assess execution readiness based on content indicators."""
    content_lower = content.lower()
    
    high_indicators = [
        'prototype', 'mvp', 'already built', 'existing', 'live', 'deployed',
        'operational', 'running', 'functional', 'working product', 'beta',
        'launched', 'production', 'established', 'proven', 'track record'
    ]
    
    low_indicators = [
        'concept', 'early stage', 'research', 'theoretical', 'ideation',
        'planning', 'proposal', 'draft', 'initial', 'exploratory'
    ]
    
    high_score = sum(1 for indicator in high_indicators if indicator in content_lower)
    low_score = sum(1 for indicator in low_indicators if indicator in content_lower)
    
    if high_score > low_score:
        return "High"
    elif low_score > high_score:
        return "Low"
    else:
        return "Medium"


def extract_experts_and_team(content):
    """Extract domain experts and team members from content."""
    experts = []
    
    # Look for name patterns
    name_patterns = [
        r'@\w+',  # Mentions
        r'[A-Z][a-z]+ [A-Z][a-z]+(?:, [A-Z][a-z]+ [A-Z][a-z]+)*',  # Full names
        r'Domain [Ee]xperts?[:\s]+([^.]*)',
        r'[Ss]tewards?[:\s]+([^.]*)',
        r'[Jj]udges?[:\s]+([^.]*)',
        r'[Tt]eam[:\s]+([^.]*)',
        r'[Ll]ead[:\s]+([^.]*)'
    ]
    
    for pattern in name_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        experts.extend(matches)
    
    # Clean and deduplicate
    cleaned_experts = []
    for expert in experts:
        if expert and len(expert.strip()) > 2:
            cleaned_experts.append(expert.strip())
    
    return ', '.join(list(dict.fromkeys(cleaned_experts))[:5])  # Top 5 unique


def determine_leverage_multiplier(content, impact_area):
    """Determine leverage/multiplier effect based on content and impact area."""
    content_lower = content.lower()
    
    high_leverage_indicators = [
        'infrastructure', 'standard', 'protocol', 'framework', 'platform',
        'ecosystem', 'multiplier', 'scale', 'network effect', 'leverage',
        'reusable', 'foundational', 'core', 'universal'
    ]
    
    # Infrastructure and core areas typically have higher leverage
    high_leverage_areas = ['Infrastructure', 'Funding/Meta', 'Data', 'Privacy']
    
    high_score = sum(1 for indicator in high_leverage_indicators if indicator in content_lower)
    
    if impact_area in high_leverage_areas or high_score >= 3:
        return "High leverage/multiplier"
    elif high_score >= 1:
        return "Medium leverage/multiplier" 
    else:
        return "Standard impact"


def extract_section_content(text, section_headers, max_chars=400):
    """Extract content from specific sections based on headers."""
    for header in section_headers:
        pattern = rf'{header}[:\s]*(.*?)(?=(?:\n[A-Z][^a-z]*:|\n\*\*[A-Z]|\Z))'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            return clean_text(content[:max_chars])
    return ""


def extract_post_content_enhanced(html_file):
    """Extract structured content from an HTML post file with enhanced parsing."""
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
            print(f"Warning: No post content found in {html_file}")
            return None
        
        # Get all text content
        full_text = post_div.get_text()
        
        # Extract TLDR
        tldr_headers = ['TLDR', 'TL;DR', 'tl;dr', 'Summary']
        tldr = extract_section_content(full_text, tldr_headers, 250)
        
        # Extract Problem Statement
        problem_headers = ['Problem & Impact', 'Problem Statement', 'Problem', 'PROBLEM AND IMPACT']
        problem = extract_section_content(full_text, problem_headers, 500)
        
        # Extract Solution/Scope
        solution_headers = ['Proposed Solution', 'Solution', 'Scope', 'Domain Proposal', 'Mechanism']
        solution = extract_section_content(full_text, solution_headers, 500)
        
        # Extract Success/Impact metrics
        impact_headers = ['Success Measurement', 'Intended Impact', 'Impact', 'Outcomes', 'Success']
        impact = extract_section_content(full_text, impact_headers, 400)
        
        # Classify impact area
        impact_area = classify_impact_area(full_text)
        
        # Assess execution readiness
        execution_readiness = assess_execution_readiness(full_text)
        
        # Extract experts
        experts = extract_experts_and_team(full_text)
        
        # Determine leverage
        leverage = determine_leverage_multiplier(full_text, impact_area)
        
        # Extract funding/risk information
        funding_patterns = [
            r'\$[\d,]+(?:\s*(?:k|K|million|M))?',
            r'[\d,]+\s*ETH',
            r'budget[^.]*\$[\d,]+',
            r'funding[^.]*\$[\d,]+'
        ]
        
        funding_risks = []
        for pattern in funding_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            funding_risks.extend(matches[:3])  # Limit to avoid too much repetition
        
        # Look for explicit risks/dependencies
        risk_headers = ['Dependencies', 'Risks', 'Challenges', 'Requirements']
        explicit_risks = extract_section_content(full_text, risk_headers, 200)
        
        if explicit_risks:
            dependencies_risks = explicit_risks
        else:
            dependencies_risks = ', '.join(funding_risks[:5]) if funding_risks else ""
        
        # Build the extracted data
        extracted_data = {
            'title': clean_text(title),
            'tldr': tldr,
            'problem_statement': problem,
            'proposed_solution': solution,
            'domain_experts': experts[:200],  # Limit length
            'intended_impact': impact,
            'impact_area': impact_area,
            'leverage_multiplier': leverage,
            'execution_readiness': execution_readiness,
            'dependencies_risks': dependencies_risks[:250],  # Limit length
            'full_content_length': len(full_text)
        }
        
        return extracted_data
        
    except Exception as e:
        print(f"Error processing {html_file}: {e}")
        return None


def update_csv_with_enhanced_data():
    """Update the CSV file with enhanced extracted data from HTML posts."""
    
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
        data = extract_post_content_enhanced(file_path)
        if data:
            extracted_data[post_id] = data
    
    # Read existing CSV
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Update rows with extracted data
    updated_count = 0
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
                    updated_count += 1
                    print(f"✓ Updated post {post_id} - {data['title'][:50]}...")
    
    # Write updated CSV
    output_file = '/Users/owocki/Sites/gg24/data_updated_enhanced.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"\n✅ Enhanced CSV saved to {output_file}")
    print(f"✅ Successfully updated {updated_count} posts with detailed content")
    print(f"✅ Impact areas identified: {set(data['impact_area'] for data in extracted_data.values())}")
    
    return output_file


if __name__ == "__main__":
    output_file = update_csv_with_enhanced_data()
    print(f"\n🎉 Enhanced analysis complete! Results saved to: {output_file}")