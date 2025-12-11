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
import { timeout, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
declare var webkitSpeechRecognition: any;
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
  private recognition: any;
  private currentPlayingMessage: any = null;

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }
  chatVisible: boolean = false;
  userQuery: string = '';
  isExpanded: boolean = false;
  lastInputWasVoice: boolean = false;
  chatHistory: { text: string; isUser: boolean;  isLoading: boolean, showStopButton?: boolean, showResumeButton?: boolean,pausedText?: string,
  pausedCharIndex?: number, isPlaying?: boolean;}[] = [];


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

ngOnInit(): void {
  if ('webkitSpeechRecognition' in window) {
    this.recognition = new webkitSpeechRecognition();
    this.recognition.continuous = false; // Stops after the first speech result
    this.recognition.interimResults = false; // Get only final results
  }
}

startVoiceInput(): void {
  this.stopSpeech(); // Stop any ongoing TTS or audio playback

  if (!this.recognition) {
    // Show message in chat instead of alert
    this.chatHistory.push({
      text: "Your browser does not support voice input.",
      isUser: false,
      isLoading: false
    });
    this.shouldScroll = true;
    this.cdr.detectChanges();
    return;
  }

  // Reset state for each new voice input attempt
  let noVoiceInputDetected = true;
  let silenceTimer: any;

  // Optional: show a "Listening..." indicator
  const listeningMessage = {
    text: "🎤 Listening...",
    isUser: false,
    isLoading: false
  };
  this.chatHistory.push(listeningMessage);
  this.shouldScroll = true;
  this.cdr.detectChanges();

  // Set up the result handler to process speech input
  this.recognition.onresult = (event: SpeechRecognitionEvent) => {
    clearTimeout(silenceTimer); // Stop silence detection when speech is detected

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];
      const transcript = result[0].transcript;
      if (result.isFinal && transcript.trim()) {
        this.userQuery = transcript.trim();
        noVoiceInputDetected = false; // Voice input detected
        this.lastInputWasVoice = true;
        this.recognition.stop(); // Stop recognition after result
        this.sendMessage(); // Send the detected message

        // Remove the "Listening..." indicator
        const index = this.chatHistory.indexOf(listeningMessage);
        if (index !== -1) this.chatHistory.splice(index, 1);
        this.cdr.detectChanges();
      }
    }
  };

  // Handle speech recognition errors
  this.recognition.onerror = (event: SpeechRecognitionError) => {
    clearTimeout(silenceTimer);
    console.error('Speech recognition error', event);

    // Replace alert with chat message
    let errorMsg = 'Sorry, something went wrong with the voice input. Please try again.';
    if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
      errorMsg = 'Microphone access denied. Please allow microphone permissions and try again.';
    } else if (event.error === 'no-speech') {
      errorMsg = 'No speech detected. Please speak clearly and try again.';
    }

    this.chatHistory.push({ text: errorMsg, isUser: false, isLoading: false });
    this.lastInputWasVoice = false;

    // Remove "Listening..." indicator
    const index = this.chatHistory.indexOf(listeningMessage);
    if (index !== -1) this.chatHistory.splice(index, 1);

    this.shouldScroll = true;
    this.cdr.detectChanges();
  };

  // Start speech recognition
  this.recognition.start();

  this.recognition.onstart = () => {
  // Set a timer for detecting no voice input
  silenceTimer = setTimeout(() => {
    if (noVoiceInputDetected) {
      this.chatHistory.push({
        text: 'No voice input detected. Please try again or type your message.',
        isUser: false,
        isLoading: false
      });
      this.lastInputWasVoice = false;
      this.recognition.stop();

      // Remove "Listening..." indicator
      const index = this.chatHistory.indexOf(listeningMessage);
      if (index !== -1) this.chatHistory.splice(index, 1);

      this.shouldScroll = true;
      this.cdr.detectChanges();
    }
  }, 6000); // 6 seconds of silence detection
};
}

  // sendMessage(): void {
  //   this.stopSpeech();

  //   if (!this.userQuery.trim()) {
  //     alert("Please enter a message or speak something.");
  //   return;  // Prevent sending an empty message
  //   }
    
  //   // Prevent duplicate sends if already processing
  //   if (this.chatHistory.some(m => m.isLoading)) {
  //     return;
  //   }
  
  //   if (this.userQuery.trim().length > 1000){
  //     alert("Your message exceeds the 1000 character limit. Please shorten your message and try again.");
  //     return;
  //   }

  //   if (this.userQuery.trim()) {
  //     this.chatHistory.push({ text: this.userQuery, isUser: true, isLoading: false });
  
  //     // Add temporary "Typing..." message only for this input
  //     const typingMessage = { text: '', isUser: false, isLoading: true };
  //     this.chatHistory.push(typingMessage);
  //     this.shouldScroll = true; // Ensure scroll after view update

  //     let dotCount = 0;
  //     const baseText = 'Thinking';
  //     const typingInterval = setInterval(() => {
  //       dotCount = (dotCount + 1) % 4; // Cycle through 0, 1, 2, 3
  //       typingMessage.text = baseText + ".".repeat(dotCount);
  //       this.cdr.markForCheck();
  //       this.shouldScroll = true; // Ensure scroll after view update
  //     }, 500); // Update every 500ms  
      
  //   const TIMEOUT_DURATION = 30000; // 10 seconds timeout
  //   //this.http.post<{ response: string }>('http://localhost:8000/chatbot/', { message: this.userQuery },{ withCredentials: true })
  //   this.http.post<{ response: string }>('http://localhost:33915/mdb/GetChatbotResponse/' , { message: this.userQuery }, { withCredentials: true })
  //   //this.http.post<{ response: string }>('http://10.96.56.51:4200/mdb/GetChatbotResponse/' , { message: this.userQuery }, { withCredentials: true })

  //       .pipe(
  //       timeout(TIMEOUT_DURATION), // Timeout after 10 seconds
  //       catchError(error => {
  //         clearInterval(typingInterval);
  //         console.error("API Error:", error); // Log exact error message

  //         const index = this.chatHistory.indexOf(typingMessage);
  //         if (index !== -1) {
  //           this.chatHistory.splice(index, 1);  // Remove "Typing..."
  //         }

  //         const errorMessage = error.name === 'TimeoutError'
  //           ? "The request took too long. Please try again later." 
  //           : "We are having some trouble right now. Please try again later.";

  //         this.chatHistory.push({ text: errorMessage, isUser: false, isLoading: false });
  //         this.shouldScroll = true; // Ensure scroll after view update
  //         return of(null); // Return empty observable to prevent further errors
  //       })
  //     )

  //       .subscribe({
  //         next: (data) => {
  //           clearInterval(typingInterval);
  //           console.log("Received response:", data); // Log response for debugging
  
  //           // Remove "Typing..." message and add the actual response
  //           const index = this.chatHistory.indexOf(typingMessage);
  //           if (index !== -1) {
  //             this.chatHistory.splice(index, 1);  // Remove only this loading message
  //           }
  //           if(data){
  //             const botMessage = ({ text: data.response, isUser: false, isLoading:false, showStopButton: false });
  //             this.chatHistory.push(botMessage);
  //             // Speak only if the last input was voice
  //             if (this.lastInputWasVoice && data.response && data.response.trim()) {
  //               botMessage.showStopButton = true;   // <--- show stop button
  //               // force UI to update BEFORE speech synthesis
  //               this.cdr.detectChanges();
  //               setTimeout(() => {
  //               const utterance = new SpeechSynthesisUtterance(data.response.trim());
            
  //               // Optional tuning
  //               utterance.lang = 'en-US';       // set to 'bn-BD' for Bengali if needed
  //               utterance.rate = 1.0;           // 0.5–2.0
  //               utterance.pitch = 1.0;          // 0–2
  //               // You can pick a voice if available:
  //               // const voices = speechSynthesis.getVoices();
  //               // const preferred = voices.find(v => v.lang === 'en-US' && v.name.includes('Female'));
  //               // if (preferred) utterance.voice = preferred;
            
  //               speechSynthesis.cancel();       // stop any ongoing speech to avoid overlaps
  //               speechSynthesis.speak(utterance);
  //               },0);
  //               }
              
  //               // Reset the flag so subsequent typed inputs don’t trigger TTS
  //               this.lastInputWasVoice = false;

  //           }

  //           this.shouldScroll = true; // Ensure scroll after view update
  //         },
  //         error: (error) => {
  //           clearInterval(typingInterval);
  //           console.error("API Error:", error); // Log exact error message
  
  //           const index = this.chatHistory.indexOf(typingMessage);
  //           if (index !== -1) {
  //             this.chatHistory.splice(index, 1);  // Remove "Typing..."
  //           }
  
  //           const errorMessage = error.status === 429 
  //             ? "Your query is highly important to us. Currently we’re receiving a huge number of requests. Please wait a moment and try again.." 
  //             : "We are having some trouble right now. Please wait or try again later.";
  
  //           this.chatHistory.push({ text: errorMessage, isUser: false, isLoading:false });
  //         },
  //         complete : () => {}
  //       });
  
  //     this.userQuery = ''; // Clear input field
  //     this.chatInput.nativeElement.focus(); // Refocus input
  //     this.shouldScroll = true; // Ensure scroll after view update
  //   }
  // }

  sendMessage(): void {
  this.stopSpeech();

  const trimmedQuery = this.userQuery.trim();

   if (!trimmedQuery) {
    this.chatHistory.push({
      text: "Please enter a message or speak something.",
      isUser: false,
      isLoading: false
    });
    this.shouldScroll = true;
    this.cdr.detectChanges();
    return;
  }

  // Prevent duplicate sends if already processing
  if (this.chatHistory.some(m => m.isLoading)) return;

    if (trimmedQuery.length > 1000) {
    this.chatHistory.push({
      text: "Your message exceeds the 1000 character limit. Please shorten your message and try again.",
      isUser: false,
      isLoading: false
    });
    this.shouldScroll = true;
    this.cdr.detectChanges();
    return;
  }

  // 1️⃣ Add user message
  this.chatHistory.push({ text: trimmedQuery, isUser: true, isLoading: false });

  // 2️⃣ Create bot message immediately
  const botMessage = { text: '', isUser: false, isLoading: true, showStopButton: false, showResumeButton: false, pausedText: '',
  pausedCharIndex: 0,isPlaying: false };
  this.chatHistory.push(botMessage);
  this.shouldScroll = true;
  this.cdr.detectChanges(); // render immediately

  // 3️⃣ Animate "Thinking..."
  let dotCount = 0;
  const baseText = 'Thinking';
  const typingInterval = setInterval(() => {
    dotCount = (dotCount + 1) % 4;
    botMessage.text = baseText + '.'.repeat(dotCount);
    this.cdr.markForCheck();
    this.shouldScroll = true;
  }, 500);

  const TIMEOUT_DURATION = 30000; // 30 seconds

  // 4️⃣ Send request to backend
  this.http.post<{ response: string }>('http://localhost:33915/mdb/GetChatbotResponse/', { message: trimmedQuery }, { withCredentials: true })
    .pipe(timeout(TIMEOUT_DURATION),
      catchError(error => {
        clearInterval(typingInterval);
        console.error("API Error:", error);

        botMessage.isLoading = false;
        botMessage.text = error.name === 'TimeoutError'
          ? "The request took too long. Please try again later."
          : "We are having some trouble right now. Please try again later.";
        this.shouldScroll = true;
        this.cdr.detectChanges();
        return of(null);
      })
    )
    .subscribe({
      next: (data) => {
        clearInterval(typingInterval);

        if (data) {
          botMessage.text = data.response;
          botMessage.isLoading = false;
          botMessage.pausedText = data.response.trim();
          this.shouldScroll = true;
          this.cdr.detectChanges();

          // 5️⃣ TTS if last input was voice
          if (this.lastInputWasVoice && data.response?.trim()) {
            botMessage.showStopButton = true;
            this.cdr.detectChanges();

            setTimeout(() => {
              this.stopSpeech(this.currentPlayingMessage);
              const utterance = new SpeechSynthesisUtterance(data.response.trim());
              utterance.lang = 'en-US';
              utterance.rate = 1.0;
              utterance.pitch = 1.0;

              this.currentPlayingMessage = botMessage;
              botMessage.showStopButton = true;
              botMessage.showResumeButton = false;
              botMessage.isPlaying = true;

              speechSynthesis.cancel();
              utterance.onboundary = (event) => {
                botMessage.pausedCharIndex = event.charIndex;     
                };
              utterance.onend = () => {
              botMessage.showResumeButton = false;
              botMessage.showStopButton = false;
              botMessage.isPlaying = false;
              this["currentPlayingMessage"] = null;
              this.cdr.detectChanges();
             };

              speechSynthesis.speak(utterance);
            }, 0);
          }
        }

        this.lastInputWasVoice = false;
      },
      error: (error) => {
        clearInterval(typingInterval);
        console.error("API Error:", error);

        botMessage.isLoading = false;
        botMessage.text = error.status === 429
          ? "Your query is highly important to us. Currently we’re receiving a huge number of requests. Please wait a moment and try again."
          : "We are having some trouble right now. Please wait or try again later.";

        this.shouldScroll = true;
        this.cdr.detectChanges();
      }
    });

  // 6️⃣ Clear input field and refocus
  this.userQuery = '';
  this.chatInput.nativeElement.focus();
  this.shouldScroll = true;
}


  @HostListener('document:click', ['$event'])
  closeChatOnOutsideClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    if (!target.closest('.chat-interface') && !target.closest('.chatbot-icon')&&
    !target.closest('.stop-btn')) {
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

stopSpeech(message?: any): void {
  speechSynthesis.cancel();

  if (message) {
    if (message.isPlaying) {
      message.showStopButton = false;
      message.showResumeButton = true;
    }
    message.isPlaying = false;
  }

  this.currentPlayingMessage = null;
  this.cdr.detectChanges();
}

resumeSpeech(message: any): void {
  if (!message.pausedText || message.pausedCharIndex == null) return;

  if (this.currentPlayingMessage && this.currentPlayingMessage !== message) {
    this.stopSpeech(this.currentPlayingMessage);
  }

  const remaining = message.pausedText.substring(message.pausedCharIndex);
  const utterance = new SpeechSynthesisUtterance(remaining);

  message.utterance = utterance;
  message.showStopButton = true;
  message.showResumeButton = false;
  message.isPlaying = true;
  this.currentPlayingMessage = message;

  utterance.lang = 'en-US';
  utterance.rate = 1.0;
  utterance.pitch = 1.0;

  utterance.onboundary = () => { };

  utterance.onend = () => {
    message.showStopButton = false;
    message.showResumeButton = false;
    message.isPlaying = false;
    this.currentPlayingMessage = null; // keep reset ONLY here
    this.cdr.detectChanges();
  };

  speechSynthesis.speak(utterance);
  this.cdr.detectChanges();
}

}