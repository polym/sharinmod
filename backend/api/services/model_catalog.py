"""Model catalog module - deprecated.

This module previously contained built-in provider and model configurations.
All provider configurations are now loaded from etc/providers.yaml on application startup.

To add new providers:
1. Add configuration to etc/providers.yaml
2. Restart the application to import the configuration

To modify existing providers:
1. Update etc/providers.yaml
2. Restart the application (upsert logic will update existing providers)
"""

# This module is kept for backward compatibility but contains no active code.
# All built-in provider info has been migrated to etc/providers.yaml.
