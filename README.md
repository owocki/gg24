# GG24 Sensemaking Reports Analysis

This repository contains tools and data for analyzing Gitcoin Grants 24 (GG24) sensemaking reports.

## Overview

This project downloads and analyzes sensemaking reports from the Gitcoin governance forum to evaluate proposals for GG24 funding domains. It extracts key information from each proposal to facilitate review and decision-making.

## Structure

```
gg24/
├── data.csv                 # Main CSV with all proposal data and analysis
├── data_original.csv        # Backup of original CSV data
├── posts/                   # Downloaded HTML files of forum posts
├── download_posts.py        # Script to download posts from URLs
├── extract_post_data.py     # Script to extract and analyze post content
└── README.md               # This file
```

## Data Columns

The `data.csv` file contains the following information for each proposal:

### Basic Information
- **Date Submitted** - Submission date of the proposal
- **Title** - Proposal title
- **Submitted By** - Author username
- **Link** - URL to the forum post

### Content & Clarity
- **TL;DR / One-liner** - 1-2 sentence summary of the proposal
- **Problem Statement** - Core problem the domain addresses
- **Proposed Solution / Scope** - What's being done about it

### People & Expertise
- **Domain Experts Involved** - Who is backing or advising
- **Community Support** - Links to endorsements, comments, or traction

### Impact & Value
- **Intended Impact** - What success looks like / target outcomes
- **Impact Area** - Category (Infrastructure, Governance, AI/ML, DeFi, etc.)
- **Leverage / Multiplier Effect** - Why this is high-leverage vs. niche

### Practicality & Feasibility
- **Execution Readiness** - High / Medium / Low ability to run in October
- **Existing Funding** - If they already have support beyond Gitcoin
- **Dependencies / Risks** - What could block progress

### Review Support
- **Review Notes** - Space for reviewer comments
- **Reviewer Score** - 1-5 or traffic-light rating

## Usage

### Download Posts
```bash
python3 scripts/download_posts.py
```
Downloads all forum posts from URLs in `data.csv` to the `posts/` directory.

### Extract and Analyze Data
```bash
python3 scripts/extract_post_data.py
```
Parses HTML files and extracts relevant information to populate all CSV columns.


### Create report card
```bash
claude code
<< edit/insert prompt.txt >>
```

Create report card judging each proposal

## Requirements

- Python 3.x
- Standard library modules (csv, urllib, html.parser, os)

## License

Data sourced from public Gitcoin governance forum posts.