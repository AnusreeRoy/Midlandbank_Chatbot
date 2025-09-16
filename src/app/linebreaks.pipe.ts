// linebreaks.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'linebreaks',
  standalone: true // This pipe can be used in standalone components
})
export class LinebreaksPipe implements PipeTransform {
  transform(text: string): string {
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

      // === HEADINGS ===
      const headingLabels = ['savings products', 'loan products', 'current products', 'islamic products',
        'general products', 'agent-banking products', 'cards products', 'loans products',
        'savings', 'loan', 'current', 'benefits', 'eligibility', 'documents'];

      const cleanedLine = line.toLowerCase().replace(/^[-•\s]+/, '').replace(/[:\s]+$/g, '').trim();

      const isHeading = headingLabels.includes(cleanedLine);

      if (isHeading) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        html += `<h3>${line.replace(/^[-•\s]+/, '').replace(/[:\s]+$/g, '').trim()}</h3>`;
        continue;
      }

      // Heading for product name
      const isPotentialProductHeading =
        /^[A-Z\s\d\-&()]+$/.test(line) && line.startsWith('MDB') && line.split(' ').length <= 6;
      if (isPotentialProductHeading) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        html += `<h3>${line.trim()}</h3>`;
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

        // Extract key and value
        const cleanLine = line.replace(/^[-•]\s*/, '');
        const [key, ...rest] = cleanLine.split(':');
        const value = rest.join(':').trim();

        html += `<p><b>${key.trim()}:</b> ${value}</p>`;
      }
      else if (isBullet) {
        if (!inList) {
          html += '<ul>';
          inList = true;
        }
        const cleanLine = line.replace(/^[-•]\s*/, '');
        html += `<li>${cleanLine}</li>`;
      }
      else {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        html += `<p>${line}</p>`;
      }
    }

    if (inList) {
      html += '</ul>';
    }

    return html;
  }
}
