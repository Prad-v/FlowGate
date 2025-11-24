"""Neo4j client for access graph operations"""

import logging
from typing import Optional, List, Dict, Any
from neo4j import GraphDatabase
from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j client wrapper for access graph operations"""

    def __init__(self):
        self._driver: Optional[Any] = None
        self._uri = settings.neo4j_uri
        self._user = settings.neo4j_user
        self._password = settings.neo4j_password

    def connect(self) -> None:
        """Connect to Neo4j database"""
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self._uri,
                    auth=(self._user, self._password)
                )
                # Test connection
                with self._driver.session() as session:
                    session.run("RETURN 1")
                logger.info(f"Connected to Neo4j at {self._uri}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise

    def close(self) -> None:
        """Close Neo4j connection"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Disconnected from Neo4j")

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results"""
        if self._driver is None:
            self.connect()

        try:
            with self._driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Error executing Neo4j query: {e}")
            raise

    def find_access_paths(
        self,
        user_id: str,
        resource_id: str,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """Find all access paths from user to resource"""
        query = """
        MATCH path = (u:User {id: $user_id})-[*1..%d]->(res:Resource {id: $resource_id})
        RETURN path, length(path) as depth
        ORDER BY depth
        LIMIT 10
        """ % max_depth

        return self.execute_query(query, {"user_id": user_id, "resource_id": resource_id})

    def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all roles for a user"""
        query = """
        MATCH (u:User {id: $user_id})-[:HAS_ROLE]->(r:Role)
        RETURN r.id as role_id, r.name as role_name, r.privilege_level as privilege_level
        """
        return self.execute_query(query, {"user_id": user_id})

    def get_resource_permissions(self, resource_id: str) -> List[Dict[str, Any]]:
        """Get all permissions for a resource"""
        query = """
        MATCH (r:Resource {id: $resource_id})<-[:HAS_PERMISSION]-(role:Role)
        RETURN role.id as role_id, role.name as role_name, role.privilege_level as privilege_level
        """
        return self.execute_query(query, {"resource_id": resource_id})

    def create_user(self, user_id: str, name: str, email: Optional[str] = None) -> None:
        """Create a user node in the graph"""
        query = """
        MERGE (u:User {id: $user_id})
        SET u.name = $name, u.email = $email, u.created_at = datetime()
        """
        self.execute_query(query, {"user_id": user_id, "name": name, "email": email})

    def create_resource(self, resource_id: str, resource_type: str, name: str) -> None:
        """Create a resource node in the graph"""
        query = """
        MERGE (r:Resource {id: $resource_id})
        SET r.type = $resource_type, r.name = $name, r.created_at = datetime()
        """
        self.execute_query(query, {
            "resource_id": resource_id,
            "resource_type": resource_type,
            "name": name
        })

    def assign_role(self, user_id: str, role_id: str, role_name: str) -> None:
        """Assign a role to a user"""
        query = """
        MATCH (u:User {id: $user_id})
        MERGE (r:Role {id: $role_id})
        SET r.name = $role_name
        MERGE (u)-[:HAS_ROLE {assigned_at: datetime()}]->(r)
        """
        self.execute_query(query, {
            "user_id": user_id,
            "role_id": role_id,
            "role_name": role_name
        })


# Global Neo4j client instance
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create global Neo4j client instance"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client

