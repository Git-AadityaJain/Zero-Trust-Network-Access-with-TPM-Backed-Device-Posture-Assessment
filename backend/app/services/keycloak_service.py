# app/services/keycloak_service.py

"""
Keycloak Admin API Service
Handles all Keycloak user management operations with proper error handling
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)


class KeycloakError(Exception):
    """Base exception for Keycloak operations"""
    pass


class KeycloakUserNotFoundError(KeycloakError):
    """Raised when user is not found in Keycloak"""
    pass


class KeycloakAuthenticationError(KeycloakError):
    """Raised when authentication with Keycloak fails"""
    pass


class KeycloakService:
    """
    Service for interacting with Keycloak Admin API
    Handles user CRUD operations, role management, and authentication
    """
    
    def __init__(self):
        # Extract realm from OIDC issuer URL
        # Format: http://keycloak:8080/realms/master or http://localhost:8080/realms/master
        issuer_parts = str(settings.OIDC_ISSUER).rstrip('/').split('/')
        self.realm = issuer_parts[-1]  # Extract realm name (e.g., "master")
        
        # Build base Keycloak URL (remove /realms/{realm})
        self.base_url = '/'.join(issuer_parts[:-2])  # http://keycloak:8080 or http://localhost:8080
        
        self.admin_api_url = f"{self.base_url}/admin/realms/{self.realm}"
        self.token_url = f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        self.client_id = settings.OIDC_CLIENT_ID
        self.client_secret = settings.OIDC_CLIENT_SECRET
        
        # Token caching
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        logger.info(f"Initialized KeycloakService for realm: {self.realm}")
    
    async def _get_admin_token(self) -> str:
        """
        Get admin access token using client credentials flow
        Caches token until expiration
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token
        
        # Request new token
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": "openid roles",  # Request roles scope to include client roles in token
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get admin token: {response.status_code} - {response.text}")
                    raise KeycloakAuthenticationError(
                        f"Failed to authenticate with Keycloak: {response.status_code}"
                    )
                
                token_data = response.json()
                self._access_token = token_data["access_token"]
                
                # Set expiration with 30 second buffer
                expires_in = token_data.get("expires_in", 300)
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 30)
                
                logger.debug("Successfully obtained Keycloak admin token")
                return self._access_token
                
        except httpx.RequestError as e:
            logger.error(f"Network error while getting admin token: {e}")
            raise KeycloakAuthenticationError(f"Network error: {e}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make authenticated request to Keycloak Admin API
        """
        token = await self._get_admin_token()
        url = f"{self.admin_api_url}/{endpoint.lstrip('/')}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                    headers=headers,
                    timeout=15.0
                )
                return response
                
        except httpx.RequestError as e:
            logger.error(f"Request error to Keycloak: {e}")
            raise KeycloakError(f"Request failed: {e}")
    
    # ==================== USER MANAGEMENT ====================
    
    async def create_user(
        self,
        username: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        enabled: bool = True,
        email_verified: bool = False,
        temporary_password: Optional[str] = None,
        attributes: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """
        Create a new user in Keycloak
        
        Args:
            username: Unique username
            email: User email address
            first_name: User's first name
            last_name: User's last name
            enabled: Whether user account is enabled
            email_verified: Whether email is verified
            temporary_password: Optional temporary password (user must change on first login)
            attributes: Custom user attributes (e.g., device_id)
        
        Returns:
            Keycloak user ID (UUID)
        
        Raises:
            KeycloakError: If user creation fails
        """
        user_data = {
            "username": username,
            "email": email,
            "enabled": enabled,
            "emailVerified": email_verified,
        }
        
        if first_name:
            user_data["firstName"] = first_name
        if last_name:
            user_data["lastName"] = last_name
        if attributes:
            user_data["attributes"] = attributes
        
        try:
            # Create user
            response = await self._make_request("POST", "/users", json_data=user_data)
            
            if response.status_code == 201:
                # Extract user ID from Location header
                location = response.headers.get("Location")
                user_id = location.split("/")[-1] if location else None
                
                if not user_id:
                    # Fallback: query user by username
                    user_id = await self.get_user_id_by_username(username)
                
                logger.info(f"Successfully created Keycloak user: {username} (ID: {user_id})")
                
                # Set password if provided (always permanent, no password change required)
                if temporary_password and user_id:
                    await self.set_user_password(user_id, temporary_password, temporary=False)
                
                return user_id
            
            elif response.status_code == 409:
                logger.warning(f"User {username} already exists in Keycloak")
                raise KeycloakError(f"User {username} already exists")
            
            else:
                logger.error(f"Failed to create user: {response.status_code} - {response.text}")
                raise KeycloakError(f"Failed to create user: {response.status_code}")
                
        except KeycloakError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating user: {e}")
            raise KeycloakError(f"Unexpected error: {e}")
    
    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """
        Get user details by Keycloak user ID
        
        Returns:
            User data dictionary
        
        Raises:
            KeycloakUserNotFoundError: If user not found
        """
        try:
            response = await self._make_request("GET", f"/users/{user_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise KeycloakUserNotFoundError(f"User {user_id} not found")
            else:
                raise KeycloakError(f"Failed to get user: {response.status_code}")
                
        except KeycloakUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            raise KeycloakError(f"Error getting user: {e}")
    
    async def get_user_id_by_username(self, username: str) -> Optional[str]:
        """
        Get Keycloak user ID by username
        
        Returns:
            User ID or None if not found
        """
        try:
            response = await self._make_request(
                "GET",
                "/users",
                params={"username": username, "exact": "true"}
            )
            
            if response.status_code == 200:
                users = response.json()
                if users and len(users) > 0:
                    return users[0]["id"]
                return None
            else:
                logger.error(f"Failed to search user: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching user {username}: {e}")
            return None
    
    async def update_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        enabled: Optional[bool] = None,
        attributes: Optional[Dict[str, List[str]]] = None
    ) -> bool:
        """
        Update user information in Keycloak
        
        Returns:
            True if successful
        
        Raises:
            KeycloakUserNotFoundError: If user not found
            KeycloakError: If update fails
        """
        # Build update payload with only provided fields
        update_data = {}
        
        if email is not None:
            update_data["email"] = email
        if first_name is not None:
            update_data["firstName"] = first_name
        if last_name is not None:
            update_data["lastName"] = last_name
        if enabled is not None:
            update_data["enabled"] = enabled
        if attributes is not None:
            update_data["attributes"] = attributes
        
        if not update_data:
            logger.warning("No fields to update")
            return True
        
        try:
            response = await self._make_request(
                "PUT",
                f"/users/{user_id}",
                json_data=update_data
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully updated user {user_id}")
                return True
            elif response.status_code == 404:
                raise KeycloakUserNotFoundError(f"User {user_id} not found")
            else:
                logger.error(f"Failed to update user: {response.status_code} - {response.text}")
                raise KeycloakError(f"Failed to update user: {response.status_code}")
                
        except KeycloakUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise KeycloakError(f"Error updating user: {e}")
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user from Keycloak
        
        Returns:
            True if successful
        
        Raises:
            KeycloakUserNotFoundError: If user not found
        """
        try:
            response = await self._make_request("DELETE", f"/users/{user_id}")
            
            if response.status_code == 204:
                logger.info(f"Successfully deleted user {user_id}")
                return True
            elif response.status_code == 404:
                raise KeycloakUserNotFoundError(f"User {user_id} not found")
            else:
                logger.error(f"Failed to delete user: {response.status_code}")
                raise KeycloakError(f"Failed to delete user: {response.status_code}")
                
        except KeycloakUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise KeycloakError(f"Error deleting user: {e}")
    
    async def set_user_password(
        self,
        user_id: str,
        password: str,
        temporary: bool = False
    ) -> bool:
        """
        Set or reset user password
        
        Args:
            user_id: Keycloak user ID
            password: New password
            temporary: If True, user must change password on next login
        
        Returns:
            True if successful
        """
        password_data = {
            "type": "password",
            "value": password,
            "temporary": temporary
        }
        
        try:
            response = await self._make_request(
                "PUT",
                f"/users/{user_id}/reset-password",
                json_data=password_data
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully set password for user {user_id}")
                return True
            elif response.status_code == 404:
                raise KeycloakUserNotFoundError(f"User {user_id} not found")
            else:
                logger.error(f"Failed to set password: {response.status_code}")
                raise KeycloakError(f"Failed to set password: {response.status_code}")
                
        except KeycloakUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error setting password for user {user_id}: {e}")
            raise KeycloakError(f"Error setting password: {e}")
    
    # ==================== ROLE MANAGEMENT ====================
    
    async def get_realm_roles(self) -> List[Dict[str, Any]]:
        """
        Get all realm-level roles
        
        Returns:
            List of role dictionaries
        """
        try:
            response = await self._make_request("GET", "/roles")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get roles: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting realm roles: {e}")
            return []
    
    async def get_role_by_name(self, role_name: str) -> Optional[Dict[str, Any]]:
        """
        Get role details by name
        
        Returns:
            Role dictionary or None if not found
        """
        try:
            response = await self._make_request("GET", f"/roles/{role_name}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Role {role_name} not found")
                return None
            else:
                logger.error(f"Failed to get role: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting role {role_name}: {e}")
            return None
    
    async def assign_realm_roles_to_user(
        self,
        user_id: str,
        role_names: List[str]
    ) -> bool:
        """
        Assign realm-level roles to user
        
        Args:
            user_id: Keycloak user ID
            role_names: List of role names to assign (e.g., ["admin", "editor"])
        
        Returns:
            True if successful
        """
        # Get role representations
        roles = []
        for role_name in role_names:
            role = await self.get_role_by_name(role_name)
            if role:
                roles.append(role)
            else:
                logger.warning(f"Role {role_name} not found, skipping")
        
        if not roles:
            logger.warning("No valid roles to assign")
            return False
        
        try:
            response = await self._make_request(
                "POST",
                f"/users/{user_id}/role-mappings/realm",
                json_data=roles
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully assigned roles {role_names} to user {user_id}")
                return True
            elif response.status_code == 404:
                raise KeycloakUserNotFoundError(f"User {user_id} not found")
            else:
                logger.error(f"Failed to assign roles: {response.status_code} - {response.text}")
                raise KeycloakError(f"Failed to assign roles: {response.status_code}")
                
        except KeycloakUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error assigning roles to user {user_id}: {e}")
            raise KeycloakError(f"Error assigning roles: {e}")
    
    async def remove_realm_roles_from_user(
        self,
        user_id: str,
        role_names: List[str]
    ) -> bool:
        """
        Remove realm-level roles from user
        
        Returns:
            True if successful
        """
        # Get role representations
        roles = []
        for role_name in role_names:
            role = await self.get_role_by_name(role_name)
            if role:
                roles.append(role)
        
        if not roles:
            logger.warning("No valid roles to remove")
            return False
        
        try:
            response = await self._make_request(
                "DELETE",
                f"/users/{user_id}/role-mappings/realm",
                json_data=roles
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully removed roles {role_names} from user {user_id}")
                return True
            else:
                logger.error(f"Failed to remove roles: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing roles from user {user_id}: {e}")
            return False
    
    async def get_user_realm_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all realm-level roles assigned to user
        
        Returns:
            List of role dictionaries
        """
        try:
            response = await self._make_request(
                "GET",
                f"/users/{user_id}/role-mappings/realm"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user roles: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting roles for user {user_id}: {e}")
            return []
    
    async def create_realm_role(
        self,
        name: str,
        description: Optional[str] = None,
        composite: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new realm-level role
        
        Args:
            name: Role name
            description: Role description
            composite: Whether this is a composite role
        
        Returns:
            Created role dictionary
        
        Raises:
            KeycloakError: If role creation fails
        """
        role_data = {
            "name": name,
            "composite": composite,
            "clientRole": False
        }
        
        if description:
            role_data["description"] = description
        
        try:
            response = await self._make_request(
                "POST",
                "/roles",
                json_data=role_data
            )
            
            if response.status_code == 201:
                # Keycloak returns 201 but doesn't return the role, so fetch it
                return await self.get_role_by_name(name)
            elif response.status_code == 409:
                raise KeycloakError(f"Role '{name}' already exists")
            else:
                logger.error(f"Failed to create role: {response.status_code} - {response.text}")
                raise KeycloakError(f"Failed to create role: {response.status_code}")
                
        except KeycloakError:
            raise
        except Exception as e:
            logger.error(f"Error creating role {name}: {e}")
            raise KeycloakError(f"Error creating role: {e}")
    
    async def update_realm_role(
        self,
        role_name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a realm-level role
        
        Args:
            role_name: Name of the role to update
            description: New description (optional)
        
        Returns:
            Updated role dictionary
        
        Raises:
            KeycloakError: If role update fails
        """
        # Get current role data
        current_role = await self.get_role_by_name(role_name)
        if not current_role:
            raise KeycloakError(f"Role '{role_name}' not found")
        
        # Prepare update data
        update_data = {
            "name": current_role["name"],
            "composite": current_role.get("composite", False),
            "clientRole": current_role.get("clientRole", False)
        }
        
        if description is not None:
            update_data["description"] = description
        elif "description" in current_role:
            update_data["description"] = current_role["description"]
        
        try:
            response = await self._make_request(
                "PUT",
                f"/roles/{role_name}",
                json_data=update_data
            )
            
            if response.status_code == 204:
                # Return updated role
                return await self.get_role_by_name(role_name)
            elif response.status_code == 404:
                raise KeycloakError(f"Role '{role_name}' not found")
            else:
                logger.error(f"Failed to update role: {response.status_code} - {response.text}")
                raise KeycloakError(f"Failed to update role: {response.status_code}")
                
        except KeycloakError:
            raise
        except Exception as e:
            logger.error(f"Error updating role {role_name}: {e}")
            raise KeycloakError(f"Error updating role: {e}")
    
    async def delete_realm_role(self, role_name: str) -> bool:
        """
        Delete a realm-level role
        
        Args:
            role_name: Name of the role to delete
        
        Returns:
            True if successful
        
        Raises:
            KeycloakError: If role deletion fails
        """
        try:
            response = await self._make_request("DELETE", f"/roles/{role_name}")
            
            if response.status_code == 204:
                logger.info(f"Successfully deleted role: {role_name}")
                return True
            elif response.status_code == 404:
                raise KeycloakError(f"Role '{role_name}' not found")
            else:
                logger.error(f"Failed to delete role: {response.status_code} - {response.text}")
                raise KeycloakError(f"Failed to delete role: {response.status_code}")
                
        except KeycloakError:
            raise
        except Exception as e:
            logger.error(f"Error deleting role {role_name}: {e}")
            raise KeycloakError(f"Error deleting role: {e}")
    
    # ==================== USER ATTRIBUTES ====================
    
    async def set_user_attribute(
        self,
        user_id: str,
        attribute_name: str,
        attribute_value: str
    ) -> bool:
        """
        Set a custom attribute on user (e.g., device_id)
        
        Args:
            user_id: Keycloak user ID
            attribute_name: Attribute key (e.g., "device_id")
            attribute_value: Attribute value
        
        Returns:
            True if successful
        """
        try:
            # Get current user data
            user = await self.get_user_by_id(user_id)
            
            # Update attributes
            attributes = user.get("attributes", {})
            attributes[attribute_name] = [attribute_value]  # Keycloak stores attributes as lists
            
            # Update user with new attributes
            return await self.update_user(user_id, attributes=attributes)
            
        except Exception as e:
            logger.error(f"Error setting attribute {attribute_name} for user {user_id}: {e}")
            raise KeycloakError(f"Error setting user attribute: {e}")
    
    async def get_user_attribute(
        self,
        user_id: str,
        attribute_name: str
    ) -> Optional[str]:
        """
        Get a custom attribute from user
        
        Returns:
            Attribute value or None if not found
        """
        try:
            user = await self.get_user_by_id(user_id)
            attributes = user.get("attributes", {})
            values = attributes.get(attribute_name, [])
            return values[0] if values else None
            
        except Exception as e:
            logger.error(f"Error getting attribute {attribute_name} for user {user_id}: {e}")
            return None
    
    # ==================== SESSION MANAGEMENT ====================
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user
        
        Args:
            user_id: Keycloak user ID
            
        Returns:
            List of session dictionaries
        """
        try:
            response = await self._make_request(
                "GET",
                f"/users/{user_id}/sessions"
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise KeycloakUserNotFoundError(f"User {user_id} not found")
            else:
                logger.error(f"Failed to get user sessions: {response.status_code}")
                return []
                
        except KeycloakUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {e}")
            return []
    
    async def logout_user_session(self, user_id: str, session_id: str) -> bool:
        """
        Logout a specific session for a user
        
        Args:
            user_id: Keycloak user ID
            session_id: Session ID to logout
            
        Returns:
            True if successful
        """
        try:
            response = await self._make_request(
                "DELETE",
                f"/users/{user_id}/sessions/{session_id}"
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully logged out session {session_id} for user {user_id}")
                return True
            elif response.status_code == 404:
                logger.warning(f"Session {session_id} not found for user {user_id}")
                return False
            else:
                logger.error(f"Failed to logout session: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging out session {session_id} for user {user_id}: {e}")
            return False
    
    async def logout_all_user_sessions(self, user_id: str) -> bool:
        """
        Logout all active sessions for a user
        
        Args:
            user_id: Keycloak user ID
            
        Returns:
            True if successful
        """
        try:
            response = await self._make_request(
                "POST",
                f"/users/{user_id}/logout"
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully logged out all sessions for user {user_id}")
                return True
            elif response.status_code == 404:
                raise KeycloakUserNotFoundError(f"User {user_id} not found")
            else:
                logger.error(f"Failed to logout all sessions: {response.status_code}")
                return False
                
        except KeycloakUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error logging out all sessions for user {user_id}: {e}")
            return False
    
    async def logout_other_user_sessions(self, user_id: str, current_session_id: str) -> int:
        """
        Logout all sessions for a user except the current one
        This enforces single-session-per-user policy
        
        Args:
            user_id: Keycloak user ID
            current_session_id: Session ID to keep active
            
        Returns:
            Number of sessions logged out
        """
        try:
            sessions = await self.get_user_sessions(user_id)
            if not sessions:
                return 0
            
            logged_out_count = 0
            for session in sessions:
                session_id = session.get("id")
                if session_id and session_id != current_session_id:
                    success = await self.logout_user_session(user_id, session_id)
                    if success:
                        logged_out_count += 1
            
            if logged_out_count > 0:
                logger.info(f"Logged out {logged_out_count} other session(s) for user {user_id}")
            
            return logged_out_count
                
        except Exception as e:
            logger.error(f"Error logging out other sessions for user {user_id}: {e}")
            return 0
    
    # ==================== UTILITY METHODS ====================
    
    async def health_check(self) -> bool:
        """
        Check if Keycloak is accessible and responding
        
        Returns:
            True if healthy
        """
        try:
            # Simple connectivity check - try to access well-known endpoint
            well_known_url = f"{self.base_url}/realms/{self.realm}/.well-known/openid-configuration"
            async with httpx.AsyncClient() as client:
                response = await client.get(well_known_url, timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Keycloak health check failed: {e}")
            return False


# Singleton instance
keycloak_service = KeycloakService()
