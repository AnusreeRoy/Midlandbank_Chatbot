import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ButtonComponent } from "./button/button.component";
import { ChatbotComponent } from "./chatbot/chatbot.component";
import { LinebreaksPipe } from './linebreaks.pipe';

@Component({
  selector: 'app-root',
  imports: [ChatbotComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'AngularApp';
}
