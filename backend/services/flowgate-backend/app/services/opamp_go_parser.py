"""Go-based OpAMP Protocol Parser

This module provides a Python wrapper around the Go-based opamp-parser binary
to ensure 100% compatibility with Go protobuf implementations.
"""

import json
import subprocess
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OpAMPGoParser:
    """Wrapper for Go-based OpAMP protobuf parser"""

    def __init__(self, parser_binary: Optional[str] = None):
        """
        Initialize the Go parser wrapper.

        Args:
            parser_binary: Path to opamp-parser binary. If None, tries to find it.
        """
        if parser_binary is None:
            # Try to find the binary in common locations
            possible_paths = [
                "/app/bin/opamp-parser",
                "/usr/local/bin/opamp-parser",
                "./bin/opamp-parser",  # Local bin directory (for volume mounts)
                "opamp-parser",  # In PATH
            ]
            for path in possible_paths:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    parser_binary = path
                    break

        if parser_binary is None or not os.path.isfile(parser_binary):
            raise FileNotFoundError(
                f"opamp-parser binary not found. Please ensure it's installed and in PATH."
            )

        self.parser_binary = parser_binary
        logger.info(f"Using OpAMP Go parser: {self.parser_binary}")

    def parse_agent_message(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse AgentToServer message from protobuf bytes using Go parser.

        Args:
            data: Raw protobuf message bytes

        Returns:
            Parsed message as dictionary, or None if parsing failed
        """
        if not data:
            return None

        try:
            # Call Go parser binary
            process = subprocess.Popen(
                [self.parser_binary, "-mode=parse"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout, stderr = process.communicate(input=data, timeout=5)

            # Parse JSON response (even if exit code is non-zero, it might have error JSON)
            try:
                response = json.loads(stdout.decode("utf-8"))
                if not response.get("success"):
                    error_msg = response.get("error", "Unknown error")
                    logger.debug(f"Go parser returned error: {error_msg}")
                    return None
                return response.get("message")
            except json.JSONDecodeError:
                # If JSON parsing fails, check stderr
                error_msg = stderr.decode("utf-8", errors="ignore")
                if process.returncode != 0:
                    logger.debug(
                        f"Go parser failed (exit code {process.returncode}): {error_msg or 'No error message'}"
                    )
                return None

        except subprocess.TimeoutExpired:
            logger.error("Go parser timed out")
            process.kill()
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Go parser JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Go parser: {e}", exc_info=True)
            return None

    def serialize_server_message(self, message: Dict[str, Any]) -> Optional[bytes]:
        """
        Serialize ServerToAgent message to protobuf bytes using Go parser.

        Args:
            message: Message as dictionary

        Returns:
            Serialized protobuf bytes, or None if serialization failed
        """
        try:
            # Prepare JSON input
            input_data = json.dumps({"message": message}).encode("utf-8")

            # Call Go parser binary
            process = subprocess.Popen(
                [self.parser_binary, "-mode=serialize"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout, stderr = process.communicate(input=input_data, timeout=5)

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore")
                logger.error(
                    f"Go serializer failed (exit code {process.returncode}): {error_msg}"
                )
                return None

            return stdout

        except subprocess.TimeoutExpired:
            logger.error("Go serializer timed out")
            process.kill()
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Go serializer: {e}", exc_info=True)
            return None


# Global instance (lazy initialization)
_go_parser: Optional[OpAMPGoParser] = None


def get_go_parser() -> Optional[OpAMPGoParser]:
    """Get or create the global Go parser instance"""
    global _go_parser
    if _go_parser is None:
        try:
            _go_parser = OpAMPGoParser()
        except FileNotFoundError as e:
            logger.warning(f"Go parser not available: {e}. Falling back to Python parser.")
            return None
    return _go_parser

