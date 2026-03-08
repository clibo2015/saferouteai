#!/usr/bin/env python3
"""
Test Suite for ModelArts Training Configuration
Validates task 7.1 implementation: Set up ModelArts training job configuration
"""

import unittest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

class TestModelArtsTrainingConfig(unittest.TestCase):
    """Test ModelArts training job configuration"""
    
    def setUp(self):
        """Set up test environment"""
        # Ensure test data directory exists
        Path("data").mkdir(exist_ok=True)
        
        # Add src to path for imports
        import sys
        sys.path.append('src')
        
        # Import modules
        from modelarts_training_config import training_configurator
        self.configurator = training_configurator
    
    def test_cost_optimized_templates_creation(self):
        """Test creation of cost-optimized training templates"""
        templates = self.configurator.create_cost_optimized_templates()
        
        # Verify templates were created
        self.assertGreater(len(templates), 0, "Should create at least one template")
        self.assertEqual(len(templates), 4, "Should create exactly 4 templates")
        
        # Verify ultra-budget template (most important for $100 budget)
        ultra_budget = templates[0]
        self.assertEqual(ultra_budget.template_id, "saferoute-ultra-budget-cpu")
        self.assertLessEqual(ultra_budget.estimated_total_cost, 1.0, "Ultra-budget should cost ≤ $1")
        self.assertEqual(ultra_budget.max_training_hours, 1, "Should limit to 1 hour")
        self.assertTrue(ultra_budget.auto_stop_enabled, "Auto-stop should be enabled")
        
        # Verify all templates have required fields
        for template in templates:
            self.assertIsNotNone(template.template_id)
            self.assertIsNotNone(template.name)
            self.assertIsNotNone(template.instance_type)
            self.assertGreater(template.estimated_cost_per_hour, 0)
            self.assertGreater(template.estimated_total_cost, 0)
            self.assertTrue(template.auto_stop_enabled)
    
    def test_template_selection_by_budget(self):
        """Test optimal template selection based on budget"""
        # Test with very low budget
        low_budget_template = self.configurator.select_optimal_template(
            available_budget=0.75, 
            performance_priority="cost"
        )
        self.assertEqual(low_budget_template.template_id, "saferoute-ultra-budget-cpu")
        
        # Test with moderate budget
        moderate_budget_template = self.configurator.select_optimal_template(
            available_budget=5.0, 
            performance_priority="cost"
        )
        self.assertLessEqual(moderate_budget_template.estimated_total_cost, 5.0)
        
        # Test with higher budget
        high_budget_template = self.configurator.select_optimal_template(
            available_budget=10.0, 
            performance_priority="performance"
        )
        self.assertLessEqual(high_budget_template.estimated_total_cost, 10.0)
    
    def test_training_job_config_creation(self):
        """Test creation of complete training job configuration"""
        # Get a template
        templates = self.configurator.create_cost_optimized_templates()
        template = templates[0]  # Ultra-budget template
        
        # Create configuration
        config = self.configurator.create_training_job_config(
            template=template,
            crime_data_path="obs://test-bucket/crime-data/processed/"
        )
        
        # Verify configuration structure
        self.assertIsNotNone(config.job_name)
        self.assertTrue(config.job_name.startswith("saferoute-training-"))
        self.assertEqual(config.template, template)
        
        # Verify data configuration
        self.assertIn("training_data_path", config.data_config)
        self.assertIn("feature_columns", config.data_config)
        self.assertGreater(len(config.data_config["feature_columns"]), 5)
        
        # Verify resource configuration
        self.assertEqual(config.resource_config["instance_type"], template.instance_type)
        self.assertEqual(config.resource_config["max_runtime_hours"], template.max_training_hours)
        self.assertTrue(config.resource_config["auto_stop_enabled"])
        self.assertTrue(config.resource_config["spot_instance_enabled"])
        
        # Verify cost controls
        self.assertIn("max_cost_usd", config.cost_controls)
        self.assertIn("auto_stop_on_budget", config.cost_controls)
        self.assertTrue(config.cost_controls["auto_stop_on_budget"])
        
        # Verify monitoring configuration
        self.assertTrue(config.monitoring_config["metrics_collection"])
        self.assertTrue(config.monitoring_config["early_stopping_monitoring"])
    
    @patch('src.modelarts_training_config.RealDataIntegrator')
    def test_obs_training_data_setup(self, mock_integrator):
        """Test OBS training data setup"""
        # Mock the data integrator
        mock_instance = MagicMock()
        mock_integrator.return_value = mock_instance
        
        # Mock crime data
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
        mock_instance.download_saps_crime_data.return_value = mock_crime_data
        
        # Test data setup
        result = self.configurator.setup_obs_training_data()
        
        # Verify result structure
        self.assertIn("status", result)
        self.assertIn("data_size", result)
        self.assertIn("features", result)
        self.assertIn("obs_path", result)
        
        # Verify features are present
        self.assertGreater(result["data_size"], 0)
        self.assertGreater(len(result["features"]), 5)
    
    def test_training_data_preparation(self):
        """Test training data preparation and feature engineering"""
        # Create mock crime data
        import pandas as pd
        mock_crime_data = pd.DataFrame({
            'station': ['Johannesburg Central', 'Soweto'],
            'province': ['Gauteng', 'Gauteng'],
            'latitude': [-26.2041, -26.2678],
            'longitude': [28.0473, 27.8546],
            'year': [2024, 2024],
            'crime_category': ['Murder', 'Robbery with aggravating circumstances'],
            'incidents': [15, 25],
            'crime_rate_per_100k': [75.0, 125.0],
            'socio_economic_index': [0.7, 0.5],
            'unemployment_rate': [25.0, 35.0],
            'area_type': ['urban', 'township'],
            'crime_severity_score': [1.0, 0.75]
        })
        
        # Prepare training data
        training_data = self.configurator._prepare_training_data(mock_crime_data)
        
        # Verify training data structure
        self.assertEqual(len(training_data), 2)
        
        # Verify required columns
        required_columns = [
            'latitude', 'longitude', 'hour', 'day_of_week', 'month',
            'crime_category_encoded', 'incidents', 'crime_rate_per_100k',
            'socio_economic_index', 'unemployment_rate', 'risk_level'
        ]
        
        for column in required_columns:
            self.assertIn(column, training_data.columns, f"Missing column: {column}")
        
        # Verify risk level calculation
        risk_levels = training_data['risk_level'].values
        self.assertTrue(all(0 <= risk <= 1 for risk in risk_levels), "Risk levels should be between 0 and 1")
        
        # Verify encoding
        self.assertGreater(training_data['crime_category_encoded'].iloc[0], 0)
        self.assertGreater(training_data['province_encoded'].iloc[0], 0)
    
    def test_cost_controls_and_optimization(self):
        """Test cost control mechanisms"""
        templates = self.configurator.create_cost_optimized_templates()
        
        # Verify cost optimization features
        for template in templates:
            # All templates should have auto-stop enabled
            self.assertTrue(template.auto_stop_enabled, f"Template {template.name} should have auto-stop")
            
            # Training time should be limited
            self.assertLessEqual(template.max_training_hours, 3, "Training time should be limited")
            
            # Cost should be reasonable for $100 budget
            self.assertLessEqual(template.estimated_total_cost, 20.0, "Cost should be reasonable")
        
        # Ultra-budget template should be most cost-effective
        ultra_budget = templates[0]
        self.assertLessEqual(ultra_budget.estimated_total_cost, 1.0, "Ultra-budget should be ≤ $1")
        self.assertEqual(ultra_budget.optimization_level, "ultra_aggressive")
    
    def test_training_status_summary(self):
        """Test training status summary generation"""
        summary = self.configurator.get_training_status_summary()
        
        # Verify summary structure
        required_keys = [
            'configuration_status', 'available_templates', 'recommended_template',
            'total_estimated_costs', 'budget_analysis', 'cost_optimization_features',
            'data_readiness', 'region', 'demo_mode'
        ]
        
        for key in required_keys:
            self.assertIn(key, summary, f"Missing key in summary: {key}")
        
        # Verify values
        self.assertEqual(summary['configuration_status'], 'ready')
        self.assertGreater(summary['available_templates'], 0)
        self.assertIsInstance(summary['cost_optimization_features'], list)
        self.assertGreater(len(summary['cost_optimization_features']), 3)
        
        # Verify budget analysis
        budget_analysis = summary['budget_analysis']
        self.assertIn('max_budget', budget_analysis)
        self.assertIn('affordable_templates', budget_analysis)
    
    def test_region_and_obs_path_configuration(self):
        """Test proper region and OBS path configuration"""
        # Verify region is set to af-south-1
        self.assertEqual(self.configurator.region, "af-south-1")
        
        # Verify OBS bucket name
        self.assertEqual(self.configurator.bucket_name, "saferoute-ai-data")
        
        # Test template OBS paths
        templates = self.configurator.create_cost_optimized_templates()
        for template in templates:
            self.assertTrue(template.data_source_path.startswith("obs://saferoute-ai-data/"))
            self.assertTrue(template.output_path.startswith("obs://saferoute-ai-data/models/"))
    
    def test_hyperparameter_optimization(self):
        """Test hyperparameter optimization for cost efficiency"""
        templates = self.configurator.create_cost_optimized_templates()
        
        # Ultra-budget template should have aggressive optimization
        ultra_budget = templates[0]
        hyperparams = ultra_budget.hyperparameters
        
        # Should have early stopping
        self.assertTrue(hyperparams.get('early_stopping', False))
        self.assertLessEqual(hyperparams.get('patience', 10), 3)
        
        # Should limit training data size
        self.assertLessEqual(hyperparams.get('max_samples', float('inf')), 50000)
        
        # Should have reasonable epochs
        self.assertLessEqual(hyperparams.get('epochs', 100), 10)
    
    def test_mock_training_job_submission(self):
        """Test mock training job submission in demo mode"""
        # Ensure demo mode
        self.configurator.demo_mode = True
        
        # Create a test configuration
        templates = self.configurator.create_cost_optimized_templates()
        template = templates[0]
        config = self.configurator.create_training_job_config(
            template=template,
            crime_data_path="obs://test-bucket/crime-data/"
        )
        
        # Submit job
        result = self.configurator.submit_training_job(config)
        
        # Verify mock submission
        self.assertEqual(result['status'], 'demo_submitted')
        self.assertIn('job_id', result)
        self.assertIn('demo_note', result)
        self.assertEqual(result['job_name'], config.job_name)
        self.assertEqual(result['estimated_cost'], template.estimated_total_cost)

class TestTrainingSetupIntegration(unittest.TestCase):
    """Integration tests for the complete training setup"""
    
    def test_setup_script_components(self):
        """Test that all components needed for setup are available"""
        # Test imports
        try:
            import sys
            sys.path.append('src')
            
            from modelarts_training_config import training_configurator
            from cost_optimizer import cost_optimizer
            from obs_manager import obs_manager
            from config import settings
        except ImportError as e:
            self.fail(f"Required module import failed: {e}")
        
        # Test that configurator is properly initialized
        self.assertIsNotNone(training_configurator)
        self.assertIsNotNone(cost_optimizer)
        self.assertIsNotNone(obs_manager)
    
    def test_configuration_file_creation(self):
        """Test that configuration files can be created and saved"""
        import sys
        sys.path.append('src')
        
        from modelarts_training_config import training_configurator
        
        # Create templates
        templates = training_configurator.create_cost_optimized_templates()
        
        # Verify template files are created
        templates_dir = Path("data/training_templates")
        self.assertTrue(templates_dir.exists())
        
        # Check that template files exist
        for template in templates:
            template_file = templates_dir / f"{template.template_id}.json"
            self.assertTrue(template_file.exists(), f"Template file should exist: {template_file}")
            
            # Verify file content
            with open(template_file, 'r') as f:
                template_data = json.load(f)
                self.assertEqual(template_data['template_id'], template.template_id)
                self.assertIn('estimated_total_cost', template_data)

def run_tests():
    """Run all tests"""
    print("🧪 Running ModelArts Training Configuration Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestModelArtsTrainingConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestTrainingSetupIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All tests passed! ModelArts training configuration is ready.")
        print(f"📊 Tests run: {result.testsRun}")
        print("🚀 Ready to set up ModelArts training jobs")
    else:
        print("❌ Some tests failed!")
        print(f"📊 Tests run: {result.testsRun}")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"💥 Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)