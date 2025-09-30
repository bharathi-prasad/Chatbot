import json
import re
from difflib import get_close_matches
from llm_handler import LLMHandler

class IntentHandler:
    def __init__(self):
        self.intents = self.load_intents()
        self.llm_handler = LLMHandler()
    
    def load_intents(self):
        """Load intents from JSON file"""
        intents_data = {
            "intents": [
                {
                    "tag": "greeting",
                    "patterns": [
                        "hello", "hi", "hey", "good morning", "good afternoon", 
                        "good evening", "greetings", "what's up", "howdy"
                    ],
                    "responses": [
                        "Hello! I'm here to help you with loan information and FAQs. How can I assist you today?",
                        "Hi there! I can help you check loan status or answer questions about our services.",
                        "Greetings! I'm your loan assistant. What would you like to know?"
                    ]
                },
                {
                    "tag": "goodbye",
                    "patterns": [
                        "bye", "goodbye", "see you later", "farewell", "talk to you later",
                        "catch you later", "until next time", "take care"
                    ],
                    "responses": [
                        "Goodbye! Feel free to reach out if you need any assistance with your loan applications.",
                        "Take care! I'm here whenever you need help with loan-related queries.",
                        "See you later! Have a great day!"
                    ]
                },
                {
                    "tag": "loan_types",
                    "patterns": [
                        "what types of loans do you offer", "loan types", "kinds of loans",
                        "available loans", "loan options", "what loans can I get"
                    ],
                    "responses": [
                        "We offer several types of loans:\n• Home Loans - for purchasing or refinancing property\n• Personal Loans - for personal expenses\n• Business Loans - for business investments\n• Car Loans - for vehicle purchases\n• Education Loans - for educational expenses\n\nWould you like more information about any specific loan type?"
                    ]
                },
                {
                    "tag": "loan_requirements",
                    "patterns": [
                        "what are the requirements", "loan requirements", "eligibility criteria",
                        "what documents do I need", "application requirements", "how to qualify"
                    ],
                    "responses": [
                        "General loan requirements include:\n• Valid ID proof\n• Income verification (salary slips, tax returns)\n• Bank statements (last 3-6 months)\n• Credit score check\n• Employment verification\n• Property documents (for secured loans)\n\nSpecific requirements may vary by loan type. Would you like details for a particular loan?"
                    ]
                },
                {
                    "tag": "interest_rates",
                    "patterns": [
                        "what are your interest rates", "interest rates", "loan rates",
                        "how much interest", "APR", "annual percentage rate"
                    ],
                    "responses": [
                        "Our current interest rates are:\n• Home Loans: 6.5% - 8.5% APR\n• Personal Loans: 10% - 18% APR\n• Business Loans: 8% - 15% APR\n• Car Loans: 7% - 12% APR\n• Education Loans: 8% - 14% APR\n\nRates may vary based on credit score, loan amount, and term. Contact us for personalized rates!"
                    ]
                },
                {
                    "tag": "application_process",
                    "patterns": [
                        "how to apply", "application process", "how do I apply for a loan",
                        "loan application", "apply for loan", "application steps"
                    ],
                    "responses": [
                        "Our loan application process:\n1. Choose your loan type\n2. Fill out the online application\n3. Submit required documents\n4. Wait for initial review (24-48 hours)\n5. Credit check and verification\n6. Approval decision\n7. Loan disbursement\n\nYou can start your application on our website or visit any branch office."
                    ]
                },
                {
                    "tag": "processing_time",
                    "patterns": [
                        "how long does it take", "processing time", "approval time",
                        "when will I get approval", "how fast", "timeline"
                    ],
                    "responses": [
                        "Processing times vary by loan type:\n• Personal Loans: 1-3 business days\n• Car Loans: 2-5 business days\n• Home Loans: 15-30 business days\n• Business Loans: 7-14 business days\n• Education Loans: 5-10 business days\n\nPre-approval can be faster. Complete documentation speeds up the process!"
                    ]
                },
                {
                    "tag": "loan_status_help",
                    "patterns": [
                        "how to check status", "check loan status", "track application",
                        "application status", "where is my application", "status check"
                    ],
                    "responses": [
                        "To check your loan status:\n1. Provide your Loan ID (format: LN followed by 3 digits)\n2. I'll instantly fetch your current status\n3. You can also check online using your application number\n\nExample: 'Check status for LN001' or just type your loan ID!"
                    ]
                },
                {
                    "tag": "contact_info",
                    "patterns": [
                        "contact information", "phone number", "email", "address",
                        "how to contact", "reach out", "customer service"
                    ],
                    "responses": [
                        "Contact Information:\n📞 Phone: 1-937-LOAN-HELP (1-937-829-1334)\n📧 Email: support@narvee.com\n🏢 Address: 17440 Dallas Pkwy,Dalls, TX 75287\n⏰ Hours: Mon-Fri 9AM-6PM, Sat 9AM-2PM\n\nYou can also chat with us here anytime!"
                    ]
                },
                {
                    "tag": "thanks",
                    "patterns": [
                        "thank you", "thanks", "appreciate it", "grateful",
                        "much appreciated", "thanks a lot"
                    ],
                    "responses": [
                        "You're welcome! I'm glad I could help. Is there anything else you'd like to know?",
                        "Happy to help! Feel free to ask if you have more questions.",
                        "You're very welcome! I'm here whenever you need assistance."
                    ]
                },
                {
                    "tag": "default",
                    "patterns": [],
                    "responses": [
                        "I'm sorry, I didn't understand that. I can help you with:\n• Loan status checking (provide your loan ID)\n• Information about loan types\n• Application process\n• Interest rates\n• Contact information\n\nCould you please rephrase your question?"
                    ]
                }
            ]
        }
        return intents_data
    
    def preprocess_text(self, text):
        """Clean and preprocess text"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    def calculate_similarity(self, user_input, pattern):
        """Calculate similarity between user input and pattern"""
        user_words = set(self.preprocess_text(user_input).split())
        pattern_words = set(self.preprocess_text(pattern).split())
        
        if not pattern_words:
            return 0
        
        intersection = user_words.intersection(pattern_words)
        return len(intersection) / len(pattern_words)
    
    def find_best_intent(self, user_input):
        """Find the best matching intent"""
        best_match = None
        best_score = 0
        threshold = 0.3
        
        for intent in self.intents["intents"]:
            if intent["tag"] == "default":
                continue
                
            for pattern in intent["patterns"]:
                score = self.calculate_similarity(user_input, pattern)
                
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = intent
                    
                # Also check for partial matches
                if pattern in user_input.lower():
                    score = 0.8
                    if score > best_score:
                        best_score = score
                        best_match = intent
        
        return best_match, best_score
    
    def get_response(self, user_input, customer_name=None):
        """Get response for user input"""
        intent, confidence = self.find_best_intent(user_input)

        if intent:
            import random
            response = random.choice(intent["responses"])
            # Customize greeting if customer_name is provided
            if intent["tag"] == "greeting" and customer_name:
                response = f"Welcome {customer_name}! How can I assist you today?"
            # Add handling for "what's my name" or similar queries
            if customer_name and re.search(r"\b(what('?s| is) my name|who am i|my name)\b", user_input.lower()):
                response = f"Your name is {customer_name}."
            return response
        else:
            # Try LLM for queries not covered by intents
            if self.llm_handler.is_available():
                try:
                    llm_response = self.llm_handler.generate_response(user_input)
                    return llm_response
                except Exception as e:
                    print(f"LLM error: {e}")
                    # Fallback to default response if LLM fails

            # Return default response
            default_intent = next(i for i in self.intents["intents"] if i["tag"] == "default")
            return default_intent["responses"][0]
    
    def add_intent(self, tag, patterns, responses):
        """Add new intent dynamically"""
        new_intent = {
            "tag": tag,
            "patterns": patterns,
            "responses": responses
        }
        self.intents["intents"].append(new_intent)
    
    def get_all_intents(self):
        """Get all available intents"""
        return [intent["tag"] for intent in self.intents["intents"]]
