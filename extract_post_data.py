import csv
import os
import re
from html.parser import HTMLParser
from urllib.parse import urlparse

class PostContentExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_post_content = False
        self.in_title = False
        self.content = []
        self.title = ""
        self.current_tag = None
        self.depth = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'div' and 'class' in attrs_dict:
            if 'post-stream' in attrs_dict['class'] or 'cooked' in attrs_dict['class']:
                self.in_post_content = True
                self.depth = 1
        elif self.in_post_content:
            self.depth += 1
            
        if tag == 'h1' and 'class' in attrs_dict and 'title' in attrs_dict['class']:
            self.in_title = True
            
        self.current_tag = tag
        
    def handle_endtag(self, tag):
        if self.in_post_content:
            self.depth -= 1
            if self.depth == 0:
                self.in_post_content = False
                
        if tag == 'h1' and self.in_title:
            self.in_title = False
            
    def handle_data(self, data):
        if self.in_post_content:
            self.content.append(data.strip())
        if self.in_title:
            self.title = data.strip()

def extract_info_from_post(html_content, original_title="", original_link=""):
    parser = PostContentExtractor()
    parser.feed(html_content)
    
    full_text = ' '.join(parser.content)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    
    title = parser.title if parser.title else original_title
    
    info = {
        'TL;DR / One-liner': '',
        'Problem Statement': '',
        'Proposed Solution / Scope': '',
        'Domain Experts Involved': '',
        'Community Support': original_link,
        'Intended Impact': '',
        'Impact Area': '',
        'Leverage / Multiplier Effect': '',
        'Execution Readiness': 'Medium',
        'Existing Funding': '',
        'Dependencies / Risks': '',
        'Review Notes': '',
        'Reviewer Score': ''
    }
    
    lower_text = full_text.lower()
    
    if 'tldr' in lower_text or 'tl;dr' in lower_text or 'summary' in lower_text:
        tldr_match = re.search(r'(tldr|tl;dr|summary)[:\s]+(.*?)(?:\.|!|\?|$)', lower_text, re.IGNORECASE)
        if tldr_match:
            info['TL;DR / One-liner'] = tldr_match.group(2).strip()[:200]
    
    if not info['TL;DR / One-liner'] and full_text:
        first_sentence = re.split(r'[.!?]', full_text)[0]
        info['TL;DR / One-liner'] = first_sentence[:200] if first_sentence else title
    
    problem_patterns = [
        r'problem[:\s]+(.*?)(?:solution|approach|methodology|$)',
        r'challenge[:\s]+(.*?)(?:solution|approach|methodology|$)',
        r'issue[:\s]+(.*?)(?:solution|approach|methodology|$)',
        r'gap[:\s]+(.*?)(?:solution|approach|methodology|$)'
    ]
    
    for pattern in problem_patterns:
        match = re.search(pattern, lower_text, re.IGNORECASE | re.DOTALL)
        if match:
            info['Problem Statement'] = match.group(1).strip()[:300]
            break
    
    solution_patterns = [
        r'solution[:\s]+(.*?)(?:impact|outcome|dependency|risk|$)',
        r'approach[:\s]+(.*?)(?:impact|outcome|dependency|risk|$)',
        r'methodology[:\s]+(.*?)(?:impact|outcome|dependency|risk|$)',
        r'proposal[:\s]+(.*?)(?:impact|outcome|dependency|risk|$)'
    ]
    
    for pattern in solution_patterns:
        match = re.search(pattern, lower_text, re.IGNORECASE | re.DOTALL)
        if match:
            info['Proposed Solution / Scope'] = match.group(1).strip()[:300]
            break
    
    if 'ai' in lower_text or 'artificial intelligence' in lower_text:
        info['Impact Area'] = 'AI/ML'
    elif 'defi' in lower_text or 'decentralized finance' in lower_text:
        info['Impact Area'] = 'DeFi'
    elif 'governance' in lower_text:
        info['Impact Area'] = 'Governance'
    elif 'infrastructure' in lower_text or 'tooling' in lower_text:
        info['Impact Area'] = 'Infrastructure'
    elif 'adoption' in lower_text or 'user experience' in lower_text or 'ux' in lower_text:
        info['Impact Area'] = 'Adoption/UX'
    elif 'privacy' in lower_text or 'kyc' in lower_text:
        info['Impact Area'] = 'Privacy/Compliance'
    elif 'funding' in lower_text or 'grant' in lower_text:
        info['Impact Area'] = 'Funding Models'
    elif 'open source' in lower_text or 'oss' in lower_text:
        info['Impact Area'] = 'Open Source'
    else:
        info['Impact Area'] = 'General'
    
    impact_patterns = [
        r'impact[:\s]+(.*?)(?:dependency|risk|conclusion|$)',
        r'outcome[:\s]+(.*?)(?:dependency|risk|conclusion|$)',
        r'success[:\s]+(.*?)(?:dependency|risk|conclusion|$)'
    ]
    
    for pattern in impact_patterns:
        match = re.search(pattern, lower_text, re.IGNORECASE | re.DOTALL)
        if match:
            info['Intended Impact'] = match.group(1).strip()[:300]
            break
    
    expert_patterns = [
        r'(?:led by|team|expert|advisor|contributor)[:\s]+(.*?)(?:\.|,|;|$)',
        r'(?:@\w+)',
    ]
    
    experts = []
    for pattern in expert_patterns[:1]:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        experts.extend(matches[:3])
    
    mention_matches = re.findall(r'@\w+', full_text)
    experts.extend(mention_matches[:5])
    
    if experts:
        info['Domain Experts Involved'] = ', '.join(set(experts[:5]))
    
    risk_patterns = [
        r'risk[:\s]+(.*?)(?:mitigation|conclusion|$)',
        r'dependency[:\s]+(.*?)(?:mitigation|conclusion|$)',
        r'challenge[:\s]+(.*?)(?:mitigation|conclusion|$)'
    ]
    
    for pattern in risk_patterns:
        match = re.search(pattern, lower_text, re.IGNORECASE | re.DOTALL)
        if match:
            info['Dependencies / Risks'] = match.group(1).strip()[:300]
            break
    
    if 'high' in lower_text and ('leverage' in lower_text or 'impact' in lower_text or 'multiplier' in lower_text):
        info['Leverage / Multiplier Effect'] = 'High - broad ecosystem impact'
    elif 'ecosystem' in lower_text or 'network effect' in lower_text:
        info['Leverage / Multiplier Effect'] = 'Network effects expected'
    else:
        info['Leverage / Multiplier Effect'] = 'Standard impact'
    
    if 'ready' in lower_text or 'immediate' in lower_text or 'launch' in lower_text:
        info['Execution Readiness'] = 'High'
    elif 'pilot' in lower_text or 'mvp' in lower_text or 'prototype' in lower_text:
        info['Execution Readiness'] = 'Medium'
    elif 'research' in lower_text or 'early' in lower_text or 'concept' in lower_text:
        info['Execution Readiness'] = 'Low'
    
    return info

def process_all_posts():
    original_data = []
    with open('data.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        original_data = list(reader)
    
    updated_data = []
    
    for row in original_data:
        link = row['Link']
        title = row['Title']
        
        # Extract post ID from URL
        url_parts = urlparse(link)
        path_parts = url_parts.path.strip('/').split('/')
        if len(path_parts) >= 2:
            post_id = path_parts[-1]
        else:
            post_id = f"post_{len(updated_data) + 1}"
        
        html_file = f"posts/{post_id}.html"
        
        new_row = {
            'Date Submitted': row['Date Submitted'],
            'Title': title,
            'Submitted By': row['Submitted By'],
            'Link': link
        }
        
        if os.path.exists(html_file):
            print(f"Processing: {title}")
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                extracted_info = extract_info_from_post(html_content, title, link)
                new_row.update(extracted_info)
                
            except Exception as e:
                print(f"  Error processing {html_file}: {e}")
                new_row.update({
                    'TL;DR / One-liner': title,
                    'Problem Statement': '',
                    'Proposed Solution / Scope': '',
                    'Domain Experts Involved': '',
                    'Community Support': link,
                    'Intended Impact': '',
                    'Impact Area': '',
                    'Leverage / Multiplier Effect': '',
                    'Execution Readiness': 'Medium',
                    'Existing Funding': '',
                    'Dependencies / Risks': '',
                    'Review Notes': '',
                    'Reviewer Score': ''
                })
        else:
            print(f"  No HTML file found for: {title}")
            new_row.update({
                'TL;DR / One-liner': title,
                'Problem Statement': '',
                'Proposed Solution / Scope': '',
                'Domain Experts Involved': '',
                'Community Support': link,
                'Intended Impact': '',
                'Impact Area': '',
                'Leverage / Multiplier Effect': '',
                'Execution Readiness': 'Medium',
                'Existing Funding': '',
                'Dependencies / Risks': '',
                'Review Notes': '',
                'Reviewer Score': ''
            })
        
        updated_data.append(new_row)
    
    fieldnames = [
        'Date Submitted', 'Title', 'Submitted By', 'Link',
        'TL;DR / One-liner', 'Problem Statement', 'Proposed Solution / Scope',
        'Domain Experts Involved', 'Community Support',
        'Intended Impact', 'Impact Area', 'Leverage / Multiplier Effect',
        'Execution Readiness', 'Existing Funding', 'Dependencies / Risks',
        'Review Notes', 'Reviewer Score'
    ]
    
    with open('data_updated.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_data)
    
    print(f"\nProcessed {len(updated_data)} posts")
    print("Updated CSV saved as 'data_updated.csv'")

if __name__ == "__main__":
    process_all_posts()