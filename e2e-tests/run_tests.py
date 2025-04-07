#!/usr/bin/env python3
"""
MidPrint End-to-End Test Runner
Executes all test cases and generates a summary report.
"""
import os
import sys
import asyncio
import subprocess
import time
import importlib.util
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_PATH = PROJECT_ROOT / "backend"
FRONTEND_PATH = PROJECT_ROOT / "frontend"

# Ensure backend is in Python path
if str(BACKEND_PATH) not in sys.path:
    sys.path.append(str(BACKEND_PATH))

# Test modules to run (relative to e2e-tests directory)
TEST_MODULES = [
    "test_nav_01",
    "test_form_01", 
    "test_flow_01"
]

# Test categorization
TEST_CATEGORIES = {
    "Navigation": ["test_nav_01"],
    "Form Interaction": ["test_form_01"],
    "Multi-step Workflows": ["test_flow_01"]
}

class TestReport:
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.results = []
        
    def add_result(self, test_name, description, result, metrics=None):
        """Add a test result with metrics"""
        self.results.append({
            "test_name": test_name,
            "description": description,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics or {}
        })
        
    def print_summary(self):
        """Print a summary of test results"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["result"] == "PASSED")
        failed = total - passed
        
        print("\n=== TEST SUMMARY ===")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print("\nResults by Category:")
        
        for category, tests in TEST_CATEGORIES.items():
            category_results = [r for r in self.results if r["test_name"] in tests]
            if category_results:
                passed = sum(1 for r in category_results if r["result"] == "PASSED")
                total = len(category_results)
                print(f"\n{category}:")
                print(f"  Passed: {passed}/{total}")
                for result in category_results:
                    status = "✅" if result["result"] == "PASSED" else "❌"
                    print(f"  {status} {result['test_name']}")
                    if result["result"] == "FAILED" and result.get("metrics", {}).get("errors"):
                        for error in result["metrics"]["errors"]:
                            print(f"    - {error}")
        
        print("\nDetailed Metrics:")
        for result in self.results:
            print(f"\n{result['test_name']}:")
            metrics = result.get("metrics", {})
            if "workflow_completion_time" in metrics:
                print(f"  Total Time: {metrics['workflow_completion_time'] - metrics['start_time']:.2f}s")
            if "screenshot_count" in metrics:
                print(f"  Screenshots: {metrics['screenshot_count']}")
            if "action_feedback_received" in metrics:
                print(f"  Actions: {metrics['action_feedback_received']}")
        
        print("\n==================")
        
    def save_report(self):
        """Save the test report to a JSON file"""
        report_dir = "test_reports"
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_dir}/test_report_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump({
                "timestamp": self.timestamp,
                "results": self.results
            }, f, indent=2)
            
        print(f"\nTest report saved to: {filename}")

async def setup_environment():
    """Set up the test environment"""
    logger.info("Setting up test environment...")
    
    # Ensure backend dependencies are installed
    logger.info("Installing backend dependencies...")
    try:
        subprocess.run(
            ["pip", "install", "-r", "requirements.txt"],
            cwd=str(BACKEND_PATH),
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install backend dependencies: {e}")
        return False
        
    # Start backend server if not running
    logger.info("Starting backend server...")
    try:
        # Check if server is already running
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            logger.info("Backend server already running")
        else:
            raise Exception("Backend server not healthy")
    except Exception:
        # Start the server
        server_process = subprocess.Popen(
            ["python", "app/main.py"],
            cwd=str(BACKEND_PATH),
            env={**os.environ, "PYTHONPATH": f"{str(BACKEND_PATH)}:{os.environ.get('PYTHONPATH', '')}"}
        )
        # Wait for server to start
        for _ in range(30):  # 30 second timeout
            try:
                response = requests.get("http://localhost:8000/health")
                if response.status_code == 200:
                    logger.info("Backend server started successfully")
                    break
            except Exception:
                time.sleep(1)
        else:
            logger.error("Failed to start backend server")
            return False
            
    return True

async def run_test_module(module_name):
    """Execute a test module as a subprocess and capture its output and metrics"""
    logger.info(f"Running test module: {module_name}")
    
    try:
        # Run the test module with proper environment
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            f"{module_name}.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={
                **os.environ,
                "PYTHONPATH": f"{str(PROJECT_ROOT)}:{str(BACKEND_PATH)}:{os.environ.get('PYTHONPATH', '')}"
            }
        )
        
        stdout, stderr = await process.communicate()
        
        # Try to extract metrics from the output
        metrics = {}
        try:
            output = stdout.decode()
            if "TEST METRICS" in output:
                # Parse metrics section
                metrics_section = output[output.find("TEST METRICS"):output.find("-------------------")]
                for line in metrics_section.split("\n"):
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        if "Time" in key and "s" in value:
                            metrics[key.strip()] = float(value.replace("s", ""))
                        elif key.strip() in ["Screenshots Received", "Action Feedback Messages"]:
                            metrics[key.strip()] = int(value)
                        else:
                            metrics[key.strip()] = value.strip()
                            
                # Extract any errors
                if "Errors:" in output:
                    errors_section = output[output.find("Errors:"):output.find("-------------------")]
                    metrics["errors"] = [
                        line.strip("- ") for line in errors_section.split("\n")
                        if line.strip().startswith("-")
                    ]
        except Exception as e:
            logger.error(f"Failed to parse metrics from {module_name}: {e}")
        
        return process.returncode == 0, metrics
        
    except Exception as e:
        logger.error(f"Failed to run {module_name}: {e}")
        return False, {"errors": [str(e)]}

async def main():
    """Run all test modules and generate a summary report"""
    report = TestReport()
    
    print("Starting MidPrint end-to-end tests...")
    
    # Set up test environment
    if not await setup_environment():
        logger.error("Failed to set up test environment")
        return False
    
    for module_name in TEST_MODULES:
        success, metrics = await run_test_module(module_name)
        
        # Add result to report
        description = {
            "test_nav_01": "Simple URL navigation test",
            "test_form_01": "Form interaction test with username/password",
            "test_flow_01": "Multi-step search-click-extract workflow"
        }.get(module_name, "")
        
        report.add_result(
            module_name,
            description,
            "PASSED" if success else "FAILED",
            metrics
        )
    
    # Print and save the report
    report.print_summary()
    report.save_report()
    
    # Return success only if all tests passed
    return all(r["result"] == "PASSED" for r in report.results)

if __name__ == "__main__":
    # Set up logging
    import logging
    import requests  # For checking server health
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("run_tests")
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 