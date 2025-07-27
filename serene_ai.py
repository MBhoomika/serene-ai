import os
from datetime import datetime
import time
import random
import re
from fallback_responses import FallbackResponses
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
import logging

class QuotesManager:
    def __init__(self):
        self.quotes = [
            {
                "text": "The greatest glory in living lies not in never falling, but in rising every time we fall.",
                "author": "Nelson Mandela"
            },
            {
                "text": "The way to get started is to quit talking and begin doing.",
                "author": "Walt Disney"
            },
            {
                "text": "Your time is limited, so don't waste it living someone else's life.",
                "author": "Steve Jobs"
            },
            {
                "text": "If life were predictable it would cease to be life, and be without flavor.",
                "author": "Eleanor Roosevelt"
            },
            {
                "text": "If you look at what you have in life, you'll always have more.",
                "author": "Oprah Winfrey"
            },
            {
                "text": "If you set your goals ridiculously high and it's a failure, you will fail above everyone else's success.",
                "author": "James Cameron"
            },
            {
                "text": "Life is what happens when you're busy making other plans.",
                "author": "John Lennon"
            },
            {
                "text": "Spread love everywhere you go. Let no one ever come to you without leaving happier.",
                "author": "Mother Teresa"
            },
            {
                "text": "When you reach the end of your rope, tie a knot in it and hang on.",
                "author": "Franklin D. Roosevelt"
            },
            {
                "text": "Always remember that you are absolutely unique. Just like everyone else.",
                "author": "Margaret Mead"
            }
        ]
        self.current_quote_index = 0
        self.last_quote_change = time.time()
        self.quote_change_interval = 10  # seconds

    def get_current_quote(self):
        """Get the current quote and update if enough time has passed"""
        current_time = time.time()
        if current_time - self.last_quote_change >= self.quote_change_interval:
            self._update_quote()
        return self._format_quote(self.quotes[self.current_quote_index])

    def _update_quote(self):
        """Update to the next quote in the sequence"""
        self.current_quote_index = (self.current_quote_index + 1) % len(self.quotes)
        self.last_quote_change = time.time()

    def _format_quote(self, quote):
        """Format the quote with proper punctuation and attribution"""
        return f'"{quote["text"]}" - {quote["author"]}'

    def get_new_quote(self):
        """Force get a new quote regardless of time elapsed"""
        self._update_quote()
        return self._format_quote(self.quotes[self.current_quote_index])

class SereneAI:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.chat_history_ids = None
        self.quotes_manager = QuotesManager()  # Initialize quotes manager
        self._initialize_model()
        
        # Predefined response templates for different scenarios
        self.response_templates = {
            'greeting': [
                "Hello! I'm here to support you. How are you feeling today?",
                "Hi there! I'm glad you're here. How can I help you today?",
                "Welcome! I'm here to listen and support you. What's on your mind?"
            ],
            'emotional_support': [
                "I understand you're feeling {emotion}. It's okay to feel this way. Would you like to talk about what's on your mind?",
                "I hear you're feeling {emotion}. That must be difficult. I'm here to listen and support you.",
                "It sounds like you're going through a tough time. Remember, it's okay to feel {emotion}. Would you like to share more?"
            ],
            'work_stress': [
                "I understand that dealing with workplace conflicts can be challenging. Would you like to talk about what happened?",
                "It sounds like you're feeling upset about what happened at work. That's completely valid. Would you like to discuss how you're feeling?",
                "Workplace situations can be difficult to handle. I'm here to listen and help you process your feelings."
            ],
            'stress_management': [
                "When feeling stressed, try taking a few deep breaths. Inhale for 4 counts, hold for 4, exhale for 4. Would you like to try this together?",
                "Stress can be overwhelming. Let's break down what's bothering you into smaller, manageable pieces. What's the most pressing concern?",
                "Remember to be kind to yourself during stressful times. What's one small thing you can do right now to take care of yourself?"
            ],
            'mindfulness': [
                "Let's take a moment to be present. What's one thing you can notice right now?",
                "Mindfulness can help ground us in the present moment. Would you like to try a simple breathing exercise?",
                "Being present can help reduce stress. What's something you're grateful for in this moment?"
            ],
            'gratitude': [
                "Practicing gratitude can be very uplifting. What's something positive that happened today?",
                "Focusing on the good things in life can help shift our perspective. What are you thankful for?",
                "Gratitude can help us find joy in everyday moments. What's one small thing that made you smile today?"
            ],
            'self_care': [
                "Self-care is important for our well-being. What's one thing you can do today to take care of yourself?",
                "Remember to be gentle with yourself. What activities help you feel recharged?",
                "Taking time for yourself isn't selfish—it's necessary. What's your favorite way to practice self-care?"
            ]
        }
        
        # Intent keywords and their associated intents
        self.intent_keywords = {
            'stress': ['stress', 'overwhelmed', 'pressure', 'stressed', 'burnt out', 'tension', 'anxious'],
            'anxiety': ['anxious', 'worry', 'nervous', 'anxiety', 'scared', 'panic', 'fear'],
            'depression': ['depressed', 'sad', 'down', 'hopeless', 'empty', 'low', 'worthless'],
            'work_stress': ['boss', 'work', 'job', 'colleague', 'manager', 'shouted', 'yelled'],
            'mindfulness': ['present', 'mindful', 'meditation', 'breath', 'ground', 'calm', 'peace'],
            'gratitude': ['thankful', 'grateful', 'appreciate', 'blessed', 'fortunate', 'happy', 'joy'],
            'self_care': ['self-care', 'care', 'rest', 'recharge', 'relax', 'unwind', 'break']
        }
        
        # Emotional keywords and their associated emotions
        self.emotion_keywords = {
            'happy': ['happy', 'joy', 'excited', 'content', 'peaceful', 'grateful', 'thankful'],
            'sad': ['sad', 'down', 'depressed', 'lonely', 'hurt', 'empty', 'hopeless'],
            'angry': ['angry', 'frustrated', 'irritated', 'annoyed', 'mad', 'upset', 'furious'],
            'anxious': ['anxious', 'worried', 'nervous', 'scared', 'fearful', 'panic', 'tense'],
            'stressed': ['stressed', 'overwhelmed', 'pressured', 'tension', 'burnt out', 'exhausted', 'drained']
        }
        
    def _initialize_model(self):
        """Initialize the AI model with proper configuration."""
        try:
            # Initialize tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
            
            # Initialize model with proper configuration
            model_config = {
                "pad_token_id": self.tokenizer.eos_token_id,
                "mean_resizing": False,  # Disable mean resizing
                "loss_type": "ForCausalLMLoss"  # Explicitly set loss type
            }
            
            self.model = AutoModelForCausalLM.from_pretrained(
                "microsoft/DialoGPT-medium",
                **model_config
            )
            
            # Add special tokens for better conversation handling
            special_tokens = {
                'pad_token': '[PAD]',
                'bos_token': '[BOS]',
                'eos_token': '[EOS]',
                'sep_token': '[SEP]'
            }
            self.tokenizer.add_special_tokens(special_tokens)
            self.model.resize_token_embeddings(len(self.tokenizer))
            
            # Fine-tune the model with our training data
            self._fine_tune_model()
            
            logging.info("✅ SereneAI initialized successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize AI model: {str(e)}")
            return False
    
    def _fine_tune_model(self):
        """Fine-tune the model with expanded domain-specific data"""
        try:
            # Define comprehensive training data for mental health support
            training_data = [
                # Stress and Anxiety Scenarios
                {
                    "input": "I'm feeling stressed about work deadlines",
                    "output": "I understand work deadlines can be overwhelming. Let's break this down into manageable steps. Would you like to try a quick breathing exercise first?"
                },
                {
                    "input": "I'm anxious about my presentation tomorrow",
                    "output": "Presentation anxiety is common. Let's practice some grounding techniques. What's one thing you can see in your environment right now?"
                },
                {
                    "input": "I'm overwhelmed with everything on my plate",
                    "output": "It sounds like you're carrying a lot. Let's prioritize together. What's the most pressing thing we can address right now?"
                },
                
                # Gratitude and Positivity
                {
                    "input": "I'm grateful for my supportive friends",
                    "output": "That's wonderful! Strong friendships are precious. What specific ways do your friends support you?"
                },
                {
                    "input": "I appreciate the small things in life",
                    "output": "That's a beautiful perspective. Would you like to share some of the small things that bring you joy?"
                },
                {
                    "input": "I'm thankful for my health",
                    "input": "How can I manage my stress?",
                    "output": "There are several ways to manage stress. Would you like to try a mindfulness exercise or discuss specific stress management techniques?"
                },
                {
                    "input": "I need help with anxiety",
                    "output": "I understand anxiety can be challenging. Let's explore some coping strategies together. Would you like to try a grounding exercise?"
                },
                {
                    "input": "I want to practice mindfulness",
                    "output": "Mindfulness is a great practice. Let's start with a simple breathing exercise. Would you like to try it together?"
                }
            ]
            
            # Convert training data to model inputs
            inputs = []
            for example in training_data:
                prompt = f"User: {example['input']}\nAI: {example['output']}"
                inputs.append(self.tokenizer.encode(prompt, return_tensors='pt'))
            
            # Fine-tune the model
            self.model.train()
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=5e-5)
            
            for input_ids in inputs:
                outputs = self.model(input_ids, labels=input_ids)
                loss = outputs.loss
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()
            
            self.model.eval()
            logging.info("Model fine-tuning completed successfully")
            
        except Exception as e:
            logging.error(f"Error during model fine-tuning: {str(e)}")
    
    def get_response(self, message: str) -> str:
        """Get a response from the AI model with improved context awareness"""
        try:
            # Clean and normalize the message
            message = message.lower().strip()
            
            # First try to use the AI model
            if self.model and self.tokenizer:
                try:
                    # Create a context-aware prompt
                    prompt = self._create_prompt(message)
                    
                    # Encode the prompt
                    input_ids = self.tokenizer.encode(prompt + self.tokenizer.eos_token, return_tensors='pt')
                    
                    # Generate response with improved parameters
                    output = self.model.generate(
                        input_ids,
                        max_length=150,
                        num_return_sequences=1,
                        no_repeat_ngram_size=2,
                        do_sample=True,
                        top_k=50,
                        top_p=0.95,
                        temperature=0.7,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                    
                    # Decode and clean the response
                    response = self.tokenizer.decode(output[0], skip_special_tokens=True)
                    response = self._clean_response(response, message)
                    
                    # Only use the model's response if it's meaningful
                    if len(response) > 10 and not response.startswith(('I don\'t know', 'I\'m not sure')):
                        return response
                        
                except Exception as e:
                    logging.error(f"Error generating AI response: {str(e)}")
            
            # If AI model fails or response is not meaningful, use contextual responses
            intent = self._analyze_intent(message)
            emotion = self._analyze_emotion(message)
            
            # Generate contextual response
            contextual_response = self._generate_response(message, intent, emotion)
            if contextual_response:
                return contextual_response
            
            # If all else fails, use a simple fallback with a quote
            return f"I'm here to listen and support you. How can I help you today? 🌸\n\n💭 {self.quotes_manager.get_current_quote()}"
            
        except Exception as e:
            logging.error(f"Error in get_response: {str(e)}")
            return f"I'm here to listen and support you. How can I help you today? 🌸\n\n💭 {self.quotes_manager.get_current_quote()}"
    
    def _create_prompt(self, message: str) -> str:
        """Create a context-aware prompt for the AI model with improved context"""
        # Analyze intent and emotion
        intent = self._analyze_intent(message)
        emotion = self._analyze_emotion(message)
        
        # Create a detailed context
        context = f"""You are SereneAI, a mental health support companion. The user is feeling {emotion} and wants to discuss {intent}.
Your role is to provide empathetic, supportive, and helpful responses while maintaining a professional and caring tone.
Focus on active listening, validation of feelings, and offering practical support when appropriate.
User: {message}
AI:"""
        
        return context
    
    def _analyze_intent(self, message: str) -> str:
        """Analyze the intent of the user's message with improved accuracy"""
        message = message.lower().strip()
        
        # Check for specific patterns first
        if any(word in message for word in ['thank', 'thanks', 'grateful', 'appreciate']):
            return 'gratitude'
        
        if any(word in message for word in ['meditate', 'meditation', 'mindful', 'present', 'breath', 'breathe']):
            return 'mindfulness'
        
        if any(word in message for word in ['work', 'job', 'boss', 'colleague', 'meeting', 'deadline']):
            return 'work_stress'
        
        if any(word in message for word in ['stress', 'overwhelm', 'pressure', 'tension']):
            return 'stress'
        
        if any(word in message for word in ['anxious', 'worry', 'nervous', 'panic']):
            return 'anxiety'
        
        if any(word in message for word in ['sad', 'depressed', 'down', 'hopeless']):
            return 'depression'
        
        if any(word in message for word in ['help', 'support', 'advice', 'guidance']):
            return 'support'
        
        if any(word in message for word in ['hello', 'hi', 'hey', 'greeting']):
            return 'greeting'
        
        return 'general'
    
    def _analyze_emotion(self, message: str) -> str:
        """Analyze the emotion in the user's message with improved accuracy"""
        message = message.lower().strip()
        
        # Check for specific patterns first
        if any(word in message for word in ['happy', 'joy', 'excited', 'grateful', 'thankful']):
            return 'happy'
        
        if any(word in message for word in ['sad', 'depressed', 'down', 'hopeless', 'lonely']):
            return 'sad'
        
        if any(word in message for word in ['angry', 'frustrated', 'irritated', 'annoyed', 'mad']):
            return 'angry'
        
        if any(word in message for word in ['anxious', 'worried', 'nervous', 'scared', 'fearful']):
            return 'anxious'
        
        if any(word in message for word in ['stressed', 'overwhelmed', 'pressured', 'tension', 'burnt out']):
            return 'stressed'
        
        if any(word in message for word in ['calm', 'peaceful', 'relaxed', 'content', 'serene']):
            return 'calm'
        
        return 'neutral'
    
    def _generate_response(self, message: str, intent: str, emotion: str) -> str:
        """Generate a contextual response based on intent and emotion"""
        message = message.lower().strip()
        
        # Handle specific patterns first
        if any(word in message for word in ['hello', 'hi', 'hey']):
            return random.choice([
                "Hello! I'm here to support you. How are you feeling today? 🌸",
                "Hi there! I'm glad you're here. How can I help you today? 💫",
                "Welcome! I'm here to listen and support you. What's on your mind? 🌟"
            ])
        
        if any(word in message for word in ['thank', 'thanks']):
            return "You're welcome! Is there anything else I can help you with? 🌸"
        
        if any(word in message for word in ['yes', 'yeah', 'sure', 'okay']):
            return "Great! Let's continue. What would you like to explore? 💫"
        
        if any(word in message for word in ['no', 'nope', 'not really']):
            return "That's okay. Is there something else you'd like to talk about? 🌿"
        
        # Handle specific intents with more context
        if intent == 'gratitude':
            return random.choice([
                "That's wonderful! Practicing gratitude can be very uplifting. What else are you thankful for today? 🌟",
                "I'm glad you're feeling grateful. Focusing on the positive can help shift our perspective. Would you like to share more? 💫",
                "Gratitude is a powerful emotion. Let's explore it further. What small things in your life bring you joy? 🌸"
            ])
        
        if intent == 'mindfulness':
            return random.choice([
                "Let's take a moment to be present. Would you like to try a simple breathing exercise? 🧘‍♂️",
                "Mindfulness can help ground us in the present moment. Let's focus on our breath together. 🌟",
                "Being present can help reduce stress. Would you like to try a quick mindfulness exercise? 💫"
            ])
        
        if intent == 'work_stress':
            return random.choice([
                "I understand that dealing with workplace stress can be challenging. Would you like to talk about what happened?",
                "It sounds like you're feeling stressed about work. That's completely valid. Would you like to discuss how you're feeling?",
                "Workplace situations can be difficult to handle. I'm here to listen and help you process your feelings."
            ])
        
        # Handle emotions with more context
        if emotion == 'happy':
            return random.choice([
                "I'm glad you're feeling positive! What's contributing to your happiness today? 🌸",
                "That's wonderful to hear! Would you like to explore what's bringing you joy? 🌟",
                "Happiness is beautiful to share. What's making you feel good right now? 💫"
            ])
        
        if emotion == 'sad':
            return random.choice([
                "I hear you're feeling down. Your feelings are valid and important. Would you like to talk about what's troubling you? 🌸",
                "It's okay to feel sad. I'm here to listen and support you. What's on your mind? 🌟",
                "Sadness can feel heavy, but you don't have to carry it alone. Would you like to share what's weighing on your heart? 💫"
            ])
        
        if emotion == 'anxious':
            return random.choice([
                "I understand you're feeling anxious. Let's try a grounding exercise together. What's one thing you can see right now? 🌸",
                "Anxiety can be challenging, but you're not alone. Would you like to try a simple breathing exercise? 🌟",
                "When anxiety feels overwhelming, remember that this feeling will pass. Let's focus on the present moment. 💫"
            ])
        
        # Handle specific keywords in the message
        if 'meditation' in message:
            return "Would you like to try a guided meditation? I can help you get started with a simple breathing exercise. 🧘‍♂️"
        
        if 'breath' in message or 'breathe' in message:
            return "Let's practice breathing together. Inhale for 4 counts, hold for 4, exhale for 4. Would you like to try it? 🌬️"
        
        if 'help' in message:
            return "I'm here to support you. What specific aspect of your well-being would you like to focus on? 🌸"
        
        if 'how are you' in message:
            return "I'm here to support you. How are you feeling today? 🌟"
        
        # If no specific pattern is matched, return a context-aware fallback
        return random.choice([
            "I'm here to listen and support you. What would you like to talk about? 🌸",
            "Your feelings matter. Would you like to share more about what's on your mind? 🌟",
            "Let's explore what's on your mind together. What would you like to discuss? 💫"
        ])
    
    def _clean_response(self, response: str, original_message: str) -> str:
        """Clean up the generated response"""
        try:
            # Remove any repeated phrases
            response = re.sub(r'(\b\w+\b)(?:\s+\1\b)+', r'\1', response)
            
            # Remove any URLs or special characters
            response = re.sub(r'http\S+|www.\S+', '', response)
            response = re.sub(r'[^\w\s.,!?-]', '', response)
            
            # Ensure the response is not too long
            if len(response) > 200:
                response = response[:200] + "..."
            
            # Add a period if the response doesn't end with punctuation
            if not response.endswith(('.', '!', '?', '...')):
                response += '.'
            
            return response
        except Exception as e:
            logging.error(f"Error cleaning response: {str(e)}")
            return "I understand you're reaching out. How can I support you today?"
    
    def _get_fallback_response(self, message: str) -> str:
        """Provide a simple fallback response based on message content"""
        message = message.lower()
        
        # Check for specific patterns
        if any(word in message for word in ['hello', 'hi', 'hey']):
            return random.choice(self.response_templates['greeting'])
        elif any(word in message for word in ['how are you', 'how\'s it going']):
            return "I'm here to support you. How are you feeling today?"
        elif any(word in message for word in ['thank', 'thanks']):
            return "You're welcome! Is there anything else I can help you with?"
        elif any(word in message for word in ['help', 'support']):
            return "I'm here to listen and support you. What's on your mind?"
        elif any(word in message for word in ['bye', 'goodbye', 'see you']):
            return "Take care! Remember, I'm here whenever you need someone to talk to. 🌸"
        else:
            return "I understand you're reaching out. How can I support you today?"

    def _update_user_info(self, message):
        """Update user information based on the message"""
        # This method can be enhanced to extract more user information
        # For now, it's a placeholder
        pass

    def _extract_name(self, message):
        name_patterns = [
            r"(?:i am|i'm|call me) ([a-z]+)",
            r"my name is ([a-z]+)",
            r"this is ([a-z]+)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1).capitalize()
        return None

    def start_activity(self, activity_type):
        """Start a specific guided activity"""
        activities = {
            "breathing": "Let's begin a calming breathing exercise. Find a comfortable position...",
            "meditation": "Welcome to this gentle meditation session. Let's start by getting comfortable...",
            "creativity": "Let's do something creative together. Do you have paper and colors nearby?",
            "stretching": "Let's do some gentle stretches. Make sure you have some space..."
        }
        
        return self.get_response(activities.get(activity_type, "Let's try a calming activity together..."))

    def handle_emotion(self, emotion):
        """Handle specific emotional states"""
        emotion_responses = {
            "anxiety": "I understand you're feeling anxious. Let's work through this together...",
            "sadness": "I hear that you're feeling sad. Know that it's okay to feel this way...",
            "stress": "When we're stressed, it helps to take things one step at a time...",
            "overwhelm": "Let's break things down into smaller, manageable pieces..."
        }
        
        return self.get_response(emotion_responses.get(emotion, "Tell me more about how you're feeling..."))

class DailyChallenge:
    def __init__(self):
        self.challenges = [
            {
                'title': '5-Minute Mindfulness',
                'description': 'Take 5 minutes to focus on your breath and observe your thoughts without judgment.',
                'icon': '🧘‍♂️'
            },
            {
                'title': 'Gratitude Journal',
                'description': 'Write down three things you are grateful for today.',
                'icon': '📝'
            },
            {
                'title': 'Kind Message',
                'description': 'Send a supportive message to someone you care about.',
                'icon': '💌'
            },
            {
                'title': 'Nature Connection',
                'description': 'Spend 10 minutes outside observing nature.',
                'icon': '🌿'
            },
            {
                'title': 'Self-Care Break',
                'description': 'Take a 15-minute break to do something that makes you feel good.',
                'icon': '💝'
            },
            {
                'title': 'Mindful Movement',
                'description': 'Do 5 minutes of gentle stretching or yoga.',
                'icon': '🌟'
            },
            {
                'title': 'Creative Expression',
                'description': 'Spend 10 minutes drawing, writing, or expressing yourself creatively.',
                'icon': '🎨'
            }
        ]
        
    def get_daily_challenge(self):
        # Use the day of the year to select a challenge, ensuring the same challenge appears on the same day
        day_of_year = datetime.now().timetuple().tm_yday
        challenge_index = day_of_year % len(self.challenges)
        return self.challenges[challenge_index]