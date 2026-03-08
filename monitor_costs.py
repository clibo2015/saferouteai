#!/usr/bin/env python3
"""
SafeRouteAI - Huawei Cloud Cost Monitor
Tracks spending against $100 coupon budget
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class CostAlert:
    threshold: float
    current_spend: float
    message: str
    severity: str

class CostMonitor:
    """Monitor Huawei Cloud costs and optimize spending"""
    
    def __init__(self, budget_limit: float = 100.0):
        self.budget_limit = budget_limit
        self.alert_thresholds = [50.0, 75.0, 90.0, 95.0]
        self.cost_history = []
        
    def get_mock_spending_data(self) -> Dict:
        """Generate mock spending data for demonstration"""
        # In production, this would call Huawei Cloud Billing API
        base_spend = 18.50  # Mock current spending including app hosting
        
        return {
            "total_spent": base_spend,
            "daily_spend": 2.80,
            "services": {
                "ECS_Hosting": 12.20,      # App hosting costs
                "ModelArts_Training": 3.20,
                "ModelArts_Inference": 1.80,
                "OBS_Storage": 0.80,
                "Data_Transfer": 0.50
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def calculate_projections(self, current_spend: float, daily_rate: float) -> Dict:
        """Calculate spending projections"""
        remaining_budget = self.budget_limit - current_spend
        days_remaining = remaining_budget / daily_rate if daily_rate > 0 else float('inf')
        
        return {
            "remaining_budget": remaining_budget,
            "daily_burn_rate": daily_rate,
            "projected_days_remaining": int(days_remaining),
            "projected_depletion_date": (datetime.now() + timedelta(days=days_remaining)).strftime("%Y-%m-%d") if days_remaining != float('inf') else "Never"
        }
    
    def check_alerts(self, current_spend: float) -> List[CostAlert]:
        """Check if any cost thresholds have been exceeded"""
        alerts = []
        spend_percentage = (current_spend / self.budget_limit) * 100
        
        for threshold in self.alert_thresholds:
            if spend_percentage >= threshold:
                severity = "HIGH" if threshold >= 90 else "MEDIUM" if threshold >= 75 else "LOW"
                alert = CostAlert(
                    threshold=threshold,
                    current_spend=current_spend,
                    message=f"Budget alert: {spend_percentage:.1f}% of ${self.budget_limit} budget used",
                    severity=severity
                )
                alerts.append(alert)
        
        return alerts
    
    def get_optimization_recommendations(self, spending_data: Dict) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        current_spend = spending_data["total_spent"]
        daily_spend = spending_data["daily_spend"]
        services = spending_data["services"]
        
        if daily_spend > 4.0:
            recommendations.append("🔥 High daily spend detected - consider scaling down services")
        
        if services.get("ECS_Hosting", 0) > 20:
            recommendations.append("🖥️ ECS hosting costs high - consider smaller instance or better auto-scaling")
        
        if services.get("ModelArts_Training", 0) > 15:
            recommendations.append("🤖 ModelArts training costs high - use CPU instances, limit job duration")
        
        if services.get("ModelArts_Inference", 0) > 10:
            recommendations.append("🔮 ModelArts inference costs high - enable auto-scaling to zero")
        
        if services.get("OBS_Storage", 0) > 5:
            recommendations.append("💾 OBS costs rising - implement data lifecycle policies")
        
        if current_spend > 50:
            recommendations.append("⚡ Enable aggressive auto-scaling to reduce idle resource costs")
            recommendations.append("📊 Schedule training jobs during off-peak hours if available")
        
        if current_spend > 75:
            recommendations.append("🚨 Consider pausing non-critical services")
            recommendations.append("🔍 Review and optimize all resource configurations")
        
        # AF-Johannesburg specific tips
        recommendations.append("🌍 Using AF-Johannesburg region for optimal costs")
        
        return recommendations
    
    def display_cost_report(self):
        """Display comprehensive cost report"""
        print("=" * 60)
        print("💰 SafeRouteAI - Huawei Cloud Cost Monitor")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Get spending data
        spending_data = self.get_mock_spending_data()
        current_spend = spending_data["total_spent"]
        
        # Calculate projections
        projections = self.calculate_projections(current_spend, spending_data["daily_spend"])
        
        # Budget overview
        print(f"\n📊 Budget Overview")
        print(f"   Total Budget:     ${self.budget_limit:.2f}")
        print(f"   Current Spend:    ${current_spend:.2f}")
        print(f"   Remaining:        ${projections['remaining_budget']:.2f}")
        print(f"   Usage:            {(current_spend/self.budget_limit)*100:.1f}%")
        
        # Spending breakdown
        print(f"\n💳 Service Breakdown")
        for service, cost in spending_data["services"].items():
            percentage = (cost / current_spend) * 100 if current_spend > 0 else 0
            print(f"   {service:<15}: ${cost:.2f} ({percentage:.1f}%)")
        
        # Projections
        print(f"\n📈 Projections")
        print(f"   Daily Burn Rate:  ${projections['daily_burn_rate']:.2f}")
        print(f"   Days Remaining:   {projections['projected_days_remaining']}")
        print(f"   Depletion Date:   {projections['projected_depletion_date']}")
        
        # Check for alerts
        alerts = self.check_alerts(current_spend)
        if alerts:
            print(f"\n🚨 Cost Alerts")
            for alert in alerts:
                icon = "🔴" if alert.severity == "HIGH" else "🟡" if alert.severity == "MEDIUM" else "🟢"
                print(f"   {icon} {alert.message}")
        
        # Recommendations
        recommendations = self.get_optimization_recommendations(spending_data)
        if recommendations:
            print(f"\n💡 Optimization Recommendations")
            for rec in recommendations:
                print(f"   {rec}")
        
        print("\n" + "=" * 60)
    
    def save_cost_history(self, spending_data: Dict):
        """Save cost data to history file"""
        history_file = "cost_history.json"
        
        # Load existing history
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Add current data
        history.append({
            "timestamp": datetime.now().isoformat(),
            "spending_data": spending_data
        })
        
        # Keep only last 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        history = [h for h in history if datetime.fromisoformat(h["timestamp"]) > cutoff_date]
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

def main():
    """Main monitoring function"""
    try:
        # Initialize cost monitor
        budget = float(os.getenv("MAX_BUDGET_USD", "100"))
        monitor = CostMonitor(budget_limit=budget)
        
        # Display cost report
        monitor.display_cost_report()
        
        # Save to history
        spending_data = monitor.get_mock_spending_data()
        monitor.save_cost_history(spending_data)
        
        print("💾 Cost data saved to cost_history.json")
        print("\n🔄 Run this script regularly to monitor your spending!")
        print("💡 Set up a cron job to run every hour: 0 * * * * python monitor_costs.py")
        
    except Exception as e:
        print(f"❌ Error monitoring costs: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())