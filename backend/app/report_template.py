REPORT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');

:root {
  --primary: #1a56db;
  --primary-light: #e8effd;
  --success: #059669;
  --success-light: #ecfdf5;
  --warning: #d97706;
  --warning-light: #fffbeb;
  --danger: #dc2626;
  --danger-light: #fef2f2;
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-200: #e5e7eb;
  --gray-300: #d1d5db;
  --gray-500: #6b7280;
  --gray-700: #374151;
  --gray-900: #111827;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--gray-700);
  line-height: 1.8;
  font-size: 14px;
  background: #fff;
}

.report {
  max-width: 900px;
  margin: 0 auto;
  padding: 48px 40px;
}

/* Cover / Title */
.report > h1:first-child {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-900);
  border-bottom: 3px solid var(--primary);
  padding-bottom: 16px;
  margin-bottom: 8px;
}

/* Metadata line right after title */
.report > p:first-of-type {
  color: var(--gray-500);
  font-size: 13px;
  margin-bottom: 32px;
}

/* Section headings */
h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--gray-900);
  margin-top: 40px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--gray-200);
}

h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-900);
  margin-top: 24px;
  margin-bottom: 12px;
}

h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700);
  margin-top: 16px;
  margin-bottom: 8px;
}

/* Paragraphs */
p {
  margin-bottom: 12px;
}

/* Lists */
ul, ol {
  margin-bottom: 16px;
  padding-left: 24px;
}

li {
  margin-bottom: 6px;
}

li > ul, li > ol {
  margin-top: 6px;
  margin-bottom: 6px;
}

/* Bold / strong as highlight */
strong {
  color: var(--gray-900);
  font-weight: 600;
}

/* Tables */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0 24px;
  font-size: 13px;
}

thead {
  background: var(--gray-50);
}

th {
  text-align: left;
  padding: 10px 12px;
  font-weight: 600;
  color: var(--gray-900);
  border-bottom: 2px solid var(--gray-200);
  white-space: nowrap;
}

td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--gray-100);
  vertical-align: top;
}

tr:hover td {
  background: var(--gray-50);
}

/* Code blocks */
code {
  background: var(--gray-100);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: var(--danger);
}

pre {
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 16px 0;
}

pre code {
  background: none;
  padding: 0;
  color: var(--gray-700);
}

/* Blockquote as callout */
blockquote {
  border-left: 4px solid var(--primary);
  background: var(--primary-light);
  padding: 12px 16px;
  margin: 16px 0;
  border-radius: 0 8px 8px 0;
}

blockquote p {
  margin-bottom: 0;
}

/* Horizontal rule as section divider */
hr {
  border: none;
  border-top: 1px solid var(--gray-200);
  margin: 32px 0;
}

/* Emoji/icon markers for common section patterns */
h2:has(+ ul) {
  margin-bottom: 12px;
}

/* Print / PDF specific */
@media print {
  .report {
    padding: 0;
    max-width: none;
  }

  h2 {
    page-break-after: avoid;
  }

  table, pre, blockquote {
    page-break-inside: avoid;
  }
}

/* PDF page settings */
@page {
  size: A4;
  margin: 20mm 15mm;
}
"""


def wrap_report_html(body_html: str, title: str = "GYG Scout Report") -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{REPORT_CSS}</style>
</head>
<body>
<div class="report">
{body_html}
</div>
</body>
</html>"""
