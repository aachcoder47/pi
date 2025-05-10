# Pi Network Transaction Bot

This bot automates the process of transferring Pi coins from your wallet to a specified destination address. It follows a structured flow to check available coins, prepare transactions, and handle the transfer process.

## Features

- Check available unlocked coins
- Prepare and send transactions
- Automatic transaction logging
- Error handling and reporting
- Configurable destination wallet

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

3. Configure your environment variables in the `.env` file:
- `PI_API_KEY`: Your Pi Network API key
- `DESTINATION_WALLET`: The wallet address to send coins to

## Usage

Run the bot:
```bash
python pi_network_bot.py
```

The bot will:
1. Check for available unlocked coins
2. Prepare a transaction if coins are available
3. Send the transaction to the specified wallet
4. Log the result in both `bot.log` and `transaction_log.json`

## Logging

- `bot.log`: Contains detailed operation logs with rotation (1 day) and retention (7 days)
- `transaction_log.json`: Contains transaction history with success/failure status

## Error Handling

The bot includes comprehensive error handling for:
- API connection issues
- Insufficient balance
- Transaction failures
- Invalid wallet addresses

## Security Notes

- Never share your API key
- Keep your `.env` file secure
- Regularly check the transaction logs for any suspicious activity 