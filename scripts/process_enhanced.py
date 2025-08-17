#!/usr/bin/env python3
import re
import html as html_module
import csv
import sys
import os
from datetime import datetime

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
    
    return title, full_content[:10000]  # Increased for better extraction

def parse_content_sections(content, title):
    """Parse content into sections with enhanced extraction"""
    sections = {
        'tldr': '',
        'problem': '',
        'solution': '',
        'domain_experts': '',
        'expert_credentials': '',
        'target_projects': '',
        'impact_areas': '',
        'risks': '',
        'detailed_risks': '',
        'funding': '',
        'outside_funding': ''
    }
    
    content_lower = content.lower()
    
    # Extract TLDR - concise
    tldr_patterns = [
        r'(?:tldr|tl;dr|summary)[:\s;]+(.*?)(?:problem|challenge|background|$)',
        r'(?:in short|briefly)[:\s]+(.*?)(?:problem|challenge|$)',
    ]
    for pattern in tldr_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            tldr = match.group(1).strip()
            tldr = re.sub(r'\s+', ' ', tldr)
            sentences = re.split(r'[.!?]', tldr)
            if sentences:
                sections['tldr'] = sentences[0].strip()[:100]
            break
    
    if not sections['tldr']:
        sentences = re.split(r'[.!?]', content)
        for sent in sentences[:3]:
            if len(sent) > 30:
                sections['tldr'] = sent.strip()[:100]
                break
    
    # Extract Problem - concise
    prob_patterns = [
        r'problem[:\s&]+(.*?)(?:solution|approach|proposal|our solution|$)',
        r'challenge[:\s]+(.*?)(?:solution|approach|$)',
        r'the issue[:\s]+(.*?)(?:solution|approach|$)',
    ]
    for pattern in prob_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            prob = match.group(1).strip()
            sentences = re.split(r'[.!?]', prob)
            if sentences:
                sections['problem'] = sentences[0].strip()[:100]
            break
    
    # Extract Solution - concise
    sol_patterns = [
        r'(?:solution|approach|proposal)[:\s]+(.*?)(?:impact|outcome|implementation|domain|$)',
        r'we propose[:\s]+(.*?)(?:impact|this will|$)',
        r'our approach[:\s]+(.*?)(?:impact|outcome|$)',
    ]
    for pattern in sol_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            sol = match.group(1).strip()
            sentences = re.split(r'[.!?]', sol)
            if sentences:
                sections['solution'] = sentences[0].strip()[:100]
            break
    
    # Extract domain experts and their credentials
    mentions = re.findall(r'@\w+', content)
    if mentions:
        sections['domain_experts'] = ', '.join(set(mentions[:5]))
        
        # Try to extract credentials
        credentials = []
        for expert in mentions[:3]:
            # Look for context around the mention
            expert_pattern = f"{expert}[^.]*(?:is|are|has|have|with|from)[^.]*"
            expert_match = re.search(expert_pattern, content, re.IGNORECASE)
            if expert_match:
                cred = expert_match.group(0).strip()[:50]
                credentials.append(cred)
        
        if credentials:
            sections['expert_credentials'] = '; '.join(credentials[:2])
        else:
            sections['expert_credentials'] = 'Contributors to proposal'
    
    # Determine impact area
    impact_keywords = {
        'AI/ML': ['ai', 'artificial intelligence', 'machine learning', 'llm'],
        'DeFi': ['defi', 'decentralized finance', 'liquidity', 'amm'],
        'Governance': ['governance', 'voting', 'dao', 'paradox'],
        'Infrastructure': ['infrastructure', 'tooling', 'developer', 'sdk'],
        'Privacy': ['privacy', 'kyc', 'zero knowledge', 'zk', 'maci'],
        'Science': ['desci', 'science', 'research', 'academic'],
        'Community': ['popup', 'residency', 'community', 'events'],
        'Funding': ['funding', 'grant', 'pgf', 'hypercert'],
        'Data': ['data', 'analytics', 'information', 'infofi'],
        'Adoption': ['adoption', 'ux', 'user experience', 'consumer']
    }
    
    for area, keywords in impact_keywords.items():
        if any(kw in content_lower for kw in keywords):
            sections['impact_areas'] = area
            break
    
    if not sections['impact_areas']:
        sections['impact_areas'] = 'General'
    
    # Extract detailed risks
    risk_patterns = [
        r'(?:risk|challenge|concern)[:\s]+(.*?)(?:mitigation|solution|conclusion|$)',
        r'(?:execution risk|implementation risk)[:\s]+(.*?)(?:mitigation|$)',
        r'(?:dependency|dependencies)[:\s]+(.*?)(?:mitigation|solution|$)',
    ]
    
    risks = []
    for pattern in risk_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches[:2]:
            risk_text = match.strip()
            sentences = re.split(r'[.!?]', risk_text)
            if sentences and sentences[0]:
                risks.append(sentences[0].strip()[:80])
    
    if risks:
        sections['risks'] = risks[0][:80]
        sections['detailed_risks'] = '; '.join(risks[:3])
    else:
        sections['risks'] = 'Execution risk'
        sections['detailed_risks'] = 'Timeline delays; resource constraints; adoption challenges'
    
    # Extract funding info
    fund_patterns = [
        r'(?:funding|grant|budget)[:\s]+(.*?)(?:timeline|implementation|$)',
        r'(?:seeking|request|need)[:\s]*\$?([\d,kKmM]+)',
        r'\$?([\d,]+[kKmM]?)(?:\s+in\s+funding)',
    ]
    
    for pattern in fund_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            fund_text = match.group(1).strip() if match.lastindex == 1 else match.group(0).strip()
            sections['funding'] = fund_text[:80]
            break
    
    # Extract outside funding
    if any(word in content_lower for word in ['secured', 'committed', 'partnered', 'matched', 'raised']):
        outside_patterns = [
            r'(?:secured|committed|partnered with|matched by)[:\s]+(.*?)(?:\.|$)',
            r'(?:external funding|outside funding|co-funding)[:\s]+(.*?)(?:\.|$)',
        ]
        for pattern in outside_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                sections['outside_funding'] = match.group(1).strip()[:80]
                break
    
    if not sections['outside_funding']:
        if 'seeking' in content_lower and 'partner' in content_lower:
            sections['outside_funding'] = 'Seeking partners'
        else:
            sections['outside_funding'] = 'None mentioned'
    
    # Extract target projects
    if 'example' in content_lower or 'project' in content_lower:
        proj_patterns = [
            r'(?:example|project|target)[:\s]+(.*?)(?:impact|outcome|$)',
            r'(?:such as|including|like)[:\s]+(.*?)(?:\.|$)',
        ]
        for pattern in proj_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                proj_text = match.group(1).strip()
                sentences = re.split(r'[.!?,]', proj_text)
                if sentences:
                    sections['target_projects'] = sentences[0].strip()[:80]
                break
    
    if not sections['target_projects']:
        sections['target_projects'] = 'TBD'
    
    return sections

def score_proposal_owocki_style(sections, title, content):
    """Score the proposal in Kevin Owocki's vision with explanations"""
    scores = {}
    explanations = {}
    feedback = []
    content_lower = content.lower()
    
    # 1. Problem Focus
    if sections['problem'] and len(sections['problem']) > 30:
        if any(word in sections['problem'].lower() for word in ['critical', 'urgent', 'fundamental', 'bottleneck', 'broken']):
            scores['problem_focus'] = 2
            explanations['problem_focus'] = "Clear critical problem"
            feedback.append("Strong problem framing")
        else:
            scores['problem_focus'] = 1
            explanations['problem_focus'] = "Problem exists but not compelling"
            feedback.append("Problem needs sharpening")
    else:
        scores['problem_focus'] = 0
        explanations['problem_focus'] = "No clear problem stated"
        feedback.append("Missing problem definition")
    
    # 2. Credible Approach
    if sections['solution'] and len(sections['solution']) > 30:
        if any(word in content_lower for word in ['proven', 'evidence', 'research', 'data', 'tested', 'pilot', 'live']):
            scores['credible_approach'] = 2
            explanations['credible_approach'] = "Evidence-based approach"
            feedback.append("Credible approach")
        else:
            scores['credible_approach'] = 1
            explanations['credible_approach'] = "Approach needs validation"
            feedback.append("Needs evidence")
    else:
        scores['credible_approach'] = 0
        explanations['credible_approach'] = "No clear solution"
        feedback.append("Solution unclear")
    
    # 3. Domain Expertise
    if sections['domain_experts']:
        expert_count = len(sections['domain_experts'].split(','))
        if expert_count >= 3:
            scores['domain_expertise'] = 2
            explanations['domain_expertise'] = "Strong expert team"
            feedback.append("Great team")
        elif expert_count >= 1:
            scores['domain_expertise'] = 1
            explanations['domain_expertise'] = "Some expertise present"
            feedback.append("Limited experts")
        else:
            scores['domain_expertise'] = 0
            explanations['domain_expertise'] = "No experts identified"
            feedback.append("Need experts")
    else:
        scores['domain_expertise'] = 0
        explanations['domain_expertise'] = "No experts identified"
        feedback.append("Missing expertise")
    
    # 4. Co-funding
    if sections['outside_funding'] and sections['outside_funding'] != 'None mentioned':
        if any(word in sections['outside_funding'].lower() for word in ['secured', 'committed', 'partnered']):
            scores['co_funding'] = 2
            explanations['co_funding'] = "Has secured co-funding"
            feedback.append("Co-funded")
        else:
            scores['co_funding'] = 1
            explanations['co_funding'] = "Seeking co-funding"
            feedback.append("Seeking partners")
    else:
        scores['co_funding'] = 0
        explanations['co_funding'] = "No co-funding mentioned"
        feedback.append("No co-funding")
    
    # 5. Capital Method
    if any(word in content_lower for word in ['hypercert', 'retroactive', 'outcome', 'impact cert', 'maci']):
        scores['capital_method'] = 2
        explanations['capital_method'] = "Innovative funding mechanism"
        feedback.append("Novel mechanism")
    elif any(word in content_lower for word in ['milestone', 'tranch', 'kpi', 'quadratic']):
        scores['capital_method'] = 1
        explanations['capital_method'] = "Standard milestone-based"
        feedback.append("Traditional method")
    else:
        scores['capital_method'] = 0
        explanations['capital_method'] = "Basic grant approach"
        feedback.append("Simple grant")
    
    # 6. Clarity
    if sections['tldr'] and len(sections['tldr']) > 20:
        if len(sections['tldr']) < 80:
            scores['clarity'] = 2
            explanations['clarity'] = "Crystal clear TLDR"
            feedback.append("Clear vision")
        else:
            scores['clarity'] = 1
            explanations['clarity'] = "TLDR present but verbose"
            feedback.append("TLDR verbose")
    else:
        scores['clarity'] = 0
        explanations['clarity'] = "Missing clear TLDR"
        feedback.append("Needs TLDR")
    
    # 7. Execution Readiness
    if any(word in content_lower for word in ['immediately', 'ready', 'launched', 'active', 'live', 'deployed']):
        scores['execution_readiness'] = 2
        explanations['execution_readiness'] = "Ready to ship now"
        feedback.append("Ship ready")
    elif any(word in content_lower for word in ['pilot', 'mvp', 'prototype', 'beta', 'testing']):
        scores['execution_readiness'] = 1
        explanations['execution_readiness'] = "In pilot phase"
        feedback.append("Pilot stage")
    else:
        scores['execution_readiness'] = 0
        explanations['execution_readiness'] = "Early stage"
        feedback.append("Too early")
    
    # 8. Vibe check
    positive_vibes = sum([
        'community' in content_lower,
        'open source' in content_lower,
        'public good' in content_lower,
        'ethereum' in content_lower,
        'decentralized' in content_lower,
        sections['tldr'] != '',
    ])
    
    if positive_vibes >= 4:
        scores['vibe_check'] = 2
        explanations['vibe_check'] = "Great energy and alignment"
        feedback.append("Vibes immaculate")
    elif positive_vibes >= 2:
        scores['vibe_check'] = 1
        explanations['vibe_check'] = "Decent energy"
        feedback.append("Vibes OK")
    else:
        scores['vibe_check'] = 0
        explanations['vibe_check'] = "Needs enthusiasm"
        feedback.append("Vibes off")
    
    # Add specific feedback
    if 'ethereum' in content_lower:
        feedback.append("ETH-aligned")
    if 'decentralized' in content_lower:
        feedback.append("Decentralized")
    
    total_score = sum(scores.values())
    
    # Calculate confidence
    confidence = 50
    if sections['tldr']: confidence += 10
    if sections['problem']: confidence += 10
    if sections['solution']: confidence += 10
    if sections['domain_experts']: confidence += 10
    if sections['funding']: confidence += 5
    if sections['outside_funding'] != 'None mentioned': confidence += 5
    confidence = min(confidence, 95)
    
    return scores, explanations, total_score, feedback[:10], confidence

def generate_steel_man_cases(sections, title, content, total_score):
    """Generate steel man cases - concise"""
    content_lower = content.lower()
    
    # Steel man FOR
    for_points = []
    if sections['problem']:
        for_points.append("Addresses real need")
    if sections['domain_experts']:
        for_points.append("Has expertise")
    if 'community' in content_lower:
        for_points.append("Community-driven")
    if sections['solution']:
        for_points.append("Clear solution")
    if total_score >= 10:
        for_points.append("Well thought out")
    
    steel_man_for = ". ".join(for_points[:3]) if for_points else "Has potential"
    
    # Steel man AGAINST
    against_points = []
    if not sections['domain_experts']:
        against_points.append("Lacks proven team")
    if sections['outside_funding'] == 'None mentioned':
        against_points.append("No co-funding")
    if total_score < 8:
        against_points.append("Execution risk high")
    if not sections['tldr'] or len(sections['tldr']) < 30:
        against_points.append("Vision unclear")
    if 'research' in content_lower:
        against_points.append("Too academic")
    
    steel_man_against = ". ".join(against_points[:3]) if against_points else "May not deliver"
    
    return steel_man_for, steel_man_against

def determine_deployment_strategy(sections, content):
    """Determine deployment strategy - concise"""
    content_lower = content.lower()
    
    # Domain type
    if 'ai' in content_lower or 'ml' in content_lower:
        domain_type = "AI"
    elif 'defi' in content_lower:
        domain_type = "DeFi"  
    elif 'governance' in content_lower:
        domain_type = "Governance"
    elif 'popup' in content_lower or 'residency' in content_lower:
        domain_type = "Events"
    elif 'tooling' in content_lower or 'developer' in content_lower:
        domain_type = "Dev Tools"
    elif 'privacy' in content_lower or 'kyc' in content_lower:
        domain_type = "Privacy"
    elif 'science' in content_lower or 'desci' in content_lower:
        domain_type = "DeSci"
    elif 'data' in content_lower or 'analytics' in content_lower:
        domain_type = "Data"
    else:
        domain_type = "General"
    
    # Size
    if 'ecosystem' in content_lower or 'large' in content_lower:
        size = "Large"
    elif 'pilot' in content_lower or 'small' in content_lower:
        size = "Small"
    else:
        size = "Medium"
    
    # Timeline
    if 'immediate' in content_lower or 'ready' in content_lower:
        timeline = "1-3mo"
    elif 'year' in content_lower:
        timeline = "12mo+"
    else:
        timeline = "3-6mo"
    
    # Approach
    if 'community' in content_lower or 'democratic' in content_lower:
        approach = "Democratic"
    else:
        approach = "Technocratic"
    
    # Funding type
    if 'retroactive' in content_lower or 'hypercert' in content_lower:
        funding_type = "Retroactive"
    else:
        funding_type = "Proactive"
    
    # Capital needed
    if '$1m' in content_lower or 'million' in content_lower:
        capital = "$1M+"
    elif '$500' in content_lower or '500k' in content_lower:
        capital = "$500K"
    elif '$100' in content_lower or '100k' in content_lower:
        capital = "$100K"
    else:
        capital = "$50K"
    
    # Mechanism
    if 'hypercert' in content_lower:
        mechanism = "Hypercerts"
    elif 'quadratic' in content_lower:
        mechanism = "QF"
    elif 'retroactive' in content_lower:
        mechanism = "Retroactive"
    elif 'maci' in content_lower:
        mechanism = "MACI"
    else:
        mechanism = "Direct grant"
    
    return domain_type, size, timeline, approach, funding_type, capital, mechanism

def format_markdown_entry(row, sections, scores, explanations, total_score, confidence, feedback, steel_for, steel_against, deployment):
    """Format a single entry in markdown"""
    title = row['Title']
    link = row['Link']
    author = row['Submitted By']
    
    domain_type, size, timeline, approach, funding_type, capital, mechanism = deployment
    
    md = f"""# [{title}]({link})

by {author}

### TLDR

{sections['tldr'] if sections['tldr'] else 'Initiative'}

### Problem

{sections['problem'] if sections['problem'] else 'Challenges'}

### Solution

{sections['solution'] if sections['solution'] else 'Approach'}

### Domain Experts

{sections['domain_experts'] if sections['domain_experts'] else 'TBD'}
{sections['expert_credentials'] if sections['expert_credentials'] else 'Contributors'}

### Target Projects (Examples)

{sections['target_projects']}

### Deployment strategy

{domain_type}
{size}
{timeline}
{approach}
{funding_type}
{capital}
{mechanism}

### Risks

{sections['detailed_risks']}

## Outside Funding

{sections['outside_funding']}

## Owockis scorecard

|#|Criterion|0|1|2|Notes|
| --- | --- | --- | --- | --- | --- |
|1|Problem Focus – Clearly frames a real problem, (one that is a priority), avoids "solutionism"|{"X" if scores['problem_focus'] == 0 else " "}|{"X" if scores['problem_focus'] == 1 else " "}|{"X" if scores['problem_focus'] == 2 else " "}|{explanations['problem_focus']}|
|2|Credible, High leverage, Evidence-Based Approach – Solutions are high-leverage and grounded in credible research|{"X" if scores['credible_approach'] == 0 else " "}|{"X" if scores['credible_approach'] == 1 else " "}|{"X" if scores['credible_approach'] == 2 else " "}|{explanations['credible_approach']}|
|3|Domain Expertise – Proposal has active involvement from recognized experts|{"X" if scores['domain_expertise'] == 0 else " "}|{"X" if scores['domain_expertise'] == 1 else " "}|{"X" if scores['domain_expertise'] == 2 else " "}|{explanations['domain_expertise']}|
|4|Co-Funding – Has financial backing beyond just Gitcoin|{"X" if scores['co_funding'] == 0 else " "}|{"X" if scores['co_funding'] == 1 else " "}|{"X" if scores['co_funding'] == 2 else " "}|{explanations['co_funding']}|
|5|Fit-for-Purpose Capital Allocation Method – Methodology matches the epistemology of the domain|{"X" if scores['capital_method'] == 0 else " "}|{"X" if scores['capital_method'] == 1 else " "}|{"X" if scores['capital_method'] == 2 else " "}|{explanations['capital_method']}|
|6|Clarity (TL;DR) – Includes a concise summary at the top|{"X" if scores['clarity'] == 0 else " "}|{"X" if scores['clarity'] == 1 else " "}|{"X" if scores['clarity'] == 2 else " "}|{explanations['clarity']}|
|7|Execution Readiness – Can deliver meaningful results by October|{"X" if scores['execution_readiness'] == 0 else " "}|{"X" if scores['execution_readiness'] == 1 else " "}|{"X" if scores['execution_readiness'] == 2 else " "}|{explanations['execution_readiness']}|
|8|Other - general vibe check and other stuff I may have missed above..|{"X" if scores['vibe_check'] == 0 else " "}|{"X" if scores['vibe_check'] == 1 else " "}|{"X" if scores['vibe_check'] == 2 else " "}|{explanations['vibe_check']}|

### Score

Confidence : {confidence}% (how confident agent is about the score)
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

def generate_owocki_feedback(title, sections, total_score):
    """Generate Owocki-style feedback"""
    if total_score >= 12:
        return "Ship it"
    elif total_score >= 8:
        return "Solid, refine"
    elif total_score >= 5:
        return "Has potential"
    else:
        return "Needs work"

def generate_rose_thorn_bud(sections, total_score):
    """Generate rose, thorn, bud"""
    rose = "Clear vision" if sections['tldr'] else "Community focus"
    
    if not sections['domain_experts']:
        thorn = "Needs experts"
    elif sections['outside_funding'] == 'None mentioned':
        thorn = "No co-funding"
    else:
        thorn = "Execution risk"
    
    if total_score >= 8:
        bud = "High impact"
    else:
        bud = "Could evolve"
    
    return rose, thorn, bud

# Main processing
if __name__ == "__main__":
    # Read CSV data
    csv_data = []
    with open('/Users/owocki/Sites/gg24/data/data.csv', 'r') as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)
    
    # Process all proposals
    posts_to_process = csv_data
    
    entries = []
    leaderboard_data = []
    
    for row in posts_to_process:
        link = row['Link']
        post_id = link.split('/')[-1]
        filepath = f'/Users/owocki/Sites/gg24/posts/{post_id}.html'
        
        title, content = extract_full_content(filepath)
        if not title:
            title = row['Title']
        
        sections = parse_content_sections(content, title)
        scores, explanations, total_score, feedback, confidence = score_proposal_owocki_style(sections, title, content)
        steel_for, steel_against = generate_steel_man_cases(sections, title, content, total_score)
        deployment = determine_deployment_strategy(sections, content)
        
        entry_md, score = format_markdown_entry(row, sections, scores, explanations, total_score, confidence, feedback, steel_for, steel_against, deployment)
        entries.append((score, entry_md, row['Title'], row['Link'], row['Submitted By']))
        
        # Generate leaderboard data
        high_level_feedback = generate_owocki_feedback(title, sections, total_score)
        rose, thorn, bud = generate_rose_thorn_bud(sections, total_score)
        leaderboard_data.append({
            'title': f"[{row['Title']}]({row['Link']})",
            'author': row['Submitted By'], 
            'score': total_score,
            'feedback': high_level_feedback,
            'rose': rose,
            'thorn': thorn,
            'bud': bud
        })
    
    # Sort by score descending
    entries.sort(key=lambda x: x[0], reverse=True)
    leaderboard_data.sort(key=lambda x: x['score'], reverse=True)
    
    # Generate output with header
    today = datetime.now().strftime("%Y/%m/%d")
    output = f"""# Sensemaking about GG24 Sensemaking
## {today} - Version 0.1.0
## By Owocki

(vibe-written by claude code using [this prompt](https://github.com/owocki/gg24/blob/main/prompt.txt), iterated on, + edited for accuracy quality and legibility by owocki himself.

## Leaderboard

| Proposal | Score | Feedback | Rose | Thorn | Bud |
| --- | --- | --- | --- | --- | --- |
"""
    
    for item in leaderboard_data:
        output += f"| {item['title']} by {item['author']} | {item['score']}/16 | {item['feedback']} | {item['rose']} | {item['thorn']} | {item['bud']} |\n"
    
    output += "\n# Reports\n\n"
    
    # Add sorted entries with rating in title
    for score, entry_md, title, link, author in entries:
        # Update the title to include the rating
        entry_md_with_rating = entry_md.replace(f"# [{title}]({link})", f"# ({score}) [{title}]({link})")
        output += entry_md_with_rating + "\n\n"
    
    # Write to file
    with open('/Users/owocki/Sites/gg24/data/data.md', 'w') as f:
        f.write(output)
    
    print(f"Created data.md with {len(entries)} proposals processed")