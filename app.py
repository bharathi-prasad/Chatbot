from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import re
from datetime import datetime
import os
from intent_handler import IntentHandler 

app = Flask(__name__)
CORS(app,origins=['http://localhost:4200'])

import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'lms_db',
    'user': 'postgres',
    'password': 'prasad',
    'port': 5432
}

# Initialize intent handler
intent_handler = IntentHandler()

class DatabaseManager:
    def __init__(self):
        self.connection = None
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
    
    def close(self):
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                self.connection.commit()
                result = cursor.rowcount
            cursor.close()
            return result
        except Exception as e:
            print(f"Query execution error: {e}")
            self.connection.rollback()
            return None

db_manager = DatabaseManager()

def decrypt_customer_id(encrypted_data: str) -> int:
    """
    Decrypt the encrypted customer_id using AES with the same key and method as Java EncryptionUtil.
    """
    try:
        secret_key = "encryptionNarveePayload"
        # Generate SHA-256 hash of the secret key and take first 16 bytes
        key_bytes = hashlib.sha256(secret_key.encode('utf-8')).digest()[:16]
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        # Decode URL-safe base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        # Unpad decrypted bytes (PKCS7)
        decrypted_bytes = unpad(decrypted_bytes, AES.block_size)
        decrypted_str = decrypted_bytes.decode('utf-8')
        return int(decrypted_str)
    except Exception as e:
        print(f"Decryption error: {e}")
        raise ValueError("Invalid encrypted customer_id")

class ChatBot:
    def __init__(self):
        self.intent_handler = intent_handler
    
    def get_loan_sanction_details(self, loan_id, account_number):
        """
        Fetch loan sanction details using both loan_id AND loan_account_number
        """
        query = """
        SELECT
            loan_id,
            loan_account_number,
            amount_sanctioned,
            emi_amount,
            emi_due_date,
            number_of_emis,
            emi_start_date,
            emi_end_date,
            rate_of_interest,
            interest_type,
            status,
            loan_requested,
            payment_freqmuency,
            repayment_mode
        FROM loancraft.lms_loan_saction
        WHERE loan_id = %s AND loan_account_number = %s
        """

        result = db_manager.execute_query(query, (loan_id, account_number))

        if result:
            loan = result[0]
            return {
                'found': True,
                'loan_id': loan['loan_id'],
                'loan_account_number': loan['loan_account_number'],
                'amount_sanctioned': float(loan['amount_sanctioned']) if loan['amount_sanctioned'] else 0,
                'emi_amount': float(loan['emi_amount']) if loan['emi_amount'] else 0,
                'emi_due_date': loan['emi_due_date'].strftime('%Y-%m-%d') if loan['emi_due_date'] else 'N/A',
                'number_of_emis': int(loan['number_of_emis']) if loan['number_of_emis'] else 0,
                'emi_start_date': loan['emi_start_date'].strftime('%Y-%m-%d') if loan['emi_start_date'] else 'N/A',
                'emi_end_date': loan['emi_end_date'].strftime('%Y-%m-%d') if loan['emi_end_date'] else 'N/A',
                'rate_of_interest': float(loan['rate_of_interest']) if loan['rate_of_interest'] else 0,
                'interest_type': loan['interest_type'] or 'N/A',
                'status': loan['status'] or 'N/A',
                'loan_requested': float(loan['loan_requested']) if loan['loan_requested'] else 0,
                'payment_frequency': loan['payment_freqmuency'] or 'N/A',
                'repayment_mode': loan['repayment_mode'] or 'N/A'
            }
        return {'found': False}

    def get_loans_by_customer_id(self, customer_id):
        """
        Fetch all loan details for a customer using customer_id
        """
        try:
            decrypted_customer_id = decrypt_customer_id(customer_id)
        except ValueError as e:
            print(f"Error decrypting customer_id: {e}")
            return []

        query = """
        SELECT
            s.loan_id,
            s.loan_account_number,
            s.amount_sanctioned,
            s.emi_amount,
            s.emi_due_date,
            s.number_of_emis,
            s.emi_start_date,
            s.emi_end_date,
            s.rate_of_interest,
            s.interest_type,
            s.status,
            s.loan_requested,
            s.payment_freqmuency,
            s.repayment_mode,
            a.application_reference_id
        FROM loancraft.lms_loan_saction s
        JOIN loancraft.lms_applications a ON a.loan_id = s.loan_id
        WHERE a.customer_id = %s
        ORDER BY s.loan_id
        """

        result = db_manager.execute_query(query, (decrypted_customer_id,))

        if result:
            loans = []
            for loan in result:
                loans.append({
                    'found': True,
                    'loan_id': loan['loan_id'],
                    'loan_account_number': loan['loan_account_number'],
                    'application_reference_id': loan['application_reference_id'],
                    'amount_sanctioned': float(loan['amount_sanctioned']) if loan['amount_sanctioned'] else 0,
                    'emi_amount': float(loan['emi_amount']) if loan['emi_amount'] else 0,
                    'emi_due_date': loan['emi_due_date'].strftime('%Y-%m-%d') if loan['emi_due_date'] else 'N/A',
                    'number_of_emis': int(loan['number_of_emis']) if loan['number_of_emis'] else 0,
                    'emi_start_date': loan['emi_start_date'].strftime('%Y-%m-%d') if loan['emi_start_date'] else 'N/A',
                    'emi_end_date': loan['emi_end_date'].strftime('%Y-%m-%d') if loan['emi_end_date'] else 'N/A',
                    'rate_of_interest': float(loan['rate_of_interest']) if loan['rate_of_interest'] else 0,
                    'interest_type': loan['interest_type'] or 'N/A',
                    'status': loan['status'] or 'N/A',
                    'loan_requested': float(loan['loan_requested']) if loan['loan_requested'] else 0,
                    'payment_frequency': loan['payment_freqmuency'] or 'N/A',
                    'repayment_mode': loan['repayment_mode'] or 'N/A'
                })
            return loans
        return []

    def get_customer_name(self, customer_id):
        """
        Fetch customer name using customer_id
        """
        try:
            decrypted_customer_id = decrypt_customer_id(customer_id)
        except ValueError as e:
            print(f"Error decrypting customer_id: {e}")
            return None

        query = """
        SELECT first_name, last_name
        FROM loancraft.lms_customers_info
        WHERE customer_id = %s
        """

        result = db_manager.execute_query(query, (decrypted_customer_id,))

        if result:
            customer = result[0]
            first_name = customer['first_name'] or ''
            last_name = customer['last_name'] or ''
            return f"{first_name} {last_name}".strip()
        return None
    
    def get_loan_status(self, loan_id, account_number):
        """
        Get loan status information - wrapper for backward compatibility
        """
        return self.get_loan_sanction_details(loan_id, account_number)
    
    def save_chat_history(self, user_message, bot_response, session_id=None):
        query = """
        INSERT INTO chat_history (user_message, bot_response, session_id)
        VALUES (%s, %s, %s)
        """
        db_manager.execute_query(query, (user_message, bot_response, session_id))
    
    def format_loan_response(self, loan_data):
        """
        Format loan data into a user-friendly response
        """
        return f"""
📄 **Loan Sanction Details**

**Loan ID:** {loan_data['loan_id']}
**Account Number:** {loan_data['loan_account_number']}
**Status:** {loan_data['status'].upper()}

💰 **Financial Details:**
• **Amount Sanctioned:** ₹{loan_data['amount_sanctioned']:,.2f}
• **Loan Requested:** ₹{loan_data['loan_requested']:,.2f}
• **EMI Amount:** ₹{loan_data['emi_amount']:,.2f}
• **Number of EMIs:** {loan_data['number_of_emis']}

📅 **EMI Schedule:**
• **EMI Due Date:** {loan_data['emi_due_date']}
• **EMI Start Date:** {loan_data['emi_start_date']}
• **EMI End Date:** {loan_data['emi_end_date']}
• **Payment Frequency:** {loan_data['payment_frequency']}

📊 **Loan Terms:**
• **Interest Rate:** {loan_data['rate_of_interest']}%
• **Interest Type:** {loan_data['interest_type']}
• **Repayment Mode:** {loan_data['repayment_mode']}

Is there anything else I can help you with regarding your loan?
        """
    
    def process_message(self, message, session_id=None, customer_name=None):
        # Check if message contains both loan ID and account number patterns
        loan_id_pattern = r'\b(\d+)\b'  # General number pattern for loan ID
        account_pattern = r'\b(BHLPL\d+)\b'  # Account number pattern
        
        loan_id_matches = re.findall(loan_id_pattern, message)
        account_matches = re.findall(account_pattern, message.upper())
        
        # More specific keywords that indicate loan STATUS/TRACKING inquiry
        # Removed generic 'loan' keyword to avoid conflicts with FAQ
        loan_status_keywords = ['status', 'emi', 'sanction', 'due date', 'details', 'track', 'check', 'loan']
        
        # Additional patterns that specifically indicate status checking
        status_patterns = [
            r'check.*status',
            r'what.*status',
            r'loan.*status',
            r'status.*loan',
            r'track.*loan',
            r'loan.*details',
            r'emi.*details',
            r'sanction.*details',
            r'emi.*due.*date',
            r'loan.*due.*date',
            r'when.*emi.*due',
            r'when.*loan.*due'
        ]
        
        # Check for status-specific keywords
        has_status_keyword = any(keyword in message.lower() for keyword in loan_status_keywords)
        
        # Check for status-specific patterns
        has_status_pattern = any(re.search(pattern, message.lower()) for pattern in status_patterns)
        
        # Only treat as loan status inquiry if:
        # 1. Has specific status keywords OR status patterns
        # 2. AND EITHER has loan ID/account number OR no loan ID/account number (to support user context)
        is_status_inquiry = (has_status_keyword or has_status_pattern)
        
        if is_status_inquiry:
            # If both loan ID and account number are provided
            if loan_id_matches and account_matches:
                loan_id = loan_id_matches[0]
                account_number = account_matches[0]
                loan_details = self.get_loan_sanction_details(loan_id, account_number)
                if loan_details['found']:
                    response = self.format_loan_response(loan_details)
                else:
                    response = f"❌ No loan found with Loan ID '{loan_id}' and Account Number '{account_number}'. Please verify both details and try again."
            # If no loan ID/account number, try to get customer_id from session and fetch loans
            elif not loan_id_matches and not account_matches and session_id:
                # Here, session_id is assumed to be customer_id for simplicity
                loans = self.get_loans_by_customer_id(session_id)
                if loans:
                    response = ""
                    for loan in loans:
                        response += self.format_loan_response(loan) + "\n\n"
                else:
                    response = "❌ No loans found for your account. Please verify your details or contact support."
            # If partial info provided
            elif loan_id_matches and not account_matches:
                response = f"""
❌ **Missing Account Number**

You provided Loan ID: **{loan_id_matches[0]}**
Please also provide your **Account Number**.
                """
            elif account_matches and not loan_id_matches:
                response = f"""
❌ **Missing Loan ID**

You provided Account Number: **{account_matches[0]}**
Please also provide your **Loan ID** .
                """
            else:
                response = """
❌ **Both Loan ID and Account Number Required**

To check your loan details, please provide **both**:
• Your **Loan ID**
• Your **Account Number**
                """
        else:
            # Handle FAQ using intent handler for all other queries
            response = self.intent_handler.get_response(message, customer_name)
        
        # Save chat history
        self.save_chat_history(message, response, session_id)
        
        return response

# Initialize chatbot
chatbot = ChatBot()

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        customer_id = data.get('customer_id')  # New parameter for user context

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Use customer_id as session_id if provided, otherwise use session_id
        # This allows the chatbot to fetch user-specific loan data
        effective_session_id = customer_id or session_id

        # Fetch customer name if customer_id is provided
        customer_name = None
        if customer_id:
            customer_name = chatbot.get_customer_name(customer_id)

        response = chatbot.process_message(message, effective_session_id, customer_name)

        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/welcome', methods=['GET'])
def welcome():
    """
    API endpoint to get a personalized welcome message for signed-in user
    """
    try:
        customer_id = request.args.get('customer_id')

        if not customer_id:
            return jsonify({'error': 'customer_id is required'}), 400

        customer_name = chatbot.get_customer_name(customer_id)

        if customer_name:
            message = f"Welcome {customer_name}! I'm here to help you with your loan information and answer any questions you may have."
        else:
            message = "Welcome! I'm here to help you with your loan information and answer any questions you may have."

        return jsonify({
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/loan-details/<loan_id>/<account_number>', methods=['GET'])
def get_loan_details_api(loan_id, account_number):
    """
    API endpoint to get loan details by both loan_id and account_number
    """
    try:
        loan_details = chatbot.get_loan_sanction_details(loan_id, account_number)
        return jsonify(loan_details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/loan-status/<loan_id>/<account_number>', methods=['GET'])
def get_loan_status_api(loan_id, account_number):
    """
    Backward compatibility endpoint - now requires both parameters
    """
    try:
        loan_status = chatbot.get_loan_status(loan_id, account_number)
        return jsonify(loan_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emi-details/<loan_id>/<account_number>', methods=['GET'])
def get_emi_details_api(loan_id, account_number):
    """
    Specific endpoint for EMI details - requires both parameters
    """
    try:
        loan_details = chatbot.get_loan_sanction_details(loan_id, account_number)
        if loan_details['found']:
            emi_details = {
                'found': True,
                'loan_id': loan_details['loan_id'],
                'account_number': loan_details['loan_account_number'],
                'emi_amount': loan_details['emi_amount'],
                'emi_due_date': loan_details['emi_due_date'],
                'number_of_emis': loan_details['number_of_emis'],
                'emi_start_date': loan_details['emi_start_date'],
                'emi_end_date': loan_details['emi_end_date']
            }
        else:
            emi_details = {'found': False}
        
        return jsonify(emi_details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/db-test', methods=['GET'])
def test_database_connection():
    """
    Test endpoint to verify database connection and table structure
    """
    try:
        if not db_manager.connect():
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Test query to check if table exists and get sample data
        test_query = """
        SELECT 
            loan_id, 
            loan_account_number, 
            amount_sanctioned, 
            emi_amount, 
            emi_due_date, 
            number_of_emis 
        FROM loancraft.lms_loan_saction 
        LIMIT 5
        """
        
        result = db_manager.execute_query(test_query)
        
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Database connection and table access successful',
                'sample_data': [dict(row) for row in result]
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Could not fetch data from loancraft.lms_loan_saction table'
            }), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database connection
    if db_manager.connect():
        print("Database connected successfully")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Failed to connect to database")
