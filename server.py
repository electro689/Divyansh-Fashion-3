from flask import Flask, request, jsonify
from flask_cors import CORS
import razorpay
import os
import random

app = Flask(__name__)
# Enable CORS so your index2.html frontend can securely ask this server for transaction IDs
CORS(app)

# ==========================================
# 1. ADD YOUR RAZORPAY KEYS HERE (Test Mode)
# ==========================================
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'YOUR_TEST_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'YOUR_TEST_KEY_SECRET')

# Safely initialize the Razorpay Client
try:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception:
    client = None

@app.route('/create_order', methods=['POST'])
def create_order():
    """
    Endpoint perfectly shaped to be called by your frontend when "Complete Purchase" is clicked.
    It returns a highly secure 'order_id' which index2.html uses to trigger the pop-up modal.
    """
    try:
        data = request.json
        amount = int(data.get('amount', 0)) * 100 # Razorpay requires paise (rupees * 100)
        currency = data.get('currency', 'INR')

        # If keys are valid, create the real financial order
        if client and RAZORPAY_KEY_ID != 'YOUR_TEST_KEY_ID':
            order_data = {
                'amount': amount,
                'currency': currency,
                'payment_capture': '1', # Auto-capture payment instantly
                'notes': {
                    'description': 'Divyansh Fashion - Premium Apparel Checkout'
                }
            }
            order = client.order.create(data=order_data)
            return jsonify({
                "status": "success",
                "order_id": order['id'],
                "amount": amount,
                "currency": currency,
                "key_id": RAZORPAY_KEY_ID
            })
            
        # Fallback simulated order if you don't have keys yet
        return jsonify({
            "status": "mock",
            "order_id": f"order_mock_{random.randint(100000, 999999)}",
            "amount": amount,
            "currency": currency,
            "message": "Razorpay keys not configured. Returned a simulated order.",
            "key_id": "test_mock_key"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    """
    Endpoint to verify the payment cryptographic signature AFTER the frontend successfully pays.
    This prevents users from tampering with network requests using fake success flags.
    """
    try:
        data = request.json
        # When Razorpay finishes, it returns exactly these 3 variables to frontend
        if client and RAZORPAY_KEY_ID != 'YOUR_TEST_KEY_ID':
            client.utility.verify_payment_signature({
                'razorpay_order_id': data.get('razorpay_order_id'),
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature': data.get('razorpay_signature')
            })
            return jsonify({"status": "success", "message": "Cryptographic signature verified! Authentic payment."})
            
        return jsonify({"status": "mock", "message": "Signature bypassed. (Simulated Mode)"})
             
    except Exception as e:
        return jsonify({"status": "error", "message": "Invalid Signature! Potential fraud block."}), 400

if __name__ == '__main__':
    print("====================================================")
    print("  Divyansh Financial Server initialized on Port 5000")
    print("  Awaiting Razorpay Authentication Credentials...")
    print("====================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
