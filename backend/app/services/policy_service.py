# services/policy_service.py

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.policy import Policy
from app.models.device import Device
from app.models.user import User
from app.schemas.policy import PolicyCreate, PolicyUpdate
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class PolicyEvaluationResult:
    """Result of policy evaluation"""
    def __init__(
        self,
        allowed: bool,
        policy_id: Optional[int] = None,
        policy_name: Optional[str] = None,
        reason: Optional[str] = None,
        violations: Optional[List[str]] = None
    ):
        self.allowed = allowed
        self.policy_id = policy_id
        self.policy_name = policy_name
        self.reason = reason
        self.violations = violations or []

class PolicyService:
    @staticmethod
    async def create_policy(db: AsyncSession, policy_data: PolicyCreate) -> Policy:
        """Create a new policy"""
        policy = Policy(**policy_data.model_dump())
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def get_policy_by_id(db: AsyncSession, policy_id: int) -> Optional[Policy]:
        """Get policy by ID"""
        result = await db.execute(select(Policy).where(Policy.id == policy_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_policy_by_name(db: AsyncSession, name: str) -> Optional[Policy]:
        """Get policy by name"""
        result = await db.execute(select(Policy).where(Policy.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_policies(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        policy_type: Optional[str] = None
    ) -> List[Policy]:
        """Get all policies with optional filters"""
        query = select(Policy)
        
        if active_only:
            query = query.where(Policy.is_active == True)
        
        if policy_type:
            query = query.where(Policy.policy_type == policy_type)
        
        query = query.order_by(Policy.priority.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_policy(
        db: AsyncSession,
        policy_id: int,
        policy_data: PolicyUpdate
    ) -> Optional[Policy]:
        """Update a policy"""
        policy = await PolicyService.get_policy_by_id(db, policy_id)
        if not policy:
            return None
        
        update_data = policy_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(policy, field, value)
        
        policy.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def delete_policy(db: AsyncSession, policy_id: int) -> bool:
        """Delete a policy"""
        policy = await PolicyService.get_policy_by_id(db, policy_id)
        if not policy:
            return False
        
        await db.delete(policy)
        await db.commit()
        return True

    @staticmethod
    async def evaluate_policies(
        db: AsyncSession,
        user: Optional[User] = None,
        device: Optional[Device] = None,
        posture_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[PolicyEvaluationResult], Optional[str]]:
        """
        Evaluate all active policies against user, device, posture, and context
        
        Args:
            db: Database session
            user: User making the request
            device: Device being evaluated
            posture_data: Current posture data
            context: Additional context (time, location, resource, etc.)
        
        Returns:
            (allowed, evaluation_results, denial_reason)
        """
        # Get all active policies, ordered by priority (highest first)
        policies = await PolicyService.get_all_policies(
            db=db,
            active_only=True,
            skip=0,
            limit=1000
        )
        
        if not policies:
            logger.debug("No active policies found, allowing access by default")
            return True, [], None
        
        evaluation_results: List[PolicyEvaluationResult] = []
        context = context or {}
        
        # Add current time if not provided
        if "time" not in context:
            context["time"] = datetime.now(timezone.utc).isoformat()
        
        # Extract user roles (from Keycloak token or user model)
        user_roles = []
        if user:
            # Try to get roles from context if provided (from token)
            if context and "user_roles" in context:
                user_roles = context["user_roles"]
            else:
                # Default role - in production, fetch from Keycloak
                user_roles = ["user"]  # Default role
        
        # Evaluate each policy
        for policy in policies:
            if policy.enforce_mode == "disabled":
                continue
            
            result = PolicyService._evaluate_single_policy(
                policy=policy,
                user=user,
                user_roles=user_roles,
                device=device,
                posture_data=posture_data,
                context=context
            )
            
            evaluation_results.append(result)
            
            # If policy is in enforce mode and denies access, stop evaluation
            if policy.enforce_mode == "enforce" and not result.allowed:
                logger.warning(
                    f"Policy '{policy.name}' (ID: {policy.id}) denied access: {result.reason}"
                )
                return False, evaluation_results, result.reason
            
            # If policy is in monitor mode, log but continue
            if policy.enforce_mode == "monitor" and not result.allowed:
                logger.info(
                    f"Policy '{policy.name}' (ID: {policy.id}) would deny access (monitor mode): {result.reason}"
                )
        
        # If we get here, all policies allowed access or were in monitor mode
        logger.debug(f"All policies evaluated, access allowed")
        return True, evaluation_results, None

    @staticmethod
    def _evaluate_single_policy(
        policy: Policy,
        user: Optional[User],
        user_roles: List[str],
        device: Optional[Device],
        posture_data: Optional[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> PolicyEvaluationResult:
        """
        Evaluate a single policy against the provided context
        
        Policy rules format:
        {
            "conditions": {
                "user_roles": ["admin", "security-analyst"],
                "device_compliant": true,
                "posture_checks": {
                    "antivirus_enabled": true,
                    "firewall_enabled": true,
                    "disk_encrypted": true
                },
                "time_restrictions": {
                    "allowed_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17],
                    "allowed_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                }
            },
            "action": "allow" | "deny"
        }
        """
        rules = policy.rules or {}
        conditions = rules.get("conditions", {})
        action = rules.get("action", "allow")
        
        violations = []
        
        # Check user roles
        if "user_roles" in conditions:
            required_roles = conditions["user_roles"]
            if not any(role in user_roles for role in required_roles):
                violations.append(f"User does not have required roles: {required_roles}")
        
        # Check device compliance
        if "device_compliant" in conditions:
            required_compliant = conditions["device_compliant"]
            if device:
                if device.is_compliant != required_compliant:
                    violations.append(
                        f"Device compliance mismatch: expected {required_compliant}, got {device.is_compliant}"
                    )
            else:
                violations.append("Device not provided for compliance check")
        
        # Check device status
        if "device_status" in conditions:
            required_status = conditions["device_status"]
            if device:
                if device.status != required_status:
                    violations.append(
                        f"Device status mismatch: expected {required_status}, got {device.status}"
                    )
            else:
                violations.append("Device not provided for status check")
        
        # Check posture data
        if "posture_checks" in conditions and posture_data:
            posture_checks = conditions["posture_checks"]
            for check, required_value in posture_checks.items():
                actual_value = posture_data.get(check)
                if actual_value != required_value:
                    violations.append(
                        f"Posture check failed: {check} = {actual_value}, expected {required_value}"
                    )
        
        # Check time restrictions
        if "time_restrictions" in conditions:
            time_restrictions = conditions["time_restrictions"]
            current_time = datetime.fromisoformat(context.get("time", datetime.now(timezone.utc).isoformat()))
            
            if "allowed_hours" in time_restrictions:
                allowed_hours = time_restrictions["allowed_hours"]
                if current_time.hour not in allowed_hours:
                    violations.append(
                        f"Access not allowed at hour {current_time.hour}. Allowed hours: {allowed_hours}"
                    )
            
            if "allowed_days" in time_restrictions:
                allowed_days = [d.lower() for d in time_restrictions["allowed_days"]]
                current_day = current_time.strftime("%A").lower()
                if current_day not in allowed_days:
                    violations.append(
                        f"Access not allowed on {current_day}. Allowed days: {allowed_days}"
                    )
        
        # Determine if policy allows or denies
        # If action is "allow" and no violations, allow
        # If action is "deny" and violations exist, deny
        if action == "allow":
            allowed = len(violations) == 0
            reason = "Policy allows access" if allowed else f"Policy violations: {', '.join(violations)}"
        else:  # action == "deny"
            allowed = len(violations) == 0  # If no violations, don't deny
            reason = "Policy denies access" if not allowed else "No policy violations found"
        
        return PolicyEvaluationResult(
            allowed=allowed,
            policy_id=policy.id,
            policy_name=policy.name,
            reason=reason,
            violations=violations
        )

    @staticmethod
    async def evaluate_for_access(
        db: AsyncSession,
        user: User,
        device: Optional[Device],
        resource: str,
        access_type: str = "read"
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Evaluate policies for access to a resource
        
        Returns:
            (allowed, denial_reason, policy_id_that_denied)
        """
        # Get latest posture data if device exists
        posture_data = None
        if device and device.posture_data:
            posture_data = device.posture_data
        
        context = {
            "resource": resource,
            "access_type": access_type,
            "time": datetime.now(timezone.utc).isoformat()
        }
        
        allowed, results, denial_reason = await PolicyService.evaluate_policies(
            db=db,
            user=user,
            device=device,
            posture_data=posture_data,
            context=context
        )
        
        # Find the policy that denied if any
        denying_policy_id = None
        if not allowed:
            for result in results:
                if not result.allowed and result.policy_id:
                    denying_policy_id = result.policy_id
                    break
        
        return allowed, denial_reason, denying_policy_id
