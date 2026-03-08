#!/usr/bin/env python3
"""
SafeRouteAI ModelArts Training Job Setup
Comprehensive setup script for cost-optimized ModelArts training using real SA crime data
Implements task 7.1: Set up ModelArts training job configuration
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main setup function for ModelArts training configuration"""
    print("=" * 80)
    print("SafeRouteAI ModelArts Training Job Configuration Setup")
    print("Task 7.1: Set up ModelArts training job configuration")
    print("=" * 80)
    
    try:
        # Add src to path for imports
        import sys
        sys.path.append('src')
        
        # Import required modules
        from modelarts_training_config import training_configurator
        from cost_optimizer import cost_optimizer
        from obs_manager import obs_manager
        from config import settings
        
        print(f"\n🌍 Region: {settings.huawei_cloud_region}")
        print(f"💰 Budget: ${settings.max_budget_usd}")
        print(f"🔧 Mode: {'Demo' if settings.demo_mode else 'Production'}")
        
        # Step 1: Check current budget status
        print("\n" + "="*50)
        print("STEP 1: Budget Analysis")
        print("="*50)
        
        cost_summary = cost_optimizer.get_cost_summary()
        remaining_budget = cost_summary["remaining_budget"]
        
        print(f"💵 Current Spend: ${cost_summary['current_spend']}")
        print(f"💰 Remaining Budget: ${remaining_budget}")
        print(f"📊 Usage: {cost_summary['usage_percentage']:.1f}%")
        print(f"🔥 Daily Burn Rate: ${cost_summary['daily_burn_rate']}")
        
        if remaining_budget < 5.0:
            print("⚠️  WARNING: Low budget remaining - using ultra-budget template only")
            available_budget = min(5.0, remaining_budget)
        else:
            available_budget = min(20.0, remaining_budget * 0.2)  # Max 20% for training
        
        print(f"🎯 Training Budget Allocation: ${available_budget}")
        
        # Step 2: Set up OBS storage structure
        print("\n" + "="*50)
        print("STEP 2: OBS Storage Setup")
        print("="*50)
        
        # Create bucket and data structure
        bucket_result = obs_manager.create_bucket_with_optimization()
        print(f"📦 Bucket Status: {bucket_result['status']}")
        
        if bucket_result["status"] in ["success", "demo_mode"]:
            print(f"✅ Bucket: {bucket_result['bucket_name']}")
            print(f"🌍 Region: {bucket_result['region']}")
            print(f"💾 Storage Class: {bucket_result['storage_class']}")
            
            # Set up data structure
            structure_result = obs_manager.setup_data_structure()
            print(f"📁 Data Structure: {structure_result['status']}")
            
            if structure_result["status"] in ["success", "demo_mode"]:
                print(f"📂 Created folders: {len(structure_result.get('created_folders', []))}")
        
        # Step 3: Prepare training data
        print("\n" + "="*50)
        print("STEP 3: Training Data Preparation")
        print("="*50)
        
        data_setup_result = training_configurator.setup_obs_training_data()
        print(f"📊 Data Setup: {data_setup_result['status']}")
        
        if data_setup_result["status"] in ["success", "demo_mode"]:
            print(f"📈 Training Samples: {data_setup_result['data_size']:,}")
            print(f"🔢 Features: {len(data_setup_result['features'])}")
            print(f"📍 OBS Path: {data_setup_result['obs_path']}")
            
            # Display feature summary
            print("🎯 Key Features:")
            for feature in data_setup_result['features'][:8]:  # Show first 8 features
                print(f"   • {feature}")
            if len(data_setup_result['features']) > 8:
                print(f"   • ... and {len(data_setup_result['features']) - 8} more")
        
        # Step 4: Create training templates
        print("\n" + "="*50)
        print("STEP 4: Training Template Creation")
        print("="*50)
        
        templates = training_configurator.create_cost_optimized_templates()
        print(f"📋 Created Templates: {len(templates)}")
        
        print("\n💡 Available Training Templates:")
        for i, template in enumerate(templates, 1):
            affordable = "✅" if template.estimated_total_cost <= available_budget else "❌"
            print(f"{i}. {affordable} {template.name}")
            print(f"   💰 Cost: ${template.estimated_total_cost} ({template.max_training_hours}h)")
            print(f"   🖥️  Instance: {template.instance_type}")
            print(f"   🎛️  Optimization: {template.optimization_level}")
            print()
        
        # Step 5: Select optimal template
        print("="*50)
        print("STEP 5: Template Selection")
        print("="*50)
        
        optimal_template = training_configurator.select_optimal_template(
            available_budget=available_budget,
            performance_priority="cost"
        )
        
        print(f"🎯 Selected Template: {optimal_template.name}")
        print(f"💰 Estimated Cost: ${optimal_template.estimated_total_cost}")
        print(f"⏱️  Max Training Time: {optimal_template.max_training_hours} hours")
        print(f"🖥️  Instance Type: {optimal_template.instance_type}")
        print(f"🔧 Optimization Level: {optimal_template.optimization_level}")
        
        # Step 6: Create training job configuration
        print("\n" + "="*50)
        print("STEP 6: Training Job Configuration")
        print("="*50)
        
        training_config = training_configurator.create_training_job_config(
            template=optimal_template,
            crime_data_path=data_setup_result['obs_path']
        )
        
        print(f"🏷️  Job Name: {training_config.job_name}")
        print(f"📊 Data Path: {training_config.data_config['training_data_path']}")
        print(f"📤 Output Path: {training_config.template.output_path}")
        
        # Display hyperparameters
        print("\n🎛️  Hyperparameters:")
        for param, value in training_config.template.hyperparameters.items():
            print(f"   • {param}: {value}")
        
        # Display cost controls
        print("\n💰 Cost Controls:")
        for control, value in training_config.cost_controls.items():
            print(f"   • {control}: {value}")
        
        # Step 7: Save configuration
        print("\n" + "="*50)
        print("STEP 7: Configuration Persistence")
        print("="*50)
        
        # Save training configuration
        config_file = Path("data/training_job_config.json")
        config_data = {
            "job_name": training_config.job_name,
            "template": training_config.template.__dict__,
            "data_config": training_config.data_config,
            "resource_config": training_config.resource_config,
            "cost_controls": training_config.cost_controls,
            "monitoring_config": training_config.monitoring_config,
            "created_at": datetime.now().isoformat(),
            "budget_analysis": {
                "available_budget": available_budget,
                "estimated_cost": optimal_template.estimated_total_cost,
                "budget_utilization": (optimal_template.estimated_total_cost / available_budget) * 100
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print(f"💾 Configuration saved: {config_file}")
        
        # Step 8: Display setup summary
        print("\n" + "="*80)
        print("SETUP SUMMARY")
        print("="*80)
        
        status_summary = training_configurator.get_training_status_summary()
        
        print(f"✅ Configuration Status: {status_summary['configuration_status']}")
        print(f"📋 Available Templates: {status_summary['available_templates']}")
        print(f"🎯 Recommended Template: {status_summary['recommended_template']}")
        print(f"💰 Budget Allocation: ${available_budget} of ${settings.max_budget_usd}")
        print(f"🌍 Region: {status_summary['region']}")
        print(f"🔧 Mode: {'Demo' if status_summary['demo_mode'] else 'Production'}")
        
        print("\n🚀 Cost Optimization Features:")
        for feature in status_summary['cost_optimization_features']:
            print(f"   • {feature}")
        
        # Step 9: Provide next steps
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        
        print("1. Submit Training Job:")
        print("   python submit_training_job.py")
        print()
        print("2. Monitor Training Progress:")
        print("   python monitor_training.py")
        print()
        print("3. Monitor Costs:")
        print("   python monitor_costs.py")
        print()
        print("4. Deploy Model (after training):")
        print("   python deploy_model.py")
        
        # Create quick submission script
        create_submission_script(training_config)
        
        print("\n" + "="*80)
        print("✅ ModelArts Training Configuration Setup Complete!")
        print("Task 7.1 Successfully Implemented")
        print("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check Huawei Cloud credentials")
        print("2. Verify region configuration (af-south-1)")
        print("3. Ensure sufficient budget remaining")
        print("4. Check network connectivity")
        return False

def create_submission_script(training_config):
    """Create a quick training job submission script"""
    submission_script = """#!/usr/bin/env python3
\"\"\"
Quick Training Job Submission Script
Generated by SafeRouteAI ModelArts Setup
\"\"\"

import logging
from src.modelarts_training_config import training_configurator
from src.cost_optimizer import cost_optimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def submit_training_job():
    \"\"\"Submit the configured training job\"\"\"
    print("🚀 Submitting SafeRouteAI Training Job...")
    
    # Add src to path
    import sys
    sys.path.append('src')
    
    from modelarts_training_config import training_configurator
    from cost_optimizer import cost_optimizer
    
    # Load configuration
    import json
    with open("data/training_job_config.json", 'r') as f:
        config_data = json.load(f)
    
    print(f"📋 Job Name: {config_data['job_name']}")
    print(f"💰 Estimated Cost: ${config_data['template']['estimated_total_cost']}")
    
    # Check budget before submission
    cost_summary = cost_optimizer.get_cost_summary()
    if cost_summary['remaining_budget'] < config_data['template']['estimated_total_cost']:
        print("❌ Insufficient budget remaining!")
        return False
    
    # Submit job (this would be implemented based on the actual config)
    print("✅ Training job configuration ready for submission")
    print("💡 In production mode, this would submit to ModelArts")
    
    return True

if __name__ == "__main__":
    submit_training_job()
"""
    
    with open("submit_training_job.py", 'w') as f:
        f.write(submission_script)
    
    print("📝 Created submission script: submit_training_job.py")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)