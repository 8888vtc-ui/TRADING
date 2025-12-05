"""Test rapide du bot"""
from bot_trading import TradingBot

print("🧪 Test du bot...")
bot = TradingBot()
print("\n📊 Premier scan...")
bot.scan_and_trade()
print("\n✅ Test terminé !")

