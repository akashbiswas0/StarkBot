import logging
import requests
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
from io import BytesIO

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

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

# Function to generate QR code
def generate_qr_code(data):
    url = f'https://api.qrserver.com/v1/create-qr-code/?data={data}&size=100x100'
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        logger.error(f'Failed to generate QR code. Status code: {response.status_code}')
        return None

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Create Wallet & Get Price", callback_data='create_wallet')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome to the StarkNet Trading Bot! Click the button below to create a new wallet and get the current StarkNet price.', reply_markup=reply_markup)

# Function to send wallet and price information
async def send_wallet_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    wallet = context.user_data.get('wallet')
    starknet_price = context.user_data.get('starknet_price')
    explorer_link = generate_explorer_link(wallet['address'])

    message = f"""
🪙 Entropy Starknet Bot 🪙
The premier StarkNet trading bot.

Entropy Wallet: {wallet['address']}

Balance: 0 STARK

STARK Price: ${starknet_price}

View on Explorer: [Voyager]({explorer_link})
Get Ahead - [Our Website](link)
"""

    keyboard = [
        [
            InlineKeyboardButton("Send", callback_data='send'),
            InlineKeyboardButton("Receive", callback_data='receive')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='Markdown')

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

        context.user_data['wallet'] = wallet
        context.user_data['starknet_price'] = starknet_price

        await send_wallet_info(query, context)

    elif query.data == 'send':
        await query.edit_message_text(text='Please enter the address where you want to send the amount:')
        context.user_data['awaiting_address'] = True

    elif query.data == 'receive':
        message = 'Choose an option:'
        keyboard = [
            [
                InlineKeyboardButton("QR Code", callback_data='qr_code'),
                InlineKeyboardButton("Send Wallet Address", callback_data='send_wallet_address')
            ],
            [
                InlineKeyboardButton("Back", callback_data='back_to_send_receive')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=message, reply_markup=reply_markup)

    elif query.data == 'qr_code':
        wallet = context.user_data.get('wallet')
        if wallet:
            qr_code_image = generate_qr_code(wallet['address'])
            if qr_code_image:
                await query.message.reply_photo(photo=InputFile(qr_code_image, filename='qr_code.png'))
            else:
                await query.edit_message_text(text='Failed to generate QR code. Please try again later.')
        else:
            await query.edit_message_text(text='No wallet found. Please create a wallet first.')
        await send_wallet_info(query, context)

    elif query.data == 'send_wallet_address':
        wallet = context.user_data.get('wallet')
        if wallet:
            await query.edit_message_text(text=f'Your wallet address: {wallet["address"]}')
        else:
            await query.edit_message_text(text='No wallet found. Please create a wallet first.')
        await send_wallet_info(query, context)

    elif query.data == 'back_to_send_receive':
        await send_wallet_info(query, context)

    elif query.data == 'confirm_send':
        amount = context.user_data.get('amount')
        address = context.user_data.get('address')
        if amount and address:
            message = f'{amount} STARK sent to {address}.'
            keyboard = [
                [
                    InlineKeyboardButton("Back", callback_data='back_to_main')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=message, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text='Failed to send amount. Please try again.')

    elif query.data == 'back_to_main':
        await send_wallet_info(query, context)

# Message handler for receiving the address and amount
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'awaiting_address' in context.user_data and context.user_data['awaiting_address']:
        address = update.message.text
        context.user_data['address'] = address
        context.user_data['awaiting_address'] = False
        context.user_data['awaiting_amount'] = True
        await update.message.reply_text(text='Please enter the amount you want to send:')
    elif 'awaiting_amount' in context.user_data and context.user_data['awaiting_amount']:
        amount = update.message.text
        context.user_data['amount'] = amount
        context.user_data['awaiting_amount'] = False
        keyboard = [
            [
                InlineKeyboardButton("Send", callback_data='confirm_send'),
                InlineKeyboardButton("Back", callback_data='back_to_send_receive')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text=f'You entered the amount: {amount}', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text='Please use the buttons to interact with the bot.')

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
