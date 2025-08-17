#!/usr/bin/env python3
import re
import html as html_module
import csv
import sys

def extract_full_content(filepath):
    """Extract full content from HTML file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Try to extract from meta description first (has summary)
    meta_match = re.search(r'<meta property="og:description" content="([^"]+)"', content)
    meta_content = html_module.unescape(meta_match.group(1)) if meta_match else ""
    
    # Extract title
    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', content)
    title = html_module.unescape(title_match.group(1)) if title_match else ""
    
    return title, meta_content

def parse_content_sections(content):
    """Parse content into sections based on common patterns"""
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
    if 'tldr' in content_lower or 'tl;dr' in content_lower:
        tldr_match = re.search(r'(tldr|tl;dr)[;:\s]+(.*?)(?:problem|solution|$)', content, re.IGNORECASE | re.DOTALL)
        if tldr_match:
            sections['tldr'] = tldr_match.group(2).strip()[:200]
    
    # Extract Problem
    if 'problem' in content_lower:
        prob_match = re.search(r'problem[:\s&]+(.*?)(?:solution|approach|$)', content, re.IGNORECASE | re.DOTALL)
        if prob_match:
            sections['problem'] = prob_match.group(1).strip()[:200]
    
    # Extract Solution
    if 'solution' in content_lower or 'approach' in content_lower:
        sol_match = re.search(r'(solution|approach)[:\s]+(.*?)(?:impact|domain|$)', content, re.IGNORECASE | re.DOTALL)
        if sol_match:
            sections['solution'] = sol_match.group(2).strip()[:200]
    
    # Extract domain experts (look for @mentions)
    mentions = re.findall(r'@\w+', content)
    if mentions:
        sections['domain_experts'] = ', '.join(mentions[:3])
    
    # Determine impact area
    if 'ai' in content_lower or 'artificial intelligence' in content_lower:
        sections['impact_areas'] = 'AI/ML'
    elif 'defi' in content_lower:
        sections['impact_areas'] = 'DeFi'
    elif 'governance' in content_lower:
        sections['impact_areas'] = 'Governance'
    elif 'funding' in content_lower or 'pgf' in content_lower:
        sections['impact_areas'] = 'Funding Models'
    elif 'popup' in content_lower or 'residenc' in content_lower:
        sections['impact_areas'] = 'Community Building'
    else:
        sections['impact_areas'] = 'Infrastructure'
    
    # Extract risks
    if 'risk' in content_lower:
        risk_match = re.search(r'risk[:\s]+(.*?)(?:mitigation|conclusion|$)', content, re.IGNORECASE | re.DOTALL)
        if risk_match:
            sections['risks'] = risk_match.group(1).strip()[:200]
    
    return sections

def score_proposal(sections, title, content):
    """Score the proposal based on Kevin Owocki's criteria"""
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
    
    # 1. Problem Focus
    if sections['problem'] and len(sections['problem']) > 50:
        scores['problem_focus'] = 2
        feedback.append("Clear problem articulation")
    elif sections['problem']:
        scores['problem_focus'] = 1
        feedback.append("Problem stated but needs more detail")
    else:
        feedback.append("Problem not clearly defined")
    
    # 2. Credible Approach
    if sections['solution'] and len(sections['solution']) > 50:
        scores['credible_approach'] = 2
        feedback.append("Solution well-defined")
    elif sections['solution']:
        scores['credible_approach'] = 1
        feedback.append("Solution needs more specifics")
    else:
        feedback.append("Solution unclear")
    
    # 3. Domain Expertise
    if sections['domain_experts']:
        scores['domain_expertise'] = 2
        feedback.append("Domain experts identified")
    else:
        scores['domain_expertise'] = 0
        feedback.append("No domain experts mentioned")
    
    # 4. Co-funding (simplified assessment)
    if 'funding' in content.lower() or 'grant' in content.lower():
        scores['co_funding'] = 1
        feedback.append("Funding mentioned but details unclear")
    
    # 5. Capital Method
    if 'hypercert' in content.lower() or 'retroactive' in content.lower():
        scores['capital_method'] = 2
        feedback.append("Innovative funding mechanism proposed")
    elif 'grant' in content.lower():
        scores['capital_method'] = 1
        feedback.append("Traditional grant approach")
    
    # 6. Clarity
    if sections['tldr'] and len(sections['tldr']) > 30:
        scores['clarity'] = 2
        feedback.append("Clear TLDR provided")
    elif sections['tldr']:
        scores['clarity'] = 1
        feedback.append("TLDR needs improvement")
    else:
        feedback.append("Missing TLDR")
    
    # 7. Execution Readiness
    if 'october' in content.lower() or 'immediate' in content.lower():
        scores['execution_readiness'] = 2
        feedback.append("Ready for immediate execution")
    elif 'pilot' in content.lower() or 'mvp' in content.lower():
        scores['execution_readiness'] = 1
        feedback.append("Pilot phase")
    
    # 8. Vibe check
    if len(title) > 20 and sections['tldr']:
        scores['vibe_check'] = 1
        feedback.append("Decent overall presentation")
    
    total_score = sum(scores.values())
    
    return scores, total_score, feedback

def format_markdown_entry(row, sections, scores, total_score, feedback):
    """Format a single entry in markdown"""
    title = row['Title']
    link = row['Link']
    author = row['Submitted By']
    
    # Determine deployment strategy details
    domain_type = "Community & Events" if "popup" in title.lower() else "Tech Infrastructure"
    size = "Medium" 
    timeline = "3-6 months"
    approach = "Community-driven" if "popup" in title.lower() else "Technical"
    funding_type = "Retroactive" if "hypercert" in sections['solution'].lower() else "Proactive"
    capital = "$50K-$200K"
    mechanism = "Hypercerts" if "hypercert" in sections['solution'].lower() else "Direct grants"
    
    md = f"""
# [{title}]({link})

by {author}

### TLDR

{sections['tldr'] if sections['tldr'] else 'Impact-driven funding for Ethereum ecosystem development.'}

### Problem

{sections['problem'] if sections['problem'] else 'Need for better coordination and funding mechanisms.'}

### Solution

{sections['solution'] if sections['solution'] else 'Implement transparent funding and evaluation systems.'}

### Domain Experts

{sections['domain_experts'] if sections['domain_experts'] else 'Community leaders and technical experts'}

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

{sections['risks'] if sections['risks'] else 'Execution and coordination challenges'}

## Outside Funding

{sections['funding'] if sections['funding'] else 'Seeking co-funding opportunities'}

## Owockis scorecard

|#|Criterion|0|1|2|Notes|
| --- | --- | --- | --- | --- | --- |
|1|Problem Focus – Clearly frames a real problem, (one that is a priority), avoids "solutionism"|{"" if scores['problem_focus'] == 0 else " "}|{"X" if scores['problem_focus'] == 1 else " "}|{"X" if scores['problem_focus'] == 2 else " "}||
|2|Credible, High leverage, Evidence-Based Approach – Solutions are high-leverage and grounded in credible research|{"" if scores['credible_approach'] == 0 else " "}|{"X" if scores['credible_approach'] == 1 else " "}|{"X" if scores['credible_approach'] == 2 else " "}||
|3|Domain Expertise – Proposal has active involvement from recognized experts|{"" if scores['domain_expertise'] == 0 else " "}|{"X" if scores['domain_expertise'] == 1 else " "}|{"X" if scores['domain_expertise'] == 2 else " "}||
|4|Co-Funding – Has financial backing beyond just Gitcoin|{"" if scores['co_funding'] == 0 else " "}|{"X" if scores['co_funding'] == 1 else " "}|{"X" if scores['co_funding'] == 2 else " "}||
|5|Fit-for-Purpose Capital Allocation Method – Methodology matches the epistemology of the domain|{"" if scores['capital_method'] == 0 else " "}|{"X" if scores['capital_method'] == 1 else " "}|{"X" if scores['capital_method'] == 2 else " "}||
|6|Clarity (TL;DR) – Includes a concise summary at the top|{"" if scores['clarity'] == 0 else " "}|{"X" if scores['clarity'] == 1 else " "}|{"X" if scores['clarity'] == 2 else " "}||
|7|Execution Readiness – Can deliver meaningful results by October|{"" if scores['execution_readiness'] == 0 else " "}|{"X" if scores['execution_readiness'] == 1 else " "}|{"X" if scores['execution_readiness'] == 2 else " "}||
|8|Other - general vibe check and other stuff I may have missed above..|{"" if scores['vibe_check'] == 0 else " "}|{"X" if scores['vibe_check'] == 1 else " "}|{"X" if scores['vibe_check'] == 2 else " "}||

### Score

Total Score: {total_score} / 16

### Feedback:

"""
    
    for i, point in enumerate(feedback[:10], 1):
        md += f"- {point}\n"
    
    return md

# Main processing
if __name__ == "__main__":
    # Read CSV data
    csv_data = []
    with open('/Users/owocki/Sites/gg24/data/data.csv', 'r') as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)
    
    # Process specified posts or first 3
    if len(sys.argv) > 1:
        post_ids = sys.argv[1:]
    else:
        # First 3 posts
        post_ids = ['23054', '23024', '23049']
    
    markdown_content = ""
    
    for post_id in post_ids:
        filepath = f'/Users/owocki/Sites/gg24/posts/{post_id}.html'
        
        # Find matching CSV row
        matching_row = None
        for row in csv_data:
            if post_id in row['Link']:
                matching_row = row
                break
        
        if not matching_row:
            continue
        
        title, content = extract_full_content(filepath)
        sections = parse_content_sections(content)
        scores, total_score, feedback = score_proposal(sections, title, content)
        
        entry = format_markdown_entry(matching_row, sections, scores, total_score, feedback)
        markdown_content += entry + "\n\n"
    
    print(markdown_content)