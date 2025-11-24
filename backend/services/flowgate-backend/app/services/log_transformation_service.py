"""Log Transformation Service

Service for managing log format templates and AI-assisted log transformation.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json
import yaml
import httpx
from datetime import datetime

from app.models.log_format_template import LogFormatTemplate, LogFormatType
from app.services.settings_service import SettingsService
from app.core.messaging import get_nats_client, format_log_subject
import asyncio


class LogTransformationService:
    """Service for managing log transformations"""

    def __init__(self, db: Session):
        self.db = db
        self.settings_service = SettingsService(db)

    def get_format_templates(self, format_type: Optional[str] = None) -> List[LogFormatTemplate]:
        """Get list of format templates with optional filter"""
        query = self.db.query(LogFormatTemplate)

        if format_type:
            # Convert string to enum if needed
            try:
                from app.models.log_format_template import LogFormatType
                format_type_enum = LogFormatType(format_type.lower())
                query = query.filter(LogFormatTemplate.format_type == format_type_enum)
            except ValueError:
                # If invalid format_type, just ignore the filter
                pass

        return query.order_by(LogFormatTemplate.display_name).all()

    def get_format_template(self, format_name: str) -> Optional[LogFormatTemplate]:
        """Get a single format template by name"""
        return self.db.query(LogFormatTemplate).filter(
            LogFormatTemplate.format_name == format_name
        ).first()

    def generate_target_json(
        self,
        org_id: str,
        source_format: Optional[str],
        sample_logs: str,
        ai_prompt: str
    ) -> Dict[str, Any]:
        """Generate target JSON structure from AI prompt"""
        try:
            # Convert org_id string to UUID if needed
            from uuid import UUID
            org_id_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
            
            # Get source format template if provided
            source_template = None
            if source_format:
                source_template = self.get_format_template(source_format)

            # Get AI provider config
            settings = self.settings_service.get_settings(org_id_uuid)
            ai_config = settings.ai_provider_config if settings else None

            if not ai_config or not ai_config.get("is_active"):
                return {
                    "success": False,
                    "target_json": "",
                    "warnings": [],
                    "errors": ["AI provider is not configured. Please configure AI settings first."]
                }

            # Validate API key
            api_key = ai_config.get("api_key")
            if not api_key or api_key.startswith("*"):
                return {
                    "success": False,
                    "target_json": "",
                    "warnings": [],
                    "errors": ["AI API key is not configured or invalid."]
                }

            # Build prompt for target JSON generation
            prompt_parts = [
                "Based on the following log samples and requirements, generate a JSON structure that represents the desired output format.",
                "\nSample Logs:",
                sample_logs
            ]

            if source_template:
                prompt_parts.append(f"\nSource Format: {source_template.display_name}")
                if source_template.schema:
                    prompt_parts.append(f"Current Format Schema: {json.dumps(source_template.schema, indent=2)}")

            prompt_parts.append(f"\nUser Requirements: {ai_prompt}")
            prompt_parts.append("\nGenerate a JSON object that represents the target structure.")
            prompt_parts.append("The JSON should include all fields mentioned in the requirements.")
            prompt_parts.append("Use example values that match the data types and formats requested.")
            prompt_parts.append("Return only valid JSON, no explanations or markdown formatting.")

            prompt = "\n".join(prompt_parts)

            # Query AI provider with JSON-specific system prompt
            try:
                generated_json = self._query_ai_provider_for_json(ai_config, prompt)
                
                # Clean up the response - remove markdown code blocks if present
                generated_json = generated_json.strip()
                if generated_json.startswith("```json"):
                    generated_json = generated_json[7:]
                if generated_json.startswith("```"):
                    generated_json = generated_json[3:]
                if generated_json.endswith("```"):
                    generated_json = generated_json[:-3]
                generated_json = generated_json.strip()

                # Validate JSON syntax
                try:
                    json.loads(generated_json)
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "target_json": "",
                        "warnings": [],
                        "errors": [f"Generated JSON is invalid: {str(e)}"]
                    }

                return {
                    "success": True,
                    "target_json": generated_json,
                    "warnings": [],
                    "errors": []
                }

            except httpx.HTTPStatusError as e:
                error_msg = f"AI provider returned error {e.response.status_code}"
                if e.response.status_code == 400:
                    error_msg += ": Bad Request"
                    # Try to get more details from the response
                    try:
                        error_body = e.response.json()
                        if "error" in error_body:
                            error_detail = error_body["error"]
                            if isinstance(error_detail, dict):
                                if "message" in error_detail:
                                    error_msg += f" - {error_detail['message']}"
                                elif "type" in error_detail:
                                    error_msg += f" - {error_detail['type']}"
                            else:
                                error_msg += f" - {str(error_detail)}"
                        else:
                            error_text = e.response.text[:300]
                            if error_text:
                                error_msg += f" - {error_text}"
                    except:
                        try:
                            error_text = e.response.text[:300]
                            if error_text:
                                error_msg += f" - {error_text}"
                        except:
                            error_msg += " - Check API key, model name, and request format"
                elif e.response.status_code == 401:
                    error_msg += ": Unauthorized - Invalid API key"
                elif e.response.status_code == 429:
                    error_msg += ": Rate limit exceeded"
                else:
                    try:
                        error_detail = e.response.text[:200]
                        error_msg += f": {error_detail}"
                    except:
                        pass
                
                return {
                    "success": False,
                    "target_json": "",
                    "warnings": [],
                    "errors": [error_msg]
                }
            except httpx.RequestError as e:
                return {
                    "success": False,
                    "target_json": "",
                    "warnings": [],
                    "errors": [f"AI provider connection failed: {str(e)}"]
                }

        except Exception as e:
            return {
                "success": False,
                "target_json": "",
                "warnings": [],
                "errors": [f"Failed to generate target JSON: {str(e)}"]
            }

    def transform_logs(
        self,
        org_id: str,
        source_format: Optional[str],
        destination_format: Optional[str],  # Deprecated, kept for backward compatibility
        sample_logs: str,
        target_json: Optional[str] = None,
        ai_prompt: Optional[str] = None,
        custom_source_parser: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transform logs using AI and generate OTel config"""
        try:
            # Convert org_id string to UUID if needed
            from uuid import UUID
            org_id_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
            
            # Get source format template if provided
            source_template = None
            if source_format:
                source_template = self.get_format_template(source_format)

            # Destination format is deprecated - we only use target_json now
            dest_template = None

            # Generate target_json from ai_prompt if provided
            final_target_json = target_json
            if ai_prompt and not target_json:
                target_json_result = self.generate_target_json(org_id, source_format, sample_logs, ai_prompt)
                if not target_json_result.get("success"):
                    return {
                        "success": False,
                        "otel_config": "",
                        "warnings": target_json_result.get("warnings", []),
                        "errors": target_json_result.get("errors", []),
                        "recommendations": []
                    }
                final_target_json = target_json_result.get("target_json")

            # Validate that target_json is provided (required)
            if not final_target_json or not final_target_json.strip():
                return {
                    "success": False,
                    "otel_config": "",
                    "warnings": [],
                    "errors": ["target_json is required. Please provide the desired output JSON structure or use AI prompt to generate it."],
                    "recommendations": []
                }

            # Generate OTel config using AI
            otel_config, warnings, errors = self._generate_otel_config(
                org_id_uuid,
                source_template,
                dest_template,
                sample_logs,
                final_target_json,
                custom_source_parser
            )

            result = {
                "success": len(errors) == 0,
                "otel_config": otel_config,
                "warnings": warnings,
                "errors": errors,
                "recommendations": []
            }

            # Publish normalized logs to NATS for threat detection pipeline
            if result["success"] and sample_logs:
                try:
                    self._publish_normalized_logs_to_nats(
                        org_id,
                        source_format or "custom",
                        sample_logs,
                        final_target_json
                    )
                except Exception as e:
                    # Don't fail the transformation if NATS publish fails
                    warnings.append(f"Failed to publish to NATS: {str(e)}")

            return result

        except Exception as e:
            return {
                "success": False,
                "otel_config": "",
                "warnings": [],
                "errors": [str(e)],
                "recommendations": []
            }

    def get_format_recommendations(
        self,
        org_id: str,
        source_format: Optional[str],
        sample_logs: Optional[str],
        use_case: Optional[str]
    ) -> Dict[str, Any]:
        """Get AI-based recommendations for destination formats"""
        try:
            # Convert org_id string to UUID
            from uuid import UUID
            org_id_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
            
            # Get AI provider config
            settings = self.settings_service.get_settings(org_id_uuid)
            ai_config = settings.ai_provider_config if settings else None

            if not ai_config or not ai_config.get("is_active"):
                # Return default recommendations if AI is not configured
                return self._get_default_recommendations(source_format)

            # Analyze source format and sample logs
            analysis = self._analyze_logs(source_format, sample_logs)

            # Query AI for recommendations
            recommendations = self._query_ai_recommendations(
                ai_config,
                source_format,
                analysis,
                use_case
            )

            return {
                "success": True,
                "recommendations": recommendations,
                "message": "Recommendations generated successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "recommendations": [],
                "message": f"Failed to get recommendations: {str(e)}"
            }

    def _generate_otel_config(
        self,
        org_id,
        source_template: Optional[LogFormatTemplate],
        dest_template: Optional[LogFormatTemplate],
        sample_logs: str,
        target_json: Optional[str],
        custom_source_parser: Optional[Dict[str, Any]]
    ) -> tuple[str, List[str], List[str]]:
        """Generate OTel transform processor config using AI"""
        warnings = []
        errors = []

        try:
            # Get AI provider config
            from uuid import UUID
            org_id_uuid = org_id if isinstance(org_id, UUID) else UUID(org_id)
            settings = self.settings_service.get_settings(org_id_uuid)
            ai_config = settings.ai_provider_config if settings else None

            if not ai_config or not ai_config.get("is_active"):
                # Generate basic config without AI
                warnings.append("AI provider not configured. Generating basic config.")
                return self._generate_basic_config(
                    source_template,
                    dest_template,
                    sample_logs,
                    target_json,
                    custom_source_parser
                )

            # Validate AI config
            api_key = ai_config.get("api_key")
            if not api_key or api_key.startswith("*"):
                warnings.append("AI API key not configured or masked. Falling back to basic config.")
                return self._generate_basic_config(
                    source_template,
                    dest_template,
                    sample_logs,
                    target_json,
                    custom_source_parser
                )

            # Build AI prompt
            prompt = self._build_ai_prompt(
                source_template,
                dest_template,
                sample_logs,
                target_json,
                custom_source_parser
            )

            # Query AI provider
            try:
                otel_config = self._query_ai_provider(ai_config, prompt)
                
                # Validate generated config
                validation_errors = self._validate_config_syntax(otel_config)
                if validation_errors:
                    errors.extend(validation_errors)
                    warnings.append("Generated config has syntax errors")
                    # Fall back to basic config if AI-generated config is invalid
                    if len(errors) > 0:
                        warnings.append("Falling back to basic config due to validation errors.")
                        return self._generate_basic_config(
                            source_template,
                            dest_template,
                            sample_logs,
                            target_json,
                            custom_source_parser
                        )

                return otel_config, warnings, errors
            except httpx.HTTPStatusError as e:
                # Handle HTTP errors from AI provider
                error_msg = f"AI provider returned error {e.response.status_code}"
                if e.response.status_code == 400:
                    error_msg += ": Bad Request - Check API key and model name"
                elif e.response.status_code == 401:
                    error_msg += ": Unauthorized - Invalid API key"
                elif e.response.status_code == 429:
                    error_msg += ": Rate limit exceeded"
                else:
                    error_msg += f": {e.response.text[:200]}"
                
                warnings.append(f"AI generation failed: {error_msg}. Falling back to basic config.")
                return self._generate_basic_config(
                    source_template,
                    dest_template,
                    sample_logs,
                    target_json,
                    custom_source_parser
                )
            except httpx.RequestError as e:
                warnings.append(f"AI provider connection failed: {str(e)}. Falling back to basic config.")
                return self._generate_basic_config(
                    source_template,
                    dest_template,
                    sample_logs,
                    target_json,
                    custom_source_parser
                )

        except httpx.HTTPStatusError as e:
            # Handle HTTP errors that weren't caught in inner try-catch
            error_msg = f"AI provider returned error {e.response.status_code}"
            if e.response.status_code == 400:
                error_msg += ": Bad Request - Check API key and model name"
            elif e.response.status_code == 401:
                error_msg += ": Unauthorized - Invalid API key"
            elif e.response.status_code == 429:
                error_msg += ": Rate limit exceeded"
            else:
                try:
                    error_detail = e.response.text[:200]
                    error_msg += f": {error_detail}"
                except:
                    pass
            
            warnings.append(f"AI generation failed: {error_msg}. Falling back to basic config.")
            return self._generate_basic_config(
                source_template,
                dest_template,
                sample_logs,
                target_json,
                custom_source_parser
            )
        except httpx.RequestError as e:
            warnings.append(f"AI provider connection failed: {str(e)}. Falling back to basic config.")
            return self._generate_basic_config(
                source_template,
                dest_template,
                sample_logs,
                target_json,
                custom_source_parser
            )
        except Exception as e:
            # For any other unexpected errors, try to fall back to basic config
            warnings.append(f"Unexpected error in AI generation: {str(e)}. Falling back to basic config.")
            try:
                return self._generate_basic_config(
                    source_template,
                    dest_template,
                    sample_logs,
                    target_json,
                    custom_source_parser
                )
            except Exception as fallback_error:
                errors.append(f"Failed to generate config: {str(e)}")
                errors.append(f"Fallback also failed: {str(fallback_error)}")
                return "", warnings, errors

    def _generate_basic_config(
        self,
        source_template: Optional[LogFormatTemplate],
        dest_template: Optional[LogFormatTemplate],
        sample_logs: str,
        target_json: Optional[str],
        custom_source_parser: Optional[Dict[str, Any]]
    ) -> tuple[str, List[str], List[str]]:
        """Generate basic OTel config without AI"""
        config_parts = ["processors:"]
        config_parts.append("  transform:")
        config_parts.append("    log_statements:")
        config_parts.append("      - context: log")
        config_parts.append("        statements:")

        # Add parser if source template provided
        if source_template and source_template.parser_config:
            parser_type = source_template.parser_config.get("type", "regex")
            if parser_type == "regex":
                regex = source_template.parser_config.get("regex", "")
                config_parts.append(f'        # Parse using regex: {regex[:50]}...')

        # Add basic transformation rules based on target JSON
        # Target JSON is required, so we should always have it
        if target_json:
            try:
                target = json.loads(target_json)
                for key, value in target.items():
                    if isinstance(value, str):
                        config_parts.append(f'        - set(attributes["{key}"], "{value}")')
                    else:
                        config_parts.append(f'        - set(attributes["{key}"], {json.dumps(value)})')
            except json.JSONDecodeError:
                warnings.append("Invalid target JSON format. Please provide valid JSON.")
        else:
            warnings.append("Target JSON is required for transformation. Please provide the desired output structure.")

        return "\n".join(config_parts), [], []

    def _build_ai_prompt(
        self,
        source_template: Optional[LogFormatTemplate],
        dest_template: Optional[LogFormatTemplate],
        sample_logs: str,
        target_json: Optional[str],
        custom_source_parser: Optional[Dict[str, Any]]
    ) -> str:
        """Build AI prompt for config generation"""
        prompt_parts = [
            "Generate an OpenTelemetry Collector transform processor configuration",
            "that transforms the source logs into the target JSON structure.\n"
        ]

        if source_template:
            prompt_parts.append(f"Source Format: {source_template.display_name} ({source_template.format_name})")
            if source_template.parser_config:
                prompt_parts.append(f"Parser Config: {json.dumps(source_template.parser_config, indent=2)}")
            if source_template.sample_logs:
                prompt_parts.append(f"Example Source Log Format:\n{source_template.sample_logs}")

        prompt_parts.append(f"\nActual Sample Logs to Transform:\n{sample_logs}")

        if target_json:
            prompt_parts.append(f"\nTarget JSON Structure (Required Output):\n{target_json}")
            prompt_parts.append("\nThe transformation must extract fields from the source logs and structure them")
            prompt_parts.append("exactly as shown in the target JSON structure above.")

        prompt_parts.append("\nGenerate a complete OpenTelemetry transform processor YAML configuration.")
        prompt_parts.append("Include parser configuration if needed for the source format.")
        prompt_parts.append("Create transformation rules that map source log fields to the target JSON structure.")
        prompt_parts.append("Return only valid YAML, no explanations.")

        return "\n".join(prompt_parts)

    def _query_ai_provider(self, ai_config: Dict[str, Any], prompt: str) -> str:
        """Query AI provider for config generation"""
        return self._query_ai_provider_with_system_prompt(
            ai_config, 
            prompt, 
            "You are an expert in OpenTelemetry Collector configuration. Generate valid YAML configurations."
        )

    def _query_ai_provider_for_json(self, ai_config: Dict[str, Any], prompt: str) -> str:
        """Query AI provider for JSON structure generation"""
        return self._query_ai_provider_with_system_prompt(
            ai_config,
            prompt,
            "You are an expert in data structure design. Generate valid JSON objects that represent log data structures. Return only valid JSON, no markdown formatting or explanations."
        )

    def _query_ai_provider_with_system_prompt(
        self, 
        ai_config: Dict[str, Any], 
        prompt: str, 
        system_prompt: str
    ) -> str:
        """Query AI provider with a custom system prompt"""
        provider_type = ai_config.get("provider_type")
        endpoint = ai_config.get("endpoint")
        api_key = ai_config.get("api_key")
        model = ai_config.get("model", "gpt-4")
        # Get temperature from config, or use None (which means use model default)
        temperature = ai_config.get("temperature")

        if not model:
            raise ValueError("Model name is required in AI provider configuration")

        # Base payload structure
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        payload = {
            "model": model,
            "messages": messages
        }

        # Only add temperature if explicitly set in config
        # Otherwise, let the model use its default temperature
        if temperature is not None:
            payload["temperature"] = temperature

        if provider_type == "litellm" and endpoint:
            # Use LiteLLM endpoint
            url = f"{endpoint.rstrip('/')}/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        elif provider_type == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        else:
            raise ValueError(f"Unsupported AI provider: {provider_type}")

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

    def _query_ai_recommendations(
        self,
        ai_config: Dict[str, Any],
        source_format: Optional[str],
        analysis: Dict[str, Any],
        use_case: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Query AI for format recommendations"""
        prompt = f"""Analyze the log format and recommend the best destination formats for transformation.

Source Format: {source_format or "Unknown"}
Log Characteristics: {json.dumps(analysis, indent=2)}
Use Case: {use_case or "General"}

Recommend 3-5 destination formats with:
- format_name
- display_name
- confidence_score (0-1)
- reasoning
- compatibility_score (0-1)

Return as JSON array."""

        try:
            response_text = self._query_ai_provider(ai_config, prompt)
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                return recommendations
        except Exception:
            pass

        # Fallback to default recommendations
        return self._get_default_recommendations(source_format)

    def _analyze_logs(self, source_format: Optional[str], sample_logs: Optional[str]) -> Dict[str, Any]:
        """Analyze log characteristics"""
        analysis = {
            "has_timestamps": False,
            "has_structured_data": False,
            "has_json": False,
            "line_count": 0,
            "avg_line_length": 0
        }

        if sample_logs:
            lines = sample_logs.strip().split('\n')
            analysis["line_count"] = len(lines)
            if lines:
                analysis["avg_line_length"] = sum(len(line) for line in lines) / len(lines)
                analysis["has_timestamps"] = any(
                    "2024" in line or "2023" in line or "T" in line or "/" in line
                    for line in lines[:5]
                )
                analysis["has_json"] = any(
                    line.strip().startswith('{') and line.strip().endswith('}')
                    for line in lines[:5]
                )
                analysis["has_structured_data"] = analysis["has_json"] or "," in lines[0]

        if source_format:
            analysis["source_format"] = source_format

        return analysis

    def _get_default_recommendations(self, source_format: Optional[str]) -> List[Dict[str, Any]]:
        """Get default format recommendations"""
        recommendations = [
            {
                "format_name": "structured_json",
                "display_name": "Structured JSON",
                "confidence_score": 0.9,
                "reasoning": "Structured JSON is a versatile format suitable for most use cases",
                "compatibility_score": 0.8
            },
            {
                "format_name": "otlp",
                "display_name": "OpenTelemetry Protocol",
                "confidence_score": 0.85,
                "reasoning": "OTLP is the standard format for OpenTelemetry observability pipelines",
                "compatibility_score": 0.75
            }
        ]

        if source_format == "json":
            recommendations.insert(0, {
                "format_name": "otlp",
                "display_name": "OpenTelemetry Protocol",
                "confidence_score": 0.95,
                "reasoning": "JSON logs can be easily converted to OTLP format",
                "compatibility_score": 0.9
            })

        return recommendations

    def _validate_config_syntax(self, config: str) -> List[str]:
        """Validate OTel config syntax"""
        errors = []
        try:
            yaml.safe_load(config)
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML syntax: {str(e)}")
        return errors

    def dry_run_config(self, config_yaml: str, sample_logs: str) -> tuple[List[Dict[str, Any]], List[str]]:
        """Execute a dry run of the OTel config on sample logs"""
        errors = []
        transformed_logs = []
        
        try:
            # Parse the config
            config = yaml.safe_load(config_yaml)
            if not config:
                return [], ["Invalid or empty config"]
            
            # Extract transform processor statements
            transform_statements = []
            if "processors" in config and "transform" in config["processors"]:
                transform_config = config["processors"]["transform"]
                if "log_statements" in transform_config:
                    for statement_group in transform_config["log_statements"]:
                        if "statements" in statement_group:
                            transform_statements.extend(statement_group["statements"])
            
            # Parse sample logs (split by newlines)
            log_lines = [line.strip() for line in sample_logs.strip().split('\n') if line.strip()]
            
            if not log_lines:
                return [], ["No sample logs provided"]
            
            # Process each log line
            for log_line in log_lines:
                # Create a base log entry
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": "INFO",
                    "message": log_line,
                    "attributes": {}
                }
                
                # Apply transformation statements
                for statement in transform_statements:
                    try:
                        # Parse statements like: set(attributes["method"], "GET")
                        # or: set(attributes["key"], value)
                        if statement.startswith("set(") and statement.endswith(")"):
                            # Extract the set statement content
                            content = statement[4:-1]  # Remove "set(" and ")"
                            
                            # Parse: attributes["key"], value
                            if ', ' in content:
                                parts = content.split(', ', 1)
                                if len(parts) == 2:
                                    attr_expr = parts[0].strip()
                                    value_expr = parts[1].strip()
                                    
                                    # Extract attribute key from attributes["key"]
                                    if attr_expr.startswith('attributes["') and attr_expr.endswith('"]'):
                                        key = attr_expr[12:-2]  # Extract key from attributes["key"]
                                        
                                        # Parse value (could be string, number, or expression)
                                        value = self._parse_value(value_expr, log_line)
                                        
                                        log_entry["attributes"][key] = value
                    except Exception as e:
                        errors.append(f"Error processing statement '{statement}': {str(e)}")
                
                # Try to extract additional fields from the log line if it looks structured
                self._extract_log_fields(log_entry, log_line)
                
                transformed_logs.append(log_entry)
            
        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {str(e)}")
        except Exception as e:
            errors.append(f"Dry run error: {str(e)}")
        
        return transformed_logs, errors

    def _parse_value(self, value_expr: str, log_line: str) -> Any:
        """Parse a value expression from a transform statement"""
        value_expr = value_expr.strip()
        
        # If it's a quoted string, return the string
        if value_expr.startswith('"') and value_expr.endswith('"'):
            return value_expr[1:-1]
        if value_expr.startswith("'") and value_expr.endswith("'"):
            return value_expr[1:-1]
        
        # If it's a number, try to parse it
        try:
            if '.' in value_expr:
                return float(value_expr)
            return int(value_expr)
        except ValueError:
            pass
        
        # If it's a boolean
        if value_expr.lower() == "true":
            return True
        if value_expr.lower() == "false":
            return False
        
        # If it's null
        if value_expr.lower() == "null" or value_expr.lower() == "none":
            return None
        
        # Otherwise, return as string
        return value_expr

    def _extract_log_fields(self, log_entry: Dict[str, Any], log_line: str) -> None:
        """Try to extract common fields from log lines"""
        # Try to parse as JSON first
        try:
            json_data = json.loads(log_line)
            if isinstance(json_data, dict):
                for key, value in json_data.items():
                    if key not in log_entry["attributes"]:
                        log_entry["attributes"][key] = value
                return
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try to extract common patterns
        # HTTP method
        if "GET" in log_line or "POST" in log_line or "PUT" in log_line or "DELETE" in log_line:
            for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                if method in log_line:
                    if "method" not in log_entry["attributes"]:
                        log_entry["attributes"]["method"] = method
                    break
        
        # Status code pattern
        import re
        status_match = re.search(r'\b(\d{3})\b', log_line)
        if status_match:
            status_code = status_match.group(1)
            if status_code.startswith(('2', '3', '4', '5')):
                if "status" not in log_entry["attributes"]:
                    log_entry["attributes"]["status"] = int(status_code)
        
        # IP address
        ip_match = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', log_line)
        if ip_match:
            if "ip" not in log_entry["attributes"]:
                log_entry["attributes"]["ip"] = ip_match.group(1)
        
        # URL path
        url_match = re.search(r'(\/[^\s\?]+)', log_line)
        if url_match:
            if "path" not in log_entry["attributes"]:
                log_entry["attributes"]["path"] = url_match.group(1)

    def _parse_logs_with_template(self, logs: str, format_template: LogFormatTemplate) -> List[Dict[str, Any]]:
        """Parse logs using template parser configuration"""
        # This would implement actual parsing logic
        # For now, return placeholder
        return []

    def _validate_transformation(self, config: str, sample_logs: str) -> Dict[str, Any]:
        """Validate transformation config"""
        errors = []
        warnings = []

        # Validate YAML syntax
        yaml_errors = self._validate_config_syntax(config)
        errors.extend(yaml_errors)

        # Additional validation could be added here

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _publish_normalized_logs_to_nats(
        self,
        org_id: str,
        source_type: str,
        log_data: str,
        target_json: Optional[str] = None
    ) -> None:
        """Publish normalized logs to NATS for threat detection pipeline"""
        try:
            nats_client = get_nats_client()
            if not nats_client.is_connected():
                # Try to connect synchronously (in production, this should be async)
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                if loop.is_running():
                    # If loop is already running, schedule the connection
                    asyncio.create_task(nats_client.connect())
                else:
                    loop.run_until_complete(nats_client.connect())

            # Prepare message payload
            message = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": source_type,
                "log_data": log_data,
                "metadata": {
                    "target_json": target_json,
                    "org_id": org_id
                },
                "org_id": org_id
            }

            # Format subject
            subject = format_log_subject(source_type, org_id)

            # Publish to NATS (async)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                asyncio.create_task(nats_client.publish(subject, message))
            else:
                loop.run_until_complete(nats_client.publish(subject, message))

        except Exception as e:
            # Log error but don't raise - NATS publishing is non-blocking
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to publish normalized logs to NATS: {e}")

