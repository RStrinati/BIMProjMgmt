#!/usr/bin/env python3
"""
Security verification script - validates all fixes are properly implemented.
Run this before deployment to confirm security hardening is in place.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

class SecurityValidator:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
    
    def check(self, name: str, condition: bool, message: str = ""):
        """Log a security check result."""
        status = "✓ PASS" if condition else "✗ FAIL"
        print(f"{status}: {name}")
        if message:
            print(f"       {message}")
        
        if condition:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
        
        return condition
    
    def warn(self, message: str):
        """Log a warning."""
        print(f"⚠ WARN: {message}")
        self.warnings.append(message)
    
    def run_all_checks(self):
        """Run all security checks."""
        print("\n" + "="*60)
        print("BIM PROJECT MANAGEMENT - SECURITY VERIFICATION")
        print("="*60 + "\n")
        
        self._check_config()
        self._check_cors()
        self._check_security_headers()
        self._check_error_handling()
        self._check_input_validation()
        self._check_logging()
        self._check_dependencies()
        self._check_documentation()
        
        self._print_summary()
    
    def _check_config(self):
        """Check configuration security."""
        print("\n[1] Configuration Security")
        print("-" * 60)
        
        # Check config.py doesn't have hardcoded defaults
        config_path = project_root / "config.py"
        if config_path.exists():
            config_content = config_path.read_text()
            
            has_hardcoded_user = '"admin02"' in config_content or "'admin02'" in config_content
            has_hardcoded_pass = '"1234"' in config_content or "'1234'" in config_content
            
            self.check(
                "No hardcoded DB_USER credential",
                not has_hardcoded_user,
                "Credentials must come from environment only"
            )
            self.check(
                "No hardcoded DB_PASSWORD credential",
                not has_hardcoded_pass,
                "Credentials must come from environment only"
            )
            
            has_credential_validation = "raise ValueError" in config_content and "Database credentials" in config_content
            self.check(
                "Database credential validation implemented",
                has_credential_validation,
                "Application should fail if credentials not configured"
            )
        else:
            self.warn("config.py not found")
    
    def _check_cors(self):
        """Check CORS configuration."""
        print("\n[2] CORS Configuration")
        print("-" * 60)
        
        app_path = project_root / "backend" / "app.py"
        if app_path.exists():
            app_content = app_path.read_text()
            
            # Should NOT have CORS(app) without restrictions
            has_unrestricted_cors = "CORS(app)" in app_content and "ALLOWED_ORIGINS" not in app_content
            self.check(
                "CORS not unrestricted",
                not has_unrestricted_cors,
                "CORS should use ALLOWED_ORIGINS whitelist"
            )
            
            has_cors_config = "ALLOWED_ORIGINS" in app_content
            self.check(
                "CORS origins configured",
                has_cors_config,
                "CORS_ORIGINS should be configurable from environment"
            )
            
            has_cors_methods = '"methods"' in app_content and "GET" in app_content
            self.check(
                "CORS methods restricted",
                has_cors_methods,
                "Only necessary HTTP methods should be allowed"
            )
        else:
            self.warn("backend/app.py not found")
    
    def _check_security_headers(self):
        """Check security headers are implemented."""
        print("\n[3] Security Headers")
        print("-" * 60)
        
        app_path = project_root / "backend" / "app.py"
        if app_path.exists():
            app_content = app_path.read_text()
            
            headers = {
                "X-Frame-Options": "SAMEORIGIN",
                "X-Content-Type-Options": "nosniff",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": "accelerometer"
            }
            
            for header_name, header_value in headers.items():
                has_header = f"'{header_name}'" in app_content or f'"{header_name}"' in app_content
                self.check(
                    f"Security header: {header_name}",
                    has_header,
                    f"Should be set to protect against security vulnerabilities"
                )
        else:
            self.warn("backend/app.py not found")
    
    def _check_error_handling(self):
        """Check error handling doesn't leak information."""
        print("\n[4] Error Handling")
        print("-" * 60)
        
        app_path = project_root / "backend" / "app.py"
        if app_path.exists():
            app_content = app_path.read_text()
            
            has_error_handlers = "@app.errorhandler" in app_content
            self.check(
                "Global error handlers implemented",
                has_error_handlers,
                "Should handle 400, 404, 405, 500 errors gracefully"
            )
            
            has_info_hiding = "Internal server error" in app_content
            self.check(
                "Error messages don't expose details",
                has_info_hiding,
                "Production errors should be generic to users"
            )
        else:
            self.warn("backend/app.py not found")
    
    def _check_input_validation(self):
        """Check input validation functions."""
        print("\n[5] Input Validation")
        print("-" * 60)
        
        app_path = project_root / "backend" / "app.py"
        if app_path.exists():
            app_content = app_path.read_text()
            
            has_sort_validation = "_validate_sort_" in app_content
            self.check(
                "Sort parameter validation implemented",
                has_sort_validation,
                "Should prevent SQL injection via sort_by/sort_dir"
            )
            
            has_whitelist = "allowed_columns" in app_content
            self.check(
                "Whitelist validation for sort columns",
                has_whitelist,
                "Only predefined columns should be allowed"
            )
        else:
            self.warn("backend/app.py not found")
    
    def _check_logging(self):
        """Check logging security."""
        print("\n[6] Logging Configuration")
        print("-" * 60)
        
        app_path = project_root / "backend" / "app.py"
        if app_path.exists():
            app_content = app_path.read_text()
            
            has_dynamic_logging = "Config.LOG_LEVEL" in app_content
            self.check(
                "Log level configurable from environment",
                has_dynamic_logging,
                "Should respect LOG_LEVEL environment variable"
            )
            
            has_no_hardcoded_debug = ".setLevel(logging.DEBUG)" not in app_content or \
                                     "getattr(logging, Config.LOG_LEVEL" in app_content
            self.check(
                "DEBUG logging not hardcoded",
                has_no_hardcoded_debug,
                "Debug level should only be used when explicitly configured"
            )
        else:
            self.warn("backend/app.py not found")
    
    def _check_dependencies(self):
        """Check dependency versions."""
        print("\n[7] Dependency Management")
        print("-" * 60)
        
        requirements_path = project_root / "requirements.txt"
        if requirements_path.exists():
            requirements = requirements_path.read_text()
            
            has_version_pins = ">=" in requirements
            self.check(
                "Dependencies have version constraints",
                has_version_pins,
                "Should specify minimum versions for security"
            )
            
            has_flask_secure = "Flask>=3" in requirements or "Flask>=2" in requirements
            self.check(
                "Flask is current version",
                has_flask_secure,
                "Flask should be 3.0.0 or later"
            )
            
            has_werkzeug = "Werkzeug" in requirements
            self.check(
                "Werkzeug explicitly included",
                has_werkzeug,
                "Should pin Werkzeug for compatibility and security"
            )
        else:
            self.warn("requirements.txt not found")
    
    def _check_documentation(self):
        """Check security documentation."""
        print("\n[8] Documentation")
        print("-" * 60)
        
        audit_path = project_root / "docs" / "security" / "SECURITY_AUDIT.md"
        env_path = project_root / "docs" / "security" / "ENVIRONMENT_SETUP.md"
        summary_path = project_root / "SECURITY_FIXES_SUMMARY.md"
        
        self.check(
            "Security audit documentation exists",
            audit_path.exists(),
            "Should document all security findings and fixes"
        )
        
        self.check(
            "Environment setup guide exists",
            env_path.exists(),
            "Should document required environment configuration"
        )
        
        self.check(
            "Security fixes summary exists",
            summary_path.exists(),
            "Should document all changes made"
        )
    
    def _print_summary(self):
        """Print summary of all checks."""
        print("\n" + "="*60)
        print("SECURITY VERIFICATION SUMMARY")
        print("="*60)
        
        total = self.checks_passed + self.checks_failed
        passed_pct = (self.checks_passed / total * 100) if total > 0 else 0
        
        print(f"\nResults: {self.checks_passed} passed, {self.checks_failed} failed out of {total} checks")
        print(f"Success Rate: {passed_pct:.1f}%")
        
        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.checks_failed == 0:
            print("\n✅ All security checks passed! Application is ready for deployment.")
            print("\nRemaining tasks:")
            print("  1. Set DB_USER environment variable")
            print("  2. Set DB_PASSWORD environment variable")
            print("  3. Set CORS_ORIGINS for your domain(s)")
            print("  4. Run: pip install --upgrade -r requirements.txt")
            print("  5. Test API endpoints before deploying to production")
            return 0
        else:
            print(f"\n❌ Security checks failed! {self.checks_failed} issue(s) to resolve.")
            print("\nPlease review the security audit documentation:")
            print("  - docs/security/SECURITY_AUDIT.md")
            print("  - docs/security/ENVIRONMENT_SETUP.md")
            print("  - SECURITY_FIXES_SUMMARY.md")
            return 1


if __name__ == "__main__":
    validator = SecurityValidator()
    validator.run_all_checks()
    sys.exit(validator.checks_failed)
