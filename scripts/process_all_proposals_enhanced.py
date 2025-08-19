#!/usr/bin/env python3
import re
import html as html_module
import csv
import sys
import os
from datetime import datetime
import random

def extract_full_content(filepath):
    """Extract full content from HTML file including body text"""
    if not os.path.exists(filepath):
        print(f"Warning: File not found: {filepath}")
        return "", ""
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Extract title using regex
    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', content)
    title = html_module.unescape(title_match.group(1)) if title_match else ""
    
    # Extract meta description
    meta_match = re.search(r'<meta property="og:description" content="([^"]+)"', content)
    meta_content = html_module.unescape(meta_match.group(1)) if meta_match else ""
    
    # Extract body content using regex
    body_content = ""
    
    # Try to find the main content area
    body_match = re.search(r'<div class="cooked"[^>]*>(.*?)</div>', content, re.DOTALL)
    if not body_match:
        body_match = re.search(r'<div[^>]*itemprop="text"[^>]*>(.*?)</div>', content, re.DOTALL)
    if not body_match:
        body_match = re.search(r'<article[^>]*>(.*?)</article>', content, re.DOTALL)
    
    if body_match:
        body_content = body_match.group(1)
        # Remove HTML tags
        body_content = re.sub(r'<script[^>]*>.*?</script>', '', body_content, flags=re.DOTALL)
        body_content = re.sub(r'<style[^>]*>.*?</style>', '', body_content, flags=re.DOTALL)
        body_content = re.sub(r'<[^>]+>', ' ', body_content)
        body_content = html_module.unescape(body_content)
        body_content = re.sub(r'\s+', ' ', body_content).strip()
    
    # Combine meta and body content
    full_content = meta_content + " " + body_content
    
    return title, full_content

def parse_content_sections(content, title):
    """Parse content into detailed sections"""
    sections = {
        'tldr': '',
        'problem': '',
        'solution': '',
        'domain_experts': '',
        'target_projects': '',
        'impact_areas': '',
        'risks': '',
        'funding': '',
        'deployment': '',
        'credentials': ''
    }
    
    content_lower = content.lower()
    
    # Extract TLDR with multiple patterns
    tldr_patterns = [
        r'(?:tldr|tl;dr|summary|abstract|overview)[:\s]*([^.!?]*[.!?])',
        r'(?:in short|briefly|quick summary)[:\s]*([^.!?]*[.!?])',
        r'(?:executive summary)[:\s]*([^.!?]*[.!?])',
    ]
    
    for pattern in tldr_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            sections['tldr'] = match.group(1).strip()[:200]
            break
    
    if not sections['tldr'] and content:
        # Take first meaningful sentence
        sentences = re.split(r'[.!?]', content)
        for sent in sentences[:3]:
            if len(sent.strip()) > 30:
                sections['tldr'] = sent.strip()[:200]
                break
    
    # Extract Problem
    prob_patterns = [
        r'(?:problem|challenge|issue|pain point)[:\s]*([^.]*(?:\.[^.]*){0,2}\.)',
        r'(?:current state|status quo)[:\s]*([^.]*(?:\.[^.]*){0,2}\.)',
        r'(?:gap|bottleneck|limitation)[:\s]*([^.]*(?:\.[^.]*){0,2}\.)',
    ]
    
    for pattern in prob_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            sections['problem'] = match.group(1).strip()[:300]
            break
    
    # Extract Solution
    sol_patterns = [
        r'(?:solution|approach|proposal|methodology)[:\s]*([^.]*(?:\.[^.]*){0,2}\.)',
        r'(?:we propose|our approach|we will)[:\s]*([^.]*(?:\.[^.]*){0,2}\.)',
        r'(?:implementation|strategy)[:\s]*([^.]*(?:\.[^.]*){0,2}\.)',
    ]
    
    for pattern in sol_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            sections['solution'] = match.group(1).strip()[:300]
            break
    
    # Extract domain experts and credentials
    expert_patterns = [
        r'(?:team|expert|advisor|contributor)[:\s]*([^.]*(?:\.[^.]*){0,2}\.)',
        r'(?:led by|managed by|coordinated by)[:\s]*([^.]*\.)',
        r'(?:credentials|experience|background)[:\s]*([^.]*(?:\.[^.]*){0,2}\.)',
    ]
    
    experts = []
    credentials = []
    
    # Find @mentions
    mentions = re.findall(r'@[\w-]+', content)
    if mentions:
        experts.extend(mentions[:5])
    
    for pattern in expert_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            text = match.group(1)
            if 'year' in text.lower() or 'experience' in text.lower() or 'phd' in text.lower():
                credentials.append(text.strip()[:100])
            else:
                # Extract names
                name_matches = re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+', text)
                experts.extend(name_matches)
    
    sections['domain_experts'] = ', '.join(list(set(experts))[:5]) if experts else ''
    sections['credentials'] = ' | '.join(credentials[:3]) if credentials else ''
    
    # Extract target projects
    project_patterns = [
        r'(?:example project|target project|use case)[:\s]*([^.]*(?:\.[^.]*){0,1}\.)',
        r'(?:pilot|implementation example)[:\s]*([^.]*\.)',
        r'(?:will work with|partnering with)[:\s]*([^.]*\.)',
    ]
    
    projects = []
    for pattern in project_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            projects.append(match.group(1).strip()[:150])
    
    sections['target_projects'] = ' | '.join(projects[:3]) if projects else ''
    
    # Determine impact areas
    impact_keywords = {
        'AI/ML': ['ai', 'artificial intelligence', 'machine learning', 'llm', 'neural', 'model training'],
        'DeFi': ['defi', 'decentralized finance', 'liquidity', 'trading', 'amm', 'dex', 'lending'],
        'Governance': ['governance', 'voting', 'dao', 'coordination', 'consensus', 'decision'],
        'Infrastructure': ['infrastructure', 'tooling', 'developer', 'sdk', 'api', 'framework', 'library'],
        'Privacy': ['privacy', 'kyc', 'zero knowledge', 'zk', 'maci', 'anonymous', 'confidential'],
        'Science': ['desci', 'science', 'research', 'academic', 'peer review', 'publication'],
        'Community': ['popup', 'residency', 'community', 'events', 'irl', 'meetup', 'conference'],
        'Funding': ['funding', 'grant', 'pgf', 'hypercert', 'retroactive', 'quadratic', 'allocation'],
        'Data': ['data', 'analytics', 'metrics', 'information', 'dashboard', 'insights', 'reporting'],
        'Adoption': ['adoption', 'ux', 'user experience', 'consumer', 'mass', 'onboarding', 'accessibility'],
        'Enterprise': ['enterprise', 'institutional', 'corporate', 'b2b', 'compliance'],
        'Education': ['education', 'learning', 'course', 'training', 'workshop', 'curriculum']
    }
    
    found_areas = []
    for area, keywords in impact_keywords.items():
        if any(kw in content_lower for kw in keywords):
            found_areas.append(area)
    
    sections['impact_areas'] = ', '.join(found_areas[:3]) if found_areas else 'General'
    
    # Extract risks
    risk_patterns = [
        r'(?:risk|challenge|concern|limitation)[:\s]*([^.]*(?:\.[^.]*){0,1}\.)',
        r'(?:potential issue|downside|trade-off)[:\s]*([^.]*\.)',
        r'(?:mitigation|contingency)[:\s]*([^.]*\.)',
    ]
    
    risks = []
    for pattern in risk_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            risks.append(match.group(1).strip()[:150])
    
    sections['risks'] = ' | '.join(risks[:2]) if risks else 'Execution and timeline risks'
    
    # Extract funding information
    funding_patterns = [
        r'(?:funding|budget|grant amount|requested)[:\s]*([^.]*(?:\.[^.]*){0,1}\.)',
        r'(?:\$[\d,]+[kKmM]?|\d+[kKmM]? (?:USD|DAI|ETH))',
        r'(?:co-funding|matched funding|external funding)[:\s]*([^.]*\.)',
    ]
    
    funding_info = []
    for pattern in funding_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            funding_info.append(match.group(0).strip()[:100])
    
    sections['funding'] = ' | '.join(funding_info[:2]) if funding_info else ''
    
    # Extract deployment strategy
    deploy_patterns = [
        r'(?:deployment|rollout|implementation plan)[:\s]*([^.]*(?:\.[^.]*){0,1}\.)',
        r'(?:timeline|roadmap|milestone)[:\s]*([^.]*(?:\.[^.]*){0,1}\.)',
        r'(?:phase \d|stage \d|step \d)[:\s]*([^.]*\.)',
    ]
    
    deployment = []
    for pattern in deploy_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            deployment.append(match.group(1).strip()[:150])
    
    sections['deployment'] = ' | '.join(deployment[:2]) if deployment else 'Phased rollout approach'
    
    return sections

def score_proposal_owocki_style(sections, title, content):
    """Score the proposal in Kevin Owocki's voice with detailed, thoughtful evaluation"""
    scores = {}
    explanations = {}
    feedback = []
    content_lower = content.lower()
    
    # 1. Problem Focus (0-2 points)
    problem_score = 0
    if sections['problem']:
        problem_keywords = ['critical', 'urgent', 'fundamental', 'bottleneck', 'broken', 'crisis', 'failing']
        priority_areas = ['coordination', 'funding', 'adoption', 'sustainability', 'incentive', 'governance']
        
        if any(word in sections['problem'].lower() for word in problem_keywords):
            problem_score += 1
        if any(area in sections['problem'].lower() for area in priority_areas):
            problem_score += 1
        
        if problem_score == 2:
            explanations['problem_focus'] = "Addresses critical ecosystem priority"
            feedback.append("Strong problem identification - this is a real pain point")
        elif problem_score == 1:
            explanations['problem_focus'] = "Valid problem but not urgent priority"
            feedback.append("Problem is real but consider why it's critical now")
        else:
            explanations['problem_focus'] = "Problem exists but lacks urgency"
            feedback.append("Need to articulate why this problem matters now")
    else:
        explanations['problem_focus'] = "No clear problem articulated"
        feedback.append("Missing clear problem statement - what are we solving?")
    
    scores['problem_focus'] = min(problem_score, 2)
    
    # 2. Credible, Evidence-Based Approach (0-2 points)
    approach_score = 0
    evidence_keywords = ['proven', 'evidence', 'research', 'data', 'tested', 'pilot', 'validated', 'demonstrated']
    methodology_keywords = ['framework', 'methodology', 'systematic', 'rigorous', 'peer-reviewed']
    
    if sections['solution']:
        if any(word in content_lower for word in evidence_keywords):
            approach_score += 1
            feedback.append("Good evidence basis")
        if any(word in content_lower for word in methodology_keywords):
            approach_score += 1
            feedback.append("Solid methodology")
        
        if approach_score == 2:
            explanations['credible_approach'] = "Strong evidence-based approach"
        elif approach_score == 1:
            explanations['credible_approach'] = "Some evidence but needs validation"
        else:
            explanations['credible_approach'] = "Approach lacks evidence"
            feedback.append("Need more evidence that this approach works")
    else:
        explanations['credible_approach'] = "No clear solution approach"
        feedback.append("Solution approach is unclear")
    
    scores['credible_approach'] = min(approach_score, 2)
    
    # 3. Domain Expertise (0-2 points)
    expert_score = 0
    if sections['domain_experts']:
        expert_count = len(sections['domain_experts'].split(','))
        if expert_count >= 3:
            expert_score = 2
            explanations['domain_expertise'] = "Strong expert team assembled"
            feedback.append("Excellent team with relevant expertise")
        elif expert_count >= 1:
            expert_score = 1
            explanations['domain_expertise'] = "Some expertise present"
            feedback.append("Consider adding more domain experts")
        else:
            explanations['domain_expertise'] = "Limited expertise shown"
            feedback.append("Need to demonstrate team capability")
    else:
        if sections['credentials']:
            expert_score = 1
            explanations['domain_expertise'] = "Credentials mentioned but team unclear"
            feedback.append("Team credentials present but need clearer team structure")
        else:
            explanations['domain_expertise'] = "No domain experts identified"
            feedback.append("Who will execute this? Need credible team")
    
    scores['domain_expertise'] = expert_score
    
    # 4. Co-Funding (0-2 points)
    funding_score = 0
    if sections['funding'] or 'funding' in content_lower:
        co_funding_keywords = ['secured', 'committed', 'partnered', 'matched', 'raised', 'confirmed']
        seeking_keywords = ['seeking', 'looking for', 'fundraising', 'targeting']
        
        if any(word in content_lower for word in co_funding_keywords):
            funding_score = 2
            explanations['co_funding'] = "Has secured external funding"
            feedback.append("Strong co-funding secured - good signal")
        elif any(word in content_lower for word in seeking_keywords):
            funding_score = 1
            explanations['co_funding'] = "Actively seeking co-funding"
            feedback.append("Working on co-funding but not secured yet")
        else:
            explanations['co_funding'] = "No clear co-funding strategy"
            feedback.append("Need to demonstrate funding beyond Gitcoin")
    else:
        explanations['co_funding'] = "No funding information provided"
        feedback.append("Funding model unclear - how will this sustain?")
    
    scores['co_funding'] = funding_score
    
    # 5. Fit-for-Purpose Capital Allocation (0-2 points)
    capital_score = 0
    innovative_mechanisms = ['hypercert', 'retroactive', 'outcome', 'impact cert', 'maci', 'quadratic']
    standard_mechanisms = ['milestone', 'tranche', 'kpi', 'deliverable', 'phased']
    
    if any(word in content_lower for word in innovative_mechanisms):
        capital_score = 2
        explanations['capital_method'] = "Innovative funding mechanism aligned with goals"
        feedback.append("Love the innovative funding approach")
    elif any(word in content_lower for word in standard_mechanisms):
        capital_score = 1
        explanations['capital_method'] = "Standard milestone-based approach"
        feedback.append("Consider more innovative funding mechanisms")
    else:
        explanations['capital_method'] = "Traditional grant approach"
        feedback.append("Funding mechanism could be more sophisticated")
    
    scores['capital_method'] = capital_score
    
    # 6. Execution Readiness (0-2 points)
    execution_score = 0
    ready_keywords = ['immediately', 'ready', 'launched', 'active', 'live', 'operational', 'deployed']
    progress_keywords = ['pilot', 'mvp', 'prototype', 'beta', 'testing', 'alpha', 'proof of concept']
    
    if any(word in content_lower for word in ready_keywords):
        execution_score = 2
        explanations['execution_readiness'] = "Ready to deploy immediately"
        feedback.append("Execution ready - can deliver by October")
    elif any(word in content_lower for word in progress_keywords):
        execution_score = 1
        explanations['execution_readiness'] = "In pilot/testing phase"
        feedback.append("Making progress but timeline tight for October")
    else:
        explanations['execution_readiness'] = "Early stage, significant work needed"
        feedback.append("Execution timeline unrealistic for October delivery")
    
    scores['execution_readiness'] = execution_score
    
    # 7. General vibe check and alignment (0-2 points)
    vibe_score = 0
    positive_signals = [
        'community' in content_lower,
        'open source' in content_lower,
        'public good' in content_lower,
        'ethereum' in content_lower,
        'decentralized' in content_lower,
        'transparent' in content_lower,
        'collaborative' in content_lower,
        sections['tldr'] != '',
        sections['problem'] != '',
        sections['solution'] != ''
    ]
    
    signal_count = sum(positive_signals)
    
    if signal_count >= 7:
        vibe_score = 2
        explanations['vibe_check'] = "Excellent alignment with ecosystem values"
        feedback.append("Great energy and values alignment")
    elif signal_count >= 4:
        vibe_score = 1
        explanations['vibe_check'] = "Good alignment, could be stronger"
        feedback.append("Decent alignment but could lean in more")
    else:
        explanations['vibe_check'] = "Needs better ecosystem alignment"
        feedback.append("Consider how this fits Ethereum/Gitcoin values")
    
    scores['vibe_check'] = vibe_score
    
    # Add more specific constructive feedback
    if 'ethereum' in content_lower and 'ecosystem' in content_lower:
        feedback.append("Good Ethereum ecosystem focus")
    
    if sections['impact_areas']:
        feedback.append(f"Clear impact in {sections['impact_areas']}")
    
    if not sections['risks']:
        feedback.append("Consider articulating risks and mitigations")
    
    if not sections['deployment']:
        feedback.append("Need clearer deployment roadmap")
    
    total_score = sum(scores.values())
    
    # Calculate confidence based on information completeness
    confidence = 50  # Base confidence
    if sections['tldr']: confidence += 10
    if sections['problem']: confidence += 10
    if sections['solution']: confidence += 10
    if sections['domain_experts']: confidence += 5
    if sections['funding']: confidence += 5
    if sections['risks']: confidence += 5
    if sections['deployment']: confidence += 5
    confidence = min(confidence, 95)
    
    return scores, explanations, total_score, feedback[:10], confidence

def generate_thoughtful_feedback(sections, scores, total_score):
    """Generate thoughtful, constructive feedback bullets"""
    feedback_points = []
    
    # Problem-focused feedback
    if scores.get('problem_focus', 0) < 2:
        feedback_points.append("Clarify the specific problem and why it's urgent for Ethereum's success")
    else:
        feedback_points.append("Excellent problem framing - clearly addresses ecosystem need")
    
    # Solution feedback
    if scores.get('credible_approach', 0) < 2:
        feedback_points.append("Strengthen the evidence base - show prior success or research backing")
    else:
        feedback_points.append("Strong evidence-based approach with clear methodology")
    
    # Team feedback
    if scores.get('domain_expertise', 0) < 2:
        feedback_points.append("Build out team with more domain experts and proven executors")
    else:
        feedback_points.append("Solid team with relevant expertise assembled")
    
    # Funding feedback
    if scores.get('co_funding', 0) == 0:
        feedback_points.append("Develop co-funding strategy to show broader support")
    elif scores.get('co_funding', 0) == 1:
        feedback_points.append("Continue pursuing co-funding to validate market demand")
    else:
        feedback_points.append("Excellent co-funding demonstrates strong validation")
    
    # Mechanism feedback
    if scores.get('capital_method', 0) < 2:
        feedback_points.append("Consider innovative funding mechanisms like hypercerts or retroactive funding")
    
    # Execution feedback
    if scores.get('execution_readiness', 0) < 2:
        feedback_points.append("Accelerate development to meet October delivery timeline")
    else:
        feedback_points.append("Great execution readiness - ready to ship")
    
    # Strategic feedback based on total score
    if total_score >= 12:
        feedback_points.append("This is a strong proposal - focus on execution excellence")
        feedback_points.append("Consider how to scale impact beyond initial implementation")
    elif total_score >= 8:
        feedback_points.append("Solid foundation - address the gaps to strengthen proposal")
        feedback_points.append("Would benefit from clearer success metrics")
    else:
        feedback_points.append("Needs significant strengthening before funding consideration")
        feedback_points.append("Consider partnering with established projects")
    
    # Add specific suggestions
    if not sections['target_projects']:
        feedback_points.append("Identify specific projects or partners for implementation")
    
    if not sections['risks']:
        feedback_points.append("Articulate key risks and mitigation strategies")
    
    return feedback_points[:10]

def generate_rose_thorn_bud(sections, scores, total_score, content):
    """Generate thoughtful rose, thorn, and bud feedback"""
    content_lower = content.lower()
    
    # Rose (what's good)
    rose_options = []
    if scores.get('problem_focus', 0) == 2:
        rose_options.append("Addresses critical ecosystem problem with clarity")
    if scores.get('credible_approach', 0) == 2:
        rose_options.append("Evidence-based approach with strong methodology")
    if scores.get('domain_expertise', 0) == 2:
        rose_options.append("Excellent team with proven expertise")
    if scores.get('co_funding', 0) == 2:
        rose_options.append("Strong co-funding validates approach")
    if 'community' in content_lower and 'open source' in content_lower:
        rose_options.append("Strong community and open source ethos")
    if sections['tldr']:
        rose_options.append("Clear vision and communication")
    
    rose = rose_options[0] if rose_options else "Has potential for ecosystem impact"
    
    # Thorn (what needs improvement)
    thorn_options = []
    if scores.get('execution_readiness', 0) == 0:
        thorn_options.append("Execution timeline unrealistic - needs acceleration")
    if scores.get('domain_expertise', 0) == 0:
        thorn_options.append("Team lacks proven domain expertise")
    if scores.get('co_funding', 0) == 0:
        thorn_options.append("No external validation through co-funding")
    if not sections['risks']:
        thorn_options.append("Risk assessment and mitigation missing")
    if scores.get('problem_focus', 0) == 0:
        thorn_options.append("Problem statement needs clarity and urgency")
    if not sections['deployment']:
        thorn_options.append("Deployment strategy unclear")
    
    thorn = thorn_options[0] if thorn_options else "Needs clearer execution path"
    
    # Bud (what could blossom)
    bud_options = []
    if total_score >= 10:
        bud_options.append("Could become ecosystem cornerstone with proper execution")
    if 'hypercert' in content_lower or 'retroactive' in content_lower:
        bud_options.append("Innovative funding model could set new standards")
    if sections['impact_areas'] and 'AI' in sections['impact_areas']:
        bud_options.append("Potential to lead Ethereum's AI integration")
    if 'community' in content_lower and total_score >= 6:
        bud_options.append("Could catalyze strong community movement")
    if 'infrastructure' in content_lower:
        bud_options.append("Could enable next wave of builders")
    if scores.get('credible_approach', 0) >= 1:
        bud_options.append("Approach could scale across ecosystem if proven")
    
    bud = bud_options[0] if bud_options else "Has potential to evolve into impactful initiative"
    
    return rose, thorn, bud

def generate_steel_man_cases(sections, scores, total_score, content):
    """Generate comprehensive steel man cases for and against"""
    content_lower = content.lower()
    
    # Steel man FOR
    for_points = []
    
    if scores.get('problem_focus', 0) >= 1:
        for_points.append("Addresses a genuine ecosystem need that impacts many projects")
    
    if scores.get('credible_approach', 0) >= 1:
        for_points.append("Approach has theoretical or empirical backing")
    
    if scores.get('domain_expertise', 0) >= 1:
        for_points.append("Team has relevant experience to execute")
    
    if 'community' in content_lower:
        for_points.append("Community-driven approach ensures grassroots adoption")
    
    if 'open source' in content_lower:
        for_points.append("Open source nature maximizes ecosystem benefit")
    
    if sections['impact_areas']:
        for_points.append(f"Clear value proposition in {sections['impact_areas'].split(',')[0]}")
    
    if total_score >= 8:
        for_points.append("Strong overall proposal with multiple strengths")
    
    steel_man_for = ". ".join(for_points[:3]) if for_points else "Has potential to create value for ecosystem"
    
    # Steel man AGAINST
    against_points = []
    
    if scores.get('execution_readiness', 0) < 2:
        against_points.append("Execution timeline suggests project may not deliver by October")
    
    if scores.get('co_funding', 0) == 0:
        against_points.append("Lack of co-funding suggests limited external validation")
    
    if scores.get('domain_expertise', 0) == 0:
        against_points.append("Team lacks proven track record in this domain")
    
    if not sections['risks']:
        against_points.append("Insufficient risk analysis suggests incomplete planning")
    
    if total_score < 8:
        against_points.append("Multiple fundamental weaknesses reduce success probability")
    
    if not sections['target_projects']:
        against_points.append("Unclear implementation path without specific partners")
    
    if scores.get('capital_method', 0) == 0:
        against_points.append("Traditional funding approach may not align incentives properly")
    
    steel_man_against = ". ".join(against_points[:3]) if against_points else "Execution risks may prevent full value realization"
    
    return steel_man_for, steel_man_against

def determine_deployment_strategy(sections, content):
    """Determine comprehensive deployment strategy"""
    content_lower = content.lower()
    strategy_parts = []
    
    # Scale determination
    if 'ecosystem' in content_lower or 'protocol' in content_lower:
        strategy_parts.append("Ecosystem-wide deployment")
    elif 'pilot' in content_lower or 'experiment' in content_lower:
        strategy_parts.append("Pilot program approach")
    else:
        strategy_parts.append("Targeted deployment")
    
    # Timeline
    if 'immediate' in content_lower or 'ready' in content_lower:
        strategy_parts.append("Immediate launch (1-2 months)")
    elif 'q4' in content_lower or 'october' in content_lower:
        strategy_parts.append("Q4 2024 delivery")
    elif 'year' in content_lower:
        strategy_parts.append("12+ month rollout")
    else:
        strategy_parts.append("3-6 month implementation")
    
    # Methodology
    if 'iterative' in content_lower or 'agile' in content_lower:
        strategy_parts.append("Iterative development with feedback loops")
    elif 'phased' in content_lower or 'milestone' in content_lower:
        strategy_parts.append("Phased milestone-based delivery")
    else:
        strategy_parts.append("Standard project delivery")
    
    # Governance
    if 'dao' in content_lower or 'democratic' in content_lower:
        strategy_parts.append("DAO governance model")
    elif 'community' in content_lower:
        strategy_parts.append("Community-led governance")
    else:
        strategy_parts.append("Core team execution")
    
    # Success metrics
    if 'kpi' in content_lower or 'metric' in content_lower:
        strategy_parts.append("Clear KPIs defined")
    elif 'impact' in content_lower:
        strategy_parts.append("Impact measurement framework")
    else:
        strategy_parts.append("Success metrics TBD")
    
    # Risk mitigation
    if 'mitigation' in content_lower or 'contingency' in content_lower:
        strategy_parts.append("Risk mitigation plan in place")
    else:
        strategy_parts.append("Risk assessment needed")
    
    return '\n'.join(strategy_parts)

def format_markdown_entry(row, sections, scores, explanations, total_score, confidence, 
                          feedback, steel_for, steel_against, deployment, rose, thorn, bud):
    """Format a comprehensive markdown entry"""
    title = row['Title']
    link = row['Link']
    author = row['Submitted By']
    
    # Determine outside funding status
    outside_funding = "No external funding mentioned"
    if sections['funding']:
        if any(word in sections['funding'].lower() for word in ['secured', 'committed', 'raised']):
            outside_funding = f"External funding secured: {sections['funding']}"
        elif any(word in sections['funding'].lower() for word in ['seeking', 'targeting']):
            outside_funding = f"Seeking external funding: {sections['funding']}"
        else:
            outside_funding = sections['funding']
    
    md = f"""# ({total_score}) [{title}]({link})

by {author}

## Proposal

### TLDR

{sections['tldr'] if sections['tldr'] else 'Summary not provided - proposal needs clearer executive summary'}

### Problem

{sections['problem'] if sections['problem'] else 'Problem statement not clearly articulated - needs definition of specific challenge being addressed'}

### Solution

{sections['solution'] if sections['solution'] else 'Solution approach not clearly defined - needs specific methodology and implementation details'}

### Domain Experts

{sections['domain_experts'] if sections['domain_experts'] else 'No domain experts identified - team composition unclear'}
{sections['credentials'] if sections['credentials'] else 'Credentials and experience not specified'}

### Target Projects (Examples)

{sections['target_projects'] if sections['target_projects'] else 'No specific implementation targets identified - needs concrete use cases or pilot partners'}

### Deployment strategy

{deployment}

### Risks

{sections['risks'] if sections['risks'] else 'Risk assessment not provided - needs identification of key risks and mitigation strategies'}

## Outside Funding

{outside_funding}

## Owockis scorecard

|#|Criterion|0|1|2|Notes|
| --- | --- | --- | --- | --- | --- |
|1|Problem Focus – Clearly frames a real problem, (one that is a priority), avoids "solutionism"|{"X" if scores['problem_focus'] == 0 else " "}|{"X" if scores['problem_focus'] == 1 else " "}|{"X" if scores['problem_focus'] == 2 else " "}|{explanations['problem_focus']}|
|2|Credible, High leverage, Evidence-Based Approach – Solutions are high-leverage and grounded in credible research|{"X" if scores['credible_approach'] == 0 else " "}|{"X" if scores['credible_approach'] == 1 else " "}|{"X" if scores['credible_approach'] == 2 else " "}|{explanations['credible_approach']}|
|3|Domain Expertise – Proposal has active involvement from recognized experts|{"X" if scores['domain_expertise'] == 0 else " "}|{"X" if scores['domain_expertise'] == 1 else " "}|{"X" if scores['domain_expertise'] == 2 else " "}|{explanations['domain_expertise']}|
|4|Co-Funding – Has financial backing beyond just Gitcoin|{"X" if scores['co_funding'] == 0 else " "}|{"X" if scores['co_funding'] == 1 else " "}|{"X" if scores['co_funding'] == 2 else " "}|{explanations['co_funding']}|
|5|Fit-for-Purpose Capital Allocation Method – Methodology matches the epistemology of the domain|{"X" if scores['capital_method'] == 0 else " "}|{"X" if scores['capital_method'] == 1 else " "}|{"X" if scores['capital_method'] == 2 else " "}|{explanations['capital_method']}|
|6|Execution Readiness – Can deliver meaningful results by October|{"X" if scores['execution_readiness'] == 0 else " "}|{"X" if scores['execution_readiness'] == 1 else " "}|{"X" if scores['execution_readiness'] == 2 else " "}|{explanations['execution_readiness']}|
|7|Other - general vibe check and other stuff I may have missed above..|{"X" if scores['vibe_check'] == 0 else " "}|{"X" if scores['vibe_check'] == 1 else " "}|{"X" if scores['vibe_check'] == 2 else " "}|{explanations['vibe_check']}|

### Score

Confidence : {confidence}%
Total Score: {total_score} / 14

### Feedback:

"""
    
    for point in feedback:
        md += f"- {point}\n"
    
    md += f"""
### Rose, bud, and thorn:

**Rose (strength):** {rose}
**Thorn (weakness):** {thorn}
**Bud (potential):** {bud}

### Steel man case for/against:

#### For

{steel_for}

#### Against

{steel_against}

"""
    
    return md

def generate_owocki_feedback(title, sections, total_score):
    """Generate Owocki-style high level feedback"""
    if total_score >= 12:
        return "Strong proposal - ready to fund with minor refinements"
    elif total_score >= 10:
        return "Solid proposal with good potential - address key gaps"
    elif total_score >= 8:
        return "Promising but needs strengthening in execution and validation"
    elif total_score >= 6:
        return "Has merit but requires significant development"
    elif total_score >= 4:
        return "Early stage - needs fundamental improvements"
    else:
        return "Not ready - requires major rethinking and development"

# Main processing
if __name__ == "__main__":
    # Read CSV data
    csv_data = []
    with open('/Users/owocki/Sites/gg24/data/data.csv', 'r') as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)
    
    print(f"Processing {len(csv_data)} proposals...")
    
    entries = []
    leaderboard_data = []
    
    for i, row in enumerate(csv_data):
        print(f"Processing {i+1}/{len(csv_data)}: {row['Title']}")
        
        link = row['Link']
        # Extract post ID from URL
        post_id_match = re.search(r'/(\d+)(?:/|$)', link)
        if not post_id_match:
            print(f"Could not extract post ID from {link}")
            continue
        
        post_id = post_id_match.group(1)
        filepath = f'/Users/owocki/Sites/gg24/posts/{post_id}.html'
        
        title, content = extract_full_content(filepath)
        if not title:
            title = row['Title']
        
        if not content:
            print(f"No content extracted for {title}")
            content = f"{title} - Content not available"
        
        sections = parse_content_sections(content, title)
        scores, explanations, total_score, initial_feedback, confidence = score_proposal_owocki_style(sections, title, content)
        
        # Generate comprehensive feedback
        feedback = generate_thoughtful_feedback(sections, scores, total_score)
        rose, thorn, bud = generate_rose_thorn_bud(sections, scores, total_score, content)
        steel_for, steel_against = generate_steel_man_cases(sections, scores, total_score, content)
        deployment = determine_deployment_strategy(sections, content)
        
        entry_md = format_markdown_entry(row, sections, scores, explanations, total_score, confidence,
                                        feedback, steel_for, steel_against, deployment, rose, thorn, bud)
        
        entries.append((total_score, entry_md, row['Title'], row['Link'], row['Submitted By']))
        
        # Generate leaderboard data
        high_level_feedback = generate_owocki_feedback(title, sections, total_score)
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
        output += f"| {item['title']} by {item['author']} | {item['score']}/14 | {item['feedback']} | {item['rose']} | {item['thorn']} | {item['bud']} |\n"
    
    output += "\n# Reports\n\n"
    
    # Add sorted entries
    for score, entry_md, title, link, author in entries:
        output += entry_md + "\n---\n\n"
    
    # Write to file
    with open('/Users/owocki/Sites/gg24/data/data.md', 'w') as f:
        f.write(output)
    
    print(f"Successfully created data.md with {len(entries)} proposals processed")
    print(f"Top proposal: {entries[0][2]} with score {entries[0][0]}/14")
    print(f"Lowest proposal: {entries[-1][2]} with score {entries[-1][0]}/14")