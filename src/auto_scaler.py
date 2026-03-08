"""
Auto Scaler for SafeRouteAI Production
Automatic service scaling and cost optimization based on usage patterns
"""

import logging
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from config import settings

logger = logging.getLogger(__name__)

class ScalingAction(Enum):
    SCALE_UP = "SCALE_UP"
    SCALE_DOWN = "SCALE_DOWN"
    SCALE_TO_ZERO = "SCALE_TO_ZERO"
    MAINTAIN = "MAINTAIN"
    PAUSE_SERVICE = "PAUSE_SERVICE"

class ServiceType(Enum):
    MODELARTS_TRAINING = "MODELARTS_TRAINING"
    MODELARTS_INFERENCE = "MODELARTS_INFERENCE"
    ECS_INSTANCE = "ECS_INSTANCE"
    OBS_STORAGE = "OBS_STORAGE"

@dataclass
class UsagePattern:
    service_name: str
    current_utilization: float
    avg_utilization_1h: float
    avg_utilization_24h: float
    request_count_1h: int
    request_count_24h: int
    idle_time_minutes: int
    peak_usage_time: str
    cost_per_hour: float

@dataclass
class ScalingDecision:
    service_name: str
    current_instances: int
    target_instances: int
    action: ScalingAction
    reason: str
    estimated_cost_impact: float
    execution_time: str
    confidence: float

class AutoScaler:
    """Automatic service scaling for cost optimization"""
    
    def __init__(self):
        self.region = settings.huawei_cloud_region or "af-south-1"
        self.demo_mode = settings.demo_mode
        self.scaling_history = []
        self.scaling_policies = self._initialize_scaling_policies()
        
        # Cost thresholds for aggressive scaling
        self.budget_limit = float(os.getenv("MAX_BUDGET_USD", "100"))
        self.aggressive_scaling_threshold = 80.0  # 80% budget usage
        self.emergency_scaling_threshold = 95.0   # 95% budget usage
    
    def _initialize_scaling_policies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize scaling policies for different services"""
        return {
            "modelarts_training": {
                "min_instances": 0,  # Can scale to zero
                "max_instances": 2,  # Limit for cost control
                "scale_up_threshold": 0.8,  # 80% utilization
                "scale_down_threshold": 0.3,  # 30% utilization
                "idle_timeout_minutes": 15,  # Scale to zero after 15 min idle
                "cost_per_instance_hour": 2.5,
                "auto_scaling_enabled": True
            },
            "modelarts_inference": {
                "min_instances": 0,  # Can scale to zero
                "max_instances": 3,  # Limit for cost control
                "scale_up_threshold": 0.7,  # 70% utilization
                "scale_down_threshold": 0.2,  # 20% utilization
                "idle_timeout_minutes": 10,  # Scale to zero after 10 min idle
                "cost_per_instance_hour": 1.5,
                "auto_scaling_enabled": True
            },
            "ecs_hosting": {
                "min_instances": 1,  # Keep at least 1 for API
                "max_instances": 2,  # Limit for cost control
                "scale_up_threshold": 0.8,  # 80% CPU utilization
                "scale_down_threshold": 0.4,  # 40% CPU utilization
                "idle_timeout_minutes": 60,  # Longer timeout for hosting
                "cost_per_instance_hour": 0.8,
                "auto_scaling_enabled": True
            }
        }
    
    def analyze_usage_patterns(self) -> List[UsagePattern]:
        """Analyze current usage patterns for all services"""
        logger.info("Analyzing usage patterns for auto-scaling...")
        
        if self.demo_mode:
            return self._generate_mock_usage_patterns()
        
        # In production, this would collect real metrics from Huawei Cloud
        return self._generate_mock_usage_patterns()
    
    def _generate_mock_usage_patterns(self) -> List[UsagePattern]:
        """Generate realistic mock usage patterns"""
        import random
        
        current_hour = datetime.now().hour
        
        # Simulate realistic usage patterns based on time of day
        base_utilization = 0.3 if 22 <= current_hour or current_hour <= 6 else 0.6
        
        patterns = [
            UsagePattern(
                service_name="modelarts_training",
                current_utilization=random.uniform(0.1, 0.4),  # Usually low
                avg_utilization_1h=random.uniform(0.1, 0.3),
                avg_utilization_24h=random.uniform(0.2, 0.4),
                request_count_1h=random.randint(0, 5),  # Few training requests
                request_count_24h=random.randint(5, 20),
                idle_time_minutes=random.randint(30, 120),  # Often idle
                peak_usage_time="09:00-11:00",
                cost_per_hour=2.5
            ),
            UsagePattern(
                service_name="modelarts_inference",
                current_utilization=base_utilization + random.uniform(-0.2, 0.2),
                avg_utilization_1h=base_utilization + random.uniform(-0.1, 0.1),
                avg_utilization_24h=random.uniform(0.4, 0.7),
                request_count_1h=random.randint(10, 50),
                request_count_24h=random.randint(200, 800),
                idle_time_minutes=random.randint(5, 30),
                peak_usage_time="08:00-17:00",
                cost_per_hour=1.5
            ),
            UsagePattern(
                service_name="ecs_hosting",
                current_utilization=base_utilization + random.uniform(-0.1, 0.3),
                avg_utilization_1h=base_utilization + random.uniform(-0.1, 0.2),
                avg_utilization_24h=random.uniform(0.5, 0.8),
                request_count_1h=random.randint(50, 200),
                request_count_24h=random.randint(1000, 3000),
                idle_time_minutes=random.randint(0, 10),  # Rarely idle
                peak_usage_time="07:00-19:00",
                cost_per_hour=0.8
            )
        ]
        
        return patterns
    
    def make_scaling_decisions(self, usage_patterns: List[UsagePattern], budget_usage_percent: float) -> List[ScalingDecision]:
        """Make scaling decisions based on usage patterns and budget"""
        logger.info(f"Making scaling decisions (Budget usage: {budget_usage_percent:.1f}%)...")
        
        decisions = []
        
        for pattern in usage_patterns:
            decision = self._analyze_service_scaling(pattern, budget_usage_percent)
            if decision:
                decisions.append(decision)
        
        return decisions
    
    def _analyze_service_scaling(self, pattern: UsagePattern, budget_usage_percent: float) -> Optional[ScalingDecision]:
        """Analyze scaling needs for a specific service"""
        service_name = pattern.service_name
        
        # Get scaling policy for this service
        policy_key = service_name.replace("_", "_").lower()
        if policy_key not in self.scaling_policies:
            return None
        
        policy = self.scaling_policies[policy_key]
        
        # Current instance count (simulated)
        current_instances = self._get_current_instance_count(service_name)
        
        # Determine scaling action based on multiple factors
        action, target_instances, reason = self._determine_scaling_action(
            pattern, policy, current_instances, budget_usage_percent
        )
        
        # Calculate cost impact
        cost_impact = (target_instances - current_instances) * policy["cost_per_instance_hour"]
        
        # Calculate confidence based on data quality and consistency
        confidence = self._calculate_scaling_confidence(pattern)
        
        return ScalingDecision(
            service_name=service_name,
            current_instances=current_instances,
            target_instances=target_instances,
            action=action,
            reason=reason,
            estimated_cost_impact=cost_impact,
            execution_time=datetime.now().isoformat(),
            confidence=confidence
        )
    
    def _determine_scaling_action(self, pattern: UsagePattern, policy: Dict[str, Any], 
                                current_instances: int, budget_usage_percent: float) -> tuple:
        """Determine the appropriate scaling action"""
        
        # Emergency budget protection
        if budget_usage_percent >= self.emergency_scaling_threshold:
            if current_instances > policy["min_instances"]:
                return ScalingAction.SCALE_TO_ZERO, policy["min_instances"], "Emergency budget protection"
        
        # Aggressive cost optimization
        if budget_usage_percent >= self.aggressive_scaling_threshold:
            if pattern.idle_time_minutes > policy["idle_timeout_minutes"]:
                return ScalingAction.SCALE_TO_ZERO, policy["min_instances"], "Aggressive cost optimization - service idle"
            elif pattern.current_utilization < policy["scale_down_threshold"]:
                target = max(policy["min_instances"], current_instances - 1)
                return ScalingAction.SCALE_DOWN, target, "Aggressive cost optimization - low utilization"
        
        # Normal scaling logic
        if pattern.idle_time_minutes > policy["idle_timeout_minutes"] and current_instances > policy["min_instances"]:
            return ScalingAction.SCALE_TO_ZERO, policy["min_instances"], f"Service idle for {pattern.idle_time_minutes} minutes"
        
        elif pattern.current_utilization > policy["scale_up_threshold"] and current_instances < policy["max_instances"]:
            target = min(policy["max_instances"], current_instances + 1)
            return ScalingAction.SCALE_UP, target, f"High utilization: {pattern.current_utilization:.1%}"
        
        elif pattern.current_utilization < policy["scale_down_threshold"] and current_instances > policy["min_instances"]:
            target = max(policy["min_instances"], current_instances - 1)
            return ScalingAction.SCALE_DOWN, target, f"Low utilization: {pattern.current_utilization:.1%}"
        
        else:
            return ScalingAction.MAINTAIN, current_instances, "Utilization within normal range"
    
    def _get_current_instance_count(self, service_name: str) -> int:
        """Get current instance count for service (simulated)"""
        # In production, this would query actual Huawei Cloud services
        import random
        
        if "training" in service_name:
            return random.randint(0, 2)
        elif "inference" in service_name:
            return random.randint(1, 3)
        elif "hosting" in service_name:
            return random.randint(1, 2)
        else:
            return 1
    
    def _calculate_scaling_confidence(self, pattern: UsagePattern) -> float:
        """Calculate confidence in scaling decision"""
        confidence = 0.8  # Base confidence
        
        # Increase confidence if utilization is consistent
        utilization_variance = abs(pattern.current_utilization - pattern.avg_utilization_1h)
        if utilization_variance < 0.1:
            confidence += 0.1
        
        # Increase confidence if there's sufficient data
        if pattern.request_count_24h > 100:
            confidence += 0.1
        
        # Decrease confidence if service is highly variable
        if utilization_variance > 0.3:
            confidence -= 0.2
        
        return max(0.5, min(1.0, confidence))
    
    def execute_scaling_decisions(self, decisions: List[ScalingDecision]) -> Dict[str, Any]:
        """Execute scaling decisions"""
        logger.info(f"Executing {len(decisions)} scaling decisions...")
        
        execution_results = []
        total_cost_impact = 0.0
        
        for decision in decisions:
            result = self._execute_single_scaling_decision(decision)
            execution_results.append(result)
            
            if result["success"]:
                total_cost_impact += decision.estimated_cost_impact
        
        # Log scaling actions
        self._log_scaling_actions(decisions, execution_results)
        
        return {
            "status": "completed",
            "decisions_executed": len(decisions),
            "successful_executions": len([r for r in execution_results if r["success"]]),
            "total_cost_impact": round(total_cost_impact, 2),
            "execution_results": execution_results,
            "execution_time": datetime.now().isoformat()
        }
    
    def _execute_single_scaling_decision(self, decision: ScalingDecision) -> Dict[str, Any]:
        """Execute a single scaling decision"""
        service_name = decision.service_name
        
        if self.demo_mode:
            # Simulate execution
            success = decision.confidence > 0.6  # Higher confidence = higher success rate
            
            return {
                "service_name": service_name,
                "action": decision.action.value,
                "target_instances": decision.target_instances,
                "success": success,
                "message": f"Simulated {decision.action.value} for {service_name}" if success else "Simulation failed",
                "cost_impact": decision.estimated_cost_impact if success else 0.0,
                "execution_time": datetime.now().isoformat()
            }
        
        try:
            # In production, this would call actual Huawei Cloud APIs
            if decision.action == ScalingAction.SCALE_TO_ZERO:
                result = self._scale_service_to_zero(service_name)
            elif decision.action == ScalingAction.SCALE_UP:
                result = self._scale_service_up(service_name, decision.target_instances)
            elif decision.action == ScalingAction.SCALE_DOWN:
                result = self._scale_service_down(service_name, decision.target_instances)
            else:
                result = {"success": True, "message": "No action required"}
            
            return {
                "service_name": service_name,
                "action": decision.action.value,
                "target_instances": decision.target_instances,
                "success": result["success"],
                "message": result["message"],
                "cost_impact": decision.estimated_cost_impact if result["success"] else 0.0,
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute scaling for {service_name}: {e}")
            return {
                "service_name": service_name,
                "action": decision.action.value,
                "success": False,
                "message": str(e),
                "cost_impact": 0.0,
                "execution_time": datetime.now().isoformat()
            }
    
    def _scale_service_to_zero(self, service_name: str) -> Dict[str, bool]:
        """Scale service to zero instances"""
        logger.info(f"Scaling {service_name} to zero instances")
        
        # In production, this would call Huawei Cloud APIs
        # For ModelArts: Stop training jobs, scale inference to 0
        # For ECS: Stop instances (if allowed by policy)
        
        return {"success": True, "message": f"Scaled {service_name} to zero"}
    
    def _scale_service_up(self, service_name: str, target_instances: int) -> Dict[str, bool]:
        """Scale service up"""
        logger.info(f"Scaling {service_name} up to {target_instances} instances")
        
        # In production, this would call Huawei Cloud APIs
        return {"success": True, "message": f"Scaled {service_name} up to {target_instances}"}
    
    def _scale_service_down(self, service_name: str, target_instances: int) -> Dict[str, bool]:
        """Scale service down"""
        logger.info(f"Scaling {service_name} down to {target_instances} instances")
        
        # In production, this would call Huawei Cloud APIs
        return {"success": True, "message": f"Scaled {service_name} down to {target_instances}"}
    
    def _log_scaling_actions(self, decisions: List[ScalingDecision], results: List[Dict[str, Any]]):
        """Log scaling actions for audit and analysis"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "decisions": [
                    {
                        "service": d.service_name,
                        "action": d.action.value,
                        "reason": d.reason,
                        "cost_impact": d.estimated_cost_impact,
                        "confidence": d.confidence
                    } for d in decisions
                ],
                "results": results
            }
            
            # Save to scaling history
            scaling_log_file = "data/scaling_history.json"
            
            if os.path.exists(scaling_log_file):
                with open(scaling_log_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            history.append(log_entry)
            
            # Keep only last 100 entries
            history = history[-100:]
            
            with open(scaling_log_file, 'w') as f:
                json.dump(history, f, indent=2)
                
            logger.info(f"Scaling actions logged to {scaling_log_file}")
            
        except Exception as e:
            logger.error(f"Failed to log scaling actions: {e}")
    
    def get_scaling_recommendations(self, budget_usage_percent: float) -> List[str]:
        """Get scaling recommendations based on current situation"""
        recommendations = []
        
        if budget_usage_percent >= self.emergency_scaling_threshold:
            recommendations.extend([
                "🚨 EMERGENCY: Scale all non-essential services to zero immediately",
                "🛑 Stop all ModelArts training jobs",
                "📉 Scale inference endpoints to minimum required",
                "⏸️ Pause background processing tasks"
            ])
        elif budget_usage_percent >= self.aggressive_scaling_threshold:
            recommendations.extend([
                "⚠️ AGGRESSIVE: Enable aggressive auto-scaling policies",
                "🔄 Scale idle services to zero after 5 minutes",
                "📊 Monitor utilization every 5 minutes",
                "💰 Prioritize cost savings over performance"
            ])
        else:
            recommendations.extend([
                "✅ NORMAL: Standard auto-scaling policies active",
                "🎯 Scale based on utilization thresholds",
                "⏰ Scale to zero after idle timeout",
                "📈 Balance performance and cost optimization"
            ])
        
        # Service-specific recommendations
        recommendations.extend([
            "🤖 ModelArts: Use CPU instances, enable auto-scaling to zero",
            "🖥️ ECS: Optimize instance types, enable auto-scaling",
            "💾 OBS: Use lifecycle policies for automatic cost optimization",
            "🌍 Regional: All services in AF-Johannesburg for cost efficiency"
        ])
        
        return recommendations
    
    def run_auto_scaling_cycle(self, budget_usage_percent: float) -> Dict[str, Any]:
        """Run complete auto-scaling cycle"""
        logger.info("Running auto-scaling cycle...")
        
        try:
            # Analyze usage patterns
            usage_patterns = self.analyze_usage_patterns()
            
            # Make scaling decisions
            decisions = self.make_scaling_decisions(usage_patterns, budget_usage_percent)
            
            # Execute decisions
            execution_results = self.execute_scaling_decisions(decisions)
            
            # Get recommendations
            recommendations = self.get_scaling_recommendations(budget_usage_percent)
            
            return {
                "status": "completed",
                "cycle_time": datetime.now().isoformat(),
                "budget_usage_percent": budget_usage_percent,
                "usage_patterns": [
                    {
                        "service": p.service_name,
                        "utilization": p.current_utilization,
                        "idle_time": p.idle_time_minutes,
                        "cost_per_hour": p.cost_per_hour
                    } for p in usage_patterns
                ],
                "scaling_decisions": len(decisions),
                "execution_results": execution_results,
                "recommendations": recommendations,
                "next_cycle": (datetime.now() + timedelta(minutes=15)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Auto-scaling cycle failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "cycle_time": datetime.now().isoformat()
            }

# Global auto scaler instance
auto_scaler = AutoScaler()