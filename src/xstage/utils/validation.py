"""
USD Validation Support
Uses UsdUtils.ComplianceChecker for USD validation
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List
from pxr import Usd, UsdUtils

try:
    from pxr import Usd, UsdUtils
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class USDValidator:
    """Validates USD stages using UsdUtils.ComplianceChecker"""
    
    def __init__(self):
        self.checker = None
        if USD_AVAILABLE:
            self.checker = UsdUtils.ComplianceChecker()
    
    def validate_stage(self, stage: Usd.Stage, 
                       check_topology: bool = True,
                       check_usd_gl: bool = True,
                       check_ar: bool = True) -> Dict:
        """
        Validate a USD stage
        
        Returns:
            Dict with 'passed', 'errors', 'warnings', 'info' keys
        """
        if not USD_AVAILABLE or not self.checker:
            return {
                'passed': False,
                'errors': ['USD not available'],
                'warnings': [],
                'info': [],
            }
        
        if not stage:
            return {
                'passed': False,
                'errors': ['Invalid stage'],
                'warnings': [],
                'info': [],
            }
        
        try:
            # Configure checker
            self.checker.CheckTopology = check_topology
            self.checker.CheckUSDGl = check_usd_gl
            self.checker.CheckAR = check_ar
            
            # Run validation
            root_prim = stage.GetPseudoRoot()
            self.checker.CheckCompliance(root_prim)
            
            # Get results
            errors = []
            warnings = []
            info = []
            
            for msg in self.checker.GetErrors():
                errors.append({
                    'message': str(msg),
                    'code': msg.code if hasattr(msg, 'code') else None,
                })
            
            for msg in self.checker.GetWarnings():
                warnings.append({
                    'message': str(msg),
                    'code': msg.code if hasattr(msg, 'code') else None,
                })
            
            for msg in self.checker.GetInfo():
                info.append({
                    'message': str(msg),
                    'code': msg.code if hasattr(msg, 'code') else None,
                })
            
            return {
                'passed': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'info': info,
            }
        except Exception as e:
            return {
                'passed': False,
                'errors': [f'Validation error: {str(e)}'],
                'warnings': [],
                'info': [],
            }
    
    def validate_file(self, filepath: str, **kwargs) -> Dict:
        """Validate a USD file"""
        if not USD_AVAILABLE:
            return {
                'passed': False,
                'errors': ['USD not available'],
                'warnings': [],
                'info': [],
            }
        
        try:
            stage = Usd.Stage.Open(filepath)
            if not stage:
                return {
                    'passed': False,
                    'errors': [f'Failed to open file: {filepath}'],
                    'warnings': [],
                    'info': [],
                }
            
            return self.validate_stage(stage, **kwargs)
        except Exception as e:
            return {
                'passed': False,
                'errors': [f'Error opening file: {str(e)}'],
                'warnings': [],
                'info': [],
            }

