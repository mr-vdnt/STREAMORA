"""
DAP Validator Stage — Schema and business rule validation.
"""
from __future__ import annotations
import logging
from typing import List
from services.ingestion.contracts import PipelineStage, PipelineMessage, MessageType
from services.ingestion.dtos import ValidationResult

logger = logging.getLogger("streamora.ingestion.validator")


class ValidatorStage(PipelineStage):
    """Validates raw payloads against schema and business rules.
    
    Consumes: RAW_PAYLOAD messages
    Emits: VALIDATED messages (or FAILED)
    """

    @property
    def stage_name(self) -> str:
        return "validator"

    async def process(self, message: PipelineMessage) -> PipelineMessage:
        raw_data = message.payload
        if not isinstance(raw_data, dict):
            return self._fail(message, "Payload is not a dictionary")

        result = self._validate(raw_data, message.entity_type)

        if not result.is_valid:
            error_str = "; ".join(result.errors)
            logger.warning(f"Validation failed for {message.external_id}: {error_str}")
            return PipelineMessage(
                message_type=MessageType.FAILED,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=message.payload,
                raw_payload_id=message.raw_payload_id,
                error=f"validation: {error_str}",
                metadata={**message.metadata, "failure_stage": "validation"},
                trace_id=message.trace_id,
            )

        if result.warnings:
            logger.info(f"Validation warnings for {message.external_id}: {result.warnings}")

        return PipelineMessage(
            message_type=MessageType.VALIDATED,
            job_id=message.job_id,
            connector_name=message.connector_name,
            external_id=message.external_id,
            entity_type=message.entity_type,
            payload=message.payload,
            raw_payload_id=message.raw_payload_id,
            metadata={**message.metadata, "validation_warnings": result.warnings},
            trace_id=message.trace_id,
        )

    def _validate(self, data: dict, entity_type: str) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # --- Required Fields ---
        title = data.get("title") or data.get("name")
        if not title:
            errors.append("Missing required field: title/name")

        external_id = data.get("id") or data.get("tmdb_id")
        if not external_id:
            errors.append("Missing required field: id/tmdb_id")

        # --- Data Type Assertions ---
        rating = data.get("vote_average") or data.get("rating")
        if rating is not None:
            try:
                rating_val = float(rating)
                if rating_val < 0.0 or rating_val > 10.0:
                    errors.append(f"Rating {rating_val} out of range [0.0, 10.0]")
            except (ValueError, TypeError):
                errors.append(f"Rating is not numeric: {rating}")

        popularity = data.get("popularity")
        if popularity is not None:
            try:
                float(popularity)
            except (ValueError, TypeError):
                warnings.append(f"Popularity is not numeric: {popularity}")

        # --- Business Rules ---
        runtime = data.get("runtime")
        if runtime is not None:
            try:
                runtime_val = int(runtime)
                if runtime_val < 0:
                    errors.append(f"Runtime is negative: {runtime_val}")
            except (ValueError, TypeError):
                warnings.append(f"Runtime is not an integer: {runtime}")

        # Date validation
        release_date = data.get("release_date") or data.get("first_air_date")
        if release_date and isinstance(release_date, str):
            parts = release_date.split("-")
            if len(parts) >= 1:
                try:
                    year = int(parts[0])
                    if year < 1888 or year > 2100:
                        warnings.append(f"Suspicious release year: {year}")
                except ValueError:
                    warnings.append(f"Unparseable release date: {release_date}")

        # Entity-type specific
        if entity_type == "tvseries":
            seasons = data.get("number_of_seasons")
            if seasons is not None:
                try:
                    if int(seasons) < 0:
                        errors.append(f"Negative season count: {seasons}")
                except (ValueError, TypeError):
                    warnings.append(f"Season count not an integer: {seasons}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _fail(self, message: PipelineMessage, error: str) -> PipelineMessage:
        return PipelineMessage(
            message_type=MessageType.FAILED,
            job_id=message.job_id,
            connector_name=message.connector_name,
            external_id=message.external_id,
            entity_type=message.entity_type,
            payload=message.payload,
            raw_payload_id=message.raw_payload_id,
            error=f"validation: {error}",
            metadata={**message.metadata, "failure_stage": "validation"},
            trace_id=message.trace_id,
        )
