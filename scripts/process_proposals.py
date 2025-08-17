#!/usr/bin/env python3
import re
import html as html_module
import csv
import sys
import os

def extract_full_content(filepath):
    """Extract full content from HTML file including body text"""
    if not os.path.exists(filepath):
        return "", ""
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Extract title
    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', content)
    title = html_module.unescape(title_match.group(1)) if title_match else ""
    
    # Extract from meta description first
    meta_match = re.search(r'<meta property="og:description" content="([^"]+)"', content)
    meta_content = html_module.unescape(meta_match.group(1)) if meta_match else ""
    
    # Try to extract main body content
    body_match = re.search(r'<div class="cooked"[^>]*>(.*?)</div>', content, re.DOTALL)
    if not body_match:
        body_match = re.search(r'<div[^>]*itemprop="text"[^>]*>(.*?)</div>', content, re.DOTALL)
    
    body_content = ""
    if body_match:
        body_content = body_match.group(1)
        body_content = re.sub(r'<[^>]+>', ' ', body_content)
        body_content = html_module.unescape(body_content)
        body_content = re.sub(r'\s+', ' ', body_content).strip()
    
    # Combine meta and body content
    full_content = meta_content + " " + body_content
    
    return title, full_content[:5000]  # Limit to 5000 chars for processing

def parse_content_sections(content, title):
    """Parse content into sections with improved extraction"""
    sections = {
        'tldr': '',
        'problem': '',
        'solution': '',
        'domain_experts': '',
        'target_projects': '',
        'impact_areas': '',
        'risks': '',
        'funding': ''
    }
    
    content_lower = content.lower()
    
    # Extract TLDR
    tldr_patterns = [
        r'(?:tldr|tl;dr|summary)[:\s;]+(.*?)(?:problem|challenge|background|$)',
        r'(?:in short|briefly)[:\s]+(.*?)(?:problem|challenge|$)',
    ]
    for pattern in tldr_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            tldr = match.group(1).strip()
            tldr = re.sub(r'\s+', ' ', tldr)[:150]
            sections['tldr'] = tldr
            break
    
    if not sections['tldr']:
        # Extract first meaningful sentence
        sentences = re.split(r'[.!?]', content)
        for sent in sentences[:3]:
            if len(sent) > 30:
                sections['tldr'] = sent.strip()[:150]
                break
    
    # Extract Problem
    prob_patterns = [
        r'problem[:\s&]+(.*?)(?:solution|approach|proposal|$)',
        r'challenge[:\s]+(.*?)(?:solution|approach|$)',
        r'issue[:\s]+(.*?)(?:solution|approach|$)',
    ]
    for pattern in prob_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            sections['problem'] = match.group(1).strip()[:150]
            break
    
    # Extract Solution
    sol_patterns = [
        r'(?:solution|approach|proposal)[:\s]+(.*?)(?:impact|outcome|implementation|$)',
        r'we propose[:\s]+(.*?)(?:impact|this will|$)',
        r'methodology[:\s]+(.*?)(?:impact|outcome|$)',
    ]
    for pattern in sol_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            sections['solution'] = match.group(1).strip()[:150]
            break
    
    # Extract domain experts
    mentions = re.findall(r'@\w+', content)
    if mentions:
        sections['domain_experts'] = ', '.join(set(mentions[:5]))
    
    # Determine impact area based on content
    impact_keywords = {
        'AI/ML': ['ai', 'artificial intelligence', 'machine learning', 'llm', 'chatbot'],
        'DeFi': ['defi', 'decentralized finance', 'liquidity', 'trading', 'amm'],
        'Governance': ['governance', 'voting', 'dao', 'paradox', 'consensus'],
        'Infrastructure': ['infrastructure', 'tooling', 'developer', 'sdk', 'api'],
        'Privacy': ['privacy', 'kyc', 'zero knowledge', 'zk', 'maci'],
        'Science': ['desci', 'science', 'research', 'academic'],
        'Community': ['popup', 'residency', 'community', 'events', 'irl'],
        'Funding': ['funding', 'grant', 'pgf', 'hypercert', 'retroactive'],
        'Data': ['data', 'analytics', 'information', 'infofi'],
        'Adoption': ['adoption', 'ux', 'user experience', 'consumer', 'mass']
    }
    
    for area, keywords in impact_keywords.items():
        if any(kw in content_lower for kw in keywords):
            sections['impact_areas'] = area
            break
    
    if not sections['impact_areas']:
        sections['impact_areas'] = 'General'
    
    # Extract risks
    risk_patterns = [
        r'risk[:\s]+(.*?)(?:mitigation|conclusion|$)',
        r'challenge[:\s]+(.*?)(?:mitigation|$)',
        r'dependency[:\s]+(.*?)(?:mitigation|$)',
    ]
    for pattern in risk_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            sections['risks'] = match.group(1).strip()[:150]
            break
    
    # Extract funding info
    if 'funding' in content_lower or 'grant' in content_lower or '$' in content:
        fund_match = re.search(r'(?:funding|grant|budget)[:\s]+(.*?)(?:timeline|implementation|$)', content, re.IGNORECASE | re.DOTALL)
        if fund_match:
            sections['funding'] = fund_match.group(1).strip()[:150]
    
    # Extract target projects
    if 'example' in content_lower or 'project' in content_lower:
        proj_match = re.search(r'(?:example|project|target)[:\s]+(.*?)(?:impact|outcome|$)', content, re.IGNORECASE | re.DOTALL)
        if proj_match:
            sections['target_projects'] = proj_match.group(1).strip()[:150]
    
    return sections

def score_proposal_owocki_style(sections, title, content):
    """Score the proposal in Kevin Owocki's voice and style"""
    scores = {
        'problem_focus': 0,
        'credible_approach': 0,
        'domain_expertise': 0,
        'co_funding': 0,
        'capital_method': 0,
        'clarity': 0,
        'execution_readiness': 0,
        'vibe_check': 0
    }
    
    feedback = []
    content_lower = content.lower()
    
    # 1. Problem Focus
    if sections['problem'] and len(sections['problem']) > 50:
        if any(word in sections['problem'].lower() for word in ['critical', 'urgent', 'fundamental', 'bottleneck']):
            scores['problem_focus'] = 2
            feedback.append("Solid problem framing")
        else:
            scores['problem_focus'] = 1
            feedback.append("Problem stated but not compelling")
    else:
        feedback.append("Weak problem definition")
    
    # 2. Credible Approach
    if sections['solution'] and len(sections['solution']) > 50:
        if any(word in content_lower for word in ['proven', 'evidence', 'research', 'data', 'tested']):
            scores['credible_approach'] = 2
            feedback.append("Evidence-based approach")
        else:
            scores['credible_approach'] = 1
            feedback.append("Approach needs validation")
    else:
        feedback.append("Solution lacks substance")
    
    # 3. Domain Expertise
    if sections['domain_experts']:
        expert_count = len(sections['domain_experts'].split(','))
        if expert_count >= 3:
            scores['domain_expertise'] = 2
            feedback.append("Strong expert involvement")
        else:
            scores['domain_expertise'] = 1
            feedback.append("Limited expert engagement")
    else:
        feedback.append("No clear domain experts")
    
    # 4. Co-funding
    if 'funding' in content_lower:
        if any(word in content_lower for word in ['secured', 'committed', 'partnered', 'matched']):
            scores['co_funding'] = 2
            feedback.append("Has co-funding secured")
        elif 'seeking' in content_lower or 'looking for' in content_lower:
            scores['co_funding'] = 1
            feedback.append("Seeking co-funding")
        else:
            feedback.append("No co-funding mentioned")
    
    # 5. Capital Method
    if any(word in content_lower for word in ['hypercert', 'retroactive', 'outcome', 'impact cert']):
        scores['capital_method'] = 2
        feedback.append("Innovative funding mechanism")
    elif any(word in content_lower for word in ['milestone', 'tranch', 'kpi']):
        scores['capital_method'] = 1
        feedback.append("Standard milestone-based")
    else:
        feedback.append("Traditional grant approach")
    
    # 6. Clarity
    if sections['tldr'] and len(sections['tldr']) > 30:
        if len(sections['tldr']) < 100:
            scores['clarity'] = 2
            feedback.append("Crystal clear TLDR")
        else:
            scores['clarity'] = 1
            feedback.append("TLDR too verbose")
    else:
        feedback.append("Missing clear TLDR")
    
    # 7. Execution Readiness
    if any(word in content_lower for word in ['immediately', 'ready', 'launched', 'active']):
        scores['execution_readiness'] = 2
        feedback.append("Ready to ship")
    elif any(word in content_lower for word in ['pilot', 'mvp', 'prototype', 'beta']):
        scores['execution_readiness'] = 1
        feedback.append("In pilot phase")
    else:
        feedback.append("Early stage")
    
    # 8. Vibe check
    positive_vibes = sum([
        'community' in content_lower,
        'open source' in content_lower,
        'public good' in content_lower,
        len(title) < 60,
        sections['tldr'] != '',
        '🚀' in content or '💪' in content or '🔥' in content
    ])
    
    if positive_vibes >= 4:
        scores['vibe_check'] = 2
        feedback.append("Great vibes")
    elif positive_vibes >= 2:
        scores['vibe_check'] = 1
        feedback.append("Decent energy")
    else:
        feedback.append("Needs more enthusiasm")
    
    # Add more specific feedback
    if 'ethereum' in content_lower:
        feedback.append("Ethereum-aligned")
    if 'decentralized' in content_lower:
        feedback.append("Values decentralization")
    
    total_score = sum(scores.values())
    
    return scores, total_score, feedback

def generate_steel_man_cases(sections, title, content):
    """Generate steel man cases for and against the proposal"""
    content_lower = content.lower()
    
    # Steel man FOR
    for_points = []
    if sections['problem']:
        for_points.append("Addresses real ecosystem need")
    if sections['domain_experts']:
        for_points.append("Has credible team")
    if 'community' in content_lower:
        for_points.append("Community-driven approach")
    if 'open source' in content_lower:
        for_points.append("Commitment to open source")
    if sections['solution']:
        for_points.append("Clear implementation path")
    
    steel_man_for = ". ".join(for_points[:3]) if for_points else "Has potential for ecosystem impact"
    
    # Steel man AGAINST
    against_points = []
    if not sections['domain_experts']:
        against_points.append("Lacks proven expertise")
    if not sections['funding']:
        against_points.append("Unclear funding sustainability")
    if 'research' in content_lower or 'study' in content_lower:
        against_points.append("May be too academic")
    if not sections['tldr'] or len(sections['tldr']) < 30:
        against_points.append("Lacks clear vision")
    if total_score < 8:
        against_points.append("Execution risk")
    
    steel_man_against = ". ".join(against_points[:3]) if against_points else "May not deliver promised impact"
    
    return steel_man_for, steel_man_against

def determine_deployment_strategy(sections, content):
    """Determine deployment strategy details"""
    content_lower = content.lower()
    
    # Domain type
    if 'ai' in content_lower or 'ml' in content_lower:
        domain_type = "AI/ML Infrastructure"
    elif 'defi' in content_lower:
        domain_type = "DeFi Protocol"
    elif 'governance' in content_lower:
        domain_type = "Governance System"
    elif 'popup' in content_lower or 'residency' in content_lower:
        domain_type = "Community Events"
    elif 'tooling' in content_lower or 'developer' in content_lower:
        domain_type = "Developer Infrastructure"
    elif 'privacy' in content_lower:
        domain_type = "Privacy Tech"
    elif 'science' in content_lower or 'desci' in content_lower:
        domain_type = "Decentralized Science"
    else:
        domain_type = "General Infrastructure"
    
    # Size
    if 'large' in content_lower or 'ecosystem' in content_lower:
        size = "Large"
    elif 'pilot' in content_lower or 'mvp' in content_lower:
        size = "Small"
    else:
        size = "Medium"
    
    # Timeline
    if 'immediate' in content_lower or 'ready' in content_lower:
        timeline = "1-3 months"
    elif 'year' in content_lower:
        timeline = "12+ months"
    else:
        timeline = "3-6 months"
    
    # Approach
    if 'community' in content_lower or 'democratic' in content_lower:
        approach = "Democratic/Community-driven"
    else:
        approach = "Technocratic/Expert-led"
    
    # Funding type
    if 'retroactive' in content_lower or 'hypercert' in content_lower:
        funding_type = "Retroactive"
    else:
        funding_type = "Proactive"
    
    # Capital needed
    if '$1m' in content_lower or 'million' in content_lower:
        capital = "$500K-$1M+"
    elif '$500' in content_lower:
        capital = "$200K-$500K"
    else:
        capital = "$50K-$200K"
    
    # Mechanism
    if 'hypercert' in content_lower:
        mechanism = "Hypercerts"
    elif 'quadratic' in content_lower:
        mechanism = "Quadratic funding"
    elif 'retroactive' in content_lower:
        mechanism = "Retroactive funding"
    else:
        mechanism = "Direct grants"
    
    return domain_type, size, timeline, approach, funding_type, capital, mechanism

def format_markdown_entry(row, sections, scores, total_score, feedback, steel_for, steel_against, deployment):
    """Format a single entry in markdown with all required fields"""
    title = row['Title']
    link = row['Link']
    author = row['Submitted By']
    
    domain_type, size, timeline, approach, funding_type, capital, mechanism = deployment
    
    md = f"""# [{title}]({link})

by {author}

### TLDR

{sections['tldr'] if sections['tldr'] else 'Impact-driven initiative for Ethereum ecosystem.'}

### Problem

{sections['problem'] if sections['problem'] else 'Coordination and funding challenges.'}

### Solution

{sections['solution'] if sections['solution'] else 'Systematic approach to ecosystem development.'}

### Domain Experts

{sections['domain_experts'] if sections['domain_experts'] else 'TBD'}

### Target Projects (Examples)

{sections['target_projects'] if sections['target_projects'] else 'Ethereum ecosystem projects'}

### Deployment strategy

{domain_type}
{size}
{timeline}
{approach}
{funding_type}
{capital}
{mechanism}

### Risks

{sections['risks'] if sections['risks'] else 'Execution and coordination risks'}

## Outside Funding

{sections['funding'] if sections['funding'] else 'Seeking partners'}

## Owockis scorecard

|#|Criterion|0|1|2|Notes|
| --- | --- | --- | --- | --- | --- |
|1|Problem Focus – Clearly frames a real problem, (one that is a priority), avoids "solutionism"|{"X" if scores['problem_focus'] == 0 else " "}|{"X" if scores['problem_focus'] == 1 else " "}|{"X" if scores['problem_focus'] == 2 else " "}||
|2|Credible, High leverage, Evidence-Based Approach – Solutions are high-leverage and grounded in credible research|{"X" if scores['credible_approach'] == 0 else " "}|{"X" if scores['credible_approach'] == 1 else " "}|{"X" if scores['credible_approach'] == 2 else " "}||
|3|Domain Expertise – Proposal has active involvement from recognized experts|{"X" if scores['domain_expertise'] == 0 else " "}|{"X" if scores['domain_expertise'] == 1 else " "}|{"X" if scores['domain_expertise'] == 2 else " "}||
|4|Co-Funding – Has financial backing beyond just Gitcoin|{"X" if scores['co_funding'] == 0 else " "}|{"X" if scores['co_funding'] == 1 else " "}|{"X" if scores['co_funding'] == 2 else " "}||
|5|Fit-for-Purpose Capital Allocation Method – Methodology matches the epistemology of the domain|{"X" if scores['capital_method'] == 0 else " "}|{"X" if scores['capital_method'] == 1 else " "}|{"X" if scores['capital_method'] == 2 else " "}||
|6|Clarity (TL;DR) – Includes a concise summary at the top|{"X" if scores['clarity'] == 0 else " "}|{"X" if scores['clarity'] == 1 else " "}|{"X" if scores['clarity'] == 2 else " "}||
|7|Execution Readiness – Can deliver meaningful results by October|{"X" if scores['execution_readiness'] == 0 else " "}|{"X" if scores['execution_readiness'] == 1 else " "}|{"X" if scores['execution_readiness'] == 2 else " "}||
|8|Other - general vibe check and other stuff I may have missed above..|{"X" if scores['vibe_check'] == 0 else " "}|{"X" if scores['vibe_check'] == 1 else " "}|{"X" if scores['vibe_check'] == 2 else " "}||

### Score

Total Score: {total_score} / 16

### Feedback:

"""
    
    for point in feedback[:10]:
        md += f"- {point}\n"
    
    md += f"""
### Steel man case for/against:

#### For

{steel_for}

#### Against

{steel_against}

"""
    
    return md, total_score

# Main processing
if __name__ == "__main__":
    # Read CSV data
    csv_data = []
    with open('/Users/owocki/Sites/gg24/data/data.csv', 'r') as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)
    
    # Process specified posts or first 3
    if len(sys.argv) > 1:
        if sys.argv[1] == 'all':
            posts_to_process = csv_data
        else:
            post_ids = sys.argv[1:]
            posts_to_process = [row for row in csv_data if any(pid in row['Link'] for pid in post_ids)]
    else:
        # First 3 posts
        posts_to_process = csv_data[:3]
    
    entries = []
    
    for row in posts_to_process:
        link = row['Link']
        post_id = link.split('/')[-1]
        filepath = f'/Users/owocki/Sites/gg24/posts/{post_id}.html'
        
        title, content = extract_full_content(filepath)
        if not title:
            title = row['Title']
        
        sections = parse_content_sections(content, title)
        scores, total_score, feedback = score_proposal_owocki_style(sections, title, content)
        steel_for, steel_against = generate_steel_man_cases(sections, title, content)
        deployment = determine_deployment_strategy(sections, content)
        
        entry_md, score = format_markdown_entry(row, sections, scores, total_score, feedback, steel_for, steel_against, deployment)
        entries.append((score, entry_md, row['Title'], row['Link'], row['Submitted By'], feedback, steel_for, steel_against))
    
    # Sort by score descending
    entries.sort(key=lambda x: x[0], reverse=True)
    
    # Generate output
    output = ""
    for score, entry_md, _, _, _, _, _, _ in entries:
        output += entry_md + "\n\n"
    
    print(output)