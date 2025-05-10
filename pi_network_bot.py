import os
import json
import requests
import webbrowser
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

class PiNetworkBot:
    def __init__(self, destination_wallet=None, seed_phrase=None):
        self.wallet_address = destination_wallet
        self.seed_phrase = seed_phrase
        self.base_url = "https://api.minepi.com/v2"
        
        # OAuth2 credentials - should be stored in .env file
        self.client_id = os.getenv("PI_CLIENT_ID")
        self.client_secret = os.getenv("PI_CLIENT_SECRET")
        self.redirect_uri = os.getenv("PI_REDIRECT_URI", "http://localhost:8000/callback")
        
        # Get access token either from env or perform auth flow
        self.access_token = "hjuxmwsq4vwxooti4gwsu2g2i6azacgl2qkojraxri73saxazvhb0czcebarkaof"
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def authenticate(self):
        """Perform OAuth2 authentication flow"""
        logger.info("Starting OAuth2 authentication flow")
        
        # Check if client credentials are available
        if not self.client_id or not self.client_secret:
            logger.error("Missing OAuth2 credentials. Please set PI_CLIENT_ID and PI_CLIENT_SECRET in .env file")
            return None
            
        # First, get authorization code
        auth_url = f"https://minepi.com/oauth?client_id={self.client_id}&response_type=code&redirect_uri={self.redirect_uri}&scope=payments"
        logger.info(f"Please visit this URL to authorize the application: {auth_url}")
        
        # Open browser for user to authorize
        webbrowser.open(auth_url)
        
        # User needs to input the code received at the redirect URI
        auth_code = input("Enter the authorization code received: ")
        
        # Exchange auth code for access token
        try:
            token_url = "https://api.minepi.com/v2/oauth/token"
            token_data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri
            }
            
            logger.info("Exchanging authorization code for access token")
            response = requests.post(token_url, data=token_data)
            
            if response.status_code != 200:
                logger.error(f"Failed to get access token: {response.text}")
                return None
                
            token_info = response.json()
            access_token = token_info.get("access_token")
            
            # Save the token to .env file for future use
            with open(".env", "a") as f:
                f.write(f"\nPI_ACCESS_TOKEN={access_token}")
                
            logger.success("Successfully obtained access token")
            return access_token
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def check_unlocked_coins(self):
        """Check available unlocked coins in the wallet"""
        try:
            logger.info(f"Making request to {self.base_url}/me")
            logger.info(f"Using headers: {self.headers}")
            
            # First get user info to verify token
            response = requests.get(
                f"{self.base_url}/me",
                headers=self.headers,
                verify=True
            )
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 401:
                logger.warning("Access token expired or invalid. Attempting to re-authenticate...")
                self.access_token = self.authenticate()
                if not self.access_token:
                    return 0
                
                # Update headers with new token
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                
                # Retry the request
                response = requests.get(
                    f"{self.base_url}/me",
                    headers=self.headers,
                    verify=True
                )
                
            if response.status_code != 200:
                logger.error(f"Error response: {response.text}")
                return 0
                
            user_info = response.json()
            logger.info(f"User info: {user_info}")

            # Then get balance
            logger.info(f"Making request to {self.base_url}/wallet/balance")
            response = requests.get(
                f"{self.base_url}/wallet/balance",
                headers=self.headers,
                verify=True
            )
            
            logger.info(f"Balance response status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Balance error response: {response.text}")
                return 0
                
            balance = response.json()
            logger.info(f"Current balance: {balance}")
            return balance.get('available_balance', 0)
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response headers: {e.response.headers}")
            logger.error(f"Response text: {e.response.text}")
            return 0
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return 0

    def prepare_transaction(self, amount):
        """Prepare a transaction with the specified amount"""
        if not self.wallet_address:
            logger.error("No destination wallet address provided")
            return None
            
        try:
            payload = {
                "amount": amount,
                "recipient": self.wallet_address,
                "memo": f"Transfer via Pi Network Bot - {datetime.now().isoformat()}"
            }
            logger.info(f"Preparing transaction with payload: {payload}")
            
            response = requests.post(
                f"{self.base_url}/payments",
                headers=self.headers,
                json=payload,
                verify=True
            )
            
            logger.info(f"Transaction response status code: {response.status_code}")
            
            if response.status_code == 401:
                logger.warning("Access token expired or invalid. Attempting to re-authenticate...")
                self.access_token = self.authenticate()
                if not self.access_token:
                    return None
                    
                # Update headers with new token
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                
                # Retry the request
                response = requests.post(
                    f"{self.base_url}/payments",
                    headers=self.headers,
                    json=payload,
                    verify=True
                )
                
            if response.status_code != 200:
                logger.error(f"Transaction error response: {response.text}")
                return None
                
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response headers: {e.response.headers}")
            logger.error(f"Response text: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

    def send_transaction(self, payment_id):
        """Send the prepared transaction"""
        try:
            logger.info(f"Sending transaction for payment_id: {payment_id}")
            
            response = requests.post(
                f"{self.base_url}/payments/{payment_id}/complete",
                headers=self.headers,
                verify=True
            )
            
            logger.info(f"Send transaction response status code: {response.status_code}")
            
            if response.status_code == 401:
                logger.warning("Access token expired or invalid. Attempting to re-authenticate...")
                self.access_token = self.authenticate()
                if not self.access_token:
                    return None
                    
                # Update headers with new token
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                
                # Retry the request
                response = requests.post(
                    f"{self.base_url}/payments/{payment_id}/complete",
                    headers=self.headers,
                    verify=True
                )
                
            if response.status_code != 200:
                logger.error(f"Send transaction error response: {response.text}")
                return None
                
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response headers: {e.response.headers}")
            logger.error(f"Response text: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

    def log_transaction(self, transaction_data, success=True):
        """Log transaction details"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "data": transaction_data,
            "destination_wallet": self.wallet_address
        }
        
        try:
            # Create directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            log_file = os.path.join("logs", "transaction_log.json")
            
            # Check if file exists and is not empty
            if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
                with open(log_file, "r") as f:
                    try:
                        logs = json.load(f)
                        if not isinstance(logs, list):
                            logs = [logs]
                    except json.JSONDecodeError:
                        # If file is corrupted, start with a new list
                        logs = []
            else:
                logs = []
                
            # Append new log entry
            logs.append(log_entry)
            
            # Write back to file
            with open(log_file, "w") as f:
                json.dump(logs, f, indent=2)
                
            logger.info(f"Transaction logged to {log_file}")
        except Exception as e:
            logger.error(f"Failed to log transaction: {str(e)}")

    def process_transaction(self):
        """Main process to handle the transaction flow"""
        if not self.wallet_address:
            logger.error("No destination wallet address provided")
            return False

        # Check available coins
        available_balance = self.check_unlocked_coins()
        logger.info(f"Available balance: {available_balance} Pi")
        
        if available_balance <= 0:
            logger.warning("No coins available for transfer")
            return False

        # Ask for confirmation
        confirm = input(f"Found {available_balance} Pi available. Proceed with transfer to {self.wallet_address}? (y/n): ")
        if confirm.lower() != 'y':
            logger.info("Transaction cancelled by user")
            return False

        # Prepare transaction
        transaction = self.prepare_transaction(available_balance)
        if not transaction:
            logger.error("Failed to prepare transaction")
            return False

        # Send transaction
        result = self.send_transaction(transaction['payment_id'])
        if not result:
            logger.error("Failed to send transaction")
            self.log_transaction(transaction, success=False)
            return False

        # Log successful transaction
        self.log_transaction(result, success=True)
        logger.success(f"Transaction completed successfully: {result}")
        return True

def setup_environment():
    """Setup environment variables if not present"""
    env_file = ".env"
    
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write("# Pi Network OAuth Credentials\n")
            f.write("PI_CLIENT_ID=\n")
            f.write("PI_CLIENT_SECRET=\n")
            f.write("PI_REDIRECT_URI=http://localhost:8000/callback\n")
        
        logger.info(f"Created {env_file} file. Please fill in your Pi Network OAuth credentials.")
        
    # Check if credentials are set
    load_dotenv()
    if not os.getenv("PI_CLIENT_ID") or not os.getenv("PI_CLIENT_SECRET"):
        logger.warning("Pi Network OAuth credentials not set. Please update the .env file.")
        print("\nTo set up Pi Network API access:")
        print("1. Go to https://developers.minepi.com/ and create a developer account")
        print("2. Create a new app and get your Client ID and Client Secret")
        print("3. Set the redirect URI to http://localhost:8000/callback")
        print("4. Add these credentials to the .env file\n")
        
        # Ask user if they want to enter credentials now
        setup_now = input("Would you like to enter credentials now? (y/n): ")
        if setup_now.lower() == 'y':
            client_id = input("Enter Pi Network Client ID: ")
            client_secret = input("Enter Pi Network Client Secret: ")
            
            # Update .env file
            with open(env_file, "r") as f:
                lines = f.readlines()
                
            with open(env_file, "w") as f:
                for line in lines:
                    if line.startswith("PI_CLIENT_ID="):
                        f.write(f"PI_CLIENT_ID={client_id}\n")
                    elif line.startswith("PI_CLIENT_SECRET="):
                        f.write(f"PI_CLIENT_SECRET={client_secret}\n")
                    else:
                        f.write(line)
            
            logger.info("Credentials updated successfully")
        else:
            logger.info("Please update the .env file with your credentials before running the bot")

def main():
    # Configure logger
    os.makedirs("logs", exist_ok=True)
    logger.add(os.path.join("logs", "bot_{time}.log"), rotation="1 day", retention="7 days")
    
    # Setup environment
    setup_environment()
    
    # Get destination wallet from user input
    destination_wallet = input("Enter destination wallet address: ")
    
    # Get seed phrase (optional)
    seed_phrase = input("Enter seed phrase (optional, press Enter to skip): ")
    if seed_phrase.strip() == "":
        seed_phrase = None
    
    # Initialize and run bot
    bot = PiNetworkBot(destination_wallet=destination_wallet, seed_phrase=seed_phrase)
    bot.process_transaction()

if __name__ == "__main__":
    main()