"""
test_policy.py

Comprehensive tests for NUPolicy policy management.
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.nupolicy import (
    Policy, PolicyConfig, PolicyLoader, PolicyManager,
    PolicyValidator, PolicyValidationError,
    PolicyExporter, ExportFormat
)


class TestPolicyConfig:
    """Tests for PolicyConfig"""

    def test_policy_config_creation(self):
        """Test basic policy config creation"""
        config = PolicyConfig(
            version="1.0.0",
            name="TestPolicy",
            description="Test policy",
            rules=[
                {"type": "CoverageRule", "threshold": 0.1}
            ]
        )

        assert config.version == "1.0.0"
        assert config.name == "TestPolicy"
        assert len(config.rules) == 1

    def test_policy_config_to_dict(self):
        """Test policy config serialization"""
        config = PolicyConfig(
            version="1.0.0",
            name="TestPolicy",
            description="Test",
            rules=[],
            escalation={"halt_on_critical": True}
        )

        d = config.to_dict()
        assert d['version'] == "1.0.0"
        assert d['name'] == "TestPolicy"
        assert d['escalation']['halt_on_critical'] is True

    def test_policy_config_from_dict(self):
        """Test policy config deserialization"""
        data = {
            'version': '2.0.0',
            'name': 'FromDict',
            'description': 'Test',
            'rules': [{'type': 'InvariantRule'}],
            'escalation': {},
            'metadata': {}
        }

        config = PolicyConfig.from_dict(data)
        assert config.version == '2.0.0'
        assert config.name == 'FromDict'


class TestPolicy:
    """Tests for Policy"""

    def test_policy_creation(self):
        """Test policy object creation"""
        config = PolicyConfig(
            version="1.0.0",
            name="Test",
            description="Test policy",
            rules=[]
        )

        policy = Policy(config=config)

        assert policy.config.name == "Test"
        assert policy.policy_hash is not None
        assert len(policy.policy_hash) == 64  # SHA-256 hex

    def test_policy_hash_computation(self):
        """Test policy hash is deterministic"""
        config1 = PolicyConfig(
            version="1.0.0",
            name="Test",
            description="Test",
            rules=[]
        )

        config2 = PolicyConfig(
            version="1.0.0",
            name="Test",
            description="Test",
            rules=[]
        )

        policy1 = Policy(config=config1)
        policy2 = Policy(config=config2)

        assert policy1.policy_hash == policy2.policy_hash

    def test_policy_hash_changes_with_content(self):
        """Test policy hash changes when content changes"""
        config1 = PolicyConfig(
            version="1.0.0",
            name="Test1",
            description="Test",
            rules=[]
        )

        config2 = PolicyConfig(
            version="1.0.0",
            name="Test2",  # Different name
            description="Test",
            rules=[]
        )

        policy1 = Policy(config=config1)
        policy2 = Policy(config=config2)

        assert policy1.policy_hash != policy2.policy_hash

    def test_policy_to_dict(self):
        """Test policy serialization"""
        config = PolicyConfig(
            version="1.0.0",
            name="Test",
            description="Test",
            rules=[]
        )

        policy = Policy(config=config, signature="test_sig", public_key="test_key")

        d = policy.to_dict()
        assert 'config' in d
        assert d['signature'] == "test_sig"
        assert d['public_key'] == "test_key"
        assert 'policy_hash' in d

    def test_policy_from_dict(self):
        """Test policy deserialization"""
        data = {
            'config': {
                'version': '1.0.0',
                'name': 'Test',
                'description': 'Test',
                'rules': [],
                'escalation': {},
                'metadata': {}
            },
            'signature': 'sig',
            'public_key': 'key',
            'policy_hash': 'hash123'
        }

        policy = Policy.from_dict(data)
        assert policy.signature == 'sig'
        assert policy.public_key == 'key'


class TestPolicyLoader:
    """Tests for PolicyLoader"""

    def test_load_from_string(self):
        """Test loading policy from JSON string"""
        policy_json = json.dumps({
            'config': {
                'version': '1.0.0',
                'name': 'StringPolicy',
                'description': 'Loaded from string',
                'rules': [
                    {'type': 'CoverageRule', 'threshold': 0.05}
                ],
                'escalation': {},
                'metadata': {}
            },
            'signature': None,
            'public_key': None,
            'policy_hash': None
        })

        policy = PolicyLoader.load_from_string(policy_json)
        assert policy.config.name == 'StringPolicy'
        assert len(policy.config.rules) == 1

    def test_load_from_file(self):
        """Test loading policy from file"""
        # Create temporary policy file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            policy_data = {
                'config': {
                    'version': '1.0.0',
                    'name': 'FilePolicy',
                    'description': 'Loaded from file',
                    'rules': [],
                    'escalation': {},
                    'metadata': {}
                },
                'signature': None,
                'public_key': None,
                'policy_hash': None
            }
            json.dump(policy_data, f)
            temp_path = Path(f.name)

        try:
            policy = PolicyLoader.load_from_file(temp_path)
            assert policy.config.name == 'FilePolicy'
        finally:
            temp_path.unlink()

    def test_load_unsigned_policy_without_signature_requirement(self):
        """Test loading unsigned policy when signature not required"""
        policy_json = json.dumps({
            'config': {
                'version': '1.0.0',
                'name': 'Unsigned',
                'description': 'No signature',
                'rules': [],
                'escalation': {},
                'metadata': {}
            },
            'signature': None,
            'public_key': None,
            'policy_hash': None
        })

        # Should succeed without signature
        policy = PolicyLoader.load_from_string(policy_json, require_signature=False)
        assert policy.config.name == 'Unsigned'

    def test_load_unsigned_policy_with_signature_requirement_fails(self):
        """Test loading unsigned policy fails when signature required"""
        policy_json = json.dumps({
            'config': {
                'version': '1.0.0',
                'name': 'Unsigned',
                'description': 'No signature',
                'rules': [],
                'escalation': {},
                'metadata': {}
            },
            'signature': None,
            'public_key': None,
            'policy_hash': None
        })

        # Should fail due to missing signature
        with pytest.raises(ValueError, match="signature verification failed"):
            PolicyLoader.load_from_string(policy_json, require_signature=True)


class TestPolicyManager:
    """Tests for PolicyManager"""

    def test_policy_manager_creation(self):
        """Test policy manager initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PolicyManager(policy_dir=Path(tmpdir))
            assert manager.policy_dir.exists()
            assert manager.current_policy is None

    def test_create_policy(self):
        """Test creating new policy"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PolicyManager(policy_dir=Path(tmpdir))

            policy = manager.create_policy(
                name="CreatedPolicy",
                description="Test creation",
                rules=[
                    {"type": "CoverageRule", "threshold": 0.1}
                ]
            )

            assert policy.config.name == "CreatedPolicy"
            assert manager.current_policy == policy

    def test_save_and_load_policy(self):
        """Test saving and loading policy"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PolicyManager(policy_dir=Path(tmpdir))

            # Create and save
            policy = manager.create_policy(
                name="SaveTest",
                description="Test save/load",
                rules=[]
            )
            manager.save_policy(policy, "test_policy")

            # Load
            loaded = manager.load_policy("test_policy")
            assert loaded.config.name == "SaveTest"
            assert loaded.policy_hash == policy.policy_hash

    def test_list_policies(self):
        """Test listing available policies"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PolicyManager(policy_dir=Path(tmpdir))

            # Create multiple policies
            for i in range(3):
                policy = manager.create_policy(
                    name=f"Policy{i}",
                    description="Test",
                    rules=[]
                )
                manager.save_policy(policy, f"policy_{i}")

            policies = manager.list_policies()
            assert len(policies) == 3
            assert "policy_0" in policies
            assert "policy_1" in policies
            assert "policy_2" in policies

    def test_policy_history(self):
        """Test policy version history tracking"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PolicyManager(policy_dir=Path(tmpdir))

            # Create and save multiple versions
            for i in range(3):
                policy = manager.create_policy(
                    name=f"Version{i}",
                    description=f"Version {i}",
                    rules=[]
                )
                manager.save_policy(policy, f"v{i}")
                manager.load_policy(f"v{i}")

            history = manager.get_history()
            assert len(history) == 3


class TestPolicyValidator:
    """Tests for PolicyValidator"""

    def test_validate_minimal_valid_policy(self):
        """Test validation of minimal valid policy"""
        policy_dict = {
            'config': {
                'version': '1.0.0',
                'name': 'ValidPolicy',
                'description': 'Valid minimal policy',
                'rules': [
                    {'type': 'InvariantRule'}
                ],
                'escalation': {},
                'metadata': {}
            }
        }

        result = PolicyValidator.validate(policy_dict)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_missing_required_field(self):
        """Test validation fails for missing required fields"""
        policy_dict = {
            'config': {
                'version': '1.0.0',
                'name': 'InvalidPolicy',
                # Missing 'description' and 'rules'
            }
        }

        result = PolicyValidator.validate(policy_dict)
        assert result.valid is False
        assert any('description' in err for err in result.errors)
        assert any('rules' in err for err in result.errors)

    def test_validate_invalid_version(self):
        """Test validation detects invalid version format"""
        policy_dict = {
            'config': {
                'version': '1.0',  # Should be x.y.z
                'name': 'Test',
                'description': 'Test',
                'rules': []
            }
        }

        result = PolicyValidator.validate(policy_dict)
        assert result.valid is False
        assert any('version' in err.lower() for err in result.errors)

    def test_validate_coverage_rule_missing_threshold(self):
        """Test validation detects missing threshold in CoverageRule"""
        policy_dict = {
            'config': {
                'version': '1.0.0',
                'name': 'Test',
                'description': 'Test',
                'rules': [
                    {'type': 'CoverageRule'}  # Missing threshold
                ]
            }
        }

        result = PolicyValidator.validate(policy_dict)
        assert result.valid is False
        assert any('threshold' in err for err in result.errors)

    def test_validate_coverage_rule_invalid_threshold(self):
        """Test validation detects out-of-range threshold"""
        policy_dict = {
            'config': {
                'version': '1.0.0',
                'name': 'Test',
                'description': 'Test',
                'rules': [
                    {'type': 'CoverageRule', 'threshold': 1.5}  # > 1.0
                ]
            }
        }

        result = PolicyValidator.validate(policy_dict)
        assert result.valid is False
        assert any('threshold' in err for err in result.errors)

    def test_validate_threshold_rule(self):
        """Test validation of ThresholdRule"""
        # Valid
        policy_dict = {
            'config': {
                'version': '1.0.0',
                'name': 'Test',
                'description': 'Test',
                'rules': [
                    {'type': 'ThresholdRule', 'max_uncertainty': 10.0}
                ]
            }
        }

        result = PolicyValidator.validate(policy_dict)
        assert result.valid is True

        # Invalid (negative)
        policy_dict['config']['rules'][0]['max_uncertainty'] = -5.0
        result = PolicyValidator.validate(policy_dict)
        assert result.valid is False

    def test_validate_composite_rule(self):
        """Test validation of CompositeRule"""
        policy_dict = {
            'config': {
                'version': '1.0.0',
                'name': 'Test',
                'description': 'Test',
                'rules': [
                    {
                        'type': 'CompositeRule',
                        'mode': 'and',
                        'rules': [
                            {'type': 'CoverageRule', 'threshold': 0.1},
                            {'type': 'ThresholdRule', 'max_uncertainty': 5.0}
                        ]
                    }
                ]
            }
        }

        result = PolicyValidator.validate(policy_dict)
        assert result.valid is True

    def test_validate_invalid_event_level(self):
        """Test validation detects invalid event level"""
        policy_dict = {
            'config': {
                'version': '1.0.0',
                'name': 'Test',
                'description': 'Test',
                'rules': [
                    {'type': 'InvariantRule', 'level': 'invalid_level'}
                ]
            }
        }

        result = PolicyValidator.validate(policy_dict)
        assert result.valid is False
        assert any('level' in err.lower() for err in result.errors)

    def test_validate_warns_on_unsigned_policy(self):
        """Test validation warns for unsigned policies"""
        policy_dict = {
            'config': {
                'version': '1.0.0',
                'name': 'Test',
                'description': 'Test',
                'rules': [{'type': 'InvariantRule'}]
            },
            'signature': None
        }

        result = PolicyValidator.validate(policy_dict)
        assert result.valid is True
        assert any('not signed' in warn.lower() for warn in result.warnings)

    def test_validate_and_raise(self):
        """Test validate_and_raise throws exception"""
        policy_dict = {
            'config': {
                'name': 'Invalid'
                # Missing required fields
            }
        }

        with pytest.raises(PolicyValidationError):
            PolicyValidator.validate_and_raise(policy_dict)


class TestPolicyExporter:
    """Tests for PolicyExporter"""

    def test_export_json(self):
        """Test JSON export"""
        config = PolicyConfig(
            version="1.0.0",
            name="ExportTest",
            description="Test",
            rules=[]
        )
        policy = Policy(config=config)

        json_str = PolicyExporter.export(policy, format=ExportFormat.JSON)
        data = json.loads(json_str)

        assert data['config']['name'] == 'ExportTest'

    def test_export_json_compact(self):
        """Test compact JSON export"""
        config = PolicyConfig(
            version="1.0.0",
            name="Compact",
            description="Test",
            rules=[]
        )
        policy = Policy(config=config)

        compact = PolicyExporter.export(policy, format=ExportFormat.JSON_COMPACT)

        # Compact should have no newlines (except potentially in strings)
        assert '\n  ' not in compact  # No indentation

    def test_export_summary(self):
        """Test human-readable summary export"""
        config = PolicyConfig(
            version="1.0.0",
            name="SummaryTest",
            description="Summary test policy",
            rules=[
                {'type': 'CoverageRule', 'threshold': 0.05, 'level': 'warning'},
                {'type': 'InvariantRule', 'level': 'critical'}
            ],
            escalation={'halt_on_critical': True, 'auto_log': True}
        )
        policy = Policy(config=config)

        summary = PolicyExporter.export(policy, format=ExportFormat.SUMMARY)

        assert 'SummaryTest' in summary
        assert '1.0.0' in summary
        assert 'CoverageRule' in summary
        assert 'InvariantRule' in summary
        assert 'halt_on_critical: True' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
