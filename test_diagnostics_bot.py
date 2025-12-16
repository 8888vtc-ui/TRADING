
import os
import sys
import time
import json
import logging
import google.generativeai as genai
from alpaca_trade_api import REST

# Setup Logging
LOG_FILE = 'unified_bot.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | STRESS_TEST | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode='a')
    ]
)
logger = logging.getLogger("AIStressTester")

class AIStressTester:
    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.base_url = os.getenv('ALPACA_BASE_URL')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        
        # Connect API
        try:
            self.api = REST(self.api_key, self.secret_key, self.base_url)
            self.account = self.api.get_account()
            logger.info(f"✅ API CONNECTED. Buying Power: ${float(self.account.buying_power):,.2f}")
        except Exception as e:
            logger.error(f"❌ API CONNECTION FAILED: {e}")
            sys.exit(1)
            
        # Connect Gemini
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("✅ GEMINI AI CONNECTED")
        else:
            logger.error("❌ GEMINI KEY MISSING")
            sys.exit(1)

    def generate_fake_signals(self):
        """Demande à l'IA de créer des scénarios de trading faux/simulés"""
        logger.info("🧠 ASKING AI FOR FAKE SIGNALS...")
        
        prompt = """
        Generate 3 diverse "Fake" Trading Signals for my testing pipeline.
        Return ONLY valid JSON array.
        
        Scenarios to cover:
        1. "SCALP_NORMAL": Buy DOGE/USD, confidence 65%.
        2. "MOONSHOT_PUMP": Buy SHIB/USD, confidence 95% (simulated pump).
        3. "PANIC_SELL": Sell BTC/USD (simulated crash - but we will interpret as BUY for test if safe).
        
        Format:
        [
            {"type": "SCALP", "symbol": "DOGE/USD", "action": "BUY", "confidence": 65, "reason": "RSI Oversold"},
            {"type": "MOONSHOT", "symbol": "SHIB/USD", "action": "BUY", "confidence": 95, "reason": "Volume Spike 500%"}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            signals = json.loads(clean_json)
            logger.info(f"🧠 AI GENERATED {len(signals)} SIGNALS")
            return signals
        except Exception as e:
            logger.error(f"❌ AI GENERATION ERROR: {e}")
            # Fallback signal if AI fails
            return [{"type": "FALLBACK", "symbol": "DOGE/USD", "action": "BUY", "confidence": 50, "reason": "AI Failed"}]

    def execute_pipeline_test(self, signal):
        """Injecte le signal dans la pipeline d'exécution"""
        symbol = signal['symbol']
        action = signal['action']
        conf = signal['confidence']
        type_ = signal['type']
        
        logger.info(f"🧪 TESTING PIPELINE: {type_} on {symbol} ({action} {conf}%)")
        
        if action != 'BUY':
            logger.info("⚠️ Skipping Non-BUY test for safety.")
            return

        try:
            # 1. Pipeline: Check Price
            try:
                trade = self.api.get_latest_trade(symbol)
                price = trade.price
                logger.info(f"   📉 Market Price: ${price}")
            except:
                logger.info("   ⚠️ Price unavailable, using Market Order")

            # 2. Pipeline: Order Execution (Small Test Size)
            qty = 10 if 'DOGE' in symbol else 1000 if 'SHIB' in symbol else 0.0001
            
            logger.info(f"   🚀 EXECUTING ORDER: {qty} {symbol}...")
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            
            logger.info(f"   ✅ ORDER SUCCESS: ID {order.id}")
            logger.info(f"   📝 LOG ENTRY CONFIRMED: {signal['reason']}")
            
        except Exception as e:
            logger.error(f"   ❌ PIPELINE ERROR: {e}")

    def run(self):
        print("🤖 AI STRESS TESTER INITIALIZED")
        fake_signals = self.generate_fake_signals()
        
        for sig in fake_signals:
            self.execute_pipeline_test(sig)
            time.sleep(2)
            
        print("🏁 SUITE DE TESTS TERMINÉE")

if __name__ == "__main__":
    bot = AIStressTester()
    bot.run()
