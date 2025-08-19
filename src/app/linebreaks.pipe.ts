// linebreaks.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'linebreaks',
  standalone: true // This pipe can be used in standalone components
})
export class LinebreaksPipe implements PipeTransform {
  transform(text: string): string {
    return text.replace(/\n/g, '<br>');
  }
}
