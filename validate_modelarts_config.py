#!/usr/bin/env python3
"""
Simple validation script for ModelArts training configuration
Validates task 7.1 implementation without complex test framework
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.append('src')

def validate_implementation():
    """Validate the ModelArts training configuration implementation"""
    print("=" * 60)
    print("VALIDATING MODELARTS TRAINING CONFIGURATION")
    print("Task 7.1: Set up ModelArts training job configuration")
    print("=" * 60)
    
    validation_results = []
    
    # Test 1: Module imports
    print("\n1. Testing module imports...")
    try:
        from modelarts_training_config import training_configurator
        from cost_optimizer import cost_optimizer
        from obs_manager import obs_manager
        from config import settings
        print("   ✅ All required modules imported successfully")
        validation_results.append(("Module Imports", True))
    except Exception as e:
        print(f"   ❌ Module import failed: {e}")
        validation_results.append(("Module Imports", False))
        return False
    
    # Test 2: Template creation
    print("\n2. Testing training template creation...")
    try:
        templates = training_configurator.create_cost_optimized_templates()
        
        if len(templates) == 4:
            print(f"   ✅ Created {len(templates)} training templates")
            
            # Check ultra-budget template
            ultra_budget = templates[0]
            if ultra_budget.estimated_total_cost <= 1.0:
                print(f"   ✅ Ultra-budget template cost: ${ultra_budget.estimated_total_cost}")
            else:
                print(f"   ⚠️  Ultra-budget template cost higher than expected: ${ultra_budget.estimated_total_cost}")
            
            # Check all templates have required fields
            all_valid = True
            for template in templates:
                if not all([template.template_id, template.name, template.instance_type]):
                    all_valid = False
                    break
            
            if all_valid:
                print("   ✅ All templates have required fields")
                validation_results.append(("Template Creation", True))
            else:
                print("   ❌ Some templates missing required fields")
                validation_results.append(("Template Creation", False))
        else:
            print(f"   ❌ Expected 4 templates, got {len(templates)}")
            validation_results.append(("Template Creation", False))
            
    except Exception as e:
        print(f"   ❌ Template creation failed: {e}")
        validation_results.append(("Template Creation", False))
    
    # Test 3: Budget-based template selection
    print("\n3. Testing budget-based template selection...")
    try:
        # Test with low budget
        low_budget_template = training_configurator.select_optimal_template(
            available_budget=0.75, 
            performance_priority="cost"
        )
        
        if low_budget_template.template_id == "saferoute-ultra-budget-cpu":
            print("   ✅ Low budget correctly selects ultra-budget template")
            
            # Test with higher budget
            high_budget_template = training_configurator.select_optimal_template(
                available_budget=5.0, 
                performance_priority="cost"
            )
            
            if high_budget_template.estimated_total_cost <= 5.0:
                print("   ✅ Budget constraints respected in template selection")
                validation_results.append(("Template Selection", True))
            else:
                print("   ❌ Template selection exceeds budget")
                validation_results.append(("Template Selection", False))
        else:
            print("   ❌ Low budget template selection incorrect")
            validation_results.append(("Template Selection", False))
            
    except Exception as e:
        print(f"   ❌ Template selection failed: {e}")
        validation_results.append(("Template Selection", False))
    
    # Test 4: Training job configuration
    print("\n4. Testing training job configuration creation...")
    try:
        templates = training_configurator.create_cost_optimized_templates()
        template = templates[0]  # Ultra-budget template
        
        config = training_configurator.create_training_job_config(
            template=template,
            crime_data_path="obs://test-bucket/crime-data/processed/"
        )
        
        # Verify configuration structure
        required_fields = ['job_name', 'template', 'data_config', 'resource_config', 'cost_controls']
        all_present = all(hasattr(config, field) for field in required_fields)
        
        if all_present:
            print("   ✅ Training job configuration has all required fields")
            
            # Check cost controls
            if config.cost_controls.get('auto_stop_on_budget', False):
                print("   ✅ Cost controls properly configured")
                validation_results.append(("Job Configuration", True))
            else:
                print("   ❌ Cost controls not properly configured")
                validation_results.append(("Job Configuration", False))
        else:
            print("   ❌ Training job configuration missing required fields")
            validation_results.append(("Job Configuration", False))
            
    except Exception as e:
        print(f"   ❌ Job configuration creation failed: {e}")
        validation_results.append(("Job Configuration", False))
    
    # Test 5: Training data preparation
    print("\n5. Testing training data preparation...")
    try:
        # Create mock crime data
        import pandas as pd
        mock_crime_data = pd.DataFrame({
            'station': ['Test Station'],
            'province': ['Gauteng'],
            'latitude': [-26.2041],
            'longitude': [28.0473],
            'year': [2024],
            'crime_category': ['Murder'],
            'incidents': [10],
            'crime_rate_per_100k': [50.0],
            'socio_economic_index': [0.6],
            'unemployment_rate': [30.0],
            'area_type': ['urban'],
            'crime_severity_score': [0.8]
        })
        
        # Prepare training data
        training_data = training_configurator._prepare_training_data(mock_crime_data)
        
        # Check required columns
        required_columns = ['latitude', 'longitude', 'risk_level', 'crime_category_encoded']
        columns_present = all(col in training_data.columns for col in required_columns)
        
        if columns_present and len(training_data) > 0:
            print("   ✅ Training data preparation successful")
            
            # Check risk level calculation
            risk_levels = training_data['risk_level'].values
            if all(0 <= risk <= 1 for risk in risk_levels):
                print("   ✅ Risk levels properly normalized (0-1)")
                validation_results.append(("Data Preparation", True))
            else:
                print("   ❌ Risk levels not properly normalized")
                validation_results.append(("Data Preparation", False))
        else:
            print("   ❌ Training data preparation incomplete")
            validation_results.append(("Data Preparation", False))
            
    except Exception as e:
        print(f"   ❌ Data preparation failed: {e}")
        validation_results.append(("Data Preparation", False))
    
    # Test 6: Cost optimization features
    print("\n6. Testing cost optimization features...")
    try:
        templates = training_configurator.create_cost_optimized_templates()
        
        # Check all templates have cost optimization
        cost_optimized = True
        for template in templates:
            if not template.auto_stop_enabled or template.max_training_hours > 3:
                cost_optimized = False
                break
        
        if cost_optimized:
            print("   ✅ All templates have cost optimization enabled")
            
            # Check ultra-budget template specifically
            ultra_budget = templates[0]
            if (ultra_budget.max_training_hours == 1 and 
                ultra_budget.estimated_total_cost <= 1.0 and
                ultra_budget.optimization_level == "ultra_aggressive"):
                print("   ✅ Ultra-budget template properly optimized for $100 budget")
                validation_results.append(("Cost Optimization", True))
            else:
                print("   ❌ Ultra-budget template not optimally configured")
                validation_results.append(("Cost Optimization", False))
        else:
            print("   ❌ Some templates lack proper cost optimization")
            validation_results.append(("Cost Optimization", False))
            
    except Exception as e:
        print(f"   ❌ Cost optimization validation failed: {e}")
        validation_results.append(("Cost Optimization", False))
    
    # Test 7: Configuration file persistence
    print("\n7. Testing configuration file creation...")
    try:
        # Check if template files were created
        templates_dir = Path("data/training_templates")
        if templates_dir.exists():
            template_files = list(templates_dir.glob("*.json"))
            if len(template_files) >= 4:
                print(f"   ✅ Created {len(template_files)} template files")
                
                # Check file content
                sample_file = template_files[0]
                with open(sample_file, 'r') as f:
                    template_data = json.load(f)
                    
                if 'template_id' in template_data and 'estimated_total_cost' in template_data:
                    print("   ✅ Template files contain required data")
                    validation_results.append(("File Persistence", True))
                else:
                    print("   ❌ Template files missing required data")
                    validation_results.append(("File Persistence", False))
            else:
                print(f"   ❌ Expected 4+ template files, found {len(template_files)}")
                validation_results.append(("File Persistence", False))
        else:
            print("   ❌ Template directory not created")
            validation_results.append(("File Persistence", False))
            
    except Exception as e:
        print(f"   ❌ File persistence validation failed: {e}")
        validation_results.append(("File Persistence", False))
    
    # Test 8: Regional configuration
    print("\n8. Testing regional configuration...")
    try:
        # Accept both af-south-1 and AF-Johannesburg as valid (they're the same region)
        valid_regions = ["af-south-1", "AF-Johannesburg"]
        if training_configurator.region in valid_regions:
            print(f"   ✅ Correctly configured for South Africa region: {training_configurator.region}")
            
            if training_configurator.bucket_name == "saferoute-ai-data":
                print("   ✅ OBS bucket name correctly configured")
                validation_results.append(("Regional Config", True))
            else:
                print("   ❌ OBS bucket name incorrect")
                validation_results.append(("Regional Config", False))
        else:
            print(f"   ❌ Incorrect region: {training_configurator.region}")
            validation_results.append(("Regional Config", False))
            
    except Exception as e:
        print(f"   ❌ Regional configuration validation failed: {e}")
        validation_results.append(("Regional Config", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in validation_results if result)
    total = len(validation_results)
    
    print(f"Tests Passed: {passed}/{total}")
    print()
    
    for test_name, result in validation_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print("\n" + "=" * 60)
    
    if passed == total:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ Task 7.1 Successfully Implemented")
        print("🚀 ModelArts training job configuration is ready")
        print("\nKey Features Implemented:")
        print("• Cost-optimized training templates")
        print("• Budget-based template selection")
        print("• Real SA crime data integration")
        print("• OBS storage configuration")
        print("• Cost controls and monitoring")
        print("• Regional compliance (af-south-1)")
        return True
    else:
        print(f"❌ {total - passed} validations failed")
        print("🔧 Review implementation and fix issues")
        return False

if __name__ == "__main__":
    success = validate_implementation()
    sys.exit(0 if success else 1)