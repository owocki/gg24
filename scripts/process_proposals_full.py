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
    
    # Extract TLDR - more concise
    tldr_patterns = [
        r'(?:tldr|tl;dr|summary)[:\s;]+(.*?)(?:problem|challenge|background|$)',
        r'(?:in short|briefly)[:\s]+(.*?)(?:problem|challenge|$)',
    ]
    for pattern in tldr_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            tldr = match.group(1).strip()
            tldr = re.sub(r'\s+', ' ', tldr)
            # Make it more concise - take first sentence only
            sentences = re.split(r'[.!?]', tldr)
            if sentences:
                sections['tldr'] = sentences[0].strip()[:100]
            break
    
    if not sections['tldr']:
        # Extract first meaningful sentence
        sentences = re.split(r'[.!?]', content)
        for sent in sentences[:3]:
            if len(sent) > 30:
                sections['tldr'] = sent.strip()[:100]
                break
    
    # Extract Problem - concise
    prob_patterns = [
        r'problem[:\s&]+(.*?)(?:solution|approach|proposal|$)',
        r'challenge[:\s]+(.*?)(?:solution|approach|$)',
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
        r'(?:solution|approach|proposal)[:\s]+(.*?)(?:impact|outcome|implementation|$)',
        r'we propose[:\s]+(.*?)(?:impact|this will|$)',
    ]
    for pattern in sol_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            sol = match.group(1).strip()
            sentences = re.split(r'[.!?]', sol)
            if sentences:
                sections['solution'] = sentences[0].strip()[:100]
            break
    
    # Extract domain experts
    mentions = re.findall(r'@\w+', content)
    if mentions:
        sections['domain_experts'] = ', '.join(set(mentions[:3]))
    
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
    
    # Extract risks - concise
    risk_patterns = [
        r'risk[:\s]+(.*?)(?:mitigation|conclusion|$)',
        r'challenge[:\s]+(.*?)(?:mitigation|$)',
    ]
    for pattern in risk_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            risk = match.group(1).strip()
            sentences = re.split(r'[.!?]', risk)
            if sentences:
                sections['risks'] = sentences[0].strip()[:80]
            break
    
    # Extract funding info - concise
    if 'funding' in content_lower or 'grant' in content_lower or '$' in content:
        fund_match = re.search(r'(?:funding|grant|budget)[:\s]+(.*?)(?:timeline|implementation|$)', content, re.IGNORECASE | re.DOTALL)
        if fund_match:
            fund_text = fund_match.group(1).strip()
            sentences = re.split(r'[.!?]', fund_text)
            if sentences:
                sections['funding'] = sentences[0].strip()[:80]
    
    # Extract target projects - concise
    if 'example' in content_lower or 'project' in content_lower:
        proj_match = re.search(r'(?:example|project|target)[:\s]+(.*?)(?:impact|outcome|$)', content, re.IGNORECASE | re.DOTALL)
        if proj_match:
            proj_text = proj_match.group(1).strip()
            sentences = re.split(r'[.!?]', proj_text)
            if sentences:
                sections['target_projects'] = sentences[0].strip()[:80]
    
    return sections

def score_proposal_owocki_style(sections, title, content):
    """Score the proposal in Kevin Owocki's voice and style with explanations"""
    scores = {}
    explanations = {}
    feedback = []
    content_lower = content.lower()
    
    # 1. Problem Focus
    if sections['problem'] and len(sections['problem']) > 30:
        if any(word in sections['problem'].lower() for word in ['critical', 'urgent', 'fundamental', 'bottleneck', 'broken']):
            scores['problem_focus'] = 2
            explanations['problem_focus'] = "Clear critical problem"
            feedback.append("Clear problem")
        else:
            scores['problem_focus'] = 1
            explanations['problem_focus'] = "Problem exists but not compelling"
            feedback.append("Problem unclear")
    else:
        scores['problem_focus'] = 0
        explanations['problem_focus'] = "No clear problem stated"
        feedback.append("No problem")
    
    # 2. Credible Approach
    if sections['solution'] and len(sections['solution']) > 30:
        if any(word in content_lower for word in ['proven', 'evidence', 'research', 'data', 'tested', 'pilot']):
            scores['credible_approach'] = 2
            explanations['credible_approach'] = "Evidence-based approach"
            feedback.append("Evidence-based")
        else:
            scores['credible_approach'] = 1
            explanations['credible_approach'] = "Approach needs validation"
            feedback.append("Needs validation")
    else:
        scores['credible_approach'] = 0
        explanations['credible_approach'] = "No clear solution"
        feedback.append("No solution")
    
    # 3. Domain Expertise
    if sections['domain_experts']:
        expert_count = len(sections['domain_experts'].split(','))
        if expert_count >= 2:
            scores['domain_expertise'] = 2
            explanations['domain_expertise'] = "Strong expert team"
            feedback.append("Has experts")
        else:
            scores['domain_expertise'] = 1
            explanations['domain_expertise'] = "Limited expertise"
            feedback.append("Few experts")
    else:
        scores['domain_expertise'] = 0
        explanations['domain_expertise'] = "No experts identified"
        feedback.append("No experts")
    
    # 4. Co-funding
    if 'funding' in content_lower:
        if any(word in content_lower for word in ['secured', 'committed', 'partnered', 'matched', 'raised']):
            scores['co_funding'] = 2
            explanations['co_funding'] = "Has secured co-funding"
            feedback.append("Co-funded")
        elif 'seeking' in content_lower or 'looking for' in content_lower:
            scores['co_funding'] = 1
            explanations['co_funding'] = "Actively seeking co-funding"
            feedback.append("Seeking funds")
        else:
            scores['co_funding'] = 0
            explanations['co_funding'] = "No co-funding mentioned"
            feedback.append("No co-funding")
    else:
        scores['co_funding'] = 0
        explanations['co_funding'] = "No funding info"
    
    # 5. Capital Method
    if any(word in content_lower for word in ['hypercert', 'retroactive', 'outcome', 'impact cert', 'maci']):
        scores['capital_method'] = 2
        explanations['capital_method'] = "Innovative funding mechanism"
        feedback.append("Novel mechanism")
    elif any(word in content_lower for word in ['milestone', 'tranch', 'kpi', 'quadratic']):
        scores['capital_method'] = 1
        explanations['capital_method'] = "Standard milestone-based"
        feedback.append("Standard method")
    else:
        scores['capital_method'] = 0
        explanations['capital_method'] = "Traditional grant approach"
        feedback.append("Basic grant")
    
    # 6. Clarity
    if sections['tldr'] and len(sections['tldr']) > 20:
        if len(sections['tldr']) < 80:
            scores['clarity'] = 2
            explanations['clarity'] = "Crystal clear TLDR"
            feedback.append("Clear TLDR")
        else:
            scores['clarity'] = 1
            explanations['clarity'] = "TLDR too verbose"
            feedback.append("TLDR long")
    else:
        scores['clarity'] = 0
        explanations['clarity'] = "Missing clear TLDR"
        feedback.append("No TLDR")
    
    # 7. Execution Readiness
    if any(word in content_lower for word in ['immediately', 'ready', 'launched', 'active', 'live']):
        scores['execution_readiness'] = 2
        explanations['execution_readiness'] = "Ready to ship now"
        feedback.append("Ready now")
    elif any(word in content_lower for word in ['pilot', 'mvp', 'prototype', 'beta', 'testing']):
        scores['execution_readiness'] = 1
        explanations['execution_readiness'] = "In pilot phase"
        feedback.append("In pilot")
    else:
        scores['execution_readiness'] = 0
        explanations['execution_readiness'] = "Early stage, not ready"
        feedback.append("Early stage")
    
    # 8. Vibe check
    positive_vibes = sum([
        'community' in content_lower,
        'open source' in content_lower,
        'public good' in content_lower,
        'ethereum' in content_lower,
        sections['tldr'] != '',
    ])
    
    if positive_vibes >= 4:
        scores['vibe_check'] = 2
        explanations['vibe_check'] = "Great energy and alignment"
        feedback.append("Good vibes")
    elif positive_vibes >= 2:
        scores['vibe_check'] = 1
        explanations['vibe_check'] = "Decent energy"
        feedback.append("OK vibes")
    else:
        scores['vibe_check'] = 0
        explanations['vibe_check'] = "Needs more enthusiasm"
        feedback.append("Meh vibes")
    
    # Add concise specific feedback
    if 'ethereum' in content_lower:
        feedback.append("ETH-aligned")
    if 'decentralized' in content_lower:
        feedback.append("Decentralized")
    
    total_score = sum(scores.values())
    
    # Calculate confidence based on how much info we have
    confidence = 50  # Base confidence
    if sections['tldr']: confidence += 10
    if sections['problem']: confidence += 10
    if sections['solution']: confidence += 10
    if sections['domain_experts']: confidence += 10
    if sections['funding']: confidence += 10
    confidence = min(confidence, 95)  # Cap at 95%
    
    return scores, explanations, total_score, feedback[:10], confidence

def generate_steel_man_cases(sections, title, content, total_score):
    """Generate steel man cases for and against the proposal"""
    content_lower = content.lower()
    
    # Steel man FOR - very concise
    for_points = []
    if sections['problem']:
        for_points.append("Addresses real need")
    if sections['domain_experts']:
        for_points.append("Has team")
    if 'community' in content_lower:
        for_points.append("Community-driven")
    if sections['solution']:
        for_points.append("Clear path")
    
    steel_man_for = ". ".join(for_points[:2]) if for_points else "Has potential"
    
    # Steel man AGAINST - very concise
    against_points = []
    if not sections['domain_experts']:
        against_points.append("No proven team")
    if not sections['funding']:
        against_points.append("Unclear funding")
    if total_score < 8:
        against_points.append("Execution risk")
    if not sections['tldr']:
        against_points.append("Unclear vision")
    
    steel_man_against = ". ".join(against_points[:2]) if against_points else "May not deliver"
    
    return steel_man_for, steel_man_against

def determine_deployment_strategy(sections, content):
    """Determine deployment strategy details - concise"""
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
    elif 'privacy' in content_lower:
        domain_type = "Privacy"
    elif 'science' in content_lower or 'desci' in content_lower:
        domain_type = "DeSci"
    else:
        domain_type = "General"
    
    # Size
    if 'large' in content_lower or 'ecosystem' in content_lower:
        size = "Large"
    elif 'pilot' in content_lower or 'mvp' in content_lower:
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
        approach = "Community"
    else:
        approach = "Expert"
    
    # Funding type
    if 'retroactive' in content_lower or 'hypercert' in content_lower:
        funding_type = "Retro"
    else:
        funding_type = "Proactive"
    
    # Capital needed
    if '$1m' in content_lower or 'million' in content_lower:
        capital = "$1M+"
    elif '$500' in content_lower:
        capital = "$500K"
    else:
        capital = "$100K"
    
    # Mechanism
    if 'hypercert' in content_lower:
        mechanism = "Hypercerts"
    elif 'quadratic' in content_lower:
        mechanism = "QF"
    elif 'retroactive' in content_lower:
        mechanism = "Retro"
    else:
        mechanism = "Direct"
    
    return domain_type, size, timeline, approach, funding_type, capital, mechanism

def format_markdown_entry(row, sections, scores, explanations, total_score, confidence, feedback, steel_for, steel_against, deployment):
    """Format a single entry in markdown with all required fields"""
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

### Target Projects (Examples)

{sections['target_projects'] if sections['target_projects'] else 'TBD'}

### Deployment strategy

{domain_type}
{size}
{timeline}
{approach}
{funding_type}
{capital}
{mechanism}

### Risks

{sections['risks'] if sections['risks'] else 'Execution'}

## Outside Funding

{sections['funding'] if sections['funding'] else 'TBD'}

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
    """Generate Owocki-style high level feedback - very concise"""
    if total_score >= 12:
        return "Strong proposal, ship it"
    elif total_score >= 8:
        return "Solid, needs refinement"
    elif total_score >= 5:
        return "Has potential, needs work"
    else:
        return "Needs major rethinking"

def generate_rose_thorn_bud(sections, total_score):
    """Generate rose, thorn, bud feedback - very concise"""
    rose = "Clear vision" if sections['tldr'] else "Community focus"
    
    if not sections['domain_experts']:
        thorn = "Needs experts"
    elif not sections['funding']:
        thorn = "Funding unclear"
    else:
        thorn = "Execution risk"
    
    if total_score >= 8:
        bud = "High impact potential"
    else:
        bud = "Could evolve well"
    
    return rose, thorn, bud

# Main processing
if __name__ == "__main__":
    # Read CSV data
    csv_data = []
    with open('/Users/owocki/Sites/gg24/data/data.csv', 'r') as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)
    
    # Process only first 3 posts
    posts_to_process = csv_data[:3]
    
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
        # Update the title in the markdown to include the rating
        entry_md_with_rating = entry_md.replace(f"# [{title}]({link})", f"# ({score}) [{title}]({link})")
        output += entry_md_with_rating + "\n\n"
    
    # Write to file
    with open('/Users/owocki/Sites/gg24/data/data.md', 'w') as f:
        f.write(output)
    
    print(f"Created data.md with {len(entries)} proposals processed")