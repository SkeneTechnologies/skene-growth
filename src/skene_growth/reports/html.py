"""
HTML Report Generator for PLG Readiness

Generates a Skene-branded HTML report from growth manifests with shareable scorecards.
"""

import html as html_module
from datetime import datetime
from pathlib import Path
from typing import Any

import json

from skene_growth.manifest import DocsManifest, GrowthManifest, ProductOverview
from skene_growth.reports.score import PLGScoreResult, calculate_plg_score


def escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS attacks."""
    if not text:
        return ""
    return html_module.escape(str(text))


def _js_string(value: str) -> str:
    """Convert Python string to JavaScript string literal."""
    return json.dumps(str(value))


def generate_html_report(manifest: GrowthManifest, score_result: PLGScoreResult | None = None) -> str:
    """
    Generate a Skene-branded HTML report from a growth manifest.

    Args:
        manifest: Growth manifest to generate report from
        score_result: Pre-calculated score result (optional, will calculate if not provided)

    Returns:
        Complete HTML document as string
    """
    # Calculate score if not provided
    if score_result is None:
        score_result = calculate_plg_score(manifest)

    # Ensure manifest has required fields
    full_manifest = _normalize_manifest(manifest)

    # Get prioritized loops and gaps
    prioritized_loops = sorted(
        full_manifest.growth_hubs,
        key=lambda x: x.confidence_score,
        reverse=True,
    )[:5]

    high_priority_gaps = [
        gap for gap in full_manifest.gtm_gaps if gap.priority == "high"
    ][:3]

    # Grade colors and emojis
    grade_colors = {
        "A": "#39ff14",  # Emerald green
        "B": "#80eaff",  # Electric blue
        "C": "#EDC29C",  # Skene brand color
        "D": "#EDC29C",  # Skene brand color
        "F": "#EDC29C",  # Skene brand color
    }

    grade_emojis = {
        "A": "🏆",
        "B": "⭐",
        "C": "📈",
        "D": "🔧",
        "F": "🌱",
    }

    grade_color = grade_colors.get(score_result.grade, "#EDC29C")
    grade_emoji = grade_emojis.get(score_result.grade, "📊")

    # Generate HTML
    html = _generate_html_template(
        full_manifest,
        score_result,
        prioritized_loops,
        high_priority_gaps,
        grade_color,
        grade_emoji,
    )

    return html


def _normalize_manifest(manifest: GrowthManifest) -> DocsManifest:
    """Normalize manifest to ensure all required fields exist."""
    # If it's already a DocsManifest, return as-is
    if isinstance(manifest, DocsManifest):
        return manifest

    # Create a DocsManifest with defaults for missing fields
    description = manifest.description or "No description available"
    product_overview = getattr(manifest, "product_overview", None)
    features = getattr(manifest, "features", [])

    # Create default product_overview if missing
    if product_overview is None:
        product_overview = ProductOverview(
            tagline=description,
            value_proposition=description,
            target_audience="Developers and product teams",
        )

    # Create DocsManifest with defaults
    return DocsManifest(
        version=manifest.version,
        project_name=manifest.project_name,
        description=description,
        tech_stack=manifest.tech_stack,
        growth_hubs=manifest.growth_hubs,
        gtm_gaps=manifest.gtm_gaps,
        generated_at=manifest.generated_at,
        product_overview=product_overview,
        features=features or [],
    )


def _generate_html_template(
    manifest: DocsManifest,
    score_result: PLGScoreResult,
    prioritized_loops: list,
    high_priority_gaps: list,
    grade_color: str,
    grade_emoji: str,
) -> str:
    """Generate the complete HTML template."""
    # Format generated_at date
    try:
        if isinstance(manifest.generated_at, str):
            gen_date = datetime.fromisoformat(manifest.generated_at.replace("Z", "+00:00"))
        else:
            gen_date = manifest.generated_at
        formatted_date = gen_date.strftime("%B %d, %Y")
    except Exception:
        formatted_date = "Unknown"

    # Generate loops HTML
    loops_html = ""
    if prioritized_loops:
        loops_html = _generate_loops_section(prioritized_loops)

    # Generate gaps HTML
    gaps_html = ""
    if high_priority_gaps:
        gaps_html = _generate_gaps_section(high_priority_gaps)

    # Generate share text for JavaScript
    share_text = (
        f'My product "{manifest.project_name}" has a PLG Readiness Score of '
        f"{score_result.score}/100 (Grade {score_result.grade})! 🚀\\n\\n"
        f"{score_result.message}\\n\\n"
        f"Check out your PLG readiness with Skene Growth Analyzer: "
        f"https://github.com/SkeneTechnologies/skene-growth"
    )

    # Escape JavaScript strings
    js_project_name = _js_string(manifest.project_name)
    js_grade = _js_string(score_result.grade)
    js_message = _js_string(score_result.message)
    js_share_text = _js_string(share_text)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta property="og:title" content="PLG Readiness: {escape_html(manifest.project_name)} - {score_result.score}/100">
  <meta property="og:description" content="{escape_html(score_result.message)}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <title>PLG Readiness: {escape_html(manifest.project_name)} - {score_result.score}/100</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    * {{ 
      margin: 0; 
      padding: 0; 
      box-sizing: border-box; 
    }}
    
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      background: #060606;
      color: #EBDCCF;
      line-height: 1.6;
      padding: 0;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      text-rendering: optimizeLegibility;
      font-feature-settings: "kern" 1;
    }}
    
    .container {{ 
      max-width: 1000px; 
      margin: 0 auto; 
      padding: 60px 24px; 
    }}
    
    .header {{
      text-align: center;
      margin-bottom: 64px;
      padding-bottom: 48px;
      border-bottom: 1px solid rgba(237, 194, 156, 0.15);
    }}
    
    .logo {{
      display: inline-flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 32px;
    }}
    
    .logo svg {{ 
      width: 40px; 
      height: 40px; 
    }}
    
    .logo-text {{
      font-size: 24px;
      font-weight: 600;
      color: #EDC29C;
      letter-spacing: -0.3px;
    }}
    
    .project-name {{
      font-size: 36px;
      font-weight: 500;
      color: #EBDCCF;
      margin-bottom: 12px;
      letter-spacing: -0.5px;
    }}
    
    .project-description {{
      font-size: 16px;
      color: #A1A1A1;
      max-width: 640px;
      margin: 0 auto;
      font-weight: 400;
      line-height: 1.6;
    }}
    
    .score-section {{
      text-align: center;
      margin-bottom: 64px;
      padding: 56px 40px;
      background: linear-gradient(135deg, rgba(237, 194, 156, 0.03) 0%, rgba(237, 194, 156, 0.01) 100%);
      border: 1px solid rgba(237, 194, 156, 0.12);
      border-radius: 20px;
    }}
    
    .score-display {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 24px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }}
    
    .score-number {{
      font-size: 120px;
      font-weight: 600;
      color: {grade_color};
      line-height: 1;
      letter-spacing: -2px;
      text-rendering: optimizeLegibility;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      font-feature-settings: "kern" 1, "liga" 1;
      text-shadow: 0 0 1px rgba(237, 194, 156, 0.1);
      display: inline-block;
    }}
    
    .score-max {{
      font-size: 56px;
      color: #A1A1A1;
      font-weight: 400;
    }}
    
    .grade-badge {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-size: 32px;
      font-weight: 500;
      color: {grade_color};
      padding: 14px 28px;
      background: rgba(237, 194, 156, 0.08);
      border: 1px solid rgba(237, 194, 156, 0.15);
      border-radius: 12px;
      text-rendering: optimizeLegibility;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      font-feature-settings: "kern" 1, "liga" 1;
    }}
    
    .grade-badge .grade-emoji {{
      font-size: 28px;
      line-height: 1;
      display: inline-block;
      vertical-align: middle;
      filter: drop-shadow(0 0 1px rgba(237, 194, 156, 0.2));
    }}
    
    .score-message {{
      font-size: 20px;
      color: #EBDCCF;
      margin-top: 24px;
      font-weight: 400;
      max-width: 600px;
      margin-left: auto;
      margin-right: auto;
    }}
    
    .share-buttons {{
      display: flex;
      justify-content: center;
      gap: 12px;
      margin-top: 32px;
      flex-wrap: wrap;
    }}
    
    .share-button {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 20px;
      background: rgba(237, 194, 156, 0.1);
      border: 1px solid rgba(237, 194, 156, 0.2);
      border-radius: 8px;
      color: #EDC29C;
      font-size: 14px;
      font-weight: 500;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.2s ease;
      font-family: 'Inter', sans-serif;
    }}
    
    .share-button:hover {{
      background: rgba(237, 194, 156, 0.15);
      border-color: rgba(237, 194, 156, 0.3);
      transform: translateY(-1px);
    }}
    
    .share-button:active {{
      transform: translateY(0);
    }}
    
    .share-button svg {{
      width: 16px;
      height: 16px;
      fill: currentColor;
    }}
    
    .breakdown {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      margin-top: 48px;
    }}
    
    .breakdown-item {{
      padding: 24px;
      background: rgba(10, 10, 10, 0.6);
      border: 1px solid rgba(237, 194, 156, 0.08);
      border-radius: 12px;
      text-align: center;
      transition: all 0.2s ease;
    }}
    
    .breakdown-item:hover {{
      border-color: rgba(237, 194, 156, 0.2);
      background: rgba(10, 10, 10, 0.8);
    }}
    
    .breakdown-label {{
      font-size: 11px;
      color: #A1A1A1;
      text-transform: uppercase;
      letter-spacing: 1.56px;
      margin-bottom: 12px;
      font-family: 'JetBrains Mono', 'Courier New', monospace;
      font-weight: 400;
    }}
    
    .breakdown-value {{
      font-size: 40px;
      font-weight: 600;
      color: #EDC29C;
      line-height: 1;
      text-rendering: optimizeLegibility;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      font-feature-settings: "kern" 1, "liga" 1;
    }}
    
    .breakdown-max {{
      font-size: 14px;
      color: #666;
      margin-top: 4px;
    }}
    
    .section {{
      margin-bottom: 56px;
    }}
    
    .section-title {{
      font-size: 28px;
      font-weight: 500;
      color: #EDC29C;
      margin-bottom: 32px;
      display: flex;
      align-items: center;
      gap: 16px;
      letter-spacing: -0.5px;
    }}
    
    .section-title::before {{
      content: '';
      width: 4px;
      height: 28px;
      background: #EDC29C;
      border-radius: 2px;
    }}
    
    .loops-grid {{
      display: grid;
      gap: 24px;
    }}
    
    .loop-card {{
      padding: 28px;
      background: rgba(10, 10, 10, 0.6);
      border: 1px solid rgba(237, 194, 156, 0.12);
      border-radius: 16px;
      transition: all 0.3s ease;
    }}
    
    .loop-card:hover {{
      border-color: rgba(237, 194, 156, 0.3);
      background: rgba(10, 10, 10, 0.8);
      transform: translateY(-2px);
    }}
    
    .loop-header {{
      display: flex;
      justify-content: space-between;
      align-items: start;
      margin-bottom: 16px;
      gap: 16px;
    }}
    
    .loop-name {{
      font-size: 20px;
      font-weight: 500;
      color: #EBDCCF;
      flex: 1;
      letter-spacing: -0.3px;
    }}
    
    .loop-confidence {{
      font-size: 12px;
      color: #EDC29C;
      background: rgba(237, 194, 156, 0.1);
      padding: 6px 14px;
      border-radius: 8px;
      font-weight: 500;
      font-family: 'JetBrains Mono', 'Courier New', monospace;
      white-space: nowrap;
    }}
    
    .loop-intent {{
      font-size: 15px;
      color: #A1A1A1;
      margin-bottom: 20px;
      line-height: 1.6;
      font-weight: 400;
    }}
    
    .loop-potential {{
      margin-top: 20px;
    }}
    
    .loop-potential-title {{
      font-size: 11px;
      color: #EDC29C;
      text-transform: uppercase;
      letter-spacing: 1.56px;
      margin-bottom: 12px;
      font-family: 'JetBrains Mono', 'Courier New', monospace;
      font-weight: 400;
    }}
    
    .loop-potential-list {{
      list-style: none;
      padding: 0;
    }}
    
    .loop-potential-list li {{
      font-size: 14px;
      color: #EBDCCF;
      padding: 10px 0;
      padding-left: 24px;
      position: relative;
      line-height: 1.6;
    }}
    
    .loop-potential-list li::before {{
      content: '→';
      position: absolute;
      left: 0;
      color: #EDC29C;
      font-weight: 500;
    }}
    
    .gaps-list {{
      list-style: none;
      padding: 0;
    }}
    
    .gap-item {{
      padding: 24px;
      background: rgba(10, 10, 10, 0.6);
      border-left: 3px solid #EDC29C;
      border-radius: 12px;
      margin-bottom: 20px;
    }}
    
    .gap-name {{
      font-size: 20px;
      font-weight: 500;
      color: #EBDCCF;
      margin-bottom: 10px;
      letter-spacing: -0.3px;
    }}
    
    .gap-description {{
      font-size: 15px;
      color: #A1A1A1;
      line-height: 1.6;
      font-weight: 400;
    }}
    
    .footer {{
      text-align: center;
      padding-top: 48px;
      margin-top: 64px;
      border-top: 1px solid rgba(237, 194, 156, 0.15);
      color: #A1A1A1;
      font-size: 14px;
    }}
    
    .footer a {{
      color: #EDC29C;
      text-decoration: none;
      transition: opacity 0.2s;
    }}
    
    .footer a:hover {{
      opacity: 0.8;
    }}
    
    .share-note {{
      margin-top: 16px;
      padding: 16px;
      background: rgba(237, 194, 156, 0.05);
      border: 1px solid rgba(237, 194, 156, 0.1);
      border-radius: 12px;
      font-size: 13px;
      color: #A1A1A1;
      text-align: left;
    }}
    
    .share-note strong {{
      color: #EDC29C;
    }}
    
    @media (max-width: 768px) {{
      .container {{ padding: 40px 20px; }}
      .score-number {{ font-size: 80px; }}
      .score-max {{ font-size: 40px; }}
      .grade-badge {{ font-size: 24px; padding: 10px 20px; }}
      .project-name {{ font-size: 28px; }}
      .section-title {{ font-size: 24px; }}
      .breakdown {{ grid-template-columns: 1fr; }}
    }}
    
    @media print {{
      body {{ background: #060606; }}
      .container {{ max-width: 100%; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none">
          <path d="M10,30 Q10,10 30,10 L70,10 Q90,10 90,30 L90,70 Q90,90 70,90 L30,90 Q10,90 10,70" stroke="#EDC29C" stroke-width="4" stroke-linecap="round"></path>
          <path d="M10,70 L10,50" stroke="#EDC29C" stroke-width="4" stroke-linecap="round"></path>
          <path d="M10,30 L10,35" stroke="#EDC29C" stroke-width="4" stroke-linecap="round"></path>
          <circle cx="30" cy="30" r="6" fill="#8C6B47" opacity="0.8"></circle>
          <circle cx="50" cy="30" r="6" fill="#8C6B47" opacity="0.8"></circle>
          <circle cx="70" cy="30" r="6" fill="#8C6B47" opacity="0.8"></circle>
        </svg>
        <span class="logo-text">Skene</span>
      </div>
      <h1 class="project-name">{escape_html(manifest.project_name)}</h1>
      <p class="project-description">{escape_html(manifest.description or '')}</p>
    </div>

    <div class="score-section">
      <div class="score-display">
        <div class="score-number">{score_result.score}</div>
        <div class="score-max">/ 100</div>
        <div class="grade-badge">
          <span class="grade-emoji">{grade_emoji}</span> Grade {score_result.grade}
        </div>
      </div>
      <p class="score-message">{escape_html(score_result.message)}</p>

      <div class="share-buttons">
        <button class="share-button" onclick="shareScorecardImage('linkedin')" title="Share scorecard image on LinkedIn">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
          </svg>
          LinkedIn
        </button>
        <button class="share-button" onclick="shareScorecardImage('twitter')" title="Share scorecard image on Twitter/X">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
          </svg>
          Twitter
        </button>
        <button class="share-button" onclick="downloadScorecardImage()" title="Download scorecard image">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Download
        </button>
      </div>

      <div class="breakdown">
        <div class="breakdown-item">
          <div class="breakdown-label">Growth Hubs</div>
          <div class="breakdown-value">{score_result.breakdown.growth_hubs}</div>
          <div class="breakdown-max">/ 40</div>
        </div>
        <div class="breakdown-item">
          <div class="breakdown-label">GTM Gaps</div>
          <div class="breakdown-value">{score_result.breakdown.gtm_gaps}</div>
          <div class="breakdown-max">/ 30</div>
        </div>
        <div class="breakdown-item">
          <div class="breakdown-label">Tech Stack</div>
          <div class="breakdown-value">{score_result.breakdown.tech_stack}</div>
          <div class="breakdown-max">/ 15</div>
        </div>
        <div class="breakdown-item">
          <div class="breakdown-label">Features</div>
          <div class="breakdown-value">{score_result.breakdown.features}</div>
          <div class="breakdown-max">/ 15</div>
        </div>
      </div>
    </div>

{loops_html}

{gaps_html}

    <div class="footer">
      <p>Generated by <a href="https://github.com/SkeneTechnologies/skene-growth" target="_blank">Skene</a> Growth Analyzer</p>
      <p style="margin-top: 8px; font-size: 12px;">Analysis Date: {formatted_date}</p>
      <div class="share-note">
        <strong>💡 How to share:</strong> Click LinkedIn or Twitter to open the share dialog with pre-filled text. The scorecard image will download automatically - just upload it to your post! On mobile devices, the image will be attached automatically.
      </div>
    </div>
  </div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
  <script>
    (function() {{
      const projectName = {js_project_name};
      const score = {score_result.score};
      const grade = {js_grade};
      const message = {js_message};
      
      const shareText = {js_share_text};

      async function captureScorecard() {{
        const scoreSection = document.querySelector('.score-section');
        if (!scoreSection) return null;

        try {{
          const canvas = await html2canvas(scoreSection, {{
            backgroundColor: '#060606',
            scale: 2,
            logging: false,
            useCORS: true,
            width: scoreSection.offsetWidth,
            height: scoreSection.offsetHeight
          }});
          
          return new Promise((resolve) => {{
            canvas.toBlob((blob) => {{
              resolve(blob);
            }}, 'image/png');
          }});
        }} catch (error) {{
          console.error('Error capturing scorecard:', error);
          return null;
        }}
      }}

      window.shareScorecardImage = async function(platform) {{
        const shareText = {js_share_text};
        const shareTextEncoded = encodeURIComponent(shareText);
        const githubUrl = 'https://github.com/SkeneTechnologies/skene-growth';

        let shareWindow = null;
        if (platform === 'linkedin') {{
          shareWindow = window.open('https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(githubUrl) + '&summary=' + shareTextEncoded, '_blank', 'width=600,height=400');
        }} else if (platform === 'twitter') {{
          shareWindow = window.open('https://twitter.com/intent/tweet?text=' + shareTextEncoded, '_blank', 'width=600,height=400');
        }}

        const blob = await captureScorecard();
        if (blob) {{
          const imageUrl = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = imageUrl;
          link.download = 'plg-readiness-scorecard.png';
          link.style.display = 'none';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          setTimeout(() => {{
            URL.revokeObjectURL(imageUrl);
          }}, 2000);
        }}
      }};

      window.downloadScorecardImage = async function() {{
        const blob = await captureScorecard();
        if (!blob) {{
          alert('Failed to capture scorecard image. Please try again.');
          return;
        }}

        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'plg-readiness-scorecard-' + projectName.toLowerCase().replace(/\\s+/g, '-') + '.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }};

      if (navigator.share) {{
        const shareButton = document.createElement('button');
        shareButton.className = 'share-button';
        shareButton.innerHTML = '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>Share';
        shareButton.onclick = async function() {{
          const blob = await captureScorecard();
          if (!blob) {{
            alert('Failed to capture scorecard image. Please try again.');
            return;
          }}
          
          const file = new File([blob], 'plg-readiness-scorecard.png', {{ type: 'image/png' }});
          try {{
            if (navigator.canShare && navigator.canShare({{ files: [file] }})) {{
              await navigator.share({{
                title: 'PLG Readiness: ' + projectName + ' - ' + score + '/100',
                text: shareText,
                files: [file]
              }});
            }} else {{
              await navigator.share({{
                title: 'PLG Readiness: ' + projectName + ' - ' + score + '/100',
                text: shareText
              }});
            }}
          }} catch (err) {{
            if (err.name !== 'AbortError') {{
              console.error('Share failed:', err);
            }}
          }}
        }};
        const shareButtons = document.querySelector('.share-buttons');
        if (shareButtons) {{
          shareButtons.appendChild(shareButton);
        }}
      }}
    }})();
  </script>
</body>
</html>"""


def _generate_loops_section(prioritized_loops: list) -> str:
    """Generate HTML for the top growth loops section."""
    loops_html = """
    <div class="section">
      <h2 class="section-title">Top Growth Loops to Enable</h2>
      <div class="loops-grid">
"""
    for loop in prioritized_loops:
        confidence_pct = round(loop.confidence_score * 100)
        potential_html = ""
        if loop.growth_potential:
            potential_items = "".join(
                f"<li>{escape_html(p)}</li>"
                for p in loop.growth_potential[:3]
            )
            potential_html = f"""
            <div class="loop-potential">
              <div class="loop-potential-title">Growth Potential</div>
              <ul class="loop-potential-list">
                {potential_items}
              </ul>
            </div>
"""
        loops_html += f"""
        <div class="loop-card">
          <div class="loop-header">
            <div class="loop-name">{escape_html(loop.feature_name)}</div>
            <div class="loop-confidence">{confidence_pct}%</div>
          </div>
          <p class="loop-intent">{escape_html(loop.detected_intent)}</p>
{potential_html}
        </div>
"""
    loops_html += """
      </div>
    </div>
"""
    return loops_html


def _generate_gaps_section(high_priority_gaps: list) -> str:
    """Generate HTML for the high-priority gaps section."""
    gaps_html = """
    <div class="section">
      <h2 class="section-title">High-Priority Opportunities</h2>
      <ul class="gaps-list">
"""
    for gap in high_priority_gaps:
        gaps_html += f"""
        <li class="gap-item">
          <div class="gap-name">{escape_html(gap.feature_name)}</div>
          <p class="gap-description">{escape_html(gap.description)}</p>
        </li>
"""
    gaps_html += """
      </ul>
    </div>
"""
    return gaps_html
