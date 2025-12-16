
import threading
import time
import sys
import os
import logging

# Configuration logging global
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('unified_bot.log', mode='a')
    ]
)
logger = logging.getLogger("UnifiedRunner")

def run_scalping_bot():
    """Lance le bot de scalping"""
    while True:
        try:
            # Ajouter le dossier scalping_bot au path pour les imports internes
            if os.path.join(os.getcwd(), 'scalping_bot') not in sys.path:
                sys.path.append(os.path.join(os.getcwd(), 'scalping_bot'))
            
            from scalping_bot.scalping_bot import ScalpingBot
            
            logger.info("🚀 Démarrage Thread: Scalping Bot")
            bot = ScalpingBot()
            bot.run()
        except Exception as e:
            logger.critical(f"❌ Crash Scalping Bot: {e}")
            import traceback
            traceback.print_exc()
            logger.info("♻️ Redémarrage du Scalping Bot dans 30s...")
            time.sleep(30)

def run_crypto_hunter():
    """Lance le bot crypto hunter"""
    try:
        # Ajouter le dossier crypto_bot au path pour les imports internes
        sys.path.append(os.path.join(os.getcwd(), 'crypto_bot'))
        from crypto_bot.crypto_hunter import CryptoHunterBot
        
        logger.info("🚀 Démarrage Thread: Crypto Hunter")
        bot = CryptoHunterBot()
        bot.run()
    except Exception as e:
        logger.critical(f"❌ Crash Crypto Hunter: {e}")
        import traceback
        traceback.print_exc()

def execute_force_trade():
    """Exécute un trade forcé pour vérifier que tout fonctionne"""
    try:
        logger.info("🧨 FORCE TRADE: Tentative d'achat immédiat (DOGE)...")
        # Attendre que les autres threads démarrent
        time.sleep(10)
        
        # Charger les variables d'env si besoin (normalement déjà là)
        from alpaca_trade_api import REST
        api = REST() 
        
        # Achat de 150 DOGE (pour dépasser le min order value de $1)
        symbol = "DOGE/USD"
        qty = 150
        
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side='buy',
            type='market',
            time_in_force='gtc' # Crypto requires GTC
        )
        logger.info(f"✅✅ FORCE TRADE RÉUSSI: Acheté {qty} {symbol} ! OrderID: {order.id}")
        logger.info("🚀 LE SYSTÈME EST OPÉRATIONNEL ET CONNECTÉ AU MARCHÉ.")
        
    except Exception as e:
        logger.error(f"❌ FORCE TRADE ÉCHOUÉ: {e}")

if __name__ == "__main__":
    print("""
    ⚡ TRADING BOT UNIFIED RUNNER
    =============================
    Bots actifs:
    1. 🏎️ Scalping Bot (Meme Coins + Tech)
    2. 🪙 Crypto Hunter (Major + Altcoins)
    3. 🧨 Force Trade (Test immédiat)
    """)
    
    # Créer les threads
    t1 = threading.Thread(target=run_scalping_bot, name="ScalpingThread", daemon=True)
    t2 = threading.Thread(target=run_crypto_hunter, name="HunterThread", daemon=True)
    t3 = threading.Thread(target=execute_force_trade, name="ForceTradeThread", daemon=True)
    
    # Démarrer
    t1.start()
    time.sleep(2)
    t2.start()
    time.sleep(2)
    # t3.start() # 🛑 Force Trade désactivé pour production
    
    # Boucle de surveillance
    try:
        while True:
            time.sleep(60)
            if not t1.is_alive():
                logger.error("⚠️ Scalping Thread is DEAD")
            if not t2.is_alive():
                logger.error("⚠️ Hunter Thread is DEAD")
            
            logger.info("✅ System OK - Bots running")
            
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt général demandé")
