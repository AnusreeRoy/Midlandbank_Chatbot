// import { CommonModule } from '@angular/common';
// import { Component, HostListener, ViewChild, ElementRef } from '@angular/core';
// import { FormsModule } from '@angular/forms';

// @Component({
//   selector: 'app-chatbot',
//   standalone: true,
//   imports: [CommonModule, FormsModule],
//   templateUrl: './chatbot.component.html',
//   styleUrls: ['./chatbot.component.scss']
// })
// export class ChatbotComponent {

//   @ViewChild('chatBody') chatBody!: ElementRef; // Reference to the chat body
//   chatVisible: boolean = false; // Controls chat visibility
//   userQuery: string = ''; // Stores user input
//   chatHistory: { text: string; isUser: boolean }[] = []; // Chat messages

//   toggleChat(): void {
//     // Toggle the visibility of the chat interface
//     console.log('toggleChat called!');
//     this.chatVisible = !this.chatVisible;
//     console.log('chatVisible:', this.chatVisible); 
//   }

//   sendMessage(): void {
//     if (this.userQuery.trim()) {
//       this.chatHistory.push({ text: this.userQuery, isUser: true }); // Add user message
//       this.chatHistory.push({ text: "I'm here to help!", isUser: false }); // Bot response placeholder
//       this.userQuery = ''; // Clear input field
//       this.scrollToBottom(); // Scroll to the latest message
//     }
//   }

//   @HostListener('document:click', ['$event']) // Listen for clicks anywhere on the page
//   closeChatOnOutsideClick(event: MouseEvent): void {
//     const target = event.target as HTMLElement;
//     const clickedInsideChat = target.closest('.chat-interface');
//     const clickedIcon = target.closest('.chatbot-icon');

//     if (!clickedInsideChat && !clickedIcon) {
//       this.chatVisible = false; // Close chat if clicked outside
//     }
//   }

//   scrollToBottom(): void {
//     setTimeout(() => {
//       if (this.chatBody && this.chatBody.nativeElement) {
//         this.chatBody.nativeElement.scrollTop = this.chatBody.nativeElement.scrollHeight;
//       }
//     }, 100); // Delay to ensure DOM updates before scrolling
//   }
// }




import { CommonModule } from '@angular/common';
import { Component, HostListener, ViewChild, ElementRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { LinebreaksPipe } from '../linebreaks.pipe';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule, LinebreaksPipe],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss']
})
export class ChatbotComponent {

  @ViewChild('chatBody') chatBody!: ElementRef;
  @ViewChild('chatInput') chatInput!: ElementRef<HTMLInputElement>;
  chatVisible: boolean = false;
  userQuery: string = '';
  isExpanded: boolean = false;
  chatHistory: { text: string; isUser: boolean;  isLoading: boolean }[] = [];

  constructor(private http: HttpClient) {} // Inject HttpClient

  toggleChat(): void {
    this.chatVisible = !this.chatVisible;

    setTimeout(() => {
      if(this.chatVisible && this.chatInput){
        this.chatInput.nativeElement.focus();
      }
    }, 100);
  }

  toggleExpand(): void {
    this.isExpanded = !this.isExpanded;
  }

  sendMessage(): void {
    if (this.userQuery.trim()) {
      this.chatHistory.push({ text: this.userQuery, isUser: true, isLoading: false });
  
      // Add temporary "Typing..." message only for this input
      const typingMessage = { text: "Thinking...", isUser: false, isLoading: true };
      this.chatHistory.push(typingMessage);

      let dotCount = 0;
      const typingInterval = setInterval(() => {
        dotCount = (dotCount + 1) % 4; // Cycle through 0, 1, 2, 3
        typingMessage.text = "Thinking" + ".".repeat(dotCount);
      }, 500); // Update every 500ms  
      
    // this.http.post<{ response: string }>('http://chatbot.midlandbankbd.net:4200/'+this.userQuery, { withCredentials: true })
      this.http.post<{ response: string }>('http://localhost:8000/chatbot/', { message: this.userQuery }, { withCredentials: true })
        .subscribe({
          next: (data) => {
            console.log("Received response:", data); // Log response for debugging
  
            // Remove "Typing..." message and add the actual response
            const index = this.chatHistory.indexOf(typingMessage);
            if (index !== -1) {
              this.chatHistory.splice(index, 1);  // Remove only this loading message
            }
  
            this.chatHistory.push({ text: data.response, isUser: false, isLoading:false });
          },
          error: (error) => {
            clearInterval(typingInterval);
            console.error("API Error:", error); // Log exact error message
  
            const index = this.chatHistory.indexOf(typingMessage);
            if (index !== -1) {
              this.chatHistory.splice(index, 1);  // Remove "Typing..."
            }
  
            const errorMessage = error.status === 429 
              ? "Rate limit exceeded. Please wait and try again." 
              : "Error communicating with chatbot.";
  
            this.chatHistory.push({ text: errorMessage, isUser: false, isLoading:false });
          },
          complete : () => {}
        });
  
      this.userQuery = ''; // Clear input field
      this.chatInput.nativeElement.focus(); // Refocus input
      this.scrollToBottom();
    }
  }

  @HostListener('document:click', ['$event'])
  closeChatOnOutsideClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    if (!target.closest('.chat-interface') && !target.closest('.chatbot-icon')) {
      this.chatVisible = false;
    }
  }

  
scrollToBottom(): void {
  setTimeout(() => {
    if (this.chatBody?.nativeElement) {
      const chatBodyEl = this.chatBody.nativeElement;
      const lastMessage = chatBodyEl.lastElementChild;

      if (lastMessage) {
        (lastMessage as HTMLElement).scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, 150); 
}

}