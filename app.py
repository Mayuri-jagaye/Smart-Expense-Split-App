from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import re
from decimal import Decimal, ROUND_HALF_UP
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///expense_splitter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

db = SQLAlchemy(app)

# Database Models
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    avatar_color = db.Column(db.String(7), default='#3B82F6')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_spent = db.Column(db.Numeric(10, 2), default=0.00)
    total_owed = db.Column(db.Numeric(10, 2), default=0.00)
    
    expenses_paid = db.relationship('Expense', backref='payer', lazy=True, foreign_keys='Expense.paid_by_id')
    expense_shares = db.relationship('ExpenseShare', backref='person', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='Other')
    paid_by_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    split_type = db.Column(db.String(20), default='equal')  # equal, percentage, custom
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20))  # weekly, monthly, yearly
    
    shares = db.relationship('ExpenseShare', backref='expense', lazy=True, cascade='all, delete-orphan')

class ExpenseShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    percentage = db.Column(db.Numeric(5, 2), default=0.00)

# Smart Category Detection
def detect_category(description):
    """AI-like category detection based on description keywords"""
    description_lower = description.lower()
    
    categories = {
        'Food & Dining': ['dinner', 'lunch', 'breakfast', 'restaurant', 'food', 'meal', 'pizza', 'burger', 'cafe'],
        'Transportation': ['petrol', 'gas', 'uber', 'taxi', 'bus', 'train', 'fuel', 'parking', 'toll'],
        'Entertainment': ['movie', 'cinema', 'concert', 'show', 'game', 'ticket', 'amusement'],
        'Shopping': ['groceries', 'shopping', 'clothes', 'electronics', 'store', 'mall'],
        'Utilities': ['electricity', 'water', 'gas', 'internet', 'wifi', 'phone', 'utility'],
        'Travel': ['hotel', 'flight', 'vacation', 'trip', 'booking', 'travel'],
        'Health': ['medicine', 'doctor', 'hospital', 'pharmacy', 'medical'],
        'Education': ['books', 'course', 'tuition', 'education', 'study'],
        'Home': ['rent', 'maintenance', 'repair', 'furniture', 'home'],
        'Other': []
    }
    
    for category, keywords in categories.items():
        if any(keyword in description_lower for keyword in keywords):
            return category
    
    return 'Other'

# Smart Person Name Extraction
def extract_people_from_description(description):
    """Extract potential person names from description using NLP-like approach"""
    # Common patterns for mentioning people
    patterns = [
        r'with\s+([A-Z][a-z]+)',
        r'for\s+([A-Z][a-z]+)',
        r'([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+)',
        r'([A-Z][a-z]+)\s+paid',
        r'([A-Z][a-z]+)\s+contributed'
    ]
    
    people = []
    for pattern in patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                people.extend(match)
            else:
                people.append(match)
    
    return list(set(people))

# Settlement Algorithm
def calculate_optimal_settlements():
    """Calculate optimal settlements using graph theory approach"""
    people = Person.query.all()
    balances = {}
    
    # Calculate net balance for each person
    for person in people:
        total_paid = sum(expense.amount for expense in person.expenses_paid)
        total_owed = sum(share.amount for share in person.expense_shares)
        balances[person.name] = float(total_paid - total_owed)
    
    # Separate debtors and creditors
    debtors = {name: amount for name, amount in balances.items() if amount < 0}
    creditors = {name: amount for name, amount in balances.items() if amount > 0}
    
    settlements = []
    
    # Optimize settlements
    for debtor_name, debt_amount in debtors.items():
        remaining_debt = abs(debt_amount)
        
        for creditor_name, credit_amount in creditors.items():
            if remaining_debt <= 0 or credit_amount <= 0:
                continue
                
            settlement_amount = min(remaining_debt, credit_amount)
            
            if settlement_amount > 0.01:  # Avoid tiny amounts
                settlements.append({
                    'from': debtor_name,
                    'to': creditor_name,
                    'amount': round(settlement_amount, 2)
                })
                
                remaining_debt -= settlement_amount
                creditors[creditor_name] -= settlement_amount
    
    return settlements

# API Routes
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """Get all expenses with detailed information"""
    try:
        expenses = Expense.query.order_by(Expense.created_at.desc()).all()
        
        expense_list = []
        for expense in expenses:
            shares = []
            for share in expense.shares:
                shares.append({
                    'person_name': share.person.name,
                    'amount': float(share.amount),
                    'percentage': float(share.percentage)
                })
            
            expense_data = {
                'id': expense.id,
                'amount': float(expense.amount),
                'description': expense.description,
                'category': expense.category,
                'paid_by': expense.payer.name,
                'split_type': expense.split_type,
                'created_at': expense.created_at.isoformat(),
                'is_recurring': expense.is_recurring,
                'recurring_frequency': expense.recurring_frequency,
                'shares': shares
            }
            expense_list.append(expense_data)
        
        return jsonify({
            'success': True,
            'data': expense_list,
            'message': f'Found {len(expense_list)} expenses'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    """Add new expense with smart features"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('amount') or float(data['amount']) <= 0:
            return jsonify({
                'success': False,
                'error': 'Amount must be positive'
            }), 400
        
        if not data.get('description'):
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
        
        if not data.get('paid_by'):
            return jsonify({
                'success': False,
                'error': 'Paid by field is required'
            }), 400
        
        amount = Decimal(str(data['amount'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        description = data['description']
        paid_by_name = data['paid_by']
        split_type = data.get('split_type', 'equal')
        
        # Smart category detection
        category = data.get('category') or detect_category(description)
        
        # Get or create payer
        payer = Person.query.filter_by(name=paid_by_name).first()
        if not payer:
            payer = Person(name=paid_by_name)
            db.session.add(payer)
            db.session.flush()
        
        # Create expense
        expense = Expense(
            amount=amount,
            description=description,
            category=category,
            paid_by_id=payer.id,
            split_type=split_type,
            is_recurring=data.get('is_recurring', False),
            recurring_frequency=data.get('recurring_frequency')
        )
        
        db.session.add(expense)
        db.session.flush()
        
        # Handle expense splitting
        people_names = data.get('split_between', [])
        if not people_names:
            # Auto-detect people from description or use all people
            people_names = extract_people_from_description(description)
            if not people_names:
                people_names = [person.name for person in Person.query.all()]
        
        # Ensure payer is included
        if paid_by_name not in people_names:
            people_names.append(paid_by_name)
        
        # Get or create people
        people = []
        for name in people_names:
            person = Person.query.filter_by(name=name).first()
            if not person:
                person = Person(name=name)
                db.session.add(person)
                db.session.flush()
            people.append(person)
        
        # Calculate shares
        if split_type == 'equal':
            share_amount = amount / len(people)
            for person in people:
                share = ExpenseShare(
                    expense_id=expense.id,
                    person_id=person.id,
                    amount=share_amount,
                    percentage=Decimal('100.00') / len(people)
                )
                db.session.add(share)
        
        elif split_type == 'percentage':
            percentages = data.get('percentages', {})
            for person in people:
                percentage = Decimal(str(percentages.get(person.name, 100 / len(people))))
                share_amount = (amount * percentage) / 100
                share = ExpenseShare(
                    expense_id=expense.id,
                    person_id=person.id,
                    amount=share_amount,
                    percentage=percentage
                )
                db.session.add(share)
        
        elif split_type == 'custom':
            custom_amounts = data.get('custom_amounts', {})
            for person in people:
                custom_amount = Decimal(str(custom_amounts.get(person.name, amount / len(people))))
                percentage = (custom_amount / amount) * 100
                share = ExpenseShare(
                    expense_id=expense.id,
                    person_id=person.id,
                    amount=custom_amount,
                    percentage=percentage
                )
                db.session.add(share)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': expense.id,
                'amount': float(expense.amount),
                'description': expense.description,
                'category': expense.category,
                'paid_by': payer.name,
                'split_type': expense.split_type
            },
            'message': 'Expense added successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """Update existing expense"""
    try:
        expense = Expense.query.get_or_404(expense_id)
        data = request.get_json()
        
        if 'amount' in data:
            if float(data['amount']) <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Amount must be positive'
                }), 400
            expense.amount = Decimal(str(data['amount']))
        
        if 'description' in data:
            expense.description = data['description']
            # Update category if description changed
            if not data.get('category'):
                expense.category = detect_category(data['description'])
        
        if 'category' in data:
            expense.category = data['category']
        
        if 'split_type' in data:
            expense.split_type = data['split_type']
        
        expense.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': expense.id,
                'amount': float(expense.amount),
                'description': expense.description,
                'category': expense.category,
                'paid_by': expense.payer.name
            },
            'message': 'Expense updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Delete expense"""
    try:
        expense = Expense.query.get_or_404(expense_id)
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Expense deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/settlements', methods=['GET'])
def get_settlements():
    """Get optimized settlement summary"""
    try:
        settlements = calculate_optimal_settlements()
        
        return jsonify({
            'success': True,
            'data': {
                'settlements': settlements,
                'total_transactions': len(settlements),
                'total_amount': sum(s['amount'] for s in settlements)
            },
            'message': f'Found {len(settlements)} optimal settlements'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/balances', methods=['GET'])
def get_balances():
    """Get current balances for all people"""
    try:
        people = Person.query.all()
        balances = []
        
        for person in people:
            total_paid = sum(expense.amount for expense in person.expenses_paid)
            total_owed = sum(share.amount for share in person.expense_shares)
            net_balance = total_paid - total_owed
            
            balances.append({
                'name': person.name,
                'total_paid': float(total_paid),
                'total_owed': float(total_owed),
                'net_balance': float(net_balance),
                'status': 'owes' if net_balance < 0 else 'owed' if net_balance > 0 else 'settled'
            })
        
        return jsonify({
            'success': True,
            'data': balances,
            'message': f'Found balances for {len(balances)} people'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/people', methods=['GET'])
def get_people():
    """Get all people with their statistics"""
    try:
        people = Person.query.all()
        people_list = []
        
        for person in people:
            total_paid = sum(expense.amount for expense in person.expenses_paid)
            total_owed = sum(share.amount for share in person.expense_shares)
            
            people_list.append({
                'id': person.id,
                'name': person.name,
                'email': person.email,
                'avatar_color': person.avatar_color,
                'total_paid': float(total_paid),
                'total_owed': float(total_owed),
                'net_balance': float(total_paid - total_owed),
                'expense_count': len(person.expenses_paid),
                'created_at': person.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'data': people_list,
            'message': f'Found {len(people_list)} people'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Enhanced Analytics Endpoints
@app.route('/api/analytics/categories', methods=['GET'])
def get_category_analytics():
    """Get spending breakdown by category"""
    try:
        expenses = Expense.query.all()
        category_totals = {}
        
        for expense in expenses:
            category = expense.category
            if category not in category_totals:
                category_totals[category] = 0
            category_totals[category] += float(expense.amount)
        
        return jsonify({
            'success': True,
            'data': category_totals,
            'message': 'Category analytics retrieved successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analytics/monthly', methods=['GET'])
def get_monthly_analytics():
    """Get monthly spending summaries"""
    try:
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        monthly_expenses = Expense.query.filter(
            db.extract('month', Expense.created_at) == current_month,
            db.extract('year', Expense.created_at) == current_year
        ).all()
        
        total_monthly = sum(float(expense.amount) for expense in monthly_expenses)
        
        return jsonify({
            'success': True,
            'data': {
                'month': current_month,
                'year': current_year,
                'total_spent': total_monthly,
                'expense_count': len(monthly_expenses),
                'average_per_expense': total_monthly / len(monthly_expenses) if monthly_expenses else 0
            },
            'message': 'Monthly analytics retrieved successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Initialize database and add sample data
@app.route('/api/init', methods=['POST'])
def initialize_database():
    """Initialize database with sample data"""
    try:
        # Create tables
        db.create_all()
        
        # Add sample people
        sample_people = [
            Person(name='Shantanu', avatar_color='#3B82F6'),
            Person(name='Sanket', avatar_color='#10B981'),
            Person(name='Om', avatar_color='#F59E0B')
        ]
        
        for person in sample_people:
            existing = Person.query.filter_by(name=person.name).first()
            if not existing:
                db.session.add(person)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Database initialized with sample data'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Web Interface Route
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Get port from environment variable (for deployment platforms)
    port = int(os.environ.get('PORT', 8899))
    app.run(debug=False, host='0.0.0.0', port=port) 