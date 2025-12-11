declare interface SpeechRecognitionEvent extends Event {
  resultIndex: number;  // <-- add this
  results: SpeechRecognitionResultList;
}

declare interface SpeechRecognitionError {
  error: string;
  message: string;
}

declare var webkitSpeechRecognition: any;
