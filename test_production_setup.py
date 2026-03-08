#!/usr/bin/env python3
"""
Test SafeRouteAI Production Setup
Validates all components without executing full deployment
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        from config import settings
        print("   ✅ config.py - Configuration management")
        
        from service_configurator import service_configurator
        print("   ✅ service_configurator.py - Huawei Cloud services")
        
        from obs_manager import obs_manager
        print("   ✅ obs_manager.py - OBS storage management")
        
        from cost_optimizer import cost_optimizer
        print("   ✅ cost_optimizer.py - Cost monitoring and optimization")
        
        from auto_scaler import auto_scaler
        print("   ✅ auto_scaler.py - Auto-scaling engine")
        
        from data_migrator import data_migrator
        print("   ✅ data_migrator.py - Data migration engine")
        
        from connection_validator import connection_validator
        print("   ✅ connection_validator.py - Connection validation")
        
        from production_orchestrator import production_orchestrator
        print("   ✅ production_orchestrator.py - Production deployment")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration settings"""
    print("\n📋 Testing configuration...")
    
    try:
        from config import settings
        
        # Test basic configuration
        print(f"   Region: {settings.huawei_cloud_region}")
        print(f"   Demo Mode: {settings.demo_mode}")
        print(f"   Production Mode: {settings.production_mode}")
        print(f"   Budget Limit: ${settings.max_budget_usd}")
        print(f"   Auto-scaling: {settings.auto_scale_enabled}")
        
        # Test credentials (without exposing them)
        has_credentials = bool(settings.huawei_cloud_ak and settings.huawei_cloud_sk and settings.huawei_cloud_project_id)
        print(f"   Credentials: {'✅ Configured' if has_credentials else '❌ Missing'}")
        
        # Test production status
        prod_status = settings.get_production_status()
        print(f"   Production Ready: {'✅ Yes' if prod_status['configuration_valid'] else '❌ No'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

def test_service_configuration():
    """Test service configuration capabilities"""
    print("\n🔧 Testing service configuration...")
    
    try:
        from service_configurator import service_configurator
        
        # Test ModelArts configuration
        modelarts_config = service_configurator.configure_modelarts()
        print(f"   ModelArts: {modelarts_config['status']}")
        
        # Test OBS configuration
        obs_config = service_configurator.configure_obs()
        print(f"   OBS: {obs_config['status']}")
        
        # Test GaussDB configuration (optional)
        gaussdb_config = service_configurator.configure_gaussdb()
        print(f"   GaussDB: {gaussdb_config['status']}")
        
        # Test cost summary
        cost_summary = service_configurator.get_cost_summary()
        print(f"   Estimated Monthly Cost: {cost_summary['total_estimated_monthly_cost']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Service configuration test failed: {e}")
        return False

def test_cost_monitoring():
    """Test cost monitoring system"""
    print("\n💰 Testing cost monitoring...")
    
    try:
        from cost_optimizer import cost_optimizer
        
        # Test spending data retrieval
        spending_data = cost_optimizer.get_current_spending()
        print(f"   Current Spend: ${spending_data['total_spent']}")
        print(f"   Daily Spend: ${spending_data['daily_spend']}")
        
        # Test budget status calculation
        budget_status = cost_optimizer.calculate_budget_status(spending_data)
        print(f"   Budget Usage: {budget_status.usage_percentage:.1f}%")
        print(f"   Days Remaining: {budget_status.projected_days_remaining}")
        
        # Test cost report generation
        cost_report = cost_optimizer.generate_cost_report()
        print(f"   Cost Report: {cost_report['report_id']}")
        print(f"   Active Alerts: {len(cost_report['active_alerts'])}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Cost monitoring test failed: {e}")
        return False

def test_data_migration():
    """Test data migration capabilities"""
    print("\n📦 Testing data migration...")
    
    try:
        from data_migrator import data_migrator
        
        # Test migration status
        migration_status = data_migrator.get_migration_status()
        print(f"   Migration Status: {migration_status['status']}")
        print(f"   OBS Bucket: {migration_status['obs_bucket']}")
        print(f"   Region: {migration_status['region']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Data migration test failed: {e}")
        return False

def test_connection_validation():
    """Test connection validation system"""
    print("\n🔍 Testing connection validation...")
    
    try:
        from connection_validator import connection_validator
        
        # Test validation summary
        validation_summary = connection_validator.get_validation_summary()
        print(f"   Validation Status: {validation_summary['status']}")
        
        if validation_summary['status'] != 'not_run':
            print(f"   Last Validation: {validation_summary['last_validation']}")
            print(f"   Success Rate: {validation_summary.get('success_rate', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Connection validation test failed: {e}")
        return False

def test_auto_scaling():
    """Test auto-scaling system"""
    print("\n⚡ Testing auto-scaling...")
    
    try:
        from auto_scaler import auto_scaler
        
        # Test usage pattern analysis
        usage_patterns = auto_scaler.analyze_usage_patterns()
        print(f"   Usage Patterns: {len(usage_patterns)} services analyzed")
        
        # Test scaling recommendations
        recommendations = auto_scaler.get_scaling_recommendations(75.0)  # 75% budget usage
        print(f"   Scaling Recommendations: {len(recommendations)} items")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Auto-scaling test failed: {e}")
        return False

def print_summary(test_results):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print()
    
    # Individual test results
    for test_name, passed in test_results.items():
        status_icon = "✅" if passed else "❌"
        print(f"{status_icon} {test_name}")
    
    print()
    
    if success_rate == 100:
        print("🎉 All tests passed! SafeRouteAI is ready for production deployment.")
        print("   Run: python deploy_production.py")
    elif success_rate >= 80:
        print("⚠️  Most tests passed. Review failed tests before production deployment.")
    else:
        print("❌ Multiple tests failed. Fix issues before attempting production deployment.")
    
    print()

def main():
    """Main test function"""
    print("🧪 SafeRouteAI Production Setup Test")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_results["Module Imports"] = test_imports()
    test_results["Configuration"] = test_configuration()
    test_results["Service Configuration"] = test_service_configuration()
    test_results["Cost Monitoring"] = test_cost_monitoring()
    test_results["Data Migration"] = test_data_migration()
    test_results["Connection Validation"] = test_connection_validation()
    test_results["Auto-scaling"] = test_auto_scaling()
    
    # Print summary
    print_summary(test_results)
    
    # Return exit code
    all_passed = all(test_results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())