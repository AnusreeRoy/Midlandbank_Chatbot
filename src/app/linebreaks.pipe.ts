import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import DOMPurify from 'dompurify';

@Pipe({
  name: 'linebreaks',
  standalone: true
})
export class LinebreaksPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  transform(text: string): SafeHtml {
    if (!text) return '';

    const lines = text.trim().split('\n');
    let html = '';
    let inList = false;

    for (let line of lines) {
      line = line.trim();
      if (!line) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        continue;
      }

      // === Headings ===
      const headingLabels = ['savings products', 'loan products', 'current products', 'islamic products',
        'general products', 'agent-banking products', 'cards products', 'loans products', 'loans', 'loan', 
        'current','savings', 'loan', 'current', 'benefits', 'eligibility', 'documents', 'institutional products'];

      const cleanedLine = line.toLowerCase().replace(/^[-•\s]+/, '').replace(/[:\s]+$/g, '').trim();
      const isHeading = headingLabels.includes(cleanedLine);

      if (isHeading) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        html += `<h3>${this.escapeHtml(line)}</h3>`;
        continue;
      }

      // MDB Product heading
      const isPotentialProductHeading =
        /^[A-Z\s\d\-&()]+$/.test(line) && line.startsWith('MDB') && line.split(' ').length <= 6;
      if (isPotentialProductHeading) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        html += `<h3>${this.escapeHtml(line)}</h3>`;
        continue;
      }

      // === Bullet Line ===
      const isBullet = line.startsWith('•') || line.startsWith('- ');
      const isKeyValue = /^[-•]?\s*[\w\s]+:\s*/.test(line);
      if (isBullet && isKeyValue) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }

        const cleanLine = line.replace(/^[-•]\s*/, '');
        const [key, ...rest] = cleanLine.split(':');
        const value = rest.join(':').trim();

        html += `<p><b>${this.escapeHtml(key.trim())}:</b> ${this.escapeHtml(value)}</p>`;
      }
      else if (isBullet) {
        if (!inList) {
          html += '<ul>';
          inList = true;
        }
        const cleanLine = line.replace(/^[-•]\s*/, '');
        html += `<li>${this.escapeHtml(cleanLine)}</li>`;
      }
      else {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        html += `<p>${this.escapeHtml(line)}</p>`;
      }
    }

    if (inList) {
      html += '</ul>';
    }

    const safeHtml = DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
    return this.sanitizer.bypassSecurityTrustHtml(safeHtml);
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
}
