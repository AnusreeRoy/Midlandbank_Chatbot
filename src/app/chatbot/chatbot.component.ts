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
import { Component, HostListener, ViewChild, ElementRef, ViewChildren, QueryList, AfterViewChecked, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { LinebreaksPipe } from '../linebreaks.pipe';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule, LinebreaksPipe],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss']
})
export class ChatbotComponent implements AfterViewChecked {

  @ViewChild('chatBody') chatBody!: ElementRef;
  @ViewChild('chatInput') chatInput!: ElementRef<HTMLInputElement>;
  @ViewChildren('messageElement') messageElements!: QueryList<ElementRef>;
  @ViewChildren('messageText') messageTexts!: QueryList<ElementRef>;

  private shouldScroll = false;

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }
  chatVisible: boolean = false;
  userQuery: string = '';
  isExpanded: boolean = false;
  chatHistory: { text: string; isUser: boolean;  isLoading: boolean }[] = [];


  constructor(private http: HttpClient, private sanitizer: DomSanitizer, private cdr: ChangeDetectorRef) {} // Inject HttpClient and DomSanitizer

toggleChat(): void {
  this.chatVisible = !this.chatVisible;

  if (this.chatVisible) {
    this.addGreeting(); // greet on open

    setTimeout(() => {
      if (this.chatInput) {
        this.chatInput.nativeElement.focus();
      }
    }, 100);
  }
}


  toggleExpand(): void {
    this.isExpanded = !this.isExpanded;
  }

  sanitize(text: string): SafeHtml {
    const escaped = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const formatted = escaped.replace(/\n/g, '<br/>');
    return this.sanitizer.bypassSecurityTrustHtml(formatted);
  }
  sendMessage(): void {
    
    if (this.userQuery.trim().length > 1000){
      alert("Your message exceeds the 1000 character limit. Please shorten your message and try again.");
      return;
    }

    if (this.userQuery.trim()) {
      this.chatHistory.push({ text: this.userQuery, isUser: true, isLoading: false });
  
      // Add temporary "Typing..." message only for this input
      const typingMessage = { text: '', isUser: false, isLoading: true };
      this.chatHistory.push(typingMessage);
      this.shouldScroll = true; // Ensure scroll after view update

      let dotCount = 0;
      const baseText = 'Thinking';
      const typingInterval = setInterval(() => {
        dotCount = (dotCount + 1) % 4; // Cycle through 0, 1, 2, 3
        typingMessage.text = baseText + ".".repeat(dotCount);
        this.cdr.markForCheck();
        this.shouldScroll = true; // Ensure scroll after view update
      }, 500); // Update every 500ms  
      
    this.http.post<{ response: string }>('http://localhost:8000/chatbot/', { message: this.userQuery },{ withCredentials: true })
    //this.http.post<{ response: string }>('http://localhost:33915/mdb/GetChatbotResponse/' , { message: this.userQuery }, { withCredentials: true })
    //this.http.post<{ response: string }>('http://10.96.56.51:4200/mdb/GetChatbotResponse/' , { message: this.userQuery }, { withCredentials: true })

        .subscribe({
          next: (data) => {
            clearInterval(typingInterval);
            console.log("Received response:", data); // Log response for debugging
  
            // Remove "Typing..." message and add the actual response
            const index = this.chatHistory.indexOf(typingMessage);
            if (index !== -1) {
              this.chatHistory.splice(index, 1);  // Remove only this loading message
            }
  
            this.chatHistory.push({ text: data.response, isUser: false, isLoading:false });
            this.shouldScroll = true; // Ensure scroll after view update
          },
          error: (error) => {
            clearInterval(typingInterval);
            console.error("API Error:", error); // Log exact error message
  
            const index = this.chatHistory.indexOf(typingMessage);
            if (index !== -1) {
              this.chatHistory.splice(index, 1);  // Remove "Typing..."
            }
  
            const errorMessage = error.status === 429 
              ? "Your query is highly important to us. Currently we’re receiving a huge number of requests. Please wait a moment and try again.." 
              : "We are having some trouble right now. Please wait or try again later.";
  
            this.chatHistory.push({ text: errorMessage, isUser: false, isLoading:false });
          },
          complete : () => {}
        });
  
      this.userQuery = ''; // Clear input field
      this.chatInput.nativeElement.focus(); // Refocus input
      this.shouldScroll = true; // Ensure scroll after view update
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
  const elements = this.messageElements?.toArray();
  if (elements && elements.length > 0) {
    const last = elements[elements.length - 1];
    last.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}


private addGreeting(): void {
  // Prevent duplicate greeting
  const alreadyGreeted = this.chatHistory.some(msg =>
    msg.text.includes("Midland Bank")
  );
  if (alreadyGreeted) return;

  // Determine time-based greeting
  const hour = new Date().getHours();
  let timeGreeting = "Hello";
  if (hour < 12) {
    timeGreeting = "Good morning";
  } else if (hour < 18) {
    timeGreeting = "Good afternoon";
  } else {
    timeGreeting = "Good evening";
  }

  // Add typing animation for realism
  const typingMessage = { text: "Typing", isUser: false, isLoading: true };
  this.chatHistory.push(typingMessage);

  let dotCount = 0;
  const typingInterval = setInterval(() => {
    dotCount = (dotCount + 1) % 4;
    typingMessage.text = "Typing" + ".".repeat(dotCount);
  }, 400);

  setTimeout(() => {
    clearInterval(typingInterval);
    const index = this.chatHistory.indexOf(typingMessage);
    if (index !== -1) this.chatHistory.splice(index, 1);

    // Push the friendly greeting
    this.chatHistory.push({
      text: `👋 ${timeGreeting}! I'm the Midland Bank AI Assistant. How can I help you today?`,
      isUser: false,
      isLoading: false
    });

    this.shouldScroll = true; // Ensure scroll after view update
  }, 200);
}


}