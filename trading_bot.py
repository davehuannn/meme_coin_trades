from binance.client import Client
from binance.exceptions import BinanceAPIException
import config
import time
import logging
from twitter_analyzer import TwitterAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='trading_bot.log'
)

class MemeCoinTrader:
    def __init__(self):
        # Initialize Binance client with API keys from config
        self.client = Client(config.API_KEY, config.API_SECRET)
        self.trading_pairs = [
            'DOGEUSDT',    # Dogecoin
            'SHIBUSDT',    # Shiba Inu
            'FLOKIUSDT',   # Floki Inu
            'PEPEUSDT',    # Pepe
            'BONKUSDT',    # Bonk
            'CATUSDT',     # Cat Token
            'BABYUSDT'     # BabyDoge
        ]  
        self.min_trade_amount = 20  # Minimum trade amount in USDT
        self.twitter_analyzer = TwitterAnalyzer()

    def get_account_balance(self, asset):
        """Get current balance for a specific asset"""
        try:
            balance = self.client.get_asset_balance(asset=asset)
            return float(balance['free'])
        except BinanceAPIException as e:
            logging.error(f"Error getting balance: {str(e)}")
            return 0

    def place_buy_order(self, symbol, quantity):
        """Place a market buy order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            logging.info(f"Buy order placed: {order}")
            return order
        except BinanceAPIException as e:
            logging.error(f"Error placing buy order: {str(e)}")
            return None

    def place_sell_order(self, symbol, quantity):
        """Place a market sell order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            logging.info(f"Sell order placed: {order}")
            return order
        except BinanceAPIException as e:
            logging.error(f"Error placing sell order: {str(e)}")
            return None

    def execute_trade(self, symbol, action, quantity):
        """Execute a trade based on the given action"""
        if action.lower() == 'buy':
            return self.place_buy_order(symbol, quantity)
        elif action.lower() == 'sell':
            return self.place_sell_order(symbol, quantity)
        else:
            logging.error(f"Invalid action: {action}")
            return None

    def get_available_pairs(self):
        """Get all available trading pairs that end with USDT"""
        try:
            exchange_info = self.client.get_exchange_info()
            all_pairs = [s['symbol'] for s in exchange_info['symbols'] if s['symbol'].endswith('USDT')]
            return all_pairs
        except BinanceAPIException as e:
            logging.error(f"Error getting trading pairs: {str(e)}")
            return []

    def add_trading_pair(self, symbol):
        """Add a new trading pair to the list"""
        if symbol not in self.trading_pairs:
            # Verify the pair exists on Binance
            available_pairs = self.get_available_pairs()
            if symbol in available_pairs:
                self.trading_pairs.append(symbol)
                logging.info(f"Added new trading pair: {symbol}")
                return True
            else:
                logging.error(f"Trading pair {symbol} not available on Binance")
                return False

    def run(self):
        """Main loop for the trading bot"""
        while True:
            try:
                for pair in self.trading_pairs:
                    coin = pair[:-4]  # Remove USDT
                    
                    # Analyze Twitter data
                    analysis = self.twitter_analyzer.analyze_coin(coin)
                    if analysis:
                        signal = self.twitter_analyzer.generate_trading_signal(analysis)
                        
                        if signal and signal['action']:
                            logging.info(f"Signal generated for {coin}: {signal}")
                            
                            # Get current balance
                            balance = self.get_account_balance('USDT')
                            
                            if signal['action'] == 'buy' and balance > self.min_trade_amount:
                                # Calculate position size based on signal strength
                                position_size = min(balance * 0.1 * signal['strength'], config.MAX_TRADE_AMOUNT_USDT)
                                self.execute_trade(pair, 'buy', position_size)
                            
                            elif signal['action'] == 'sell':
                                coin_balance = self.get_account_balance(coin)
                                if coin_balance > 0:
                                    self.execute_trade(pair, 'sell', coin_balance)
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    trader = MemeCoinTrader()
    trader.run() 