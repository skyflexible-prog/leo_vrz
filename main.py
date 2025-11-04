"""
Main application entry point
"""
import asyncio
import signal
from config.settings import settings
from database.mongodb_client import mongodb_client
from database.repositories.vrz_repository import vrz_repository
from database.repositories.user_settings_repository import user_settings_repository
from database.repositories.trade_repository import trade_repository
from trading.position_manager import position_manager
from bot.bot_handler import telegram_bot
from utils.logger import bot_logger
from utils.health_check import app as health_app, health_checker
import uvicorn


class TradingBotApp:
    """Main trading bot application"""
    
    def __init__(self):
        self.running = False
        self.health_server = None
        self.trading_task = None
        
    async def initialize(self):
        """Initialize all components"""
        try:
            bot_logger.info("=" * 70)
            bot_logger.info("DELTA VRZ TRADING BOT STARTING")
            bot_logger.info("=" * 70)
            
            # Initialize MongoDB
            bot_logger.info("Connecting to MongoDB...")
            await mongodb_client.connect()
            
            # Initialize repositories
            bot_logger.info("Initializing repositories...")
            await vrz_repository.initialize()
            await user_settings_repository.initialize()
            await trade_repository.initialize()
            await position_manager.initialize()
            
            # Initialize Telegram bot
            bot_logger.info("Initializing Telegram bot...")
            await telegram_bot.initialize()
            
            # Update health status
            health_checker.update_status(
                bot_status="initialized",
                mongodb="connected",
                delta_api="unknown"
            )
            
            bot_logger.info("All components initialized successfully")
            
        except Exception as e:
            bot_logger.critical(f"Initialization failed: {str(e)}", exc_info=True)
            raise
    
    async def start_health_server(self):
        """Start health check HTTP server"""
        try:
            config = uvicorn.Config(
                app=health_app,
                host=settings.HOST,
                port=settings.PORT,
                log_level="info"
            )
            self.health_server = uvicorn.Server(config)
            
            bot_logger.info(f"Health check server starting on {settings.HOST}:{settings.PORT}")
            await self.health_server.serve()
            
        except Exception as e:
            bot_logger.error(f"Health server error: {str(e)}", exc_info=True)
    
    async def trading_loop(self):
        """Main trading loop"""
        try:
            from trading.entry_engine import EntryEngine
            from trading.exit_engine import exit_engine
            
            bot_logger.info("Trading loop started")
            health_checker.update_status(bot_status="running")
            
            while self.running:
                try:
                    # Get all active users
                    active_users = await user_settings_repository.get_all_active_users()
                    
                    for user_settings in active_users:
                        user_id = user_settings['telegram_user_id']
                        
                        # Get user's selected assets
                        asset_mode = user_settings.get('asset_selection_mode', 'individual')
                        selected_assets = user_settings.get('selected_assets', [])
                        
                        # Get assets based on mode
                        if asset_mode == 'top_gainers':
                            from api.delta_client import delta_client
                            movers = await delta_client.get_top_movers(limit=10)
                            assets = movers['top_gainers']
                        elif asset_mode == 'top_losers':
                            from api.delta_client import delta_client
                            movers = await delta_client.get_top_movers(limit=10)
                            assets = movers['top_losers']
                        elif asset_mode == 'both':
                            from api.delta_client import delta_client
                            movers = await delta_client.get_top_movers(limit=10)
                            assets = movers['top_gainers'] + movers['top_losers']
                        elif asset_mode == 'all':
                            from api.delta_client import delta_client
                            products = await delta_client.get_products()
                            assets = [p for p in products if p.get('product_type') == 'future']
                        else:  # individual
                            assets = [{'symbol': s} for s in selected_assets]
                        
                        # Scan for entry signals
                        entry_engine = EntryEngine(user_settings)
                        
                        for asset in assets:
                            symbol = asset['symbol']
                            product_id = asset.get('product_id')
                            
                            # Scan for entry
                            signal = await entry_engine.scan_for_entry_signals(symbol, product_id)
                            
                            if signal:
                                # Execute entry
                                order_response = await entry_engine.execute_entry(signal)
                                
                                if order_response:
                                    # Create position record
                                    signal['telegram_user_id'] = user_id
                                    await position_manager.create_position(signal, order_response)
                        
                        # Manage open positions
                        open_positions = await position_manager.get_open_positions(user_id)
                        
                        for position in open_positions:
                            # Get current price
                            from api.delta_client import delta_client
                            candles = await delta_client.get_ohlc_candles(
                                symbol=position['symbol'],
                                resolution='1m',
                                start=int(asyncio.get_event_loop().time()) - 300,
                                end=int(asyncio.get_event_loop().time())
                            )
                            
                            if candles:
                                current_price = candles[-1]['close']
                                
                                # Manage exits
                                exit_result = await exit_engine.manage_exits(position, current_price)
                                
                                # Update position with exit actions
                                for action in exit_result.get('actions', []):
                                    if action['action'] in ['partial_exit', 'stop_loss_exit']:
                                        await position_manager.update_position_exit(
                                            str(position['_id']), action
                                        )
                                    elif action['action'] == 'trail_stop':
                                        await position_manager.update_stop_loss(
                                            str(position['_id']), action['new_stop_loss']
                                        )
                    
                    # Update health metrics
                    all_positions = await position_manager.get_open_positions()
                    health_checker.update_status(positions=len(all_positions))
                    
                    # Sleep before next iteration
                    await asyncio.sleep(60)  # Check every minute
                    
                except Exception as e:
                    bot_logger.error(f"Error in trading loop iteration: {str(e)}", exc_info=True)
                    await asyncio.sleep(30)
            
        except Exception as e:
            bot_logger.critical(f"Trading loop crashed: {str(e)}", exc_info=True)
    
    async def start(self):
        """Start the application"""
        try:
            self.running = True
            
            # Start Telegram bot
            await telegram_bot.start()
            
            # Start trading loop
            self.trading_task = asyncio.create_task(self.trading_loop())
            
            # Start health server (blocks until shutdown)
            await self.start_health_server()
            
        except Exception as e:
            bot_logger.critical(f"Application start failed: {str(e)}", exc_info=True)
            raise
    
    async def stop(self):
        """Stop the application"""
        try:
            bot_logger.info("Shutting down application...")
            self.running = False
            
            # Stop trading loop
            if self.trading_task:
                self.trading_task.cancel()
                try:
                    await self.trading_task
                except asyncio.CancelledError:
                    pass
            
            # Stop Telegram bot
            await telegram_bot.stop()
            
            # Close MongoDB
            await mongodb_client.close()
            
            # Stop health server
            if self.health_server:
                self.health_server.should_exit = True
            
            bot_logger.info("Application stopped")
            
        except Exception as e:
            bot_logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


# Application instance
app = TradingBotApp()


async def main():
    """Main entry point"""
    # Initialize application
    await app.initialize()
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        bot_logger.info("Received shutdown signal")
        asyncio.create_task(app.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    # Start application
    await app.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        bot_logger.info("Keyboard interrupt received")
    except Exception as e:
        bot_logger.critical(f"Application crashed: {str(e)}", exc_info=True)
                          
