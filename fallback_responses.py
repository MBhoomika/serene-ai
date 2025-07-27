import random

class FallbackResponses:
    @staticmethod
    def get_response(message):
        """Generate a context-aware fallback response"""
        # Convert message to lowercase for easier matching
        message = message.lower()
        
        # Define response categories with more detailed responses
        greetings = [
            "Hello! I'm here to support you. How are you feeling today? 🌟",
            "Hi there! I'm ready to listen and help. What's on your mind? 💫",
            "Welcome! I'm here to provide support and guidance. How can I assist you today? 🌸",
            "Hello! It's good to see you. How are you doing right now? 🌿",
            "Hi! I'm here to help you find peace and clarity. What would you like to talk about? 💝"
        ]
        
        stress_responses = [
            "I understand you might be feeling stressed. Let's try a simple breathing exercise together: Inhale for 4 counts, hold for 4, exhale for 4. Would you like to try it with me? 🌬️",
            "Stress can feel overwhelming. Let's break it down into smaller pieces. What's the most pressing concern on your mind right now? 🌸",
            "It's okay to feel stressed. Would you like to try a quick grounding technique? Name 5 things you can see, 4 things you can touch, 3 things you can hear, 2 things you can smell, and 1 thing you can taste. 🌟",
            "When stress feels heavy, remember to take things one step at a time. What's one small thing you can do right now to help yourself? 💫",
            "Stress is a natural response. Let's explore what's triggering it and find ways to manage it together. Would you like to talk about what's causing your stress? 🌿"
        ]
        
        anxiety_responses = [
            "I hear you're feeling anxious. Let's try a grounding exercise: Focus on your breath and notice the sensation of your feet on the ground. You're safe in this moment. 🌸",
            "Anxiety can be challenging, but you're not alone. Would you like to try a simple mindfulness exercise together? 🌟",
            "When anxiety feels overwhelming, remember that this feeling will pass. Let's focus on the present moment. What's one thing you can see or hear right now? 💫",
            "Anxiety often comes from worrying about the future. Let's bring our attention back to the present. Would you like to try a calming visualization? 🌿",
            "I understand anxiety can be difficult. Let's break it down: What's the smallest step you can take right now to feel more at ease? 💝"
        ]
        
        sadness_responses = [
            "I'm sorry you're feeling down. Your feelings are valid and important. Would you like to talk about what's troubling you? 🌸",
            "It's okay to feel sad. I'm here to listen and support you. What's on your mind? 🌟",
            "Sadness can feel heavy, but you don't have to carry it alone. Would you like to share what's weighing on your heart? 💫",
            "I hear your sadness. Let's explore what might help you feel better. What usually brings you comfort? 🌿",
            "Your feelings matter. Would you like to talk about what's causing your sadness? I'm here to listen without judgment. 💝"
        ]
        
        gratitude_responses = [
            "That's wonderful! Practicing gratitude can be very uplifting. What else are you thankful for today? 🌟",
            "I'm glad you're feeling grateful. Focusing on the positive can help shift our perspective. Would you like to share more? 💫",
            "Gratitude is a powerful emotion. Let's explore it further. What small things in your life bring you joy? 🌸",
            "That's a beautiful thing to be grateful for. Would you like to try listing three more things you appreciate? 🌿",
            "Gratitude can be a source of strength. What other positive aspects of your life come to mind? 💝"
        ]
        
        sleep_responses = [
            "Having trouble sleeping? Let's try a relaxation technique: Tense and relax each muscle group, starting from your toes and moving up to your head. Would you like to try it? 🌙",
            "Sleep is important for our wellbeing. Would you like some tips for creating a peaceful bedtime routine? 💫",
            "When sleep is difficult, try focusing on your breath. Inhale slowly through your nose, exhale through your mouth. Let's practice together. 🌟",
            "A good night's sleep can make a big difference. What's your current bedtime routine like? 🌸",
            "Sleep troubles can be frustrating. Would you like to explore some relaxation techniques together? 🌿"
        ]
        
        exercise_responses = [
            "Physical movement can be great for mental health. Would you like some gentle exercise suggestions? 🚶‍♂️",
            "Exercise is wonderful for both body and mind. What kind of movement do you enjoy? 🌟",
            "Even a short walk can help clear your mind. Would you like to try some simple stretches? 💫",
            "Movement can help shift our energy. What activities make you feel good? 🌸",
            "Let's get that energy flowing! Would you like some suggestions for mindful movement? 🌿"
        ]
        
        meditation_responses = [
            "Would you like to try a brief guided meditation? Let's start with three deep breaths together. 🧘‍♂️",
            "Meditation can help find inner peace. Shall we do a quick mindfulness exercise? 🌟",
            "Let's take a moment to be present. Would you like to try a simple breathing exercise? 💫",
            "Mindfulness can help ground us. Would you like to try focusing on your breath for a moment? 🌸",
            "Let's practice being in the present. Would you like to try a short meditation together? 🌿"
        ]
        
        general_support = [
            "I'm here to listen and support you. What would you like to talk about? 🌟",
            "Your feelings matter. Would you like to share more about what's on your mind? 💫",
            "I'm here to help you find clarity and peace. What's troubling you? 🌸",
            "Let's explore what's on your mind together. What would you like to discuss? 🌿",
            "I'm here to support you. What's the most important thing you'd like to talk about right now? 💝"
        ]
        
        # Check for keywords and return appropriate response
        if any(word in message for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon']):
            return random.choice(greetings)
        elif any(word in message for word in ['stress', 'overwhelm', 'pressure', 'stressed']):
            return random.choice(stress_responses)
        elif any(word in message for word in ['anxious', 'worry', 'nervous', 'anxiety']):
            return random.choice(anxiety_responses)
        elif any(word in message for word in ['sad', 'down', 'depressed', 'unhappy']):
            return random.choice(sadness_responses)
        elif any(word in message for word in ['thank', 'grateful', 'appreciate', 'thanks']):
            return random.choice(gratitude_responses)
        elif any(word in message for word in ['sleep', 'tired', 'insomnia', 'exhausted']):
            return random.choice(sleep_responses)
        elif any(word in message for word in ['exercise', 'workout', 'yoga', 'physical']):
            return random.choice(exercise_responses)
        elif any(word in message for word in ['meditate', 'meditation', 'mindful', 'mindfulness']):
            return random.choice(meditation_responses)
        else:
            return random.choice(general_support) 