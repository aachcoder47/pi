from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
from pi_network_bot import PiNetworkBot
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
load_dotenv()

class TransactionForm(FlaskForm):
    seed_phrase = StringField('Seed Phrase', 
                            validators=[DataRequired()],
                            render_kw={"placeholder": "Enter your Pi Network seed phrase"})
    destination_wallet = StringField('Destination Wallet Address', 
                                   validators=[DataRequired(), Length(min=32, max=100)],
                                   render_kw={"placeholder": "Enter Pi Network wallet address"})
    amount = FloatField('Amount (Pi)', 
                       validators=[DataRequired(), NumberRange(min=0.1)],
                       render_kw={"placeholder": "Enter amount to transfer"})
    memo = StringField('Memo (Optional)', 
                      render_kw={"placeholder": "Add a memo to your transaction"})
    submit = SubmitField('Send Transaction')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = TransactionForm()
    if form.validate_on_submit():
        try:
            # Initialize bot with form data
            bot = PiNetworkBot(
                destination_wallet=form.destination_wallet.data,
                seed_phrase=form.seed_phrase.data
            )
            
            # Prepare transaction
            transaction = bot.prepare_transaction(form.amount.data)
            if transaction:
                # Send transaction
                result = bot.send_transaction(transaction['payment_id'])
                if result:
                    flash('Transaction completed successfully!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Failed to complete transaction. Please try again.', 'error')
            else:
                flash('Failed to prepare transaction. Please check your inputs.', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
    
    return render_template('index.html', form=form)

@app.route('/balance', methods=['POST'])
def check_balance():
    try:
        seed_phrase = request.json.get('seed_phrase')
        if not seed_phrase:
            return {'error': 'Seed phrase is required'}, 400
            
        bot = PiNetworkBot(seed_phrase=seed_phrase)
        balance = bot.check_unlocked_coins()
        return {'balance': balance}
    except Exception as e:
        return {'error': str(e)}, 400

if __name__ == '__main__':
    app.run(debug=True) 