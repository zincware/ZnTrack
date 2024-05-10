"""Module to handle notifications."""
import dataclasses
import yaml

@dataclasses.dataclass
class NotificationHandler:
    """Handle ZnTrack notifications to external services."""

    @classmethod
    def from_config(cls, config_file: str):
        """Create a NotificationHandler from a configuration file."""
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
        return cls(**config)
    
    def send(self, message: str) -> None:
        """Send a message to the notification service."""
        raise NotImplementedError
        