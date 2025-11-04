"""
Health check HTTP server for UptimeRobot monitoring
"""
from fastapi import FastAPI
from typing import Dict
from datetime import datetime


app = FastAPI(title="Delta VRZ Bot Health Check")


class HealthCheckServer:
    """Health check endpoints for monitoring"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.bot_status = "starting"
        self.delta_api_status = "unknown"
        self.mongodb_status = "unknown"
        self.active_positions_count = 0
    
    def update_status(self, bot_status: str = None, delta_api: str = None, 
                     mongodb: str = None, positions: int = None):
        """Update health check status"""
        if bot_status:
            self.bot_status = bot_status
        if delta_api:
            self.delta_api_status = delta_api
        if mongodb:
            self.mongodb_status = mongodb
        if positions is not None:
            self.active_positions_count = positions


health_checker = HealthCheckServer()


@app.get("/")
@app.head("/")
async def root_health_check() -> Dict:
    """Simple health check for UptimeRobot"""
    return {
        "status": "alive",
        "bot_status": health_checker.bot_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def detailed_health_check() -> Dict:
    """Detailed health check with component status"""
    uptime = (datetime.utcnow() - health_checker.start_time).total_seconds()
    
    return {
        "status": "healthy" if health_checker.bot_status == "running" else "degraded",
        "uptime_seconds": uptime,
        "components": {
            "bot": health_checker.bot_status,
            "delta_api": health_checker.delta_api_status,
            "mongodb": health_checker.mongodb_status
        },
        "metrics": {
            "active_positions": health_checker.active_positions_count
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ping")
async def ping() -> Dict:
    """Simple ping endpoint"""
    return {"pong": True}
  
