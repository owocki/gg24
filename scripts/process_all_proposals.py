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
    
    # Extract title using regex
    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', content)
    title = html_module.unescape(title_match.group(1)) if title_match else ""
    
    # Extract main content using regex
    # Try to find the cooked div first
    cooked_match = re.search(r'<div class="cooked"[^>]*>(.*?)</div>\s*(?:<div|<footer|<script|</article)', content, re.DOTALL)
    if not cooked_match:
        # Try alternative patterns
        cooked_match = re.search(r'<div[^>]*itemprop="text"[^>]*>(.*?)</div>\s*(?:<div|<footer|<script)', content, re.DOTALL)
    
    if cooked_match:
        text = cooked_match.group(1)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Unescape HTML entities
        text = html_module.unescape(text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return title, text[:8000]
    
    # Fallback: try to extract any text content
    meta_desc = re.search(r'<meta property="og:description" content="([^"]+)"', content)
    if meta_desc:
        text = html_module.unescape(meta_desc.group(1))
        return title, text
    
    return title, ""

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
        'funding': '',
        'external_funders': ''
    }
    
    content_lower = content.lower()
    
    # Extract TLDR
    tldr_patterns = [
        r'(?:tldr|tl;dr|summary|executive summary)[:\s]+(.*?)(?:\n\n|problem|challenge|background|$)',
        r'(?:in short|briefly|overview)[:\s]+(.*?)(?:\n\n|problem|challenge|$)',
    ]
    for pattern in tldr_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            tldr = match.group(1).strip()
            tldr = re.sub(r'\s+', ' ', tldr)
            sections['tldr'] = tldr[:300]
            break
    
    if not sections['tldr'] and content:
        # Take first substantial paragraph
        paragraphs = re.split(r'\n\n+', content)
        for para in paragraphs[:3]:
            if len(para) > 50:
                sections['tldr'] = para.strip()[:300]
                break
    
    # Extract Problem
    prob_patterns = [
        r'(?:problem statement|the problem|problem)[:\s]+(.*?)(?:solution|approach|proposal|methodology|$)',
        r'(?:challenge|issue|pain point)[:\s]+(.*?)(?:solution|approach|$)',
        r'(?:what.{0,10}problem|addressing)[:\s]+(.*?)(?:solution|how|$)',
    ]
    for pattern in prob_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            prob = match.group(1).strip()
            prob = re.sub(r'\s+', ' ', prob)
            sections['problem'] = prob[:400]
            break
    
    # Extract Solution
    sol_patterns = [
        r'(?:solution|approach|proposal|methodology)[:\s]+(.*?)(?:impact|outcome|implementation|timeline|$)',
        r'(?:we propose|our solution|we will)[:\s]+(.*?)(?:impact|this will|expected|$)',
        r'(?:how we.{0,10}solve|our approach)[:\s]+(.*?)(?:impact|outcome|$)',
    ]
    for pattern in sol_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            sol = match.group(1).strip()
            sol = re.sub(r'\s+', ' ', sol)
            sections['solution'] = sol[:400]
            break
    
    # Extract domain experts and credentials
    expert_patterns = [
        r'(?:domain expert|expert|team|contributor|advisor)[:\s]+(.*?)(?:\n\n|impact|$)',
        r'(?:led by|managed by|coordinated by)[:\s]+(.*?)(?:\n|$)',
    ]
    experts = []
    for pattern in expert_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            expert_text = match.group(1).strip()[:200]
            if expert_text:
                experts.append(expert_text)
    
    # Also look for @ mentions
    mentions = re.findall(r'@[\w-]+', content)
    if mentions:
        experts.extend(mentions[:5])
    
    if experts:
        sections['domain_experts'] = '\n'.join(set(experts[:3]))
    
    # Extract target projects
    proj_patterns = [
        r'(?:target project|example project|pilot|use case)[:\s]+(.*?)(?:\n\n|impact|$)',
        r'(?:project example|implementation example)[:\s]+(.*?)(?:\n\n|$)',
    ]
    projects = []
    for pattern in proj_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            proj = match.group(1).strip()
            proj = re.sub(r'\s+', ' ', proj)[:200]
            if proj:
                projects.append(proj)
    
    if projects:
        sections['target_projects'] = '\n'.join(projects[:3])
    
    # Determine impact areas
    impact_keywords = {
        'AI/ML': ['ai', 'artificial intelligence', 'machine learning', 'llm', 'neural', 'model training'],
        'DeFi': ['defi', 'decentralized finance', 'liquidity', 'trading', 'amm', 'dex', 'lending'],
        'Governance': ['governance', 'voting', 'dao', 'paradox', 'consensus', 'coordination'],
        'Infrastructure': ['infrastructure', 'tooling', 'developer', 'sdk', 'api', 'core', 'protocol'],
        'Privacy': ['privacy', 'kyc', 'zero knowledge', 'zk', 'maci', 'anonymous', 'confidential'],
        'Science': ['desci', 'science', 'research', 'academic', 'peer review', 'publication'],
        'Community': ['popup', 'residency', 'community', 'events', 'irl', 'meetup', 'conference'],
        'Funding': ['funding', 'grant', 'pgf', 'hypercert', 'retroactive', 'quadratic', 'allocation'],
        'Data': ['data', 'analytics', 'information', 'infofi', 'metrics', 'transparency'],
        'Adoption': ['adoption', 'ux', 'user experience', 'consumer', 'mass', 'onboarding', 'mainstream'],
        'Enterprise': ['enterprise', 'business', 'b2b', 'corporate', 'institutional'],
        'Localism': ['local', 'regen', 'regional', 'community', 'grassroots']
    }
    
    found_areas = []
    for area, keywords in impact_keywords.items():
        if any(kw in content_lower for kw in keywords):
            found_areas.append(area)
    
    sections['impact_areas'] = ', '.join(found_areas[:3]) if found_areas else 'General'
    
    # Extract risks
    risk_patterns = [
        r'(?:risk|challenge|concern|limitation)[:\s]+(.*?)(?:mitigation|conclusion|timeline|$)',
        r'(?:potential issue|obstacle)[:\s]+(.*?)(?:mitigation|solution|$)',
    ]
    risks = []
    for pattern in risk_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            risk = match.group(1).strip()
            risk = re.sub(r'\s+', ' ', risk)[:200]
            if risk:
                risks.append(risk)
    
    if risks:
        sections['risks'] = '\n'.join(risks[:2])
    
    # Extract funding info
    fund_patterns = [
        r'(?:funding ask|budget|request|allocation)[:\s]+(.*?)(?:\n\n|timeline|$)',
        r'(?:grant amount|funding needed)[:\s]+(.*?)(?:\n|$)',
        r'\$[\d,]+[kKmM]?(?:\s+(?:USD|usd))?',
    ]
    
    funding_info = []
    for pattern in fund_patterns[:2]:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            fund = match.group(1).strip()[:200]
            funding_info.append(fund)
    
    # Also look for dollar amounts
    dollar_matches = re.findall(r'\$[\d,]+[kKmM]?(?:\s+(?:USD|usd))?', content)
    if dollar_matches:
        funding_info.extend(dollar_matches[:3])
    
    if funding_info:
        sections['funding'] = ' '.join(funding_info[:2])
    
    # Extract external funders
    funder_patterns = [
        r'(?:partner|co-fund|match|external fund|secured from)[:\s]+(.*?)(?:\n|$)',
        r'(?:backed by|supported by|funded by)[:\s]+(.*?)(?:\n|$)',
    ]
    funders = []
    for pattern in funder_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            funder = match.group(1).strip()[:100]
            if funder:
                funders.append(funder)
    
    if funders:
        sections['external_funders'] = ', '.join(funders[:2])
    
    return sections

def score_proposal_owocki_style(sections, title, content):
    """Score the proposal in Kevin Owocki's voice and style with detailed explanations"""
    scores = {}
    explanations = {}
    feedback = []
    content_lower = content.lower()
    
    # 1. Problem Focus - Does it clearly frame a real, priority problem?
    if sections['problem']:
        problem_lower = sections['problem'].lower()
        if any(word in problem_lower for word in ['critical', 'urgent', 'fundamental', 'bottleneck', 'broken', 'failing']):
            if len(sections['problem']) > 100:
                scores['problem_focus'] = 2
                explanations['problem_focus'] = "Clearly articulates a critical problem that needs solving"
                feedback.append("Strong problem definition that resonates")
            else:
                scores['problem_focus'] = 1
                explanations['problem_focus'] = "Problem mentioned but needs more depth"
                feedback.append("Problem needs more context and urgency")
        elif len(sections['problem']) > 50:
            scores['problem_focus'] = 1
            explanations['problem_focus'] = "Problem exists but doesn't feel urgent or well-defined"
            feedback.append("Problem lacks urgency - why solve this NOW?")
        else:
            scores['problem_focus'] = 0
            explanations['problem_focus'] = "Problem statement is weak or missing"
            feedback.append("Need clearer problem statement - what's actually broken?")
    else:
        scores['problem_focus'] = 0
        explanations['problem_focus'] = "No clear problem identified - seems like a solution looking for a problem"
        feedback.append("Missing problem statement - classic solutionism")
    
    # 2. Credible, Evidence-Based Approach
    evidence_words = ['proven', 'evidence', 'research', 'data', 'tested', 'pilot', 'study', 'analysis', 'benchmark', 'metric']
    evidence_count = sum(1 for word in evidence_words if word in content_lower)
    
    if sections['solution']:
        if evidence_count >= 3:
            scores['credible_approach'] = 2
            explanations['credible_approach'] = "Strong evidence-based approach with research backing"
            feedback.append("Love the data-driven approach")
        elif evidence_count >= 1:
            scores['credible_approach'] = 1
            explanations['credible_approach'] = "Some evidence but needs more validation"
            feedback.append("Add more evidence/data to support approach")
        else:
            scores['credible_approach'] = 0
            explanations['credible_approach'] = "Lacks evidence or research backing"
            feedback.append("Where's the evidence this will work?")
    else:
        scores['credible_approach'] = 0
        explanations['credible_approach'] = "No clear solution approach defined"
        feedback.append("Solution approach needs definition")
    
    # 3. Domain Expertise
    if sections['domain_experts']:
        expert_indicators = ['founder', 'ceo', 'phd', 'researcher', 'expert', 'lead', 'director', 'years']
        has_credentials = any(ind in sections['domain_experts'].lower() for ind in expert_indicators)
        expert_count = len(sections['domain_experts'].split('\n'))
        
        if expert_count >= 2 and has_credentials:
            scores['domain_expertise'] = 2
            explanations['domain_expertise'] = "Strong team with proven domain expertise"
            feedback.append("Solid team with right expertise")
        elif expert_count >= 1 or '@' in sections['domain_experts']:
            scores['domain_expertise'] = 1
            explanations['domain_expertise'] = "Some expertise but team needs strengthening"
            feedback.append("Consider adding more domain experts")
        else:
            scores['domain_expertise'] = 0
            explanations['domain_expertise'] = "Limited domain expertise shown"
            feedback.append("Who are the experts backing this?")
    else:
        scores['domain_expertise'] = 0
        explanations['domain_expertise'] = "No domain experts identified"
        feedback.append("Need proven experts on the team")
    
    # 4. Co-Funding
    funding_indicators = ['secured', 'committed', 'partnered', 'matched', 'raised', 'funded', 'backing']
    has_cofunding = any(word in content_lower for word in funding_indicators)
    
    if sections['external_funders'] or has_cofunding:
        if '$' in sections.get('external_funders', '') or 'secured' in content_lower:
            scores['co_funding'] = 2
            explanations['co_funding'] = "Has secured external funding/partners"
            feedback.append("Good to see external validation via funding")
        else:
            scores['co_funding'] = 1
            explanations['co_funding'] = "Some funding interest but not secured"
            feedback.append("Lock in that co-funding commitment")
    elif 'seeking' in content_lower or 'looking for' in content_lower:
        scores['co_funding'] = 1
        explanations['co_funding'] = "Actively seeking co-funding but none secured"
        feedback.append("Need to secure co-funding for credibility")
    else:
        scores['co_funding'] = 0
        explanations['co_funding'] = "No co-funding mentioned - all on Gitcoin?"
        feedback.append("Where's the skin in the game from others?")
    
    # 5. Fit-for-Purpose Capital Allocation Method
    innovative_mechanisms = ['hypercert', 'retroactive', 'outcome', 'impact cert', 'maci', 'quadratic', 'conviction']
    standard_mechanisms = ['milestone', 'tranch', 'kpi', 'deliverable']
    
    mechanism_score = sum(1 for mech in innovative_mechanisms if mech in content_lower)
    
    if mechanism_score >= 2:
        scores['capital_method'] = 2
        explanations['capital_method'] = "Innovative funding mechanism that aligns incentives well"
        feedback.append("Interesting funding mechanism design")
    elif mechanism_score >= 1 or any(mech in content_lower for mech in standard_mechanisms):
        scores['capital_method'] = 1
        explanations['capital_method'] = "Standard milestone-based approach"
        feedback.append("Consider more innovative funding mechanisms")
    else:
        scores['capital_method'] = 0
        explanations['capital_method'] = "Traditional grant approach - no innovation in capital allocation"
        feedback.append("Funding method feels too traditional")
    
    # 6. Clarity (TL;DR)
    if sections['tldr']:
        tldr_length = len(sections['tldr'])
        if 50 <= tldr_length <= 200:
            scores['clarity'] = 2
            explanations['clarity'] = "Crystal clear and concise TLDR"
            feedback.append("Great TLDR - immediately got it")
        elif tldr_length > 200:
            scores['clarity'] = 1
            explanations['clarity'] = "TLDR exists but too verbose"
            feedback.append("TLDR needs to be more concise")
        else:
            scores['clarity'] = 1
            explanations['clarity'] = "TLDR too brief to be useful"
            feedback.append("TLDR needs more substance")
    else:
        scores['clarity'] = 0
        explanations['clarity'] = "Missing clear TLDR - hard to grasp quickly"
        feedback.append("Add a clear TLDR at the top")
    
    # 7. Execution Readiness
    readiness_indicators = ['immediately', 'ready', 'launched', 'active', 'live', 'deployed', 'running']
    pilot_indicators = ['pilot', 'mvp', 'prototype', 'beta', 'testing', 'alpha']
    
    if any(word in content_lower for word in readiness_indicators):
        scores['execution_readiness'] = 2
        explanations['execution_readiness'] = "Ready to ship now - can deliver by October"
        feedback.append("Love that this is ready to go")
    elif any(word in content_lower for word in pilot_indicators):
        scores['execution_readiness'] = 1
        explanations['execution_readiness'] = "In pilot/testing phase - might deliver by October"
        feedback.append("Push to get to production ASAP")
    else:
        scores['execution_readiness'] = 0
        explanations['execution_readiness'] = "Early stage - unlikely to deliver meaningful results by October"
        feedback.append("Timeline seems unrealistic for October delivery")
    
    # 8. Vibe check - general feel and alignment
    positive_vibes = [
        'community' in content_lower,
        'open source' in content_lower,
        'public good' in content_lower,
        'ethereum' in content_lower,
        'decentralized' in content_lower,
        'transparent' in content_lower,
        'collaborative' in content_lower,
        bool(sections['tldr']),
        bool(sections['problem']),
        bool(sections['solution'])
    ]
    vibe_score = sum(positive_vibes)
    
    if vibe_score >= 7:
        scores['vibe_check'] = 2
        explanations['vibe_check'] = "Great energy, fully aligned with Ethereum values"
        feedback.append("This feels right - good Ethereum vibes")
    elif vibe_score >= 4:
        scores['vibe_check'] = 1
        explanations['vibe_check'] = "Decent alignment but could be stronger"
        feedback.append("Alignment is okay but could be stronger")
    else:
        scores['vibe_check'] = 0
        explanations['vibe_check'] = "Doesn't feel aligned with public goods ethos"
        feedback.append("Missing that public goods energy")
    
    # Add more specific contextual feedback
    if 'ethereum' in content_lower:
        feedback.append("Good Ethereum alignment")
    if 'retroactive' in content_lower:
        feedback.append("Like the retroactive funding angle")
    if not sections['target_projects']:
        feedback.append("Need concrete examples of target projects")
    if 'impact' in content_lower and 'measure' in content_lower:
        feedback.append("Good focus on measurable impact")
    
    total_score = sum(scores.values())
    
    # Calculate confidence
    confidence = 50  # Base
    if sections['tldr']: confidence += 10
    if sections['problem']: confidence += 10
    if sections['solution']: confidence += 10
    if sections['domain_experts']: confidence += 5
    if sections['funding']: confidence += 5
    if len(content) > 1000: confidence += 10
    confidence = min(confidence, 90)
    
    return scores, explanations, total_score, feedback[:10], confidence

def generate_steel_man_cases(sections, title, content, total_score):
    """Generate steel man cases for and against the proposal"""
    content_lower = content.lower()
    
    # Steel man FOR
    for_points = []
    
    if sections['problem'] and len(sections['problem']) > 50:
        for_points.append("Addresses a real and documented problem in the ecosystem")
    
    if sections['domain_experts']:
        for_points.append("Has domain experts who understand the space")
    
    if 'community' in content_lower or 'open source' in content_lower:
        for_points.append("Aligned with community values and open source ethos")
    
    if sections['solution'] and ('evidence' in content_lower or 'proven' in content_lower):
        for_points.append("Solution has evidence or prior validation")
    
    if 'ethereum' in content_lower:
        for_points.append("Directly supports Ethereum ecosystem growth")
    
    if sections['external_funders'] or 'secured' in content_lower:
        for_points.append("Has external validation through co-funding")
    
    steel_man_for = ". ".join(for_points[:3]) if for_points else "Has potential to create value in the ecosystem"
    
    # Steel man AGAINST
    against_points = []
    
    if not sections['domain_experts']:
        against_points.append("Team lacks proven domain expertise")
    
    if not sections['external_funders'] and 'secured' not in content_lower:
        against_points.append("No external funding validates market need")
    
    if total_score < 8:
        against_points.append("Multiple weak areas suggest execution risk")
    
    if not sections['tldr'] or len(sections['tldr']) < 50:
        against_points.append("Lack of clarity suggests incomplete thinking")
    
    if 'immediately' not in content_lower and 'ready' not in content_lower:
        against_points.append("Not ready to deliver results in near term")
    
    if not sections['risks']:
        against_points.append("Hasn't thoughtfully considered risks")
    
    steel_man_against = ". ".join(against_points[:3]) if against_points else "Execution risks may prevent achieving stated goals"
    
    return steel_man_for, steel_man_against

def determine_deployment_strategy(sections, content):
    """Determine deployment strategy details"""
    content_lower = content.lower()
    
    # Domain type
    domain_mappings = {
        'AI': ['ai', 'ml', 'machine learning', 'artificial intelligence', 'llm'],
        'DeFi': ['defi', 'amm', 'dex', 'liquidity', 'trading'],
        'Governance': ['governance', 'dao', 'voting', 'coordination'],
        'Events': ['popup', 'residency', 'conference', 'meetup', 'irl'],
        'Dev Tools': ['tooling', 'developer', 'sdk', 'api', 'infrastructure'],
        'Privacy': ['privacy', 'zk', 'zero knowledge', 'kyc', 'maci'],
        'DeSci': ['science', 'desci', 'research', 'academic'],
        'Data': ['data', 'analytics', 'transparency', 'infofi'],
        'Adoption': ['adoption', 'ux', 'consumer', 'mass', 'onboarding'],
        'Enterprise': ['enterprise', 'b2b', 'institutional'],
        'Funding': ['funding', 'grant', 'pgf', 'hypercert']
    }
    
    domain_type = "General"
    for domain, keywords in domain_mappings.items():
        if any(kw in content_lower for kw in keywords):
            domain_type = domain
            break
    
    # Size assessment
    if any(word in content_lower for word in ['ecosystem', 'large scale', 'global', 'widespread']):
        size = "Large scale initiative"
    elif any(word in content_lower for word in ['pilot', 'mvp', 'experiment', 'small']):
        size = "Small pilot/experiment"
    else:
        size = "Medium scope project"
    
    # Timeline
    if any(word in content_lower for word in ['immediate', 'ready now', 'already']):
        timeline = "Ready now (1-3 months)"
    elif any(word in content_lower for word in ['year', 'long term', '2025', '2026']):
        timeline = "Long term (12+ months)"
    else:
        timeline = "Medium term (3-6 months)"
    
    # Approach
    if any(word in content_lower for word in ['community', 'democratic', 'participatory', 'bottom-up']):
        approach = "Democratic/Community-driven"
    else:
        approach = "Technocratic/Expert-led"
    
    # Funding type
    if any(word in content_lower for word in ['retroactive', 'retro', 'outcome']):
        funding_type = "Retroactive funding"
    else:
        funding_type = "Proactive funding"
    
    # Capital needed
    amounts = re.findall(r'\$?([\d,]+)[kKmM]', content)
    if amounts:
        amount_str = amounts[0].replace(',', '')
        if 'M' in content or 'm' in content:
            capital = f"${amount_str}M+"
        elif 'K' in content or 'k' in content:
            capital = f"${amount_str}K"
        else:
            capital = "Amount specified"
    else:
        if 'million' in content_lower:
            capital = "$1M+"
        elif 'hundred thousand' in content_lower:
            capital = "$100K-500K"
        else:
            capital = "$50K-100K (estimated)"
    
    # Mechanism
    if 'hypercert' in content_lower:
        mechanism = "Hypercerts"
    elif 'quadratic' in content_lower:
        mechanism = "Quadratic Funding"
    elif 'retroactive' in content_lower:
        mechanism = "Retroactive PGF"
    elif 'maci' in content_lower:
        mechanism = "MACI"
    elif 'milestone' in content_lower:
        mechanism = "Milestone-based"
    else:
        mechanism = "Direct grants"
    
    return domain_type, size, timeline, approach, funding_type, capital, mechanism

def format_markdown_entry(row, sections, scores, explanations, total_score, confidence, feedback, steel_for, steel_against, deployment):
    """Format a single entry in markdown with all required fields"""
    title = row['Title']
    link = row['Link']
    author = row['Submitted By']
    
    domain_type, size, timeline, approach, funding_type, capital, mechanism = deployment
    
    md = f"""# [{title}]({link})

by {author}

## Proposal

### TLDR

{sections['tldr'] if sections['tldr'] else 'No clear summary provided'}

### Problem

{sections['problem'] if sections['problem'] else 'Problem statement not clearly articulated'}

### Solution

{sections['solution'] if sections['solution'] else 'Solution approach not well defined'}

### Domain Experts

{sections['domain_experts'] if sections['domain_experts'] else 'No domain experts identified'}

### Target Projects (Examples)

{sections['target_projects'] if sections['target_projects'] else 'No specific target projects mentioned'}

### Deployment strategy

Domain: {domain_type}
Scale: {size}
Timeline: {timeline}
Approach: {approach}
Funding Type: {funding_type}
Capital Needed: {capital}
Mechanism: {mechanism}

### Risks

{sections['risks'] if sections['risks'] else 'Risks not explicitly addressed'}

## Outside Funding

{sections['external_funders'] if sections['external_funders'] else sections['funding'] if sections['funding'] else 'No external funding mentioned'}

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
    """Generate Owocki-style high level feedback"""
    if total_score >= 14:
        return "This is the way. Ship it yesterday."
    elif total_score >= 12:
        return "Strong proposal, ready to fund with minor tweaks"
    elif total_score >= 10:
        return "Solid foundation, needs some work on execution details"
    elif total_score >= 8:
        return "Has potential but needs significant refinement"
    elif total_score >= 6:
        return "Interesting idea but not ready for funding"
    elif total_score >= 4:
        return "Needs major rework before consideration"
    else:
        return "Back to the drawing board"

def generate_rose_thorn_bud(sections, total_score, content):
    """Generate rose, thorn, bud feedback with more thoughtful analysis"""
    content_lower = content.lower()
    
    # Rose (what's good)
    roses = []
    if sections['tldr'] and len(sections['tldr']) > 50:
        roses.append("Clear vision and communication")
    if sections['domain_experts']:
        roses.append("Strong team with expertise")
    if 'ethereum' in content_lower:
        roses.append("Aligned with Ethereum values")
    if 'community' in content_lower:
        roses.append("Community-focused approach")
    if sections['problem'] and len(sections['problem']) > 100:
        roses.append("Well-defined problem statement")
    
    rose = roses[0] if roses else "Has foundational elements"
    
    # Thorn (what needs improvement)
    thorns = []
    if not sections['domain_experts']:
        thorns.append("Needs proven experts on team")
    if not sections['external_funders'] and not sections['funding']:
        thorns.append("Lacks funding clarity/commitment")
    if not sections['risks']:
        thorns.append("Hasn't addressed risks")
    if total_score < 8:
        thorns.append("Multiple areas need strengthening")
    if not sections['target_projects']:
        thorns.append("Missing concrete examples")
    
    thorn = thorns[0] if thorns else "Execution details need work"
    
    # Bud (what could grow)
    buds = []
    if 'pilot' in content_lower or 'mvp' in content_lower:
        buds.append("Pilot could scale if successful")
    if 'retroactive' in content_lower or 'hypercert' in content_lower:
        buds.append("Novel funding model could set precedent")
    if total_score >= 10:
        buds.append("Strong potential for ecosystem impact")
    elif total_score >= 6:
        buds.append("Could evolve into fundable proposal")
    else:
        buds.append("Seeds of good idea need nurturing")
    
    bud = buds[0] if buds else "Potential for growth with iteration"
    
    return rose, thorn, bud

# Main processing
if __name__ == "__main__":
    # Read CSV data
    csv_data = []
    with open('/Users/owocki/Sites/gg24/data/data.csv', 'r') as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)
    
    # Remove duplicates based on Link
    seen_links = set()
    unique_data = []
    for row in csv_data:
        if row['Link'] not in seen_links:
            seen_links.add(row['Link'])
            unique_data.append(row)
    
    print(f"Processing {len(unique_data)} unique proposals...")
    
    entries = []
    leaderboard_data = []
    
    for i, row in enumerate(unique_data, 1):
        print(f"Processing {i}/{len(unique_data)}: {row['Title']}")
        
        # Extract post ID from URL
        link = row['Link']
        # Get the last part of the URL path
        parts = link.rstrip('/').split('/')
        post_id = parts[-1].split('-')[-1] if parts else ""
        
        # Try to find the HTML file
        filepath = f'/Users/owocki/Sites/gg24/posts/{post_id}.html'
        if not os.path.exists(filepath):
            # Try without extracting ID
            filepath = f'/Users/owocki/Sites/gg24/posts/{post_id}.html'
        
        title, content = extract_full_content(filepath)
        if not title:
            title = row['Title']
        
        if not content:
            print(f"  Warning: No content found for {title}")
            content = f"{title}. {row.get('Description', '')}"
        
        sections = parse_content_sections(content, title)
        scores, explanations, total_score, feedback, confidence = score_proposal_owocki_style(sections, title, content)
        steel_for, steel_against = generate_steel_man_cases(sections, title, content, total_score)
        deployment = determine_deployment_strategy(sections, content)
        
        entry_md, score = format_markdown_entry(row, sections, scores, explanations, total_score, confidence, feedback, steel_for, steel_against, deployment)
        entries.append((score, entry_md, row['Title'], row['Link'], row['Submitted By']))
        
        # Generate leaderboard data
        high_level_feedback = generate_owocki_feedback(title, sections, total_score)
        rose, thorn, bud = generate_rose_thorn_bud(sections, total_score, content)
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

(vibe-written by claude code using [this prompt](https://github.com/owocki/gg24/blob/main/prompt.txt), iterated on, + edited for accuracy quality and legibility by owocki himself.)

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
        entry_md_with_rating = entry_md.replace(f"# [{title}]({link})", f"# ({score}/16) [{title}]({link})")
        output += entry_md_with_rating + "\n\n---\n\n"
    
    # Write to file
    with open('/Users/owocki/Sites/gg24/data/data.md', 'w') as f:
        f.write(output)
    
    print(f"\nSuccessfully created data.md with {len(entries)} proposals processed")
    print(f"Top 3 proposals by score:")
    for i, item in enumerate(leaderboard_data[:3], 1):
        print(f"  {i}. {item['score']}/16 - {item['title']}")