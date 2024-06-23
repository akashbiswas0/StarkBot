import logging
import requests
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Get the token from the environment variable
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Add debug logging
logger.info(f"Token read from .env: {TOKEN}")

if not TOKEN:
    logger.error("No token found in environment variables.")
    logger.info("Printing all environment variables:")
    logger.info(str(os.environ))
    raise ValueError("No token found. Make sure you have a .env file with TELEGRAM_BOT_TOKEN set.")

# Function to fetch StarkNet price from Coingecko
async def fetch_starknet_price():
    try:
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=starknet&vs_currencies=usd')
        response.raise_for_status()
        return response.json()['starknet']['usd']
    except requests.RequestException as e:
        logger.error(f'Error fetching StarkNet price: {e}')
        return None

# Function to create a random wallet address
def create_random_wallet():
    address = '0x' + ''.join(random.choices(string.hexdigits, k=40)).lower()
    private_key = ''.join(random.choices(string.hexdigits, k=64)).lower()
    public_key = ''.join(random.choices(string.hexdigits, k=128)).lower()
    return {
        'address': address,
        'private_key': private_key,
        'public_key': public_key
    }

# Function to generate explorer link using Voyager
def generate_explorer_link(address):
    return f'https://voyager.online/address/{address}'

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Create Wallet & Get Price", callback_data='create_wallet')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome to the StarkNet Trading Bot! Click the button below to create a new wallet and get the current StarkNet price.', reply_markup=reply_markup)

# Callback query handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'create_wallet':
        await query.edit_message_text(text='Creating your StarkNet wallet and fetching the price...')

        wallet = create_random_wallet()
        starknet_price = await fetch_starknet_price()

        if starknet_price is None:
            await query.edit_message_text(text='Failed to fetch StarkNet price. Please try again later.')
            return

        explorer_link = generate_explorer_link(wallet['address'])

        message = f"""
🪙 Entropy Starknet Bot 🪙
The premier StarkNet trading bot.

Entropy Wallet: {wallet['address']}
Balance: 0 STARK
STARK Price: ${starknet_price}

View on Explorer: [Voyager]({explorer_link})
Get Ahead - our website [HERE](link)

"""
        await query.edit_message_text(text=message, parse_mode='Markdown')

def main() -> None:
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on callback queries - handle button clicks
    application.add_handler(CallbackQueryHandler(button))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()