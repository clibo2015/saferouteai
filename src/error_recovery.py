"""
Error Recovery and Retry Logic for Huawei Cloud Resource Provisioning
Implements error handling, retry logic, circuit breaker, and rollback capabilities
"""
import time
import json
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors that can occur during provisioning"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE_CREATION = "resource_creation"
    NETWORK = "network"
    DATA_UPLOAD = "data_upload"
    COST_BUDGET = "cost_budget"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """Actions to take when recovering from errors"""
    RETRY = "retry"
    PROMPT_USER = "prompt_user"
    SKIP = "skip"
    ROLLBACK = "rollback"
    HALT = "halt"
    LOG_AND_CONTINUE = "log_and_continue"


@dataclass
class ErrorContext:
    """Context information about an error"""
    error_type: str
    error_message: str
    error_category: ErrorCategory
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryStrategy:
    """Strategy for recovering from an error"""
    action: RecoveryAction
    message: str
    rollback_required: bool
    retry_allowed: bool = False
    max_retries: int = 3
    user_prompt: Optional[str] = None
    recovery_steps: List[str] = field(default_factory=list)


class HuaweiCloudError(Exception):
    """Base exception for Huawei Cloud errors"""
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN):
        super().__init__(message)
        self.category = category


class AuthenticationError(HuaweiCloudError):
    """Authentication failed"""
    def __init__(self, message: str):
        super().__init__(message, ErrorCategory.AUTHENTICATION)


class AuthorizationError(HuaweiCloudError):
    """Authorization/permission denied"""
    def __init__(self, message: str):
        super().__init__(message, ErrorCategory.AUTHORIZATION)


class ResourceCreationError(HuaweiCloudError):
    """Resource creation failed"""
    def __init__(self, message: str, resource_type: str = None):
        super().__init__(message, ErrorCategory.RESOURCE_CREATION)
        self.resource_type = resource_type


class QuotaExceededError(HuaweiCloudError):
    """Resource quota exceeded"""
    def __init__(self, message: str, current_usage: int = None, quota_limit: int = None):
        super().__init__(message, ErrorCategory.RESOURCE_CREATION)
        self.current_usage = current_usage
        self.quota_limit = quota_limit


class NetworkError(HuaweiCloudError):
    """Network connectivity error"""
    def __init__(self, message: str):
        super().__init__(message, ErrorCategory.NETWORK)


class DataUploadError(HuaweiCloudError):
    """Data upload failed"""
    def __init__(self, message: str, file_path: str = None):
        super().__init__(message, ErrorCategory.DATA_UPLOAD)
        self.file_path = file_path


class BudgetExceededError(HuaweiCloudError):
    """Budget limit exceeded"""
    def __init__(self, message: str, current_spend: float = None, budget_limit: float = None):
        super().__init__(message, ErrorCategory.COST_BUDGET)
        self.current_spend = current_spend
        self.budget_limit = budget_limit


class ValidationError(HuaweiCloudError):
    """Resource validation failed"""
    def __init__(self, message: str, resource_id: str = None):
        super().__init__(message, ErrorCategory.VALIDATION)
        self.resource_id = resource_id


class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open, preventing API calls"""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for API call protection
    Prevents cascading failures by stopping requests when error rate is high
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, name: str = "default"):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            name: Name of this circuit breaker for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open
        
        logger.info(f"CircuitBreaker '{name}' initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
        
        Returns:
            Result of function execution
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception raised by the function
        """
        # Check circuit state
        if self.state == "open":
            if self._should_attempt_reset():
                logger.info(f"CircuitBreaker '{self.name}': Attempting recovery (half-open)")
                self.state = "half_open"
            else:
                time_remaining = self.recovery_timeout - (time.time() - self.last_failure_time)
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Retry in {time_remaining:.0f} seconds."
                )
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        if self.state == "half_open":
            logger.info(f"CircuitBreaker '{self.name}': Recovery successful, closing circuit")
        
        self.failure_count = 0
        self.success_count += 1
        self.state = "closed"
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            logger.warning(
                f"CircuitBreaker '{self.name}': Failure threshold reached "
                f"({self.failure_count}/{self.failure_threshold}), opening circuit"
            )
            self.state = "open"
        else:
            logger.debug(
                f"CircuitBreaker '{self.name}': Failure {self.failure_count}/{self.failure_threshold}"
            )
    
    def reset(self):
        """Manually reset the circuit breaker"""
        logger.info(f"CircuitBreaker '{self.name}': Manual reset")
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "closed"
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'name': self.name,
            'state': self.state,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'failure_threshold': self.failure_threshold,
            'recovery_timeout': self.recovery_timeout,
            'last_failure_time': self.last_failure_time
        }


class ErrorRecoveryManager:
    """
    Manages error recovery, retry logic, and rollback operations
    Implements exponential backoff and state persistence
    """
    
    def __init__(self, state_file: str = "error_recovery_state.json"):
        """
        Initialize error recovery manager
        
        Args:
            state_file: Path to file for persisting error recovery state
        """
        self.state_file = state_file
        self.max_retries = 3
        self.retry_delays = [2, 4, 8]  # Exponential backoff in seconds
        self.error_history: List[ErrorContext] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Create default circuit breakers for different API types
        self._initialize_circuit_breakers()
        
        logger.info("ErrorRecoveryManager initialized")
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for different API types"""
        self.circuit_breakers = {
            'obs': CircuitBreaker(failure_threshold=5, recovery_timeout=60, name='OBS'),
            'modelarts': CircuitBreaker(failure_threshold=5, recovery_timeout=60, name='ModelArts'),
            'vpc': CircuitBreaker(failure_threshold=5, recovery_timeout=60, name='VPC'),
            'iam': CircuitBreaker(failure_threshold=5, recovery_timeout=60, name='IAM'),
            'bss': CircuitBreaker(failure_threshold=5, recovery_timeout=60, name='BSS'),
            'default': CircuitBreaker(failure_threshold=5, recovery_timeout=60, name='Default')
        }
    
    def get_circuit_breaker(self, service: str) -> CircuitBreaker:
        """
        Get circuit breaker for a specific service
        
        Args:
            service: Service name (obs, modelarts, vpc, iam, bss)
        
        Returns:
            CircuitBreaker instance for the service
        """
        return self.circuit_breakers.get(service.lower(), self.circuit_breakers['default'])
    
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """
        Categorize an error based on its type and message
        
        Args:
            error: Exception to categorize
        
        Returns:
            ErrorCategory enum value
        """
        if isinstance(error, HuaweiCloudError):
            return error.category
        
        error_msg = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Authentication errors
        if any(keyword in error_msg for keyword in ['authentication', 'invalid credentials', 'ak/sk', 'unauthorized']):
            return ErrorCategory.AUTHENTICATION
        
        # Authorization errors
        if any(keyword in error_msg for keyword in ['permission denied', 'forbidden', 'access denied', 'insufficient permissions']):
            return ErrorCategory.AUTHORIZATION
        
        # Network errors
        if any(keyword in error_msg for keyword in ['timeout', 'connection', 'network', 'unreachable', 'dns']):
            return ErrorCategory.NETWORK
        
        # Resource creation errors
        if any(keyword in error_msg for keyword in ['quota', 'limit exceeded', 'already exists', 'invalid configuration']):
            return ErrorCategory.RESOURCE_CREATION
        
        # Data upload errors
        if any(keyword in error_msg for keyword in ['upload', 'checksum', 'file not found', 'storage']):
            return ErrorCategory.DATA_UPLOAD
        
        # Budget errors
        if any(keyword in error_msg for keyword in ['budget', 'cost', 'billing', 'payment']):
            return ErrorCategory.COST_BUDGET
        
        # Validation errors
        if any(keyword in error_msg for keyword in ['validation', 'not found', 'invalid state']):
            return ErrorCategory.VALIDATION
        
        return ErrorCategory.UNKNOWN
    
    def create_error_context(self, error: Exception, resource_type: str = None, 
                           resource_id: str = None, metadata: Dict[str, Any] = None) -> ErrorContext:
        """
        Create error context from an exception
        
        Args:
            error: Exception that occurred
            resource_type: Type of resource being provisioned
            resource_id: ID of resource being provisioned
            metadata: Additional metadata about the error
        
        Returns:
            ErrorContext object
        """
        import traceback
        
        category = self.categorize_error(error)
        
        context = ErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            error_category=category,
            resource_type=resource_type,
            resource_id=resource_id,
            stack_trace=traceback.format_exc(),
            metadata=metadata or {}
        )
        
        self.error_history.append(context)
        return context
    
    def get_recovery_strategy(self, error_context: ErrorContext) -> RecoveryStrategy:
        """
        Determine recovery strategy based on error context
        
        Args:
            error_context: Context information about the error
        
        Returns:
            RecoveryStrategy object
        """
        category = error_context.error_category
        
        # Authentication errors
        if category == ErrorCategory.AUTHENTICATION:
            return RecoveryStrategy(
                action=RecoveryAction.PROMPT_USER,
                message="Authentication failed. Please verify your AK/SK credentials.",
                rollback_required=False,
                retry_allowed=False,
                user_prompt="Please check your HUAWEI_CLOUD_AK and HUAWEI_CLOUD_SK environment variables.",
                recovery_steps=[
                    "Verify AK/SK credentials in .env file",
                    "Check if credentials have expired",
                    "Ensure credentials have correct permissions",
                    "Test credentials with a simple API call"
                ]
            )
        
        # Authorization errors
        elif category == ErrorCategory.AUTHORIZATION:
            return RecoveryStrategy(
                action=RecoveryAction.PROMPT_USER,
                message="Authorization failed. Insufficient permissions for this operation.",
                rollback_required=False,
                retry_allowed=False,
                user_prompt="Please verify IAM permissions for your account.",
                recovery_steps=[
                    "Check IAM policies attached to your account",
                    "Verify region access permissions (af-south-1)",
                    "Ensure service-specific permissions are granted",
                    "Contact administrator to grant required permissions"
                ]
            )
        
        # Network errors - retry with backoff
        elif category == ErrorCategory.NETWORK:
            return RecoveryStrategy(
                action=RecoveryAction.RETRY,
                message="Network error occurred. Retrying with exponential backoff...",
                rollback_required=False,
                retry_allowed=True,
                max_retries=self.max_retries,
                recovery_steps=[
                    "Check internet connectivity",
                    "Verify Huawei Cloud API endpoints are accessible",
                    "Check firewall and proxy settings",
                    "Retry the operation"
                ]
            )
        
        # Resource creation errors
        elif category == ErrorCategory.RESOURCE_CREATION:
            error_msg = error_context.error_message.lower()
            
            # Resource already exists - skip
            if 'already exists' in error_msg:
                return RecoveryStrategy(
                    action=RecoveryAction.SKIP,
                    message=f"Resource already exists. Skipping creation.",
                    rollback_required=False,
                    retry_allowed=False,
                    recovery_steps=[
                        "Verify existing resource configuration",
                        "Reuse existing resource if configuration matches",
                        "Delete and recreate if configuration differs"
                    ]
                )
            
            # Quota exceeded
            elif 'quota' in error_msg or 'limit exceeded' in error_msg:
                return RecoveryStrategy(
                    action=RecoveryAction.HALT,
                    message="Resource quota exceeded. Cannot proceed with provisioning.",
                    rollback_required=True,
                    retry_allowed=False,
                    user_prompt="Please increase quota or clean up existing resources.",
                    recovery_steps=[
                        "Check current resource usage in console",
                        "Request quota increase from Huawei Cloud",
                        "Delete unused resources to free up quota",
                        "Use smaller instance types or fewer resources"
                    ]
                )
            
            # Invalid configuration
            else:
                return RecoveryStrategy(
                    action=RecoveryAction.HALT,
                    message="Resource creation failed due to invalid configuration.",
                    rollback_required=True,
                    retry_allowed=False,
                    recovery_steps=[
                        "Verify resource configuration parameters",
                        "Check region-specific limitations",
                        "Review error message for specific issues",
                        "Correct configuration and retry"
                    ]
                )
        
        # Data upload errors - retry
        elif category == ErrorCategory.DATA_UPLOAD:
            return RecoveryStrategy(
                action=RecoveryAction.RETRY,
                message="Data upload failed. Retrying with multipart upload...",
                rollback_required=False,
                retry_allowed=True,
                max_retries=self.max_retries,
                recovery_steps=[
                    "Verify file exists and is readable",
                    "Check available storage quota",
                    "Use multipart upload for large files",
                    "Verify checksum after upload"
                ]
            )
        
        # Budget exceeded - halt immediately
        elif category == ErrorCategory.COST_BUDGET:
            return RecoveryStrategy(
                action=RecoveryAction.HALT,
                message="Budget limit exceeded. Halting provisioning to prevent cost overruns.",
                rollback_required=True,
                retry_allowed=False,
                user_prompt="Budget limit reached. Please review costs and adjust budget if needed.",
                recovery_steps=[
                    "Review current spending in billing console",
                    "Identify high-cost resources",
                    "Delete unnecessary resources",
                    "Increase budget limit if appropriate",
                    "Optimize resource configurations for cost"
                ]
            )
        
        # Validation errors - log and continue
        elif category == ErrorCategory.VALIDATION:
            return RecoveryStrategy(
                action=RecoveryAction.LOG_AND_CONTINUE,
                message="Validation failed. Logging error and continuing...",
                rollback_required=False,
                retry_allowed=True,
                max_retries=2,
                recovery_steps=[
                    "Check if resource was actually created",
                    "Verify resource appears in console",
                    "Retry validation after a delay",
                    "Manually verify resource if needed"
                ]
            )
        
        # Unknown errors - log and halt
        else:
            return RecoveryStrategy(
                action=RecoveryAction.HALT,
                message=f"Unexpected error occurred: {error_context.error_message}",
                rollback_required=True,
                retry_allowed=False,
                recovery_steps=[
                    "Review error message and stack trace",
                    "Check Huawei Cloud service status",
                    "Verify all prerequisites are met",
                    "Contact support if issue persists"
                ]
            )
    
    def retry_with_backoff(self, func: Callable, *args, max_retries: int = None, 
                          service: str = 'default', **kwargs) -> Any:
        """
        Execute function with retry logic and exponential backoff
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            max_retries: Maximum number of retries (default: self.max_retries)
            service: Service name for circuit breaker
            **kwargs: Keyword arguments for function
        
        Returns:
            Result of function execution
        
        Raises:
            Exception: Last exception if all retries fail
        """
        if max_retries is None:
            max_retries = self.max_retries
        
        circuit_breaker = self.get_circuit_breaker(service)
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                # Use circuit breaker for API call protection
                result = circuit_breaker.call(func, *args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"✅ Retry successful after {attempt} attempt(s)")
                
                return result
                
            except CircuitBreakerOpenError as e:
                logger.error(f"Circuit breaker open: {e}")
                raise
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.warning(
                        f"⚠️  Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"❌ All {max_retries + 1} attempts failed")
        
        # All retries exhausted
        raise last_exception
    
    def save_error_state(self, additional_data: Dict[str, Any] = None):
        """
        Save error recovery state to file
        
        Args:
            additional_data: Additional data to save with error state
        """
        try:
            state = {
                'error_history': [
                    {
                        'error_type': e.error_type,
                        'error_message': e.error_message,
                        'error_category': e.error_category.value,
                        'resource_type': e.resource_type,
                        'resource_id': e.resource_id,
                        'timestamp': e.timestamp,
                        'metadata': e.metadata
                    }
                    for e in self.error_history
                ],
                'circuit_breakers': {
                    name: cb.get_state()
                    for name, cb in self.circuit_breakers.items()
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if additional_data:
                state['additional_data'] = additional_data
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.debug(f"💾 Error recovery state saved to {self.state_file}")
            
        except Exception as e:
            logger.error(f"Failed to save error recovery state: {e}")
    
    def load_error_state(self) -> Dict[str, Any]:
        """
        Load error recovery state from file
        
        Returns:
            Dictionary with error state, or empty dict if file doesn't exist
        """
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load error recovery state: {e}")
            return {}
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of error history
        
        Returns:
            Dictionary with error statistics
        """
        if not self.error_history:
            return {
                'total_errors': 0,
                'errors_by_category': {},
                'errors_by_resource_type': {},
                'recent_errors': []
            }
        
        # Count by category
        errors_by_category = {}
        for error in self.error_history:
            category = error.error_category.value
            errors_by_category[category] = errors_by_category.get(category, 0) + 1
        
        # Count by resource type
        errors_by_resource_type = {}
        for error in self.error_history:
            if error.resource_type:
                errors_by_resource_type[error.resource_type] = \
                    errors_by_resource_type.get(error.resource_type, 0) + 1
        
        # Get recent errors (last 10)
        recent_errors = [
            {
                'error_type': e.error_type,
                'error_message': e.error_message,
                'category': e.error_category.value,
                'resource_type': e.resource_type,
                'timestamp': e.timestamp
            }
            for e in self.error_history[-10:]
        ]
        
        return {
            'total_errors': len(self.error_history),
            'errors_by_category': errors_by_category,
            'errors_by_resource_type': errors_by_resource_type,
            'recent_errors': recent_errors
        }


# Import os for file operations
import os


if __name__ == "__main__":
    # Test error recovery manager
    print("\n" + "="*60)
    print("Error Recovery Manager Test")
    print("="*60)
    
    manager = ErrorRecoveryManager()
    
    # Test error categorization
    print("\n🔍 Testing Error Categorization:")
    test_errors = [
        (AuthenticationError("Invalid AK/SK"), "Authentication"),
        (NetworkError("Connection timeout"), "Network"),
        (QuotaExceededError("Quota exceeded", 10, 5), "Resource Creation"),
        (BudgetExceededError("Budget exceeded", 150.0, 100.0), "Cost/Budget"),
    ]
    
    for error, expected_category in test_errors:
        context = manager.create_error_context(error)
        print(f"  {error.__class__.__name__}: {context.error_category.value}")
    
    # Test recovery strategies
    print("\n🔧 Testing Recovery Strategies:")
    for error, _ in test_errors:
        context = manager.create_error_context(error)
        strategy = manager.get_recovery_strategy(context)
        print(f"\n  {error.__class__.__name__}:")
        print(f"    Action: {strategy.action.value}")
        print(f"    Message: {strategy.message}")
        print(f"    Rollback Required: {strategy.rollback_required}")
    
    # Test circuit breaker
    print("\n⚡ Testing Circuit Breaker:")
    cb = manager.get_circuit_breaker('obs')
    print(f"  Initial state: {cb.state}")
    
    # Simulate failures
    for i in range(6):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
        except Exception:
            pass
    
    print(f"  After {cb.failure_count} failures: {cb.state}")
    
    # Test retry with backoff
    print("\n🔄 Testing Retry with Backoff:")
    attempt_count = [0]
    
    def flaky_function():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise NetworkError("Temporary network error")
        return "Success!"
    
    try:
        # Reset circuit breaker first
        manager.get_circuit_breaker('default').reset()
        result = manager.retry_with_backoff(flaky_function, max_retries=3)
        print(f"  Result after {attempt_count[0]} attempts: {result}")
    except Exception as e:
        print(f"  Failed: {e}")
    
    # Print error summary
    print("\n📊 Error Summary:")
    summary = manager.get_error_summary()
    print(f"  Total Errors: {summary['total_errors']}")
    print(f"  Errors by Category: {summary['errors_by_category']}")
    
    print("\n" + "="*60)
