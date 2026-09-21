import io
import re
from xhtml2pdf import pisa


def generate_pdf_bytes_from_html(html_content: str) -> bytes:
    """Renders exact HTML/CSS layouts into PDF using pure Python (xhtml2pdf)."""
    pdf_buffer = io.BytesIO()
    
    # Render HTML + CSS directly into PDF
    pisa_status = pisa.CreatePDF(
        src=html_content,
        dest=pdf_buffer
    )
    
    if pisa_status.err:
        raise RuntimeError("Failed to render PDF using xhtml2pdf.")
        
    return pdf_buffer.getvalue()


def generate_pdf_bytes(title: str, text_content: str) -> bytes:
    """Backwards-compatibility wrapper for legacy plain-text and Market Report PDF generation calls."""
    # Format line breaks and paragraphs cleanly into HTML
    formatted_body = text_content.replace('\n', '<br>')
    
    formatted_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #2D3748;
                line-height: 1.5;
                font-size: 10pt;
            }}
            h1 {{
                color: #1A365D;
                font-size: 16pt;
                text-align: center;
                border-bottom: 2px solid #2B6CB0;
                padding-bottom: 6px;
                margin-bottom: 15px;
            }}
            .report-content {{
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 12px 15px;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="report-content">
            {formatted_body}
        </div>
    </body>
    </html>"""
    
    return generate_pdf_bytes_from_html(formatted_html)


def generate_resume_html(
    name: str = "SOUVIK GHOSH",
    title: str = "Backend Engineer - Cloud Native & Scalable Systems",
    phone: str = "+91 967 484 7794",
    email: str = "souvik.ghosh12@tcs.com",
    github: str = "https://github.com",
    linkedin: str = "https://linkedin.com",
    education: str = "",
    summary: str = "",
    competencies: dict = None,
    experiences: list = None,
    projects: list = None,
    certifications: list = None
) -> str:
    """Generates clean, print-ready HTML with custom styled CSS boxes for resumes."""
    
    # 1. Contact Links Row
    links = []
    if phone:
        links.append(f'<span>{phone}</span>')
    if email:
        links.append(f'<a href="mailto:{email}">{email}</a>')
    if github:
        links.append(f'<a href="{github}">GitHub</a>')
    if linkedin:
        links.append(f'<a href="{linkedin}">LinkedIn</a>')
    
    links_html = " &nbsp;•&nbsp; ".join(links)

    # 2. Core Competencies Table Rows
    comp_rows = ""
    if competencies:
        for cat, val in competencies.items():
            comp_rows += f"""
            <tr>
                <td class="comp-label">{cat}</td>
                <td class="comp-val">{val}</td>
            </tr>
            """

    # 3. Professional Experience Blocks
    exp_html = ""
    if experiences:
        for exp in experiences:
            bullets = "".join([f"<li>{b}</li>" for b in exp.get("bullets", [])])
            exp_html += f"""
            <div class="exp-item">
                <div class="item-header">
                    <span class="role-company"><b>{exp.get('company', '')}</b> — <i>{exp.get('role', '')}</i></span>
                    <span class="dates">{exp.get('location', '')} | {exp.get('dates', '')}</span>
                </div>
                <ul>{bullets}</ul>
            </div>
            """

    # 4. Selected Projects Rows
    proj_rows = ""
    if projects:
        for p in projects:
            proj_rows += f"""
            <tr>
                <td style="width: 25%;"><b>{p.get('name', '')}</b></td>
                <td style="width: 35%;">{p.get('tech', '')}</td>
                <td style="width: 40%;">{p.get('impact', '')}</td>
            </tr>
            """

    # 5. Certifications Bullet List
    certs_html = ""
    if certifications:
        certs_bullets = "".join([f"<li>{c}</li>" for c in certifications])
        certs_html = f"<ul>{certs_bullets}</ul>"

    # Full Styled HTML Template
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @page {{
            size: A4;
            margin: 10mm 12mm 10mm 12mm;
        }}
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #2D3748;
            line-height: 1.35;
            font-size: 9.5pt;
            margin: 0;
            padding: 0;
        }}
        
        /* HEADER STYLING */
        .header-container {{
            text-align: center;
            border-bottom: 2px solid #2B6CB0;
            padding-bottom: 6px;
            margin-bottom: 10px;
        }}
        .candidate-name {{
            font-size: 18pt;
            font-weight: bold;
            color: #1A365D;
            letter-spacing: 0.5px;
            margin: 0;
            text-transform: uppercase;
        }}
        .candidate-title {{
            font-size: 10.5pt;
            font-weight: 600;
            color: #2B6CB0;
            margin-top: 2px;
        }}
        .contact-row {{
            font-size: 8.5pt;
            color: #4A5568;
            margin-top: 4px;
        }}
        .contact-row a {{
            color: #2B6CB0;
            text-decoration: none;
        }}

        /* SECTION BOXES STYLING */
        .section-box {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 5px;
            padding: 8px 10px;
            margin-bottom: 10px;
        }}
        .section-title {{
            font-size: 10pt;
            font-weight: bold;
            color: #1A365D;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
            border-bottom: 1px solid #CBD5E0;
            padding-bottom: 2px;
        }}

        /* COMPETENCIES TABLE */
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        td {{
            vertical-align: top;
            padding: 3px 5px;
            font-size: 9pt;
        }}
        .comp-label {{
            font-weight: bold;
            width: 25%;
            color: #2D3748;
            border-right: 1px solid #E2E8F0;
        }}
        .comp-val {{
            width: 75%;
            color: #4A5568;
        }}

        /* EXPERIENCES & LISTS */
        .exp-item {{
            margin-bottom: 6px;
        }}
        .item-header {{
            font-size: 9pt;
            margin-bottom: 2px;
            overflow: hidden;
        }}
        .role-company {{
            color: #1A365D;
            float: left;
        }}
        .dates {{
            color: #718096;
            font-size: 8.5pt;
            float: right;
        }}
        ul {{
            margin: 2px 0 4px 16px;
            padding: 0;
            clear: both;
        }}
        li {{
            margin-bottom: 2px;
            font-size: 8.8pt;
            color: #2D3748;
        }}

        /* PROJECTS TABLE */
        .proj-table th {{
            background-color: #2B6CB0;
            color: #ffffff;
            font-size: 8.5pt;
            text-align: left;
            padding: 4px 6px;
        }}
        .proj-table td {{
            border-bottom: 1px solid #E2E8F0;
            font-size: 8.5pt;
        }}
    </style>
</head>
<body>

    <!-- HEADER SECTION -->
    <div class="header-container">
        <div class="candidate-name">{name}</div>
        <div class="candidate-title">{title}</div>
        <div class="contact-row">{links_html}</div>
    </div>

    <!-- EDUCATION BOX -->
    {f'<div class="section-box"><div class="section-title">Education</div><div>{education}</div></div>' if education else ''}

    <!-- PROFESSIONAL SUMMARY BOX -->
    {f'<div class="section-box"><div class="section-title">Professional Summary</div><div style="font-size: 9pt; text-align: justify; color: #2D3748;">{summary}</div></div>' if summary else ''}

    <!-- CORE COMPETENCIES BOX -->
    {f'<div class="section-box"><div class="section-title">Core Competencies</div><table>{comp_rows}</table></div>' if comp_rows else ''}

    <!-- PROFESSIONAL EXPERIENCE BOX -->
    {f'<div class="section-box"><div class="section-title">Professional Experience</div>{exp_html}</div>' if exp_html else ''}

    <!-- SELECTED PROJECTS BOX -->
    {f'''<div class="section-box">
        <div class="section-title">Selected Projects</div>
        <table class="proj-table">
            <thead>
                <tr>
                    <th>Project Name</th>
                    <th>Role & Tech Stack</th>
                    <th>Impact / Key Outcome</th>
                </tr>
            </thead>
            <tbody>
                {proj_rows}
            </tbody>
        </table>
    </div>''' if proj_rows else ''}

    <!-- CERTIFICATIONS & ACHIEVEMENTS BOX -->
    {f'''<div class="section-box">
        <div class="section-title">Certifications & Achievements</div>
        {certs_html}
    </div>''' if certs_html else ''}

</body>
</html>
"""