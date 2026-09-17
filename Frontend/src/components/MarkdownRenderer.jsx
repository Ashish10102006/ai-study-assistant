import React from 'react';

/**
 * Parses inline markdown tokens: **bold**, *italic*, `code`, and links [text](url)
 */
function renderInline(text) {
  if (!text) return null;

  // Split text by markdown tokens: bold, italic, code
  const parts = [];
  let remaining = text;
  let key = 0;

  // Regex matches: **bold**, *italic*, `code`, [link](url)
  const regex = /(\*\*.*?\*\*|\*.*?\*|`.*?`|\[.*?\]\(.*?\))/g;
  let match;
  let lastIdx = 0;

  while ((match = regex.exec(text)) !== null) {
    // Text before match
    if (match.index > lastIdx) {
      parts.push(text.substring(lastIdx, match.index));
    }

    const token = match[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(
        <strong key={key++} style={{ color: '#ffffff', fontWeight: 700 }}>
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith('*') && token.endsWith('*')) {
      parts.push(
        <em key={key++} style={{ color: 'var(--text-secondary, #94a3b8)', fontStyle: 'italic' }}>
          {token.slice(1, -1)}
        </em>
      );
    } else if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(
        <code
          key={key++}
          style={{
            background: 'rgba(0, 242, 254, 0.1)',
            color: 'var(--brand-cyan, #00f2fe)',
            padding: '0.15rem 0.4rem',
            borderRadius: '4px',
            fontSize: '0.9em',
            fontFamily: 'monospace'
          }}
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith('[') && token.includes('](') && token.endsWith(')')) {
      const label = token.substring(1, token.indexOf(']('));
      const url = token.substring(token.indexOf('](') + 2, token.length - 1);
      parts.push(
        <a
          key={key++}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: 'var(--brand-cyan, #00f2fe)', textDecoration: 'underline' }}
        >
          {label}
        </a>
      );
    }

    lastIdx = match.index + token.length;
  }

  if (lastIdx < text.length) {
    parts.push(text.substring(lastIdx));
  }

  return parts.length > 0 ? parts : text;
}

export default function MarkdownRenderer({ content, style = {} }) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements = [];
  let inCodeBlock = false;
  let codeBlockContent = [];
  let codeBlockLang = '';
  let listItems = [];
  let listType = null; // 'ul' | 'ol'
  let tableRows = [];

  const flushTable = () => {
    if (tableRows.length > 0) {
      const isDivider = (r) => r.every(cell => /^[-: ]+$/.test(cell));
      let headerRow = null;
      let bodyRows = [];

      if (tableRows.length > 1 && isDivider(tableRows[1])) {
        headerRow = tableRows[0];
        bodyRows = tableRows.slice(2);
      } else {
        bodyRows = tableRows;
      }

      elements.push(
        <div key={elements.length} className="markdown-table-wrapper">
          <table className="markdown-table">
            {headerRow && (
              <thead>
                <tr>
                  {headerRow.map((cell, cIdx) => (
                    <th key={cIdx}>{renderInline(cell)}</th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody>
              {bodyRows.map((row, rIdx) => (
                <tr key={rIdx}>
                  {row.map((cell, cIdx) => (
                    <td key={cIdx}>{renderInline(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableRows = [];
    }
  };

  const flushList = () => {
    if (listItems.length > 0) {
      if (listType === 'ol') {
        elements.push(
          <ol key={elements.length} style={{ paddingLeft: '1.5rem', marginBottom: '0.85rem' }}>
            {listItems.map((item, idx) => (
              <li key={idx} style={{ marginBottom: '0.35rem', lineHeight: '1.6' }}>
                {renderInline(item)}
              </li>
            ))}
          </ol>
        );
      } else {
        elements.push(
          <ul key={elements.length} style={{ paddingLeft: '1.5rem', marginBottom: '0.85rem' }}>
            {listItems.map((item, idx) => (
              <li key={idx} style={{ marginBottom: '0.35rem', lineHeight: '1.6' }}>
                {renderInline(item)}
              </li>
            ))}
          </ul>
        );
      }
      listItems = [];
      listType = null;
    }
  };

  const flushAll = () => {
    flushList();
    flushTable();
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Handle multi-line code blocks: ```lang ... ```
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        // End of code block
        elements.push(
          <div
            key={elements.length}
            style={{
              background: '#090d16',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '10px',
              padding: '0.85rem 1rem',
              margin: '0.85rem 0',
              overflowX: 'auto',
              WebkitOverflowScrolling: 'touch',
              maxWidth: '100%',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '0.85rem'
            }}
          >
            <pre style={{ margin: 0, color: '#e2e8f0', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {codeBlockContent.join('\n')}
            </pre>
          </div>
        );
        inCodeBlock = false;
        codeBlockContent = [];
        codeBlockLang = '';
      } else {
        flushAll();
        inCodeBlock = true;
        codeBlockLang = line.trim().slice(3).trim();
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line);
      continue;
    }

    // Markdown Table Rows: | col1 | col2 |
    const trimmedLine = line.trim();
    if (trimmedLine.startsWith('|') && trimmedLine.endsWith('|') && trimmedLine.length > 2) {
      flushList();
      const cells = trimmedLine.slice(1, -1).split('|').map(c => c.trim());
      tableRows.push(cells);
      continue;
    } else {
      flushTable();
    }

    // Horizontal Rule: --- or ***
    if (line.trim() === '---' || line.trim() === '***') {
      flushAll();
      elements.push(
        <hr
          key={elements.length}
          style={{
            border: 'none',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            margin: '1.25rem 0'
          }}
        />
      );
      continue;
    }

    // Headings: #, ##, ###, ####
    if (line.startsWith('### ')) {
      flushAll();
      elements.push(
        <h3
          key={elements.length}
          style={{
            fontSize: '1.18rem',
            fontWeight: 700,
            color: '#f8fafc',
            marginTop: '1.25rem',
            marginBottom: '0.5rem',
            lineHeight: '1.35'
          }}
        >
          {renderInline(line.slice(4))}
        </h3>
      );
      continue;
    }

    if (line.startsWith('## ')) {
      flushAll();
      elements.push(
        <h2
          key={elements.length}
          style={{
            fontSize: '1.35rem',
            fontWeight: 700,
            color: 'var(--brand-cyan, #00f2fe)',
            marginTop: '1.5rem',
            marginBottom: '0.6rem',
            lineHeight: '1.35'
          }}
        >
          {renderInline(line.slice(3))}
        </h2>
      );
      continue;
    }

    if (line.startsWith('# ')) {
      flushAll();
      elements.push(
        <h1
          key={elements.length}
          style={{
            fontSize: '1.55rem',
            fontWeight: 800,
            color: '#ffffff',
            marginTop: '1.75rem',
            marginBottom: '0.75rem'
          }}
        >
          {renderInline(line.slice(2))}
        </h1>
      );
      continue;
    }

    // Unordered List Items: - item or * item
    const ulMatch = line.match(/^(\s*)[-*]\s+(.+)/);
    if (ulMatch) {
      if (listType !== 'ul') {
        flushAll();
        listType = 'ul';
      }
      listItems.push(ulMatch[2]);
      continue;
    }

    // Ordered List Items: 1. item
    const olMatch = line.match(/^(\s*)\d+\.\s+(.+)/);
    if (olMatch) {
      if (listType !== 'ol') {
        flushAll();
        listType = 'ol';
      }
      listItems.push(olMatch[2]);
      continue;
    }

    // Blank line
    if (!line.trim()) {
      flushAll();
      continue;
    }

    // Regular Paragraph
    flushAll();
    elements.push(
      <p
        key={elements.length}
        style={{
          marginBottom: '0.85rem',
          lineHeight: '1.65',
          color: '#e2e8f0'
        }}
      >
        {renderInline(line)}
      </p>
    );
  }

  flushAll();

  return <div style={{ fontSize: '0.96rem', maxWidth: '100%', wordBreak: 'break-word', overflowWrap: 'anywhere', ...style }}>{elements}</div>;
}
